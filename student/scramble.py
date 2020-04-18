import random


def scramble(email, exam, groups=True, questions=True, options=True):
    random.seed(email)
    if groups:
        random.shuffle(exam["groups"])
    for group in exam["groups"]:
        if questions:
            random.shuffle(group["questions"])
        for question in group["questions"]:
            if options and isinstance(question["options"], list):
                random.shuffle(question["options"])
    return exam
