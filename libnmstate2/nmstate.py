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

import yaml
import os
import logging
import copy


from .plugin import NmStatePlugin
from .plugins.nm import NetworkManagerPlugin
from .net_state import NetState


class NmState(object):
    def __init__(self, load_default_plugins=True):
        self._plugins = {}
        self._iface_plugins = []
        self._dns_plugin = None
        self._route_plugin = None
        # TODO: Add support of route rule
        if load_default_plugins:
            self.load_plugin(NetworkManagerPlugin())

    def load_plugin(self, plugin):
        self._plugins[plugin.name] = plugin
        if plugin.capabilities & NmStatePlugin.CAPABILITY_IFACE:
            self._iface_plugins.append(plugin)
        if plugin.capabilities & NmStatePlugin.CAPABILITY_DNS:
            if self._dns_plugin:
                raise Exception("TODO: duplicate dns_plugin")
            self._dns_plugin = plugin
        if plugin.capabilities & NmStatePlugin.CAPABILITY_ROUTE:
            if self._route_plugin:
                raise Exception("TODO: duplicate route_plugin")
            self._route_plugin = plugin

    def __del__(self):
        for plugin in self._plugins.values():
            plugin.unload()
        self._plugins = {}
        self._iface_plugins = []
        self._dns_plugins = []
        self._route_plugins = []

    def _get_iface_states(self):
        iface_states = []
        for plugin in self._iface_plugins:
            if plugin.get_iface_states:
                iface_states.extend(plugin.get_iface_states())
        return iface_states

    def _get_dns_states(self):
        if self._dns_plugin:
            return self._dns_plugin.get_dns_state()
        return None

    def _get_route_states(self):
        if self._route_plugin:
            return self._route_plugin.get_route_state()
        return None

    def get(self):
        net_state = NetState()
        net_state.iface_states = self._get_iface_states()
        net_state.dns_state = self._get_dns_states()
        net_state.route_state = self._get_route_states()
        return net_state

    def set(self, desired_state, verify_change=True):
        """
        Apply specified NetState and fallback to original state if failed.
        """
        current_state = self.get()
        full_state = copy.deepcopy(desired_state)
        full_state.full_merge(current_state)
        merged_state = copy.deepcopy(desired_state)
        merged_state.merge(current_state)
        merged_state.generate_metadata(full_state)
        plugin_checkpoints = {}
        for plugin_name, plugin in self._plugins.items():
            if not plugin.capabilities & NmStatePlugin.CAPABILITY_CHECKPOINT:
                continue
            checkpoint = plugin.checkpoint_create()
            if checkpoint:
                plugin_checkpoints[plugin_name] = plugin.checkpoint_create()

        try:
            for plugin in self._plugins.values():
                plugin.apply_state(merged_state, full_state)

            if verify_change:
                new_state = self.get()
                desired_state.verify(new_state)
        except Exception as e:
            for plugin_name, checkpoint in plugin_checkpoints.items():
                try:
                    self._plugins[plugin_name].checkpoint_rollback(checkpoint)
                    self._plugins[plugin_name] = None
                except Exception as rollback_failure:
                    logging.warning(
                        "Exception happened during checkpoint rollback "
                        f"{rollback_failure}"
                    )
            raise e

        for plugin_name, checkpoint in plugin_checkpoints.items():
            self._plugins[plugin_name].checkpoint_destroy(checkpoint)
            self._plugins[plugin_name] = None


class RouteState:
    def to_dict(self):
        pass


class RouteRuleState:
    def to_dict(self):
        pass
