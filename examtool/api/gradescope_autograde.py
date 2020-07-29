"""
Developed by ThaumicMekanism [Stephan K.] - all credit goes to him!
"""

import examtool.api.download
from examtool.api.gradescope_upload import APIClient
from examtool.api.extract_questions import extract_groups, extract_questions, extract_public
from fullGSapi.api.client import GradescopeClient
from fullGSapi.api.assignment_grader import GS_Crop_info, GS_Outline, GS_assignment_Grader, GS_Outline_Question, GS_Question, GroupTypes, RubricItem, QuestionRubric
import os
import time

class GradescopeGrader:
    def __init__(self, email: str=None, password: str=None, gs_client: GradescopeClient=None, gs_api_client: APIClient=None):
        print(f"Setting up the Gradescope Grader...")
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
                print(f"Logging into the normal Gradescope API...")
                self.gs_client.log_in(email, password)
            if not self.gs_api_client.is_logged_in():
                print(f"Logging into the full Gradescope API...")
                self.gs_api_client.log_in(email, password)
        print(f"Finished setting up the Gradescope Grader")

    def main(
        self,
        exams: [str], 
        out: str, 
        name_question_id: str, 
        sid_question_id: str, 
        gs_class_id: str, 
        gs_assignment_id: str=None, # If none, we will create a class.
        gs_assignment_title: str="Examtool Exam",
        emails: [str] = None,
        blacklist_emails: [str] = None,
        email_mutation_list: {str: str} = {},
        question_numbers: [str] = None,
        blacklist_question_numbers: [str] = None
        ):
        if gs_assignment_title is None:
            gs_assignment_title = "Examtool Exam"
        if not exams:
            raise ValueError("You must specify at least one exam you would like to upload!")

        out = out or "out/export/" + exams[0]

        exam_json, email_to_data_map = self.fetch_and_export_examtool_exam_data(
            exams, 
            out, 
            name_question_id, 
            sid_question_id, 
            emails=emails, 
            email_mutation_list=email_mutation_list
        )

        # Remove blacklisted emails
        if blacklist_emails is not None:
            for bemail in blacklist_emails:
                email_to_data_map.pop(bemail, None)

        # Create assignment if one is not already created.
        if gs_assignment_id is None:
            print("Creating the gradescope assignment...")
            outline_path = f"{out}/OUTLINE.pdf"
            gs_assignment_id = self.create_assignment(gs_class_id, gs_assignment_title, outline_path)
            if not gs_assignment_id:
                raise ValueError("Did not receive a valid assignment id. Did assignment creation fail?")
            print(f"Created gradescope assignment with id {gs_assignment_id}!")
        else:
            print(f"Using assignment ({gs_assignment_id}) which was already created!")

        # Lets now get the assignment grader
        grader: GS_assignment_Grader = self.get_assignment_grader(gs_class_id, gs_assignment_id)
        
        # Now that we have the assignment and outline pdf, lets generate the outline.
        print("Generating the examtool outline...")
        examtool_outline = ExamtoolOutline(grader, exam_json, [name_question_id, sid_question_id])

        # Finally we need to upload and sync the outline.
        print("Uploading the generated outline...")
        self.upload_outline(grader, examtool_outline)

        # We can now upload the student submission since we have an outline
        print("Uploading student submissions...")
        failed_uploads = self.upload_student_submissions(out, gs_class_id, gs_assignment_id, emails=email_to_data_map.keys())

        # Removing emails which failed to upload
        if failed_uploads:
            print(f"Removing emails which failed to upload. Note: These will NOT be graded! {failed_uploads}")
            for email in failed_uploads:
                email_to_data_map.pop(email)

        # For each question, group, add rubric and grade
        print("Setting the grade type for grouping for each question...")
        gs_outline = examtool_outline.get_gs_outline()
        self.set_group_types(gs_outline)

        # Fetch the student email to question id map
        print("Fetching the student email to submission id's mapping...")
        email_to_question_sub_id = grader.email_to_qids()

        # Check to see which emails may not be in the Gradescope roster and attempt to correct
        self.attempt_fix_unknown_gs_email(email_to_question_sub_id, email_to_data_map, name_question_id=name_question_id, sid_question_id=sid_question_id)

        # Finally we can process each question
        print("Grouping and grading questions...")
        for qid, question in gs_outline.questions_iterator():
            if question_numbers is not None and qid not in question_numbers or blacklist_question_numbers is not None and qid in blacklist_question_numbers:
                print(f"[{qid}]: Skipping!")
                continue
            print(f"[{qid}]: Processing question...")
            try:
                self.process_question(qid, question.get_gs_question(), email_to_data_map, email_to_question_sub_id, name_question_id, sid_question_id)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)

    def add_additional_exams(
        self,
        exams: [str], 
        out: str, 
        name_question_id: str, 
        sid_question_id: str, 
        gs_class_id: str, 
        gs_assignment_id: str,
        emails: [str]=None,
        blacklist_emails: [str] = None,
        email_mutation_list: {str: str} = {},
        question_numbers: [str] = None,
        blacklist_question_numbers: [str] = None
        ):
        """
        If emails is None, we will import the entire exam, if it has emails in it, it will only upload submissions
        from the students in the emails list contained in the exams list. If the student has submissions in multiple exams,
        the tool will warn you and ask which exam you would like to use as the student submission.
        """
        if not exams:
            raise ValueError("You must specify at least one exam you would like to upload!")
        if email_mutation_list is None:
            email_mutation_list = {}

        out = out or "out/export/" + exams[0]

        exam_json, email_to_data_map = self.fetch_and_export_examtool_exam_data(
            exams, 
            out, 
            name_question_id, 
            sid_question_id, 
            emails=emails, 
            email_mutation_list=email_mutation_list
        )

        # Remove blacklisted emails
        if blacklist_emails is not None:
            for bemail in blacklist_emails:
                email_to_data_map.pop(bemail, None)

        
        # Lets now get the assignment grader
        grader: GS_assignment_Grader = self.get_assignment_grader(gs_class_id, gs_assignment_id)

        # Now that we have the assignment and outline pdf, lets generate the outline.
        print("Generating the examtool outline...")
        examtool_outline = ExamtoolOutline(grader, exam_json, [name_question_id, sid_question_id])

        # Merge the outline with the existing one
        outline = grader.get_outline()
        if not outline: 
            raise ValueError("Failed to fetch the existing outline")
        examtool_outline.merge_gs_outline_ids(outline)

        # We can now upload the student submission since we have an outline
        print("Uploading student submissions...")
        failed_uploads = self.upload_student_submissions(out, gs_class_id, gs_assignment_id, emails=email_to_data_map.keys())

        # Removing emails which failed to upload
        if failed_uploads:
            print(f"Removing emails which failed to upload. Note: These will NOT be graded! {failed_uploads}")
            for email in failed_uploads:
                email_to_data_map.pop(email)

        # Fetch the student email to question id map
        print("Fetching the student email to submission id's mapping...")
        email_to_question_sub_id = grader.email_to_qids()

        # Check to see which emails may not be in the Gradescope roster and attempt to correct
        self.attempt_fix_unknown_gs_email(email_to_question_sub_id, email_to_data_map, name_question_id=name_question_id, sid_question_id=sid_question_id)

        # Finally we can process each question
        print("Grouping and grading questions...")
        gs_outline = examtool_outline.get_gs_outline()
        for qid, question in gs_outline.questions_iterator():
            if question_numbers is not None and qid not in question_numbers or blacklist_question_numbers is not None and qid in blacklist_question_numbers:
                print(f"[{qid}]: Skipping!")
                continue
            print(f"[{qid}]: Processing question...")
            try:
                self.process_question(qid, question.get_gs_question(), email_to_data_map, email_to_question_sub_id, name_question_id, sid_question_id)
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(e)

    
    def fetch_and_export_examtool_exam_data(
        self,
        exams: [str],
        out: str,
        name_question_id: str,
        sid_question_id: str,
        emails: [str] = None,
        email_mutation_list: {str: str} = {}
        ):
        """
        Fetches the submissions from the exams in the exams list.
        If the emails list is None, it will fetch all emails, if it has emails in it, it will only return data for those emails.
        The mutation step occurres after the specific emails selection stage if applicable.
        The mutation list comes in the form of current email to new email.

        Returns:
        exam_json - The json of the exam
        email_to_data_map - the mapping of emails to their data.
        """
        if not exams:
            raise ValueError("You must specify at least one exam you would like to upload!")
        if email_mutation_list is None:
            email_mutation_list = {}

        print("Downloading exams data...")
        exam_json = None
        email_to_data_map = {}
        email_to_exam_map = {}

        first_exam = True
        for exam in exams:
            tmp_exam_json, tmp_template_questions, tmp_email_to_data_map, tmp_total = examtool.api.download.download(exam)
                

            # Choose only the emails we want to keep.
            if emails:
                for email in list(tmp_email_to_data_map.keys()):
                    if email not in emails:
                        tmp_email_to_data_map.pop(email, None)

            # Next, we want to mutate any emails
            for orig_email, new_email in email_mutation_list.items():
                if orig_email not in tmp_email_to_data_map:
                    print(f"WARNING: Could not perform mutation on email {orig_email} (to {new_email}) because it does not exist in the data map!")
                    continue
                if new_email in tmp_email_to_data_map:
                    print(f"Could not mutate email {new_email} (from {orig_email}) as the original email is already in the data map!")
                    continue
                tmp_email_to_data_map[new_email] = tmp_email_to_data_map.pop(orig_email)
            
            # Finally, we should merge together the student responses.
            for email, data in tmp_email_to_data_map.items():
                if email in email_to_data_map:
                    print(f"WARNING: Student with email {email} submitted to multiple exams!")
                    def prompt_q():
                        input_data = None
                        while not input_data:
                            print(f"Student's current responses are from {email_to_exam_map[email]}, would you like to use {exam} instead?")
                            input_data = input("[y/n]> ")
                            if input_data.lower() in ["y", "yes"]:
                                return True
                            if input_data.lower() in ["n", "no"]:
                                return False
                            print("Please type yes or no!")
                    if not prompt_q():
                        continue
                email_to_exam_map[email] = exam
                email_to_data_map[email] = data
            print(f"[{exam}]: Exporting exam pdfs...")
            self.export_exam(tmp_template_questions, tmp_email_to_data_map, tmp_total, exam, out, name_question_id, sid_question_id, include_outline=first_exam)

            # Set global data for the examtool
            if first_exam:
                first_exam = False
                exam_json = tmp_exam_json

        # Lets finally clean up the student responses
        self.cleanse_student_response_data(email_to_data_map)

        return exam_json, email_to_data_map

    def attempt_fix_unknown_gs_email(self, email_to_question_sub_id, email_to_data_map, name_question_id, sid_question_id):
        def prompt_fix(old_email, name, sid):
            input_data = None
            while not input_data:
                print(f"Could not find {old_email} (name: {name}; sid: {sid}) in Gradescope! Please enter the Gradescope email of the student or `skip` to remove this student from autograding.")
                input_data = input("> ")
                if "@" in input_data.lower():
                    return input_data
                if input_data.lower() in ["n", "no", "skip"]:
                    return False
                print("The input is not a valid email (you are missing the `@`)! If you would like to skip, type `skip` or `no`.")
        remove_email = ["DUMMY"]
        map_email = {}
        while remove_email or map_email:
            remove_email = []
            map_email = {}
            for email, data in email_to_data_map.items():
                if email not in email_to_question_sub_id:
                    responses = data["responses"]
                    name = responses.get(name_question_id, None)
                    sid = responses.get(sid_question_id, None)
                    new_email = prompt_fix(email, name, sid)
                    if new_email:
                        map_email[email] = new_email
                    else:
                        print(f"Skipping {email}! This will remove the email from the data map.")
                        remove_email.append(email)
            for email, new_email in map_email.items():
                email_to_data_map[new_email] = email_to_data_map.pop(email)
            for email in remove_email:
                email_to_data_map.pop(email)


    def cleanse_student_response_data(self, email_to_data_map: dict):
        for email, data in email_to_data_map.items():
            std_questions = data["student_questions"]
            std_responses = data["responses"]
            for question in std_questions:
                qid = question["id"]
                if qid not in std_responses:
                    std_responses[qid] = [] if question["type"] in ["multiple_choice", "select_all"] else ""
            


    def export_exam(self, template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id, include_outline=True):
        examtool.api.download.export(template_questions, email_to_data_map, total, exam, out, name_question_id, sid_question_id, include_outline=include_outline)

    def create_assignment(self, gs_class_id: str, gs_title: str, outline_path: str):
        assignment_id = self.gs_client.create_exam(gs_class_id, gs_title, outline_path)
        if not assignment_id:
            print("Failed to create the exam! Make sure it has a unique title.")
            return
        return assignment_id

    def get_assignment_grader(self, gs_class_id: str, assignment_id: str) -> GS_assignment_Grader:
        return self.gs_client.get_assignment_grader(gs_class_id, assignment_id)

    def upload_outline(self, grader: GS_assignment_Grader, examtool_outline: "ExamtoolOutline"):
        outline = grader.update_outline(examtool_outline.get_gs_outline())
        if not outline:
            raise ValueError("Failed to upload or get the outline")
        examtool_outline.merge_gs_outline_ids(outline)

    def upload_student_submissions(self, out: str, gs_class_id: str, assignment_id: str, emails: [str] = None):
        failed_emails = []
        email_files = []
        for file_name in os.listdir(out):
            if "@" not in file_name:
                continue
            student_email = file_name[:-4]
            if emails and student_email not in emails:
                continue
            email_files.append((file_name, student_email))
        for i, (file_name, student_email) in enumerate(email_files):
            print(f"Uploading {i + 1} / {len(email_files)}", end="\r")
            if not self.gs_api_client.upload_submission(gs_class_id, assignment_id, student_email, os.path.join(out, file_name)):
                failed_emails.append(student_email)
        return failed_emails

    def set_group_types(self, outline: GS_Outline, debug=True):
        questions = list(outline.questions_iterator())
        qlen = len(questions)
        for i, (qid, question) in enumerate(questions):
            print(f"Setting group type {i + 1} / {qlen}", end="\r")
            self.set_group_type(question)
    
    def set_group_type(self, o_question: GS_Outline_Question):
        question_type = o_question.data.get("type")
        q = o_question.get_gs_question()
        q_type = GroupTypes.complex
        if question_type in ["select_all", "multiple_choice"]:
            q_type = GroupTypes.mc
        # if question_type in ["long_answer", "long_code_answer"]:
        #     q_type = GroupTypes.non_grouped
        return q.set_group_type(q_type)
    
    def process_question(
        self, 
        qid: str, 
        question: GS_Question, 
        email_to_data_map: dict, 
        email_to_question_sub_id_map: dict, 
        name_question_id: str, 
        sid_question_id: str
        ):
        # Group questions
        if question.data.get("id") in [name_question_id, sid_question_id]:
            print("Skipping grouping of an id question!")
            return
        print(f"Grouping...")
        groups = self.group_question(qid, question, email_to_data_map, email_to_question_sub_id_map)
        if groups:
            # Group answers
            print(f"Syncing groups on gradescope...")
            self.sync_groups_on_gradescope(qid, question, groups)
            print(f"Syncing rubric items...")
            rubric = self.sync_rubric(qid, question, groups)
            # in here, add check to see if qid is equal to either name or sid q id so we do not group those.
            print(f"Applying grades for each group...")
            self.grade_question(question, rubric, groups)
        else:
            print(f"Failed to group question {qid}!")
    
    def group_question(self, qid: str, question: GS_Question, email_to_data_map: dict, email_to_question_sub_id_map: dict):
        qtype = question.data.get("type")
        if qtype == "multiple_choice":
            return self.group_mc_question(qid, question, email_to_data_map, email_to_question_sub_id_map)
        elif qtype == "select_all":
            return self.group_sel_all_question(qid, question, email_to_data_map, email_to_question_sub_id_map)
        elif qtype in ["short_answer", "short_code_answer"]:
            return self.group_short_ans_question(qid, question, email_to_data_map, email_to_question_sub_id_map)
        elif qtype in ["long_answer", "long_code_answer"]:
            return self.group_long_ans_question(qid, question, email_to_data_map, email_to_question_sub_id_map)
        else:
            print(f"Unsupported question type {qtype} for question {question.data}!")
            return None


    def group_mc_question(self, qid: str, question: GS_Question, email_to_data_map: dict, email_to_question_sub_id_map: dict):
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        correct_seq = []
        seq_name = []
        solution_options = data.get("solution", {})
        if solution_options is not None:
            solution_options = solution_options.get("options", [])
        if solution_options is None:
            solution_options = []
        all_options = [option.get("text") for option in data.get("options", [])]
        for option in all_options:
            correct_seq.append(option in solution_options)
            seq_name.append(option)

        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        g_data = {}
        groups = {
            "correct_seq": correct_seq,
            "seq_names": seq_name,
            # groups is a dict of tuples where index:
            # key is the name of the group
            # "sids" is the list of submission id's which selected that
            # "sel_seq" is the selected sequence (list of true false for selected)
            "groups": g_data,
        }

        def list_to_str(l):
            s = ""
            for item in l:
                s += str(int(item))
            return s

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            selection = [False] * len(correct_seq)
            if response is None:
                selection[-1] = True
            elif response == []:
                selection[-2] = True
            else:
                for i, option in enumerate(all_options):
                    selection[i] = option == response

            s = list_to_str(selection)
            sid = email_to_question_sub_id_map[email][qid]
            if s not in g_data:
                g_data[s] = {
                    "sids": [],
                    "sel_seq": selection
                }
            g_data[s]["sids"].append(sid)
        return groups

    def group_sel_all_question(self, qid: str, question: GS_Question, email_to_data_map: dict, email_to_question_sub_id_map: dict):
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        correct_seq = []
        seq_name = []
        solution_options = data.get("solution", {})
        if solution_options is not None:
            solution_options = solution_options.get("options", [])
        if solution_options is None:
            solution_options = []
        all_options = [option.get("text") for option in data.get("options", [])]
        for option in all_options:
            correct_seq.append(option in solution_options)
            seq_name.append(option)

        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        g_data = {}
        groups = {
            "correct_seq": correct_seq,
            "seq_names": seq_name,
            # groups is a dict of tuples where index:
            # key is the name of the group
            # "sids" is the list of submission id's which selected that
            # "sel_seq" is the selected sequence (list of true false for selected)
            "groups": g_data,
        }

        def list_to_str(l):
            s = ""
            for item in l:
                s += str(int(item))
            return s

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            selection = [False] * len(correct_seq)
            if response is None:
                selection[-1] = True
            elif response == []:
                selection[-2] = True
            else:
                for i, option in enumerate(all_options):
                    selection[i] = option in response

            s = list_to_str(selection)
            sid = email_to_question_sub_id_map[email][qid]
            if s not in g_data:
                g_data[s] = {
                    "sids": [],
                    "sel_seq": selection
                }
            g_data[s]["sids"].append(sid)
        return groups

    def group_short_ans_question(self, qid: str, question: GS_Question, email_to_data_map: dict, email_to_question_sub_id_map: dict, lower_check: bool=True):
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        solution = data.get("solution", {})
        if solution is not None:
            solution = solution.get("solution", {})
            if solution is not None:
                solution = solution.get("text")
        if not solution:
            print(f"[{qid}]: No solution defined for this question! Only grouping blank and std did not receive.")
            solution = "Correct"
        correct_seq = [True]
        seq_name = [solution]

        # Add a wrong option
        correct_seq.append(None)
        seq_name.append("Incorrect")
        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        g_data = {}
        groups = {
            "correct_seq": correct_seq,
            "seq_names": seq_name,
            # groups is a dict of tuples where index:
            # key is the name of the group
            # "sids" is the list of submission id's which selected that
            # "sel_seq" is the selected sequence (list of true false for selected)
            "groups": g_data,
        }

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            selection = [False] * len(correct_seq)
            if response is None:
                selection[-1] = True
                response = "Student did not receive this question"
            elif response == "":
                selection[-2] = True
                response = "Blank"
            else:
                if solution is not None:
                    same = None
                    if lower_check:
                        same = response.lower().strip() == solution.lower().strip()
                    else:
                        same = response.strip() == solution.strip()
                    if same:
                        selection[0] = True
                    else:
                        selection[1] = True

            sid = email_to_question_sub_id_map[email][qid]
            if response not in g_data:
                g_data[response] = {
                    "sids": [],
                    "sel_seq": selection
                }
            g_data[response]["sids"].append(sid)
        return groups

    def group_long_ans_question(self, qid: str, question: GS_Question, email_to_data_map: dict, email_to_question_sub_id_map: dict):
        """
        We will only be grouping students who did not get the question or left it blank.
        """
        data = question.data
        # This is a list of correct options from left (top) to right (bottom)
        correct_seq = [True]
        seq_name = ["Correct"]

        # Add blank option
        correct_seq.append(None)
        seq_name.append("Blank")
        # Add student did not receive this question
        correct_seq.append(None)
        seq_name.append("Student did not receive this question")

        g_data = {
            "Blank": {
                "sids": [],
                "sel_seq": [False, True, False],
            },
            "Student did not receive this question": {
                "sids": [],
                "sel_seq": [False, False, True]
            },
        }
        groups = {
            "correct_seq": correct_seq,
            "seq_names": seq_name,
            # groups is a dict of tuples where index:
            # key is the name of the group
            # "sids" is the list of submission id's which selected that
            # "sel_seq" is the selected sequence (list of true false for selected)
            "groups": g_data,
        }

        eqid = question.data["id"]
        for email, data in email_to_data_map.items():
            responses = data.get("responses", {})
            response = responses.get(eqid)
            if not response:
                sid = email_to_question_sub_id_map[email][qid]
                if response is None:
                    g_data["Student did not receive this question"]["sids"].append(sid)            
                elif response == "":
                    g_data["Blank"]["sids"].append(sid)
        return groups

    def sync_groups_on_gradescope(self, qid: str, question: GS_Question, groups: dict):
        """
        Groups is a list of name, submission_id, selected answers
        """
        failed_groups_names = []
        i = 1
        failed = False
        while not question.is_grouping_ready():
            timeout = 5
            print(f"[{qid}]: Question grouping not ready! Retrying in {timeout} seconds" + (" " * timeout), end="\r")
            for i in range (timeout):
                print(f"[{qid}]: Question grouping not ready! Retrying in {timeout} seconds" + ("." * (1 + i)), end="\r")
                time.sleep(1)
            failed = True
        if failed:
            print("")
        gradescope_groups = question.get_groups()
        gdata = groups["groups"]
        def all_zeros(s: str):
            return s and all(v=='0' for v in s)
        def set_group(g_name, data, gs_group):
            data["id"] = gs_group.get("id")
        for g_name, data in gdata.items():
            for gs_group in gradescope_groups:
                if gs_group["question_type"] == "mc":
                    # The question type is mc so lets group by the internal mc
                    if g_name == "Blank":
                        # This is the blank group, lets use the internal label to group
                        if all_zeros(gs_group["internal_title"]):
                            set_group(g_name, data, gs_group)
                    else:
                        flip_g_name = g_name[:-2][::-1]
                        if gs_group["internal_title"] is not None:
                            if flip_g_name == gs_group["internal_title"] and g_name[len(g_name) - 1] != "1":
                                set_group(g_name, data, gs_group)
                        else:
                            if g_name == gs_group["title"]:
                                set_group(g_name, data, gs_group)
                else:
                    # The question type is not mc so we should group on title and internal title for blank.
                    # The internal title should only say Blank for default blank grouped submissions.
                    # We then check the normal title if this is not true
                    if g_name == gs_group["internal_title"] or g_name == gs_group["title"]:
                        set_group(g_name, data, gs_group)

        max_attempts = 5
        attempt = 1
        for i, (g_name, data) in enumerate(gdata.items()):
            print(f"Syncing group {i + 1} / {len(gdata.items())}", end="\r")
            sids = data["sids"]
            if not sids:
                # We do not want to create groups which no questions exist.
                continue
            group_id = data.get("id", None)
            while attempt < max_attempts:
                if not group_id:
                    group_id = question.add_group(g_name)
                if group_id is None:
                    attempt += 1
                    time.sleep(1)
                    continue
                if not question.group_submissions(group_id, sids):
                    print(f"[{qid}]: Failed to group submissions to {group_id}. SIDS: {sids}")
                    failed_groups_names.append(g_name)
                break
            else:
                print(f"Failed to create group for {g_name}! ({groups})")
                failed_groups_names.append(g_name)
        
        # This is to decrease down stream errors
        for failed_group_name in failed_groups_names:
            gdata.pop(failed_group_name, None)
    
    def sync_rubric(self, qid: str, question: GS_Question, groups: dict) -> QuestionRubric:
        rubric = QuestionRubric(question)
        seq_names = groups["seq_names"]
        correct_seq = groups["correct_seq"]
        if len(seq_names) == 0:
            return rubric
        rubric_scores = self.get_rubric_scores(question, seq_names, correct_seq)
        if len(rubric) == 1:
            default_rubric_item = rubric.get_rubric_items()[0]
            if default_rubric_item.description == "Correct":
                if not rubric.update_rubric_item(default_rubric_item, description=seq_names[0]):
                    print(f"[{qid}]: Failed to update default \"Correct\" rubric item!")
        existing_rubric_items = rubric.get_rubric_items()
        for i, (name, score) in enumerate(zip(seq_names, rubric_scores)):
            print(f"Syncing rubric {i + 1} / {len(seq_names)}", end="\r")
            for existing_rubric_item in existing_rubric_items:
                if existing_rubric_item.description == name:
                    if float(existing_rubric_item.weight) != score:
                        rubric.update_rubric_item(existing_rubric_item, weight=score)
                    break
            else:
                rubric_item = RubricItem(description=name, weight=score)
                rubric.add_rubric_item(rubric_item)

        return rubric

    def get_rubric_scores(self,question: GS_Question, seq_names: [str], correct_seq: [bool]):
        qtype = question.data.get("type")
        if qtype == "multiple_choice":
            return self.get_mc_rubric_scores(question, seq_names, correct_seq)
        elif qtype == "select_all":
            return self.get_sel_all_rubric_scores(question, seq_names, correct_seq)
        elif qtype in ["short_answer", "short_code_answer"]:
            return self.get_short_ans_rubric_scores(question, seq_names, correct_seq)
        elif qtype in ["long_answer", "long_code_answer"]:
            return self.get_long_ans_rubric_scores(question, seq_names, correct_seq)
        else:
            print(f"Unsupported question type {qtype} for question {question.data}!")
            return None

    def get_mc_rubric_scores(self, question: GS_Question, group_names, correct_seq):
        scores = []
        num_correct = sum([1 for correct in correct_seq if correct])
        num_choices = sum([1 for correct in correct_seq if correct is not None])
        points = question.data.get("points", 1)
        if points is None:
            points = 1
        rubric_weight = 0
        if num_correct != 0:
            rubric_weight = (1 / num_correct) * points
        for correct in correct_seq:
            if correct is None:
                scores.append(0)
            else:
                if correct:
                    scores.append(rubric_weight)
                else:
                    scores.append(-rubric_weight)
        return scores


    def get_sel_all_rubric_scores(self, question: GS_Question, group_names, correct_seq):
        return self.get_mc_rubric_scores(question, group_names, correct_seq)

    def get_short_ans_rubric_scores(self, question: GS_Question, group_names, correct_seq):
        return self.get_mc_rubric_scores(question, group_names, correct_seq)

    def get_long_ans_rubric_scores(self, question: GS_Question, group_names, correct_seq):
        return [0] * len(correct_seq)

    def grade_question(self, question: GS_Question, rubric: QuestionRubric, groups: dict):
        question_data = question.get_question_info()
        sub_id_mapping = {str(sub["id"]): sub for sub in question_data["submissions"]}
        glen = len(groups["groups"].items())
        for i, (group_name, group_data) in enumerate(groups["groups"].items()):
            print(f"Grading {i + 1} / {glen}", end="\r")
            group_sel = group_data["sel_seq"]
            group_sids = group_data["sids"]
            if len(group_sids) > 0:
                sid = group_sids[0]
                if not sub_id_mapping[str(sid)]["graded"]:
                    if not rubric.grade(sid, group_sel, save_group=True):
                        print(f"Failed to grade group {group_name}!")



class ExamtoolOutline:
    name_region = GS_Crop_info(1, 2.4, 11.4, 100, 18.8)
    sid_region = GS_Crop_info(1, 2.4, 18.9, 100, 28.7)

    def __init__(self, grader: GS_assignment_Grader, exam_json: dict, id_question_ids: [str]):
        self.exam_json = exam_json
        self.gs_number_to_exam_q, self.gs_outline = self.generate_gs_outline(grader, exam_json, id_question_ids)

    def get_gs_crop_info(self, page, question=None):
        return GS_Crop_info(page, 2, 2, 98, 98)

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

    def generate_gs_outline(self, grader: GS_assignment_Grader, exam_json: dict, id_question_ids: [str]):
        gs_number_to_exam_q = {}
        questions = []

        page = 2 # Page 1 is an info page
        
        qid = 1
        if exam_json.get("public"):
            prev_page = 1
            pg = GS_Outline_Question(grader, None, [self.get_gs_crop_info(page, exam_json.get("public"))], title="Public", weight=0)
            sqid = 1
            for question in extract_public(exam_json):
                question_id = question.get("id")
                if question_id in id_question_ids:
                    print(f"Skipping {question_id} as it is an id question.")
                    page += 1 # Still need to increment this as it is still on the exam pdf.
                    continue
                pg.add_child(self.question_to_gso_question(grader, page, question))
                gs_number_to_exam_q[f"{qid}.{sqid}"] = question
                sqid += 1
                page += 1
            if page != prev_page and len(pg.children) > 0:
                questions.append(pg)
                qid += 1
        
        for group in extract_groups(exam_json):
            prev_page = page
            weight = group.get("points", "0")
            if not weight:
                weight = 0
            g = GS_Outline_Question(grader, None, [self.get_gs_crop_info(page, group)], title=group.get("name", ""), weight=weight)
            sqid = 1
            for question in extract_questions(group, extract_public_bool=False, top_level=False):
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
            q.data = self.gs_number_to_exam_q[qnum]
    
    def questions_iterator(self):
        yield from self.gs_outline.questions_iterator()
