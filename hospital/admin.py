from django.contrib import admin
from unfold.admin import ModelAdmin

from core.admin import TenantAdminMixin

from .models import Hospital, Room


@admin.register(Hospital)
class HospitalAdmin(ModelAdmin):
    """병원 관리 (슈퍼유저 전용)"""

    list_display = ["name", "code", "phone", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "code"]
    ordering = ["name"]

    fieldsets = (
        (
            "기본 정보",
            {"fields": ("name", "code", "phone", "address", "is_active")},
        ),
    )

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Room)
class RoomAdmin(TenantAdminMixin, ModelAdmin):
    """진료실 관리"""

    list_display = ["hospital", "name", "order", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    ordering = ["order", "name"]

    fieldsets = (
        (
            "기본 정보",
            {"fields": ("hospital", "name", "is_active", "order")},
        ),
    )
