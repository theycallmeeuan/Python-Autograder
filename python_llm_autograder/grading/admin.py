from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Lecturer,CourseGroup,Assignment,Question,ModelSolution,StudentSubmission,SubmissionBatch
# Register your models here.


from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import Lecturer

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = Lecturer
    list_display = ["email", "username",]

admin.site.register(Lecturer, CustomUserAdmin)
admin.site.register(CourseGroup)
admin.site.register(Assignment)
admin.site.register(Question)
admin.site.register(ModelSolution)
admin.site.register(StudentSubmission)
admin.site.register(SubmissionBatch)

