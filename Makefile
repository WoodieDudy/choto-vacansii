.PHONY: frontend start

define check_torchservices
	@echo "Waiting for torchservices to start"
	@while [ "$$(curl -s http://localhost:8080/ping | jq '.status' | tr -d '"')" != "Healthy" ] ; do \
		printf "." ; \
		sleep 1 ; \
	done
	@echo "Saiga is ready"
endef

start:
	cd backend; python -m poetry shell; torchserve --start --ncs --ts-config config.properties
	cd frontend; bash run.sh
	$(check_torchservices)


stop:
	cd backend; python -m poetry shell;
	torchserve --stop