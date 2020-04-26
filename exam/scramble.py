import random


def scramble(email, exam):
    random.seed(email)
    global_substitutions = select(exam["substitutions"])
    exam["config"]["scramble_groups"] = exam["config"].get("scramble_groups", [-1]) or range(100)
    if 0 in exam["config"]["scramble_groups"]:
        random.shuffle(exam["groups"])
    for group in exam["groups"]:
        scramble_group(group, [global_substitutions], exam["config"], 1)
    exam.pop("config", None)

    return exam


def scramble_group(group, substitutions, config, depth):
    group_substitutions = select(group["substitutions"])
    substitute(
        group,
        [*substitutions, group_substitutions],
        ["name", "html", "tex", "text"],
    )
    if depth in config["scramble_groups"]:
        random.shuffle(group["elements"])
    for element in group["elements"]:
        if element.get("type") == "group":
            scramble_group(element, [*substitutions, group_substitutions], config, depth + 1)
        else:
            scramble_question(element, [*substitutions, group_substitutions], config)


def scramble_question(question, substitutions, config):
    question_substitutions = select(question["substitutions"])
    substitute(
        question,
        [question_substitutions, *substitutions],
        ["html", "tex", "text"],
    )
    if "scramble_options" in config and isinstance(question["options"], list):
        random.shuffle(question["options"])
        for option in question["options"]:
            substitute(
                option,
                [
                    *substitutions,
                    question_substitutions,
                ],
                ["html", "tex", "text"],
            )


def select(substitutions):
    out = {}
    for k, v in substitutions.items():
        out[k] = random.choice(v)
    return out


def substitute(target: dict, list_substitutions, attrs):
    for substitutions in list_substitutions:
        for attr in attrs:
            for k, v in substitutions.items():
                target[attr] = target[attr].replace(k, v)
                target[attr] = target[attr].replace(k.title(), v.title())
    target.pop("substitutions", None)
