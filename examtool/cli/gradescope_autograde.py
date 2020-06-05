import os
import json

import click

from examtool.cli.utils import exam_name_option, hidden_target_folder_option
from examtool.api.gradescope_autograde import GradescopeGrader


@click.command()
@click.option("--exam", prompt=True, multiple=True, default=["cs61a-test-final"], help="The list of exam names. If it is just one exam, just include one. Separate exam names by spaces.")
@click.option("--name-question", default=None, prompt=True, help="The ID of the question for the student's name.")
@click.option("--sid-question", default=None, prompt=True, help="The ID of the question for the student's SID.")
@click.option("--course", prompt=True, help="The Gradescope course ID.")
@click.option("--assignment", default=None, help="The Gradescope assignment ID. If this is left blank, this tool will create the Gradescope assignment.")
@click.option("--assignment-title", default=None, help="The title you want the Gradescope assignment to have.")
@click.option("--email", prompt=True, help="Your Gradescope email address.")
@click.option("--password", prompt=True, hide_input=True, help="Your Gradescope account password.")
@click.option("--emails", multiple=True, default=None, help="This is a list of emails you want to autograde to the assignment. If left blank, it will include all emails from the exams. Selection occurres before mutation.")
@click.option("--mutate-emails", default=None, help="This is a json dictionary which maps the email on examtool to the default email on gradescope ({str:str}). It will not mutate emails which are not in the list. If this is left blank, it will not mutate any emails.")
@click.option("--create/--update", default=True, help="Create will generate the outline and set the grouping type, update will ")
@hidden_target_folder_option
def gradescope_autograde(exam, name_question, sid_question, course, assignment, title, email, password, emails, mutate_emails, create_or_update, target):
    """
    Uploads and autogrades the given exam(s).
    """
    target = target or "out/export/" + exam

    grader = GradescopeGrader(email=email, password=password)

    if create_or_update or assignment is None:
        email_mutation_list = None
        if mutate_emails:
            with open(mutate_emails, "r") as f:
                email_mutation_list = json.load(f)
        grader.main(exam, target, name_question, sid_question, course, gs_assignment_id=assignment, gs_assignment_title=title, emails=emails, email_mutation_list=email_mutation_list)
    else:
        grader.add_additional_exams(exam, target, name_question, sid_question, course, assignment, emails=emails, email_mutation_list=mutate_emails)


if __name__ == '__main__':
    gradescope_autograde()
