export PROJECT_ID=banded-syntax-252420

.PHONY: exam-deploy
exam-deploy:
	cd exam && gcloud functions deploy exam-server --runtime python37 --trigger-http --entry-point index

.PHONY: exam-dev
exam-dev:
	export MODE=exam; \
	export FLASK_APP=run_local; \
	export GOOGLE_APPLICATION_CREDENTIALS=$(shell pwd)/creds.json; \
	export ENV=dev; \
	yarn run concurrently webpack "flask run"

.PHONY: admin-deploy
admin-deploy:
	cd admin && gcloud functions deploy exam-admin --runtime python37 --trigger-http --entry-point index

.PHONY: admin-dev
admin-dev:
	export MODE=admin; \
	export FLASK_APP=run_local; \
	export GOOGLE_APPLICATION_CREDENTIALS=$(shell pwd)/creds.json; \
	export ENV=dev; \
	yarn run concurrently webpack "flask run"

.PHONY: write-dev
write-dev:
	export MODE=write; \
	export FLASK_APP=staff/app; \
	export GOOGLE_APPLICATION_CREDENTIALS=$(shell pwd)/creds.json; \
	export ENV=dev; \
	yarn run concurrently webpack "flask run"

.PHONY: write-deploy
write-deploy:
	cd write && \
	gcloud builds submit --tag gcr.io/$(PROJECT_ID)/staff-exam-server && \
	gcloud run deploy --image gcr.io/$(PROJECT_ID)/staff-exam-server --platform managed
