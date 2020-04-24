import base64
import csv
import os

import click
from sendgrid import SendGridAPIClient


@click.command()
@click.option(
    "--roster", prompt=True, default="sample_roster.csv", type=click.File("r")
)
@click.option("--pdf-folder", prompt=True, default="out", type=click.Path())
def send_emails(roster, pdf_folder):
    roster = csv.reader(roster, delimiter=",")

    next(roster)

    roster = list(roster)

    if input("Sending email to {} people - confirm? (y/N) ".format(len(roster))).lower() != "y":
        exit(1)

    for email, _ in roster:
        body = (
            "Hello!\n\n"
            "You have an upcoming exam taking place on exam.cs61a.org. "
            "You should complete your exam on that website.\n\n"
            "However, if you encounter technical difficulties and are unable to do so, "
            "we have attached an encrypted PDF containing the same exam. "
            "You can then complete your exam on the Google Form provided to you by "
            "course staff. "
            "Your submissions on exam.cs61a.org will be merged with your Google Form "
            "responses, so you can switch from exam.cs61a.org to the Google Form "
            "halfway through the exam if you want, without having to resubmit answers. "
            "To unlock the PDF, its password will be revealed on Piazza when the exam starts.\n\n"
            "Good luck, and remember to have fun!"
        )

        with open(
            os.path.join(
                pdf_folder, "exam_" + email.replace("@", "_").replace(".", "_") + ".pdf"
            ),
            "rb"
        ) as f:
            pdf = base64.b64encode(f.read()).decode("ascii")
        data = {
            "from": {"email": "cs61a@berkeley.edu", "name": "CS 61A Exam Platform"},
            "personalizations": [
                {"to": [{"email": email}], "substitutions": {}}
            ],
            "subject": "CS 61A Final Exam PDF",
            "content": [{"type": "text/plain", "value": body}],
            "attachments": [
                {
                    "content": pdf,
                    "type": "application/pdf",
                    "filename": "Encrypted CS 61A Exam",
                    "disposition": "attachment",
                }
            ],
        }

        try:
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            response = sg.client.mail.send.post(data)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    send_emails()
