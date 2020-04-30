Module nornir_utils.plugins.processors
======================================

Sub-modules
-----------
* nornir_utils.plugins.processors.print_result

Classes
-------

`PrintResult(severity_level: int = 20)`
:   Prints information about the task execution on screen.
    
    Arguments:
        severity_level: Print only results with this severity level or higher

    ### Methods

    `subtask_instance_completed(self, task: nornir.core.task.Task, host: nornir.core.inventory.Host, result: nornir.core.task.MultiResult) -> NoneType`
    :

    `subtask_instance_started(self, task: nornir.core.task.Task, host: nornir.core.inventory.Host) -> NoneType`
    :

    `task_completed(self, task: nornir.core.task.Task, result: nornir.core.task.AggregatedResult) -> NoneType`
    :

    `task_instance_completed(self, task: nornir.core.task.Task, host: nornir.core.inventory.Host, results: nornir.core.task.MultiResult) -> NoneType`
    :

    `task_instance_started(self, task: nornir.core.task.Task, host: nornir.core.inventory.Host) -> NoneType`
    :

    `task_started(self, task: nornir.core.task.Task) -> NoneType`
    :[0m
[0m