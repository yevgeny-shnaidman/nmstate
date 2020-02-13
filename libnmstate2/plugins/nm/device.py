from libnmstate2.iface_state import IfaceState
from .context import NM


# Naming scheme:
#   * nm_dev    Object of NM.Device
#   * nm_ac     Object of NM.ActiveConnection

_NM_IFACE_TYPE_MAP = {
    NM.DeviceType.GENERIC: IfaceState.TYPE_UNKNOWN,
    NM.DeviceType.ETHERNET: IfaceState.TYPE_ETHERNET,
    NM.DeviceType.VETH: IfaceState.TYPE_ETHERNET,
    NM.DeviceType.BOND: IfaceState.TYPE_BOND,
}


def get_dev_master(nm_dev):
    nm_ac = get_nm_ac(nm_dev)
    if nm_ac:
        master_dev = nm_ac.get_master()
        if master_dev:
            return master_dev.get_iface(), get_dev_type(master_dev)
    return "", None


def get_dev_type(nm_dev):
    return _NM_IFACE_TYPE_MAP.get(
        nm_dev.props.device_type, IfaceState.TYPE_UNKNOWN
    )


def get_nm_ac(nm_dev):
    return nm_dev.get_active_connection()


def get_dev_state(nm_dev):
    state = nm_dev.get_state()
    if NM.DeviceState.IP_CONFIG <= state <= NM.DeviceState.ACTIVATED:
        return IfaceState.STATE_UP
    if state == NM.DeviceState.UNMANAGED:
        return IfaceState.STATE_UNMANAGED
    return IfaceState.STATE_DOWN


def get_nm_ip4_profile(nm_dev):
    nm_profile = get_nm_profile(nm_dev)
    if nm_profile:
        return nm_profile.get_setting_ip4_config()
    return None


def get_nm_ip6_profile(nm_dev):
    nm_profile = get_nm_profile(nm_dev)
    if nm_profile:
        return nm_profile.get_setting_ip6_config()
    return None


def get_nm_profile(nm_dev):
    nm_ac = get_nm_ac(nm_dev)
    if nm_ac:
        return nm_ac.get_connection()
    return None
