"""멀티테넌시 미들웨어"""

from .managers import clear_current_hospital, set_current_hospital


class TenantMiddleware:
    """멀티테넌시 미들웨어 - 요청마다 현재 병원 설정"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 요청 시작 시 병원 설정
        if request.user.is_authenticated:
            # 모든 사용자: 세션에서 병원 선택
            hospital_id = request.session.get("selected_hospital_id")

            if hospital_id:
                from hospital.models import Hospital

                try:
                    hospital = Hospital.objects.get(id=hospital_id)
                    set_current_hospital(hospital)
                except Hospital.DoesNotExist:
                    # 병원이 삭제됐거나 잘못된 ID - 세션 초기화
                    del request.session["selected_hospital_id"]
            else:
                # 세션에 병원 선택이 없으면
                if request.user.can_access_all_hospitals():
                    # 슈퍼유저 또는 대표: 연결된 병원이 없으면 첫 번째 병원 자동 선택
                    from hospital.models import Hospital

                    selected_hospital: Hospital | None = None
                    if request.user.hospitals.exists():
                        selected_hospital = request.user.hospitals.first()
                    else:
                        selected_hospital = Hospital.objects.filter(
                            is_active=True
                        ).first()

                    if selected_hospital:
                        request.session["selected_hospital_id"] = (
                            selected_hospital.id
                        )
                        set_current_hospital(selected_hospital)
                else:
                    # 관리자 또는 일반 사용자: 첫 번째 병원 자동 선택 & 세션에 저장
                    if request.user.hospitals.exists():
                        user_hospital = request.user.hospitals.first()
                        if user_hospital:
                            request.session["selected_hospital_id"] = (
                                user_hospital.id
                            )
                            set_current_hospital(user_hospital)

        response = self.get_response(request)

        # 요청 종료 시 병원 정보 초기화
        clear_current_hospital()

        return response
