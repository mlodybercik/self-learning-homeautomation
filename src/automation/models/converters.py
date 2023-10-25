import typing as t
import numpy as np
from abc import ABC, abstractstaticmethod
from datetime import time, timedelta


T = t.TypeVar('T')
class Convertable(t.Generic[T], ABC):
    
    @abstractstaticmethod
    def convert_to(x: T) -> float: ...

    @abstractstaticmethod
    def convert_from(x: float) -> T: ...


class AnyConvertable(Convertable[t.Any]):
    def convert_from(x: float) -> t.Any:
        return x
    
    def convert_to(x: t.Any) -> float:
        return x 
    

class TimeConvertable(Convertable[time]):
    SECONDS_IN_A_DAY = 60 * 60 * 24

    def convert_to(x: time) -> float:
        seconds = timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds()
        return np.cos(seconds * np.pi / __class__.SECONDS_IN_A_DAY)

    def convert_from(_: float) -> time:
        raise AttributeError('convert_from is not needed')
    
