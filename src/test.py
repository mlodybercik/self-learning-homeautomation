from datetime import datetime
from automation.collector.data import Collector
from automation.models.manager import ModelManager
from automation.models.converters import AnyConvertable, TimeConvertable
from automation.models.serializer import ModelSerializer

device0 = [
    {
        "entity_id": "input_boolean.test_switch_1",
        "state": "on" if (i % 2) else "off",
        "last_changed": datetime(2023, 10, j, i, 0, 0).isoformat(),
    }
    for j in range(10, 20) for i in range(4, 20)
]

device1 = [
    {
        "entity_id": "input_boolean.test_switch_2",
        "state": "on" if (i % 2) else "off",
        "last_changed": datetime(2023, 10, j, i, 0, 15).isoformat(),
    }
    for j in range(10, 20) for i in range(4, 20)
]

a = Collector(
    {'input_boolean.test_switch_1': 'bool', 'input_boolean.test_switch_2': 'bool'},
    {'input_boolean.test_switch_1': device0, 'input_boolean.test_switch_2': device1}
)

X, Y = [], []
for x, y in a.generate_state_change_chain():
    X.append(x)
    Y.append(y)

agent = ModelManager.from_raw(
    {
        'time': TimeConvertable(),
        'input_boolean.test_switch_1': AnyConvertable(),
        'input_boolean.test_switch_2': AnyConvertable()
    },
    ['input_boolean.test_switch_1', 'input_boolean.test_switch_2']
)

pre_X, pre_Y = agent.generate_empty_actions()
agent.fit(pre_X, pre_Y, 1)
agent.fit(X[:-1], Y[:-1], 5)

with ModelSerializer("/tmp/model.ha", "w") as ha:
    ha.save_manager_to_archive(agent)