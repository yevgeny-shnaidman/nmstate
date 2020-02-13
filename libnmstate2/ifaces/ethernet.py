from libnmstate2.iface_state import IfaceState
from libnmstate2.common import default_property


@default_property("mac_address", "00:00:00:00:00:00", "MAC address of interface")
class EthernetIfaceState(IfaceState):
    MAC = "mac-address"

    KEYS = IfaceState.KEYS + [MAC]

    MAC_UNKNOWN = "00:00:00:00:00:00"

    @property
    def mac(self):
        return self._mac_address

    @mac.setter
    def mac(self, mac):
        self._mac_address = mac
