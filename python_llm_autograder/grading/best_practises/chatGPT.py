from openai import OpenAI
import pprint
import os
import json
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    organization=os.getenv('OPENAI_ORG_ID'),
    project=os.getenv('OPENAI_PROJECT_ID'),
    api_key=os.getenv('OPENAI_API_KEY')    
)

class Code(BaseModel):
    line_number: int
    code: str

class Step(BaseModel):
    redundant_code_topic: str
    summary: str
    redundant_code_line_number: list[Code]

class Summary(BaseModel):
    redundant_code: list[Step]


def check_redundancy(model_code, student_code):
    # json_format = {"redundant_code_topic": {
    #     "summary": "Repeated addition of weighted_sum for 'T' and 'G'.",
    #     "code_line_number": [
    #             {'26':'code',
    #             '28':'code'}
    #         ]
    #     }
    # }
    rubric_category = ["Faulty Conditional Statements","Inefficient Algorithm","High Memory Usage"]
    system_message = (
    f"You are a coding tutor helping beginner Python students. "
    f"The model code provided is the perfect solution. If student code is the same as model code. Dont give any feedback. "
    f"Please compare it with the student's code to identify any major redundant or inefficient code "
    f"based on these categories: {rubric_category}. "
    f"Be lenient and supportive in your feedback, focusing on key learning points."
    f"Provide the issues in JSON format as follows:\n")
    #f'{{"issues": [{{"summary": "Issue summary.", "code_line_number": [line_numbers]}}]}}\n'
    #f"Only output the JSON without additional explanations."
    

    completion =  client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Model Code:\n\n{model_code}"},
            {"role": "user", "content": f"Student Code:\n\n{student_code}"}
        ],
        temperature=0.5,
        response_format=Summary,
        #seed = None
    )
    msg = completion.choices[0].message.parsed
    return msg.dict()
    #return msg[7:-3
