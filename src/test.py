from datetime import datetime
from automation.collector.data import Collector

device0 = [
    {
        "entity_id": "input_boolean.test_switch_1",
        "state": "on",
        "last_changed": "2023-10-23T14:32:59.740067+00:00",
    },
    {
        "entity_id": "input_boolean.test_switch_1",
        "state": "off",
        "last_changed": "2023-10-23T15:35:00.120265+00:00",
    },
    {
        "entity_id": "input_boolean.test_switch_1",
        "state": "on",
        "last_changed": "2023-10-23T16:40:00.368812+00:00",
    },
    {
        "entity_id": "input_boolean.test_switch_1",
        "state": "off",
        "last_changed": "2023-10-23T17:40:00.368812+00:00",
    }
]

device1 = [
    {
        "entity_id": "input_boolean.test_switch_2",
        "state": "on",
        "last_changed": "2023-10-23T14:32:55.740067+00:00",
    },
    {
        "entity_id": "input_boolean.test_switch_2",
        "state": "off",
        "last_changed": "2023-10-23T15:34:55.120265+00:00",
    },
    {
        "entity_id": "input_boolean.test_switch_2",
        "state": "on",
        "last_changed": "2023-10-23T16:39:55.368812+00:00",
    },
    {
        "entity_id": "input_boolean.test_switch_2",
        "state": "off",
        "last_changed": "2023-10-23T17:39:55.368812+00:00",
    }
]


a = Collector(
    {'input_boolean.test_switch_1': 'bool', 'input_boolean.test_switch_2': 'bool'},
    {'input_boolean.test_switch_1': device0, 'input_boolean.test_switch_2': device1}
)
a.generate_state_change_history()