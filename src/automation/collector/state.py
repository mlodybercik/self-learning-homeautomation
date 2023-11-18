import typing as t
from datetime import datetime

from automation.collector.device_history import DEVICE_HISTORY_HANDLER, TimeEntry
from automation.utils import get_logger, get_utc_now

logger = get_logger("collector.state")


class StateCollector:
    def __init__(self, devices: t.Dict[str, str]):
        self.devices = {device: DEVICE_HISTORY_HANDLER[d_type] for device, d_type in devices.items()}

    def parse_state_change(self, states: t.Dict[str, dict]) -> t.Dict[str, float]:
        ret = {}
        now = get_utc_now()
        for device in self.devices.keys():
            entry = TimeEntry(
                last_changed=datetime.fromisoformat(states[device]["last_changed"]),
                device_name=device,
                state=states[device]["state"],
            )
            state = self.devices[device].get_current_state(entry, now)
            ret[device] = state
        return ret

    def create_state_change_functions(self, change: t.Dict[str, float], state: t.Dict[str, float]):
        return {
            device: self.devices[device].generate_change_state_func(device, change[device], state[device])
            for device in self.devices
        }

    def compare_actions(
        self, previous_state: t.Dict[str, float], new_state: t.Dict[str, float], machine_change: t.Dict[str, float]
    ):
        # Mann vs Machine
        # 1. compare previous state to current state to extract change.
        # 2. compare user changes and machine predictions
        # 3. if the intent is common, let machine execute them

        human_change = {
            device: handler.get_current_change(new_state[device], previous_state[device])
            for device, handler in self.devices.items()
        }

        key_of_change = None
        for key, value in human_change.items():
            if value:
                key_of_change = key

        if not key_of_change:
            return False

        # changes = [human_change[device] == action for device, action in machine_change.items()]
        # change = any(changes)

        # debug_changes = [str(change) for change in changes]
        human_changes = [str(human_change[device]) for device in human_change]
        machine_changes = [str(machine_change[device]) for device in machine_change]

        # logger.debug(f"Calculated simmilarity table: [{', '.join(debug_changes)}]")
        logger.debug(f"Change on key: {key_of_change}")
        logger.debug(f"Human change table: [{', '.join(human_changes)}]")
        logger.debug(f"Machine change table: [{', '.join(machine_changes)}]")

        return human_change[key_of_change] == machine_change[key_of_change]
