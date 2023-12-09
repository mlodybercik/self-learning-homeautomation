import typing as t
from abc import ABC, abstractmethod, abstractstaticmethod
from datetime import time, timedelta
from inspect import isabstract

import numpy as np

from automation.utils import get_logger

logger = get_logger("models.converters")

T = t.TypeVar("T")
SECONDS_IN_A_DAY = 60 * 60 * 24
WIDTH = 1


class Convertable(t.Generic[T], ABC):
    @classmethod
    @property
    @abstractmethod
    def TYPE(cls) -> str:
        ...

    @abstractstaticmethod
    def convert_to(x: T) -> float:
        ...

    @abstractstaticmethod
    def convert_from(x: float) -> T:
        ...


class CompoundConvertable(ABC):
    @classmethod
    @property
    @abstractmethod
    def TYPE(cls) -> str:
        ...

    @classmethod
    @property
    @abstractmethod
    def TYPES(cls) -> t.Dict[str, t.Type[Convertable]]:
        ...

    @staticmethod
    def convert_to(x):
        return {name: type_.convert_to(x) for name, type_ in __class__.TYPES.items()}

    @staticmethod
    def convert_from(x):
        return {name: type_.convert_from(x) for name, type_ in __class__.TYPES.items()}


class AnyConvertable(Convertable[t.Any]):
    TYPE = "any"

    @staticmethod
    def convert_to(x: float) -> t.Any:
        return float(x)

    @staticmethod
    def convert_from(x: t.Any) -> float:
        return np.round(x)
        # debugging purposes
        # return x


def create_time_convertable(time_at: time):
    at_seconds = (
        timedelta(hours=time_at.hour, minutes=time_at.minute, seconds=time_at.second).total_seconds() / SECONDS_IN_A_DAY
    )

    class BinaryTimeConvertable(Convertable[time]):
        @staticmethod
        def convert_to(x: time) -> float:
            global WIDTH
            seconds = timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds() / SECONDS_IN_A_DAY
            return np.exp(WIDTH * -np.abs((seconds - at_seconds) * 36) ** 2)

        @staticmethod
        def convert_from(_: float) -> time:
            raise AttributeError("convert_from is not needed")

    return BinaryTimeConvertable


class TimeCosConvertable(Convertable[time]):
    TYPE = "time_cos"

    @staticmethod
    def convert_to(x: time) -> float:
        seconds = timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds()
        return np.cos(seconds * 2 * np.pi / SECONDS_IN_A_DAY)

    @staticmethod
    def convert_from(_: float) -> time:
        raise AttributeError("convert_from is not needed")


class TimeSinConvertable(Convertable[time]):
    TYPE = "time_sin"

    @staticmethod
    def convert_to(x: time) -> float:
        seconds = timedelta(hours=x.hour, minutes=x.minute, seconds=x.second).total_seconds()
        return np.sin(seconds * 2 * np.pi / SECONDS_IN_A_DAY)

    @staticmethod
    def convert_from(_: float) -> time:
        raise AttributeError("convert_from is not needed")


class CompoundTimeConverter(CompoundConvertable):
    TYPE = "time"
    TYPES = {
        "time_cos": TimeCosConvertable(),
        "time_sin": TimeSinConvertable(),
    }


class BinaryTimeConverter(CompoundConvertable):
    TYPE = "binary_time"
    TYPES = {f"t_{n}": create_time_convertable(time(hour=n))() for n in range(0, 24)}


_locals = locals().copy()
CONVERTERS = {}
for _local in _locals.values():
    try:
        if issubclass(_local, (CompoundConvertable, Convertable)) and not isabstract(_local):
            CONVERTERS[_local.TYPE] = _local
    except TypeError:
        pass

CONVERTERS_REVERSE = {v: k for k, v in CONVERTERS.items()}

logger.debug(f"CONVERTERS = {CONVERTERS}")
logger.debug(f"CONVERTERS_REVERSE = {CONVERTERS_REVERSE}")
