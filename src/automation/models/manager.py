import typing as t
from automation.models.dnn import DNNAgent
from automation.models.converters import Convertable, TimeConvertable
from automation.utils import get_logger
from datetime import time
import random
import numpy as np
import math

get_time = lambda x: time(hour=(hours := x // 3600), minute=(x - (hours * 3600)) // 60, second=x % 60)

logger = get_logger("models.manager")

class ModelManager:
    agents: t.Dict[str, DNNAgent]
    converters: t.Dict[str, Convertable]

    def __init__(self, agents: t.Dict[str, DNNAgent], converters: t.Dict[str, Convertable]):
        self.agents = agents
        self.converters = converters

    @classmethod
    def from_raw(cls, inputs: t.Dict[str, Convertable], outputs: t.Sequence[str]):
        agents = {}

        for name in outputs:
            agents[name] = DNNAgent.from_raw(inputs.keys(), [name])

        logger.debug(
            f"Creating manager for inputs <{', '.join(inputs.keys())}> " + \
            f"and outputs <{', '.join(agents.keys())}>"
        )

        return cls(agents, inputs)


    def fit(self, x: t.Sequence[dict], y: t.Sequence[dict], epochs: int, batch_size = 16):
        x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}

        for name, agent in self.agents.items():
            y_new = {name: np.array([d[name] for d in y])}
            logger.debug(f"training {name}")
            history = agent.train(x, y_new, epochs=epochs, batch_size=batch_size)
            logger.debug(f"Last loss = {history.history['loss'][-1]:4e}")

    def predict(self, x: t.Sequence[dict]):
        x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}
        ret = {}
        for agent in self.agents.values():
            ret.update(agent.predict(x))
        return ret
    
    def predict_single(self, x: dict):
        return {agent: self.predict([x])[agent].numpy().item() for agent in self.agents.keys()}
    
    @staticmethod
    def apply_round(x: t.Dict[str, float]):
        return {i: np.round(j) for i, j in x.items()}
    
    def generate_empty_actions(self, n: int = 1000, time_param = "time", random = False):
        Y = [{output: 0.0 for output in self.agents.keys()} for _ in range(n)]
        X = []
        if random:
            for i in range(n):
                x = {output: float(random.random() > 0.5) for output in self.agents.keys()}
                x.update({time_param: get_time(math.floor((i / n) * TimeConvertable.SECONDS_IN_A_DAY))})
                X.append(x)
        else:
            for i in range(n):
                x = dict.fromkeys(self.agents.keys(), 0.0)
                x.update({time_param: get_time(math.floor((i / n) * TimeConvertable.SECONDS_IN_A_DAY))})
                X.append(x)

        return X, Y
                     
        

