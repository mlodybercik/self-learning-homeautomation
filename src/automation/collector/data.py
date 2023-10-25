import typing as t
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dataclasses import dataclass
from appdaemon.plugins.hass import hassapi

@dataclass
class TimeEntry:
    last_changed: datetime
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
    WINDOW_LENGTH: int = 300
    DEVICE_TYPE: str
    history: 't.Sequence[TimeEntry]'

    def __init__(self, device_name: str, history: t.Sequence[t.Dict[str, t.Any]]) -> None:
        self.device_name = device_name

        self.history = sorted([TimeEntry(datetime.fromisoformat(e['last_changed']), e['state']) for e in history])

    @abstractmethod
    def get_state_at(self, time: datetime, window_length: int = WINDOW_LENGTH): ...


    def search_for_time(self, time: datetime) -> int:
        assert len(self.history) > 2
        L, R = 0, len(self.history) - 1

        while L <= R:
            M = ((L + R) // 2)
            if self.history[M].last_changed <= time:
                L = M + 1
            elif self.history[M].last_changed >= time:
                R = M - 1
            else: 
                return M
        return M
        

            
    def get_time_span(self) -> t.Tuple[datetime, datetime]:
        return self.history[0].last_changed, self.history[-1].last_changed
    
    def get_actions_from_to(self, time_start: datetime, seconds: int) -> t.Sequence[t.Tuple[TimeEntry, int]]:
        ret = []
        up_to = time_start + timedelta(seconds=seconds)
        i = self.search_for_time(time_start)
        while self.history[i].last_changed < time_start:
            i += 1

        while self.history[i].last_changed < up_to:
            ret.append((self.history[i], 1))
            i += 1
        return ret


class BooleanHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "bool"
    STATES = {"off": -1, "on": 1}

    def get_state_at(self, time: datetime, window_length: int = DeviceHistoryGeneric.WINDOW_LENGTH):
        # back                                 now
        # <-x--------- - - 10 minutes - - ------x------>
        # if time is inbetween back and now it could happen that the state is 0,
        # because the window_length is greater, we have to check and return appropriate state

        i = self.search_for_time(time)
        back, now = self.history[i - 1], self.history[i]

        if time < now.last_changed:
            seconds = (time - back.last_changed).total_seconds()
        elif time > now.last_changed:
            seconds = (time - now.last_changed).total_seconds()
        else:
            seconds = window_length + 1
        
        if seconds > window_length: 
            return 0
        return __class__.STATES[back.state]

    

class ButtonHistory(DeviceHistoryGeneric):
    DEVICE_TYPE = "button"

    def get_state_at(self, time: datetime, window_length: int = DeviceHistoryGeneric.WINDOW_LENGTH):
        i = self.search_for_time(time)
        back, now = self.history[i - 1], self.history[i]

        if time < now.last_changed:
            seconds = (time - back.last_changed).total_seconds()
        elif time > now.last_changed:
            seconds = (time - now.last_changed).total_seconds()
        else:
            seconds = window_length + 1

        if seconds > window_length: 
            return 0
        return 1
    


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
    devices: t.Dict[str, DeviceHistoryGeneric]
    _min_time: datetime
    _max_time: datetime

    def __init__(self, devices: t.Dict[str, str], history_dict: t.Dict[str, t.Any]):
        self.devices = {}

        for device, handler in devices.items():
            cls = __class__._DEVICE_HISTORY_HANDLER[handler]
            self.devices[device] = cls(device_name=device, history=history_dict[device])

        times = [handler.get_time_span() for handler in self.devices.values()]
        self._min_time = max(i[0] for i in times)
        self._max_time = min(i[1] for i in times)
            

    def get_state_at(self, time: datetime):
        # if time > self._max_time or time < self._min_time:
        #     raise AttributeError('not enough data to get state in that period')
        
        return {device: handler.get_state_at(time) for device, handler in self.devices.items()}
    
    def get_state_history(self, episode_length: int = 30):
        current_time = self._min_time
        delta = timedelta(seconds=episode_length)

        while (current_time := current_time + delta) < self._max_time:
            state = {device: handler.get_state_at(current_time, episode_length) for device, handler in self.devices.items()}
            state.update(time=current_time.time())
            yield state


    def generate_state_change_history(self, episode_length: int = 30):
        minimum_time = lambda a: a[0].last_changed
        current_state = {d: 0 for d in self.devices.keys()}
        current_index = current_state.copy()

        while all(index < len(self.devices[device].history) for device, index in current_index.items()):
            entry, device = min(
                ((self.devices[device].history[current_index[device]], device) for device in current_index.keys()),
                key=minimum_time
            )

            updates = {device: handler.get_actions_from_to(entry.last_changed, episode_length) for device, handler in self.devices.items()}
            for device in updates.keys():
                if updates[device]:
                    current_index[device] = max(updates[device][-1][1] + 1, current_index[device]) 
            print(current_state)