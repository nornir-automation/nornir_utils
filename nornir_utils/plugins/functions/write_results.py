import json
import logging
import os
import threading
from pathlib import Path
from typing import Dict, List, Tuple

from nornir.core.task import AggregatedResult, MultiResult, Result

from nornir_utils.plugins.tasks.files.write_file import _generate_diff


LOCK = threading.Lock()


def _write_individual_result(
    result: Result,
    attrs: List[str],
    failed: bool,
    severity_level: int,
    task_group: bool = False,
    write_host: bool = False,
    no_errors: bool = False,
    content: Dict[str, List[str]] = None,
) -> Dict[str, List[str]]:

    if content is None:
        content = {}

    individual_result = []

    # ignore results with a specific severity_level
    if result.severity_level < severity_level:
        return content

    # ignore results with errors
    if no_errors and result.exception:
        return content

    filename = str(result.host)

    subtitle = (
        "" if result.changed is None else " ** changed : {} ".format(result.changed)
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
                    json.dumps(x, indent=2, ensure_ascii=False).encode("utf-8").decode()
                )
            except TypeError:
                individual_result.append(str(x))
        elif x:
            individual_result.append(x)

    lines = [line.strip() for line in individual_result]
    content[filename].extend(lines)

    return content


def _write_results(
    result: Result,
    attrs: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    write_host: bool = False,
    no_errors: bool = False,
    content: Dict[str, List[str]] = None,
) -> Dict[str, List[str]]:

    if content is None:
        content = {}

    attrs = attrs or ["diff", "result", "stdout"]
    if isinstance(attrs, str):
        attrs = [attrs]

    if isinstance(result, AggregatedResult):
        for host_data in result.values():
            content = _write_results(
                host_data,
                attrs,
                failed,
                severity_level,
                write_host,
                no_errors=no_errors,
                content=content,
            )
    elif isinstance(result, MultiResult):
        for r in result:
            # collect the results to dict, where key = result.host.name
            if result.host and result.host.name:
                filename = result.host.name
                if filename not in content.keys():
                    content[filename] = []
            else:
                continue
            content = _write_results(
                r,
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
            attrs,
            failed,
            severity_level,
            write_host=write_host,
            no_errors=no_errors,
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
    no_errors: bool = False,
    append: bool = False,
) -> List[Tuple[str, str]]:
    """
    Writes an object of type `nornir.core.task.Result`
    to files with hostname names

    Args:
        result: From a previous task(Result or AggregatedResult or MultiResult)
        dirname: Directory you want to write into
        vars: Which attributes you want to write
        (see ``class Result`` attributes)
        failed: If ``True`` assume the task failed
        severity_level: Write only errors with this severity level or higher
        write_host: Write hostname to file
        no_errors: Don't write results with errors
        append: "a+" if ``True`` or "w+" if ``False``

    Returns:
        List[Tuple[str, str]]: List of tuples with hostname + diff
        between previous file state and new file state

    Raises:
        N/A
    """
    Path(dirname).mkdir(parents=True, exist_ok=True)

    mode = "a+" if append else "w+"

    LOCK.acquire()

    try:
        content: Dict[str, List[str]] = _write_results(
            result,
            attrs=vars,
            failed=failed,
            severity_level=severity_level,
            write_host=write_host,
            no_errors=no_errors,
            content={},
        )

        diffs = []

        for name, res in content.items():
            path = os.path.join(dirname, name)
            with open(path, mode=mode) as f:
                line = "\n\n".join(res)

                lf = "\n\n" if Path(path).stat().st_size != 0 and append else ""

                line = lf + line

                diff = _generate_diff(path, line, append)

                f.write(line)
            diffs.append((name, diff))
        return diffs
    finally:
        LOCK.release()
