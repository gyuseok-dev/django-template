from django.urls import path

from . import views

app_name = "record"

urlpatterns = [
    # 환자 진료 기록 대시보드
    path("", views.patient_records_dashboard, name="patient_records_dashboard"),
    path(
        "api/patient-monthly-stats/",
        views.patient_monthly_stats_api,
        name="patient_monthly_stats_api",
    ),
    path(
        "api/patient-department-stats/",
        views.patient_department_stats_api,
        name="patient_department_stats_api",
    ),
    path(
        "api/monthly-comparison/",
        views.monthly_comparison_api,
        name="monthly_comparison_api",
    ),
]
