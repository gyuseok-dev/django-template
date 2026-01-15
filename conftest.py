"""pytest configuration for Django tests"""

import os

# Django 설정 모듈을 먼저 설정 (settings 접근 전에 필요)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()

import pytest
from django.conf import settings


def pytest_configure(config):
    """Configure Django settings for tests with PostgreSQL (test-db on port 5433)"""
    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "test_postgres"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5433"),
        }
    }

    # Set DEBUG=True for tests to avoid manifest requirements
    settings.DEBUG = True

    # Disable whitenoise manifest storage for tests
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    settings.STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    # Remove debug_toolbar from middleware if present (causes staticfiles wrapper issues)
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if "debug_toolbar" not in m
    ]

    # Remove debug_toolbar from installed apps if present
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if "debug_toolbar" not in app
    ]


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests automatically"""
    pass


@pytest.fixture(autouse=True)
def disable_static_manifest():
    """Disable static files manifest for tests"""
    original_storage = settings.STATICFILES_STORAGE
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    yield
    settings.STATICFILES_STORAGE = original_storage
