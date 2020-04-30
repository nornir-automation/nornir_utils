Module nornir_utils.plugins.inventory
=====================================

Sub-modules
-----------
* nornir_utils.plugins.inventory.simple

Classes
-------

`SimpleInventory(host_file: str = 'hosts.yaml', group_file: str = 'groups.yaml', defaults_file: str = 'defaults.yaml')`
:   SimpleInventory is an inventory plugin that loads data from YAML files.
    The YAML files follow the same structure as the native objects
    
    Args:
        host_file: path to file with hosts definition
        group_file: path to file with groups definition. If
            it doesn't exist it will be skipped
        defaults_file: path to file with defaults definition.
            If it doesn't exist it will be skipped

    ### Methods

    `load(self) -> nornir.core.inventory.Inventory`
    :
