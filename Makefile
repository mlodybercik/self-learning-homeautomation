run:
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
	-e TOKEN -e HA_URL='http://localhost:8123' \
	acockburn/appdaemon:latest

start:
	-docker start homeassistant
	-docker start appdeamon

stop:
	docker stop homeassistant

restart:
	@$(MAKE) stop
	@$(MAKE) start
