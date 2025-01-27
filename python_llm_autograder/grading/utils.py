import zipfile
import tempfile
import subprocess
import os
import sys
import signal
import psutil
from django.core.files.storage import default_storage
from grading.best_practises import chatGPT
import pandas as pd
from grading.best_practises import built_in_func_def


def get_file_content(file_field, encoding='utf-8'):
    """
    Reads the content of a file from a FileField.

    Args:
        file_field: The FileField instance from which to read the file.
        encoding: The encoding used to decode the file content.

    Returns:
        A tuple containing:
        - file_content (str): The content of the file as a string.
        - error_message (str): An error message if an exception occurs; otherwise, None.
    """
    if not file_field:
        return '', 'No file available'

    try:
        # Use the storage system to open the file
        with default_storage.open(file_field.name, 'rb+') as f:
            file_content_bytes = f.read()
            # Decode the content using the specified encoding
            file_content = file_content_bytes.decode(encoding)
        return (file_content, '')
    except Exception as e:
        error_message = f'Error reading file: {str(e)}'
        return ('', error_message)
    
def get_1_file_content(file_field, encoding='utf-8'):
    """
    Reads the content of a file from a FileField.

    Args:
        file_field: The FileField instance from which to read the file.
        encoding: The encoding used to decode the file content.

    Returns:
        A tuple containing:
        - file_content (str): The content of the file as a string.
        - error_message (str): An error message if an exception occurs; otherwise, None.
    """
    if not file_field:
        return '', 'No file available'

    try:
        # Use the storage system to open the file
        with open(file_field, 'rb+') as f:
            file_content_bytes = f.read()
            # Decode the content using the specified encoding
            file_content = file_content_bytes.decode(encoding)
        return (file_content, '')
    except Exception as e:
        error_message = f'Error reading file: {str(e)}'
        return ('', error_message)


def get_python_file_paths(zip_file_path):
    python_file_paths = []
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_file_paths.append(file_path)
    return python_file_paths, temp_dir

# def terminate_process(process):
#     if sys.platform.startswith('win'):
#         process.send_signal(signal.CTRL_BREAK_EVENT)
#     else:
#         os.killpg(os.getpgid(process.pid), signal.SIGTERM)

# def execute_student_code(file_path, user_inputs):
#     try:
#         # Use subprocess.run with resource limits
#         result = subprocess.run(
#             ["python", file_path],
#             input=user_inputs,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             timeout=20,  # Set a timeout
#             # preexec_fn=lambda: os.setsid()  # Start a new session
#         )
#         output = result.stdout.strip()
#         error = result.stderr.strip()
#     except subprocess.TimeoutExpired:
#         result.kill()
#         result.wait()
#         output = ''
#         error = 'Execution timed out.'
#     except Exception as e:
#         output = ''
#         error = f'An error occurred: {e}'
#     return output, error

import sys
import subprocess
import psutil  # Ensure psutil is imported
import signal

def terminate_process(process):
    """
    Terminate a subprocess and all its child processes.
    
    Args:
        process (subprocess.Popen): The subprocess to terminate.
    """
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        parent.terminate()
        gone, still_alive = psutil.wait_procs(children + [parent], timeout=3)
        for p in still_alive:
            p.kill()
    except psutil.NoSuchProcess:
        pass  # Process already terminated
    except Exception as e:
        print(f"Error terminating process: {e}")

def execute_student_code(file_path, user_inputs):
    """
    Execute a Python script with user inputs and handle timeouts and errors.
    
    Args:
        file_path (str): The path to the Python script to execute.
        user_inputs (str): The input to pass to the script.
    
    Returns:
        tuple: (output, error)
    """
    try:
        if sys.platform.startswith('win'):
            # Windows: Create a new process group
            process = subprocess.Popen(
                ["python", file_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix-like: Start the process in a new session
            process = subprocess.Popen(
                ["python", file_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid
            )
        
        try:
            # Communicate with the subprocess
            output, error = process.communicate(input=user_inputs, timeout=20)
            output = output.strip()
            print("FROM UTILS.PY:", output, "#####################")
            error = error.strip()
        except subprocess.TimeoutExpired:
            # Timeout: Terminate the process and its children
            terminate_process(process)
            output = ''
            error = 'Execution timed out.'
    except Exception as e:
        output = ''
        error = f'An error occurred: {e}'
        return output, error
    
    return output, error


def warm_up_gpt(model_code, sample_code,limit=2):

    for i in range(limit):
        chatGPT.check_redundancy(model_code,sample_code)
    
    print(f"Ran code {limit} times on model")

def add_severity_marks_redundant_code(code):
    mapping = {
        'Faulty Conditional Statements': 'LOGIC002',
        'Inefficient Algorithm': 'PERF001',
        'High Memory Usage': 'PERF003'
    }

    unique_codes = set()
    total_marks = 0

    for item in code['redundant_code']:
        rubric_code = mapping.get(item['redundant_code_topic'])
        if rubric_code:
            severity = built_in_func_def.get_severity(rubric_code)
            marks = built_in_func_def.get_marks(rubric_code)
            item['Severity'] = severity
            item['Marks'] = marks

            if rubric_code not in unique_codes:
                unique_codes.add(rubric_code)
                total_marks += marks

    # Add the total marks as a separate item
    code['total_marks_deducted'] = total_marks
    return code

def convert_best_practice_to_df(data):
    rubric_codes = []
    lines = []
    messages = []
    marks = []  
    severity = []

    for file, rubrics in data.items():
        for rubric_code, details in rubrics.items():
            mark = built_in_func_def.get_marks(rubric_code)
            sev = built_in_func_def.get_severity(rubric_code)
            for detail in details:
                rubric_codes.append(rubric_code)
                lines.append(detail['line'])
                messages.append(detail['message'])
                marks.append(mark)
                severity.append(sev)  

    df = pd.DataFrame({
        'rubric_code': rubric_codes,
        'line': lines,
        'message': messages,
        'marks': marks,
        'severity': severity
    })

    result_dict = df.to_dict(orient='records')

    unique_rubric_codes = set(rubric_codes)
    total_marks_per_rubric_code = sum(built_in_func_def.get_marks(code) for code in unique_rubric_codes)

    result = {
        'best_practice_result': result_dict,
        'total_marks_deducted': total_marks_per_rubric_code
    }
    return result


def calculate_suggested_score(test_cases_passed,test_cases_total,partial_mark,total_partial_mark_score,overall_score):
    # # from the autograder
    # # test_cases_passed = 2
    # # test_cases_total= 4
    # # from the autograder
    # #partial_mark = 3 # student only got 3 marks for partial
    # # calculated
    # proportion_of_passed_test_cases = test_cases_passed / test_cases_total
    # test_case_score = test_cases_total if proportion_of_passed_test_cases == 1 else 0
    # # if all test cases pass, test case score is the input from Terence, otherwise 0
    # # if proportion_of_passed_test_cases == 1:
    # #     test_case_score = actual_score     # in this scenario, student got 0 for test case score
    final_suggested_score = 0
    needs_manual_review = False

    # if test_case_score == 0:
    #     final_suggested_score = partial_mark # if 1 test case fail, assign partial marks as suggested. Thus student gets 3 marks.
    # if proportion_of_passed_test_cases == 1:
    #     if partial_mark < total_partial_mark_score:
    #         needs_manual_review = True
    #         final_suggested_score = partial_mark
    #     else:
    #         final_suggested_score = test_case_score
    proportion_of_passed_test_cases = test_cases_passed / test_cases_total

    if proportion_of_passed_test_cases == 1:
        if partial_mark == total_partial_mark_score:
            final_suggested_score = overall_score
            needs_manual_review = False
        else:
            if (partial_mark < total_partial_mark_score):
                final_suggested_score = partial_mark
                needs_manual_review = True
    else:
        if partial_mark == total_partial_mark_score:
            final_suggested_score = total_partial_mark_score
            needs_manual_review = True
        elif partial_mark < total_partial_mark_score:
            final_suggested_score = partial_mark
            needs_manual_review = False
            
    return (final_suggested_score, needs_manual_review)