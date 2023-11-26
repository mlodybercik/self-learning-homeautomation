from collections import defaultdict
from datetime import time
from json import dump

from automation.models.serializer import ModelSerializer

with ModelSerializer("/tmp/model.ha", "r") as ha:
    model = ha.load_manager_from_archive()

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
    for minute in range(0, 60, 10):
        state = _state.copy()
        state["time"] = time(hour=hour, minute=minute)
        _to_be_tested.append(state)

tested = model.predict(_to_be_tested)

print("\t" + "\t".join([i[:5] for i in _state.keys()]))
for hour in range(24):
    prepd = "\t".join([f"{tested[device][hour * 6][0]:+0.2f}" for device in _state.keys()])
    print(f"Hour {hour:2d}: {prepd}")

export = defaultdict(list)

for i, hour in enumerate(range(24)):
    for j, minute in enumerate(range(0, 60, 10)):
        for device in tested.keys():
            export[device].append(tested[device][(i * 6) + j].numpy().item())

with open("asd.json", "wt") as file:
    dump(dict(export), file)
