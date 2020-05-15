def boolstring(bool):
    return "Matches solution." if bool else "May not match solution."


def grade(question, responses, dispatch=None):
    if dispatch:
        if dispatch(question):
            return dispatch(question)(responses)
    response = responses.get(question["id"])
    if "solution" not in question:
        return "Instant autograder unavailable."

    if response is None:
        return boolstring(False)

    if question["type"] == "multiple_choice":
        return boolstring(response in question["solution"]["options"])
    elif question["type"] == "select_all":
        return boolstring(sorted(response) == sorted(question["solution"]["options"]))
    else:
        return boolstring(response == question["solution"]["solution"]["text"])
