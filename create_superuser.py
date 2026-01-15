# create_superuser.py
import os

import django
from django.contrib.auth import get_user_model

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "hospital_erp.settings"
)  # 프로젝트명 확인!
django.setup()

User = get_user_model()
USERNAME = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
EMAIL = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
PASSWORD = os.environ.get(
    "DJANGO_SUPERUSER_PASSWORD", "admin1234"
)  # 강력한 비번으로 변경 권장

if not User.objects.filter(username=USERNAME).exists():
    print(f"Creating superuser: {USERNAME}")
    User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
else:
    print(f"Superuser {USERNAME} already exists.")
