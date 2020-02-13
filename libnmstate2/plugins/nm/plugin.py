# Naming scheme:
#   * profile: NM.RemoteConnection related on-disk configuration
#   * setting: NM.Setting related on-disk configuration

from libnmstate2.plugin import NmStatePlugin

from .bond import BondIfacePlugin
from .context import NmContext
from .ethernet import EthernetIfacePlugin
from .device import get_nm_profile
from .iface_plugin import BaseIfacePlugin
from .profile import Profile


class NetworkManagerPlugin(NmStatePlugin):
    @property
    def name(self):
        return "NetworkManager"

    def __init__(self):
        self.ctx = NmContext()
        self._iface_plugins = [
            EthernetIfacePlugin(self.ctx),
            BondIfacePlugin(self.ctx),
        ]

    def checkpoint_create(self):
        pass

    def checkpoint_rollback(self):
        pass

    def checkpoint_destroy(self):
        pass

    def apply_state(self, merged_state, _full_state):
        """
        * Create NM.RemoteConnection
        * Wait mainloop finish all works.
        * Activation.
        * Wait mainloop finish all works.
        """
        active_profiles = []
        for iface_state in merged_state.iface_states:
            cur_profile = Profile.load_from_iface_state(self.ctx, iface_state)
            if iface_state.is_down():
                cur_profile.deactivate()
                continue
            if iface_state.is_absent():
                cur_profile.delete()
                continue
            new_profile = Profile.create(
                self.ctx, iface_state, cur_profile, self._iface_plugins
            )
            if cur_profile:
                cur_profile.update(new_profile)
            else:
                new_profile.add()
            active_profiles.append(new_profile)
        error = self.ctx.wait_all_finish()
        if error:
            raise error
        for profile in active_profiles:
            profile.activate()
        error = self.ctx.wait_all_finish()
        if error:
            raise error

    @property
    def capabilities(self):
        return (
            NmStatePlugin.CAPABILITY_IFACE
            & NmStatePlugin.CAPABILITY_CHECKPOINT
        )

    def get_iface_states(self):
        iface_states = []
        base_iface_states = BaseIfacePlugin.get_iface_states(self.ctx)
        for iface_state in base_iface_states:
            for plugin in self._iface_plugins:
                if iface_state.type in plugin.supported_iface_types:
                    iface_states.append(plugin.get_iface_state(iface_state))

        return iface_states

    def unload(self):
        for iface_plugin in self._iface_plugins:
            iface_plugin.unload()
        self.ctx.clean()
