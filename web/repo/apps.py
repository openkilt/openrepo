from django.apps import AppConfig


class RepoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repo'

    def ready(self):
        import repo.signals