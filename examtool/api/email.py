import os
from os import getenv

from examtool.api.server_delegate import server_only

if getenv("ENV") == "SERVER":
    from sendgrid import SendGridAPIClient


@server_only
def send_email(*, exam, data):
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    sg.client.mail.send.post(data)


@server_only
def send_email_batch(*, exam, data_list):
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    for data in data_list:
        sg.client.mail.send.post(data)


@server_only
def get_api_key(*, exam):
    return os.environ.get("SENDGRID_API_KEY")


def send_email_local(key, data):
    sg = SendGridAPIClient(key)
    response = sg.client.mail.send.post(data)
    print(response.status_code)
    print(response.body)
    print(response.headers)
