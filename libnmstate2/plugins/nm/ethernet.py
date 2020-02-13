# Copyright (C) 2020 Red Hat, Inc.
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; If not, see <http://www.gnu.org/licenses/>.
#
# Author: Gris Ge <fge@redhat.com>
import logging

from libnmstate2.iface_state import IfaceState
from libnmstate2.ifaces import EthernetIfaceState
from .iface_plugin import NmIfacePlugin
from .context import NM


class EthernetIfacePlugin(NmIfacePlugin):
    @property
    def supported_iface_types(self):
        return [IfaceState.TYPE_ETHERNET]

    def get_iface_state(self, parent_iface_state):
        nm_dev = self.ctx.get_nm_dev(parent_iface_state)

        iface_state = EthernetIfaceState()
        iface_state.load(parent_iface_state.to_dict())
        iface_state.mac = nm_dev.get_hw_address()
        if not iface_state.mac:
            iface_state.mac = _get_mac_address_from_sysfs(self.name)
            logging.debug(
                f"NM does not provide MAC address of interface {self.name}, "
                f"using sysfs one: {iface_state.mac}"
            )

        return iface_state

    def create_settings(_self, iface_state, base_profile):
        nm_setting = None
        if base_profile:
            base_setting = base_profile.nm_profile.get_setting_wired()
            nm_setting = base_setting.duplicate()
        if not nm_setting:
            nm_setting = NM.SettingWired.new()

        # TODO, auto-negotiation and etc

        if (
            iface_state.mac
            and iface_state.mac != EthernetIfaceState.MAC_UNKNOWN
        ):
            nm_setting.props.cloned_mac_address = iface_state.mac
        if iface_state.mtu:
            nm_setting.props.mtu = iface_state.mtu
        return [nm_setting]


def _get_mac_address_from_sysfs(iface_name):
    """
    Fetch the mac address of an interface from sysfs.
    This is a workaround for https://bugzilla.redhat.com/1786937.
    """
    mac = None
    sysfs_path = f"/sys/class/net/{ifname}/address"
    try:
        with open(sysfs_path) as f:
            mac = f.read().rstrip("\n")
    except FileNotFoundError:
        pass
    return mac
