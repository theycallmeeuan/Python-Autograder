# # grading/dash_app.py

# import pandas as pd
# import numpy as np
# import plotly.express as px
# # from dash import dcc, html
# import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output
# # import dash_core_components as dcc
# # import dash_html_components as html
# from dash import dcc,html

# from django_plotly_dash import DjangoDash
# from django_pandas.io import read_frame

# from grading.models import StudentSubmission

# # Fetch data from the StudentSubmission model
# submissions = StudentSubmission.objects.all()

# # Convert QuerySet to DataFrame
# students_df = read_frame(submissions)

# # Ensure student_id is a string
# students_df['student_id'] = students_df['student_id'].astype(str)

# # Compute summary statistics for final suggested scores
# final_scores = students_df['final_suggested_score'].fillna(0)
# mean_score = np.mean(final_scores)
# median_score = np.median(final_scores)
# std_dev_score = np.std(final_scores, ddof=0)

# # Extract and process error-related data from 'checker_feedback' field
# error_data = []
# for i, student in students_df.iterrows():
#     error_topics = []
#     checker_feedback = student['checker_feedback'] or {}
#     redundant_code_list = checker_feedback.get('redundant_code', [])
#     if isinstance(redundant_code_list, list):
#         for issue in redundant_code_list:
#             error_topic = issue.get('redundant_code_topic', 'Unknown Error')
#             error_topics.append(error_topic)
#     error_data.append({'Student ID': student['student_id'], 'Error Topics': error_topics})

# error_df = pd.DataFrame(error_data)

# # Extract and process criteria met data from 'question_specific_feedback' field
# criteria_met_data = []
# criteria_set = set()
# for i, student in students_df.iterrows():
#     student_criteria = {}
#     feedback = student['question_specific_feedback'] or {}
#     criteria_list = feedback.get('Criteria', [])
#     marks_list = feedback.get('Marks', [])
#     for criterion, mark in zip(criteria_list, marks_list):
#         student_criteria[criterion] = float(mark)
#         criteria_set.add(criterion)
#     criteria_met_data.append(student_criteria)

# # Create a DataFrame for criteria met analysis
# criteria_df = pd.DataFrame(criteria_met_data)

# # Fill missing criteria with zeros
# for criterion in criteria_set:
#     if criterion not in criteria_df.columns:
#         criteria_df[criterion] = 0.0

# # Sum marks per criterion
# criteria_summary = criteria_df.notnull().astype(int).sum().reset_index()
# criteria_summary.columns = ['Criterion', 'Number of Students Met']

# # Calculate total marks per student
# students_df['Total Marks'] = criteria_df.sum(axis=1)

# # app = DjangoDash('AutograderAnalyticsDashboard', external_stylesheets=[dbc.themes.BOOTSTRAP])

# # app.layout = html.Div([
# #     html.H1("Test Dashboard"),
# #     html.P("This is a test.")
# # ])
# # Initialize the Dash app
# app = DjangoDash('AutograderAnalyticsDashboard', external_stylesheets=[dbc.themes.BOOTSTRAP],serve_locally=False)

# # Define the layout
# app.layout = dbc.Container([
#     html.H1("Python Autograder Analytics Dashboard"),

#     # Summary Statistics and Student Dropdown
#     dbc.Row([
#         dbc.Col([
#             html.H4("Summary Statistics"),
#             html.P(f"Mean Final Score: {mean_score:.2f}"),
#             html.P(f"Median Final Score: {median_score:.2f}"),
#             html.P(f"Standard Deviation: {std_dev_score:.2f}"),
#         ], width=4),

#         dbc.Col([
#             html.H4("Select a Student"),
#             dcc.Dropdown(
#                 id='student-dropdown',
#                 options=[
#                     {'label': f"Student {student_id}", 'value': student_id}
#                     for student_id in students_df['student_id']
#                 ],
#                 placeholder="Select a student",
#             ),
#             html.Div(id='student-data'),
#         ], width=8),
#     ], className='mb-4'),

#     # Row for Pie Charts
#     dbc.Row([
#         dbc.Col(dcc.Graph(id='score-distribution'), width=6),
#         dbc.Col(dcc.Graph(id='mark-distribution'), width=6),
#     ], className='mb-4'),

#     # Row for Other Graphs
#     dbc.Row([
#         dbc.Col(dcc.Graph(id='error-topic-distribution'), width=6),
#         dbc.Col(dcc.Graph(id='test-cases-distribution'), width=6),
#     ]),

#     # Row for Criteria Met Distribution
#     dbc.Row([
#         dbc.Col(dcc.Graph(id='criteria-met-distribution'), width=12),
#     ], className='mt-4'),
# ])

# # Callbacks and other code remain the same, adjusted for the new data sources
# # Callback for Final Suggested Score Distribution
# @app.callback(
#     Output('score-distribution', 'figure'),
#     Input('score-distribution', 'id')
# )
# def update_score_distribution(_):
#     score_counts = students_df['final_suggested_score'].value_counts().reset_index()
#     score_counts.columns = ['Final Suggested Score', 'Count']
#     fig = px.pie(score_counts, names='Final Suggested Score', values='Count',
#                  title='Distribution of Final Suggested Scores')
#     return fig

# # Callback for Total Marks Distribution
# @app.callback(
#     Output('mark-distribution', 'figure'),
#     Input('mark-distribution', 'id')
# )
# def update_mark_distribution(_):
#     total_marks = students_df['Total Marks']
#     marks_counts = total_marks.value_counts().reset_index()
#     marks_counts.columns = ['Total Marks', 'Count']
#     fig = px.pie(marks_counts, names='Total Marks', values='Count',
#                  title='Distribution of Total Marks')
#     return fig

# # Callback for Error Topic Distribution
# @app.callback(
#     Output('error-topic-distribution', 'figure'),
#     Input('error-topic-distribution', 'id')
# )
# def update_error_topic_distribution(_):
#     all_error_topics = []
#     for topics in error_df['Error Topics']:
#         all_error_topics.extend(topics)
#     error_topic_counts = pd.Series(all_error_topics).value_counts().reset_index()
#     error_topic_counts.columns = ['Error Topic', 'Count']
#     fig = px.bar(error_topic_counts, x='Error Topic', y='Count', title='Distribution of Error Topics')
#     return fig

# # Callback for Test Cases Passed Distribution
# @app.callback(
#     Output('test-cases-distribution', 'figure'),
#     Input('test-cases-distribution', 'id')
# )
# def update_test_cases_distribution(_):
#     test_cases_passed = students_df['test_cases_passed']
#     test_cases_passed = pd.to_numeric(test_cases_passed, errors='coerce').fillna(0).astype(int)
#     distribution = test_cases_passed.value_counts().sort_index().reset_index()
#     distribution.columns = ['Number of Test Cases Passed', 'Number of Students']
#     fig = px.bar(distribution, x='Number of Test Cases Passed', y='Number of Students',
#                  title='Distribution of Number of Test Cases Passed',
#                  labels={'Number of Test Cases Passed': 'Test Cases Passed', 'Number of Students': 'Students'})
#     return fig

# # Callback for Criteria Met Distribution
# @app.callback(
#     Output('criteria-met-distribution', 'figure'),
#     Input('criteria-met-distribution', 'id')
# )
# def update_criteria_met_distribution(_):
#     criteria_counts = criteria_df.notnull().astype(int).sum().reset_index()
#     criteria_counts.columns = ['Criterion', 'Number of Students Met']
#     fig = px.bar(criteria_counts, x='Criterion', y='Number of Students Met',
#                 title='Number of Students Who Met Each Criterion')
#     return fig

# # Callback to display student data
# @app.callback(
#     Output('student-data', 'children'),
#     Input('student-dropdown', 'value')
# )
# def display_student_data(student_id):
#     if student_id is None:
#         return html.P("Select a student to see their data.")
#     else:
#         student = students_df[students_df['student_id'] == student_id].iloc[0]

#         # Prepare data to display
#         student_info = [
#             html.H5(f"Student ID: {student['student_id']}"),
#             html.P(f"Needs Manual Review: {student['needs_manual_review']}"),
#             html.P(f"Actual Score: {student['actual_score']}"),
#             html.P(f"Test Cases Passed: {student['test_cases_passed']} / {student['total_test_cases']}"),
#             html.P(f"Best Practices Score: {student['best_practices_score']}"),
#             html.P(f"Question Specific Score: {student['question_specific_score']}"),
#             html.P(f"Final Suggested Score: {student['final_suggested_score']}"),
#             html.P(f"Total Marks: {student['Total Marks']}"),
#         ]

#         # Display test cases feedback
#         test_cases_feedback = student['test_cases_feedback'] or {}
#         test_cases_list = []
#         for test_case_name, feedback in test_cases_feedback.items():
#             result = feedback.get('result', 'No Result')
#             message = feedback.get('message', '')
#             test_cases_list.append(html.Li(f"{test_case_name}: {result} - {message}"))
#         test_cases_div = html.Div([
#             html.H6("Test Cases Feedback:"),
#             html.Ul(test_cases_list)
#         ])

#         # Display best practices feedback
#         best_practices_feedback = student['best_practices_feedback'] or {}
#         best_practices_list = []
#         best_practice_results = best_practices_feedback.get('best_practice_result', [])
#         if isinstance(best_practice_results, list):
#             for issue in best_practice_results:
#                 line = issue.get('line', 'Unknown Line')
#                 message = issue.get('message', 'No Message')
#                 best_practices_list.append(html.Li(f"Line {line}: {message}"))
#         best_practices_div = html.Div([
#             html.H6("Best Practices Feedback:"),
#             html.Ul(best_practices_list)
#         ])

#         # Display question specific feedback
#         qn_feedback = student['question_specific_feedback'] or {}
#         criteria = qn_feedback.get('Criteria', [])
#         descriptions = qn_feedback.get('Description', [])
#         marks = qn_feedback.get('Marks', [])
#         qn_feedback_list = []
#         for criterion, description, mark in zip(criteria, descriptions, marks):
#             qn_feedback_list.append(
#                 html.Tr([
#                     html.Td(criterion),
#                     html.Td(description),
#                     html.Td(mark)
#                 ])
#             )
#         qn_feedback_table = html.Table([
#             html.Thead(html.Tr([html.Th("Criteria"), html.Th("Description"), html.Th("Marks")])),
#             html.Tbody(qn_feedback_list)
#         ])
#         qn_specific_div = html.Div([
#             html.H6("Question Specific Feedback:"),
#             qn_feedback_table
#         ])

#         return html.Div([
#             *student_info,
#             html.Hr(),
#             test_cases_div,
#             html.Hr(),
#             best_practices_div,
#             html.Hr(),
#             qn_specific_div
#         ])
