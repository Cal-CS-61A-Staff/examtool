import csv
from datetime import datetime

import click
import pytz
from google.cloud import firestore


@click.command()
@click.option("--email", default=None)
@click.option("--roster", default=None, type=click.File("r"))
@click.option("--exam")
def get_last_submission(email, exam, roster):
    db = firestore.Client()
    if roster:
        roster = csv.reader(roster, delimiter=",")
        next(roster)
        emails = [x[0] for x in roster if x[1]]
    else:
        emails = [email]

    all_students = []

    for email in emails:
        print(email)
        latest = 0
        for record in db.collection(exam).document(email).collection("log").stream():
            record = record.to_dict()
            latest = max(latest, record["timestamp"])
        latest = datetime.utcfromtimestamp(latest).replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/Los_Angeles"))
        all_students.append([email, latest])

    all_students.sort(key=lambda x: x[0])

    print(all_students)


if __name__ == '__main__':
    get_last_submission()
