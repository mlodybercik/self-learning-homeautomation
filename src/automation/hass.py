import typing as t
from appdaemon.plugins.hass import hassapi as hass

import os
from pathlib import Path
from datetime import datetime

from automation.collector.data import Collector
from automation.collector.state import StateCollector
from automation.models.manager import ModelManager
from automation.models.converters import AnyConvertable, TimeConvertable
from automation.models.serializer import ModelSerializer
from automation.utils import get_logger, get_utc_now

MODEL_PACKAGE_LOCATION = Path(os.environ.get("MODEL_PACKAGE_LOCATION", "/models/model.ha")).absolute()

# Declare Class
class DeepNetwork(hass.Hass):
    agent: ModelManager
    _ignore_changes: t.Dict[str, bool]
    _current_state: t.Dict[str, float]

    def _create_agent(self, model_location: Path) -> ModelManager:
        try:
            with ModelSerializer(model_location, "r") as serializer:
                info = serializer.load_info_from_archive()

                # FIXME: when names dont change but type of device does it could lead to using wrong converter
                inputs = set(info['converters'].keys())
                outputs = set(info['agents'])

                # TODO: change this to remove "not-device" inputs like time or other apis (weather)
                inputs.remove("time")

                if not (diff := set(self.args['devices'].keys()).difference(inputs)):
                    return serializer.load_manager_from_archive()

            self.log(f"Found difference <{', '.join(diff)}>")

            now = datetime.now().strftime('%Y%M%d%H%M%S')
            new_name = model_location.absolute().parent / f"{now}_{model_location.name}"
            self.log(f"Moving old model to {new_name}")
            model_location.rename(new_name)

        except FileNotFoundError:
            self.log(f"Could not open {model_location}")

        self.log("Creating new models...")

        # FIXME: this could lock-up the app
        collector = Collector(
            self.args['devices'],
            {device: self.get_history(entity_id=device, days=31)[0] for device in self.args['devices'].keys()}
        )

        agent = ModelManager.from_raw(
            {'time': TimeConvertable(), **{d: AnyConvertable() for d in self.args['devices'].keys()}},
            list(self.args['devices'].keys())
        )

        X, Y = [], []
        for x, y in collector.generate_state_change_chain():
            X.append(x)
            Y.append(y)

        self.log(f"{X[:10]} {Y[:10]}")

        self.log(f"Found {len(X)} episodes to learn.")

        # FIXME: tasks that spin for long amount of time could be terminated by AD
        pre_X, pre_Y = agent.generate_empty_actions()
        agent.fit(pre_X, pre_Y, 1)
        agent.fit(X[:-1], Y[:-1], 5)


        with ModelSerializer(model_location, "w") as serializer:
            serializer.save_manager_to_archive(agent)
        self.log(f"Model saved to: {model_location}")

        return agent
    
    def get_current_state(self):
        current_state = self.state_collector.parse_state_change(
            {device: self.get_state(entity_id=device, attribute='all') for device in self.args['devices'].keys()}
        )
        current_state["time"] = get_utc_now().time()
        return current_state

    def initialize(self):
        self.logger = get_logger("hass", "INFO")
        self._ignore_changes = {device: False for device in self.args['devices'].keys()}
        self.state_collector = StateCollector(self.args['devices'])

        self._current_state = self.get_current_state()

        self.agent = self._create_agent(MODEL_PACKAGE_LOCATION)

        self.log("Registering event handler")
        self.listen_state(self.state_changed, list(self.args['devices'].keys()))


    def state_changed(self, entity: str, attribute: str, old: str, new: str, cb_args: dict):
        if self._ignore_changes[entity]:
            self._ignore_changes[entity] = False
            self.log(f"Entity <{entity}> changed its attribute, but has been ignored")
            return
        
        self.log(f"Entity <{entity}> changed its attribute <{attribute}> from <{old}> to <{new}>")

        current_state = self.get_current_state()
        y = self.agent.predict_single(current_state)
        functions = self.state_collector.create_state_change_functions(self.agent.apply_round(y))

        self.log("Executing predicted changes")

        for device, function in functions.items():
            if function:
                self._ignore_changes[device] = True

        for device, function in functions.items():
            if function:
                function(self)

