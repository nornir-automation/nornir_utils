import os
import json
import difflib
import logging
import threading
from pathlib import Path
from itertools import islice
from typing import List, Optional, Tuple, NamedTuple
from nornir.core.task import AggregatedResult, MultiResult, Result
from nornir_utils.plugins.tasks.files.write_file import _read_file


LOCK = threading.Lock()


class ResultRecord(NamedTuple):
    name: str
    res: str
    diff: str


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
    dirname: str,
    attrs: List[str],
    failed: bool,
    severity_level: int,
    task_group: bool = False,
    write_host: bool = False,
    no_errors: bool = False,
    append: bool = False,
    content: List[ResultRecord] = [],
) -> List[ResultRecord]:

    individual_result = []

    # ignore results with a specifig severity_level
    if result.severity_level < severity_level:
        return content

    # ignore results with errors
    if no_errors:
        if result.exception:
            return content

    # create file only if there is a result.host.name
    if result.host and result.host.name:
        filename = result.host.name
    else:
        return content

    filepath = os.path.join(dirname, filename)
    old_lines = _read_file(filepath)

    subtitle = (
        "" if result.changed is None else " ** changed : {} ".format(
            result.changed
        )
    )
    level_name = logging.getLevelName(result.severity_level)
    symbol = "v" if task_group else "-"
    host = f"{filename}: " if write_host else ""
    msg = "{} {}{}{}".format(symbol * 4, host, result.name, subtitle)
    individual_result.append(
        "{}{} {}".format(msg, symbol * (80 - len(msg)), level_name)
    )
    for attribute in attrs:
        x = getattr(result, attribute, "")
        if isinstance(x, BaseException):
            # for consistency between py3.6 and py3.7
            individual_result.append(f"{x.__class__.__name__}{x.args}")
        elif x and not isinstance(x, str):
            try:
                individual_result.append(
                    json.dumps(
                        x, indent=2, ensure_ascii=False
                    ).encode("utf-8").decode()
                )
            except TypeError:
                individual_result.append(str(x))
        elif x:
            individual_result.append(x)

    lines = [line.strip() for line in individual_result]
    line = "\n\n".join(lines)

    diff = _generate_diff(old_lines, line, append, filepath)

    result_record = ResultRecord._make([filename, lines, diff])

    # add namedtuple with filename, Result attributes, diff
    content.append(result_record)
    return content


def _write_results(
    result: Result,
    dirname: str,
    attrs: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    write_host: bool = False,
    count: Optional[int] = None,
    no_errors: bool = False,
    append: bool = False,
    content: List[ResultRecord] = [],
) -> List[ResultRecord]:

    attrs = attrs or ["diff", "result", "stdout"]
    if isinstance(attrs, str):
        attrs = [attrs]

    if isinstance(result, AggregatedResult):
        result = dict(sorted(result.items()))

        if isinstance(count, int):
            length = len(result)
            if count >= 0:
                _ = [0, length and count]
            elif (length + count) < 0:
                _ = [0, length]
            else:
                _ = [length + count, length]
            result = dict(islice(result.items()), *_)

        for host_data in result.values():
            content = _write_results(
                host_data,
                dirname,
                attrs,
                failed,
                severity_level,
                write_host,
                no_errors=no_errors,
                append=append,
                content=content,
            )
    elif isinstance(result, MultiResult):
        for r in result:
            content = _write_results(
                r,
                dirname,
                attrs,
                failed,
                severity_level,
                write_host,
                no_errors=no_errors,
                append=append,
                content=content,
            )
    elif isinstance(result, Result):
        content = _write_individual_result(
            result,
            dirname,
            attrs,
            failed,
            severity_level,
            write_host=write_host,
            no_errors=no_errors,
            append=append,
            content=content,
        )

    return content


def write_results(
    result: Result,
    dirname: str,
    vars: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    write_host: bool = True,
    count: Optional[int] = None,
    no_errors: bool = False,
    append: bool = False,
) -> List[Tuple[str, str]]:
    """
    Writes an object of type `nornir.core.task.Result`
    to files with hostname names

    Arguments:

      result: from a previous task(Result or AggregatedResult or MultiResult)

      dirname: directory you want to write into

      vars: Which attributes you want to write(see ``class Result`` attributes)

      failed: if ``True`` assume the task failed

      severity_level: Print only errors with this severity level or higher

      write_host: Write hostname to file

      count: Number of sorted results. It's acceptable
      to use numbers with minus sign(-5 as example),
      then results will be from the end of results list

      no_errors: Don't write results with errors

      append: "a+" if ``True`` or "w+" if ``False``
    """
    Path(dirname).mkdir(parents=True, exist_ok=True)

    mode = "a+" if append else "w+"

    LOCK.acquire()

    try:
        content: List[ResultRecord] = _write_results(
            result,
            dirname,
            attrs=vars,
            failed=failed,
            severity_level=severity_level,
            write_host=write_host,
            count=count,
            no_errors=no_errors,
            append=append,
            content=[],
        )

        diffs = []

        for value in content:
            path = os.path.join(dirname, value.name)
            with open(path, mode=mode) as f:

                lf = "\n\n" if Path(
                    path
                ).stat().st_size != 0 and append else ""

                f.write(lf + "\n\n".join(value.res))
            diffs.append((value.name, value.diff))
        return diffs
    finally:
        LOCK.release()
