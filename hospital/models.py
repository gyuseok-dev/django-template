from django.db import models

from core.models import BaseModel


class Hospital(BaseModel):
    """병원 모델 - 멀티테넌시의 핵심"""

    name = models.CharField(max_length=200, unique=True, verbose_name="병원명")
    code = models.CharField(max_length=50, unique=True, verbose_name="병원 코드", db_index=True)

    # 병원 정보
    address = models.TextField(blank=True, verbose_name="주소")
    phone = models.CharField(max_length=20, blank=True, verbose_name="대표 전화")

    is_active = models.BooleanField(default=True, verbose_name="활성화")

    class Meta:
        verbose_name = "병원"
        verbose_name_plural = "병원"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Room(BaseModel):
    """진료실"""

    hospital = models.ForeignKey(
        "Hospital",
        on_delete=models.CASCADE,
        related_name="rooms",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    name = models.CharField(max_length=100, verbose_name="진료실명", db_index=True)

    is_active = models.BooleanField(
        default=True, verbose_name="활성화", help_text="비활성화 시 급여 입력에서 제외됩니다"
    )

    order = models.IntegerField(default=0, verbose_name="정렬 순서", help_text="탭에 표시될 순서")

    class Meta:
        verbose_name = "진료실"
        verbose_name_plural = "진료실"
        ordering = ["order", "name"]
        unique_together = [["hospital", "name"]]  # 병원 내에서만 진료실명 고유

    def __str__(self):
        return self.name
