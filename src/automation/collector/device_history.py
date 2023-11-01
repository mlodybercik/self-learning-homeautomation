import typing as t
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractstaticmethod
from . import EPISODE_DELTA

@dataclass
class TimeEntry:
    last_changed: datetime
    device_name: str
    state: str

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed == __value.last_changed
        raise NotImplemented()
    
    def __gt__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed > __value.last_changed
        raise NotImplemented()
    
    def __lt__(self, __value: object) -> bool:
        if isinstance(__value, __class__):
            return self.last_changed < __value.last_changed
        raise NotImplemented()
    


class DeviceHistoryGeneric(ABC):
    DEVICE_TYPE: str

    @staticmethod
    @abstractstaticmethod
    def get_past_state(current: TimeEntry, previous: t.Optional[TimeEntry], up_to: t.Optional[datetime]) -> t.Tuple[int, int]:
        "first state, second change"

    @staticmethod
    @abstractstaticmethod
    def get_current_state(current: TimeEntry, now: datetime) -> int:
        "returns only current state"


class BooleanHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "bool"
    STATES = {"off": -1.0, "on": 1.0}

    @staticmethod
    def get_past_state(current: TimeEntry, previous: t.Optional[TimeEntry], up_to: t.Optional[datetime]) -> t.Tuple[int, int]:
        if not previous:
            return 0.0 if current.state == 'on' else 1.0, __class__.STATES[current.state]
        
        assert previous.device_name == current.device_name

        state, change = 0.0, 0.0
        if (previous.last_changed < up_to):
            change = __class__.STATES[current.state]

        state = int(previous.state == 'on')

        return state, change
    
    @staticmethod
    def get_current_state(current: TimeEntry, _: datetime) -> int:
        return 1.0 if current.state == 'on' else 0.0


class ButtonHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "button"

    @staticmethod
    def get_past_state(current: TimeEntry, previous: t.Optional[TimeEntry], up_to: t.Optional[datetime]) -> t.Tuple[int, int]:
        if not previous:
            return 1.0, 1.0
        assert previous.device_name == current.device_name

        state, change = 0.0, 0.0
        if (previous.last_changed < up_to):
            change = 1.0
        return state, change
    
    @staticmethod
    def get_current_state(current: TimeEntry, now: datetime) -> int:
        return current.last_changed + EPISODE_DELTA > now
    


DEVICE_HISTORY_HANDLER: t.Dict[str, DeviceHistoryGeneric] = {
    ButtonHistory.DEVICE_TYPE: ButtonHistory,
    BooleanHistory.DEVICE_TYPE: BooleanHistory,
}