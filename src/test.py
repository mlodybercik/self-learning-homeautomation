from datetime import datetime
from automation.collector.data import Collector
from automation.models.manager import ModelManager
from automation.models.converters import AnyConvertable, TimeConvertable
from automation.models.serializer import ModelSerializer

get_device = lambda n, d: [
    {
        "entity_id": f"input_boolean.test_switch_{n}",
        "state": "on" if (i % 2) else "off",
        "last_changed": datetime(2023, 10, j, i, 0, d).isoformat(),
    }
    for j in range(10, 20) for i in range(4, 20)
]

a = Collector(
    {f'input_boolean.test_switch_{n+1}': 'bool' for n in range(9)},
    {f'input_boolean.test_switch_{n+1}': get_device(n, n*2) for n in range(9)}
)

X, Y = [], []
for x, y in a.generate_state_change_chain():
    X.append(x)
    Y.append(y)

agent = ModelManager.from_raw(
    {
        'time': TimeConvertable(),
        **{f'input_boolean.test_switch_{n+1}': AnyConvertable() for n in range(9)}
    },
    [f'input_boolean.test_switch_{n+1}' for n in range(9)]
)

pre_X, pre_Y = agent.generate_empty_actions()
agent.fit(pre_X, pre_Y, 1)
agent.fit(X[:-1], Y[:-1], 5)

with ModelSerializer("/tmp/model.ha", "w") as ha:
    ha.save_manager_to_archive(agent)