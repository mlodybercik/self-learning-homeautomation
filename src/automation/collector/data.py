import typing as t
from abc import ABC, abstractmethod, abstractstaticmethod
from datetime import datetime, timedelta
from dataclasses import dataclass
from automation.utils import get_logger
from appdaemon.plugins.hass import hassapi

logger = get_logger("collector.data")

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
    def get_current_state(previous: t.Optional[TimeEntry], current: TimeEntry, up_to: datetime) -> t.Tuple[int, int]:
        "first state, second change"


class BooleanHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "bool"
    STATES = {"off": -1, "on": 1}

    @staticmethod
    def get_current_state(previous: t.Optional[TimeEntry], current: TimeEntry, up_to: datetime) -> t.Tuple[int, int]:
        if not previous:
            return 0 if current.state == 'on' else 1, __class__.STATES[current.state]
        
        assert previous.device_name == current.device_name

        state, change = 0, 0
        if (previous.last_changed < up_to):
            change = __class__.STATES[current.state]

        state = int(previous.state == 'on')

        return state, change


class ButtonHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "button"

    @staticmethod
    def get_current_state(previous: t.Optional[TimeEntry], current: TimeEntry, up_to: datetime) -> t.Tuple[int, int]:
        if not previous:
            return 0, 0
        assert previous.device_name == current.device_name

        state, change = 0, 0
        if (previous.last_changed < up_to):
            change = 1
        return state, change


class Collector:
    """
    &&&&%%%%%%%%%###((((//(###%&&&%%%%%####(((((***//(((((((((#####%%%%%%%#/,*,*#%%%
    &&&&&&&&%%%%%%%%%%%%%%%##((/*/**/((///((((((/*,,******/((((((#########%%#/,,*(%%
    &&&&&&&&%%%%%%%###############((/,*#%#******,***//////***,*/(((########%%%(*,/%%
    &&&&&&&&%%%%%%%%%###(((////////*/##%#*,*//////**(//////((//*,,,,***/((//(*,,*((#
    &%%%%%%%%&%%%%%#######(///*/*,*(##%#/,,,,***,(##/**/////(//(/*,,,,,/#%(,.,...,,,
    ,/#################(((((/***,(#((%%(*,,,,,*###%#,,,,*/*****,,,,,,./###(/(##&&(,,
    ,,,*//((((((((((((((///***,,/%((%%%%/.,*##(/(%#/.,(%%(,.,*/##%%&&%(((##%%#/,,//(
    ,,,,,,,,***/((///////****,*(%(/(#%%#%%##(//(#%%%%%%%#(#%%%##%%#(((###%%#((#(//#%
    ,,,,,,,*////////**/*,,,,,/#%##((((#######(/,..,*/(*.,*/(((/(((%%%&%%#((///(#%&#/
    ,,,,,,,,**////****,,,,,,,(##%#, ,///(((//(##////**//*****///(%%#((///((###(///*(
    ,,,,,,,,,,,,,,,,,,..,/(%&&%%%%&&&%%%&&&&%(//**/***,.*///((#(#(///(((((((((((*,(*
    ,,,,,,,,,,.,**/(##%&&%%#%%%%%%%#####(((((#(*/*. .,///(((((**,,*///**//**,.,.,((,
    %%#(((%@&&%%%################((////***.. ./(/,*##((#(*,.,**(#%%%%&&&%%%%%%%%&%,,
    %%%&%%#**/&&#(#(((((//*..,*...        *(####/(#//((,,(%%%&@&&@&&%%%%###%%%%&&#,,
    %%%&%%%&&*  ,/(,          ,*. ..,*//(###%%%#*,*(#(#%(/#&&&&&#((%@&(#%&%#%&&&&#,,
    @@@&%%%%%%&/   *(,        ,*. .(@%#(####&#,.*#%%%%//%@@&&&%(%@@%##&&%##%&&%&&%/,
    @@@@@@%##%%#%(.  ,(,   ,,/#/,..(&%%%%%%%###%((%&#*/%@@@&%%&@@&###&%/,*(((&%&&&%,
    @@@@@@@@&((###&(. .((/****/#&%/,/%##%%##(///(&@&((%@&%#&&/,(##%&@@(. ./&&#(%&&&/
    @@@@@@@@@@&####%%*..(&#/(####%&%//##(/(((#%%&@&%##%%%(/,,,**,,,/&&%%##%%(%&&%&&#
    @@@@@@@@@@@@%#%%&&%**#&%%####%%###//#%#%##%&#%@%(##/,,*///////*,*(#((#/#@&&&%&&%
    @@@@@@@@@@@@@&%%%&&%((%&%%%%%&&&@@@&&%%%%%%(####%/,,*//////////(**,,,,./&&&&&&&%
    @@@@@@@@@@@@@@@%%&&&%##&@&&&&&&&&&&&&&&&&%###%%/,,///(((((((((((///*,.(%%#%&&&&/
    &&@@@@@@@@@@@@@&%%&&&%#%&&&&&&&&&&&&&&&%&&&&#*,*//(#((((#####(((((*,*&%/(&%&@&/*
    &&&@@@@@@@@@@@@@&%%&&%##&@&&&&&&&&&%%%&&@@%*,*(#(################(**%#//#%&&(*/(
    %##%&@@@@@@@@@@&%&&&&%#%&&%&&&%%%%&&&&@#,,*(#####%%%%%%%%%%%%%###*,/#%%#(**/#((
    @&#((((%@@@@@@@@@&&&&&%#%&&&&%%&%%&&&&(.,/(%%%%%%%%%%%%%%%%%%%%%%#/,,,,.,*(#((((
    @@@&#((#%&@@@@@@@&%&&&%#&&%#%&&&&&@%/,,*(%%%%%##%%%%%%%%%%%%%%%%%(*,,,*(%#######
    ./@@@&%#%&&&&@@@&%%&&%%%%&&&@&&&&(,,*/(&&%&&%##%&%%%%%%%%%%%%%%(*,,*(#%%#%######
    ,,,/&@&&&&&&&&@&%%%%%%&&/,/%%%(*,,,,(&&&&&%##%%&&&%%%%%%%%%%&&&%%%#/*****/(#####
    ,,,,,*#&@@@@@&%%%%%%%%#,.,,,,,,,,,,#&&&&&%((#%%&%&%%%%%%%%&&%#((///(((#######%%%
    ,,,,,,,,*(%&&%&&&&&&(,.,,,,,,,,,,*%&&&&%#((#%%&%%%%%%%&%%((((#%&&&&%&&%%%%%%%%%%
    ,,,,,,,,,,,,,*****,.,,,,,,,,,,,,/%&&&&%#((#%%%&%%%%&&%#%%&&&&%%%%%%%%%%%%%%%%%%%
    """
    _DEVICE_HISTORY_HANDLER: t.Dict[str, DeviceHistoryGeneric] = {
        ButtonHistory.DEVICE_TYPE: ButtonHistory,
        BooleanHistory.DEVICE_TYPE: BooleanHistory,
    }
    history: t.Sequence[TimeEntry]

    def __init__(self, devices: t.Dict[str, str], history_dict: t.Dict[str, t.Sequence[dict]]):
        self.history = []
        self.devices = {device: self._DEVICE_HISTORY_HANDLER[d_type] for device, d_type in devices.items()}

        for device, history in history_dict.items():
            logger.debug(f"Adding device {device}")
            for e in history:
                self.history.append(TimeEntry(
                    last_changed=datetime.fromisoformat(e['last_changed']),
                    device_name=device,
                    state=e['state']
                ))

        self.history = sorted(self.history, key=lambda a: a.last_changed)

    def generate_state_change_chain(self, episode_length: int = 30):
        i = 0
        delta = timedelta(seconds=episode_length)
        last_changed = {device: None for device in self.devices.keys()}
        ALL_DEVICES_EMPTY_STATE = {device: 0.0 for device in self.devices.keys()}

        logger.debug(f"Looking for episodes of max length {episode_length}")

        while self.history[i] != self.history[-1]:
            j = i
            up_to = self.history[i].last_changed + delta
            try:
                while self.history[j].last_changed < up_to:
                    j += 1
            except IndexError:
                j -= 1

            logger.debug(f"Found episode from {i} to {j}")

            device_changes = {self.history[k].device_name: self.history[k] for k in range(i, j)}
            
            computed_state = {
                device: self.devices[device].get_current_state(
                    last_changed[device],
                    device_changes[device],
                    up_to
                ) for device in device_changes.keys()
            }

            for device, entry in device_changes.items():
                last_changed[device] = entry
            
            state = {d: float(v[0]) for d,v in computed_state.items()}
            change = {d: float(v[1]) for d,v in computed_state.items()}

            state.update(time=self.history[i].last_changed.time())

            new_state = ALL_DEVICES_EMPTY_STATE.copy()
            new_state.update(state)
            
            yield new_state, change

            i = j
            