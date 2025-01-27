from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
# from ckeditor.widgets import CKEditorWidget
from .models import Lecturer,CourseGroup,Assignment,Question,ModelSolution,SubmissionBatch,StudentSubmission

class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = Lecturer
        fields = ("username", "email")

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = Lecturer
        fields = ("username", "email")


class CourseGroupForm(forms.ModelForm):
    class Meta:
        model = CourseGroup
        fields = ('class_code',)
        # 'lecturer' will be set to the logged-in user, so it's not included here

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('assignment_code', 'created_at',)
        widgets = {
            'created_at': forms.HiddenInput(),  # Auto-set in the view
        }
    
    def validate_unique(self):
        # Skip the uniqueness validation for the form
        pass

# forms.py
class CourseGroupSelectionForm(forms.Form):
    course_group = forms.ModelChoiceField(
        queryset=CourseGroup.objects.all(),
        required=False,
        label="Select Existing Course Group",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    new_class_code = forms.CharField(
        max_length=20,
        required=False,
        label="Or Enter New Class Code",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.lecturer = kwargs.pop('lecturer', None)
        super().__init__(*args, **kwargs)
        if self.lecturer:
            self.fields['course_group'].queryset = CourseGroup.objects.filter(lecturer=self.lecturer)

    def clean(self):
        cleaned_data = super().clean()
        course_group = cleaned_data.get('course_group')
        new_class_code = cleaned_data.get('new_class_code')

        if not course_group and not new_class_code:
            raise forms.ValidationError(
                "Please select an existing course group or enter a new class code!"
            )
        if course_group and new_class_code:
            raise forms.ValidationError(
                "Please fill in either option not both!"
            )
        if new_class_code:
            # Check if the class code already exists
            if CourseGroup.objects.filter(class_code=new_class_code).exists():
                raise forms.ValidationError(
                    f"Course group with class code '{new_class_code}' already exists."
                )
            

################################################################################
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['qn_code', 'assignment', 'grading_rubric', 'question_file','test_cases_file',"qn_total_score"]
        # widgets = {
        #     'assignment': forms.Select(),  # Dropdown to select existing assignments
        # }
    def __init__(self, *args, **kwargs):
        print(kwargs)
        lecturer = kwargs.pop('lecturer', None)
        super(QuestionForm, self).__init__(*args, **kwargs)
        if lecturer:
            # Filter assignments to those created by the lecturer
            self.fields['assignment'].queryset = Assignment.objects.filter(
                course_group__lecturer=lecturer
            ).distinct()

class ModelSolutionForm(forms.ModelForm):
    class Meta:
        model = ModelSolution
        fields = ['model_solution']
########################################################################################
class SubmissionUploadForm(forms.ModelForm):

    class Meta:
        model = SubmissionBatch
        fields = ['course_group', 'assignment', 'question', 'student_submissions_zip']

    def __init__(self, *args, **kwargs):
        lecturer = kwargs.pop('lecturer', None)
        super(SubmissionUploadForm, self).__init__(*args, **kwargs)
        
        self.fields['course_group'].queryset = CourseGroup.objects.filter(lecturer=lecturer)


        # Initialize assignment and question querysets
        self.fields['assignment'].queryset = Assignment.objects.none()
        self.fields['question'].queryset = Question.objects.none()

        if 'course_group' in self.data:
            try:
                course_group_id = self.data.get('course_group')
                self.fields['assignment'].queryset = Assignment.objects.filter(
                    course_group=course_group_id,
                )
            except (ValueError, TypeError):
                pass

        if 'assignment' in self.data:
            try:
                assignment_id = self.data.get('assignment')
                self.fields['question'].queryset = Question.objects.filter(
                    assignment__assignment_code=assignment_id,
                )
            except (ValueError, TypeError):
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        course_group = cleaned_data.get('course_group')
        assignment = cleaned_data.get('assignment')
        question = cleaned_data.get('question')

        if not assignment and not course_group and not question:
            raise forms.ValidationError("Fill in all fields")

        if question and assignment:
            if question.assignment != assignment:
                raise forms.ValidationError("Selected question does not belong to the selected assignment.")

        if assignment and course_group:
            if not assignment.course_group.filter(pk=course_group.class_code).exists():
                raise forms.ValidationError("Selected assignment does not belong to the selected course group.")

        if question and assignment:
            if SubmissionBatch.objects.filter(
                course_group=course_group,
                assignment=assignment,
                question=question
                ).exists():
                raise forms.ValidationError("There is already a submission for this quesiton")
#####################################################################################################
class AllModelSolutionForm(forms.ModelForm):
    class Meta:
        model = ModelSolution
        fields = ['model_solution_all_solutions']
        widgets = {
            'model_solution_all_solutions': forms.Textarea(attrs={'class': 'code-editor'})
        }

class ActualScoreForm(forms.Form):
    actual_score = forms.FloatField(
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control form-control-sm',
                'style': 'border: 1px solid #000;margin-bottom: 5px;',
                'min': '0'
                }
            )
        )
###############################################################################################
class DashboardFilterForm(forms.ModelForm):

    class Meta:
        model = SubmissionBatch
        fields = ['assignment', 'question','course_group']

    def __init__(self, *args, **kwargs):
        lecturer = kwargs.pop('lecturer', None)
        super(DashboardFilterForm, self).__init__(*args, **kwargs)
        
        self.fields['course_group'].queryset = CourseGroup.objects.filter(lecturer=lecturer)


        # Initialize assignment and question querysets
        self.fields['assignment'].queryset = Assignment.objects.none()
        self.fields['question'].queryset = Question.objects.none()

        if 'course_group' in self.data:
            try:
                course_group_id = self.data.get('course_group')
                self.fields['assignment'].queryset = Assignment.objects.filter(
                    course_group=course_group_id,
                )
            except (ValueError, TypeError):
                pass

        if 'assignment' in self.data:
            try:
                assignment_id = self.data.get('assignment')
                self.fields['question'].queryset = Question.objects.filter(
                    assignment__assignment_code=assignment_id,
                )
            except (ValueError, TypeError):
                pass
    def validate_unique(self):
        # Skip the uniqueness validation for the form
        pass

    def clean(self):
        cleaned_data = super().clean()
        course_group = cleaned_data.get('course_group')
        assignment = cleaned_data.get('assignment')
        question = cleaned_data.get('question')

        if not assignment and not course_group and not question:
            raise forms.ValidationError("Fill in all fields")

        if question and assignment:
            if question.assignment != assignment:
                raise forms.ValidationError("Selected question does not belong to the selected assignment.")

        if assignment and course_group:
            if not assignment.course_group.filter(pk=course_group.class_code).exists():
                raise forms.ValidationError("Selected assignment does not belong to the selected course group.")

        # if question and assignment:
        #     if SubmissionBatch.objects.filter(
        #         course_group=course_group,
        #         assignment=assignment,
        #         question=question
        #         ).exists():
        #         raise forms.ValidationError("There is already a submission for this quesiton")

