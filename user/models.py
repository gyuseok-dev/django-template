from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    커스텀 User 모델
    """
    name = models.CharField(max_length=150, unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        db_table = 'user'  # ✅ 테이블명을 'user'로! Create your models here.
