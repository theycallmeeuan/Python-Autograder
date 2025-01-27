# import pandas as pd
# import numpy as np
# import plotly.express as px
# import dash_bootstrap_components as dbc
# from dash.dependencies import Input, Output, State
# from dash import dcc, html

# from django_plotly_dash import DjangoDash
# from django_pandas.io import read_frame

# from grading.models import StudentSubmission

# # Initialize the Dash app
# app = DjangoDash('AutograderAnalyticsDashboard', external_stylesheets=[dbc.themes.BOOTSTRAP])

# # Define the layout
# def serve_layout(**kwargs):
#     initial_arguments = kwargs.get('initial_arguments', {})
#     return dbc.Container([
#         dcc.Store(id='initial-arguments', data=initial_arguments),
#         dcc.Store(id='filtered-data', data=None),
#         html.Div(id='page-content'),
#         html.Div(id='debug-info', style={'margin-top': '20px', 'color': 'red'})  # Visible for debugging
#     ])

# app.layout = serve_layout  # Set the app layout to the function

# # Callback to parse initial arguments and fetch data
# @app.callback(
#     [Output('filtered-data', 'data'),
#      Output('page-content', 'children'),
#      Output('debug-info', 'children')],  # Output for debugging
#     Input('initial-arguments', 'data')
# )
# def update_data_and_layout(initial_arguments):
#     if not initial_arguments:
#         debug = "No initial arguments"
#         return None, html.H1("No data selected."), debug
#     else:
#         # Get parameters from initial_arguments
#         course_group_code = initial_arguments.get('course_group')
#         assignment_code = initial_arguments.get('assignment')
#         question_id = initial_arguments.get('question')

#         # Debugging: display the parsed parameters
#         debug = f"Parsed Parameters - Course Group: {course_group_code}, Assignment: {assignment_code}, Question ID: {question_id}"

#         if course_group_code and assignment_code and question_id:
#             # Fetch data from the database using the IDs
#             submissions = StudentSubmission.objects.filter(
#                 submission_batch__course_group__class_code=course_group_code,
#                 submission_batch__assignment__assignment_code=assignment_code,
#                 submission_batch__question__qn_code=question_id
#             )

#             # Check if submissions exist
#             if not submissions.exists():
#                 debug += " | No submissions found."
#                 return None, html.H1("No data available for the selected filters."), debug

#             # Convert QuerySet to DataFrame
#             students_df = read_frame(submissions)

#             # Ensure 'student_id' is a string
#             students_df['student_id'] = students_df['student_id'].astype(str)

#             # Serialize the DataFrame to JSON for storage in dcc.Store
#             data = students_df.to_json(date_format='iso', orient='split')

#             # Prepare the content layout
#             content = dbc.Container([
#                 html.H1("Python Autograder Analytics Dashboard"),

#                 # Summary Statistics and Student Dropdown
#                 dbc.Row([
#                     dbc.Col([
#                         html.H4("Summary Statistics"),
#                         html.Div(id='summary-stats'),
#                     ], width=4),

#                     dbc.Col([
#                         html.H4("Select a Student"),
#                         dcc.Dropdown(id='student-dropdown', placeholder="Select a student"),
#                         html.Div(id='student-data'),
#                     ], width=8),
#                 ], className='mb-4'),

#                 # Row for Pie Charts
#                 dbc.Row([
#                     dbc.Col(dcc.Graph(id='mark-distribution'), width=6),
#                     dbc.Col(dcc.Graph(id='error-topic-distribution'), width=6),
#                 ], className='mb-4'),

#                 # Row for Other Graphs
#                 dbc.Row([
#                     dbc.Col(dcc.Graph(id='test-cases-distribution'), width=6),
#                     dbc.Col(dcc.Graph(id='criteria-met-distribution'), width=6),
#                 ]),
#             ])
#             return data, content, debug
#         else:
#             debug += " | Missing parameters."
#             return None, html.H1("Invalid parameters."), debug

# # Callback to update the summary statistics and student dropdown
# @app.callback(
#     [Output('summary-stats', 'children'),
#      Output('student-dropdown', 'options')],
#     Input('filtered-data', 'data')
# )
# def update_summary_and_dropdown(data):
#     if data is None:
#         return html.P("No data available."), []
#     else:
#         students_df = pd.read_json(data, orient='split')
#         # Compute summary statistics
#         actual_scores = students_df['actual_score'].fillna(0)
#         mean_score = np.mean(actual_scores)
#         median_score = np.median(actual_scores)
#         std_dev_score = np.std(actual_scores, ddof=0)

#         summary = [
#             html.P(f"Mean Actual Score: {mean_score:.2f}"),
#             html.P(f"Median Actual Score: {median_score:.2f}"),
#             html.P(f"Standard Deviation: {std_dev_score:.2f}"),
#         ]

#         # Update student dropdown options
#         dropdown_options = [
#             {'label': f"Student {student_id}", 'value': student_id}
#             for student_id in students_df['student_id']
#         ]

#         return summary, dropdown_options

# # Callback for Total Marks Distribution
# @app.callback(
#     Output('mark-distribution', 'figure'),
#     Input('filtered-data', 'data')
# )
# def update_mark_distribution(data):
#     if data is None:
#         return {}
#     else:
#         students_df = pd.read_json(data, orient='split')
#         # Ensure 'Total Marks' exists
#         if 'Total Marks' not in students_df.columns:
#             students_df['Total Marks'] = students_df['actual_score']  # Or compute as needed

#         total_marks = students_df['Total Marks']
#         marks_counts = total_marks.value_counts().reset_index()
#         marks_counts.columns = ['Total Marks', 'Count']
#         fig = px.pie(marks_counts, names='Total Marks', values='Count',
#                      title='Distribution of Total Marks')
#         return fig

# # Callback for Error Topic Distribution
# @app.callback(
#     Output('error-topic-distribution', 'figure'),
#     Input('filtered-data', 'data')
# )
# def update_error_topic_distribution(data):
#     if data is None:
#         return {}
#     else:
#         students_df = pd.read_json(data, orient='split')
#         # Process error data
#         error_data = []
#         for _, student in students_df.iterrows():
#             error_topics = []
#             checker_feedback = student.get('checker_feedback', {}) or {}
#             redundant_code_list = checker_feedback.get('redundant_code', [])
#             if isinstance(redundant_code_list, list) and redundant_code_list:
#                 for issue in redundant_code_list:
#                     error_topic = issue.get('redundant_code_topic', 'Unknown Error')
#                     error_topics.append(error_topic)
#             else:
#                 error_topics.append('No Errors')
#             error_data.extend(error_topics)

#         error_topic_counts = pd.Series(error_data).value_counts().reset_index()
#         error_topic_counts.columns = ['Error Topic', 'Count']
#         fig = px.bar(error_topic_counts, x='Error Topic', y='Count', title='Distribution of Error Topics')
#         return fig

# # Callback for Test Cases Passed Distribution
# @app.callback(
#     Output('test-cases-distribution', 'figure'),
#     Input('filtered-data', 'data')
# )
# def update_test_cases_distribution(data):
#     if data is None:
#         return {}
#     else:
#         students_df = pd.read_json(data, orient='split')
#         test_cases_passed = students_df.get('test_cases_passed', pd.Series(dtype=int))
#         test_cases_passed = pd.to_numeric(test_cases_passed, errors='coerce').fillna(0).astype(int)
#         distribution = test_cases_passed.value_counts().sort_index().reset_index()
#         distribution.columns = ['Number of Test Cases Passed', 'Number of Students']
#         fig = px.bar(distribution, x='Number of Test Cases Passed', y='Number of Students',
#                      title='Distribution of Number of Test Cases Passed',
#                      labels={'Number of Test Cases Passed': 'Test Cases Passed', 'Number of Students': 'Students'})
#         return fig

# # Callback for Criteria Met Distribution
# @app.callback(
#     Output('criteria-met-distribution', 'figure'),
#     Input('filtered-data', 'data')
# )
# def update_criteria_met_distribution(data):
#     if data is None:
#         return {}
#     else:
#         students_df = pd.read_json(data, orient='split')
#         # Extract and process criteria met data from 'question_specific_feedback' field
#         criteria_met_data = []
#         criteria_set = set()
#         for _, student in students_df.iterrows():
#             student_criteria = {}
#             feedback = student.get('question_specific_feedback', {}) or {}
#             criteria_list = feedback.get('Criteria', [])
#             marks_list = feedback.get('Marks', [])
#             for criterion, mark in zip(criteria_list, marks_list):
#                 student_criteria[criterion] = float(mark)
#                 criteria_set.add(criterion)
#             criteria_met_data.append(student_criteria)

#         # Create a DataFrame for criteria met analysis
#         criteria_df = pd.DataFrame(criteria_met_data)

#         # Fill missing criteria with zeros
#         for criterion in criteria_set:
#             if criterion not in criteria_df.columns:
#                 criteria_df[criterion] = 0.0

#         # Sum marks per criterion
#         criteria_counts = criteria_df.notnull().astype(int).sum().reset_index()
#         criteria_counts.columns = ['Criterion', 'Number of Students Met']

#         fig = px.bar(criteria_counts, x='Criterion', y='Number of Students Met',
#                      title='Number of Students Who Met Each Criterion')
#         return fig

# # Callback to display student data
# @app.callback(
#     Output('student-data', 'children'),
#     [Input('student-dropdown', 'value'),
#      State('filtered-data', 'data')]
# )
# def display_student_data(student_id, data):
#     if student_id is None or data is None:
#         return html.P("Select a student to see their data.")
#     else:
#         students_df = pd.read_json(data, orient='split')
#         student = students_df[students_df['student_id'] == student_id].iloc[0]

#         # Prepare data to display
#         student_info = [
#             html.H5(f"Student ID: {student['student_id']}"),
#             html.P(f"Needs Manual Review: {student.get('needs_manual_review', 'N/A')}"),
#             html.P(f"Actual Score: {student.get('actual_score', 'N/A')}"),
#             html.P(f"Test Cases Passed: {student.get('test_cases_passed', 'N/A')} / {student.get('total_test_cases', 'N/A')}"),
#             html.P(f"Best Practices Score: {student.get('best_practices_score', 'N/A')}"),
#             html.P(f"Question Specific Score: {student.get('question_specific_score', 'N/A')}"),
#             html.P(f"Final Suggested Score: {student.get('final_suggested_score', 'N/A')}"),
#             html.P(f"Total Marks: {student.get('Total Marks', 'N/A')}"),
#         ]

#         # Display test cases feedback
#         test_cases_feedback = student.get('test_cases_feedback', {}) or {}
#         test_cases_list = []
#         if test_cases_feedback:
#             for test_case_name, feedback in test_cases_feedback.items():
#                 result = feedback.get('result', 'No Result')
#                 message = feedback.get('message', '')
#                 test_cases_list.append(html.Li(f"{test_case_name}: {result} - {message}"))
#             test_cases_div = html.Div([
#                 html.H6("Test Cases Feedback:"),
#                 html.Ul(test_cases_list)
#             ])
#         else:
#             test_cases_div = html.P("No test cases feedback available.")

#         # Display best practices feedback
#         best_practices_feedback = student.get('best_practices_feedback', {}) or {}
#         best_practices_list = []
#         redundant_code_list = best_practices_feedback.get('redundant_code', [])
#         if isinstance(redundant_code_list, list) and redundant_code_list:
#             for issue in redundant_code_list:
#                 issue_topic = issue.get('redundant_code_topic', 'No Topic')
#                 summary = issue.get('summary', '')
#                 issue_lines = issue.get('redundant_code_line_number', [])
#                 lines_list = []
#                 for line in issue_lines:
#                     line_number = line.get('line_number', 'Unknown')
#                     code_line = line.get('code', '')
#                     lines_list.append(html.Li(f"Line {line_number}: {code_line}"))
#                 best_practices_list.append(
#                     html.Div([
#                         html.H6(issue_topic),
#                         html.P(summary),
#                         html.Ul(lines_list)
#                     ])
#                 )
#             best_practices_div = html.Div([
#                 html.H6("Best Practices Feedback:"),
#                 html.Div(best_practices_list)
#             ])
#         else:
#             best_practices_div = html.P("No best practices feedback available.")

#         # Display question specific feedback
#         qn_feedback = student.get('question_specific_feedback', {}) or {}
#         criteria = qn_feedback.get('Criteria', {})
#         descriptions = qn_feedback.get('Description', {})
#         marks = qn_feedback.get('Marks', {})
#         if criteria:
#             qn_feedback_list = []
#             for key in sorted(criteria.keys(), key=lambda x: int(x)):
#                 qn_feedback_list.append(
#                     html.Tr([
#                         html.Td(criteria[key]),
#                         html.Td(descriptions.get(key, '')),
#                         html.Td(marks.get(key, ''))
#                     ])
#                 )
#             qn_feedback_table = html.Table([
#                 html.Thead(html.Tr([html.Th("Criteria"), html.Th("Description"), html.Th("Marks")])),
#                 html.Tbody(qn_feedback_list)
#             ])
#             qn_specific_div = html.Div([
#                 html.H6("Question Specific Feedback:"),
#                 qn_feedback_table
#             ])
#         else:
#             qn_specific_div = html.P("No question-specific feedback available.")

#         return html.Div([
#             *student_info,
#             html.Hr(),
#             test_cases_div,
#             html.Hr(),
#             best_practices_div,
#             html.Hr(),
#             qn_specific_div
#         ])


# # # Fetch data from the StudentSubmission model
# # submissions = StudentSubmission.objects.all()

# # # Convert QuerySet to DataFrame
# # students_df = read_frame(submissions)

# # # Ensure student_id is a string
# # students_df['student_id'] = students_df['student_id'].astype(str)

# # # Check if the DataFrame is empty
# # if students_df.empty:
# #     print("No data available.")
# # else:
# #     # Compute summary statistics for actual scores
# #     actual_scores = students_df['actual_score'].fillna(0)
# #     mean_score = np.mean(actual_scores)
# #     median_score = np.median(actual_scores)
# #     std_dev_score = np.std(actual_scores, ddof=0)

# #     # Extract and process error-related data from 'checker_feedback' field
# #     error_data = []
# #     for i, student in students_df.iterrows():
# #         error_topics = []
# #         checker_feedback = student['checker_feedback'] or {}
# #         redundant_code_list = checker_feedback.get('redundant_code', [])
# #         if isinstance(redundant_code_list, list) and redundant_code_list:
# #             for issue in redundant_code_list:
# #                 error_topic = issue.get('redundant_code_topic', 'Unknown Error')
# #                 error_topics.append(error_topic)
# #         else:
# #             error_topics.append('No Errors')
# #         error_data.append({'Student ID': student['student_id'], 'Error Topics': error_topics})

# #     error_df = pd.DataFrame(error_data)

# #     # Extract and process criteria met data from 'question_specific_feedback' field
# #     criteria_met_data = []
# #     criteria_set = set()
# #     for i, student in students_df.iterrows():
# #         student_criteria = {}
# #         feedback = student['question_specific_feedback'] or {}
# #         criteria_list = feedback.get('Criteria', [])
# #         marks_list = feedback.get('Marks', [])
# #         for criterion, mark in zip(criteria_list, marks_list):
# #             student_criteria[criterion] = float(mark)
# #             criteria_set.add(criterion)
# #         criteria_met_data.append(student_criteria)

# #     # Create a DataFrame for criteria met analysis
# #     criteria_df = pd.DataFrame(criteria_met_data)

# #     # Fill missing criteria with zeros
# #     for criterion in criteria_set:
# #         if criterion not in criteria_df.columns:
# #             criteria_df[criterion] = 0.0

# #     # Sum marks per criterion
# #     criteria_summary = criteria_df.notnull().astype(int).sum().reset_index()
# #     criteria_summary.columns = ['Criterion', 'Number of Students Met']

# #     # Calculate total marks per student
# #     students_df['Total Marks'] = criteria_df.sum(axis=1)

# # # Initialize the Dash app
# # app = DjangoDash('AutograderAnalyticsDashboard', external_stylesheets=[dbc.themes.BOOTSTRAP], serve_locally=False)

# # # Define the layout
# # def serve_layout():
# #     if students_df.empty:
# #         # Display a message when there's no data
# #         return dbc.Container([
# #             html.H1("Dashboard is not available as no data has been uploaded.")
# #         ])
# #     else:
# #         # Proceed with the normal layout
# #         return dbc.Container([
# #             html.H1("Python Autograder Analytics Dashboard"),

# #             # Summary Statistics and Student Dropdown
# #             dbc.Row([
# #                 dbc.Col([
# #                     html.H4("Summary Statistics"),
# #                     html.P(f"Mean Actual Score: {mean_score:.2f}"),
# #                     html.P(f"Median Actual Score: {median_score:.2f}"),
# #                     html.P(f"Standard Deviation: {std_dev_score:.2f}"),
# #                 ], width=4),

# #                 dbc.Col([
# #                     html.H4("Select a Student"),
# #                     dcc.Dropdown(
# #                         id='student-dropdown',
# #                         options=[
# #                             {'label': f"Student {student_id}", 'value': student_id}
# #                             for student_id in students_df['student_id']
# #                         ],
# #                         placeholder="Select a student",
# #                     ),
# #                     html.Div(id='student-data'),
# #                 ], width=8),
# #             ], className='mb-4'),

# #             # Row for Pie Charts (Removed score-distribution graph)
# #             dbc.Row([
# #                 # Removed score-distribution graph
# #                 dbc.Col(dcc.Graph(id='mark-distribution'), width=6),
# #             ], className='mb-4'),

# #             # Row for Other Graphs
# #             dbc.Row([
# #                 dbc.Col(dcc.Graph(id='error-topic-distribution'), width=6),
# #                 dbc.Col(dcc.Graph(id='test-cases-distribution'), width=6),
# #             ]),

# #             # Row for Criteria Met Distribution
# #             dbc.Row([
# #                 dbc.Col(dcc.Graph(id='criteria-met-distribution'), width=12),
# #             ], className='mt-4'),
# #         ])

# # app.layout = serve_layout  # Set the app layout to the function

# # # Only proceed with callbacks if data is available
# # if not students_df.empty:

# #     # Removed the callback for Final Suggested Score Distribution
# #     # Callback for Total Marks Distribution
# #     @app.callback(
# #         Output('mark-distribution', 'figure'),
# #         Input('mark-distribution', 'id')
# #     )
# #     def update_mark_distribution(_):
# #         total_marks = students_df['Total Marks']
# #         marks_counts = total_marks.value_counts().reset_index()
# #         marks_counts.columns = ['Total Marks', 'Count']
# #         fig = px.pie(marks_counts, names='Total Marks', values='Count',
# #                      title=f'Distribution of Criteria Marks')
# #         return fig

# #     # Callback for Error Topic Distribution
# #     @app.callback(
# #         Output('error-topic-distribution', 'figure'),
# #         Input('error-topic-distribution', 'id')
# #     )
# #     def update_error_topic_distribution(_):
# #         all_error_topics = []
# #         for topics in error_df['Error Topics']:
# #             all_error_topics.extend(topics)
# #         error_topic_counts = pd.Series(all_error_topics).value_counts().reset_index()
# #         error_topic_counts.columns = ['Error Topic', 'Count']
# #         fig = px.bar(error_topic_counts, x='Error Topic', y='Count', title='Distribution of Error Topics')
# #         return fig

# #     # Callback for Test Cases Passed Distribution
# #     @app.callback(
# #         Output('test-cases-distribution', 'figure'),
# #         Input('test-cases-distribution', 'id')
# #     )
# #     def update_test_cases_distribution(_):
# #         test_cases_passed = students_df.get('test_cases_passed', pd.Series(dtype=int))
# #         test_cases_passed = pd.to_numeric(test_cases_passed, errors='coerce').fillna(0).astype(int)
# #         distribution = test_cases_passed.value_counts().sort_index().reset_index()
# #         distribution.columns = ['Number of Test Cases Passed', 'Number of Students']
# #         fig = px.bar(distribution, x='Number of Test Cases Passed', y='Number of Students',
# #                      title='Distribution of Number of Test Cases Passed',
# #                      labels={'Number of Test Cases Passed': 'Test Cases Passed', 'Number of Students': 'Students'})
# #         return fig

# #     # Callback for Criteria Met Distribution
# #     @app.callback(
# #         Output('criteria-met-distribution', 'figure'),
# #         Input('criteria-met-distribution', 'id')
# #     )
# #     def update_criteria_met_distribution(_):
# #         criteria_counts = criteria_df.notnull().astype(int).sum().reset_index()
# #         criteria_counts.columns = ['Criterion', 'Number of Students Met']
# #         fig = px.bar(criteria_counts, x='Criterion', y='Number of Students Met',
# #                     title='Number of Students Who Met Each Criterion')
# #         return fig

# #     # Callback to display student data
# #     @app.callback(
# #         Output('student-data', 'children'),
# #         Input('student-dropdown', 'value')
# #     )
# #     def display_student_data(student_id):
# #         if student_id is None:
# #             return html.P("Select a student to see their data.")
# #         else:
# #             student = students_df[students_df['student_id'] == student_id].iloc[0]

# #             # Prepare data to display
# #             student_info = [
# #                 html.H5(f"Student ID: {student['student_id']}"),
# #                 html.P(f"Needs Manual Review: {student.get('needs_manual_review', 'N/A')}"),
# #                 html.P(f"Actual Score: {student.get('actual_score', 'N/A')}"),
# #                 html.P(f"Test Cases Passed: {student.get('test_cases_passed', 'N/A')} / {student.get('total_test_cases', 'N/A')}"),
# #                 html.P(f"Best Practices Score: {student.get('best_practices_score', 'N/A')}"),
# #                 html.P(f"Question Specific Score: {student.get('question_specific_score', 'N/A')}"),
# #                 html.P(f"Total Marks: {student.get('Total Marks', 'N/A')}"),
# #             ]

# #             # Display test cases feedback
# #             test_cases_feedback = student.get('test_cases_feedback', {}) or {}
# #             test_cases_list = []
# #             if test_cases_feedback:
# #                 for test_case_name, feedback in test_cases_feedback.items():
# #                     result = feedback.get('result', 'No Result')
# #                     message = feedback.get('message', '')
# #                     test_cases_list.append(html.Li(f"{test_case_name}: {result} - {message}"))
# #                 test_cases_div = html.Div([
# #                     html.H6("Test Cases Feedback:"),
# #                     html.Ul(test_cases_list)
# #                 ])
# #             else:
# #                 test_cases_div = html.P("No test cases feedback available.")

# #             # Display best practices feedback
# #             best_practices_feedback = student.get('best_practices_feedback', {}) or {}
# #             best_practices_list = []
# #             best_practice_results = best_practices_feedback.get('best_practice_result', [])
# #             if isinstance(best_practice_results, list) and best_practice_results:
# #                 for issue in best_practice_results:
# #                     line = issue.get('line', 'Unknown Line')
# #                     message = issue.get('message', 'No Message')
# #                     best_practices_list.append(html.Li(f"Line {line}: {message}"))
# #                 best_practices_div = html.Div([
# #                     html.H6("Best Practices Feedback:"),
# #                     html.Ul(best_practices_list)
# #                 ])
# #             else:
# #                 best_practices_div = html.P("No best practices feedback available.")

# #             # Display question specific feedback
# #             qn_feedback = student.get('question_specific_feedback', {}) or {}
# #             criteria = qn_feedback.get('Criteria', [])
# #             descriptions = qn_feedback.get('Description', [])
# #             marks = qn_feedback.get('Marks', [])
# #             if criteria:
# #                 qn_feedback_list = []
# #                 for criterion, description, mark in zip(criteria, descriptions, marks):
# #                     qn_feedback_list.append(
# #                         html.Tr([
# #                             html.Td(criterion),
# #                             html.Td(description),
# #                             html.Td(mark)
# #                         ])
# #                     )
# #                 qn_feedback_table = html.Table([
# #                     html.Thead(html.Tr([html.Th("Criteria"), html.Th("Description"), html.Th("Marks")])),
# #                     html.Tbody(qn_feedback_list)
# #                 ])
# #                 qn_specific_div = html.Div([
# #                     html.H6("Question Specific Feedback:"),
# #                     qn_feedback_table
# #                 ])
# #             else:
# #                 qn_specific_div = html.P("No question-specific feedback available.")

# #             return html.Div([
# #                 *student_info,
# #                 html.Hr(),
# #                 test_cases_div,
# #                 html.Hr(),
# #                 best_practices_div,
# #                 html.Hr(),
# #                 qn_specific_div
# #             ])

