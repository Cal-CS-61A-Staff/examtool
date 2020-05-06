import csv
from json import loads

import click
from cryptography.fernet import Fernet

from examtool.api.database import set_exam, get_exam, set_roster
from examtool.cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option(
    "--json",
    prompt=True,
    type=click.File("r"),
    help="The exam JSON you wish to deploy.",
)
@click.option(
    "--roster",
    prompt=True,
    type=click.File("r"),
    help="The roster CSV you wish to deploy.",
)
@click.option(
    "--default-deadline",
    prompt=True,
    default=0,
    type=int,
    help="Specify if you want unregistered students to be able to take the exam, with this as the default deadline.",
)
def deploy(exam, json, roster, default_deadline):
    """
    Deploy an exam to the website. You must specify an exam JSON and associated roster CSV.
    You can deploy the JSON multiple times and the password will remain unchanged.
    """
    json = json.read()
    roster = csv.reader(roster, delimiter=",")

    json = loads(json)

    json["default_deadline"] = default_deadline
    json["secret"] = Fernet.generate_key().decode("utf-8")

    try:
        json["secret"] = get_exam(exam=exam)["secret"]
    except (TypeError, KeyError):
        pass

    set_exam(exam=exam, json=json)

    next(roster)  # ditch headers
    set_roster(exam=exam, roster=list(roster))

    print("Exam uploaded with password:", json["secret"][:-1])


if __name__ == "__main__":
    deploy()
