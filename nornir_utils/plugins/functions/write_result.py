import os
import difflib
import logging
import threading
import json
from pathlib import Path
from typing import List, Optional, IO, AnyStr
from nornir_utils.plugins.tasks.files.write_file import _read_file
from nornir_utils.plugins.functions.print_result import _slice_result

from nornir.core.task import AggregatedResult, MultiResult, Result


LOCK = threading.Lock()


def _generate_diff(
    old_lines: List[str],
    new_lines: str,
    append: bool,
    filename: str,
) -> str:
    if append:
        c = list(old_lines)
        c.extend(new_lines.splitlines())
        new_content = c
    else:
        new_content = new_lines.splitlines()

    diff = difflib.unified_diff(
        old_lines, new_content, fromfile=filename, tofile="new"
    )

    return "\n".join(diff)


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

    # ignore results with a specifig severity_level
    if result.severity_level < severity_level:
        return content

    # ignore results with errors
    if no_errors:
        if result.exception:
            return content

    subtitle = (
        ""
        if result.changed is None
        else " ** changed : {} ".format(result.changed)
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
                    json.dumps(x, indent=2, ensure_ascii=False)
                    .encode("utf-8")
                    .decode()
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
    count: Optional[int] = None,
    no_errors: bool = False,
    content: List[str] = [],
) -> List[str]:

    attrs = attrs or ["diff", "result", "stdout"]
    if isinstance(attrs, str):
        attrs = [attrs]

    if isinstance(result, AggregatedResult):
        result = _slice_result(result, count)
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
    count: Optional[int] = None,
    append: bool = False,
    no_errors: bool = False,
) -> str:
    """
    Writes an object of type `nornir.core.task.Result` to file

    Arguments:
      result: from a previous task (Result or AggregatedResult or MultiResult)
      filename: file you want to write the result
      vars: Which attributes you want to write(see ``class Result`` attributes)
      failed: if ``True`` assume the task failed
      severity_level: Print only errors with this severity level or higher
      write_host: Write hostname to file
      count: Number of sorted results. It's acceptable
      to use numbers with minus sign(-5 as example),
      then results will be from the end of results list
      append: "a+" if ``True`` or "w+" if ``False``
      no_errors: Don't write results with errors
    """
    old_lines = _read_file(filename)

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
                count=count,
                no_errors=no_errors,
                content=[],
            )

            lf = (
                "\n\n" if Path(filename).stat().st_size != 0 and append else ""
            )

            lines = [line.strip() for line in content]
            line = lf + "\n\n".join(lines)

            f.write(line)

        diff = _generate_diff(old_lines, line, append, filename)

        return diff
    finally:
        LOCK.release()
