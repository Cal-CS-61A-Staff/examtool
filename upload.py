import csv
import json

from cryptography.fernet import Fernet
from google.cloud import firestore


def upload_exam(exam_name, exam, roster):
    db = firestore.Client()
    ref = db.collection("exams").document(exam_name)
    exam = json.loads(exam)
    exam["secret"] = Fernet.generate_key()
    ref.set(exam)

    ref = db.collection("roster").document(exam_name).collection("deadline")
    next(roster)  # ditch headers
    for email, deadline in roster:
        ref.document(email).set({"deadline": int(deadline)})

    ref = db.collection("exams").document("all")
    data = ref.get().to_dict()
    if exam_name not in data["exam-list"]:
        data["exam-list"].append(exam_name)
    ref.set(data)

    print("Exam uploaded with password:", exam["secret"][:-1].decode("utf-8"))


if __name__ == '__main__':
    exam_name = input("Exam Name: [cs61a-exam-test]? ") or "cs61a-exam-test"
    exam_json = input("Exam JSON: [sample_exam.json]? ") or "sample_exam.json"
    roster_csv = input("Roster CSV: [sample_roster.csv]? ") or "sample_roster.csv"
    with open(exam_json) as f, open(roster_csv) as g:
        upload_exam(exam_name, f.read(), csv.reader(g, delimiter=','))
