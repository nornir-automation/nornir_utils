from colorama import init

from .print_result import (
    print_result,
    print_title,
)
from .print_stat import print_stat
from .write_result import write_result
from .write_results import write_results

init(autoreset=True, strip=False)

__all__ = (
    "print_result",
    "print_title",
    "print_stat",
    "write_result",
    "write_results",
)
