import logging
import os
import threading
from pathlib import Path
from typing import List

from nornir.core.task import Result

from .print_result import print_result


LOCK = threading.Lock()


def write_result(
    result: Result,
    filepath: str,
    vars: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    no_errors: bool = False,
    write_host: bool = True,
    append: bool = False,
) -> None:
    """
    Writes an object of type `nornir.core.task.Result` to file

    Args:
        result: From a previous task
        (Result or AggregatedResult or MultiResult)
        filepath: Filepath you want to write the result
        vars: Which attributes you want to write
        (see ``class Result`` attributes)
        failed: If ``True`` assume the task failed
        severity_level: Write only errors with this severity level or higher
        no_errors: Don't write results with exceptions
        write_host: Write hostname to file for MultiResult and Result objects
        append: "a+" if ``True`` or "w+" if ``False``

    Returns:
        N/A

    Raises:
        N/A
    """

    dirname = os.path.dirname(filepath)
    Path(dirname).mkdir(parents=True, exist_ok=True)

    mode = "a+" if append else "w+"

    LOCK.acquire()

    try:
        with open(filepath, mode=mode) as f:
            if append and Path(filepath).stat().st_size != 0:
                f.write("\n\n")
            print_result(result, vars, failed, severity_level, no_errors, write_host, f)
    finally:
        LOCK.release()
