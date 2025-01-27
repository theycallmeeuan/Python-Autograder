from django.db import models
from django.contrib.auth.models import AbstractUser,User
from django.utils import timezone
# from ckeditor.fields import RichTextField
# Create your models here.

def grading_rubric_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    assignment = instance.assignment.assignment_code
    question = instance.qn_code
    lecturer = instance.lecturer.username
    print()
    return f"{lecturer}/{assignment}/{question}/grading_rubric/{filename}"

def question_file_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    assignment = instance.assignment.assignment_code
    question = instance.qn_code
    lecturer = instance.lecturer.username
    return f"{lecturer}/{assignment}/{question}/question_file/{filename}"

def model_solution_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    assignment = instance.question.assignment.assignment_code
    question = instance.question.qn_code
    lecturer = instance.lecturer.username
    return f"{lecturer}/{assignment}/{question}/model_solution/{filename}"

def ast_python_solution_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    assignment = instance.question.assignment.assignment_code
    question = instance.question.qn_code
    lecturer = instance.lecturer.username
    return f"{lecturer}/{assignment}/{question}/ast_python_solution/{filename}"

def test_cases_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    assignment = instance.assignment.assignment_code
    question = instance.qn_code
    lecturer = instance.lecturer.username
    return f"{lecturer}/{assignment}/{question}/test_cases/{filename}"

def submission_batch_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    assignment = instance.question.assignment.assignment_code
    question = instance.question.qn_code
    lecturer = instance.lecturer.username
    course_group = instance.course_group.class_code
    return f"{lecturer}/{assignment}/{question}/submission_batch/{course_group}/{filename}"
    #return f"{lecturer}/{assignment}/{question}/submission_batch/{filename}"

class Lecturer(AbstractUser):
    pass
    # add additional fields in here

    def __str__(self):
        return self.username

class CourseGroup(models.Model):
    class_code = models.CharField(primary_key=True,max_length=20)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name='course_groups')

    def __str__(self):
        return f"{self.class_code}"

class Assignment(models.Model):
    assignment_code = models.CharField(primary_key=True, max_length=20)
    course_group = models.ManyToManyField(CourseGroup, related_name='assignments')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        course_codes = ", ".join([cg.class_code for cg in self.course_group.all()])
        return f"{self.assignment_code} (Course Groups: {course_codes})"

class Question(models.Model):
    #not setting qn_code as primary key in case you have multiple 'Q2' code or same assignment code
    qn_code = models.CharField(max_length=10)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='questions')
    #description = models.TextField(null=True)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)    
    grading_rubric = models.FileField(upload_to=grading_rubric_directory_path)
    question_file = models.FileField(upload_to=question_file_directory_path,default= "")
    test_cases_file = models.FileField(upload_to=test_cases_directory_path,default="")
    qn_total_score = models.FloatField(default=0,null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [['qn_code', 'assignment']]
    def __str__(self):
        return f"{self.qn_code},{self.assignment.assignment_code}"

class ModelSolution(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='model_solutions')
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)    
    model_solution = models.FileField(upload_to=model_solution_directory_path)
    model_solution_all_solutions = models.TextField(null=True, blank=True)
    ast_python_code = models.FileField(upload_to=ast_python_solution_directory_path, null=True, blank=True)  # Change to FileField
    

    def __str__(self):
        return f"Model Solution for {self.question.qn_code}"

class SubmissionBatch(models.Model):
    submission_id = models.AutoField(primary_key=True)
    # course_group = models.CharField( default = "", max_length=20)# for storing course group name when saving form to guide file path directory
    # question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='submission_batch')
    # lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True, blank=True)# for storing lecturer name when saving form to guide file path directory
    # # form fields to populate upload path
    # course_group = models.CharField(null=True, blank=True,default="",max_length=20)
    # assignment = models.CharField(null=True, blank=True,default="",max_length=20)
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
    )
    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    course_group = models.ForeignKey(
        CourseGroup,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    assignment = models.ForeignKey(
        Assignment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    
    student_submissions_zip = models.FileField(upload_to=submission_batch_directory_path)
    uploaded_at = models.DateTimeField(default=timezone.now)
    total_submissions = models.IntegerField(default=0) #TODO: if celery workers wanna update this
    processed_submissions = models.IntegerField(default=0) #TODO: if celery workers wanna update this

    def __str__(self):
        return f"Submission Batch for {self.question.qn_code} with id {self.submission_id}"


class StudentSubmission(models.Model):
    student_id = models.AutoField(primary_key=True) # proof of concept so each student has no id yet #TODO: make into primary key in the future
    submission_batch = models.ForeignKey(SubmissionBatch, on_delete=models.CASCADE, related_name='student_submissions')
    submission_file = models.TextField(max_length=10000)
    needs_manual_review = models.BooleanField(default=False)
    actual_score = models.FloatField(null=True, blank=True)  # Score after lecturer's manual adjustment

    
    # Results from checkers
    test_cases_passed = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    test_cases_feedback = models.JSONField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True,default=0)
    ################################################################
    best_practices_score = models.FloatField(null=True, blank=True)
    best_practices_feedback = models.JSONField(null=True, blank=True)
    ###################################################################
    question_specific_score = models.FloatField(null=True, blank=True)
    question_specific_total_score = models.FloatField(default=0,null=True, blank=True)
    question_specific_feedback = models.JSONField(null=True, blank=True)
    final_suggested_score = models.FloatField(null=True, blank=True)

    # Storing detailed feedback as JSON
    checker_feedback = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.student_id} - Submission Batch ID: {self.submission_batch.submission_id}"
