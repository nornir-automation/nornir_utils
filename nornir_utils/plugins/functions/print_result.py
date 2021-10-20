import logging
import pprint
import threading
from itertools import islice
from typing import List, cast, Optional, Dict, Any
from collections import OrderedDict
import json

from colorama import Fore, Style, init

from nornir.core.task import AggregatedResult, MultiResult, Result


LOCK = threading.Lock()


init(autoreset=True, strip=False)


def _slice_result(
    result: AggregatedResult,
    count: Optional[int] = None,
):
    msg = result.name
    msg = "{}{}{}{}".format(
        Style.BRIGHT, Fore.CYAN, msg, "*" * (80 - len(msg))
    )
    results: Dict[Any, Any] = dict(sorted(result.items()))
    if count != 0:
        print(msg)
    if isinstance(count, int):
        length = len(results)
        if count >= 0:
            _ = [0, length and count]
        elif (length + count) < 0:
            _ = [0, length]
        else:
            _ = [length + count, length]
        results = dict(islice(results.items(), *_))
    return results


def print_title(title: str) -> None:
    """
    Helper function to print a title.
    """
    msg = "**** {} ".format(title)
    print(
        "{}{}{}{}".format(Style.BRIGHT, Fore.GREEN, msg, "*" * (80 - len(msg)))
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
    print_host: bool = False,
) -> None:
    if result.severity_level < severity_level:
        return

    color = _get_color(result, failed)
    subtitle = (
        ""
        if result.changed is None
        else " ** changed : {} ".format(result.changed)
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
        )
    )
    for attribute in attrs:
        x = getattr(result, attribute, "")
        if isinstance(x, BaseException):
            # for consistency between py3.6 and py3.7
            print(f"{x.__class__.__name__}{x.args}")
        elif x and not isinstance(x, str):
            if isinstance(x, OrderedDict):
                print(json.dumps(x, indent=2))
            else:
                pprint.pprint(x, indent=2)
        elif x:
            print(x)


def _print_result(
    result: Result,
    attrs: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    print_host: bool = False,
    count: Optional[int] = None,
) -> None:
    attrs = attrs or ["diff", "result", "stdout"]
    if isinstance(attrs, str):
        attrs = [attrs]

    if isinstance(result, AggregatedResult):
        result = _slice_result(result, count)
        for host, host_data in result.items():
            title = (
                ""
                if host_data.changed is None
                else " ** changed : {} ".format(host_data.changed)
            )
            msg = "* {}{}".format(host, title)
            print(
                "{}{}{}{}".format(
                    Style.BRIGHT, Fore.BLUE, msg, "*" * (80 - len(msg))
                )
            )
            _print_result(host_data, attrs, failed, severity_level)
    elif isinstance(result, MultiResult):
        _print_individual_result(
            result[0],
            attrs,
            failed,
            severity_level,
            task_group=True,
            print_host=print_host,
        )
        for r in result[1:]:
            _print_result(r, attrs, failed, severity_level)
        color = _get_color(result[0], failed)
        msg = "^^^^ END {} ".format(result[0].name)
        print(
            "{}{}{}{}".format(Style.BRIGHT, color, msg, "^" * (80 - len(msg)))
        )
    elif isinstance(result, Result):
        _print_individual_result(
            result, attrs, failed, severity_level, print_host=print_host
        )


def print_result(
    result: Result,
    vars: List[str] = None,
    failed: bool = False,
    severity_level: int = logging.INFO,
    count: Optional[int] = None,
) -> None:
    """
    Prints an object of type `nornir.core.task.Result`

    Arguments:
      result: from a previous task
      vars: Which attributes you want to print
      failed: if ``True`` assume the task failed
      severity_level: Print only errors with this severity level or higher
      count: Number of sorted results. It's acceptable
      to use numbers with minus sign(-5 as example),
      then results will be from the end of results list
    """
    LOCK.acquire()
    try:
        _print_result(
            result,
            vars,
            failed=failed,
            severity_level=severity_level,
            print_host=True,
            count=count,
        )
    finally:
        LOCK.release()
