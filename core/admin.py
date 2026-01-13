"""멀티테넌시 지원 Admin Mixin"""

from .managers import get_current_hospital


class TenantAdminMixin:
    """멀티테넌시 지원 Admin Mixin"""

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # hospital 필드가 없는 모델은 그대로 반환
        if not hasattr(self.model, "hospital"):
            return qs

        if request.user.is_superuser:
            # 슈퍼유저는 선택된 병원 또는 전체
            hospital_id = request.session.get("selected_hospital_id")
            if hospital_id:
                return qs.filter(hospital_id=hospital_id)
            return qs  # 전체 조회
        else:
            # 일반 사용자는 자신의 병원만
            hospital = get_current_hospital()
            if hospital:
                return qs.filter(hospital=hospital)
            return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """FK 필드에 병원 필터 적용"""
        if db_field.name == "hospital":
            if not request.user.is_superuser:
                # 일반 사용자는 자신의 병원만 선택 가능
                kwargs["queryset"] = request.user.hospitals.filter(is_active=True)
            # 슈퍼유저는 모든 병원 선택 가능
        elif hasattr(db_field.related_model, "hospital"):
            # 다른 FK도 병원별 필터링
            hospital = get_current_hospital()
            if hospital and not request.user.is_superuser:
                kwargs["queryset"] = db_field.related_model.objects.filter(hospital=hospital)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        """모델 저장 시 자동으로 병원 설정"""
        if hasattr(obj, "hospital") and not obj.hospital_id:
            hospital = get_current_hospital()
            if hospital:
                obj.hospital = hospital
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """변경 권한 체크"""
        if obj and hasattr(obj, "hospital"):
            if not request.user.is_superuser:
                if obj.hospital not in request.user.hospitals.all():
                    return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """삭제 권한 체크"""
        if obj and hasattr(obj, "hospital"):
            if not request.user.is_superuser:
                if obj.hospital not in request.user.hospitals.all():
                    return False
        return super().has_delete_permission(request, obj)
