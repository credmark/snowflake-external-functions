LOCAL_PORT  := 9000
SERVICE_URL := "http://localhost:${LOCAL_PORT}/2015-03-31/functions/function/invocations"

local-to-signature:
	@echo "testing to_signature_handler..."
	@echo "=================================================================="
	@echo "service will be made available at ${SERVICE_URL}"
	@echo "=================================================================="
	@docker-compose run -p ${LOCAL_PORT}:8080 to_signature

local-to-signature-hash:
	@echo "testing to_signature_hash_handler..."
	@echo "=================================================================="
	@echo "service will be made available at ${SERVICE_URL}"
	@echo "=================================================================="
	@docker-compose run -p ${LOCAL_PORT}:8080 to_signature_hash