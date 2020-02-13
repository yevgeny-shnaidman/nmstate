#
# Copyright (c) 2020 Red Hat, Inc.
#
# This file is part of nmstate
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#

# Naming Scheme:
#   * ip_state      Object of IPState
#   * ip_info       Dict of IPState

from functools import total_ordering

from .common import BaseState
from .common import default_property


@default_property("ip", "", "IP address")
@default_property("prefix_length", 0, "IP address prefix length")
class IPAddr(BaseState):
    IP = "ip"
    PREFIX_LENGTH = "prefix-length"

    KEYS = [IP, PREFIX_LENGTH]

    @staticmethod
    def is_ipv6(ip):
        return ":" in ip

    def load(self, addr):
        ip_addr = IPAddr()
        ip_addr.ip = addr.get(IPAddr.IP, "")
        if IPAddr.is_ipv6(ip_addr.ip):
            ip_addr.prefix_length = int(addr.get(IPAddr.PREFIX_LENGTH, 128))
        else:
            ip_addr.prefix_length = int(addr.get(IPAddr.PREFIX_LENGTH, 32))
        return ip_addr


@default_property("enabled", False, "Whether IP stack is enabled")
@default_property("dhcp", False, "Whether DHCPv4 is enabled")
@default_property("addresses", [], "A list of IP static address")
@default_property(
    "auto_dns",
    True,
    "Whether apply DNS configuration retrieved "
    "from dynamic IP configuration method(e.g. DHCP)",
)
@default_property(
    "auto_routes",
    True,
    "Whether apply routes(including default gateway) retrieved "
    "from dynamic IP configuration method(e.g. DHCP)",
)
@default_property(
    "auto_gateway",
    True,
    "Whether apply default gateway retrieved "
    "from dynamic IP configuration method(e.g. DHCP)",
)
class IPState(BaseState):
    ENABLED = "enabled"

    ADDRESSES = "addresses"

    DHCP = "dhcp"
    AUTO_DNS = "auto-dns"
    AUTO_GATEWAY = "auto-gateway"
    AUTO_ROUTES = "auto-routes"

    KEYS = [ENABLED, DHCP, AUTO_DNS, AUTO_GATEWAY, AUTO_ROUTES, ADDRESSES]

    @property
    def addresses(self):
        if self._addresses is None:
            return []
        return self._addresses

    @addresses.setter
    def addresses(self, value):
        if isinstance(value, list):
            if value:
                if isinstance(value[0], IPAddr):
                    # Setting via a list of IPAddr
                    self._addresses = value
                else:
                    # Setting via a list of dict
                    self._addresses = []
                    for addr in value:
                        ip_addr = IPAddr()
                        ip_addr.load(addr)
                        self._addresses.append(addr)
            else:
                self._addresses = []
        else:
            raise Exception("TODO: Invalid value for IPState.address")

    def is_dynamic(self):
        return self.dhcp

    def _clean_up_info(self, info):
        if IPState.ENABLED in info and not info[IPState.ENABLED]:
            info = {IPState.ENABLED: False}
        if self.is_dynamic():
            info.pop(IPState.ADDRESSES, None)
        else:
            try:
                info.pop(IPState.AUTO_DNS, None)
                info.pop(IPState.AUTO_GATEWAY, None)
                info.pop(IPState.AUTO_ROUTES, None)
            except ValueError:
                pass


class IPv4State(IPState):
    def is_ipv6(self):
        return False


@default_property(
    "autoconf",
    False,
    "Whether use IPv6 Router Advertisement  for auto-configuration",
)
@default_property("DHCP", False, "Whether enable DHCPv6")
class IPv6State(IPState):
    AUTOCONF = "autoconf"

    KEYS = IPState.KEYS + [AUTOCONF]

    def __init__(self):
        super().__init__()
        self.autoconf = False

    def is_ipv6(self):
        return True

    def is_dynamic(self):
        return self.dhcp or self.autoconf
