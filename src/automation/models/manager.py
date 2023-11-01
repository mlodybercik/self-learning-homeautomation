import typing as t
from automation.models.dnn import DNNAgent
from automation.models.converters import Convertable, TimeConvertable
from automation.utils import get_logger
from datetime import time
import numpy as np
import math

get_time = lambda x: time(hour=(hours := x // 3600), minute=(x - (hours * 3600)) // 60, second=x % 60)

logger = get_logger("models.manager")

class ModelManager:
    agents: t.Dict[str, DNNAgent] = {}
    converters: t.Dict[str, Convertable] = {}

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


    def fit(self, x: t.Sequence[dict], y: t.Sequence[dict], epochs: int):
        x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}

        for name, agent in self.agents.items():
            y_new = {name: np.array([d[name] for d in y])}
            logger.debug(f"training {name}")
            agent.train(x, y_new, epochs=epochs)

    def predict(self, x: t.Sequence[dict]):
        x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}
        ret = {}
        for _, agent in self.agents.items():
            ret.update(agent.predict(x))
        return ret
    
    def generate_empty_actions(self, n: int = 1000, time_param = "time"):
        Y = [{output: 0.0 for output in self.agents.keys()} for _ in range(n)]
        X = []
        for i in range(n):
            x = dict.fromkeys(self.converters.keys(), 0.0)
            x.update({time_param: get_time(math.floor((i / n) * TimeConvertable.SECONDS_IN_A_DAY))})
            X.append(x)

        return X, Y
                     
        

