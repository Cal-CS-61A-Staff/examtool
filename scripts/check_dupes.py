import glob
import os
from collections import defaultdict

import click


@click.command()
@click.option("--exam", prompt=True, default="cs61a-test-final")
def check_dupes(exam):
    files = defaultdict(list)
    for target in os.listdir("out/export"):
        if not target.startswith(exam):
            continue
        target = os.path.join("out/export", target)
        if not os.path.isdir(target):
            continue
        for file in os.listdir(target):
            if "@" not in file:
                continue
            files[file].append(target)
    for file, exams in files.items():
        if len(exams) > 1:
            print(file, exams)


if __name__ == '__main__':
    check_dupes()

