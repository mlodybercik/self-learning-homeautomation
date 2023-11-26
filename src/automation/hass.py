import os
import typing as t
from datetime import datetime
from pathlib import Path

from appdaemon.plugins.hass import hassapi as hass

from automation.collector.data import Collector
from automation.collector.state import StateCollector
from automation.models.converters import AnyConvertable, TimeCosConvertable
from automation.models.manager import ModelManager
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
                inputs = set(info["converters"].keys())
                _ = set(info["agents"])

                # TODO: change this to remove "not-device" inputs like time or other apis (weather)
                inputs.remove("time")

                if not (diff := set(self.args["devices"].keys()).difference(inputs)):
                    return serializer.load_manager_from_archive()

            self.log(f"Found difference <{', '.join(diff)}>")

            now = datetime.now().strftime("%Y%M%d%H%M%S")
            new_name = model_location.absolute().parent / f"{now}_{model_location.name}"
            self.log(f"Moving old model to {new_name}")
            model_location.rename(new_name)

        except FileNotFoundError:
            self.log(f"Could not open {model_location}")

        self.log("Creating new models...")

        # FIXME: this could lock-up the app
        collector = Collector(
            self.args["devices"],
            {device: self.get_history(entity_id=device, days=31)[0] for device in self.args["devices"].keys()},
        )

        agent = ModelManager.from_raw(
            {"time": TimeCosConvertable(), **{d: AnyConvertable() for d in self.args["devices"].keys()}},
            list(self.args["devices"].keys()),
        )

        X, Y = [], []
        for x, y in collector.generate_state_change_chain():
            X.append(x)
            Y.append(y)

        self.log(f"{X[:10]} {Y[:10]}")

        self.log(f"Found {len(X)} episodes to learn.")

        # FIXME: tasks that spin for long amount of time could be terminated by AD
        pre_X, pre_Y = agent.generate_empty_actions()
        agent.fit(pre_X, pre_Y, 1, batch_size=1)
        agent.fit(X[:-1], Y[:-1], 5, batch_size=1)

        with ModelSerializer(model_location, "w") as serializer:
            serializer.save_manager_to_archive(agent)
        self.log(f"Model saved to: {model_location}")

        return agent

    def get_current_state(self):
        current_state = self.state_collector.parse_state_change(
            {device: self.get_state(entity_id=device, attribute="all") for device in self.args["devices"].keys()}
        )
        current_state["time"] = get_utc_now().time()
        return current_state

    def initialize(self):
        self.logger = get_logger("hass", "INFO")
        self.state_collector = StateCollector(self.args["devices"])

        self._ignore_changes = {device: False for device in self.args["devices"].keys()}
        self._previous_state = self.get_current_state()

        self.agent = self._create_agent(MODEL_PACKAGE_LOCATION)

        self.log("Registering event handler")
        self.listen_state(self.state_changed, list(self.args["devices"].keys()))

    def state_changed(self, entity: str, attribute: str, old: str, new: str, cb_args: dict):
        # _current_state = self.get_current_state()
        _current_state = self._previous_state.copy()
        _current_state[entity] = new

        if self._ignore_changes[entity]:
            self._ignore_changes[entity] = False
            self._previous_state = _current_state
            return

        self.log(f"Entity <{entity}> changed its attribute <{attribute}> from <{old}> to <{new}>")

        predicted_actions_for_previous_state = self.agent.predict_single(self._previous_state)

        # self.log(f"Previous_state: {self._previous_state}")
        # self.log(f"Raw predicted actions for previous_state: {raw_predicted_actions_for_previous_state}")
        # self.log(f"Predicted actions {predicted_actions}")

        if not self.state_collector.compare_actions(
            self._previous_state, _current_state, predicted_actions_for_previous_state
        ):
            # execute actions only when they are consistent with user actions:
            self._previous_state = _current_state
            self.log("Machine actions are not consistent with user inputs, ignoring")
            return

        functions = self.state_collector.create_state_change_functions(
            predicted_actions_for_previous_state, _current_state
        )

        self.log("Executing predicted changes")

        for device, function in functions.items():
            if device == entity:
                # one of the changes has been done
                continue

            if function:
                self._ignore_changes[device] = True
                function(self)
