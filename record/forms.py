from datetime import date

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Fieldset, Layout
from django import forms

from hospital.models import Hospital, Room

from .models import ManualRecord


class ManualRecordForm(forms.ModelForm):
    """마감일지 수동 입력 폼"""

    class Meta:
        model = ManualRecord
        fields = [
            "hospital",
            "date",
            "medical_record_file",
            "visit_source_file",
        ]

    def __init__(self, *args, **kwargs):
        # hospital_id를 kwargs에서 추출
        hospital_id = kwargs.pop("hospital_id", None)

        super().__init__(*args, **kwargs)

        # hospital_id를 인스턴스 변수로 저장 (save 시 사용)
        self._hospital_id = hospital_id
        self._hospital_name = None

        # 병원 필드 설정 (수정 불가, 기본값으로 선택된 병원)
        if hospital_id:
            try:
                hospital = Hospital.objects.get(id=hospital_id)
                self._hospital_name = hospital.name
                self.fields["hospital"].initial = hospital
                self.fields["hospital"].widget = forms.HiddenInput()
                self.fields["hospital"].required = True
            except Hospital.DoesNotExist:
                pass

        # 기존 인스턴스 수정 시에도 병원 이름 저장
        if self.instance.pk and self.instance.hospital:
            self._hospital_name = self.instance.hospital.name

        # 새로 추가하는 경우(인스턴스가 없는 경우) 오늘 날짜를 기본값으로 설정
        if not self.instance.pk:
            self.fields["date"].initial = date.today()

        # 활성화된 Room별 모든 필드 동적 생성
        active_rooms = Room.objects.filter(is_active=True)

        # 필드 목록 정의
        room_fields = [
            ("급여", "급여"),
            ("비급여", "비급여"),
            ("조합청구액", "조합청구액"),
            ("단위절사", "100/100미만 총액"),
            ("전액본인", "장애인기금/전액본인"),
            ("미수_발생금액", "미수발생 금액"),
            ("미수_발생건수", "미수발생 건수"),
            ("미수_입금금액", "미수입금 금액"),
            ("미수_입금건수", "미수입금 건수"),
        ]

        for room in active_rooms:
            # 기존 RoomRecord 가져오기
            room_record = None
            if self.instance.pk:
                try:
                    room_record = self.instance.room_records.get(room=room)
                except self.instance.room_records.model.DoesNotExist:
                    pass

            # 각 필드 생성
            for field_key, field_label in room_fields:
                field_name = f"room_{room.id}_{field_key}"
                self.fields[field_name] = forms.IntegerField(
                    label=field_label,
                    initial=0,
                    required=False,
                    widget=forms.NumberInput(attrs={"class": "form-control"}),
                )

                # 기존 값이 있으면 초기값 설정
                if room_record:
                    self.fields[field_name].initial = getattr(room_record, field_key, 0)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "space-y-6"
        self.helper.attrs = {"enctype": "multipart/form-data"}

        # JavaScript 탭 UI 생성
        if active_rooms:
            # 탭 버튼 생성
            tab_buttons = ['<div class="flex gap-2 mb-4 border-b">']
            for idx, room in enumerate(active_rooms):
                active_class = "bg-blue-500 text-white" if idx == 0 else "bg-gray-200 text-gray-700 hover:bg-gray-300"
                tab_buttons.append(f"""
                    <button type="button"
                            class="room-tab px-4 py-2 rounded-t-lg transition-colors {active_class}"
                            data-room-id="{room.id}"
                            onclick="switchRoomTab({room.id})">
                        {room.name}
                    </button>
                """)
            tab_buttons.append("</div>")

            # 각 탭 패널 생성
            tab_panes = []
            for idx, room in enumerate(active_rooms):
                display_style = "block" if idx == 0 else "none"

                tab_panes.append(
                    HTML(f"""
                    <div class="room-tab-pane" id="room-pane-{room.id}" style="display: {display_style};">
                        <h5 class="text-lg font-semibold mb-3">{room.name} 수납 정보 입력</h5>
                """)
                )

                # 모든 필드 추가
                for field_key, _ in room_fields:
                    field_name = f"room_{room.id}_{field_key}"
                    tab_panes.append(Field(field_name))

                tab_panes.append(HTML("</div>"))

            # JavaScript 코드
            tab_script = """
                <script>
                function switchRoomTab(roomId) {
                    // 모든 탭 버튼 비활성화
                    document.querySelectorAll('.room-tab').forEach(btn => {
                        btn.classList.remove('bg-blue-500', 'text-white');
                        btn.classList.add('bg-gray-200', 'text-gray-700', 'hover:bg-gray-300');
                    });

                    // 클릭한 탭 버튼 활성화
                    const activeBtn = document.querySelector(`[data-room-id="${roomId}"]`);
                    if (activeBtn) {
                        activeBtn.classList.remove('bg-gray-200', 'text-gray-700', 'hover:bg-gray-300');
                        activeBtn.classList.add('bg-blue-500', 'text-white');
                    }

                    // 모든 탭 패널 숨기기
                    document.querySelectorAll('.room-tab-pane').forEach(pane => {
                        pane.style.display = 'none';
                    });

                    // 선택한 탭 패널 표시
                    const activePane = document.getElementById(`room-pane-${roomId}`);
                    if (activePane) {
                        activePane.style.display = 'block';
                    }
                }
                </script>
            """

            room_payment_section = [HTML("".join(tab_buttons)), *tab_panes, HTML(tab_script)]
        else:
            room_payment_section = [HTML("<p>등록된 진료실이 없습니다.</p>")]

        # 병원 이름 표시 HTML 생성
        hospital_display_html = ""
        if self._hospital_name:
            hospital_display_html = f"""
            <div class="mb-3">
                <label class="form-label font-semibold">병원</label>
                <div class="p-2 bg-gray-100 rounded border border-gray-300">
                    {self._hospital_name}
                </div>
            </div>
            """

        self.helper.layout = Layout(
            Fieldset(
                "기본 정보",
                HTML(hospital_display_html),
                Field("hospital"),  # Hidden field
                Field("date"),
                Field("medical_record_file"),
                Field("visit_source_file"),
                css_class="mb-4",
            ),
            Fieldset(
                "진료실별 수납 정보 입력",
                *room_payment_section,
                css_class="mb-4",
            ),
        )

        # 기존 인스턴스가 있는 경우 연동된 데이터 표시
        if self.instance.pk:
            patient_count = self.instance.patient_records.count()
            visit_count = self.instance.visit_channel_records.count()

            self.helper.layout.append(
                Fieldset(
                    "연동된 데이터",
                    HTML(f'<div class="mb-3"><strong>환자 진료 기록 수:</strong> {patient_count:,}건</div>'),
                    HTML(f'<div class="mb-3"><strong>내원 경로 기록 수:</strong> {visit_count:,}건</div>'),
                    css_class="mb-4",
                ),
            )

    def clean(self):
        """날짜 중복 체크 (삭제된 레코드 제외, 병원별)"""
        cleaned_data = super().clean()
        if cleaned_data is None:
            return cleaned_data

        date_value = cleaned_data.get("date")

        # disabled 필드는 cleaned_data에 포함되지 않으므로 초기값이나 인스턴스에서 가져옴
        hospital = cleaned_data.get("hospital")
        if not hospital:
            # 새로 생성하는 경우 _hospital_id에서 가져옴
            if hasattr(self, "_hospital_id") and self._hospital_id:
                try:
                    hospital = Hospital.objects.get(id=self._hospital_id)
                except Hospital.DoesNotExist:
                    pass
            # 기존 인스턴스를 수정하는 경우
            elif self.instance.pk and self.instance.hospital:
                hospital = self.instance.hospital

        if date_value is None:
            raise forms.ValidationError("날짜를 입력해주세요.")

        if hospital is None:
            raise forms.ValidationError("병원을 선택해주세요.")

        # 기존 레코드 수정 시에는 자기 자신을 제외
        queryset = ManualRecord.objects.filter(date=date_value, hospital=hospital)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        # 삭제되지 않은 레코드 중 중복이 있는지 확인
        if queryset.exists():
            raise forms.ValidationError(f"{hospital.name}의 {date_value} 날짜의 마감일지가 이미 존재합니다.")

        return cleaned_data

    def save(self, commit=True):
        """ManualRecord 저장 후 RoomRecord 레코드 생성/업데이트"""
        from .models import RoomRecord

        instance = super().save(commit=False)

        # disabled 필드는 cleaned_data에 포함되지 않으므로 명시적으로 설정
        if not instance.hospital_id and hasattr(self, "_hospital_id") and self._hospital_id:
            instance.hospital_id = self._hospital_id

        # commit=True일 때만 여기서 저장
        if commit:
            instance.save()

        # 필드 목록 정의
        room_fields = [
            ("급여", "급여"),
            ("비급여", "비급여"),
            ("조합청구액", "조합청구액"),
            ("단위절사", "100/100미만 총액"),
            ("전액본인", "장애인기금/전액본인"),
            ("미수_발생금액", "미수발생 금액"),
            ("미수_발생건수", "미수발생 건수"),
            ("미수_입금금액", "미수입금 금액"),
            ("미수_입금건수", "미수입금 건수"),
        ]

        def save_room_records():
            """RoomRecord 저장 함수"""
            active_rooms = Room.objects.filter(is_active=True)

            for room in active_rooms:
                # 각 필드 값 가져오기
                defaults = {}
                for field_key, _ in room_fields:
                    field_name = f"room_{room.id}_{field_key}"
                    field_value = self.cleaned_data.get(field_name, 0) or 0
                    defaults[field_key] = field_value

                # RoomRecord 생성 또는 업데이트
                try:
                    RoomRecord.objects.update_or_create(manual_record=instance, room=room, defaults=defaults)
                except Exception as e:
                    print(f"RoomRecord 저장 실패 - Room: {room.name}, Error: {e}")
                    raise

        if commit:
            save_room_records()
            # RoomRecord signal이 자동으로 total_revenue를 계산하고 통계를 업데이트함
        else:
            # commit=False인 경우, save_m2m에 추가
            old_save_m2m = self.save_m2m

            def new_save_m2m():
                old_save_m2m()
                save_room_records()

            self.save_m2m = new_save_m2m  # type: ignore[method-assign]

        return instance
