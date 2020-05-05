import re
from functools import wraps
from os import getenv

import click

from cli import auth

exam_name_option = click.option(
    "--exam", prompt=True, default="cs61a-test-final", help="The exam name."
)
hidden_output_folder_option = click.option(
    "--out",
    default=None,
    help="Output folder. Leave as default for dependent commands to work.",
    type=click.Path()
)
hidden_target_folder_option = click.option(
    "--target",
    default=None,
    help="Target folder for PDFs. Leave as default unless the source output folder is not the default.",
    type=click.Path()
)


def prettify(course_code):
    m = re.match(r"([a-z]+)([0-9]+[a-z]?)", course_code)
    return m and (m.group(1) + " " + m.group(2)).upper()


def delegate_to_server(func):
    @wraps(func)
    def wrapped(**kwargs):
        if getenv("SERVER"):
            from google.cloud import firestore
            return func(**kwargs, db=firestore.Client())
        else:
            token = auth.OAuthSession().auth()
            method = func.__name__

    return wrapped
