import logging

from .context import NM
from .device import get_nm_ac
from .device import get_nm_profile
from .iface_plugin import BaseIfacePlugin
from .ip import is_ipv4_dynamic
from .ip import is_ipv6_dynamic


class Profile:
    def __init__(self, ctx, nm_dev, nm_profile, iface_state):
        self._ctx = ctx
        self._nm_profile = nm_profile
        self._nm_dev = nm_dev
        self._iface_state = iface_state
        self._nm_ac = None
        # self._proxy_nm_profile = None     # For OVS
        self._ac_handlers = set()
        self._dev_handlers = set()

    @property
    def nm_profile(self):
        return self._nm_profile

    @property
    def _connection(self):
        return f"{self._nm_profile.get_id()} {self._nm_profile.get_uuid()}"

    @staticmethod
    def create(ctx, iface_state, base_profile, plugins):
        profile = Profile(
            ctx,
            ctx.get_nm_dev(iface_state),
            NM.SimpleConnection.new(),
            iface_state,
        )
        settings = BaseIfacePlugin.create_settings(
            ctx, iface_state, base_profile
        )
        for plugin in plugins:
            if iface_state.type in plugin.supported_iface_types:
                settings.extend(
                    plugin.create_settings(iface_state, base_profile)
                )
        for setting in settings:
            profile._nm_profile.add_setting(setting)
        return profile

    @staticmethod
    def load_from_iface_state(ctx, iface_state):
        nm_dev = ctx.get_nm_dev(iface_state)
        if nm_dev:
            cur_nm_profile = get_nm_profile(nm_dev)
            if cur_nm_profile:
                return Profile(ctx, nm_dev, cur_nm_profile, iface_state)
        return None

    def add(self):
        # TODO: Remove all existing for the same device.
        action = f"add_connection2 {self._connection}"
        self._ctx.register_async(action)
        user_data = action
        flags = (
            NM.SettingsAddConnection2Flags.BLOCK_AUTOCONNECT
            | NM.SettingsAddConnection2Flags.TO_DISK
        )

        cancellable = None  # TODO
        args = None
        ignore_out_result = False
        self._ctx.client.add_connection2(
            self._nm_profile.to_dbus(NM.ConnectionSerializationFlags.ALL),
            flags,
            args,
            ignore_out_result,
            cancellable,
            self._add_connection2_callback,
            user_data,
        )

    def _add_connection2_callback(self, src_object, result, action):
        self._ctx.finish_async(action)
        try:
            profile = src_object.add_connection2_finish(result)[0]
        except Exception as e:
            # TODO: Wrap Nm error into NmStateError.
            self._ctx.error = e
            return

        if profile is None:
            self._ctx.error = Exception(
                f"Connection adding failed on {self._connection}: error=unknown"
            )
        else:
            devname = profile.get_interface_name()
            new_nm_profile = self._ctx.client.get_connection_by_uuid(
                self._nm_profile.get_uuid()
            )
            self._nm_profile = new_nm_profile
            logging.debug(f"Connection adding succeeded: {self._connection}")

    def delete(self):
        self.deactivate()
        pass

    def update(self):
        pass

    def activate(self):
        action = f"activate_connection_async {self._connection}"
        self._ctx.register_async(action)

        specific_object = None
        cancellable = None  # TODO
        user_data = action
        self._ctx.client.activate_connection_async(
            self._nm_profile,
            self._nm_dev,
            specific_object,
            cancellable,
            self._active_connection_callback,
            user_data,
        )

    def _active_connection_callback(self, nm_client, result, action):
        try:
            nm_ac = nm_client.activate_connection_finish(result)
        except Exception as e:
            self._ctx.finish_async(action)
            self._ctx.error = e
            return

        if nm_ac is None:
            self._ctx.finish_async(action)
            error_msg = f"Connection activation failed on {self._connection}"
            logging.error(error_msg)
            self._ctx.error = Exception(error_msg)
            return

        self._nm_ac = nm_ac
        self._nm_dev = self._ctx.get_nm_dev(self._iface_state)

        if self._is_activated():
            self._ctx.finish_async(action)
            logging.debug(f"Connection {self._connection} is activated")
            return
        elif self._is_activating():
            logging.debug(
                f"Connection {self._connection} is activating: "
                f"{self._nm_ac.get_state()}"
                f"{self._nm_dev.get_state()}"
            )
            self._wait_activation(action)
        else:
            self._ctx.finish_async(action)
            nm_dev = self._ctx.get_nm_dev(self._iface_state)
            if nm_dev:
                error_msg = (
                    f"Connection {self._connection} failed: "
                    f"state={nm_ac.get_state()} reason={nm_ac.get_state_reason()} "
                    f"dev_state={nm_dev.get_state()} "
                    f"dev_reason={nm_dev.get_state_reason()}"
                )
            else:
                error_msg = (
                    f"Connection {self._connection} failed: "
                    f"state={nm_ac.get_state()} "
                    f"reason={nm_ac.get_state_reason()} dev=None"
                )
            logging.error(error_msg)
            self._ctx.error = Exception(error_msg)

    def _wait_activation(self, action):
        self._ac_handlers.add(
            self._nm_ac.connect(
                "state-changed", self._ac_state_change_callback, action
            )
        )
        self._ac_handlers.add(
            self._nm_ac.connect(
                "notify::state-flags",
                self._ac_state_flags_change_callback,
                action,
            )
        )
        self._dev_handlers.add(
            self._nm_dev.connect(
                "state-changed", self._dev_state_change_callback, action
            )
        )

    def _ac_state_change_callback(self, _nm_act_con, _state, _reason, action):
        cur_nm_dev = self._ctx.get_nm_dev(self._iface_state)
        if cur_nm_dev and cur_nm_dev != self._nm_dev:
            logging.debug(f"NM.Device of profile {self._connection} changed")
            self._remove_dev_handlers()
            self._nm_dev = cur_nm_dev

        cur_nm_ac = get_nm_ac(self._nm_dev)
        if cur_nm_ac and cur_nm_ac != self._nm_ac:
            logging.debug(
                f"NM.ActiveConnection of profile {self._connection} changed"
            )
            self._remove_ac_handlers()
            self._nm_ac = cur_nm_ac
            self._wait_activation(action)
        if self._is_activated():
            self._remove_ac_handlers()
            self._remove_dev_handlers()
            self._ctx.finish_async(action)
            logging.debug(f"Connection {self._connection} is activated")
            return
        elif self._is_activating():
            pass
        else:
            self._ctx.finish_async(action)
            if self._nm_dev:
                error_msg = (
                    f"Connection {self._connection} failed: "
                    f"state={self._nm_ac.get_state()} "
                    f"reason={self._nm_ac.get_state_reason()} "
                    f"dev_state={self._nm_dev.get_state()} "
                    f"dev_reason={self._nm_dev.get_state_reason()}"
                )
            else:
                error_msg = (
                    f"Connection {self._connection} failed: "
                    f"state={self._nm_ac.get_state()} "
                    f"reason={self._nm_ac.get_state_reason()} dev=None"
                )
            self._ctx.error = Exception(error_msg)
            logging.error(error_msg)

    def _ac_state_flags_change_callback(self, _nm_act_con, _state, action):
        self._ac_state_change_callback(None, None, None, action)

    def _dev_state_change_callback(
        self, _dev, _new_state, _old_state, _reason, action
    ):
        self._ac_state_change_callback(None, None, None, action)

    def _remove_dev_handlers(self):
        for handler_id in self._dev_handlers:
            self._nm_dev.handler_disconnect(handler_id)
        self._dev_handlers = set()

    def _remove_ac_handlers(self):
        for handler_id in self._ac_handlers:
            self._nm_ac.handler_disconnect(handler_id)
        self._ac_handlers = set()

    def deactivate(self):
        pass

    def _is_activated(self):
        if not self._nm_ac or not self._nm_dev:
            return False

        state = self._nm_ac.get_state()
        if state == NM.ActiveConnectionState.ACTIVATED:
            return True
        elif state == NM.ActiveConnectionState.ACTIVATING:
            ac_state_flags = self._nm_ac.get_state_flags()
            nm_flags = NM.ActivationStateFlags
            ip4_is_dynamic = is_ipv4_dynamic(self._nm_ac)
            ip6_is_dynamic = is_ipv6_dynamic(self._nm_ac)
            if (
                ac_state_flags & nm_flags.IS_MASTER
                or (ip4_is_dynamic and ac_state_flags & nm_flags.IP6_READY)
                or (ip6_is_dynamic and ac_state_flags & nm_flags.IP4_READY)
                or (ip4_is_dynamic and ip6_is_dynamic)
            ):
                # For interface meet any condition below will be
                # treated as activated when reach IP_CONFIG state:
                #   * Is master device.
                #   * DHCPv4 enabled with IP6_READY flag.
                #   * DHCPv6/Autoconf with IP4_READY flag.
                #   * DHCPv4 enabled with DHCPv6/Autoconf enabled.
                return (
                    NM.DeviceState.IP_CONFIG
                    <= self._nm_dev.get_state()
                    <= NM.DeviceState.ACTIVATED
                )

        return False

    def _is_activating(self):
        if not self._nm_ac or not self._nm_dev:
            return True
        if (
            self._nm_dev.get_state_reason()
            == NM.DeviceStateReason.NEW_ACTIVATION
        ):
            return True

        return (
            self._nm_ac.get_state() == NM.ActiveConnectionState.ACTIVATING
            and not self._is_activated()
        )
