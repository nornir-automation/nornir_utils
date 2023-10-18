import json
import logging
import pprint
import sys
import threading
from collections import OrderedDict
from typing import IO, List, cast, Optional

from colorama import AnsiToWin32, Fore, Style, init
from colorama.ansitowin32 import StreamWrapper

from nornir.core.task import AggregatedResult, MultiResult, Result


LOCK = threading.Lock()


init(autoreset=True, strip=False)


def print_title(title: str, file: IO[str] = sys.stdout) -> None:
    """
    Helper function to print a title.
    """
    msg = "**** {} ".format(title)
    print(
        "{}{}{}{}".format(Style.BRIGHT, Fore.GREEN, msg, "*" * (80 - len(msg))),
        file=file,
    )


def _get_color(result: Result, failed: bool) -> str:
    if result.failed or failed:
        color = Fore.RED
    elif result.changed:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN
    return cast(str, color)


def _print_individual_result(
    result: Result,
    attrs: List[str],
    failed: bool,
    severity_level: int,
    task_group: bool = False,
    no_errors: bool = False,
    print_host: bool = False,
    file: IO[str] = sys.stdout,
) -> None:
    if result.severity_level < severity_level:
        return

    if no_errors and result.exception:
        return

    color = _get_color(result, failed)
    subtitle = (
        "" if result.changed is None else " ** changed : {} ".format(result.changed)
    )
    level_name = logging.getLevelName(result.severity_level)
    symbol = "v" if task_group else "-"
    host = (
        f"{result.host.name}: "
        if (print_host and result.host and result.host.name)
        else ""
    )
    msg = "{} {}{}{}".format(symbol * 4, host, result.name, subtitle)
    print(
        "{}{}{}{} {}".format(
            Style.BRIGHT, color, msg, symbol * (80 - len(msg)), level_name
        ),
        file=file,
    )
    for attribute in attrs:
        x = getattr(result, attribute, "")
        if isinstance(x, BaseException):
            # for consistency between py3.6 and py3.7
            print(f"{x.__class__.__name__}{x.args}", file=file)
        elif x and not isinstance(x, str):
            if isinstance(x, OrderedDict):
                print(json.dumps(x, indent=2), file=file)
            else:
                pprint.pprint(x, indent=2, stream=file)
        elif x:
            print(x, file=file)


def _print_result(
    result: Result,
    attrs: Optional[List[str]] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    no_errors: bool = False,
    print_host: bool = False,
    file: IO[str] = sys.stdout,
) -> None:
    attrs = attrs or ["diff", "result", "stdout"]
    if isinstance(attrs, str):
        attrs = [attrs]

    if isinstance(result, AggregatedResult):
        msg = result.name
        print(
            "{}{}{}{}".format(Style.BRIGHT, Fore.CYAN, msg, "*" * (80 - len(msg))),
            file=file,
        )
        for host, host_data in sorted(result.items()):
            title = (
                ""
                if host_data.changed is None
                else " ** changed : {} ".format(host_data.changed)
            )
            msg = "* {}{}".format(host, title)
            print(
                "{}{}{}{}".format(Style.BRIGHT, Fore.BLUE, msg, "*" * (80 - len(msg))),
                file=file,
            )
            _print_result(
                host_data, attrs, failed, severity_level, no_errors, file=file
            )
    elif isinstance(result, MultiResult):
        _print_individual_result(
            result[0],
            attrs,
            failed,
            severity_level,
            task_group=True,
            no_errors=no_errors,
            print_host=print_host,
            file=file,
        )
        for r in result[1:]:
            _print_result(r, attrs, failed, severity_level, no_errors, file=file)
        color = _get_color(result[0], failed)
        msg = "^^^^ END {} ".format(result[0].name)
        if result[0].severity_level >= severity_level or not (
            result[0].exception and no_errors
        ):
            print(
                "{}{}{}{}".format(Style.BRIGHT, color, msg, "^" * (80 - len(msg))),
                file=file,
            )
    elif isinstance(result, Result):
        _print_individual_result(
            result,
            attrs,
            failed,
            severity_level,
            no_errors=no_errors,
            print_host=print_host,
            file=file,
        )


def print_result(
    result: Result,
    vars: Optional[List[str]] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    no_errors: bool = False,
    print_host: bool = True,
    file: IO[str] = sys.stdout,
) -> None:
    """
    Prints an object of type `nornir.core.task.Result`

    Args:
        result: From a previous task
        vars: Which attributes you want to print
        failed: If ``True`` assume the task failed
        severity_level: Print/write only errors with this severity level or higher
        no_errors: Don't print/write results with exceptions
        print_host: Print/write hostname for MultiResult and Result objects
        file: The file argument must be an object with a write(string) method;
        if it is not present or None, sys.stdout will be used.
        The file argument of the print_result function uses the same file argument
        of the print function

    Returns:
        N/A

    Raises:
        N/A
    """
    if file and not isinstance(file, StreamWrapper):
        file = AnsiToWin32(file, strip=True, autoreset=True).stream
    LOCK.acquire()
    try:
        _print_result(result, vars, failed, severity_level, no_errors, print_host, file)
    finally:
        LOCK.release()
