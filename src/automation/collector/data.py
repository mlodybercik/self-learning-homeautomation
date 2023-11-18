import typing as t
from datetime import datetime

from automation.collector.device_history import DEVICE_HISTORY_HANDLER, TimeEntry
from automation.utils import get_logger

from . import EPISODE_DELTA

logger = get_logger("collector.data")


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

    history: t.Sequence[TimeEntry]

    def __init__(self, devices: t.Dict[str, str], history_dict: t.Dict[str, t.Sequence[dict]]):
        self.history = []
        self.devices = {device: DEVICE_HISTORY_HANDLER[d_type] for device, d_type in devices.items()}

        for device, history in history_dict.items():
            logger.debug(f"Adding device {device}")
            for e in history:
                self.history.append(
                    TimeEntry(
                        last_changed=datetime.fromisoformat(e["last_changed"]), device_name=device, state=e["state"]
                    )
                )

        self.history = sorted(self.history, key=lambda a: a.last_changed)

    def generate_state_change_chain(self):
        i = 0

        last_changed = {device: None for device in self.devices.keys()}
        ALL_DEVICES_EMPTY_STATE = {device: 0.0 for device in self.devices.keys()}
        ALL_DEVICES_EMPTY_CHANGE = {device: 0.0 for device in self.devices.keys()}

        logger.debug(f"Looking for episodes of max length {EPISODE_DELTA.total_seconds()}")

        while self.history[i] != self.history[-1]:
            j = i
            up_to = self.history[i].last_changed + EPISODE_DELTA
            try:
                while self.history[j].last_changed < up_to:
                    j += 1
            except IndexError:
                j -= 1

            logger.debug(f"Found episode from {i} to {j}")

            device_changes = {self.history[k].device_name: self.history[k] for k in range(i, j)}

            computed_state = {
                device: self.devices[device].get_past_state(device_changes[device], last_changed[device], up_to)
                for device in device_changes.keys()
            }

            for device, entry in device_changes.items():
                last_changed[device] = entry

            state = {d: float(v[0]) for d, v in computed_state.items()}
            change = {d: float(v[1]) for d, v in computed_state.items()}

            state.update(time=self.history[i].last_changed.time())

            full_state = ALL_DEVICES_EMPTY_STATE.copy()
            full_state.update(state)

            full_change = ALL_DEVICES_EMPTY_CHANGE.copy()
            full_change.update(change)

            yield full_state, full_change

            i = j
