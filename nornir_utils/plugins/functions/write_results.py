import logging
import os
import threading
from pathlib import Path
from typing import List, Optional

from nornir.core.task import AggregatedResult, MultiResult, Result

from .print_result import print_result


LOCK = threading.Lock()


def _write_results(
    result: Result,
    dirpath: str,
    attrs: Optional[List[str]] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    no_errors: bool = False,
    write_host: bool = False,
    append: bool = False,
    mode: str = "w+",
    msg: str = "",
) -> None:
    if isinstance(result, AggregatedResult):
        for host, host_data in sorted(result.items()):
            msg = result.name
            msg = "{}{}\n".format(msg, "*" * (80 - len(msg)))

            title = (
                ""
                if host_data.changed is None
                else " ** changed : {} ".format(host_data.changed)
            )
            title = "* {}{}".format(host, title)
            msg = "{}{}{}\n".format(msg, title, "*" * (80 - len(title)))

            _write_results(
                host_data,
                dirpath,
                attrs,
                failed,
                severity_level,
                no_errors,
                write_host=False,
                append=append,
                mode=mode,
                msg=msg,
            )

    elif isinstance(result, (MultiResult, Result)):
        if result.host and result.host.name:
            filepath = os.path.join(dirpath, result.host.name)
            with open(filepath, mode) as f:
                if append and Path(filepath).stat().st_size != 0:
                    f.write("\n\n")

                if msg:
                    f.write(msg)

                print_result(
                    result, attrs, failed, severity_level, no_errors, write_host, f
                )


def write_results(
    result: Result,
    dirpath: str,
    vars: Optional[List[str]] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    no_errors: bool = False,
    write_host: bool = True,
    append: bool = False,
) -> None:
    """
    Writes an object of type `nornir.core.task.Result`
    to files with hostname names

    Args:
        result: From a previous task(Result or AggregatedResult or MultiResult)
        dirpath: Directory path you want to write into
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
    Path(dirpath).mkdir(parents=True, exist_ok=True)

    mode = "a+" if append else "w+"

    LOCK.acquire()

    try:
        _write_results(
            result,
            dirpath,
            vars,
            failed,
            severity_level,
            no_errors,
            write_host,
            append,
            mode,
            msg="",
        )
    finally:
        LOCK.release()
