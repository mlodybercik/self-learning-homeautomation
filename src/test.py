from datetime import datetime, time
from random import random
from automation.collector.data import Collector
from automation.models.manager import ModelManager
from automation.models.converters import AnyConvertable, TimeConvertable
from automation.models.serializer import ModelSerializer

def create_device(n, days, d_skip, hours, h_skip):
    return [
        {
            "entity_id": f"input_boolean.test_switch_{n}",
            "state": "on" if (i % 2) else "off",
            "last_changed": datetime(2023, 10, day, hour, 0, round(random() * 10)).isoformat(),
        }
        for day in range(days[0], days[1]) for i, hour in enumerate(range(hours[0], hours[1], h_skip))
    ]


a = Collector(
    {f'input_boolean.test_switch_{n+1}': 'bool' for n in range(9)},
    {
        'input_boolean.test_switch_1': create_device(1, (5, 20), 1, (6, 19), 4),  # + create_device(1, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_2': create_device(2, (5, 20), 1, (6, 19), 4),  # + create_device(2, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_3': create_device(3, (5, 20), 1, (6, 19), 4),  # + create_device(3, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_4': create_device(4, (20, 20), 1, (16, 18), 1), # + create_device(4, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_5': create_device(5, (20, 20), 1, (16, 18), 1), # + create_device(5, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_6': create_device(6, (20, 20), 1, (16, 18), 1), # + create_device(6, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_7': create_device(7, (20, 20), 1, (16, 18), 1), # + create_device(7, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_8': create_device(8, (20, 20), 1, (12, 14), 1), # + create_device(8, (13, 20), 1, (11, 13), 1),
        'input_boolean.test_switch_9': create_device(9, (20, 20), 1, (16, 18), 1), # + create_device(9, (13, 20), 1, (11, 13), 1),
    }
)

X, Y = [], []
values_dict = {}
for x, y in a.generate_state_change_chain():
    X.append(x.copy())
    Y.append(y)
    x.pop("time")
    values_dict[tuple(x.values())] = tuple(y.values())

agent = ModelManager.from_raw(
    {
        'time': TimeConvertable(),
        **{f'input_boolean.test_switch_{n+1}': AnyConvertable() for n in range(9)}
    },
    [f'input_boolean.test_switch_{n+1}' for n in range(9)]
)


pre_X, pre_Y = agent.generate_empty_actions(1000)
print(len(X), len(pre_X))
for _ in range(2):
    agent.fit(pre_X, pre_Y, 1, batch_size=1)
    agent.fit(X[:-1], Y[:-1], 2, batch_size=1)

_state = {
    'input_boolean.test_switch_1': 0.0,
    'input_boolean.test_switch_2': 0.0,
    'input_boolean.test_switch_3': 0.0,
    'input_boolean.test_switch_4': 0.0,
    'input_boolean.test_switch_5': 0.0,
    'input_boolean.test_switch_6': 0.0,
    'input_boolean.test_switch_7': 0.0,
    'input_boolean.test_switch_8': 0.0,
    'input_boolean.test_switch_9': 0.0,
}

_to_be_tested = []
for hour in range(4, 20):
    state = _state.copy()
    state["time"] = time(hour=hour)
    _to_be_tested.append(state)

print(agent.predict(_to_be_tested))

with ModelSerializer("/tmp/model.ha", "w") as ha:
    ha.save_manager_to_archive(agent)

# 1
# 2
# 3
# 4
# 5
# 6
# 7
# 8
# 9