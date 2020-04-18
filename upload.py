import json

from google.cloud import firestore


def upload_exam(exam_name, exam):
    db = firestore.Client()
    ref = db.collection("exams").document(exam_name)
    if isinstance(exam, str):
        exam = json.loads(exam)
    ref.set(exam)
    ref = db.collection("exams").document("all")
    data = ref.get().to_dict()
    if exam_name not in data["exam-list"]:
        data["exam-list"].append(exam_name)
    ref.set(data)


if __name__ == '__main__':
    exam_name = input("Exam Name: [cs61a-exam-test]? ") or "cs61a-exam-test"
    exam_json = input("Exam JSON: [sample_exam.json]? ") or "sample_exam.json"
    with open(exam_json) as f:
        upload_exam(exam_name, f.read())
