import csv
from datetime import datetime

import click
import pytz
from google.cloud import firestore


def time(timestamp):
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc).astimezone(pytz.timezone("America/Los_Angeles"))


@click.command()
@click.option("--email", default=None)
@click.option("--roster", default=None, type=click.File("r"))
@click.option("--exam", prompt=True, default="cs61a-test-final")
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
        times = []
        for record in db.collection(exam).document(email).collection("log").stream():
            record = record.to_dict()
            ref = time(record.pop("timestamp"))
            times.append([ref, next(iter(record.keys())), next(iter(record.values()))])
        print("\n".join(str(x) + " " + str(y) + " " + str(z) for x, y, z in sorted(times)))

    all_students.sort(key=lambda x: x[0])

    print("\n".join(str(x) + " " + str(y) for x, y in all_students))


if __name__ == '__main__':
    get_last_submission()
