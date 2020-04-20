import json
import sys
from os import getenv

from cryptography.fernet import Fernet
from flask import jsonify, abort
from google.cloud import firestore
from google.oauth2 import id_token
from google.auth.transport import requests
from google.cloud.exceptions import NotFound

from scramble import scramble

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

        if request.path.endswith("list_exams"):
            return jsonify(
                db.collection("exams").document("all").get().to_dict()["exam-list"]
            )

        if request.path.endswith("get_exam"):
            exam = request.json["exam"]
            email = get_email(request)
            ref = db.collection(exam).document(email)
            try:
                answers = ref.get().to_dict() or {}
            except NotFound:
                answers = {}

            ref = db.collection("roster").document(exam).collection("deadline").document(email)
            try:
                deadline = ref.get().to_dict()["deadline"]
            except NotFound:
                abort(401)
                return

            exam_data = db.collection("exams").document(exam).get().to_dict()
            config = exam_data["config"]
            exam_data = scramble(
                email,
                exam_data,
                groups="scramble_groups" in config,
                questions="scramble_questions" in config,
                options="scramble_options" in config,
            )

            return jsonify(
                {
                    "success": True,
                    "exam": exam,
                    "publicGroup": exam_data["public"],
                    "privateGroups": Fernet(exam_data["secret"])
                    .encrypt(json.dumps(exam_data["groups"]).encode("ascii"))
                    .decode("ascii"),
                    "answers": answers,
                    "deadline": deadline,
                }
            )

        if request.path.endswith("submit_question"):
            exam = request.json["exam"]
            question_id = request.json["id"]
            value = request.json["value"]
            email = get_email(request)

            db.collection(exam).document(email).set({question_id: value}, merge=True)

            return jsonify({"success": True})
    except:
        return jsonify({"success": False})

    return request.path
