Module nornir_utils.plugins.functions
=====================================

Functions
---------

    
`print_result(result: nornir.core.task.Result, host: Union[str, NoneType] = None, vars: List[str] = None, failed: bool = False, severity_level: int = 20) -> NoneType`
:   Prints the :obj:`nornir.core.task.Result` from a previous task to screen
    
    Arguments:
        result: from a previous task
        host: # TODO
        vars: Which attributes you want to print
        failed: if ``True`` assume the task failed
        severity_level: Print only errors with this severity level or higher

    
`print_title(title: str) -> NoneType`
:   Helper function to print a title.[0m
[0m