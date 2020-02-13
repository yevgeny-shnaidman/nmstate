import datetime
import logging

import gi

gi.require_version("NM", "1.0")
from gi.repository import GLib, NM

TIMEOUT_PER_ACTION = 10      # TODO: Wait STP is still required?


class NmContext:
    def __init__(self):
        self._client = NM.Client.new(None)
        self._context = self.client.get_main_context()
        self._async_actions = {}
        self.error = None

    def get_nm_dev(self, iface_state):
        if not self._client:
            raise Exception(f"Got NULL client for get_nm_dev(): {iface_state}")

        if iface_state.is_ovs():
            # TODO: Search in self.client.get_devices()
            return None
        else:
            return self.client.get_device_by_iface(iface_state.name)

    @property
    def client(self):
        return self._client

    def __del__(self):
        self.clean()

    def clean(self):
        if self.client:
            is_done = []
            self.client.get_context_busy_watcher().weak_ref(
                lambda: is_done.append(1)
            )

            self._client = None

            while self._context.iteration(False):
                pass

            if not is_done:
                logging.debug(
                    "context.iteration() does not delete "
                    "the context_busy_watcher, "
                    "waiting 50 milliseconds"
                )
                timeout_source = GLib.timeout_source_new(50)
                try:
                    timeout_source.set_callback(lambda x: is_done.append(1))
                    timeout_source.attach(context)
                    while not is_done:
                        self._context.iteration(True)
                finally:
                    timeout_source.destroy()

    def register_async(self, action):
        """
        Register action(string) to wait list.
        """
        logging.debug(f"Async action '{action}' started")
        self._async_actions[action] = datetime.datetime.now()

    def finish_async(self, action):
        """
        Mark action(string) as finished.
        """
        logging.debug(f"Async action '{action}' finished")
        self._async_actions.pop(action, None)

    def _is_any_action_timeout(self):
        now = datetime.datetime.now()
        timeout = datetime.timedelta(seconds=TIMEOUT_PER_ACTION)
        for action, start_time in self._async_actions.items():
            if (now - start_time) > timeout:
                self.error = Exception(f"Action '{action}' timeout")
                return True
        return False

    def _action_all_finished(self):
        return len(self._async_actions) == 0

    def wait_all_finish(self):
        # The GLib.MainContext.iteration(True) might hang tile next
        # NM event. Use timeout source to limit the blocking time to
        # 1 second(1000 milliseconds).
        def _timeout_cb(_):
            return True

        timeout_source = GLib.timeout_source_new(1000)
        timeout_source.set_callback(_timeout_cb)
        timeout_source.attach(self._context)

        while (
            not self._action_all_finished()
            and not self._is_any_action_timeout()
            and not self.error
        ):
            self._context.iteration(True)

        return self.error
