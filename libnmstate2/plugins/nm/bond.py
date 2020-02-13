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
from libnmstate2.ifaces import BondIfaceState

from .context import NM
from .ethernet import EthernetIfacePlugin
from .iface_plugin import NmIfacePlugin


class BondIfacePlugin(NmIfacePlugin):
    @property
    def supported_iface_types(self):
        return [IfaceState.TYPE_BOND]

    def get_iface_state(self, parent_iface_state):
        nm_dev = self.ctx.get_nm_dev(parent_iface_state)
        wire_plugin = EthernetIfacePlugin(self.ctx)
        eth_iface_state = wire_plugin.get_iface_state(parent_iface_state)

        iface_state = BondIfaceState()
        iface_state.load(eth_iface_state.to_dict())
        iface_state.slaves = [d.get_iface() for d in nm_dev.get_slaves()]

        return iface_state

    def create_settings(self, iface_state, base_profile):
        wire_plugin = EthernetIfacePlugin(self.ctx)
        nm_settings = wire_plugin.create_settings(
            iface_state, base_profile
        )
        nm_bond_setting = NM.SettingBond.new()
        nm_bond_setting.add_option("mode", iface_state.mode)
        nm_settings.append(nm_bond_setting)
        return nm_settings
