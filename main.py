from os import getenv

from cryptography.fernet import Fernet
from flask import jsonify
from google.cloud import firestore


KEY = b'U5VyveKIg1cyYzIBoQbkTKWrSsaC5NbnsSHvsw_2cPI='


def update_cache():
    global main_html, main_js
    with open("static/index.html") as f:
        main_html = f.read()

    with open("static/main.js") as f:
        main_js = f.read()


update_cache()


def index(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """

    if getenv("ENV") == "dev":
        update_cache()

    db = firestore.Client()

    if request.path.endswith("main.js"):
        return main_js

    if request.path == "/":
        return main_html

    if request.path.endswith("get_exam"):
        with open("sample_exam.json") as f:
            content = f.read().encode("ascii")
        return jsonify({
            "success": True,
            "exam": "cs61a-final-wednesday",
            "payload": Fernet(KEY).encrypt(content).decode("ascii")
        })

    count = 0
    if "count" in request.path:
        for doc in db.collection("users").stream():
            count += 1
        return str(count)

    doc = db.collection("users").add({
        "question_1": 1
    })

    return request.path
