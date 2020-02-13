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
#   * iface_state       Object of IfaceState
#   * iface_info        Dictionary of interface state
#   * net_state         Object of NetState
#   * net_info          Dictionary of NetState

from .iface_states import IfaceStates


class NetState(object):
    INTERFACES = "interfaces"
    DNS = "dns-resolver"
    ROUTES = "routes"

    def __init__(self, state=None):
        self._iface_states = None
        self._dns_state = None
        self._route_state = None
        if state:
            if state.get(NetState.INTERFACES):
                self._iface_states = IfaceStates(state[NetState.INTERFACES])
            self._dns_state = state.get(NetState.DNS)
            self._route_state = state.get(NetState.ROUTES)

    def to_dict(self):
        info = {
            NetState.INTERFACES: self._iface_states.to_dict()
        }
        if self._dns_state:
            info[NetState.DNS] = self._dns_state.to_dict()
        if self._route_state:
            info[NetState.ROUTES] = self._route_state.to_dict()
        return info

    def to_dict_full(self):
        info = {
            NetState.INTERFACES: self._iface_states.to_dict_full()
        }
        if self._dns_state:
            info[NetState.DNS] = self._dns_state.to_dict_full()
        if self._route_state:
            info[NetState.ROUTES] = self._route_state.to_dict_full()
        return info

    def load(self, net_info):
        """
        Along with schema check, canonical check.
        """
        pass

    def __str__(self):
        return f"{yaml.dump(self.to_dict(), default_flow_style=False)}"

    def __repr__(self):
        return self.__str__()

    def get_iface_state(self, iface_name):
        return None

    @property
    def iface_states(self):
        return self._iface_states

    @iface_states.setter
    def iface_states(self, iface_states):
        if isinstance(iface_states, list):
            self._iface_states = IfaceStates()
            self._iface_states.load_from_list(iface_states)
        elif isinstance(iface_states, dict):
            self._iface_states = IfaceStates()
            self._iface_states.load_from_list(list(iface_states.values()))
        else:
            raise Exception(
                "TODO: unexpected type(not list or dict): "
                f"{type(iface_states)} for iface_states"
            )

    def iface_state(self, iface_name):
        return self._iface_states.get(iface_name)

    @property
    def dns_state(self):
        return self._dns_state

    @dns_state.setter
    def dns_state(self, dns_state):
        self._dns_state = dns_state

    @property
    def route_state(self):
        return self._route_state

    @route_state.setter
    def route_state(self, route_state):
        self._route_state = route_state

    def merge(self, other_state):
        """
        Merged date from other_state when maritally define in self.
        """
        # self.route_state.merge(other_state.route_state)
        # self.dns_state.merge(other_state.dns_state)
        self.iface_states.merge(other_state.iface_states)

    def full_merge(self, other_state):
        """
        Merge data from other_state regardless whether they are defined in
        self or not.
        """
        # self.route_state.merge(other_state.route_state)
        # self.dns_state.merge(other_state.dns_state)
        self.iface_states.full_merge(other_state.iface_states)

    def generate_metadata(self, full_state):
        # self.route_state.merge(other_state.route_state)
        # self.dns_state.merge(other_state.dns_state)
        self.iface_states.generate_metadata(full_state.iface_states)

    def verify(self, current_state):
        pass

class DnsState:
    def to_dict(self):
        pass
    def to_dict_full(self):
        pass


class RouteState:
    def to_dict(self):
        pass

    def to_dict_full(self):
        pass
