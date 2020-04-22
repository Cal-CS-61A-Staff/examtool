import random


def scramble(email, exam, groups=True, questions=True, options=True):
    random.seed(email)
    global_substitutions = select(exam["substitutions"])
    if groups:
        random.shuffle(exam["groups"])
    for group in exam["groups"]:
        group_substitutions = select(group["substitutions"])
        substitute(
            group,
            [global_substitutions, group_substitutions],
            ["name", "html", "tex", "text"],
        )
        if questions:
            random.shuffle(group["questions"])
        for question in group["questions"]:
            question_substitutions = select(question["substitutions"])
            substitute(
                question,
                [question_substitutions, global_substitutions, group_substitutions],
                ["html", "tex", "text"],
            )
            if options and isinstance(question["options"], list):
                random.shuffle(question["options"])
                for option in question["options"]:
                    substitute(
                        option,
                        [
                            global_substitutions,
                            group_substitutions,
                            question_substitutions,
                        ],
                        ["html", "tex", "text"],
                    )

    return exam


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
