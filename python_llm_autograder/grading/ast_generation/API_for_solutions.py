from openai import OpenAI
import os
import json
from dotenv import load_dotenv
# from Upload_question import new_question
# from Upload_rubrics import *
load_dotenv()
# Initialize the OpenAI client
client = OpenAI(
    organization=os.getenv('OPENAI_ORG_ID'),
    project=os.getenv('OPENAI_PROJECT_ID'),
    api_key=os.getenv('OPENAI_API_KEY')
)

# Function to read the model solution from a file
def read_file(file_path):
    with open(file_path, 'r+') as file:
        f = file.read()
        return f

# Load the sample model solution (Python code to be evaluated)
# model_solution = read_file('C:/Users/Andrew/OneDrive - Singapore Management University/SMU stuff/4.1/FYP/35_Equinox_Python_Autograder/Template files for AST generation/Upload_model_solution.py')

# # Sample question and rubrics for the task
# question = new_question
# rubrics = new_rubrics
# added_rubrics = output_rubrics

# Function to call the OpenAI API and generate 8 model solutions
def generate_model_solutions(question, rubrics, model_solution, added_rubrics=""):
    # Create the prompt for GPT-4.0 to generate 5 different model solutions
    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert Python code generator that creates different solutions for a given problem."},
            {"role": "user", "content": f"Here is the question: {question}.\n"
                                        f"The rubrics are: {rubrics} and {added_rubrics}.\n"
                                        f"A sample model solution is: {model_solution}.\n"
                                        f"Please generate 8 different valid solutions that follow the rubrics."},
            {"role": "user", "content": f"""Each solution should:
            1. Be valid and correct according to the question.
            2. Follow the rubrics provided.
            3. Use a mix of for loops and list comprehension ONLY and other valid Python constructs like lists or tuples.
            4. Each solution should be different in its approach but still correct.
            5. Solution can take an input as a string, then make it an integer later on in a separate line.
            Please output exactly 8 Python code solutions.
            In the .py file, only output the Python code that can be directly executed. 
            No comments or explanations, just executable code.
            """}
        ],
        temperature=1,
        stream=False
    )

    # Extract the response (multiple solutions) from the API
    msg = stream.choices[0].message.content
    return msg

# # Generate the model solutions using the OpenAI API
# model_solutions = generate_model_solutions(question, rubrics, added_rubrics, model_solution)

# # Clean up the model solutions (remove any markdown-like block quotes)
# model_solutions_cleaned = model_solutions.replace('```python', '').replace('```', '').strip()

# # Get the current working directory of this script
# current_folder = os.path.dirname(os.path.abspath(__file__))

# # Write the model solutions to a file in the same folder as the API script
# output_file_path = os.path.join(current_folder, "generated_model_solutions.py")
# with open(output_file_path, "w+") as f:
#     f.write(model_solutions_cleaned)
#     print(f"Model solutions written to {output_file_path}.")

