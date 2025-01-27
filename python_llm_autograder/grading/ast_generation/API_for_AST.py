from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# from Upload_question import new_question
# from Upload_rubrics import *
# from edge_cases import *
load_dotenv()
# Initialize the OpenAI client
client = OpenAI(
    organization=os.getenv('OPENAI_ORG_ID'),
    project=os.getenv('OPENAI_PROJECT_ID'),
    api_key=os.getenv('OPENAI_API_KEY')
    
)

# # Function to read the model solution from a file
# def read_file(file_path):
#     with open(file_path, 'r+') as file: 
#         f = file.read()
#         return f

# # Load the model solutions (Python code to be evaluated)
# model_code = read_file('C:/Users/Andrew/OneDrive - Singapore Management University/SMU stuff/4.1/FYP/35_Equinox_Python_Autograder/Template files for AST generation/Upload_model_solution.py')
# model_code1 = read_file('C:/Users/Andrew/OneDrive - Singapore Management University/SMU stuff/4.1/FYP/35_Equinox_Python_Autograder/Template files for AST generation/generated_model_solutions.py')

# # Sample question and rubrics for the task
# question = new_question


# Rubrics for grading
# ast_rubrics = new_rubrics
# output_rubrics = output_rubrics
# edge_cases = edge_cases

# Function to call the OpenAI API and generate the AST code for grading
def generate_ast_and_evaluation(model_code, model_code1, question, ast_rubrics,edge_cases="", output_rubrics={}):
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an AST code generator that captures all details in a set of specific rubrics for grading Python assignments of students."},
            {"role": "user", "content": f"You are given the rubrics for AST: {ast_rubrics} and output rubris {output_rubrics} for the question: {question}. Do consider these specific edge cases: {edge_cases}."},
            {"role": "user", "content": f"""Several samples of the perfect solution given: {model_code}{model_code1}. 
             Generate the AST Python code to mark student assignments. The AST generated should award the solutions in
             {model_code} and {model_code1} as full marks. Split the functions into one to evaluate code and one to check output.
            Do not use classes or class-based methods. Only use pure functions for all tasks. 
            Ensure that all code remains function-based and never uses object-oriented constructs.
            In the .py file, only output the Python code that can be directly executed. 
            No comments or explanations, just executable code.
             Do not define more functions than Criteria in {ast_rubrics} and {output_rubrics}.

            Please wrap the functions under an umbrella function evaluate_code_ast(code_submitted, rubrics), like this:"""},
            {"role": "user", "content": """
                
           import ast

def evaluate_code_ast(code, rubric):
    tree = ast.parse(code)
    results = {
        "Criteria": rubric["Criteria"],
        "Marks": [0] * len(rubric["Marks"]),
        "Description": rubric["Description"],
        "Total": 0
    }

    variable_assignments = {}

    def is_definitely_non_iterable(node):
        # Returns True if the node is known to be non-iterable
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ('int', 'float'):
                    return True
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name in variable_assignments:
                return is_definitely_non_iterable(variable_assignments[var_name])
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return True
        return False

    def is_variable_defined(name):
        return name in variable_assignments

    def build_variable_assignments():
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variable_assignments[target.id] = node.value

    uses_input = False
    uses_for_loop = False
    correct_for_loop_usage = True
    uses_nested_loop = False
    correct_nested_loop_usage = True

    build_variable_assignments()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'input':
            uses_input = True

    # Check for loops and their correctness
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            # Check if outer loop iterator is incorrect
            if not uses_for_loop:
                uses_for_loop = True
                if is_definitely_non_iterable(node.iter):
                    correct_for_loop_usage = False
                elif isinstance(node.iter, ast.Name) and not is_variable_defined(node.iter.id):
                    correct_for_loop_usage = False

            # Now check all nested loops within this loop
            for inner_node in ast.walk(node):
                if isinstance(inner_node, ast.For) and inner_node != node:
                    uses_nested_loop = True
                    # Check if nested loop iterator is incorrect
                    if is_definitely_non_iterable(inner_node.iter):
                        correct_nested_loop_usage = False
                    elif isinstance(inner_node.iter, ast.Name) and not is_variable_defined(inner_node.iter.id):
                        correct_nested_loop_usage = False

    # Assign marks based on criteria
    if uses_input:
        results["Marks"][0] = rubric["Marks"][0]  # Input Handling

    if uses_for_loop and correct_for_loop_usage:
        results["Marks"][1] = rubric["Marks"][1]  # Use of For-Loop
    else:
        results["Marks"][1] = 0  # Incorrect use of For-Loop

    if uses_nested_loop and correct_nested_loop_usage:
        results["Marks"][2] = rubric["Marks"][2]  # Use of Nested Loop
    else:
        results["Marks"][2] = 0  # Incorrect use of Nested Loop

    results["Total"] = sum(results["Marks"])
    return results

def evaluate_output(submitted_output, expected_output, output_rubric):
    results = {
        "Criteria": output_rubric["Criteria"],
        "Marks": [0] * len(output_rubric["Marks"]),
        "Description": output_rubric["Description"],
        "Total": 0
    }

    submitted_lines = submitted_output.strip().split('\n')
    expected_lines = expected_output.strip().split('\n')

    # Criteria 1: Correct number of rows
    correct_number_of_rows = len(submitted_lines) == len(expected_lines)
    if correct_number_of_rows:
        results["Marks"][0] = output_rubric["Marks"][0]

    # Criteria 2: Correct number of elements per row
    correct_elements_per_row = True
    for s_line, e_line in zip(submitted_lines, expected_lines):
        # Remove whitespace to focus on the elements
        s_line_stripped = s_line.strip()
        e_line_stripped = e_line.strip()
        if len(s_line_stripped) != len(e_line_stripped):
            correct_elements_per_row = False
            break
    if correct_elements_per_row:
        results["Marks"][1] = output_rubric["Marks"][1]

    results["Total"] = sum(results["Marks"])
    return results


                """}
        ],
        temperature=0.1,
        stream=False
    )

    msg = stream.choices[0].message.content
    return msg

# Generate the AST code using the OpenAI API
# ast_code = generate_ast_and_evaluation(model_code, model_code1, question, edge_cases, ast_rubrics, output_rubrics)

# # Clean up the AST code (remove any markdown-like block quotes)
# ast_code_cleaned = ast_code.replace('```python', '').replace('```', '').strip()

# # Get the current working directory of this script
# current_folder = os.path.dirname(os.path.abspath(__file__))

# # Write the cleaned AST code to a file in the same folder as the API script
# output_file_path = os.path.join(current_folder, "ast_generated.py")
# with open(output_file_path, "w+") as f:
#     f.write(ast_code_cleaned)
#     print(f"AST code written to {output_file_path}.")