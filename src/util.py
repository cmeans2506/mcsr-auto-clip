from datetime import datetime
from typing import TypeVar, Iterable, Callable, Optional


# Converts milliseconds into a time string with three decimal places (MM:SS.ms).
# This is specifically suitable for the timing scenarios in this project.
def ts_to_str(timestamp: Optional[int]) -> Optional[str]:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp / 1000).strftime("%M:%S.%f")[:-3]


def ts_to_str_sec(timestamp: Optional[int]) -> Optional[str]:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp / 1000).strftime("%M:%S")


T = TypeVar('T')

def find_first(cond: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    return next(filter(cond, iterable), None)