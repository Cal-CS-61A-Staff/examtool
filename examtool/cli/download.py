import csv
import json
import os
import pathlib

import click
from fpdf import FPDF

from examtool.api.database import get_exam, get_submissions
from examtool.api.scramble import scramble
from examtool.cli.utils import exam_name_option, hidden_output_folder_option


@click.command()
@exam_name_option
@click.option("--name-question", default=None, help="The ID of the question for the student's name.")
@click.option("--sid-question", default=None, help="The ID of the question for the student's SID.")
@hidden_output_folder_option
def download(exam, out, name_question, sid_question):
    """
    Download student submissions for an exam.
    Exams are downloaded as PDFs into a target folder - specify `out` to redirect the folder.
    An `OUTLINE.pdf` is also generated for Gradescope, as is a `summary.csv` for analytics or autograding.
    """
    exam_json = get_exam(exam=exam)
    exam_json.pop("secret")
    exam_json = json.dumps(exam_json)

    out = out or "out/export/" + exam

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=16)
    pdf.multi_cell(200, 20, txt=exam, align="L")

    pdf.set_font("Courier", size=9)
    for question in extract_questions(json.loads(exam_json)):
        pdf.add_page()
        pdf.multi_cell(200, 5, txt="\nQUESTION", align="L")
        for line in question["text"].split("\n"):
            pdf.multi_cell(200, 5, txt=line, align="L")
        pdf.multi_cell(200, 5, txt="\nANSWER", align="L")
    pdf.output(os.path.join(out, "OUTLINE.pdf"))

    q_order = [question["id"] for question in extract_questions(json.loads(exam_json))]

    total = [["Email"] + [question["text"] for question in extract_questions(json.loads(exam_json))]]

    for email, response in get_submissions(exam=exam):
        if 1 < len(response) < 10:
            print(email, response)

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Courier", size=16)
        pdf.multi_cell(200, 20, txt=exam, align="L")
        pdf.multi_cell(200, 20, txt=response.get(name_question, "NO NAME"), align="L")
        pdf.multi_cell(200, 20, txt=response.get(sid_question, "NO SID"), align="L")

        pdf.set_font("Courier", size=9)

        q_lookup = {question["id"]: question for question in extract_questions(scramble(email, json.loads(exam_json)))}

        total.append([email])

        for question_id in q_order:
            question = q_lookup.get(question_id, {"text": "QUESTION WAS NOT DISPLAYED"})
            pdf.add_page()
            pdf.multi_cell(200, 5, txt="\nQUESTION", align="L")
            for line in question["text"].split("\n"):
                pdf.multi_cell(200, 5, txt=line, align="L")

            pdf.multi_cell(200, 5, txt="\nANSWER", align="L")
            if question.get("type") == "select_all":
                selected_options = response.get(question_id, [])
                available_options = [option["text"] for option in question["options"]]
                for option in sorted(available_options):
                    if option in selected_options:
                        pdf.multi_cell(200, 5, txt="X " + option, align="L")
                    else:
                        pdf.multi_cell(200, 5, txt="  " + option, align="L")
            else:
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
    download()
