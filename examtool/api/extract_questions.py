from examtool.api.scramble import is_compresable_group

def extract_questions(exam, extract_public: bool=True):
    if extract_public:
        yield from extract_public(exam)
    for group in exam["groups"]:
        yield from group_questions(group)


def group_questions(group):
    out = _group_questions(group)
    try:
        first = next(out)
    except StopIteration:
        return
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

def extract_public(exam):
    if exam.get("public"):
        yield from group_questions(exam["public"])

def extract_groups(group):
    for g in group["groups"]:
        if is_compresable_group(g):
            for g2 in g["groups"]:
                yield g2
        else:
            yield g