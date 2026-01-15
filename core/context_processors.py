"""Context Processors for Hospital Selection"""


def hospital_context(request):
    """병원 선택 관련 컨텍스트"""
    if not request.user.is_authenticated:
        return {}

    from hospital.models import Hospital

    # 현재 선택된 병원
    selected_hospital_id = request.session.get("selected_hospital_id")
    selected_hospital = None
    if selected_hospital_id:
        try:
            selected_hospital = Hospital.objects.get(id=selected_hospital_id)
        except Hospital.DoesNotExist:
            pass

    # 사용 가능한 병원 목록
    if request.user.can_access_all_hospitals():
        # 슈퍼유저 또는 대표: 모든 활성 병원
        available_hospitals = Hospital.objects.filter(is_active=True).order_by(
            "name"
        )
    else:
        # 일반 사용자: 연결된 병원만
        available_hospitals = request.user.hospitals.filter(
            is_active=True
        ).order_by("name")

    return {
        "selected_hospital": selected_hospital,
        "available_hospitals": available_hospitals,
    }
