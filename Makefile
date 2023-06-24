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
	cd backend/saiga; python -m poetry shell
	cd backend/saiga; torch-model-archiver --model-name saiga --version 1.0 --export-path model_store --extra-files conversation.py --handler handler.py -f && torchserve --start --ncs --ts-config config.properties
#        $(check_torchservices)
	cd frontend; bash run.sh

stop:
	cd backend/saiga; python -m poetry shell;
	torchserve --stop
