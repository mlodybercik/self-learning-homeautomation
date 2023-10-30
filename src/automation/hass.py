from appdaemon.plugins.hass import hassapi as hass

from automation.collector.data import Collector
from automation.models.manager import ModelManager
from automation.models.converters import AnyConvertable, TimeConvertable

# Declare Class
class DeepNetwork(hass.Hass):
    agent: ModelManager

    def initialize(self):

        # TODO: this could lock-up the app
        collector = Collector(
            self.args['devices'],
            {device: self.get_history(entity_id=device, days=31)[0] for device in self.args['devices'].keys()}
        )

        self.agent = ModelManager.from_raw(
            {'time': TimeConvertable(), **{d: AnyConvertable() for d in self.args['devices'].keys()}},
            list(self.args['devices'].keys())
        )

        X, Y = [], []
        for x, y in collector.generate_state_change_chain():
            X.append(x)
            Y.append(y)

        self.log(f"{X[:5]}")
        self.log(f"{Y[:5]}")

        # FIXME: tasks that spin for long amount of time could be terminated by AD
        pre_X, pre_Y = self.agent.generate_empty_actions()
        self.agent.fit(pre_X, pre_Y, 1)
        self.agent.fit(X[:-1], Y[:-1], 5)

    def state_changed(self, entity, attribute, old, new, cb_args):
        self.log(f"Entity <{entity}> changed its attribute <{attribute}> from <{old}> to <{new}>")
