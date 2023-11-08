from automation.models.serializer import ModelSerializer
from datetime import time


with ModelSerializer("/tmp/model.ha", "r") as ha:
    model = ha.load_manager_from_archive()

_state = {
    "kuchnia": 0.0,
    "ekspres": 0.0,
    "swiatla_salon": 0.0,
    "telewizor": 0.0,
    "swiatla_balkon": 1.0,
    "lampka_sypialnia": 0.0,
}

_to_be_tested = []
for hour in range(24):
    state = _state.copy()
    state["time"] = time(hour=hour)
    _to_be_tested.append(state)

tested = model.predict(_to_be_tested)

print("\t" + "\t".join([i[:5] for i in _state.keys()]))
for hour in range(24):
    prepd = "\t".join([f"{tested[device][hour][0]:+0.2f}" for device in _state.keys()])
    print(f"Hour {hour:2d}: {prepd}")