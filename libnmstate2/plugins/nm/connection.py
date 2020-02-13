from libnmstate2.iface_state import IfaceState

from .context import NM

NM_CONNECTION_TYPE_MAP = {
    IfaceState.TYPE_ETHERNET: NM.SETTING_WIRED_SETTING_NAME,
    IfaceState.TYPE_BOND: NM.SETTING_BOND_SETTING_NAME,
}

def create_connection_setting(iface_state):
    con_setting = NM.SettingConnection.new()
    con_setting.props.id = iface_state.name
    con_setting.props.interface_name = iface_state.name
    con_setting.props.uuid = NM.utils_uuid_generate()
    con_setting.props.type = NM_CONNECTION_TYPE_MAP[iface_state.type]
    con_setting.props.autoconnect = True
    con_setting.props.autoconnect_slaves = (
        NM.SettingConnectionAutoconnectSlaves.YES
    )
    con_setting.props.master = iface_state._master
    con_setting.props.slave_type = iface_state._master_type
    return con_setting
