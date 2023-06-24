.PHONY: start stop

define check_torchservices
	@echo "Waiting for torchservices to start"
	@while [ "$$(curl -s http://localhost:8080/ping | jq '.status' | tr -d '"')" != "Healthy" ] ; do \
		printf "." ; \
		sleep 1 ; \
	done
	@echo "Saiga is ready"
endef

start:
	cd backend/saiga; python -m poetry shell;
	torchserve --torch-model-archiver --model-name saiga --version 1.0 --export-path model_store --extra-files conversation.py --handler handler.py -f
	cd backend/saiga; torchserve --start --ncs --ts-config config.properties;
	cd frontend; bash run.sh
	$(check_torchservices)

stop:
	cd backend; python -m poetry shell;
	torchserve --stop
