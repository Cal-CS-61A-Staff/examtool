import json
import random
import string

import pypandoc


class LineBuffer:
    def __init__(self, text):
        self.lines = text.strip().split("\n")
        self.i = 0

    def pop(self) -> str:
        if self.i == len(self.lines):
            raise SyntaxError("File terminated unexpectedly")
        self.i += 1
        return self.lines[self.i - 1]

    def empty(self):
        return self.i == len(self.lines)


def directive_type(line):
    if not line.startswith("# BEGIN ") and not line.startswith("# END ") and not line.startswith("# INPUT "):
        return None, None, None
    tokens = line.split(" ", 3)
    return tokens[1], tokens[2] if len(tokens) > 2 else "", tokens[3] if len(tokens) > 3 else ""


def get_points(line):
    tokens = line.split(" ")
    point_sec = tokens[-1]
    if not point_sec or point_sec[0] != "[" or point_sec[-1] != "]":
        return line, None
    try:
        return " ".join(tokens[:-1]), float(point_sec[1:-1])
    except ValueError:
        return line, None


def rand_id():
    return ''.join(random.choices(string.ascii_uppercase, k=32))


def parse(text):
    return pypandoc.convert_text(text, "html5", "md", ["--mathjax"])


def parse_input_lines(lines):
    if not lines:
        raise SyntaxError("No INPUT directives found in QUESTION")
    _, directive, rest = directive_type(lines[0])
    if directive == "OPTION" or directive == "SELECT":
        options = []
        for line in lines:
            _, other_directive, rest = directive_type(line)
            if other_directive != directive:
                raise SyntaxError("Multiple INPUT types found in a single QUESTION")
            options.append(parse(rest))
        return "multiple_choice" if directive == "OPTION" else "select_all", options
    elif directive == "SHORT_ANSWER":
        if len(lines) > 1:
            raise SyntaxError("Multiple INPUT directives found for a SHORT_ANSWER")
        return "short_answer", None


def consume_rest_of_question(buff):
    contents = []
    input_lines = []
    while True:
        line = buff.pop()
        mode, directive, rest = directive_type(line)
        if mode is None:
            if input_lines and line.strip():
                raise SyntaxError("Unexpected content in QUESTION after INPUT")
            elif not input_lines:
                contents.append(line)
        elif mode == "INPUT":
            input_lines.append(line)
        elif mode == "END":
            if directive == "QUESTION":
                question_type, options = parse_input_lines(input_lines)
                return {
                    "id": rand_id(),
                    "type": question_type,
                    "html": parse("\n".join(contents)),
                    "options": options,
                }
            else:
                raise SyntaxError("Unexpected END in QUESTION")
        else:
            raise SyntaxError("Unexpected directive in QUESTION")


def consume_rest_of_group(buff):
    group_contents = []
    questions = []
    started_question = False
    while True:
        line = buff.pop()
        mode, directive, rest = directive_type(line)
        if mode is None:
            if started_question and line.strip():
                raise SyntaxError("Unexpected text in GROUP after QUESTIONs started")
            elif not started_question:
                group_contents.append(line)
        elif mode == "BEGIN" and directive == "QUESTION":
            started_question = True
            title, points = get_points(rest)
            if title:
                raise SyntaxError("Unexpected arguments passed in BEGIN QUESTION directive")
            question = consume_rest_of_question(buff)
            question["points"] = points
            questions.append(question)
        elif mode == "END" and directive == "GROUP":
            return "\n".join(group_contents), questions
        else:
            raise SyntaxError("Unexpected directive in GROUP")


def consume_group(buff):
    while True:
        group_line = buff.pop()
        if group_line.strip():
            break
    mode, directive, rest = directive_type(group_line)
    if mode != "BEGIN" or directive not in ("GROUP", "PUBLIC"):
        raise SyntaxError("Expected BEGIN GROUP or BEGIN PUBLIC directive")
    title, points = get_points(rest)

    body, questions = consume_rest_of_group(buff)

    return {
        "name": title,
        "points": points,
        "html": parse(body),
        "questions": questions,
    }


def convert(text):
    buff = LineBuffer(text)
    groups = []

    try:
        while not buff.empty():
            groups.append(consume_group(buff))
    except SyntaxError as e:
        raise SyntaxError("Parse stopped on line {} with error {}".format(buff.i, e))

    return {
        "groups": groups,
    }


def convert_str(text):
    return json.dumps(convert(text), indent=2)
