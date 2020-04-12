.PHONY: deploy
deploy:
	gcloud functions deploy exam-server --runtime python37 --trigger-http --entry-point index
