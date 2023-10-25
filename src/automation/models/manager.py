import typing as t
from models.dnn import DNNAgent
from models.converters import Convertable
import numpy as np


class ModelManager:
    agents: t.Dict[str, DNNAgent] = {}
    converters: t.Dict[str, Convertable] = {}

    def __init__(self, inputs: t.Dict[str, Convertable], outputs: t.Sequence[str]):
        self.converters = inputs

        for name in outputs:
            self.agents[name] = DNNAgent(inputs.keys(), [name])


    def fit(self, x: t.Sequence[dict], y: t.Sequence[dict], epochs: int):
        x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}

        for name, agent in self.agents.items():
            y_new = {name: np.array([d[name] for d in y])}
            print(f"training {name}")
            agent.train(x, y_new, epochs=epochs)

    def predict(self, x: t.Sequence[dict]):
        x = {i: np.array([self.converters[i].convert_to(d[i]) for d in x]) for i in self.converters.keys()}
        ret = {}
        for _, agent in self.agents.items():
            ret.update(agent.predict(x))
        return ret