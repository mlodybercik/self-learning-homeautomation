import typing as t
from abc import ABC, abstractmethod, abstractstaticmethod
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from inspect import isabstract

from appdaemon.plugins.hass import hassapi as hass

from automation.utils import get_logger, get_utc_now

from . import EPISODE_DELTA

logger = get_logger("collector.device_history")


@dataclass
class TimeEntry:
    last_changed: datetime
    device_name: str
    state: str

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed == __value.last_changed
        raise NotImplementedError()

    def __gt__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed > __value.last_changed
        raise NotImplementedError()

    def __lt__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed < __value.last_changed
        raise NotImplementedError()


class DeviceHistoryGeneric(ABC):
    @property
    @classmethod
    @abstractmethod
    def DEVICE_TYPE(cls) -> str:
        ...

    @staticmethod
    @abstractstaticmethod
    def get_past_state(
        current: TimeEntry, previous: t.Optional[TimeEntry], up_to: t.Optional[datetime]
    ) -> t.Tuple[int, int]:
        "first state, second change"

    @staticmethod
    @abstractstaticmethod
    def get_current_state(current: TimeEntry, now: datetime) -> float:
        "returns only current state"

    @staticmethod
    @abstractstaticmethod
    def generate_change_state_func(device: str, change: float, state: float) -> "t.Callable[[hass.Hass], None] | None":
        r"""
        create func for manager to execute to change to given state
        DANGER: could be unsafe to use ¯\_(ツ)_/¯
        """

    @staticmethod
    @abstractstaticmethod
    def get_current_change(current: float, previous: float) -> float:
        "returns only current RECENT change"


class BooleanHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "bool"
    STATES = {"off": -1.0, "on": 1.0}
    REV_STATES = {-1: "turn_off", 1: "turn_on"}

    @staticmethod
    def get_past_state(
        current: TimeEntry, previous: t.Optional[TimeEntry], up_to: t.Optional[datetime]
    ) -> t.Tuple[int, int]:
        if not previous:
            return 0.0 if current.state == "on" else 1.0, __class__.STATES[current.state]

        assert previous.device_name == current.device_name

        state, change = 0.0, 0.0
        if previous.last_changed < up_to:
            change = __class__.STATES[current.state]

        state = int(previous.state == "on")

        return state, change

    @staticmethod
    def get_current_state(current: TimeEntry, _: datetime) -> float:
        return 1.0 if current.state == "on" else 0.0

    @staticmethod
    def generate_change_state_func(device: str, change: float, state: float) -> "t.Callable[[hass.Hass], None] | None":
        if change:
            if (change == -1 and state == 0) or (change == 1 and state == 1):
                return None
            return partial(getattr(hass.Hass, __class__.REV_STATES[change]), entity_id=device)
        return None

    @staticmethod
    def get_current_change(current: float, previous: float) -> float:
        if current == previous:
            return 0.0
        if previous == 1.0:
            return -1.0
        return 1.0


class ButtonHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "button"

    @staticmethod
    def get_past_state(
        current: TimeEntry, previous: t.Optional[TimeEntry], up_to: t.Optional[datetime]
    ) -> t.Tuple[int, int]:
        if not previous:
            return 1.0, 1.0
        assert previous.device_name == current.device_name

        state, change = 0.0, 0.0
        if previous.last_changed < up_to:
            change = 1.0
        return state, change

    @staticmethod
    def get_current_state(current: TimeEntry, now: datetime) -> float:
        return float(current.last_changed + EPISODE_DELTA > now)

    @staticmethod
    def generate_change_state_func(device: str, change: float, state: float) -> "t.Callable[[hass.Hass], None] | None":
        logger.warning("generate_change_state_func is borked")
        if state:
            return partial(hass.Hass.set_state, entity_id=device, state=get_utc_now().isoformat())
        return None

    @staticmethod
    def get_current_change(current: float, previous: float) -> float:
        logger.warning("get_current_change for button is not supported")
        return 0.0


_locals = locals().copy()
DEVICE_HISTORY_HANDLER = {}
for _local in _locals.values():
    try:
        if issubclass(_local, DeviceHistoryGeneric) and not isabstract(_local):
            DEVICE_HISTORY_HANDLER[_local.DEVICE_TYPE] = _local
    except TypeError:
        pass

logger.debug(f"DEVICE_HISTORY_HANDLER = {DEVICE_HISTORY_HANDLER}")
