import os
import sys
from os import getenv

from flask import Flask, request

mode = getenv("MODE")

if mode == "student":
    sys.path.append(os.path.abspath("student"))
    os.chdir("student")
    from student.main import index

if mode == "staff":
    sys.path.append("staff")
    os.chdir("staff")
    from student.main import index


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def main(path="/"):
    return index(request)


if __name__ == '__main__':
    app.run()
