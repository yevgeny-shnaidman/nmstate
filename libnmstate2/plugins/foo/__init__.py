from libnmstate2.plugin import NmStatePlugin
from libnmstate2.plugin import default_property
from libnmstate2.iface_state import IfaceState
from libnmstate2.iface_states import IfaceStates

# To use this plugin in nmstate:
#
#   from libnmstate2 import NmState
#   ns = NmState(load_default_plugins=False)
#   ns.load_plugin(FooPlugin())
#   foo_state = ns.get()
#   print(foo_state.to_dict_full())
#
# check 'libnmstate2/ncl2_foo' for detail


@default_property("foo_speed", 100, "Interface speed")
@default_property("foo_mode", "", "Interface mode")
class FooIfaceState(IfaceState):
    FOO_SPEED = "foo-speed"
    FOO_MODE = "foo-mode"
    KEYS = IfaceState.KEYS + [FOO_MODE, FOO_SPEED]

    FOO_MODE_ACTIVE = "active"
    FOO_MODE_PASSIVE = "passive"

    def __init__(self):
        super().__init__()
        self.type = "Foo"
        self.state = IfaceState.STATE_UP

    @staticmethod
    def create(name, mode, speed):
        obj = FooIfaceState()
        obj.name = name
        obj.foo_speed = speed
        obj.foo_mode = mode
        return obj


class FooPlugin(NmStatePlugin):
    def __init__(self):
        # Store your context here
        pass

    @property
    def capabilities(self):
        return NmStatePlugin.CAPABILITY_IFACE

    @property
    def name(self):
        return "Foo"

    def get_iface_states(self):
        iface_states = IfaceStates()
        iface_states.load_from_list(
            [
                FooIfaceState.create("a", FooIfaceState.FOO_MODE_ACTIVE, 1000),
                FooIfaceState.create("b", FooIfaceState.FOO_MODE_PASSIVE, 100),
            ]
        )
        return iface_states

    def apply_state(self, _merged_state, _full_state):
        # Make the state persistent
        pass

    def unload(self):
        # Release plugin resources
        pass
