from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    커스텀 User 모델
    """

    name = models.CharField(max_length=150, blank=True, default="", verbose_name="이름")
    phone = models.CharField(max_length=15, blank=True, default="")

    # is_staff 기본값을 True로 설정 (모든 사용자가 Admin 접근 가능)
    is_staff = models.BooleanField(default=True)

    # 병원 관계 추가 (N:M)
    hospitals = models.ManyToManyField(
        "hospital.Hospital",
        related_name="users",
        blank=True,
        verbose_name="소속 병원",
    )

    class Meta:
        db_table = "user"  # ✅ 테이블명을 'user'로! Create your models here.

    def is_representative(self):
        """대표 권한 확인 - 모든 병원 접근 가능"""
        return self.groups.filter(name="대표").exists()

    def is_manager(self):
        """관리자 권한 확인 - 연결된 병원만 접근 가능"""
        return self.groups.filter(name="관리자").exists()

    def can_access_all_hospitals(self):
        """모든 병원 접근 가능 여부 (슈퍼유저 또는 대표)"""
        return self.is_superuser or self.is_representative()
