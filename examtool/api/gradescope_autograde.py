import examtool.api.download

def generate_and_upload_exams_and_setup_outline(exam, out, name_question_id, sid_question_id, compact=False):
    template_questions, email_to_data_map, total = examtool.api.download.download(exam)
    examtool.api.download.export(template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id, compact)

def grade_assignment():
    pass