from django.apps import AppConfig


class RecordConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "record"
    verbose_name = "진료 기록 관리"

    def ready(self):
        """앱 초기화 시 시그널 등록"""
        import record.signals  # noqa: F401
