import os
import pathlib
from io import BytesIO
from json import load

import click
from pikepdf import Pdf

from examtool.api.database import get_exam
from examtool.api.gen_latex import render_latex
from examtool.cli.utils import exam_name_option, hidden_output_folder_option, prettify


@click.command()
@exam_name_option
@click.option(
    "--json",
    default=None,
    type=click.File("r"),
    help="The exam JSON you wish to compile. Leave blank to compile the deployed exam.",
)
@hidden_output_folder_option
def compile(exam, json, out):
    """
    Compile one PDF, unencrypted.
    Exam must have been deployed first.
    """
    if not out:
        out = ""

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    if not json:
        exam_data = get_exam(exam=exam)
    else:
        exam_data = load(json)

    with render_latex(
        exam_data, {"coursecode": prettify(exam.split("-")[0]), "description": "Sample Exam."}
    ) as pdf:
        pdf = Pdf.open(BytesIO(pdf))
        pdf.save(os.path.join(out, exam + ".pdf"))
        pdf.close()


if __name__ == "__main__":
    compile()
