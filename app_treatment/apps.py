from django.apps import AppConfig

class ApHrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_treatment'

    def ready(self):
        import app_treatment.signals  