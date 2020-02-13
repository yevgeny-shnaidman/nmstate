<!-- vim-markdown-toc GFM -->

* [Main design](#main-design)
    * [Public interfaces:](#public-interfaces)
    * [nmstate.py](#nmstatepy)
    * [common.py](#commonpy)
    * [ip.py](#ippy)
    * [plugin.py](#pluginpy)
    * [ifaces folder](#ifaces-folder)
        * [ifaces](#ifaces)
* [Plugin design](#plugin-design)

<!-- vim-markdown-toc -->

## Main design

CLI demo code `libnmstate2/ncl2`:
    * No argument means query.
    * First argument is the yaml file to set.

### Public interfaces:

 * `NmState()`
   Load plugins and hold their contexts into `NmState` object.
   And will unload them at `__del__`.

 * `NmState.load_plugin()`
   Load a `NmStatePlugin` plugin and initialize it.

 * `NmState.get()`
   Return a object of `NetState` which holds the network state.

 * `NmState.set()`
   Set the network state to match the specified `NetState` object.

### nmstate.py

 * `NmState().get()`
   Return `NetState` object representing the whole network state.

 * `NmState().set()`
   Apply the `NetState`.

### common.py

 * `default_property()`
   Decorator to generate `getter()` and `setter()` property of class with
   document. Internally, use `self._<prop_name>` for storage.

 * `BaseState`
   The base class holding the shared functions of all user facing objects of
   network states. Notes:
    * `BaseState.to_dict()`
      Export as dictionary, with metadata, without undefined properties.
      Often used internally or in verification stage.

    * `BaseState.to_dict_full()`
      Export as dictionary, without metadata, with undefined properties set
      to default value.

    * `BaseState.KEYS`
      Properties will be stored at top level of dictionary when exporting
      using `self.to_dict()` or `self.to_dict_full()`

    * `BaseState.SUB_CONFIG_KEYS` and `BaseState.SUB_CONFIG_NAME`
      Properties will be stored at second level of exporting dictionary as
      `top_dict[self.SUB_CONFIG_NAME]`.

    * `BaseState.load()`
      Load information from dictionary.

### ip.py

 * `IPState()`
 * `IPv4State()`
 * `IPv6State()`
 * `IPAddr()`

### plugin.py

Define the plugin interface. The plugin used in `NmState.load_plugin()`
should be implementation of `NmStatePlugin`.

 * `NmStatePlugin().name`
   The name of plugin

 * `NmStatePlugin().unload`
   Do plugin clean up.

 * `NmStatePlugin().capabilities`
   Bit map of below values:
    * `NmStatePlugin.CAPABILITY_IFACE`
      Can to `NmStatePlugin().get_iface_states()`
    * `NmStatePlugin.CAPABILITY_DNS`
    * `NmStatePlugin.CAPABILITY_DNS_IFACE_BAESD`
    * `NmStatePlugin.CAPABILITY_ROUTE`
    * `NmStatePlugin.CAPABILITY_ROUTE_IFACE_BASED`
    * `NmStatePlugin.CAPABILITY_ROUTE_RULE`
    * `NmStatePlugin.CAPABILITY_ROUTE_RULE_IFACE_BASED`

 * `NmStatePlugin().checkpoint_create()`
   Return a newly created checkpoint.

 * `NmStatePlugin().checkpoint_rollback(check_point)`
   Rollback the specified checkpoint.

 * `NmStatePlugin().checkpoint_destroy(check_point)`
   Destroy the specified checkpoint.

 * `NmStatePlugin().checkpoint_destroy(check_point)`
   Destroy the specified checkpoint.

 * `NmStatePlugin().get_iface_states()`

### ifaces folder

#### ifaces

## Plugin design
