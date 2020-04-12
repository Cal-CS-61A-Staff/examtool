To develop, run
```
yarn && pip install -r requirements.txt
```
to install dependencies, then
```
yarn run webpack
```
to start the JS compiler, then
```
python3 run_local.py
```
to start the Flask server.

To deploy, run
```
make deploy
```
after setting up the relevant `gCloud` credentials.

To do local development using the GCP database backend, add a `creds.json` file linked to a service account in the root directory and activate it.
