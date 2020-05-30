import examtool.api.download
from examtool.api.gradescope_upload import APIClient
from examtool.api.fullGSapi.client import GradescopeClient
from examtool.api.fullGSapi.assignment_grader import GS_Crop_info, GS_Outline, GS_assignment_Grader, GS_Outline_Question, GS_Question, GroupTypes
from examtool.api.extract_questions import extract_groups, extract_questions, extract_public
import os
import time

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

        # TODO For each question, group, add rubric and grade
        print("Setting the grade type for grouping for each question....")
        gs_outline = examtool_outline.get_gs_outline()
        self.set_group_types(gs_outline)

        # Fetch the student email to question id map
        print("Fetching the student email to submission id's mapping....")
        email_to_question_sub_id = grader.student_email_to_submission_ids()

        # Finally we can process each question
        print("Grouping and grading questions...")
        for qid, question in gs_outline.questions_iterator():
            print(f"Processing question {qid}...")
            self.process_question(qid, question, email_to_responses_map, email_to_question_sub_id)


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

    def set_group_types(self, outline: GS_Outline, debug=True):
        for qid, question in outline.questions_iterator():
            self.set_group_type(question)
    
    def set_group_type(self, o_question: GS_Outline_Question):
        question_type = o_question.data.get("type")
        q = o_question.get_gs_question()
        q_type = GroupTypes.complex
        if question_type in ["select_all", "multiple_choice"]:
            q_type = GroupTypes.mc
        if question_type in ["long_answer", "long_code_answer"]:
            q_type = GroupTypes.non_grouped
        return q.set_group_type(q_type)
    
    def process_question(self, num_id: str, question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict):
        # TODO Group questions
        groups = self.group_question(question, num_id, email_to_responses_map, email_to_question_sub_id_map)
        if groups:
            # TODO Add rubrics
            self.add_rubric(question, email_to_responses_map, email_to_question_sub_id_map)
            # in here, add check to see if qid is equal to either name or sid q id so we do not group those.
            # TODO Grade questions
            self.grade_question(question, email_to_responses_map, email_to_question_sub_id_map)
    
    def group_question(self, num_id: str, question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict):
        while not question.is_grouping_ready():
            timeout = 5
            print(f"Question grouping not ready! Retrying in {timeout} seconds.")
            time.sleep(timeout)
        qtype = question.data.get("type")
        if qtype == "multiple_choice":
            return self.group_mc_question(question, email_to_responses_map, email_to_question_sub_id_map)
        elif qtype == "select_all":
            return self.group_sel_all_question(question, email_to_responses_map, email_to_question_sub_id_map)
        elif qtype in ["short_answer", "short_code_answer"]:
            return self.group_short_ans_question(question, email_to_responses_map, email_to_question_sub_id_map)
        elif qtype in ["long_answer", "long_code_answer"]:
            return self.group_long_ans_question(question, email_to_responses_map, email_to_question_sub_id_map)
        else:
            print(f"Unsupported question type {qtype} for question {question.data}!")
            return None


    def group_mc_question(self, num_id: str, question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict):
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        correct_seq = []
        solution_options = data.get("solution", {}).get("options", [])
        for option in data.get("options", []):
            correct_seq.append(option in solution_options)

        groups = {
            "correct_seq": correct_seq,
            # groups is a list of tuples where index:
            # 0 is the name of the group
            # 1 is the selected sequence (list of true false for selected) and
            # 2 is the list of submission id's which selected that.
            "groups": [],
        }

        for email, submission_ids in email_to_question_sub_id_map.items():
            pass

        return groups

    def group_sel_all_question(self, num_id: str, question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict):
        return self.group_mc_question(question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict)

    def group_short_ans_question(self, num_id: str, question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict):
        pass

    def group_long_ans_question(self, num_id: str, question: GS_Question, email_to_responses_map: dict, email_to_question_sub_id_map: dict):
        """
        We will not be grouping long ans question so we will skip and return.
        """
        return None
    
    def add_rubric(self, question):
        pass

    def grade_question(self, question):
        pass

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