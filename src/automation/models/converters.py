import typing as t
import numpy as np
from abc import ABC, abstractstaticmethod
from datetime import time, timedelta


T = t.TypeVar('T')
class Convertable(t.Generic[T], ABC):
    TYPE: str
    
    @abstractstaticmethod
    def convert_to(x: T) -> float: ...

    @abstractstaticmethod
    def convert_from(x: float) -> T: ...


class AnyConvertable(Convertable[t.Any]):
    TYPE = 'any'

    @staticmethod
    def convert_from(x: float) -> t.Any:
        return float(x)
    
    @staticmethod
    def convert_to(x: t.Any) -> float:
        return float(x) 
    

class TimeConvertable(Convertable[time]):
    SECONDS_IN_A_DAY = 60 * 60 * 24
    TYPE = 'time'

    @staticmethod
    def convert_to(x: time) -> float:
        seconds = timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds()
        return np.cos(seconds * np.pi / __class__.SECONDS_IN_A_DAY)

    @staticmethod
    def convert_from(_: float) -> time:
        raise AttributeError('convert_from is not needed')
    
CONVERTERS = {
    TimeConvertable.TYPE: TimeConvertable,
    AnyConvertable.TYPE: AnyConvertable,
}

CONVERTERS_REVERSE = {v: k for k, v in CONVERTERS.items()}