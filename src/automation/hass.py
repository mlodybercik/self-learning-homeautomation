from appdaemon.plugins.hass import hassapi as hass

import os
from pathlib import Path
from datetime import datetime

from automation.collector.data import Collector
from automation.models.manager import ModelManager
from automation.models.converters import AnyConvertable, TimeConvertable
from automation.models.serializer import ModelSerializer

MODEL_PACKAGE_LOCATION = Path(os.environ.get("MODEL_PACKAGE_LOCATION", "/models/model.ha")).absolute()

# Declare Class
class DeepNetwork(hass.Hass):
    agent: ModelManager

    def _create_agent(self, model_location: Path) -> ModelManager:
        try:
            with ModelSerializer(model_location, "r") as serializer:
                info = serializer.load_info_from_archive()

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


    def initialize(self):
        self.agent = self._create_agent(MODEL_PACKAGE_LOCATION)



    def state_changed(self, entity, attribute, old, new, cb_args):
        self.log(f"Entity <{entity}> changed its attribute <{attribute}> from <{old}> to <{new}>")
