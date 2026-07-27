from django.apps import AppConfig

class TrustScoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.trust_scores'

    def ready(self):
        import apps.trust_scores.signals
