import typing as t
from automation.utils import get_logger, get_utc_now
from automation.collector.device_history import TimeEntry, DEVICE_HISTORY_HANDLER
from datetime import datetime

logger = get_logger("collector.state")


class StateCollector:
    def __init__(self, devices: t.Dict[str, str]):
        self.devices = {device: DEVICE_HISTORY_HANDLER[d_type] for device, d_type in devices.items()}

    def parse_state_change(self, states: t.Dict[str, dict]) -> t.Dict[str, int]:
        ret = {}
        now = get_utc_now()
        for device in self.devices.keys():
            entry = TimeEntry(
                last_changed=datetime.fromisoformat(states[device]['last_changed']),
                device_name=device,
                state=states[device]['state']
            )
            state = self.devices[device].get_current_state(entry, now)
            ret[device] = state
        return ret
    
    def create_state_change_functions(self, change: t.Dict[str, float]):
        return {device: self.devices[device].generate_change_state_func(device, change[device]) for device in self.devices}
    