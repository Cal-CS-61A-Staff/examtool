import csv
from json import loads

import click
from cryptography.fernet import Fernet
from google.cloud import firestore
from google.cloud.exceptions import NotFound

from cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option(
    "--json",
    prompt=True,
    default="data/exams/sample_exam.json",
    type=click.File("r"),
    help="The json JSON you wish to deploy.",
)
@click.option(
    "--roster",
    prompt=True,
    default="data/rosters/sample_roster.csv",
    type=click.File("r"),
    help="The json roster you wish to deploy.",
)
@click.option(
    "--default-deadline",
    prompt=True,
    default=0,
    type=int,
    help="Specify if you want unregistered students to be able to take the json, with this as the default deadline.",
)
def deploy(exam, json, roster, default_deadline):
    """
    Deploy an json to the website. You must specify a JSON and associated roster CSV.
    You can deploy the json multiple times and the password will remain unchanged.
    """
    json = json.read()
    roster = csv.reader(roster, delimiter=",")

    db = firestore.Client()
    ref = db.collection("exams").document(exam)
    json = loads(json)

    json["default_deadline"] = default_deadline
    json["secret"] = Fernet.generate_key()

    try:
        json["secret"] = ref.get().to_dict()["secret"]
    except (NotFound, TypeError):
        pass

    ref.set(json)

    ref = db.collection("roster").document(exam).collection("deadline")

    print("Deleting previously uploaded roster...")
    batch = db.batch()
    cnt = 0
    for document in ref.stream():
        batch.delete(document.reference)
        cnt += 1
        if cnt > 400:
            batch.commit()
            batch = db.batch()
            cnt = 0
            print("Batch of 400 deletes complete")
    batch.commit()
    print("Old roster deleted!")

    next(roster)  # ditch headers

    print("Uploading new roster...")
    batch = db.batch()
    cnt = 0
    for email, deadline in roster:
        doc_ref = ref.document(email)
        batch.set(doc_ref, {"deadline": int(deadline)})
        cnt += 1
        if cnt > 400:
            batch.commit()
            batch = db.batch()
            cnt = 0
            print("Batch of 400 writes complete")
    batch.commit()
    print("New roster uploaded!")

    ref = db.collection("exams").document("all")
    data = ref.get().to_dict()
    if exam not in data["exam-list"]:
        data["exam-list"].append(exam)
    ref.set(data)

    print("Exam uploaded with password:", json["secret"][:-1].decode("utf-8"))


if __name__ == "__main__":
    deploy()
