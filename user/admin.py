from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """커스텀 User 모델용 Admin (Unfold 스타일)"""

    # Unfold 폼 적용
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    # 목록 페이지
    list_display = [
        "username",
        "name",
        "phone",
        "email",
        "is_staff",
        "is_active",
        "date_joined",
    ]

    list_filter = list(BaseUserAdmin.list_filter) + ["name"]
    search_fields = ("username", "name", "phone", "email")

    # 상세 페이지 필드셋 (비밀번호 암호화 자동 적용)
    fieldsets = list(BaseUserAdmin.fieldsets or []) + [
        ("추가 정보", {"fields": ("name", "phone")})
    ]

    # 사용자 추가 페이지
    add_fieldsets = list(BaseUserAdmin.add_fieldsets or []) + [
        ("추가 정보", {"fields": ("name", "phone")})
    ]

    # 슈퍼유저만 접근 가능
    def has_module_permission(self, request):
        """슈퍼유저만 사이드바에 표시"""
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """슈퍼유저만 조회 가능"""
        return request.user.is_superuser

    def has_add_permission(self, request):
        """슈퍼유저만 추가 가능"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """슈퍼유저만 수정 가능"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """슈퍼유저만 삭제 가능"""
        return request.user.is_superuser


# 기존 Group unregister 후 Unfold 스타일로 재등록
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Group Admin (Unfold 스타일, 슈퍼유저 전용)"""

    # 슈퍼유저만 접근 가능
    def has_module_permission(self, request):
        """슈퍼유저만 사이드바에 표시"""
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """슈퍼유저만 조회 가능"""
        return request.user.is_superuser

    def has_add_permission(self, request):
        """슈퍼유저만 추가 가능"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """슈퍼유저만 수정 가능"""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """슈퍼유저만 삭제 가능"""
        return request.user.is_superuser
