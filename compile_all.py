import csv
import json
import os
from datetime import datetime
from io import BytesIO

import PyPDF2 as PyPDF2
import click
import pytz

from exam.scramble import scramble
from write.gen_latex import render_latex


@click.command()
@click.option("--exam", prompt=True, default="sample_exam.json", type=click.File("r"))
@click.option(
    "--roster", prompt=True, default="sample_roster.csv", type=click.File("r")
)
@click.option("--out", prompt=True, default="out", type=click.Path())
@click.option("--password", prompt=True, type=click.Path())
def compile_all(exam, roster, out, password):
    exam_str = exam.read()
    roster = csv.reader(roster, delimiter=",")

    if not os.path.exists(out):
        os.mkdir(out)

    next(roster)  # ditch headers
    for email, deadline in roster:
        if not deadline:
            continue
        exam = json.loads(exam_str)
        scramble(email, exam)
        deadline_utc = datetime.utcfromtimestamp(int(deadline))
        deadline_pst = pytz.utc.localize(deadline_utc).astimezone(
            pytz.timezone("America/Los_Angeles")
        )
        deadline_string = deadline_pst.strftime("%I:%M%p")
        with render_latex(
            exam, {"emailaddress": email.replace("_", r"\_"), "deadline": deadline_string}
        ) as pdf:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

            pdf = PyPDF2.PdfFileReader(BytesIO(pdf))
            out_pdf = PyPDF2.PdfFileWriter()
            out_pdf.appendPagesFromReader(pdf)
            out_pdf.encrypt(password)

            with open(
                os.path.join(
                    out, "exam_" + email.replace("@", "_").replace(".", "_") + ".pdf"
                ),
                "wb",
            ) as f:
                out_pdf.write(f)


if __name__ == "__main__":
    compile_all()
