import csv
import json
import os

import click
from google.cloud import firestore
from fpdf import FPDF

from apps.exam import scramble


@click.command()
@click.option("--name", prompt=True, default="cs61a-test-final")
@click.option("--exam", prompt=True, default="sample_exam.json", type=click.File('r'))
@click.option("--name-question", prompt=True)
@click.option("--sid-question", prompt=True)
@click.option("--out", default=None, type=click.Path())
def download_all(name, exam, out, name_question, sid_question):
    exam = exam.read()

    out = out or "export/" + name

    if not os.path.exists(out):
        os.mkdir(out)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=16)
    pdf.multi_cell(200, 20, txt=name, align="L")

    pdf.set_font("Courier", size=9)
    for question in extract_questions(json.loads(exam)):
        pdf.add_page()
        pdf.multi_cell(200, 5, txt="\nQUESTION", align="L")
        for line in question["text"].split("\n"):
            pdf.multi_cell(200, 5, txt=line, align="L")
        pdf.multi_cell(200, 5, txt="\nANSWER", align="L")
    pdf.output(os.path.join(out, "OUTLINE.pdf"))

    q_order = [question["id"] for question in extract_questions(json.loads(exam))]

    total = [["Email"] + [question["text"] for question in extract_questions(json.loads(exam))]]

    db = firestore.Client()
    for i, submission in enumerate(db.collection(name).stream()):
        email = submission.id
        response = submission.to_dict()

        if 1 < len(response) < 10:
            print(email, response)

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Courier", size=16)
        pdf.multi_cell(200, 20, txt=name, align="L")
        pdf.multi_cell(200, 20, txt=response.get(name_question, "NO NAME"), align="L")
        pdf.multi_cell(200, 20, txt=response.get(sid_question, "NO SID"), align="L")

        pdf.set_font("Courier", size=9)

        q_lookup = {question["id"]: question for question in extract_questions(scramble(email, json.loads(exam)))}

        total.append([email])

        for question_id in q_order:
            question = q_lookup[question_id]
            pdf.add_page()
            pdf.multi_cell(200, 5, txt="\nQUESTION", align="L")
            for line in question["text"].split("\n"):
                pdf.multi_cell(200, 5, txt=line, align="L")

            pdf.multi_cell(200, 5, txt="\nANSWER", align="L")
            for line in response.get(question_id, "").encode('latin-1', 'replace').decode('latin-1').split("\n"):
                pdf.multi_cell(200, 5, txt=line, align="L")

            total[-1].append(response.get(question_id, ""))

        pdf.output(os.path.join(out, "{}.pdf".format(email)))

    with open(os.path.join(out, "summary.csv"), "w") as f:
        writer = csv.writer(f)
        for row in total:
            writer.writerow(row)


def extract_questions(exam):
    if "public" in exam:
        yield from group_questions(exam["public"])
    for group in exam["groups"]:
        yield from group_questions(group)


def group_questions(group):
    out = _group_questions(group)
    first = next(out)
    first["text"] = group["name"] + "\n\n" + group["text"] + "\n\n" + first["text"]
    yield first
    yield from out


def _group_questions(group):
    for element in group.get("elements", []) + group.get("questions", []):
        if element.get("type") == "group":
            out = group_questions(element)
            yield from out
        else:
            yield element


if __name__ == "__main__":
    download_all()
