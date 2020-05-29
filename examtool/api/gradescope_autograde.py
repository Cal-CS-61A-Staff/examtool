import examtool.api.download
from examtool.api.gradescope_upload import APIClient
from examtool.api.fullGSapi.client import GradescopeClient
from examtool.api.fullGSapi.assignment_grader import GS_Crop_info, GS_Outline, GS_assignment_Grader, GS_Outline_Question
from examtool.api.extract_questions import extract_groups, extract_questions, extract_public
import os

class GradescopeGrader:
    def __init__(self, email: str=None, password: str=None, gs_client: GradescopeClient=None, gs_api_client: APIClient=None):
        if gs_client is None:
            gs_client = GradescopeClient()
        if gs_api_client is None:
            gs_api_client = APIClient()

        if (not email or not password) and (not gs_client.is_logged_in() or not gs_api_client.is_logged_in()):
            raise ValueError("You must supply the username and password if you are not already logged into the passed in clients!")

        self.gs_client = gs_client
        self.gs_api_client = gs_api_client

        if email and password:
            if not gs_client.is_logged_in():
                self.gs_client.log_in(email, password)
            if not self.gs_api_client.is_logged_in():
                self.gs_api_client.log_in(email, password)

    def main(
        self, 
        exam: str, 
        out: str, 
        name_question_id: str, 
        sid_question_id: str, 
        gs_class_id: str, 
        gs_assignment_id: str=None, # If none, we will create a class.
        gs_assignment_title: str="Examtool Exam",
        ):

        out = out or "out/export/" + exam
        exam_json, template_questions, email_to_data_map, total = examtool.api.download.download(exam)

        self.export_exam(template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id)

        # Create assignment if one is not already created.
        if gs_assignment_id is None:
            outline_path = f"{out}/OUTLINE.pdf"
            gs_assignment_id = self.create_assignment(gs_class_id, gs_assignment_title, outline_path)
            if not gs_assignment_id:
                raise ValueError("Did not receive a valid assignment id. Did assignment creation fail?")

        # Lets now get the assignment grader
        grader: GS_assignment_Grader = self.get_assignment_grader(gs_class_id, gs_assignment_id)
        
        # Now that we have the assignment and outline pdf, lets generate the outline.
        examtool_outline = ExamtoolOutline(grader, exam_json)

        # Finally we need to upload and sync the outline.
        self.upload_outline(grader, examtool_outline)

        # We can now upload the student submission since we have an outline
        self.upload_student_submissions(out, gs_class_id, gs_assignment_id)

        # TODO Add rubrics
        # TODO Group questions
        # in here, add check to see if qid is equal to either name or sid q id so we do not group those.
        # TODO Grade questions


    def export_exam(self, template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id):
        examtool.api.download.export(template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id)

    def create_assignment(self, gs_class_id: str, gs_title: str, outline_path: str):
        assignment_id = self.gs_client.create_exam(gs_class_id, gs_title, outline_path)
        if not assignment_id:
            print("Failed to create the exam! Make sure it has a unique title.")
            return
        return assignment_id

    def get_assignment_grader(self, gs_class_id: str, assignment_id: str) -> GS_assignment_Grader:
        return self.gs_client.get_assignment_grader(gs_class_id, assignment_id)

    def upload_outline(self, grader: GS_assignment_Grader, examtool_outline: "ExamtoolOutline"):
        outline = grader.update_outline(examtool_outline.get_gs_outline().json())
        if not outline:
            raise ValueError("Failed to upload or get the outline")
        examtool_outline.merge_gs_outline_ids(outline)

    def upload_student_submissions(self, out: str, gs_class_id: str, assignment_id: str):
        for file_name in os.listdir(out):
            if "@" not in file_name:
                continue
            student_email = file_name[:-4]
            self.gs_api_client.upload_submission(gs_class_id, assignment_id, student_email, os.path.join(out, file_name))

class ExamtoolOutline:
    name_region = GS_Crop_info(1, 2.4, 11.4, 100, 18.8)
    sid_region = GS_Crop_info(1, 2.4, 18.9, 100, 28.7)

    def __init__(self, grader: GS_assignment_Grader, exam_json: dict):
        self.exam_json = exam_json
        self.gs_number_to_exam_q, self.gs_outline = self.generate_gs_outline(grader, exam_json)

    def get_gs_crop_info(self, page, question=None):
        return GS_Crop_info(page, 0, 0, 100, 100)

    def question_to_gso_question(self, grader: GS_assignment_Grader, page, question: dict) -> GS_Outline_Question:
        weight = question.get("points")
        if not weight:
            weight = 0
        return GS_Outline_Question(
            grader, 
            None, 
            [self.get_gs_crop_info(page, question=question)],
            title=question.get("name", ""),
            weight=weight
            )

    def generate_gs_outline(self, grader: GS_assignment_Grader, exam_json: dict):
        gs_number_to_exam_q = {}
        questions = []

        page = 2 # Page 1 is an info page
        
        qid = 1
        if exam_json.get("public"):
            prev_page = 1
            g = GS_Outline_Question(grader, None, [self.get_gs_crop_info(page, exam_json.get("public"))], title="Public", weight=0)
            questions.append(g)
            sqid = 1
            for question in extract_public(exam_json):
                g.add_child(self.question_to_gso_question(grader, page, question))
                gs_number_to_exam_q[f"{qid}.{sqid}"] = question
                sqid += 1
                page += 1
            if page != prev_page:
                questions.append(g)
                qid += 1

        for group in extract_groups(exam_json):
            prev_page = page
            weight = group.get("points", "0")
            if not weight:
                weight = 0
            g = GS_Outline_Question(grader, None, self.get_gs_crop_info(page, group), title=group.get("name", ""), weight=weight)
            sqid = 1
            for question in extract_questions(group, extract_public=False):
                g.add_child(self.question_to_gso_question(grader, page, question))
                gs_number_to_exam_q[f"{qid}.{sqid}"] = question
                sqid += 1
                page += 1
            if page != prev_page:
                questions.append(g)
                qid += 1
        
        outline = GS_Outline(self.name_region, self.sid_region, questions)
        return (gs_number_to_exam_q, outline)

    def get_gs_outline(self):
        return self.gs_outline

    def merge_gs_outline_ids(self, outline: GS_Outline):
        self.gs_outline = outline
        for qnum, q in outline.questions_iterator():
            q.data = self.gs_number_to_exam_q["qnum"]
    
    def questions_iterator(self):
        yield from self.gs_outline.questions_iterator()