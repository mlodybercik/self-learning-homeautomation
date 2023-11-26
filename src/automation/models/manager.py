import math
import typing as t
from collections import defaultdict
from datetime import time, timedelta
from random import choice, random

import numpy as np

from automation.models.converters import (
    SECONDS_IN_A_DAY,
    CompoundConvertable,
    Convertable,
)
from automation.models.dnn import DNNAgent
from automation.utils import get_logger

get_time = lambda x: time(hour=(hours := x // 3600), minute=(x - (hours * 3600)) // 60, second=x % 60)

logger = get_logger("models.manager")


def _generate_repeatedly(func, *args, **kwargs):
    while True:
        yield func(*args, **kwargs)


class ModelManager:
    agents: t.Dict[str, DNNAgent]
    converters: t.Dict[str, Convertable]
    real_inputs: t.Sequence[str]

    def __init__(
        self,
        agents: t.Dict[str, DNNAgent],
        converters: t.Dict[str, Convertable],
        real_inputs: t.Optional[t.Sequence[str]] = None,
    ):
        self.agents = agents
        self.converters = converters
        self.real_inputs = real_inputs if real_inputs else converters.keys()

    @classmethod
    def from_raw(cls, inputs: t.Dict[str, Convertable], outputs: t.Sequence[str]):
        agents = {}
        real_inputs = []

        for input, converter in inputs.items():
            if isinstance(converter, CompoundConvertable):
                real_inputs.extend(converter.TYPES.keys())
            else:
                real_inputs.append(input)

        for name in outputs:
            agents[name] = DNNAgent.from_raw(real_inputs, [name])

        logger.debug(
            f"Creating manager for inputs <{', '.join(real_inputs)}> " + f"and outputs <{', '.join(agents.keys())}>"
        )

        return cls(agents, inputs, real_inputs)

    def _convert(self, x: t.Sequence[dict]):
        real_x = []
        for item in x:
            entry = {}
            for device, value in item.items():
                converted = self.converters[device].convert_to(value)
                if isinstance(converted, dict):
                    entry.update(converted)
                else:
                    entry[device] = converted
            real_x.append(entry)
        return {i: np.array([d[i] for d in real_x]) for i in self.real_inputs}

    def fit(self, x: t.Sequence[dict], y: t.Sequence[dict], epochs: int, batch_size=16):
        # x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}
        x = self._convert(x)

        for name, agent in self.agents.items():
            y_new = {name: np.array([d[name] for d in y])}
            logger.debug(f"training {name}")
            history = agent.train(x, y_new, epochs=epochs, batch_size=batch_size)
            logger.debug(f"Last loss = {history.history['loss'][-1]:4e}")

    def predict(self, x: t.Sequence[dict]):
        # x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}
        x = self._convert(x)

        ret = {}
        for agent_name, agent in self.agents.items():
            ret[agent_name] = self.converters[agent_name].convert_from(agent.predict(x)[agent_name])
        return ret

    def predict_single(self, x: dict):
        return {agent: self.predict([x])[agent].numpy().item() for agent in self.agents.keys()}

    @staticmethod
    def apply_round(x: t.Dict[str, float]):
        return {i: np.round(j) for i, j in x.items()}

    def generate_empty_actions(self, n: int = 1000, time_param="time", _random=False):
        X = []
        Y = [{output: 0.0 for output in self.agents.keys()} for _ in range(n)]
        if _random:
            for i in range(n):
                x = {output: float(random() > 0.5) for output in self.agents.keys()}
                x.update({time_param: get_time(math.floor((i / n) * SECONDS_IN_A_DAY))})
                X.append(x)
        else:
            for i in range(n):
                x = dict.fromkeys(self.agents.keys(), 0.0)
                x.update({time_param: get_time(math.floor((i / n) * SECONDS_IN_A_DAY))})
                X.append(x)

        return X, Y

    def generate_dummy_values(
        self,
        x: t.Sequence[t.Dict[str, float]],
        y: t.Sequence[t.Dict[str, float]],
        time_param="time",
        width=0.075,
        amount=100,
        clip=(0.75, 0.90),
    ):
        X = []
        Y = []
        time_value_dict = defaultdict(list)
        change_value_dict = defaultdict(set)

        labels = list(x[0].keys())
        del labels[labels.index(time_param)]

        for input_state, change in zip(x, y):
            state = input_state.copy()
            state_time = state.pop(time_param)

            time_value_dict[tuple(state.values())].append(state_time)
            change_value_dict[tuple(state.values())].add(tuple(change.values()))

        _range = np.linspace(0, 1, 1000, endpoint=False)

        for state, times in time_value_dict.items():
            time_range = np.zeros_like(_range, dtype=float)
            for _time in times:
                location = (
                    timedelta(hours=_time.hour, minutes=_time.minute, seconds=_time.second).total_seconds()
                    / SECONDS_IN_A_DAY
                )
                time_range += 1 / (width * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((_range - location) / width) ** 2)

            _x = np.clip(time_range.max() - time_range, clip[0], clip[1])
            _x -= _x.min()
            for new_time in np.random.choice(_range, amount * len(times), p=(_x / _x.sum())):
                new_state = {k: v for k, v in zip(x[0].keys(), state)}
                new_state[time_param] = get_time(math.floor((new_time * SECONDS_IN_A_DAY) % SECONDS_IN_A_DAY))
                X.append(new_state)
                Y.append({output: 0.0 for output in self.agents.keys()})

            for _, random_time, random_choice in zip(
                range(amount * len(times)),
                _generate_repeatedly(np.random.choice, list(times)),
                _generate_repeatedly(choice, list(change_value_dict[state])),
            ):
                new_state = {k: v for k, v in zip(x[0].keys(), state)}
                new_state[time_param] = random_time

                new_change = {k: v for k, v in zip(y[0].keys(), random_choice)}

                X.append(new_state)
                Y.append(new_change)

        return X, Y
