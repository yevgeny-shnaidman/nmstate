import socket

from libnmstate2.ip import IPAddr
from libnmstate2.ip import IPv4State
from libnmstate2.ip import IPv6State

from .device import get_nm_ac
from .device import get_nm_ip4_profile
from .device import get_nm_ip6_profile
from .context import NM

# Naming scheme:
#   * ip_state          Object of IPState
#   * nm_ip_profile     Object of NM.SettingIPConfig, the on-disk config
#   * nm_nm_ip_config      Object of NM.IPConfig


def get_ipv4_state(nm_dev):
    ip_state = IPv4State()
    return _get_ip_state(nm_dev, ip_state)


def get_ipv6_state(nm_dev):
    ip_state = IPv6State()
    return _get_ip_state(nm_dev, ip_state)


def _get_ip_state(nm_dev, ip_state):
    """
    Currently(NM 1.22) cannot show the runtime state of on-going DHCP,
    read on-disk configuration as reluctant workaround.
    """
    nm_ac = get_nm_ac(nm_dev)
    if not nm_ac:
        return ip_state
    if ip_state.is_ipv6():
        nm_ip_config = nm_ac.get_ip6_config()
        nm_ip_profile = get_nm_ip6_profile(nm_dev)
        ip_state.dhcp = _is_dhcpv6(nm_ip_profile)
        ip_state.autoconf = _is_autoconf(nm_ip_profile)
        # When IPv6 method is LINK_LOCAL, treat it as IPv6 enabled.
        if _is_ipv6_link_local_only(nm_ip_profile):
            ip_state.enabled = True
    else:
        nm_ip_config = nm_ac.get_ip4_config()
        nm_ip_profile = get_nm_ip4_profile(nm_dev)
        ip_state.dhcp = _is_dhcpv4(nm_ip_profile)
    if nm_ip_config:
        ip_state.addresses = _get_address(nm_ip_config)
        if ip_state.addresses:
            ip_state.enabled = True

    if ip_state.is_dynamic():
        ip_state.enabled = True
        ip_state.auto_routes = not nm_ip_profile.props.ignore_auto_routes
        ip_state.auto_gateways = not nm_ip_profile.props.never_default
        ip_state.auto_dns = not nm_ip_profile.props.ignore_auto_dns

    return ip_state


def _get_address(nm_ip_config):
    addresses = []
    if nm_ip_config:
        for nm_addr in nm_ip_config.get_addresses():
            if nm_addr:
                addresses.append(_nm_addr_to_nmstate(nm_addr))
    return addresses


def _nm_addr_to_nmstate(nm_addr):
    ip_addr = IPAddr()
    ip_addr.ip = nm_addr.get_address()
    ip_addr.prefix_length = nm_addr.get_prefix()
    return ip_addr


def _is_dhcpv6(nm_ip_profile):
    if nm_ip_profile:
        return nm_ip_profile.get_method() in (
            NM.SETTING_IP6_CONFIG_METHOD_AUTO,
            NM.SETTING_IP6_CONFIG_METHOD_DHCP,
        )
    else:
        return False


def _is_autoconf(nm_ip_profile):
    if nm_ip_profile:
        return nm_ip_profile.get_method() == NM.SETTING_IP6_CONFIG_METHOD_AUTO
    else:
        return False


def _is_ipv6_link_local_only(nm_ip_profile):
    if nm_ip_profile:
        return (
            nm_ip_profile.get_method()
            == NM.SETTING_IP6_CONFIG_METHOD_LINK_LOCAL
        )
    else:
        return False


def _is_dhcpv4(nm_ip_profile):
    if nm_ip_profile:
        return nm_ip_profile.get_method() == NM.SETTING_IP4_CONFIG_METHOD_AUTO
    else:
        return False


def create_ipv4_setting(ip_state, base_setting):
    return _create_ip_setting(ip_state, base_setting)


def create_ipv6_setting(ip_state, base_setting):
    return _create_ip_setting(ip_state, base_setting)


def _create_ip_setting(ip_state, base_setting):
    ip_setting = None
    if base_setting and ip_state.enabled:
        ip_setting = base_con_profile.get_setting_ip4_config()
        if ip_setting:
            ip_setting = ip_setting.duplicate()
            ip_setting.clear_addresses()
            ip_setting.props.ignore_auto_routes = False
            ip_setting.props.never_default = False
            ip_setting.props.ignore_auto_dns = False
            ip_setting.props.gateway = None

    if not ip_setting:
        if ip_state.is_ipv6():
            ip_setting = NM.SettingIP6Config.new()
        else:
            ip_setting = NM.SettingIP4Config.new()

    if ip_state.is_ipv6():
        _set_dynamic_ipv6_mac_based(ip_setting)
        _set_ipv6_method(ip_state, ip_setting)
    else:
        _set_dhcpv4_mac_based(ip_setting)
        _set_ipv4_method(ip_state, ip_setting)

    return ip_setting


def _set_dynamic_ipv6_mac_based(ip_setting):
    # Ensure IPv6 RA and DHCPv6 is based on MAC address only
    ip_setting.props.addr_gen_mode = NM.SettingIP6ConfigAddrGenMode.EUI64
    ip_setting.props.dhcp_duid = "ll"
    ip_setting.props.dhcp_iaid = "mac"


def _set_dhcpv4_mac_based(ip_setting):
    ip_setting.props.dhcp_client_id = "mac"


def _set_ipv4_method(ip_state, ip_setting):
    if not ip_state.enabled:
        ip_setting.props.method = NM.SETTING_IP4_CONFIG_METHOD_DISABLED
    elif ip_state.dhcp:
        ip_setting.props.method = NM.SETTING_IP4_CONFIG_METHOD_AUTO
        _set_dynamic_option(ip_state, ip_setting)
    elif ip_state.addresses:
        ip_setting.props.method = NM.SETTING_IP4_CONFIG_METHOD_MANUAL
        _set_ip_addresses(ip_state.addresses, ip_setting)
    else:
        ip_setting.props.method = NM.SETTING_IP4_CONFIG_METHOD_DISABLED
        _set_ip_addresses(ip_state.addresses, ip_setting)


def _set_ipv6_method(ip_state, ip_setting):
    if not ip_state.enabled:
        ip_setting.props.method = NM.SETTING_IP6_CONFIG_METHOD_DISABLED
    elif ip_state.dhcp and ip_state.autoconf:
        ip_setting.props.method = NM.SETTING_IP6_CONFIG_METHOD_AUTO
        _set_dynamic_option(ip_state, ip_setting)
    elif ip_state.dhcp and not ip_state.autoconf:
        ip_setting.props.method = NM.SETTING_IP6_CONFIG_METHOD_DHCP
        _set_dynamic_option(ip_state, ip_setting)
    elif not ip_state.dhcp and ip_state.autoconf:
        raise Exception("Autoconf without DHCP is not supported yet")
    elif ip_state.addresses:
        ip_setting.props.method = NM.SETTING_IP6_CONFIG_METHOD_MANUAL
        _set_ip_addresses(ip_state.addresses, ip_setting)
    else:
        ip_setting.props.method = NM.SETTING_IP6_CONFIG_METHOD_LINK_LOCAL


def _set_ip_addresses(ip_addrs, ip_setting):
    for ip_addr in ip_addrs:
        nm_addr = nmclient.NM.IPAddress.new(
            socket.AF_INET6 if IpAddr.is_ipv6(ip_addr.ip) else socket.AF_INET,
            address.ip,
            address.prefix_length,
        )
        ip_setting.add_address(nm_addr)


def _set_dynamic_option(ip_state, ip_setting):
    ip_setting.props.ignore_auto_routes = not ip_state.auto_routes
    ip_setting.props.never_default = not ip_state.auto_gateway
    ip_setting.props.ignore_auto_dns = not ip_state.auto_dns


def is_ipv4_dynamic(nm_ac):
    profile = nm_ac.get_connection()
    if profile:
        ip_profile = profile.get_setting_ip4_config()
        if ip_profile:
            return ip_profile.props.method == NM.SETTING_IP4_CONFIG_METHOD_AUTO
    return False


def is_ipv6_dynamic(nm_ac):
    profile = nm_ac.get_connection()
    if profile:
        ip_profile = profile.get_setting_ip6_config()
        if ip_profile:
            return ip_profile.props.method in (
                NM.SETTING_IP6_CONFIG_METHOD_AUTO,
                NM.SETTING_IP6_CONFIG_METHOD_DHCP,
            )
    return False
