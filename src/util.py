from datetime import datetime
from typing import TypeVar, Iterable, Callable, Optional


# 毫秒转成三位小数的时间字符串，对本项目的场景比较适用。偷懒名字就简写了。
def ts_to_str(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000).strftime("%M:%S.%f")[:-3]


T = TypeVar('T')

def find_first(cond: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    return next(filter(cond, iterable), None)