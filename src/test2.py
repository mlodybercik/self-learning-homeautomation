from automation.models.serializer import ModelSerializer


with ModelSerializer("/tmp/model.ha", "r") as ha:
    model = ha.load_manager_from_archive()

print(model.agents)
print(model.converters)