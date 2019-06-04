#
# Copyright 2019 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import six

from libnmstate import iplib
from libnmstate.appliers import linux_bridge
from libnmstate.error import NmstateNotImplementedError
from libnmstate.error import NmstateValueError
from libnmstate.schema import Interface
from libnmstate.schema import Route
from libnmstate.schema import DNS
from libnmstate.nm.route import IPV4_DEFAULT_GATEWAY_DESTINATION
from libnmstate.nm.route import IPV6_DEFAULT_GATEWAY_DESTINATION


BRPORT_OPTIONS = '_brport_options'
MASTER = '_master'
MASTER_TYPE = '_master_type'
ROUTES = '_routes'
DNS_METADATA = '_dns'


def generate_ifaces_metadata(desired_state, current_state):
    """
    The described desired state for each interface may include references to
    other interfaces. As the provider handles the interface setting in an
    isolated manner, it is sometime necessary to specify a property on an
    interface based on a property from a different interface.
    An exmaple of this, is the bond slaves property, which should mark each
    slave with the setting of it being a slave.

    For such relationships between interfaces or some other potential inputs,
    metadata is generated on interfaces, usable by the provider when
    configuring the interface.
    """
    _generate_link_master_metadata(
        desired_state.interfaces,
        current_state.interfaces,
        master_type='bond',
        get_slaves_func=_get_bond_slaves_from_state,
        set_metadata_func=_set_common_slaves_metadata
    )
    _generate_link_master_metadata(
        desired_state.interfaces,
        current_state.interfaces,
        master_type='ovs-bridge',
        get_slaves_func=_get_ovs_slaves_from_state,
        set_metadata_func=_set_ovs_bridge_ports_metadata
    )
    _generate_link_master_metadata(
        desired_state.interfaces,
        current_state.interfaces,
        master_type='linux-bridge',
        get_slaves_func=linux_bridge.get_slaves_from_state,
        set_metadata_func=linux_bridge.set_bridge_ports_metadata
    )
    _generate_route_metadata(desired_state)
    _generate_dns_metadata(desired_state, current_state)


def remove_ifaces_metadata(ifaces_state):
    for iface_state in six.viewvalues(ifaces_state.interfaces):
        iface_state.pop(MASTER, None)
        iface_state.pop(MASTER_TYPE, None)
        iface_state.pop(BRPORT_OPTIONS, None)
        iface_state.get(Interface.IPV4, {}).pop(ROUTES, None)
        iface_state.get(Interface.IPV6, {}).pop(ROUTES, None)
        iface_state.get(Interface.IPV4, {}).pop(DNS_METADATA, None)
        iface_state.get(Interface.IPV6, {}).pop(DNS_METADATA, None)


def _get_bond_slaves_from_state(iface_state, default=()):
    return iface_state.get('link-aggregation', {}).get('slaves', default)


def _set_ovs_bridge_ports_metadata(master_state, slave_state):
    _set_common_slaves_metadata(master_state, slave_state)

    ports = master_state.get('bridge', {}).get('port', [])
    port = next(
        six.moves.filter(lambda n: n['name'] == slave_state['name'], ports),
        {}
    )
    slave_state[BRPORT_OPTIONS] = port


def _set_common_slaves_metadata(master_state, slave_state):
    slave_state[MASTER] = master_state['name']
    slave_state[MASTER_TYPE] = master_state['type']


def _get_ovs_slaves_from_state(iface_state, default=()):
    ports = iface_state.get('bridge', {}).get('port')
    if ports is None:
        return default
    return [p['name'] for p in ports]


def _generate_link_master_metadata(ifaces_desired_state,
                                   ifaces_current_state,
                                   master_type,
                                   get_slaves_func,
                                   set_metadata_func):
    """
    Given master's slaves, add to the slave interface the master information.

    Possible scenarios for a given desired and current sate:
    - The desired state contains both the masters and their slaves.
    - The desired state contains the masters and partially (or not at all)
      the slaves. Some or all the slaves are in the current state.
    - Master is in the current state and some of the slaves are in the desired
      state.
    """
    desired_masters = [
        (ifname, ifstate)
        for ifname, ifstate in six.viewitems(ifaces_desired_state)
        if ifstate.get('type') == master_type
    ]
    for master_name, master_state in desired_masters:
        desired_slaves = get_slaves_func(master_state)
        for slave in desired_slaves:
            if slave in ifaces_desired_state:
                set_metadata_func(master_state, ifaces_desired_state[slave])
            elif slave in ifaces_current_state:
                ifaces_desired_state[slave] = {'name': slave,
                                               'state': master_state['state']}
                set_metadata_func(master_state, ifaces_desired_state[slave])

        desired_slaves = get_slaves_func(master_state)
        current_master_state = ifaces_current_state.get(master_name)
        if desired_slaves and current_master_state:
            current_slaves = get_slaves_func(current_master_state)
            slaves2remove = (set(current_slaves) - set(desired_slaves))
            for slave in slaves2remove:
                if slave not in ifaces_desired_state:
                    ifaces_desired_state[slave] = {'name': slave}

    current_masters = (
        (ifname, ifstate)
        for ifname, ifstate in six.viewitems(ifaces_current_state)
        if ifstate.get('type') == master_type
    )
    for master_name, master_state in current_masters:
        current_slaves = get_slaves_func(master_state)
        for slave in current_slaves:
            if slave in ifaces_desired_state:
                iface_state = ifaces_desired_state.get(master_name, {})
                master_has_no_slaves_specified_in_desired = (
                    get_slaves_func(iface_state, None) is None)
                slave_has_no_master_specified_in_desired = (
                    ifaces_desired_state[slave].get(MASTER) is None)
                if (slave_has_no_master_specified_in_desired and
                        master_has_no_slaves_specified_in_desired):
                    set_metadata_func(
                        master_state, ifaces_desired_state[slave])


def _generate_route_metadata(desired_state):
    """
    Save routes under interface IP protocol so that nm/ipv4.py or nm/ipv6.py
    could include route configuration in `create_setting()`.
    Currently route['next-hop-interface'] is mandatory.
    """
    for iface_name, routes in six.viewitems(desired_state.config_iface_routes):
        iface_state = desired_state.interfaces.get(iface_name, {})
        for family in (Interface.IPV4, Interface.IPV6):
            if family in iface_state:
                iface_state[family][ROUTES] = []
            else:
                iface_state[family] = {ROUTES: []}
        for route in routes:
            if iplib.is_ipv6_address(route[Route.DESTINATION]):
                iface_state[Interface.IPV6][ROUTES].append(route)
            else:
                iface_state[Interface.IPV4][ROUTES].append(route)


def _generate_dns_metadata(desired_state, current_state):
    """
    Save DNS configuration to chose interface as metadata.
    Raise NmstateValueError if failed to find interface.
    To handle 3 DNS name server, we need 2+ interfaces when IPv6 server been
    placed between two IPv4 servers and it also require assigning DNS priority.
    To simplify workflow, currently we only support at most 2 name servers.
    """
    servers = desired_state.config_dns.get(DNS.SERVER, [])
    searches = desired_state.config_dns.get(DNS.SEARCH, [])
    if len(servers) > 2:
        raise NmstateNotImplementedError(
            'Nmstate only support at most 2 DNS name servers')

    ipv4_server = []
    ipv6_server = []
    for server in servers:
        if iplib.is_ipv6_address(server):
            ipv6_server.append(server)
        else:
            ipv4_server.append(server)

    search_saved = False
    ipv4_iface, ipv6_iface = _choose_iface_for_dns(desired_state,
                                                   current_state)
    print('ifaces', ipv4_iface, ipv6_iface)
    for iface, family, servers in ((ipv6_iface, Interface.IPV6, ipv6_server),
                                   (ipv4_iface, Interface.IPV4, ipv4_server)):
        if servers:
            if not iface:
                raise NmstateValueError(
                    'Failed to find suitable interface for saving DNS '
                    'name servers: %s' % servers)
            if iface not in desired_state.interfaces:
                desired_state.add_interface_with_name_only(iface)
            dns_meta = {
                DNS.SERVER: servers,
                DNS.SEARCH: []
            }
            if not search_saved:
                dns_meta[DNS.SEARCH] = searches
                search_saved = True
            iface_state = desired_state.interfaces[iface]
            if family not in iface_state:
                iface_state[family] = {DNS_METADATA: dns_meta}
            else:
                iface_state[family][DNS_METADATA] = dns_meta


def _choose_iface_for_dns(desired_state, current_state):
    """
    Find out the interface to store the DNS configuration:
        * Static gateway configured
        * DHCP with auto-dns false
    Return two iface_names, first is for ipv4, second for ipv6.
    """
    ipv6_iface = None
    ipv4_iface = None
    print(desired_state.config_iface_routes)
    for iface_name, routes in six.viewitems(desired_state.config_iface_routes):
        for route in routes:
            if ipv6_iface and ipv4_iface:
                return ipv4_iface, ipv6_iface
            if not ipv6_iface and \
               route[Route.DESTINATION] == IPV6_DEFAULT_GATEWAY_DESTINATION:
                ipv6_iface = iface_name
                continue
            if not ipv4_iface and \
               route[Route.DESTINATION] == IPV4_DEFAULT_GATEWAY_DESTINATION:
                ipv4_iface = iface_name
                continue
    if not ipv4_iface:
        ipv4_iface = _chose_auto_iface_without_auto_dns(
            Interface.IPV4, desired_state, current_state)
    if not ipv6_iface:
        ipv6_iface = _chose_auto_iface_without_auto_dns(
            Interface.IPV6, desired_state, current_state)
    return ipv4_iface, ipv6_iface

def _chose_auto_iface_without_auto_dns(family, desired_state, current_state):
    """
    Return the interface which has DHCP/Autoconf enabled but auto_dns False.
    """
    # The interface is not merged yet, we have to do ourselves.
    pass
