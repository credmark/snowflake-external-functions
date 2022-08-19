LOCAL_PORT  := 9000
SERVICE_URL := "http://localhost:${LOCAL_PORT}/2015-03-31/functions/function/invocations"
AWS_REGION  := us-west-2

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

local-decode-contract-event:
	@echo "testing to_signature_hash_handler..."
	@echo "=================================================================="
	@echo "service will be made available at ${SERVICE_URL}"
	@echo "=================================================================="
	@docker-compose run -p ${LOCAL_PORT}:8080 decode_contract_event


local-decode_contract_function:
	@echo "testing to_signature_hash_handler..."
	@echo "=================================================================="
	@echo "service will be made available at ${SERVICE_URL}"
	@echo "=================================================================="
	@docker-compose run -p ${LOCAL_PORT}:8080 decode_contract_function

deploy-dev:
	@echo deploying serverless service to dev account
	@serverless deploy --stage dev --region ${AWS_REGION} --verbose --aws-profile ${AWS_DEV_PROFILE}

remove-dev:
	@echo removing the service
	@serverless remove --stage dev --region ${AWS_REGION} --verbose --aws-profile ${AWS_DEV_PROFILE}

deploy-prod:
	@echo deploying serverless service to dev account
	@serverless deploy --stage prod --region ${AWS_REGION} --verbose --aws-profile ${AWS_PROFILE}