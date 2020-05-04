"""
Developed by Data 8 course staff - all credit goes to them!
"""
import csv
import json
import os

import click
import requests

GRADESCOPE_URL = "https://www.gradescope.com/api/v1/courses/{}/assignments/{}/submissions"


class APIClient:
    def __init__(self):
        self.session = requests.Session()

    def log_in(self, email, password):
        login_url = "https://www.gradescope.com/api/v1/user_session"

        form_data = {
            "email": email,
            "password": password
        }
        r = self.post(login_url, data=form_data)
        print(r.status_code, r.json())

        self.token = r.json()['token']

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def upload_submission(self, course_id, assignment_id, student_email, filename):
        url = GRADESCOPE_URL.format(course_id, assignment_id)
        form_data = {"owner_email": student_email}
        files = {'pdf_attachment': open(filename, 'rb')}
        request_headers = {'access-token': self.token}

        num_attempts = 0
        while num_attempts < 5:  # Control how many times to retry
            r = self.post(url, data=form_data, headers=request_headers, files=files)
            if r.status_code == 200:
                return
            if r.status_code != 200:
                num_attempts += 1

        # Report error
        print('Issue uploading to Gradescope. Gradescope error output below:', student_email)
        error_lines = json.loads(r._content)['errors']
        for line in error_lines:
            print(line)
        print("Upload URL:", url)


@click.command()
@click.option("--course", prompt=True)
@click.option("--assignment", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--exam", prompt=True, default="cs61a-test-final")
def upload_folder(course, assignment, email, password, exam):
    target = "out/export/" + exam

    client = APIClient()
    client.log_in(email, password)

    for file_name in os.listdir(target):
        if "@" not in file_name:
            continue
        student_email = file_name[:-4]
        # print("Uploading:", file_name)
        client.upload_submission(course, assignment, student_email, os.path.join(target, file_name))


if __name__ == '__main__':
    upload_folder()
