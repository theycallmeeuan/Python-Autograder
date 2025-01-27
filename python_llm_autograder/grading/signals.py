from django.db.models.signals import post_delete
from django.dispatch import receiver
import os,shutil

from .models import Question, ModelSolution, SubmissionBatch

# Utility function to delete files
def delete_files(instance, field_names):
    directories_to_delete = set()
    for field_name in field_names:
        file_field = getattr(instance, field_name)
        if file_field and hasattr(file_field, 'delete'):
            # Get the file's full path
            file_path = file_field.path
            # Delete the file
            file_field.delete(save=False)
            # Collect directories to delete
            dir_path = os.path.dirname(file_path)
            directories_to_delete.add(dir_path)
    
        # delete the directories
        for dir_path in directories_to_delete:
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f"Directory:{dir_path} dosen't exist")
                pass

### Signal Receivers

@receiver(post_delete, sender=Question)
def delete_question_files(sender, instance, **kwargs):
    field_names = ['grading_rubric', 'question_file','test_cases_file']
    delete_files(instance, field_names)
    

@receiver(post_delete, sender=ModelSolution)
def delete_modelsolution_files(sender, instance, **kwargs):
    field_names = ['model_solution', 'ast_python_code']
    delete_files(instance, field_names)

@receiver(post_delete, sender=SubmissionBatch)
def delete_submissionbatch_files(sender, instance, **kwargs):
    field_names = ['student_submissions_zip']
    delete_files(instance, field_names)
