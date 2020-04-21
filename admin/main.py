from os import getenv

from flask import jsonify
from google.auth.transport import requests
from google.cloud import firestore
from google.oauth2 import id_token

# this can be public
CLIENT_ID = "713452892775-59gliacuhbfho8qvn4ctngtp3858fgf9.apps.googleusercontent.com"

DEV_EMAIL = getenv("DEV_EMAIL", "exam-test@berkeley.edu")


def update_cache():
    global main_html, main_js
    with open("static/index.html") as f:
        main_html = f.read()

    with open("static/main.js") as f:
        main_js = f.read()


update_cache()


def get_email(request):
    if getenv("ENV") == "dev":
        return DEV_EMAIL

    token = request.json["token"]

    # validate token
    id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

    if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
        raise ValueError("Wrong issuer.")

    return id_info["email"]


def index(request):
    try:
        if getenv("ENV") == "dev":
            update_cache()

        db = firestore.Client()

        if request.path.endswith("main.js"):
            return main_js

        if request.path == "/":
            return main_html

    except:
        return jsonify({"success": False})

    return request.path
