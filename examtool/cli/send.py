import base64
import os

import click

from examtool.api import get_roster
from examtool.api import send_email
from examtool.cli.utils import hidden_target_folder_option, exam_name_option, prettify


@click.command()
@exam_name_option
@hidden_target_folder_option
@click.option("--email", help="The email address of a particular student.")
def send(exam, target, email):
    """
    Email an encrypted PDF to all students taking an exam. Specify `email` to email only a particular student.
    """
    if not target:
        target = "out/latex/" + exam

    course = prettify(exam.split("-")[0])

    roster = []
    if email:
        roster = [email]
    else:
        for email, deadline in get_roster(exam):
            if deadline:
                roster.append(email)

    if input("Sending email to {} people - confirm? (y/N) ".format(len(roster))).lower() != "y":
        exit(1)

    for email, deadline in roster:
        if not int(deadline):
            continue

        body = (
            "Hello!\n\n"
            "You have an upcoming exam taking place on exam.cs61a.org. "
            "You should complete your exam on that website.\n\n"
            "However, if you encounter technical difficulties and are unable to do so, "
            "we have attached an encrypted PDF containing the same exam. "
            "You can then email your exam solutions to course staff before the deadline "
            "rather than submitting using exam.cs61a.org. "
            "To unlock the PDF, its password will be revealed on Piazza when the exam starts.\n\n"
            "Good luck, and remember to have fun!"
        )

        with open(
            os.path.join(
                target, "exam_" + email.replace("@", "_").replace(".", "_") + ".pdf"
            ),
            "rb"
        ) as f:
            pdf = base64.b64encode(f.read()).decode("ascii")
        data = {
            "from": {"email": "cs61a@berkeley.edu", "name": "CS 61A Exam Platform"},
            "personalizations": [
                {"to": [{"email": email}], "substitutions": {}}
            ],
            "subject": "{course} Final Exam PDF".format(course=course),
            "content": [{"type": "text/plain", "value": body}],
            "attachments": [
                {
                    "content": pdf,
                    "type": "application/pdf",
                    "filename": "Encrypted {course} Exam.pdf".format(course=course),
                    "disposition": "attachment",
                }
            ],
        }

        send_email(data)


if __name__ == "__main__":
    send()
