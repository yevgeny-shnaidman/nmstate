from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
import logging

from libnmstate2.iface_state import IfaceState
from .context import NM
from .connection import create_connection_setting
from .ip import get_ipv4_state
from .ip import get_ipv6_state
from .ip import create_ipv4_setting
from .ip import create_ipv6_setting
from .device import get_dev_type
from .device import get_dev_state
from .device import get_dev_master

# Naming scheme:
#   * nm_dev    Object of NM.Device
#   * nm_ac     Object of NM.ActiveConnection


class NmIfacePlugin(metaclass=ABCMeta):
    def __init__(self, ctx):
        self.ctx = ctx

    def unload(self):
        self.ctx = None

    @abstractproperty
    def supported_iface_types(self):
        pass

    @abstractmethod
    def get_iface_state(self, parent_iface_state):
        pass


class BaseIfacePlugin:
    @staticmethod
    def create_settings(ctx, iface_state, base_profile):
        connection_setting = create_connection_setting(iface_state)
        ip4_setting = create_ipv4_setting(
            iface_state.ipv4,
            base_profile.nm_profile.get_setting_ip4_config()
            if base_profile
            else None,
        )
        ip6_setting = create_ipv6_setting(
            iface_state.ipv6,
            base_profile.nm_profile.get_setting_ip6_config()
            if base_profile
            else None,
        )
        return [connection_setting, ip4_setting, ip6_setting]

    @staticmethod
    def get_iface_states(ctx):
        iface_states = []
        for nm_dev in ctx.client.get_devices():
            name = nm_dev.get_iface()
            if not name:
                logging.warning(
                    "Got NULL named NM.Device: "
                    f"Unique Device Identifier: {nm_dev.get_udi()}"
                )
                continue
            type = get_dev_type(nm_dev)
            if name == "lo" and type == IfaceState.TYPE_UNKNOWN:
                continue
            if type == IfaceState.TYPE_UNKNOWN:
                logging.warning(
                    "Interface Unsupported interface type: "
                    f"type {nm_dev.props.device_type} on interface {name}"
                )
            iface_state = IfaceState()
            iface_state.name = name
            iface_state.type = type
            iface_state.mtu = nm_dev.get_mtu()
            iface_state.state = get_dev_state(nm_dev)
            (iface_state.master, iface_state.master_type,) = get_dev_master(
                nm_dev
            )
            iface_state.ipv4 = get_ipv4_state(nm_dev)
            iface_state.ipv6 = get_ipv6_state(nm_dev)

            iface_states.append(iface_state)
        return iface_states
