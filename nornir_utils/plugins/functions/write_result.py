import os
import logging
import threading
import json
from pathlib import Path
from typing import List, IO, AnyStr
from nornir_utils.plugins.tasks.files.write_file import _generate_diff
from nornir.core.task import AggregatedResult, MultiResult, Result


LOCK = threading.Lock()


def _write_individual_result(
    result: Result,
    io: IO[AnyStr],
    attrs: List[str],
    failed: bool,
    severity_level: int,
    task_group: bool = False,
    write_host: bool = False,
    no_errors: bool = False,
    content: List[str] = [],
) -> List[str]:

    # ignore results with a specific severity_level
    if result.severity_level < severity_level:
        return content

    # ignore results with errors
    if no_errors:
        if result.exception:
            return content

    subtitle = (
        "" if result.changed is None else " ** changed : {} ".format(result.changed)
    )
    level_name = logging.getLevelName(result.severity_level)
    symbol = "v" if task_group else "-"
    host = (
        f"{result.host.name}: "
        if (write_host and result.host and result.host.name)
        else ""
    )
    msg = "{} {}{}{}".format(symbol * 4, host, result.name, subtitle)
    content.append("{}{} {}".format(msg, symbol * (80 - len(msg)), level_name))
    for attribute in attrs:
        x = getattr(result, attribute, "")
        if isinstance(x, BaseException):
            # for consistency between py3.6 and py3.7
            content.append(f"{x.__class__.__name__}{x.args}")
        elif x and not isinstance(x, str):
            try:
                content.append(
                    json.dumps(x, indent=2, ensure_ascii=False).encode("utf-8").decode()
                )
            except TypeError:
                content.append(str(x))
        elif x:
            content.append(x)

    return content


def _write_result(
    result: Result,
    io: IO[AnyStr],
    attrs: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    write_host: bool = False,
    no_errors: bool = False,
    content: List[str] = [],
) -> List[str]:

    attrs = attrs or ["diff", "result", "stdout"]
    if isinstance(attrs, str):
        attrs = [attrs]

    if isinstance(result, AggregatedResult):
        for host_data in result.values():
            content = _write_result(
                host_data,
                io,
                attrs,
                failed,
                severity_level,
                write_host,
                no_errors=no_errors,
                content=content,
            )
    elif isinstance(result, MultiResult):
        for r in result:
            content = _write_result(
                r,
                io,
                attrs,
                failed,
                severity_level,
                write_host,
                no_errors=no_errors,
                content=content,
            )
    elif isinstance(result, Result):
        content = _write_individual_result(
            result,
            io,
            attrs,
            failed,
            severity_level,
            write_host=write_host,
            no_errors=no_errors,
            content=content,
        )

    return content


def write_result(
    result: Result,
    filename: str,
    vars: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    write_host: bool = True,
    append: bool = False,
    no_errors: bool = False,
) -> str:
    """
    Writes an object of type `nornir.core.task.Result` to file

    Args:
        result: From a previous task
        (Result or AggregatedResult or MultiResult)
        filename: File you want to write the result
        vars: Which attributes you want to write
        (see ``class Result`` attributes)
        failed: If ``True`` assume the task failed
        severity_level: Write only errors with this severity level or higher
        write_host: Write hostname to file
        append: "a+" if ``True`` or "w+" if ``False``
        no_errors: Don't write results with errors

    Returns:
        str: Diff between previous file state and new file state

    Raises:
        N/A
    """

    dirname = os.path.dirname(filename)
    Path(dirname).mkdir(parents=True, exist_ok=True)

    mode = "a+" if append else "w+"

    LOCK.acquire()

    try:
        with open(filename, mode=mode) as f:
            content: List[str] = _write_result(
                result,
                io=f,
                attrs=vars,
                failed=failed,
                severity_level=severity_level,
                write_host=write_host,
                no_errors=no_errors,
                content=[],
            )

            lf = "\n\n" if Path(filename).stat().st_size != 0 and append else ""

            lines = [line.strip() for line in content]
            line = lf + "\n\n".join(lines)

            diff = _generate_diff(filename, line, append)

            f.write(line)

        return diff
    finally:
        LOCK.release()
