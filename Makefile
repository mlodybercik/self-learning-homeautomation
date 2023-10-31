run: build_deamon
	-docker run -d \
	--name homeassistant \
 	-e TZ=Europe/Warsaw \
	-v ${PWD}/config:/config \
	--network=host \
	ghcr.io/home-assistant/home-assistant:stable

	-docker run -d \
	--name appdeamon \
	--network=host \
	-p 5050:5050 \
	-v ${PWD}/appdeamon_config:/conf \
	-v ${PWD}/models:/models \
	-e TOKEN -e HA_URL='http://localhost:8123' \
	automation:0.1.0

build_deamon:
	if ! ls dist/*.whl 1> /dev/null 2>&1 ; then \
		python -m build --wheel; \
		docker build -t automation:0.1.0 . ;\
	fi; 
	

start:
	-docker start homeassistant
	-docker start appdeamon

stop:
	docker stop homeassistant

clean:
	rm -v dist/*
	docker rm appdeamon --force

restart:
	@$(MAKE) stop
	@$(MAKE) start
