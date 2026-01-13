"""멀티테넌시 지원 Manager 및 QuerySet"""

from threading import local

from django.db import models

# Thread-local storage for current hospital
_thread_locals = local()


def set_current_hospital(hospital):
    """현재 요청의 병원 설정"""
    _thread_locals.hospital = hospital


def get_current_hospital():
    """현재 요청의 병원 조회"""
    return getattr(_thread_locals, "hospital", None)


def clear_current_hospital():
    """현재 요청의 병원 초기화"""
    if hasattr(_thread_locals, "hospital"):
        del _thread_locals.hospital


class TenantQuerySet(models.QuerySet):
    """병원별 필터링 QuerySet"""

    def for_hospital(self, hospital):
        """특정 병원의 데이터만 조회"""
        if hospital:
            return self.filter(hospital=hospital, deleted_at__isnull=True)
        return self.none()

    def for_current_hospital(self):
        """현재 요청 병원의 데이터만 조회"""
        hospital = get_current_hospital()
        return self.for_hospital(hospital)


class TenantManager(models.Manager):
    """병원별 자동 필터링 Manager (SoftDelete 미지원 버전)"""

    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)

        # 현재 병원이 설정되어 있으면 자동 필터링
        hospital = get_current_hospital()
        if hospital:
            return qs.filter(hospital=hospital)

        return qs

    def for_hospital(self, hospital):
        """특정 병원 데이터 조회 (관리자용)"""
        return TenantQuerySet(self.model, using=self._db).for_hospital(hospital)

    def all_hospitals(self):
        """모든 병원 데이터 조회 (슈퍼유저용)"""
        return TenantQuerySet(self.model, using=self._db)


class SoftDeleteTenantManager(models.Manager):
    """병원별 자동 필터링 + Soft Delete Manager"""

    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)

        # Soft Delete 필터링
        qs = qs.filter(deleted_at__isnull=True)

        # 현재 병원이 설정되어 있으면 자동 필터링
        hospital = get_current_hospital()
        if hospital:
            return qs.filter(hospital=hospital)

        return qs

    def for_hospital(self, hospital):
        """특정 병원 데이터 조회 (관리자용)"""
        return TenantQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True).filter(hospital=hospital)

    def all_hospitals(self):
        """모든 병원 데이터 조회 (슈퍼유저용, soft delete만 필터링)"""
        return TenantQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)

    def with_deleted(self):
        """삭제된 데이터를 포함한 전체 데이터 조회"""
        hospital = get_current_hospital()
        qs = TenantQuerySet(self.model, using=self._db)
        if hospital:
            return qs.filter(hospital=hospital)
        return qs

    def deleted_only(self):
        """삭제된 데이터만 조회"""
        hospital = get_current_hospital()
        qs = TenantQuerySet(self.model, using=self._db).filter(deleted_at__isnull=False)
        if hospital:
            return qs.filter(hospital=hospital)
        return qs
