"""Core URL patterns"""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("select-hospital/", views.select_hospital, name="select_hospital"),
]
