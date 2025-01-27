from django.urls import path
from . import views
from .views import SignUpView
from django.conf import settings
from django.conf.urls.static import static
# from grading.dash_apps.finished_apps import AutograderAnalyticsDashboard

urlpatterns = [
    path("", views.home, name="grading-home"), #Empty route pattern matching from project urls.py
    path("history/", views.history, name="grading-history"), #Route pattern matching from project urls.py
    path('delete_submission_batch/<int:pk>/', views.delete_submission_batch, name='delete_submission_batch'),
    path("dashboard/", views.dashboard, name="grading-dashboard"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path('logout/',views.logout_view,name='logout'),
    path("assignment_class/", views.create_course_and_assignment, name="assignment-class"),
    path("question/", views.upload_materials, name="question-upload"),
    path("submission_upload/", views.submission_upload, name="submission-upload"),
    path("model_solution_generator/<int:pk>/", views.model_solution_generator, name="model-solution-generator"),
    path('student-submissions/<int:pk>/', views.student_submissions_list, name='student_submissions_list'),
    path('update_actual_score/<int:pk>/', views.update_actual_score, name='update_actual_score'),
    path('student/<int:pk>/', views.student_submission_detail, name='student_submission_detail'),
    path('question-list/', views.question_list, name='question_list'),
    path('delete_question/<int:pk>/', views.delete_question, name='delete_question'),

    path('ajax/load-assignments/', views.load_assignments, name='ajax_load_assignments'),
    path('ajax/load-questions/', views.load_questions, name='ajax_load_questions'),
    path('ajax/load-course-groups/', views.load_course_groups, name='ajax_load_course_groups')

] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
