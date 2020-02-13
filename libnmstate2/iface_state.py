from collections import OrderedDict
from copy import deepcopy
from functools import total_ordering

from .common import BaseState
from .common import default_property
from .ip import IPv4State
from .ip import IPv6State


@total_ordering
@default_property("name", "", "Interface name")
@default_property("type", "unknown", "Interface type")
@default_property("state", "unknown", "Interface state")
@default_property("mtu", 0, "Interface MTU(Maximum Transmission Unit)")
class IfaceState(BaseState):
    NAME = "name"
    TYPE = "type"
    MASTER = "_master"
    MASTER_TYPE = "_master_type"
    MTU = "mtu"
    STATE = "state"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    KEYS = [
        NAME,
        TYPE,
        STATE,
        MTU,
        IPV4,
        IPV6,
        MASTER,
        MASTER_TYPE,
    ]

    MTU_UNKNOWN = 0

    STATE_UP = "up"
    STATE_DOWN = "down"
    STATE_UNMANAGED = "unmanaged"
    STATE_UNKNOWN = "unknown"
    STATE_ABSENT = "absent"

    TYPE_ETHERNET = "ethernet"
    TYPE_BOND = "bond"
    TYPE_UNKNOWN = "unknown"
    TYPE_OVS_BRIDGE = "ovs-bridge"
    TYPE_OVS_INTERFACE = "ovs-interface"
    TYPE_OVS_PORT = "ovs-port"

    _SOFT_TYPES = (
        TYPE_BOND,
        TYPE_OVS_BRIDGE,
        TYPE_OVS_INTERFACE,
        TYPE_OVS_PORT,
    )

    def __init__(self):
        super().__init__()
        # Manual metadata initialization, as default_property() generated
        # name will be `__xyz` which is class internal only data.
        self._master = None
        self._master_type = None

    def is_ovs(self):
        return self.type in (
            IfaceState.TYPE_OVS_BRIDGE,
            IfaceState.TYPE_OVS_INTERFACE,
            IfaceState.TYPE_OVS_PORT,
        )

    def __eq__(self, other):
        return self is other or self.to_dict() == other.to_dict()

    def __lt__(self, other):
        return (self.name, self.type) < (other.name, other.type)

    def _clean_up_info(self, info):
        if self._master:
            info.pop(IfaceState.IPV4, None)
            info.pop(IfaceState.IPV6, None)

    @property
    def ipv4(self):
        if self._ipv4 is None:
            return IPv4State()
        return self._ipv4

    @ipv4.setter
    def ipv4(self, value):
        if isinstance(value, IPv4State):
            self._ipv4 = value
        else:
            self._ipv4 = IPv4State()
            self._ipv4.load(value)

    @property
    def ipv6(self):
        if self._ipv6 is None:
            return IPv6State()
        return self._ipv6

    @ipv6.setter
    def ipv6(self, value):
        if isinstance(value, IPv6State):
            self._ipv6 = value
        else:
            self._ipv6 = IPv6State()
            self._ipv6.load(value)

    def duplicate(self):
        return deepcopy(self)

    def is_soft(self):
        return self.type in IfaceState._SOFT_TYPES

    def is_up(self):
        return self.state == IfaceState.STATE_UP

    def is_down(self):
        return self.state == IfaceState.STATE_DOWN

    def is_absent(self):
        return self.state == IfaceState.STATE_ABSENT

    @property
    def slaves(self):
        """
        Return a list of interface name which is slave to self.
        """
        return []

    def set_master(self, master_iface_state):
        self._master = master_iface_state.name
        self._master_type = master_iface_state.type
