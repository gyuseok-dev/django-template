from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Soft Delete를 지원하는 커스텀 매니저
    기본 쿼리셋은 deleted_at이 None인 데이터만 조회
    """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """삭제된 데이터를 포함한 전체 데이터 조회"""
        return super().get_queryset()

    def deleted_only(self):
        """삭제된 데이터만 조회"""
        return super().get_queryset().filter(deleted_at__isnull=False)


class BaseModel(models.Model):
    """
    모든 모델의 기본 추상 클래스
    - 생성/수정/삭제 시간 추적
    - Soft Delete 지원
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성 일시"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 일시"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="삭제 일시"
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # 모든 객체 조회용 (삭제된 것 포함)

    class Meta:
        abstract = True

    def soft_delete(self):
        """Soft delete: deleted_at에 현재 시간 설정"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        """삭제된 객체 복원"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    def is_deleted(self):
        """삭제 여부 확인"""
        return self.deleted_at is not None
