import csv
import json
import os
import pathlib

import click
from fpdf import FPDF

from examtool.api.database import get_exam, get_submissions
from examtool.api.extract_questions import extract_questions
from examtool.api.grade import grade
from examtool.api.scramble import scramble
from examtool.cli.utils import exam_name_option, hidden_output_folder_option


def write_exam(response, exam, template_questions, student_questions, name_question, sid_question, compact):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Courier", size=16)
    pdf.multi_cell(200, 20, txt=exam, align="L")
    pdf.multi_cell(200, 20, txt=response.get(name_question, "NO NAME"), align="L")
    pdf.multi_cell(200, 20, txt=response.get(sid_question, "NO SID"), align="L")

    pdf.set_font("Courier", size=9)

    def out(text):
        pdf.multi_cell(200, 5, txt=text, align="L")

    line_count = 0
    force_new = True

    student_question_lookup = {q["id"]: q for q in student_questions}

    for question in template_questions:
        if line_count > 30 or force_new or not compact:
            pdf.add_page()
            line_count = 0
            force_new = False

        out("\nQUESTION")
        for line in question["text"].split("\n"):
            out(line)
            line_count += 1

        out("\nANSWER")

        if question.get("type") not in ["multiple_choice", "select_all"]:
            force_new = True

        if question.get("type") in ["multiple_choice", "select_all"]:
            selected_options = response.get(question["id"], [])
            if question.get("type") == "multiple_choice" and not isinstance(selected_options, list):
                selected_options = [selected_options]
            available_options = sorted([option["text"] for option in question["options"]])
            if question["id"] not in student_question_lookup:
                out("STUDENT DID NOT RECEIVE QUESTION")
                line_count += 1
            else:
                student_options = sorted([option["text"] for option in student_question_lookup[question["id"]]["options"]])
                for template, option in zip(available_options, student_options):
                    if option in selected_options:
                        out("[X] " + template)
                    else:
                        out("[ ] " + template)
                line_count += 1
        else:
            for line in response.get(question["id"], "").encode('latin-1', 'replace').decode('latin-1').split("\n"):
                out(line)
                line_count += 1

        out("\nAUTOGRADER")
        if question["id"] in student_question_lookup and question["id"] in response:
            out(grade(student_question_lookup[question["id"]], response))

    return pdf


@click.command()
@exam_name_option
@click.option("--name-question", default=None, help="The ID of the question for the student's name.")
@click.option("--sid-question", default=None, help="The ID of the question for the student's SID.")
@click.option("--compact/--expanded", default=False, help="Combine questions on the same page to save space.")
@hidden_output_folder_option
def download(exam, out, name_question, sid_question, compact):
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

    template_questions = list(extract_questions(json.loads(exam_json)))

    pdf = write_exam({}, exam, template_questions, template_questions, name_question, sid_question, compact)
    pdf.output(os.path.join(out, "OUTLINE.pdf"))

    total = [["Email"] + [question["text"] for question in extract_questions(json.loads(exam_json))]]

    for email, response in get_submissions(exam=exam):
        if 1 < len(response) < 10:
            print(email, response)

        total.append([email])
        for question in template_questions:
            total[-1].append(response.get(question["id"], ""))

        student_questions = list(extract_questions(scramble(email, json.loads(exam_json), keep_data=True)))

        pdf = write_exam(response, exam, template_questions, student_questions, name_question, sid_question, compact)
        pdf.output(os.path.join(out, "{}.pdf".format(email)))

    with open(os.path.join(out, "summary.csv"), "w") as f:
        writer = csv.writer(f)
        for row in total:
            writer.writerow(row)


if __name__ == "__main__":
    download()
