import json
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib import messages
from .forms import CustomUserCreationForm, QuestionForm, AssignmentForm, ModelSolutionForm, SubmissionUploadForm, CourseGroupSelectionForm, AllModelSolutionForm,ActualScoreForm,DashboardFilterForm
from .models import Lecturer,CourseGroup,Assignment,Question,ModelSolution,SubmissionBatch,StudentSubmission 
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from grading.ast_generation.API_for_solutions import generate_model_solutions
from grading.ast_generation.API_for_AST import generate_ast_and_evaluation
from grading.best_practises.chatGPT import check_redundancy
from grading.best_practises.autograder_linter_func import best_practice_checker
from .utils import get_file_content,get_1_file_content, get_python_file_paths,execute_student_code, warm_up_gpt, add_severity_marks_redundant_code, convert_best_practice_to_df, calculate_suggested_score
import os,subprocess,signal, importlib.util
import shutil
import tempfile
from django.core.files.base import ContentFile
from django.urls import reverse
import plotly
import plotly.express as px
import pandas as pd
# from django_pandas.io import read_frame
# Create your views here.
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

def logout_view(request):
    logout(request)
    return redirect('login')

def home(request):
    return render(request, "grading/home.html")

@login_required
def history(request):
    submission_batches = SubmissionBatch.objects.filter(lecturer=request.user)
    return render(request, 
                "grading/history.html", 
                {"submission_batches": submission_batches})

@login_required
def delete_submission_batch(request, pk):
    submission_batch = get_object_or_404(SubmissionBatch, pk=pk)
    if request.method == 'POST':
        submission_batch.delete()
    return redirect('grading-history')
    #return render(request, 'grading/confirm_delete.html', {'submission_batch': submission_batch})

def dashboard(request):

    course_group_id = request.GET.get("course_group")
    assignment_id = request.GET.get("assignment")
    question_id = request.GET.get("question")
    

    charts = {}
    filter_params = {}
    if all([course_group_id, assignment_id, question_id]):
        submissions = StudentSubmission.objects.filter(
            submission_batch__course_group__class_code=course_group_id,
            submission_batch__assignment__assignment_code=assignment_id,
            submission_batch__question=question_id,
        )
        if submissions.exists():
            data = list(submissions.values())
            students_df = pd.DataFrame(data)
            charts = generate_charts(students_df)
            mean_score = students_df['actual_score'].mean()
            median_score = students_df['actual_score'].median()
            std_dev_score = students_df['actual_score'].std()
            filter_params = {
                'course_group_id': course_group_id,
                'assignment_id': assignment_id,
                'question_id': question_id,
                'mean_score': mean_score,
                'median_score': median_score,
                'std_dev_score': std_dev_score,
                'overall_score' : students_df['overall_score'].mean(),
            }
        else:
            messages.warning(request, "No data available for the selected filters.")

    print("GET is:",request.GET)
    ## triend sending request.GET to pre-populate form but because its dependent select I keep getting validation errors
    form = DashboardFilterForm(request.GET or None,lecturer=request.user)

    context = {
        'form': form,
        'charts': charts,
        'filter_params' : filter_params
    }
    return render(request, "grading/dashboard.html", context)

def generate_charts(students_df):
    charts = {}

    # Ensure 'actual_score' exists
    students_df['actual_score'] = students_df['actual_score'].fillna(0)

    # **Chart 1: Total Marks Distribution**
    total_marks = students_df['actual_score']
    fig1 = px.pie(names=total_marks, title='Distribution of Total Marks')
    charts['marks_distribution'] = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)

    # **Chart 2: Error Topic Distribution**
    error_data = []
    for _, student in students_df.iterrows():
        checker_feedback = student.get('checker_feedback', {}) or {}
        redundant_code_list = checker_feedback.get('redundant_code', [])
        if redundant_code_list:
            for issue in redundant_code_list:
                error_topic = issue.get('redundant_code_topic', 'Unknown Error')
                error_data.append(error_topic)
        else:
            error_data.append('No Errors')
    error_topic_counts = pd.Series(error_data).value_counts().reset_index()
    error_topic_counts.columns = ['Error Topic', 'Count']
    fig2 = px.bar(error_topic_counts, x='Error Topic', y='Count', title='Distribution of Error Topics')
    charts['error_topic_distribution'] = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    # **Chart 3: Test Cases Passed Distribution**
    test_cases_passed = students_df.get('test_cases_passed', pd.Series(dtype=int))
    test_cases_passed = pd.to_numeric(test_cases_passed, errors='coerce').fillna(0).astype(int)
    distribution = test_cases_passed.value_counts().sort_index().reset_index()
    distribution.columns = ['Number of Test Cases Passed', 'Number of Students']
    fig3 = px.bar(distribution, x='Number of Test Cases Passed', y='Number of Students',
                title='Distribution of Number of Test Cases Passed')
    charts['test_cases_distribution'] = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)

    # **Chart 4: Criteria Met Distribution**
    # Similar to previous code, process the criteria met data
    # Assuming 'question_specific_feedback' is in the DataFrame
    criteria_met_data = []
    criteria_set = set()
    for _, student in students_df.iterrows():
        student_criteria = {}
        feedback = student.get('question_specific_feedback', {}) or {}
        criteria_list = feedback.get('Criteria', [])
        if isinstance(criteria_list, list):
            for criterion_info in criteria_list:
                criterion_name = criterion_info.get('Criteria', 'Unknown Criterion')
                mark = criterion_info.get('Marks', 0)
                student_criteria[criterion_name] = float(mark)
                criteria_set.add(criterion_name)
        else:
            # Handle cases where 'Criteria' is not a list
            continue
        criteria_met_data.append(student_criteria)

    # Create a DataFrame from the criteria data
    criteria_df = pd.DataFrame(criteria_met_data)

    # Ensure all criteria are present in the DataFrame
    for criterion in criteria_set:
        if criterion not in criteria_df.columns:
            criteria_df[criterion] = 0.0

    # Count the number of students who met each criterion (mark > 0)
    criteria_counts = (criteria_df > 0).sum().reset_index()
    criteria_counts.columns = ['Criterion', 'Number of Students Met']

    # Generate the bar chart
    fig4 = px.bar(criteria_counts, x='Criterion', y='Number of Students Met',
                  title='Number of Students Who Met Each Criterion')

    # Add the chart to the charts dictionary
    charts['criteria_met_distribution'] = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)

    return charts



@login_required(login_url="/accounts/login")
def create_course_and_assignment(request):
    if request.method == "POST":
        course_group_form = CourseGroupSelectionForm(request.POST)
        assignment_form = AssignmentForm(request.POST)

        if course_group_form.is_valid() and assignment_form.is_valid():
            # Process Course Group
            course_group = course_group_form.cleaned_data.get('course_group')
            new_class_code = course_group_form.cleaned_data.get('new_class_code')
            if new_class_code:
                # Create a new CourseGroup
                course_group = CourseGroup.objects.create(
                    class_code=new_class_code,
                    lecturer=request.user
                )

            # Process Assignment
            assignment_code = assignment_form.cleaned_data['assignment_code']
            assignment, created = Assignment.objects.get_or_create(
                assignment_code = assignment_code
            )
            assignment.course_group.add(course_group)

            messages.success(request, f"Assignment '{assignment.assignment_code}' associated with course group '{course_group.class_code}'.")

            return redirect('assignment-class')
    else:
        course_group_form = CourseGroupSelectionForm(lecturer=request.user)
        assignment_form = AssignmentForm()

    context = {
        "course_group_form": course_group_form,
        "assignment_form": assignment_form,
        "assignments_objects": [assignment.assignment_code for assignment in Assignment.objects.filter(
                course_group__lecturer=request.user
            ).distinct()]
    }
    return render(request, 'grading/assignment_class.html', context)


@login_required
def upload_materials(request):

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES,lecturer=request.user)
        model_solution_form = ModelSolutionForm(request.POST, request.FILES)
        # submission_batch_form = SubmissionBatchForm(request.POST, request.FILES)

        if all([question_form.is_valid(),model_solution_form.is_valid()]):
            # Save Question
            question = question_form.save(commit = False)
            question.qn_code = question_form.cleaned_data['qn_code'].upper()
            question.lecturer = request.user
            question.save()
            

            # Save ModelSolution
            model_solution = model_solution_form.save(commit=False)
            model_solution.question = question
            model_solution.lecturer = request.user
            model_solution.save()

            errors = ""
            qn_file_content, error_message_1 = get_file_content(question.question_file)
            grading_rubric_file_content, error_message_2 = get_file_content(question.grading_rubric)
            model_solution_file_content, error_message_3 = get_file_content(model_solution.model_solution)
            
            errors += error_message_1 + '\n' + error_message_2 + '\n' + error_message_3

            generated_solutions = generate_model_solutions(qn_file_content, grading_rubric_file_content, model_solution_file_content)
            generated_solutions_cleaned = generated_solutions.replace('```python', '').replace('```', '').strip()

            # ast_python_code = generate_ast_and_evaluation(model_solution_file_content, generated_solutions_cleaned, qn_file_content, grading_rubric_file_content)
            
            # ast_python_code_cleaned = ast_python_code.replace('```python', '').replace('```', '').strip()
            # # Write ast_python_code_cleaned to a temporary file
            # with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            #     temp_file.write(ast_python_code_cleaned.encode('utf-8'))
            #     temp_file_path = temp_file.name

            # # Save the temporary file to the FileField
            # with open(temp_file_path, 'rb') as temp_file:
            #     model_solution.ast_python_code.save(f"{question.qn_code}_ast_python_code.py", ContentFile(temp_file.read()))


            model_solution.model_solution_all_solutions = generated_solutions_cleaned
            model_solution.save()
            
            print(errors)
            # if len(errors) != 0:
            #     messages.error(request, errors)
            #     return redirect('question-upload')
            messages.success(request, f"Form uploaded by {request.user}")
            return redirect('model-solution-generator', pk=model_solution.pk)  # Redirect to a success page
    else:
        question_form = QuestionForm(lecturer=request.user)
        model_solution_form = ModelSolutionForm()
        # submission_batch_form = SubmissionBatchForm()

    context = {
        'question_form': question_form,
        'model_solution_form': model_solution_form,
        # 'submission_batch_form': submission_batch_form,
    }
    return render(request, 'grading/question_upload.html', context)
    

###################################################################################################
@login_required
def submission_upload(request):
    if request.method == 'POST':
        form = SubmissionUploadForm(request.POST, request.FILES, lecturer=request.user)
        if form.is_valid():
            submission_batch = form.save(commit=False)
            submission_batch.lecturer = request.user
            submission_batch.save()
            #####################################################################################################################
            # marking solution part happens here
            test_cases_raw, test_case_error = get_file_content(submission_batch.question.test_cases_file)
            try:
                test_cases_json = json.loads(test_cases_raw)
                test_cases = test_cases_json.get('test_cases', [])
            except json.JSONDecodeError as e:
                messages.warning(request, f'Error reading test cases file: {str(e)}')
                submission_batch.delete()
                return redirect('submission-upload')
            # print(test_cases)
            # Get the list of Python file paths
            zip_file_path = submission_batch.student_submissions_zip.path
            python_file_paths, temp_dir = get_python_file_paths(zip_file_path)
            model_solution = ModelSolution.objects.get(question=submission_batch.question).model_solution.path
            # Execute the student code for each Python file
            # print(model_solution)
            # Dynamically import the grading rubric module
            grading_rubric_path = submission_batch.question.grading_rubric.path
            spec = importlib.util.spec_from_file_location("grading_rubric", grading_rubric_path)
            grading_rubric_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(grading_rubric_module)
            # print(grading_rubric_path)
            # Access the new_rubrics from the imported module
            new_rubrics = grading_rubric_module.new_rubrics

            # Dynamically import the ast python code module
            ast_python_solution_path = ModelSolution.objects.get(question=submission_batch.question).ast_python_code.path
            # Dynamically import the AST Python code module
            spec_ast = importlib.util.spec_from_file_location("ast_python_solution", ast_python_solution_path)
            ast_python_solution_module = importlib.util.module_from_spec(spec_ast)
            spec_ast.loader.exec_module(ast_python_solution_module)
            # print(ast_python_solution_path)
            # print(dir(ast_python_solution_module))
            import inspect

            for name in dir(ast_python_solution_module):
                attr = getattr(ast_python_solution_module, name)
                if inspect.isfunction(attr):
                    print(f"\nFunction {name}:\n")
                    print(inspect.getsource(attr))
                        
            gpt_startup = False
            ##################################################################
            for file_path in python_file_paths:
                student = StudentSubmission(
                submission_batch=submission_batch, 
                total_test_cases=len(test_cases),
                test_cases_passed = 0,
                )
                student_code, student_code_error = get_1_file_content(file_path)
                model_code, model_code_error = get_1_file_content(model_solution)
                

                # file_name = os.path.basename(file_path)
                test_cases_feedback = {}
                for i in range(student.total_test_cases):
                    test_cases_feedback[f"Test Case {i+1}"] = {"result": "", "message": ""}

                count = 0
                for test_case in test_cases:
                    user_inputs = test_case.get('input1', '')
                    student_output, student_error = execute_student_code(file_path, user_inputs)
                    model_output, model_error = execute_student_code(model_solution, user_inputs)
                    count += 1
                    print('---------------NEW------------------')
                    print(file_path)
                    print(f"{student_output}")
                    print('-------------------------------------')
                    print(f"{student_error}")
                    print('-------------------------------------')
                    print(f"{model_output}")
                    print('-------------------------------------')
                    print(f"{student_output == model_output}")
                    print('--------------END NEW-------------------')
                    if student_output == model_output:
                        student.test_cases_passed += 1
                        test_cases_feedback[f"Test Case {count}"]["result"] = "Pass"
                        test_cases_feedback[f"Test Case {count}"]["message"] = ""
                    else:
                        test_cases_feedback[f"Test Case {count}"]["result"] = "Failed"
                        test_cases_feedback[f"Test Case {count}"]["message"] = json.dumps({"msg":"Output dosent match",'student_output':student_output,'model_output':model_output,'student_error':student_error})
                student.test_cases_feedback = test_cases_feedback   
                ##########################################################################
                if not gpt_startup:
                    warm_up_gpt(model_output,student_output,2)
                    gpt_startup = True
                
                best_practices_result = best_practice_checker(student_code)
                best_practises_df = convert_best_practice_to_df(best_practices_result)
                best_practices_score = best_practises_df['total_marks_deducted']

                redundant_code_result = check_redundancy(model_code, student_code)
                redundant_code_df = add_severity_marks_redundant_code(redundant_code_result)
                redundant_code_score = redundant_code_df['total_marks_deducted']

                student.best_practices_score = best_practices_score + redundant_code_score
                student.best_practices_feedback = best_practises_df
                student.checker_feedback = redundant_code_df

                #####################################################################
                # Access the evaluate_code_ast function from the imported module
                # print(type(student_code))   
                # print(f"##########################This is student code:{student_code} \n\n################")
                evaluate_code_ast = ast_python_solution_module.evaluate_code_ast(student_code,new_rubrics)
                student.question_specific_feedback = {
                                                        'Total': evaluate_code_ast['Total'],
                                                        'Criteria': [
                                                            {
                                                                'Criteria': criterion,
                                                                'Description': description,
                                                                'Marks': mark,
                                                            }
                                                            for criterion, mark, description in zip(evaluate_code_ast['Criteria'], evaluate_code_ast['Marks'], evaluate_code_ast['Description'])
                                                        ]
                                                    }
                student.question_specific_score = float(evaluate_code_ast['Total'])
                ###############################################################
                student.final_suggested_score,student.needs_manual_review = calculate_suggested_score(student.test_cases_passed,student.total_test_cases,
                                                                student.question_specific_score,new_rubrics["Total"],submission_batch.question.qn_total_score)
                
                student.question_specific_total_score = new_rubrics["Total"]
                student.overall_score = submission_batch.question.qn_total_score
                
                StudentSubmission.objects.create(
                    submission_batch=student.submission_batch,
                    needs_manual_review=student.needs_manual_review,
                    actual_score = student.final_suggested_score,
                    submission_file=student_code,
                    total_test_cases=student.total_test_cases,
                    test_cases_passed=student.test_cases_passed,
                    test_cases_feedback=student.test_cases_feedback,
                    overall_score=student.overall_score,
                    best_practices_score=student.best_practices_score,
                    best_practices_feedback=student.best_practices_feedback,
                    question_specific_score = student.question_specific_score,
                    question_specific_total_score = student.question_specific_total_score,
                    question_specific_feedback=student.question_specific_feedback,
                    final_suggested_score = student.final_suggested_score,
                    checker_feedback=student.checker_feedback
                )
            ###################################################################
            shutil.rmtree(temp_dir)
            messages.success(request, f'Submission batch uploaded successfully.')
            return redirect('submission-upload')
        # else:
        #     return render(request, 'grading/submission_upload.html', {'form': form})
    else:
        form = SubmissionUploadForm(lecturer=request.user)
    return render(request, 'grading/submission_upload.html', {'form': form})

############################################################################################################

@login_required
@require_GET
def load_assignments(request):
    course_group_id = request.GET.get('course_group')
    assignments = Assignment.objects.filter(
        course_group=course_group_id,
    ).distinct()
    assignment_list = list(assignments.values('assignment_code', 'assignment_code'))
    print(assignment_list)
    return JsonResponse({'assignments': assignment_list})

@login_required
@require_GET
def load_questions(request):
    assignment_id = request.GET.get('assignment')
    questions = Question.objects.filter(assignment=assignment_id)
    question_list = list(questions.values('id','qn_code'))
    print(question_list)
    return JsonResponse({'questions': question_list})

@login_required
@require_GET
def load_course_groups(request):
    question_id = request.GET.get('question')
    question = Question.objects.get(pk=question_id)
    all_course_groups = question.assignment.course_group.all()
    course_group_list = list(all_course_groups.values('class_code','class_code'))
    return JsonResponse({'course_groups': course_group_list})
############################################################################################################

@login_required
# views.py
def model_solution_generator(request, pk):
    model_solution = get_object_or_404(ModelSolution, pk=pk)
    
    if request.method == 'POST':
        form = AllModelSolutionForm(request.POST, instance=model_solution)
        if form.is_valid():
            form.save()
            #################################################################
            ast_python_code = generate_ast_and_evaluation(get_1_file_content(model_solution.model_solution.path),
                                                        model_solution.model_solution_all_solutions, 
                                                        get_1_file_content(model_solution.question.question_file.path),
                                                        get_1_file_content(model_solution.question.grading_rubric.path))
            
            ast_python_code_cleaned = ast_python_code.replace('```python', '').replace('```', '').strip()
            # Write ast_python_code_cleaned to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
                temp_file.write(ast_python_code_cleaned.encode('utf-8'))
                temp_file_path = temp_file.name

            # Save the temporary file to the FileField
            with open(temp_file_path, 'rb') as temp_file:
                model_solution.ast_python_code.save(f"{model_solution.question.qn_code}_ast_python_code.py", ContentFile(temp_file.read()))
            #################################################################
            messages.success(request, 'Model solutions and AST code updated successfully.')
            return redirect('model-solution-generator', pk=model_solution.pk)
    else:
        form = AllModelSolutionForm(instance=model_solution)
        
    return render(request, 'grading/model_solution_generator.html', {'form': form})


######################################################################################################################
def student_submissions_list(request,pk): #add pk for later
    submissions = StudentSubmission.objects.filter(submission_batch=pk)
    form = ActualScoreForm()
    updated_submission_pk = request.GET.get('updated_submission_pk')
    return render(request, 'grading/student_submissions_list.html', {
        'submissions': submissions,
        'form': form,
        'updated_submission_pk': updated_submission_pk,
    })


def update_actual_score(request,pk):
    submission = get_object_or_404(StudentSubmission, pk=pk)
    if request.method == 'POST':
        form = ActualScoreForm(request.POST)
        if form.is_valid():
            submission.actual_score = form.cleaned_data['actual_score']
            submission.save()
            return redirect(f"{reverse('student_submissions_list', kwargs={'pk': submission.submission_batch.pk})}?updated_submission_pk={submission.pk}")
    return redirect('student_submissions_list')
    # else:
    #     form = ActualScoreForm(initial={'actual_score': submission.actual_score})
    # # Handle rendering a template if needed
    # return redirect('student_submissions_list')

@login_required
def student_submission_detail(request, pk):
    submission = get_object_or_404(StudentSubmission, pk=pk)
    return render(request, 'grading/student_submission_detail.html', {
        'submission': submission,
    })
##################################################################

def question_list(request):
    questions = Question.objects.filter(lecturer=request.user)
    return render(request, 'grading/question_list.html', {'questions': questions})

def delete_question(request, pk):
    if request.method == 'POST':
        question = get_object_or_404(Question, pk=pk)
        question.delete()
    return redirect('question_list')