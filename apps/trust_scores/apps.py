from django.apps import AppConfig

class TrustScoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trust_scores'

    def ready(self):
        import trust_scores.signals
