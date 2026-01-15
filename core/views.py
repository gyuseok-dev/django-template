"""Core views for hospital selection"""

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from hospital.models import Hospital

if TYPE_CHECKING:
    from user.models import User


@login_required
@require_POST
def select_hospital(request: HttpRequest) -> HttpResponse:
    """병원 선택"""
    hospital_id = request.POST.get("hospital_id")
    user: User = request.user  # type: ignore[assignment]

    if not hospital_id:
        from django.contrib import messages

        messages.error(request, "병원 ID가 필요합니다.")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    try:
        hospital = Hospital.objects.get(id=hospital_id, is_active=True)

        # 권한 확인
        if not user.can_access_all_hospitals():
            # 일반 사용자는 연결된 병원만 선택 가능
            if not user.hospitals.filter(id=hospital_id).exists():
                from django.contrib import messages

                messages.error(request, "이 병원에 접근할 수 없습니다.")
                return redirect(request.META.get("HTTP_REFERER", "/admin/"))

        # 세션에 저장
        request.session["selected_hospital_id"] = hospital.id

        # 이전 페이지로 리다이렉트
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))

    except Hospital.DoesNotExist:
        from django.contrib import messages

        messages.error(request, "병원을 찾을 수 없습니다.")
        return redirect(request.META.get("HTTP_REFERER", "/admin/"))
