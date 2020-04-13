export PROJECT_ID=banded-syntax-252420

.PHONY: deploy-student
deploy-student:
	cd student && gcloud functions deploy exam-server --runtime python37 --trigger-http --entry-point index

.PHONY: dev-student
dev-student:
	export MODE=student; \
	export FLASK_APP=run_local; \
	export GOOGLE_APPLICATION_CREDENTIALS=$(shell pwd)/creds.json; \
	export ENV=dev; \
	yarn run concurrently webpack "flask run"

.PHONY: dev-staff
dev-staff:
	export MODE=staff; \
	export FLASK_APP=staff/app; \
	export GOOGLE_APPLICATION_CREDENTIALS=$(shell pwd)/creds.json; \
	export ENV=dev; \
	yarn run concurrently webpack "flask run"

.PHONY: deploy-staff
deploy-staff:
	cd staff && \
	gcloud builds submit --tag gcr.io/$(PROJECT_ID)/staff-exam-server && \
	gcloud run deploy --image gcr.io/$(PROJECT_ID)/staff-exam-server --platform managed
