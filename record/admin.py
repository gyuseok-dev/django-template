from dateutil.relativedelta import relativedelta
from django.contrib import admin
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import DateTimeWidget
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import RangeDateFilter
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from core.admin import TenantAdminMixin

from .forms import ManualRecordForm
from .models import (
    DailyStatistics,
    GlobalStatistics,
    ManualRecord,
    MonthlyStatistics,
    PatientRecord,
    VisitChannelRecord,
)


class ManualRecordMonthFilter(admin.SimpleListFilter):
    """마감일지 월별 필터"""

    title = "마감일지 월"
    parameter_name = "manual_record_month"

    def lookups(self, request, model_admin):
        """필터 옵션 생성 - 최근 12개월"""
        months = []
        current_date = timezone.now().date()

        for i in range(12):
            date = current_date - relativedelta(months=i)
            year_month = date.strftime("%Y-%m")
            display_text = date.strftime("%Y년 %m월")
            months.append((year_month, display_text))

        return months

    def queryset(self, request, queryset):
        """선택된 월로 필터링"""
        value = self.value()
        if value:
            year, month = value.split("-")
            return queryset.filter(
                manual_record__date__year=year, manual_record__date__month=month
            )
        return queryset


class PatientRecordResource(resources.ModelResource):
    """환자 진료 기록 Import/Export 리소스"""

    chart_number = fields.Field(
        column_name="챠트번호",
        attribute="chart_number",
    )

    patient_name = fields.Field(
        column_name="수진자명",
        attribute="patient_name",
    )
    patient_id = fields.Field(
        column_name="주민번호",
        attribute="patient_id",
    )
    insurance_type = fields.Field(
        column_name="보험유형",
        attribute="insurance_type",
    )
    room = fields.Field(
        column_name="진료과",
        attribute="room",
    )
    doctor_name = fields.Field(
        column_name="담당의",
        attribute="doctor_name",
    )
    visit_type = fields.Field(
        column_name="초/재",
        attribute="visit_type",
    )

    visit_at = fields.Field(
        column_name="내원일",
        attribute="visit_at",
        widget=DateTimeWidget(format="%Y%m%d%H%M"),
    )

    class Meta:
        model = PatientRecord
        fields = (
            "chart_number",
            "patient_name",
            "patient_id",
            "insurance_type",
            "room",
            "doctor_name",
            "visit_type",
            "visit_at",
            "manual_record",
        )
        export_order = fields
        import_id_fields = ["chart_number", "visit_at"]
        skip_unchanged = True
        report_skipped = True

    def before_import(self, dataset, **kwargs):
        """
        헤더 행을 찾아서 그 이전 행들을 제거
        '차트번호' 또는 'chart_number' 헤더가 있는 행을 찾습니다
        """
        header_keywords = [
            "차트번호",
            "chart_number",
            "수진자명",
            "patient_name",
            "챠트번호",
        ]
        header_row_index = None

        # 헤더 행 찾기
        for idx, row in enumerate(dataset):
            row_values = [
                str(cell).strip().lower() if cell else "" for cell in row
            ]
            # 헤더 키워드 중 하나라도 있으면 헤더 행으로 판단
            if any(
                keyword.lower() in " ".join(row_values)
                for keyword in header_keywords
            ):
                header_row_index = idx
                break

        # 헤더 행을 찾았다면, 그 이전 행들 삭제
        if header_row_index is not None:
            # 헤더 행을 새로운 헤더로 설정
            dataset.headers = [
                str(cell).strip() if cell else ""
                for cell in dataset[header_row_index]
            ]
            # 헤더 이전 행들 + 헤더 행 삭제
            del dataset[: header_row_index + 1]

        # 빈 행 제거 (모든 셀이 비어있는 행)
        rows_to_remove = []
        for idx, row in enumerate(dataset):
            # 모든 셀이 비어있거나 None이면 제거
            if all(not cell or str(cell).strip() == "" for cell in row):
                rows_to_remove.append(idx)

        # 역순으로 제거
        for idx in reversed(rows_to_remove):
            del dataset[idx]

        return super().before_import(dataset, **kwargs)

    def before_import_row(self, row, row_number=None, **kwargs):
        """각 행을 import하기 전에 manual_record 설정"""
        manual_record = kwargs.get("manual_record")
        if manual_record:
            row["manual_record"] = manual_record.id
        return super().before_import_row(row, **kwargs)


class VisitChannelRecordResource(resources.ModelResource):
    """내원 경로 Import/Export 리소스"""

    chart_number = fields.Field(
        column_name="차트번호",
        attribute="chart_number",
    )

    patient_name = fields.Field(
        column_name="이름",
        attribute="patient_name",
    )
    insurance_type = fields.Field(
        column_name="보험유형",
        attribute="insurance_type",
    )
    room = fields.Field(
        column_name="진료과목",
        attribute="room",
    )
    doctor_name = fields.Field(
        column_name="담당의",
        attribute="doctor_name",
    )
    visit_type = fields.Field(
        column_name="초재진구분",
        attribute="visit_type",
    )
    channel = fields.Field(
        column_name="내원경로",
        attribute="channel",
    )

    visit_at = fields.Field(
        column_name="내원날짜",
        attribute="visit_at",
        widget=DateTimeWidget(format="%Y%m%d%H%M"),
    )

    class Meta:
        model = VisitChannelRecord
        fields = (
            "chart_number",
            "patient_name",
            "insurance_type",
            "room",
            "doctor_name",
            "visit_type",
            "channel",
            "visit_at",
            "manual_record",
        )
        export_order = fields
        import_id_fields = ["chart_number", "visit_at"]  # 중복체크
        skip_unchanged = True
        report_skipped = True

    def before_import(self, dataset, **kwargs):
        """
        통계 행 제거
        "【 소 계 】", "【 총 계 】"로 시작하는 행들을 제거합니다
        """
        # 통계 행 키워드
        skip_keywords = ["【 소 계 】", "【 총 계 】", "소계", "총계"]

        # 제거할 행의 인덱스를 저장
        rows_to_remove = []

        for idx, row in enumerate(dataset):
            # 첫 번째 셀 확인
            if row and len(row) > 0:
                first_cell = str(row[0]).strip() if row[0] else ""
                # 통계 행이면 제거 대상에 추가
                if any(keyword in first_cell for keyword in skip_keywords):
                    rows_to_remove.append(idx)

            # 빈 행도 제거 (모든 셀이 비어있는 행)
            if all(not cell or str(cell).strip() == "" for cell in row):
                rows_to_remove.append(idx)

        # 역순으로 제거 (인덱스가 변경되지 않도록)
        for idx in reversed(rows_to_remove):
            del dataset[idx]

        return super().before_import(dataset, **kwargs)

    def before_import_row(self, row, row_number=None, **kwargs):
        """각 행을 import하기 전에 manual_record 설정"""
        manual_record = kwargs.get("manual_record")
        if manual_record:
            row["manual_record"] = manual_record.id
        return super().before_import_row(row, **kwargs)


@admin.register(PatientRecord)
class PatientRecordAdmin(TenantAdminMixin, ModelAdmin, ImportExportModelAdmin):
    """환자 진료 기록 Admin"""

    # Import/Export 설정
    resource_class = PatientRecordResource
    import_form_class = ImportForm
    export_form_class = ExportForm

    # 목록 페이지 설정
    list_display = [
        "hospital",
        "chart_number",
        "patient_name",
        "get_masked_patient_id",
        "insurance_type",
        "room",
        "visit_type",
        "doctor_name",
        "visit_at",
        "created_at",
    ]

    list_filter_submit = True
    list_filter = [
        ("manual_record__date", RangeDateFilter),
        ManualRecordMonthFilter,
        "room",
        "visit_type",
        "insurance_type",
        "visit_at",
    ]

    search_fields = [
        "patient_name",
    ]

    # 읽기 전용 필드
    readonly_fields = [
        "get_masked_patient_id",
        "created_at",
        "updated_at",
    ]

    # 정렬
    ordering = ["-created_at", "patient_name"]

    # 한 페이지에 표시할 항목 수
    list_per_page = 50

    @admin.display(description="주민번호")
    def get_masked_patient_id(self, obj):
        """주민번호 마스킹 표시"""
        return obj.masked_patient_id

    # Admin 인터페이스 사용자 정의
    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "chart_number",
                    "patient_name",
                    "patient_id",
                    "get_masked_patient_id",
                )
            },
        ),
        (
            "진료 정보",
            {
                "fields": (
                    "room",
                    "insurance_type",
                    "visit_type",
                    "doctor_name",
                    "visit_at",
                )
            },
        ),
        (
            "메타 정보",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(VisitChannelRecord)
class VisitChannelRecordAdmin(
    TenantAdminMixin, ModelAdmin, ImportExportModelAdmin
):
    """내원 경로 Admin"""

    # Import/Export 설정
    resource_class = VisitChannelRecordResource
    import_form_class = ImportForm
    export_form_class = ExportForm

    # 목록 페이지 설정
    list_display = [
        "hospital",
        "chart_number",
        "patient_name",
        "channel",
        "insurance_type",
        "room",
        "visit_type",
        "doctor_name",
        "visit_at",
        "created_at",
    ]

    list_filter_submit = True
    list_filter = [
        ("manual_record__date", RangeDateFilter),
        ManualRecordMonthFilter,
        "channel",
        "room",
        "visit_type",
        "insurance_type",
        "visit_at",
    ]

    search_fields = [
        "patient_name",
        "channel",
    ]

    # 읽기 전용 필드
    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    # 정렬
    ordering = ["-created_at", "patient_name"]

    # 한 페이지에 표시할 항목 수
    list_per_page = 50

    # Admin 인터페이스 사용자 정의
    fieldsets = (
        ("기본 정보", {"fields": ("chart_number", "patient_name")}),
        ("내원 정보", {"fields": ("channel", "visit_at")}),
        (
            "진료 정보",
            {"fields": ("room", "insurance_type", "visit_type", "doctor_name")},
        ),
        (
            "메타 정보",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ManualRecord)
class ManualRecordAdmin(TenantAdminMixin, ModelAdmin):
    """마감일지 수동 입력 Admin"""

    # Crispy Forms 사용
    form = ManualRecordForm

    # 액션 목록
    actions = ["recalculate_statistics"]

    # 목록 페이지 설정
    list_display = [
        "hospital",
        "date",
        "created_at",
    ]

    list_filter = [
        "date",
    ]

    search_fields = [
        "date",
    ]

    # 읽기 전용 필드
    readonly_fields = [
        "get_patient_record_count",
        "get_visit_channel_record_count",
        "created_at",
        "updated_at",
    ]

    # 정렬
    ordering = ["-date"]

    # 한 페이지에 표시할 항목 수
    list_per_page = 30

    def get_form(self, request, obj=None, **kwargs):
        """폼에 hospital_id 전달"""
        form_class = super().get_form(request, obj, **kwargs)

        class FormWithHospitalId(form_class):  # type: ignore[valid-type,misc]
            def __init__(self, *args, **kwargs):
                # 세션에서 selected_hospital_id 가져오기
                hospital_id = request.session.get("selected_hospital_id")
                super().__init__(*args, hospital_id=hospital_id, **kwargs)

        return FormWithHospitalId

    def get_queryset(self, request):
        """삭제되지 않은 레코드만 표시"""
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    @admin.display(description="환자 진료 기록 수")
    def get_patient_record_count(self, obj):
        """연동된 환자 진료 기록 개수"""
        if obj.pk:
            count = obj.patient_records.count()
            return f"{count:,}건"
        return "0건"

    @admin.display(description="내원 경로 기록 수")
    def get_visit_channel_record_count(self, obj):
        """연동된 내원 경로 기록 개수"""
        if obj.pk:
            count = obj.visit_channel_records.count()
            return f"{count:,}건"
        return "0건"

    def save_model(self, request, obj: ManualRecord, form, change):
        """
        모델 저장 시 파일이 있으면 자동으로 import 수행
        - medical_record_file: PatientRecord import
        - visit_source_file: VisitChannelRecord import

        트랜잭션으로 묶여서 에러 발생 시 전체 롤백됩니다.
        """
        with transaction.atomic():
            # 먼저 ManualRecord 저장
            super().save_model(request, obj, form, change)

            # 저장 후 total_revenue 계산 및 업데이트
            obj.total_revenue = obj.calculate_total_revenue()
            obj.save(update_fields=["total_revenue"])

            needs_statistics_update = False

            # medical_record_file 처리 (통계 갱신은 스킵)
            if obj.medical_record_file and hasattr(
                obj.medical_record_file, "file"
            ):
                self._import_medical_records(request, obj, skip_statistics=True)
                needs_statistics_update = True

            # visit_source_file 처리 (통계 갱신은 스킵)
            if obj.visit_source_file and hasattr(obj.visit_source_file, "file"):
                self._import_visit_channel_records(
                    request, obj, skip_statistics=True
                )
                needs_statistics_update = True

            # 모든 import 완료 후 통계를 한 번만 갱신
            if needs_statistics_update:
                from record.signals import update_daily_statistics

                update_daily_statistics(ManualRecord, obj, created=False)

    def _import_medical_records(self, request, obj, skip_statistics=False):
        """환자 진료 기록 파일 import - 최적화 버전 (삭제 후 bulk_create)"""
        import time

        from tablib import Dataset

        timing = {}  # 성능 측정용

        try:
            start_time = time.time()

            # 1단계: 파일 읽기 및 파싱
            dataset = Dataset()
            file_content = obj.medical_record_file.read()

            file_name = obj.medical_record_file.name
            if file_name.endswith(".xlsx"):
                dataset.load(file_content, format="xlsx")
            elif file_name.endswith(".xls"):
                dataset.load(file_content, format="xls")
            else:
                self.message_user(
                    request,
                    "지원하지 않는 파일 형식입니다. .xlsx 또는 .xls 파일을 업로드해주세요.",
                    level="error",
                )
                return

            timing["file_read"] = time.time() - start_time

            # 2단계: 데이터 전처리 (before_import로 헤더 정리)
            step_time = time.time()
            resource = PatientRecordResource()
            resource.before_import(dataset, manual_record=obj)
            timing["preprocessing"] = time.time() - step_time

            # 3단계: 기존 데이터 삭제
            step_time = time.time()
            deleted_count = obj.patient_records.all().delete()[0]
            timing["delete"] = time.time() - step_time

            # 4단계: bulk_create용 객체 리스트 생성
            step_time = time.time()
            records_to_create = []

            for row in dataset.dict:
                # 내원일 파싱 (YYYYMMDDHHmm 형식)
                visit_at_str = row.get("내원일", "")
                visit_at = None
                if visit_at_str:
                    from datetime import datetime

                    try:
                        visit_at = datetime.strptime(
                            str(visit_at_str), "%Y%m%d%H%M"
                        )
                    except ValueError:
                        pass  # 파싱 실패 시 None

                patient_record = PatientRecord(
                    hospital=obj.hospital,
                    manual_record=obj,
                    chart_number=row.get("챠트번호", ""),
                    patient_name=row.get("수진자명", ""),
                    patient_id=row.get("주민번호", ""),
                    insurance_type=row.get("보험유형", ""),
                    room=row.get("진료과", ""),
                    doctor_name=row.get("담당의", ""),
                    visit_type=row.get("초/재", ""),
                    visit_at=visit_at,  # type: ignore[misc]
                )
                records_to_create.append(patient_record)

            timing["parse_objects"] = time.time() - step_time

            # 5단계: bulk_create (시그널 없이 일괄 생성)
            step_time = time.time()
            created_records = PatientRecord.objects.bulk_create(
                records_to_create, batch_size=500
            )
            timing["bulk_create"] = time.time() - step_time

            # 6단계: 통계 갱신 (skip_statistics=False일 때만)
            if not skip_statistics:
                step_time = time.time()
                from record.signals import update_daily_statistics

                update_daily_statistics(ManualRecord, obj, created=False)
                timing["statistics"] = time.time() - step_time

            timing["total"] = time.time() - start_time

            # 성능 측정 결과 표시
            stats_msg = (
                f", 통계 {timing.get('statistics', 0):.2f}초"
                if not skip_statistics
                else ""
            )
            self.message_user(
                request,
                f"환자 진료 기록 import 완료: 삭제 {deleted_count}건, 신규 생성 {len(created_records)}건\n"
                f"소요시간: 파일읽기 {timing['file_read']:.2f}초, 전처리 {timing['preprocessing']:.2f}초, "
                f"삭제 {timing['delete']:.2f}초, 파싱 {timing['parse_objects']:.2f}초, "
                f"생성 {timing['bulk_create']:.2f}초{stats_msg}, 전체 {timing['total']:.2f}초",
                level="success",
            )

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            self.message_user(
                request,
                f"환자 진료 기록 파일 import 중 오류 발생:\n{type(e).__name__}: {str(e)}\n\n상세 정보:\n{error_detail}",
                level="error",
            )
            raise  # transaction.atomic()이 롤백 처리

    def _import_visit_channel_records(
        self, request, obj, skip_statistics=False
    ):
        """내원 경로 파일 import - 최적화 버전 (삭제 후 bulk_create)"""
        import time

        from tablib import Dataset

        timing = {}  # 성능 측정용

        try:
            start_time = time.time()

            # 1단계: 파일 읽기 및 파싱
            dataset = Dataset()
            file_content = obj.visit_source_file.read()

            file_name = obj.visit_source_file.name
            if file_name.endswith(".xlsx"):
                dataset.load(file_content, format="xlsx")
            elif file_name.endswith(".xls"):
                dataset.load(file_content, format="xls")
            else:
                self.message_user(
                    request,
                    "지원하지 않는 파일 형식입니다. .xlsx 또는 .xls 파일을 업로드해주세요.",
                    level="error",
                )
                return

            timing["file_read"] = time.time() - start_time

            # 2단계: 데이터 전처리 (before_import로 통계 행 제거)
            step_time = time.time()
            resource = VisitChannelRecordResource()
            resource.before_import(dataset, manual_record=obj)
            timing["preprocessing"] = time.time() - step_time

            # 3단계: 기존 데이터 삭제
            step_time = time.time()
            deleted_count = obj.visit_channel_records.all().delete()[0]
            timing["delete"] = time.time() - step_time

            # 4단계: bulk_create용 객체 리스트 생성
            step_time = time.time()
            records_to_create = []

            for row in dataset.dict:
                visit_record = VisitChannelRecord(
                    hospital=obj.hospital,
                    manual_record=obj,
                    chart_number=row.get("차트번호", ""),
                    patient_name=row.get("이름", ""),
                    insurance_type=row.get("보험유형", ""),
                    room=row.get("진료과목", ""),
                    doctor_name=row.get("담당의", ""),
                    visit_type=row.get("초재진구분", ""),
                    visit_at=row.get("내원날짜", ""),
                    channel=row.get("내원경로", ""),
                )
                records_to_create.append(visit_record)

            timing["parse_objects"] = time.time() - step_time

            # 5단계: bulk_create (시그널 없이 일괄 생성)
            step_time = time.time()
            created_records = VisitChannelRecord.objects.bulk_create(
                records_to_create, batch_size=500
            )
            timing["bulk_create"] = time.time() - step_time

            # 6단계: 통계 갱신 (skip_statistics=False일 때만)
            if not skip_statistics:
                step_time = time.time()
                from record.signals import update_daily_statistics

                update_daily_statistics(ManualRecord, obj, created=False)
                timing["statistics"] = time.time() - step_time

            timing["total"] = time.time() - start_time

            # 성능 측정 결과 표시
            stats_msg = (
                f", 통계 {timing.get('statistics', 0):.2f}초"
                if not skip_statistics
                else ""
            )
            self.message_user(
                request,
                f"내원 경로 import 완료: 삭제 {deleted_count}건, 신규 생성 {len(created_records)}건\n"
                f"소요시간: 파일읽기 {timing['file_read']:.2f}초, 전처리 {timing['preprocessing']:.2f}초, "
                f"삭제 {timing['delete']:.2f}초, 파싱 {timing['parse_objects']:.2f}초, "
                f"생성 {timing['bulk_create']:.2f}초{stats_msg}, 전체 {timing['total']:.2f}초",
                level="success",
            )

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            self.message_user(
                request,
                f"내원 경로 파일 import 중 오류 발생:\n{type(e).__name__}: {str(e)}\n\n상세 정보:\n{error_detail}",
                level="error",
            )
            raise  # transaction.atomic()이 롤백 처리

    def delete_model(self, request, obj):
        """
        단일 마감일지 삭제 (soft delete)
        - ManualRecord soft delete
        - 관련 DailyStatistics soft delete
        - 월별/전역 통계 업데이트
        """
        from record.signals import (
            update_global_statistics,
            update_monthly_statistics_for_date,
        )

        # 통계 업데이트를 위해 날짜 저장
        date = obj.date

        # ManualRecord soft delete
        obj.soft_delete()

        # 관련 DailyStatistics도 soft delete
        try:
            daily_stat = DailyStatistics.all_objects.get(manual_record=obj)
            daily_stat.soft_delete()
        except DailyStatistics.DoesNotExist:
            pass

        # 통계 업데이트
        update_monthly_statistics_for_date(date, obj.hospital)
        update_global_statistics(obj.hospital)

        self.message_user(
            request,
            f"{obj.date} 마감일지가 삭제되었습니다. 월별/전역 통계가 업데이트되었습니다.",
            level="success",
        )

    def delete_queryset(self, request, queryset):
        """
        여러 마감일지 삭제 (soft delete)
        - 선택된 ManualRecord들 soft delete
        - 관련 DailyStatistics soft delete
        - 월별/전역 통계 업데이트
        """
        from record.signals import (
            update_global_statistics,
            update_monthly_statistics_for_date,
        )

        # 영향받은 월 추적
        months_updated = set()
        count = 0

        for obj in queryset:
            # 통계 업데이트를 위해 날짜 저장
            months_updated.add((obj.date.year, obj.date.month))

            # ManualRecord soft delete
            obj.soft_delete()

            # 관련 DailyStatistics도 soft delete
            try:
                daily_stat = DailyStatistics.all_objects.get(manual_record=obj)
                daily_stat.soft_delete()
            except DailyStatistics.DoesNotExist:
                pass

            count += 1

        # 영향받은 월별 통계 재계산
        for year, month in months_updated:
            from datetime import date

            update_monthly_statistics_for_date(
                date(year, month, 1), queryset.first().hospital
            )

        # 전역 통계 재계산
        update_global_statistics(queryset.first().hospital)

        self.message_user(
            request,
            f"{count}개 마감일지가 삭제되었습니다. "
            f"영향받은 월: {len(months_updated)}개월, 전역 통계도 업데이트되었습니다.",
            level="success",
        )

    @admin.action(description="선택된 마감일지의 통계 재계산")
    def recalculate_statistics(self, request, queryset):
        """데이터 불일치 시 관리자가 수동으로 통계 재계산"""
        from record.models import DailyStatistics
        from record.signals import (
            update_global_statistics,
            update_monthly_statistics_for_date,
        )

        count = 0
        months_updated = set()

        for manual_record in queryset:
            # 일별 통계 재계산
            daily_stat, _ = DailyStatistics.objects.get_or_create(
                manual_record=manual_record
            )

            # 총매출 계산
            daily_stat.total_revenue = manual_record.total_revenue

            # 환자 통계 계산
            patient_records = PatientRecord.objects.filter(
                manual_record=manual_record
            )
            daily_stat.new_patient_count = patient_records.filter(
                Q(visit_type__icontains="신환") | Q(visit_type__icontains="신")
            ).count()
            daily_stat.revisit_patient_count = patient_records.filter(
                Q(visit_type__icontains="재진") | Q(visit_type__icontains="재")
            ).count()
            daily_stat.ninety_day_patient_count = patient_records.filter(
                Q(visit_type__icontains="90")
            ).count()
            daily_stat.total_patient_count = (
                daily_stat.new_patient_count
                + daily_stat.revisit_patient_count
                + daily_stat.ninety_day_patient_count
            )

            # 내원 경로 통계
            visit_records = VisitChannelRecord.objects.filter(
                manual_record=manual_record
            )
            channel_counts = {}
            for channel in ["인터넷", "간판", "소개", "전화", "재방문", "기타"]:
                channel_counts[channel] = visit_records.filter(
                    channel=channel
                ).count()
            daily_stat.channel_counts = channel_counts

            daily_stat.save()

            # 해당 월 추적
            months_updated.add(
                (manual_record.date.year, manual_record.date.month)
            )
            count += 1

        # 영향받은 월별 통계 재계산
        for year, month in months_updated:
            from datetime import date

            update_monthly_statistics_for_date(
                date(year, month, 1), queryset.first().hospital
            )

        # 전역 통계 재계산
        update_global_statistics(queryset.first().hospital)

        self.message_user(
            request,
            f"{count}개 마감일지의 통계를 재계산했습니다. "
            f"영향받은 월: {len(months_updated)}개월, 전역 통계도 업데이트되었습니다.",
            level="success",
        )


# ============================================
# 통계 모델 Admin
# ============================================


@admin.register(DailyStatistics)
class DailyStatisticsAdmin(TenantAdminMixin, ModelAdmin):
    """일별 통계 Admin (읽기 전용)"""

    list_display = [
        "hospital",
        "get_date",
        "total_revenue",
        "total_patient_count",
        "new_patient_count",
        "revisit_patient_count",
    ]

    list_filter = [
        "manual_record__date",
    ]

    ordering = ["-manual_record__date"]

    @admin.display(description="날짜", ordering="manual_record__date")
    def get_date(self, obj):
        return obj.manual_record.date

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MonthlyStatistics)
class MonthlyStatisticsAdmin(TenantAdminMixin, ModelAdmin):
    """월별 통계 Admin (읽기 전용)"""

    list_display = [
        "hospital",
        "get_year_month",
        "working_days",
        "total_revenue",
        "total_patients",
        "avg_total_patients",
        "fee_per_case",
    ]

    ordering = ["-year", "-month"]

    @admin.display(description="년월")
    def get_year_month(self, obj):
        return f"{obj.year}년 {obj.month:02d}월"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GlobalStatistics)
class GlobalStatisticsAdmin(TenantAdminMixin, ModelAdmin):
    """병원별 통계 Admin (읽기 전용)"""

    list_display = [
        "hospital",
        "key",
        "get_value_display",
        "description",
        "updated_at",
    ]

    ordering = ["key"]

    @admin.display(description="값")
    def get_value_display(self, obj):
        value = obj.value
        if "amount" in value:
            return f"{value['amount']:,}원"
        elif "count" in value:
            return f"{value['count']}명"
        return str(value)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
