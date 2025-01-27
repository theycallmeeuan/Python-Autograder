from django.apps import AppConfig


class GradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "grading"

    def ready(self):
        import grading.signals
        #import grading.dash_apps.AutograderAnalyticsDashboard
