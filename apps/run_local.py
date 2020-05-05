import os
import sys
from os import getenv

from flask import Flask, request

mode = getenv("MODE")

if mode == "exam":
    sys.path.append(os.path.abspath("exam"))
    os.chdir("exam")
    from exam.main import index

if mode == "admin":
    sys.path.append(os.path.abspath("admin"))
    os.chdir("admin")
    from main import index

if mode == "write":
    sys.path.append(os.path.abspath("write"))
    os.chdir("write")
    from write.app import app
    app.run()


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def main(path="/"):
    return index(request)


if __name__ == '__main__':
    app.run()
