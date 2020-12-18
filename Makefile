SHELL:=/bin/bash

.PHONY: help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

config: ## Setting deploy configuration
	@TMP_PROJECT=$(shell gcloud config list --format 'value(core.project)'); \
	read -e -p "Enter Your Project Name: " -i $${TMP_PROJECT} PROJECT_ID; \
	gcloud config set project $${PROJECT_ID}; \
	read -e -p "Enter Desired Cloud Run Region: " -i 'europe-west1' CLOUD_RUN_REGION; \
	gcloud config set run/region $${CLOUD_RUN_REGION}; \
	read -e -p "Enter Desired Cloud Run Platform: " -i 'managed' CLOUD_RUN_PLATFORM; \
	gcloud config set run/platform $${CLOUD_RUN_PLATFORM};

init: init-users ## Activation of API, creation of service account with roles

build: build-pusher ## Build all Cloud Run Image

deploy: deploy-pusher ## Deploy Cloud Run Image by using the last built image

init-users: ## Create Cloud Run needed users
	@TMP_PROJECT=$(shell gcloud config list --format 'value(core.project)'); \
	read -e -p "Enter Your Project Name: " -i $${TMP_PROJECT} PROJECT_ID; \
	gcloud config set project $${PROJECT_ID}; \
	PROJECT_NUMBER=$(shell gcloud projects list --filter=$(shell gcloud config list --format 'value(core.project)') --format="value(PROJECT_NUMBER)"); \
	gcloud iam service-accounts create cloud-run-pubsub-invoker \
 		--display-name "Cloud Run Pub/Sub Invoker"; \
	gcloud iam service-accounts create cloud-run-agent-pusher \
		--display-name "Cloud Run Insight Receiver"; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:cloud-run-agent-pusher@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/bigquery.admin; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:cloud-run-agent-pusher@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/datastore.user; \

build-pusher: ## Build receiver and upload Cloud Run Image
	@PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	cd pusher; \
	gcloud builds submit --tag gcr.io/$${PROJECT_ID}/agent-pusher;

deploy-pusher: ## Deploy a pusher from last built image
	@PUSHER_ID="000"; \
	PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	CLOUD_RUN_REGION=$(shell gcloud config list --format 'value(run.region)'); \
	CLOUD_RUN_PLATFORM=$(shell gcloud config list --format 'value(run.platform)'); \
	gcloud run deploy agent-pusher-$${PUSHER_ID} \
		--image gcr.io/$${PROJECT_ID}/agent-pusher \
    	--service-account cloud-run-agent-pusher@$${PROJECT_ID}.iam.gserviceaccount.com \
		--region $${CLOUD_RUN_REGION} \
		--platform $${CLOUD_RUN_PLATFORM} \
		--no-allow-unauthenticated; \
	gcloud run services add-iam-policy-binding agent-pusher-$${PUSHER_ID} \
		--member=serviceAccount:cloud-run-pubsub-invoker@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/run.invoker \
		--region $${CLOUD_RUN_REGION} \
		--platform $${CLOUD_RUN_PLATFORM};


