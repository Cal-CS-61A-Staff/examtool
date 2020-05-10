import json

from examtool.api.database import get_exam
from examtool.api.extract_questions import extract_questions
from examtool.api.scramble import scramble, get_elements


def find_unexpected_words(exam, logs):
    data = get_exam(exam=exam)
    exam_json = json.dumps(data)
    for i, (email, log) in enumerate(logs):
        all_alternatives = get_substitutions(data)
        selected = {
            question["id"]: question["substitutions"]
            for question in extract_questions(scramble(email, json.loads(exam_json), keep_data=True))
        }
        for record in log:
            record.pop("timestamp")
            question = next(iter(record.keys()))
            answer = next(iter(record.values()))
            if question not in all_alternatives:
                continue
            for keyword, variants in all_alternatives[question].items():
                for variant in variants:
                    if variant == selected[question][keyword]:
                        continue
                    if variant in answer:
                        # check for false positive
                        for other in selected[question].values():
                            if variant in other and other != variant:
                                break
                        else:
                            print(email, selected[question], variant, answer)
                            break
                else:
                    continue
                break
            else:
                continue
            break


def get_substitutions(exam):
    out = {}

    def process_group(group, substitutions):
        group_substitutions = group["substitutions"]
        for element in get_elements(group):
            if element.get("type") == "group":
                process_group(element, {**substitutions, **group_substitutions})
            else:
                process_question(element, {**substitutions, **group_substitutions})

    def process_question(question, substitutions):
        out[question["id"]] = {**substitutions, **question["substitutions"]}

    global_substitutions = exam["substitutions"]
    for group in exam["groups"]:
        process_group(group, global_substitutions)

    return out
