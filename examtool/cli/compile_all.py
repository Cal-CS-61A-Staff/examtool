import json
import os
import pathlib
from datetime import datetime
from io import BytesIO

from pikepdf import Pdf, Encryption
import click
import pytz

from examtool.api.database import get_exam, get_roster
from examtool.api.scramble import scramble
from examtool.api.gen_latex import render_latex
from examtool.cli.utils import exam_name_option, hidden_output_folder_option, prettify


@click.command()
@exam_name_option
@click.option("--subtitle", prompt=True, default="Structure and Interpretation of Computer Programs")
@hidden_output_folder_option
@click.option("--do-twice", is_flag=True, help="Run the compile twice for each student to fix weird rendering bugs.")
def compile_all(exam, subtitle, out, do_twice):
    """
    Compile individualized PDFs for the specified exam.
    Exam must have been deployed first.
    """
    if not out:
        out = "out/latex/" + exam

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    exam_data = get_exam(exam=exam)
    password = exam_data.pop("secret")[:-1]
    print(password)
    exam_str = json.dumps(exam_data)

    for email, deadline in get_roster(exam=exam):
        if not deadline:
            continue
        exam_data = json.loads(exam_str)
        scramble(email, exam_data)
        deadline_utc = datetime.utcfromtimestamp(int(deadline))
        deadline_pst = pytz.utc.localize(deadline_utc).astimezone(
            pytz.timezone("America/Los_Angeles")
        )
        deadline_string = deadline_pst.strftime("%I:%M%p")

        with render_latex(
            exam_data,
            {
                "emailaddress": email.replace("_", r"\_"),
                "deadline": deadline_string,
                "coursecode": prettify(exam.split("-")[0]),
                "description": subtitle,
            },
            do_twice=do_twice,
        ) as pdf:
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
