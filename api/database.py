from google.cloud import firestore

from api.utils import as_list


def get_exam(exam):
    db = firestore.Client()
    return db.collection("exams").document(exam).get().to_dict()


def set_exam(exam, json):
    db = firestore.Client()
    db.collection("exams").document(exam).set(json)

    ref = db.collection("exams").document("all")
    data = ref.get().to_dict()
    if exam not in data["exam-list"]:
        data["exam-list"].append(exam)
    ref.set(data)


@as_list
def get_roster(exam):
    db = firestore.Client()
    for student in db.collection("roster").document(exam).collection("deadline").stream():
        yield student.id, student.to_dict()["deadline"]


def set_roster(exam, roster):
    db = firestore.Client()

    ref = db.collection("roster").document(exam).collection("deadline")

    batch = db.batch()
    cnt = 0
    for document in ref.stream():
        batch.delete(document.reference)
        cnt += 1
        if cnt > 400:
            batch.commit()
            batch = db.batch()
            cnt = 0
    batch.commit()

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
    batch.commit()


# def get_submissions(exam):
