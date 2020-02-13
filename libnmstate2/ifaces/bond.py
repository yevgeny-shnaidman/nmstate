from .ethernet import EthernetIfaceState
from libnmstate2.common import default_property

@default_property("mode", "unknown", "Bond mode")
@default_property("slaves", [], "The name of Bond slave interfaces")
class BondIfaceState(EthernetIfaceState):
    BOND_CONFIG_SUBTREE = "link-aggregation"

    MODE = "mode"
    SLAVES = "slaves"

    SUB_CONFIG_NAME = BOND_CONFIG_SUBTREE
    SUB_CONFIG_KEYS = [MODE, SLAVES]

    MODE_UNKNOWN = "unknown"

    def validation(self):
        pass
