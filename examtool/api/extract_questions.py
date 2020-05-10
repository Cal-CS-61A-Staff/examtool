def extract_questions(exam):
    if "public" in exam:
        yield from group_questions(exam["public"])
    for group in exam["groups"]:
        yield from group_questions(group)


def group_questions(group):
    out = _group_questions(group)
    first = next(out)
    first["text"] = group["name"] + "\n\n" + group["text"] + "\n\n" + first["text"]
    yield first
    yield from out


def _group_questions(group):
    for element in group.get("elements", []) + group.get("questions", []):
        if element.get("type") == "group":
            out = group_questions(element)
            yield from out
        else:
            yield element
