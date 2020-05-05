import csv
from json import loads

import click
from cryptography.fernet import Fernet
from google.cloud import firestore
from google.cloud.exceptions import NotFound

from api.database import set_exam, get_exam, set_roster
from cli.utils import exam_name_option


@click.command()
@exam_name_option
@click.option(
    "--json",
    prompt=True,
    default="data/exams/sample_exam.json",
    type=click.File("r"),
    help="The json JSON you wish to deploy.",
)
@click.option(
    "--roster",
    prompt=True,
    default="data/rosters/sample_roster.csv",
    type=click.File("r"),
    help="The json roster you wish to deploy.",
)
@click.option(
    "--default-deadline",
    prompt=True,
    default=0,
    type=int,
    help="Specify if you want unregistered students to be able to take the json, with this as the default deadline.",
)
def deploy(exam, json, roster, default_deadline):
    """
    Deploy an json to the website. You must specify a JSON and associated roster CSV.
    You can deploy the json multiple times and the password will remain unchanged.
    """
    json = json.read()
    roster = csv.reader(roster, delimiter=",")

    json = loads(json)

    json["default_deadline"] = default_deadline
    json["secret"] = Fernet.generate_key()

    try:
        json["secret"] = get_exam(exam)["secret"]
    except (NotFound, TypeError):
        pass

    set_exam(exam, json)

    next(roster)  # ditch headers
    set_roster(exam, roster)

    print("Exam uploaded with password:", json["secret"][:-1].decode("utf-8"))


if __name__ == "__main__":
    deploy()
