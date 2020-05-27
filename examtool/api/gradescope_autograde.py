import examtool.api.download
from examtool.api.gradescope_upload import APIClient
from examtool.api.fullGSapi.assignment_grader import GS_Crop_info, GS_Outline, GS_assignment_Grader
import os

def generate_and_upload_exams_and_setup_outline(gs_client, email, password, gs_class_id, gs_title, exam, out, name_question_id, sid_question_id):
    if not gs_client.logged_in:
        gs_client.log_in(email, password)
    out = out or "out/export/" + exam
    template_questions, email_to_data_map, total = examtool.api.download.download(exam)

    # This is temporary just for my debugging due to issues with emails.
    email_to_data_map["skaminsky115+test1@berkeley.edu"] = email_to_data_map["skaminsky115@berkeley.edu"]
    email_to_data_map.pop("skaminsky115@berkeley.edu", None)

    examtool.api.download.export(template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id)
    outline_path = f"{out}/OUTLINE.pdf"
    assignment_id = gs_client.create_exam(gs_class_id, gs_title, outline_path)
    if not assignment_id:
        print("Failed to create the exam! Make sure it has a unique title.")
        return

    # Create outline
    name_region = GS_Crop_info(1, 2.4, 11.4, 100, 18.8)
    sid_region = GS_Crop_info(1, 2.4, 18.9, 100, 28.7)
    questions = []

    # figure out questions to add.
    
    outline = GS_Outline(name_region, sid_region, questions)
    grader: GS_assignment_Grader = gs_client.get_assignment_grader(gs_class_id, assignment_id)
    grader.update_outline(outline.json())

    # Upload Student Submissions

    client = APIClient()
    client.log_in(email, password)

    for file_name in os.listdir(out):
        if "@" not in file_name:
            continue
        student_email = file_name[:-4]
        client.upload_submission(gs_class_id, assignment_id, student_email, os.path.join(out, file_name))
    
    return (template_questions, email_to_data_map, assignment_id)

def grade_assignment():
    pass