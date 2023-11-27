import json
import math
import random
from collections import defaultdict
from datetime import date, datetime
from functools import partial
from itertools import islice

import tensorflow as tf

import automation.models.converters
import automation.models.dnn
from automation.collector.data import Collector
from automation.models.converters import (
    SECONDS_IN_A_DAY,
    AnyConvertable,
    BinaryTimeConverter,
    CompoundTimeConverter,
    TimeCosConvertable,
)
from automation.models.manager import ModelManager, get_time

S = "state"
LC = "last_changed"
GENERATE_NOISE = False

V = (S, LC)


def reset_seeds():
    tf.keras.utils.set_random_seed(0x2137)
    random.seed(0x2137)


def batched(iterable, n):
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch


def fill_dict(input_dict: dict, key: list, value: list):
    copy = input_dict.copy()
    for k, v in zip(key, value):
        copy[k] = v
    return copy


def generate_random(d_: dict, i: int, *args):
    while True:
        off, on = sorted(
            (
                get_time(math.floor(random.random() * SECONDS_IN_A_DAY)),
                get_time(math.floor(random.random() * SECONDS_IN_A_DAY)),
            )
        )
        if between_time(off, on, *args):
            return (
                fill_dict(d_, V, ["off", datetime.combine(date(2023, 10, i), off).isoformat()]),
                fill_dict(d_, V, ["on", datetime.combine(date(2023, 10, i), on).isoformat()]),
            )


def between_time(off, on, *args):
    assert not len(args) % 2
    for a, b in batched(args, 2):
        if not (off < a.time() and on > b.time()):
            return False
    return True


def seconds():
    return math.floor(60 * random.random())


def minutes():
    return math.floor(60 * random.random())


def hours():
    return math.floor(24 * random.random())


reset_seeds()


def get_kuchnia():
    k_dict = {"entity_id": "kuchnia"}
    ret = []
    for i in range(10, 30):
        ret.append(fill_dict(k_dict, V, ["on", (j := datetime(2023, 10, i, 5, 30, seconds())).isoformat()]))
        ret.append(fill_dict(k_dict, V, ["off", (k := datetime(2023, 10, i, 7, 35, seconds())).isoformat()]))
        ret.append(fill_dict(k_dict, V, ["on", (L := datetime(2023, 10, i, 16, 20, seconds())).isoformat()]))
        ret.append(fill_dict(k_dict, V, ["off", (m := datetime(2023, 10, i, 16, 37, seconds())).isoformat()]))
        ret.append(fill_dict(k_dict, V, ["on", (n := datetime(2023, 10, i, 21, 35, seconds())).isoformat()]))
        ret.append(fill_dict(k_dict, V, ["off", (o := datetime(2023, 10, i, 22, 15, seconds())).isoformat()]))

        x, y = generate_random(k_dict, i, j, k, L, m, n, o)
        if GENERATE_NOISE:
            ret.append(x)
            ret.append(y)

    return ret


def get_ekspres():
    e_dict = {"entity_id": "ekspres"}
    ret = []
    for i in range(10, 30):
        ret.append(fill_dict(e_dict, V, ["on", (j := datetime(2023, 10, i, 5, 30, seconds())).isoformat()]))
        ret.append(fill_dict(e_dict, V, ["off", (k := datetime(2023, 10, i, 7, 32, seconds())).isoformat()]))
        ret.append(fill_dict(e_dict, V, ["on", (L := datetime(2023, 10, i, 16, 30, seconds())).isoformat()]))
        ret.append(fill_dict(e_dict, V, ["off", (m := datetime(2023, 10, i, 16, 37, seconds())).isoformat()]))

        x, y = generate_random(e_dict, i, j, k, L, m)
        if GENERATE_NOISE:
            ret.append(x)
            ret.append(y)
    return ret


def get_swiatla_salon():
    s_dict = {"entity_id": "swiatla_salon"}
    ret = []
    for i in range(10, 30):
        ret.append(fill_dict(s_dict, V, ["on", (j := datetime(2023, 10, i, 16, 38, seconds())).isoformat()]))
        ret.append(fill_dict(s_dict, V, ["off", (k := datetime(2023, 10, i, 21, 35, seconds())).isoformat()]))

        x, y = generate_random(s_dict, i, j, k)
        if GENERATE_NOISE:
            ret.append(x)
            ret.append(y)
    return ret


def get_telewizor():
    t_dict = {"entity_id": "telewizor"}
    ret = []
    for i in range(10, 30):
        ret.append(fill_dict(t_dict, V, ["on", (j := datetime(2023, 10, i, 16, 38, seconds())).isoformat()]))
        ret.append(fill_dict(t_dict, V, ["off", (k := datetime(2023, 10, i, 21, 35, seconds())).isoformat()]))
        ret.append(fill_dict(t_dict, V, ["on", (L := datetime(2023, 10, i, 6, 38, seconds())).isoformat()]))
        ret.append(fill_dict(t_dict, V, ["off", (m := datetime(2023, 10, i, 7, 33, seconds())).isoformat()]))

        x, y = generate_random(t_dict, i, j, k, L, m)
        if GENERATE_NOISE:
            ret.append(x)
            ret.append(y)
    return ret


def get_swiatla_balkon():
    b_dict = {"entity_id": "swiatla_balkon"}
    ret = []
    for i in range(10, 30):
        ret.append(fill_dict(b_dict, V, ["off", datetime(2023, 10, i, 5, 31, seconds()).isoformat()]))
        ret.append(fill_dict(b_dict, V, ["on", datetime(2023, 10, i, 22, 40, seconds()).isoformat()]))
    return ret


def get_lampka_sypialnia():
    s_dict = {"entity_id": "lampka_sypialnia"}
    ret = []
    for i in range(10, 30):
        ret.append(fill_dict(s_dict, V, ["on", (j := datetime(2023, 10, i, 22, 15, seconds())).isoformat()]))
        ret.append(fill_dict(s_dict, V, ["off", (k := datetime(2023, 10, i, 22, 40, seconds())).isoformat()]))

        x, y = generate_random(s_dict, i, j, k)
        if GENERATE_NOISE:
            ret.append(x)
            ret.append(y)
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

orig_X, orig_Y = [], []
for x, y in a.generate_state_change_chain():
    orig_X.append(x)
    orig_Y.append(y)

GENERATE_NOISE = True
reset_seeds()

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

ret = defaultdict(partial(defaultdict, partial(defaultdict, dict)))

try:
    for LEARN_RATE in [0.005, 0.001]:
        for clip in [(0.50, 0.95), (0.75, 0.90)]:
            for time_converter_type in [BinaryTimeConverter, CompoundTimeConverter, TimeCosConvertable]:
                automation.models.dnn.LEARNING_RATE = LEARN_RATE

                reset_seeds()
                agent = ModelManager.from_raw(
                    {"time": time_converter_type(), **{k: AnyConvertable() for k in a.devices.keys()}},
                    [k for k in a.devices.keys()],
                )
                gen_X, gen_Y = agent.generate_dummy_values(X[:-1], Y[:-1], amount=10, clip=clip)
                agent.fit(gen_X + X[:-1], gen_Y + Y[:-1], 16, 32)
                ev = agent.evaluate(orig_X[:-1], orig_Y[:-1])

                ret[time_converter_type.TYPE][LEARN_RATE][clip[0]] = ev
except KeyError:
    pass
finally:
    with open("dump.json", "w") as file:
        json.dump(ret, file)
