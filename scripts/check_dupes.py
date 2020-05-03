import os
from collections import defaultdict

import click


@click.command()
@click.argument("targets", nargs=-1, type=click.Path())
def check_dupes(targets):
    files = defaultdict(list)
    for target in targets:
        for file in os.listdir(target):
            if "@" not in file:
                continue
            files[file].append(target)
    for file, exams in files.items():
        if len(exams) > 1:
            print(file, exams)


if __name__ == '__main__':
    check_dupes()

