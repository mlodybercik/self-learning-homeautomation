from datetime import datetime
from io import BytesIO
from json import dumps, loads
from pathlib import Path
import typing as t
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import tensorflow as tf

from automation.utils import get_logger
from automation.models.manager import ModelManager
from automation.models.dnn import DNNAgent
from automation.models.converters import CONVERTERS


logger = get_logger(__name__)


class ModelSerializer:
    _buffer: t.Optional[BytesIO]
    _zip: t.Optional[ZipFile]
    model_path: Path

    def __init__(self, model_path: str, mode: str):
        self.model_path = Path(model_path).absolute()
        if self.model_path.is_dir():
            raise ValueError(f"{model_path} is a directory")
        self._buffer = None
        self._zip = None
        self.mode = mode

    def __enter__(self):
        logger.debug(f"Entering into zip {self.model_path}")
        self._buffer = BytesIO()
        if self.mode == "r":
            with open(self.model_path, "rb") as file:
                self._buffer.write(file.read())
        self._zip = ZipFile(self._buffer, self.mode, ZIP_DEFLATED)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._zip.close()
        if self.mode == "w":
            with open(self.model_path, "wb") as file:
                file.write(self._buffer.getbuffer())
        self._buffer.close()

        self._buffer = None
        self._zip = None

    def _save_model_to_zip(self, name: str, model: tf.keras.Model):
        logger.debug("Writing single model to zip...")
        if not self._zip:
            raise RuntimeError("class should be handled only with with keyword")
        if self.mode != "w":
            raise RuntimeError("tried to write to readonly file")

        model_declaration = model.get_config()
        model_weights = [i.tolist() for i in model.get_weights()]
        info = {
            "name": self.name,
            "create_time": datetime.now().isoformat(),
            "layers": len(model.layers),
        }

        self._zip.writestr(f"{name}/declaration.json", dumps(model_declaration).encode())
        self._zip.writestr(f"{name}/weights.json", dumps(model_weights).encode())
        self._zip.writestr(f"{name}/meta/info.json", dumps(info).encode())
        logger.debug("Done writing to zip")

    def _load_model_from_zip(self, name) -> t.Tuple[tf.keras.models.Model, dict]:
        # serializing and deserializing in this way requires the whole model to
        # to be decompressed into memory, and then loaded as a model. this could
        # cause problems when handling huge models

        model_declaration = loads(self._zip.read(f"{name}/declaration.json").decode())
        model_weights = [np.array(layer) for layer in loads(self._zip.read(f"{name}/weights.json").decode())]

        info = loads(self._zip.read(f"{name}/meta/info.json").decode())
        if info["name"] != self.name:
            logger.warning(f"Loaded filename doesn't match model name '{info['name']}' != '{self.name}'")

        model = tf.keras.Model.from_config(model_declaration)
        model.set_weights(model_weights)

        return model, info

    def save_manager_to_archive(self, manager: ModelManager):
        logger.debug("Saving manager")
        if not self._zip:
            raise RuntimeError("class should be handled only with with keyword")
        if self.mode != "w":
            raise RuntimeError("tried to write to readonly file")

        info = {
            "converters": {device: CONVERTERS[converter.TYPE] for device, converter in manager.converters.items()},
            "agents": list(manager.agents.keys())
        }

        for device, agent in manager.agents.items():
            self._save_model_to_zip(device, agent.model)

        self._zip.writestr("info.json", dumps(info).encode())
        


    def load_manager_from_archive(self) -> ModelManager:
        info = loads(self._zip.read("info.json").decode())
        converters = {}
        agents = {}

        for device, converter_type in info['converters'].items():
            converters[device] = CONVERTERS[converter_type]

        for device in info['agents']:
            model, _ = self._load_model_from_zip(device)
            agents[device] = DNNAgent(model=model)

        return ModelManager(agents, converters)
