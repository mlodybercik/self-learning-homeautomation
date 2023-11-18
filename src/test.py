import math
import random
from datetime import datetime

from automation.collector.data import Collector
from automation.models.converters import AnyConvertable, BinaryTimeConverter
from automation.models.manager import ModelManager
from automation.models.serializer import ModelSerializer

seconds = lambda: 60 * math.floor(random.random())


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
                    "last_changed": datetime(2023, 10, i, 16, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 17, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 21, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 22, 00, seconds()).isoformat(),
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
                    "last_changed": datetime(2023, 10, i, 16, 35, seconds()).isoformat(),
                },
                {
                    "entity_id": "kuchnia",
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
                    "last_changed": datetime(2023, 10, i, 16, 40, seconds()).isoformat(),
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
                    "last_changed": datetime(2023, 10, i, 16, 40, seconds()).isoformat(),
                },
                {
                    "entity_id": "telewizor",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 21, 35, seconds()).isoformat(),
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
                    "last_changed": datetime(2023, 10, i, 5, 31, 40, seconds()).isoformat(),
                },
                {
                    "entity_id": "swiatla_balkon",
                    "state": "on",
                    "last_changed": datetime(2023, 10, i, 22, 40, 40, seconds()).isoformat(),
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
                    "last_changed": datetime(2023, 10, i, 22, 00, 50, seconds()).isoformat(),
                },
                {
                    "entity_id": "lampka_sypialnia",
                    "state": "off",
                    "last_changed": datetime(2023, 10, i, 22, 40, 50, seconds()).isoformat(),
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
gen_X, gen_Y = agent.generate_dummy_values(X[:-1], Y[:-1], amount=100)

print(len(gen_X))

# train_X = X[:-1] + gen_X#  + pre_X
# train_Y = Y[:-1] + gen_Y#  + pre_Y

agent.fit(gen_X, gen_Y, 16, 16)

with ModelSerializer("/tmp/model.ha", "w") as ha:
    ha.save_manager_to_archive(agent)
