import random


def scramble(email, exam, *, keep_data=False):
    random.seed(email)

    def scramble_group(group, substitutions, config, depth):
        group_substitutions = select(group["substitutions"])
        group_substitutions.update(
            select_no_replace(group.get("substitutions_match", []))
        )
        substitute(
            group,
            [*substitutions, group_substitutions],
            ["name", "html", "tex", "text"],
        )
        if depth in config["scramble_groups"] or group.get("scramble"):
            scramble_keep_fixed(get_elements(group))
        if group.get("pick_some"):
            get_elements(group)[:] = random.sample(
                get_elements(group), group["pick_some"]
            )
        for element in get_elements(group):
            if element.get("type") == "group":
                scramble_group(
                    element, [*substitutions, group_substitutions], config, depth + 1
                )
            else:
                scramble_question(
                    element, [*substitutions, group_substitutions], config
                )
        if (is_compresable_group(group)):
            text, html, tex = group["text"], group["html"], group["tex"]
            element = get_elements(group)[0]
            if element.get("type") != "group" and depth == 1:
                return
            group.clear()
            group.update(element)
            group["text"] = text + "\n" + group["text"]
            group["html"] = html + "\n" + group["html"]
            group["tex"] = tex + "\n" + group["tex"]

    def scramble_question(question, substitutions, config):
        question_substitutions = select(question["substitutions"])
        question_substitutions.update(
            select_no_replace(question.get("substitutions_match", []))
        )
        substitute(
            question, [question_substitutions, *substitutions], ["html", "tex", "text"]
        )
        if "scramble_options" in config and isinstance(question["options"], list):
            scramble_keep_fixed(question["options"])
            for option in question["options"]:
                substitute(
                    option,
                    [*substitutions, question_substitutions],
                    ["html", "tex", "text"],
                )

        if keep_data and "solution" in question:
            solution = question["solution"]
            if solution.get("solution") is not None:
                substitute(
                    solution["solution"], [question_substitutions, *substitutions], ["html", "tex", "text"], store=False
                )
            else:
                options = solution["options"]
                if options:
                    substitute(
                        options,
                        [question_substitutions, *substitutions],
                        range(len(options)),
                        store=False,
                    )
        else:
            question.pop("solution", None)

    def substitute(target: dict, list_substitutions, attrs, *, store=True):
        merged = {}
        for substitutions in list_substitutions:
            merged = {**merged, **substitutions}
            for attr in attrs:
                for k, v in substitutions.items():
                    target[attr] = target[attr].replace(k, v)
                    target[attr] = target[attr].replace(k.title(), v.title())
        if store:
            if keep_data:
                target["substitutions"] = merged
            else:
                target.pop("substitutions", None)

    global_substitutions = select(exam["substitutions"])
    global_substitutions.update(select_no_replace(exam.get("substitutions_match", [])))
    exam["config"]["scramble_groups"] = exam["config"].get(
        "scramble_groups", [-1]
    ) or range(100)
    if 0 in exam["config"]["scramble_groups"]:
        scramble_keep_fixed(exam["groups"])
    for group in exam["groups"]:
        scramble_group(group, [global_substitutions], exam["config"], 1)
    exam.pop("config", None)

    return exam


def scramble_keep_fixed(objects):
    movable_object_pos = []
    movable_object_values = []
    for i, object in enumerate(objects):
        if not object.get("fixed"):
            movable_object_pos.append(i)
            movable_object_values.append(object)
    random.shuffle(movable_object_values)
    for i, object in zip(movable_object_pos, movable_object_values):
        objects[i] = object


def get_elements(group):
    return group.get("elements") if "elements" in group else group.get("questions")


def select(substitutions):
    out = {}
    # DEFINE
    for k, v in sorted(substitutions.items()):
        out[k] = random.choice(v)
    return out


def select_no_replace(substitutions_match):
    out = {}
    # DEFINE MATCH
    for item in substitutions_match:
        k = item["directives"]
        v = item["replacements"]
        values = v.copy()
        for choice in k:
            c = random.choice(values)
            values.remove(c)
            out[choice] = c
    return out

def is_compresable_group(group):
    return group.get("pick_some") == 1 and not group["name"].strip() and group["points"] is None