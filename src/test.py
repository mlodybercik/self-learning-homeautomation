import math
import random
from datetime import datetime, time

from automation.collector.data import Collector
from automation.models.converters import AnyConvertable, BinaryTimeConverter
from automation.models.manager import ModelManager
from automation.models.serializer import ModelSerializer


def seconds():
    return math.floor(60 * random.random())


def minutes():
    return math.floor(60 * random.random())


def hours():
    return math.floor(24 * random.random())


random.seed(0x2137)


def get_kuchnia():
    ret = []
    for i in range(10, 30):
        ret.extend(
            [
                {
                    "entity_id": "kuchnia",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 5, 30, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 7, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 16, 20, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 16, 37, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 21, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 22, 15, seconds()).isoformat(),
                },
            ]
        )
    return ret


def get_ekspres():
    ret = []
    for i in range(10, 30):
        ret.extend(
            [
                {
                    "entity_id": "ekspres",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 5, 30, seconds()).isoformat(),
                },
                {
                    "entity_id": "ekspres",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 7, 32, seconds()).isoformat(),
                },
                {
                    "entity_id": "ekspres",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 16, 30, seconds()).isoformat(),
                },
                {
                    "entity_id": "ekspres",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 16, 37, seconds()).isoformat(),
                },
            ]
        )
    return ret


def get_swiatla_salon():
    ret = []
    for i in range(10, 30):
        ret.extend(
            [
                {
                    "entity_id": "swiatla_salon",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 16, 38, seconds()).isoformat(),
                },
                {
                    "entity_id": "swiatla_salon",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 21, 35, seconds()).isoformat(),
                },
            ]
        )
    return ret


def get_telewizor():
    ret = []
    for i in range(10, 30):
        ret.extend(
            [
                {
                    "entity_id": "telewizor",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 16, 38, seconds()).isoformat(),
                },
                {
                    "entity_id": "telewizor",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 21, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "telewizor",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 6, 38, seconds()).isoformat(),
                },
                {
                    "entity_id": "telewizor",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 7, 33, seconds()).isoformat(),
                },
            ]
        )
    return ret


def get_swiatla_balkon():
    ret = []
    for i in range(10, 30):
        ret.extend(
            [
                {
                    "entity_id": "swiatla_balkon",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 5, 31, seconds()).isoformat(),
                },
                {
                    "entity_id": "swiatla_balkon",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 22, 40, seconds()).isoformat(),
                },
            ]
        )
    return ret


def get_lampka_sypialnia():
    ret = []
    for i in range(10, 30):
        ret.extend(
            [
                {
                    "entity_id": "lampka_sypialnia",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 22, 15, seconds()).isoformat(),
                },
                {
                    "entity_id": "lampka_sypialnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 22, 40, seconds()).isoformat(),
                },
            ]
        )
    return ret


a = Collector(
    {
        "kuchnia": "bool",
        "ekspres": "bool",
        "swiatla_salon": "bool",
        "telewizor": "bool",
        "swiatla_balkon": "bool",
        "lampka_sypialnia": "bool",
    },
    {
        "kuchnia": get_kuchnia(),
        "ekspres": get_ekspres(),
        "swiatla_salon": get_swiatla_salon(),
        "telewizor": get_telewizor(),
        "swiatla_balkon": get_swiatla_balkon(),
        "lampka_sypialnia": get_lampka_sypialnia(),
    },
)

X, Y = [], []
for x, y in a.generate_state_change_chain():
    X.append(x)
    Y.append(y)

agent = ModelManager.from_raw(
    {"time": BinaryTimeConverter(), **{k: AnyConvertable() for k in a.devices.keys()}}, [k for k in a.devices.keys()]
)


# pre_X, pre_Y = agent.generate_empty_actions(1000)
gen_X, gen_Y = agent.generate_dummy_values(X[:-1], Y[:-1], amount=5)
print(len(gen_X))
print(len(X))
agent.fit(gen_X + X[:-1], gen_Y + Y[:-1], 16, 32)

# agent.fit(X[:-1], Y[:-1], 4, 16)

with ModelSerializer("/tmp/model.ha", "w") as ha:
    ha.save_manager_to_archive(agent)


_state = {
    "kuchnia": 1.0,
    "ekspres": 1.0,
    "swiatla_salon": 0.0,
    "telewizor": 0.0,
    "swiatla_balkon": 0.0,
    "lampka_sypialnia": 0.0,
}

_to_be_tested = []
for hour in range(24):
    state = _state.copy()
    state["time"] = time(hour=hour)
    _to_be_tested.append(state)

tested = agent.predict(_to_be_tested)

print("\t" + "\t".join([i[:5] for i in _state.keys()]))
for hour in range(24):
    prepd = "\t".join([f"{tested[device][hour][0]:+0.2f}" for device in _state.keys()])
    print(f"Hour {hour:2d}: {prepd}")
