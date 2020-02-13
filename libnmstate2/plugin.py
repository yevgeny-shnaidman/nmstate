#
# Copyright (c) 2019 Red Hat, Inc.
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

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty

from .common import default_property


class NmStatePlugin(metaclass=ABCMeta):
    CAPABILITY_IFACE = 1
    CAPABILITY_DNS = 1 << 5
    CAPABILITY_DNS_IFACE_BAESD = 1 << 6
    CAPABILITY_ROUTE = 1 << 10
    CAPABILITY_ROUTE_IFACE_BASED = 1 << 11
    CAPABILITY_ROUTE_RULE = 1 << 15
    CAPABILITY_ROUTE_RULE_IFACE_BASED = 1 << 16
    CAPABILITY_CHECKPOINT = 1 << 20

    @abstractmethod
    def unload(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def capabilities(self):
        pass

    @abstractmethod
    def get_iface_states(self):
        """
        Return a IfaceStates object.
        """
        pass

    def checkpoint_create(self, checkpoing):
        """
        Create a checkpoint
        """
        pass

    def checkpoint_rollback(self, checkpoing):
        """
        Rollback the checkpoint
        """
        pass

    def checkpoint_destroy(self, checkpoing):
        """
        Destroy the checkpoint
        """
        pass


__all__ = ["default_property", "NmStatePlugin"]
