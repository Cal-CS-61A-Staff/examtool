import requests
import json

GRADESCOPE_URL = "https://www.gradescope.com/api/v1/courses/{}/assignments/{}/submissions"

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None

    def log_in(self, email, password):
        login_url = "https://www.gradescope.com/api/v1/user_session"

        form_data = {
            "email": email,
            "password": password
        }
        r = self.post(login_url, data=form_data)
        print(r.status_code, r.json())

        self.token = r.json()['token']

    def is_logged_in(self):
        return self.token is not None

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