import os
import pathlib
from io import BytesIO
from json import load, dump

import click
from pikepdf import Pdf

from examtool.api.convert import convert
from examtool.api.database import get_exam
from examtool.api.gen_latex import render_latex
from examtool.api.scramble import scramble
from examtool.cli.utils import exam_name_option, hidden_output_folder_option, prettify


@click.command()
@exam_name_option
@click.option(
    "--json",
    default=None,
    type=click.File("r"),
    help="The exam JSON you wish to compile. Leave blank to compile the deployed exam.",
)
@click.option(
    "--md",
    default=None,
    type=click.File("r"),
    help="The exam Markdown you wish to compile. Leave blank to compile the deployed exam.",
)
@click.option(
    "--seed",
    default=None,
    help="Scrambles the exam based off of the seed (E.g. a student's email)."
)
@click.option(
    "--json-out",
    default=None,
    type=click.File("w"),
    help="Exports the JSON to the file specified."
)
@hidden_output_folder_option
def compile(exam, json, md, seed, json_out, out):
    """
    Compile one PDF or JSON (from Markdown), unencrypted.
    The exam may be deployed or local (in Markdown or JSON).
    If a seed is specified, it will scramble the exam.
    """
    if not out:
        out = ""

    pathlib.Path(out).mkdir(parents=True, exist_ok=True)

    if json:
        print("Loading exam...")
        exam_data = load(json)
    elif md:
        print("Compiling exam...")
        exam_text_data = md.read()
        exam_data = convert(exam_text_data)
    else:
        print("Fetching exam...")
        exam_data = get_exam(exam=exam)

    if seed:
        print("Scrambling exam...")
        exam_data = scramble(seed, exam_data,)

    if json_out:
        print("Dumping json...")
        dump(exam_data, json_out)
        return

    print("Rendering exam...")
    with render_latex(
        exam_data, {"coursecode": prettify(exam.split("-")[0]), "description": "Sample Exam."}
    ) as pdf:
        pdf = Pdf.open(BytesIO(pdf))
        pdf.save(os.path.join(out, exam + ".pdf"))
        pdf.close()


if __name__ == "__main__":
    compile()
