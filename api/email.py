import os

from sendgrid import SendGridAPIClient


def send_email(data):
    try:
        send_email(data)
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.client.mail.send.post(data)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)

