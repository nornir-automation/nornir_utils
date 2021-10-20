import threading
from typing import Optional, Tuple
from nornir_utils.plugins.functions.print_result import (
    _get_color,
    _slice_result,
)

from colorama import Fore, Style, init

from nornir.core.task import AggregatedResult, MultiResult, Result


LOCK = threading.Lock()


init(autoreset=True, strip=False)


def _print_individual_stat(
    result: Result,
    res_sum: int = 0,
    ch_sum: int = 0,
    f_sum: int = 0,
) -> Tuple[int, int, int]:

    f, ch = (result.failed, result.changed)

    res_sum += 1
    ch_sum += int(ch)
    f_sum += int(f)

    color = _get_color(result, f)
    msg = "{:<35} ok={:<15} changed={:<15} failed={:<15}".format(
        result.name, not f, ch, f
    )
    print("    {}{}{}".format(Style.BRIGHT, color, msg))
    return res_sum, ch_sum, f_sum


def _print_stat(
    result: Result,
    count: Optional[int] = None,
    res_sum: int = 0,
    ch_sum: int = 0,
    f_sum: int = 0,
) -> Tuple[int, int, int]:

    if isinstance(result, AggregatedResult):
        msg = result.name
        msg = "{}{}{}{}".format(
            Style.BRIGHT, Fore.CYAN, msg, "*" * (80 - len(msg))
        )
        if count != 0:
            print(msg)
        result = _slice_result(result, count)
        for host, host_data in result.items():
            msg_host = "* {} ".format(host)
            print(
                "{}{}{}{}".format(
                    Style.BRIGHT,
                    Fore.BLUE,
                    msg_host,
                    "*" * (80 - len(msg_host)),
                )
            )
            res_sum, ch_sum, f_sum = _print_stat(
                host_data, count, res_sum, ch_sum, f_sum
            )
    elif isinstance(result, MultiResult):
        for res in result:
            res_sum, ch_sum, f_sum = _print_stat(
                res, count, res_sum, ch_sum, f_sum
            )
    elif isinstance(result, Result):
        res_sum, ch_sum, f_sum = _print_individual_stat(
            result, res_sum, ch_sum, f_sum
        )

    return res_sum, ch_sum, f_sum


def print_stat(result: Result, count: Optional[int] = None) -> None:
    """
    Prints statistic for `nornir.core.task.Result` object

    Arguments:
      result: from a previous task
      count: Number of sorted results. It's acceptable
      to use numbers with minus sign(-5 as example),
      then results will be from the end of results list
    """
    LOCK.acquire()
    try:
        res_sum, ch_sum, f_sum = _print_stat(
            result,
            count=count,
            res_sum=0,
            ch_sum=0,
            f_sum=0,
        )
        print()
        for state, summary, color in zip(
            ("OK", "CHANGED", "FAILED"),
            (res_sum - f_sum, ch_sum, f_sum),
            (Fore.GREEN, Fore.YELLOW, Fore.RED),
        ):
            print("{}{}{:<8}: {}".format(Style.BRIGHT, color, state, summary))
    finally:
        LOCK.release()
