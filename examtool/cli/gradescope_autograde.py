"""
Developed by ThaumicMekanism [Stephan K.] - all credit goes to him!
"""
import os
import json

import click

from examtool.cli.utils import exam_name_option, hidden_target_folder_option
from examtool.api.gradescope_autograde import GradescopeGrader


@click.command()
@click.option("--exam", default="cs61a-test-final", help="The list of exam names. If it is just one exam, just include one. Separate exams with commas: Eg 'cs61a-final-8am,cs61c-final-10am`")
@click.option("--name-question", default=None, prompt=True, help="The ID of the question for the student's name.")
@click.option("--sid-question", default=None, prompt=True, help="The ID of the question for the student's SID.")
@click.option("--course", prompt=True, help="The Gradescope course ID.")
@click.option("--assignment", default=None, help="The Gradescope assignment ID. If this is left blank, this tool will create the Gradescope assignment.")
@click.option("--assignment-title", default=None, help="The title you want the Gradescope assignment to have.")
@click.option("--email", prompt=True, help="Your Gradescope email address.")
@click.option("--password", prompt=True, hide_input=True, help="Your Gradescope account password.")
@click.option("--emails", default=None, help="This is a list of emails you want to autograde to the assignment. Separate emails with a comma. If left blank, it will include all emails from the exams. Selection occurres before mutation.")
@click.option("--mutate-emails", default=None, help="This is a json dictionary which maps the email on examtool to the default email on gradescope ({str:str}). It will not mutate emails which are not in the list. If this is left blank, it will not mutate any emails.")
@click.option("--question-numbers", default=None, help="This is a list of question numbers you want to autograde to the assignment (Numbers are defined by the Gradescope question number). Separate question numbers with a comma. If left blank, it will grade all questions from the exams.")
@click.option("--create/--update", default=True, help="Create will generate the outline and set the grouping type, update will ")
@hidden_target_folder_option
def gradescope_autograde(exam, name_question, sid_question, course, assignment, assignment_title, email, password, emails, mutate_emails, question_numbers, create, target):
    """
    Uploads and autogrades the given exam(s).
    """
    exam = [e.strip() for e in exam.split(",")]
    target = target or "out/export/" + exam[0]

    grader = GradescopeGrader(email=email, password=password)
    email_mutation_list = None
    if mutate_emails:
        with open(mutate_emails, "r") as f:
            email_mutation_list = json.load(f)
    if emails is not None:
        emails = [e.strip() for e in emails.split(",")]
    if question_numbers is not None:
        question_numbers = [qn.strip() for qn in question_numbers.split(",")]
    if create or assignment is None:
        grader.main(exam, target, name_question, sid_question, course, gs_assignment_id=assignment, gs_assignment_title=assignment_title, emails=emails, email_mutation_list=email_mutation_list, question_numbers=question_numbers)
    else:
        grader.add_additional_exams(exam, target, name_question, sid_question, course, assignment, emails=emails, email_mutation_list=email_mutation_list, question_numbers=question_numbers)


if __name__ == '__main__':
    gradescope_autograde()
