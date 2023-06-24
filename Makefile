define check_torchservices
	@echo "Waiting for torchservices to start"
	@while [ "$$(curl -s http://localhost:8080/ping | jq '.status' | tr -d '"')" != "Healthy" ] ; do \
		printf "." ; \
		sleep 1 ; \
	done
	@echo "Saiga is ready"
endef

start: build_cpu
	@docker-compose up -d
	$(check_torchservices)

stop:
	@docker-compose down
