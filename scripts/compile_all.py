import json
import os
from datetime import datetime
from io import BytesIO

from google.cloud import firestore
from pikepdf import Pdf, Encryption
import click
import pytz

from apps.exam.scramble import scramble
from apps.write.gen_latex import render_latex


@click.command()
@click.option("--name", prompt=True, default="cs61a-test-final")
@click.option("--out", default=None, type=click.Path())
def compile_all(name, out):
    db = firestore.Client()

    if not out:
        out = "out/latex/" + name

    if not os.path.exists(out):
        os.mkdir(out)

    exam = db.collection("exams").document(name).get().to_dict()
    password = exam.pop("secret")
    exam_str = json.dumps(exam)

    for student in db.collection("roster").document(name).collection("deadline").stream():
        email = student.id
        deadline = student.to_dict()["deadline"]
        if not int(deadline):
            continue
        exam = json.loads(exam_str)
        scramble(email, exam)
        deadline_utc = datetime.utcfromtimestamp(int(deadline))
        deadline_pst = pytz.utc.localize(deadline_utc).astimezone(
            pytz.timezone("America/Los_Angeles")
        )
        deadline_string = deadline_pst.strftime("%I:%M%p")

        with render_latex(
            exam,
            {"emailaddress": email.replace("_", r"\_"), "deadline": deadline_string},
        ) as pdf:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

            pdf = Pdf.open(BytesIO(pdf))
            pdf.save(
                os.path.join(
                    out, "exam_" + email.replace("@", "_").replace(".", "_") + ".pdf"
                ),
                encryption=Encryption(owner=password, user=password),
            )
            pdf.close()


if __name__ == "__main__":
    compile_all()
