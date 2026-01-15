from django.db import models

from core.models import BaseModel
from hospital.models import Room


def upload_to_folder(instance, filename):
    return f"file/{instance.date}/{filename}"


class ManualRecord(BaseModel):
    """일일 마감일지 공통 정보"""

    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="manual_records",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    date = models.DateField(verbose_name="마감일", db_index=True)

    # 엑셀 파일 TODO: Attachment로 분리
    medical_record_file = models.FileField(
        upload_to=upload_to_folder,
        verbose_name="일일환자집계",
        blank=True,
        null=True,
        help_text="환자 진료 기록 엑셀 파일 (.xlsx, .xls)",
    )

    visit_source_file = models.FileField(
        upload_to=upload_to_folder,
        verbose_name="일일내원경로",
        blank=True,
        null=True,
        help_text="내원경로 기록 엑셀 파일 (.xlsx, .xls)",
    )

    # 총매출 (자동 계산되어 저장됨)
    total_revenue = models.IntegerField(
        default=0,
        verbose_name="총매출",
        help_text="총진료비 - 미수발생 + 미수입금",
    )

    class Meta:
        verbose_name = "마감일지"
        verbose_name_plural = "마감일지"
        ordering = ["-date"]
        unique_together = [["hospital", "date"]]  # 병원별 날짜 고유

    def __str__(self):
        return f"{self.date} 마감일지"

    @property
    def 급여(self):
        """모든 진료실의 급여 합계"""
        return sum(record.급여 for record in self.room_records.all())

    @property
    def 비급여(self):
        """모든 진료실의 비급여 합계"""
        return sum(record.비급여 for record in self.room_records.all())

    @property
    def 조합청구액(self):
        """모든 진료실의 조합청구액 합계"""
        return sum(record.조합청구액 for record in self.room_records.all())

    @property
    def 단위절사(self):
        """모든 진료실의 단위절사 합계"""
        return sum(record.단위절사 for record in self.room_records.all())

    @property
    def 전액본인(self):
        """모든 진료실의 전액본인 합계"""
        return sum(record.전액본인 for record in self.room_records.all())

    @property
    def 미수_발생금액(self):
        """모든 진료실의 미수발생 금액 합계"""
        return sum(record.미수_발생금액 for record in self.room_records.all())

    @property
    def 미수_발생건수(self):
        """모든 진료실의 미수발생 건수 합계"""
        return sum(record.미수_발생건수 for record in self.room_records.all())

    @property
    def 미수_입금금액(self):
        """모든 진료실의 미수입금 금액 합계"""
        return sum(record.미수_입금금액 for record in self.room_records.all())

    @property
    def 미수_입금건수(self):
        """모든 진료실의 미수입금 건수 합계"""
        return sum(record.미수_입금건수 for record in self.room_records.all())

    @property
    def total_jinryobi(self):
        """총진료비 = 급여 + 비급여 + 조합청구액 + 100/100미만 총액 + 장애인기금/전액본인"""
        return (
            self.급여
            + self.비급여
            + self.조합청구액
            + self.단위절사
            + self.전액본인
        )

    def calculate_total_revenue(self):
        """총매출 계산 = 총진료비 - 미수발생 금액 + 미수입금 금액"""
        return self.total_jinryobi - self.미수_발생금액 + self.미수_입금금액


class RoomRecord(BaseModel):
    """진료실별 급여 정보"""

    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="room_records",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    manual_record = models.ForeignKey(
        ManualRecord,
        on_delete=models.CASCADE,
        related_name="room_records",
        verbose_name="마감일지",
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="records",
        verbose_name="진료실",
    )

    급여 = models.IntegerField(default=0, verbose_name="급여")

    # 진료비 구성 항목
    비급여 = models.IntegerField(default=0, verbose_name="비급여")
    조합청구액 = models.IntegerField(default=0, verbose_name="조합청구액")
    단위절사 = models.IntegerField(default=0, verbose_name="100/100미만 총액")
    전액본인 = models.IntegerField(
        default=0, verbose_name="장애인기금/전액본인"
    )

    # 미수 관련
    미수_발생금액 = models.IntegerField(default=0, verbose_name="미수발생 금액")
    미수_발생건수 = models.IntegerField(default=0, verbose_name="미수발생 건수")
    미수_입금금액 = models.IntegerField(default=0, verbose_name="미수입금 금액")
    미수_입금건수 = models.IntegerField(default=0, verbose_name="미수입금 건수")

    class Meta:
        verbose_name = "진료실별 마감일지"
        verbose_name_plural = "진료실별 마감일지"
        unique_together = [["manual_record", "room"]]
        ordering = ["room__order", "room__name"]

    def __str__(self):
        room_name = self.room.name if self.room else "알수없음"
        return f"{self.manual_record.date} - {room_name}: {self.급여:,}원"


class PatientRecord(BaseModel):
    """환자 진료 기록"""

    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="patient_records",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    manual_record = models.ForeignKey(
        ManualRecord,
        on_delete=models.CASCADE,
        related_name="patient_records",
        verbose_name="마감일지",
        null=True,
        blank=True,
    )

    chart_number = models.IntegerField(verbose_name="차트번호", db_index=True)
    # 기본 정보
    visit_at = models.DateTimeField(
        max_length=7,
        verbose_name="내원일",
        help_text="YYYY-MM 형식",
        db_index=True,
    )

    visit_type = models.CharField(
        max_length=20,
        verbose_name="초재",
        blank=True,
        help_text="신환/재진/90일초진 등",
    )

    patient_name = models.CharField(max_length=100, verbose_name="수진자명")
    patient_id = models.CharField(
        max_length=50,
        verbose_name="주민번호",
        blank=True,
        help_text="주민등록번호",
    )

    # 보험 및 진료 정보
    insurance_type = models.TextField(
        verbose_name="보험유형",
        blank=True,
        help_text="예: 국민건강보험, 보호1종  등",
    )
    room = models.CharField(
        max_length=100, verbose_name="진료실", db_index=True
    )

    doctor_name = models.CharField(
        max_length=100, verbose_name="담당의", blank=True, db_index=True
    )

    class Meta:
        verbose_name = "환자 진료 기록"
        verbose_name_plural = "환자 진료 기록"
        ordering = ["-created_at", "patient_name"]
        indexes = [
            models.Index(fields=["created_at", "room"]),
            models.Index(fields=["patient_name"]),
        ]

    def __str__(self):
        return f"{self.visit_date}#{self.patient_name} ({self.room})"

    @property
    def masked_patient_id(self):
        """주민번호 마스킹 처리"""
        if not self.patient_id:
            return ""
        if len(self.patient_id) >= 8:
            return f"{self.patient_id[:6]}-{self.patient_id[6]}******"
        return "******"

    @property
    def created_date(self):
        """생성일 (날짜만)"""
        if self.created_at:
            return self.created_at.date()
        return None

    @property
    def visit_date(self):
        """내원일 (날짜만)"""
        if self.visit_at:
            return self.visit_at.date()
        return None


class VisitChannelRecord(BaseModel):
    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="visit_channel_records",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    manual_record = models.ForeignKey(
        ManualRecord,
        on_delete=models.CASCADE,
        related_name="visit_channel_records",
        verbose_name="마감일지",
        null=True,
        blank=True,
    )

    channel = models.TextField(
        verbose_name="내원경로", help_text="예: 인터넷, 간판, 소개"
    )

    chart_number = models.IntegerField(verbose_name="차트번호", db_index=True)
    # 기본 정보
    visit_at = models.DateTimeField(
        max_length=7,
        verbose_name="내원일",
        help_text="YYYY-MM 형식",
        db_index=True,
    )

    visit_type = models.CharField(
        max_length=20,
        verbose_name="초재",
        blank=True,
        help_text="신환/재진/90일초진 등",
    )

    patient_name = models.CharField(max_length=100, verbose_name="수진자명")

    # 보험 및 진료 정보
    insurance_type = models.TextField(
        verbose_name="보험유형",
        blank=True,
        help_text="예: 국민건강보험, 보호1종  등",
    )
    room = models.CharField(
        max_length=100, verbose_name="진료실", db_index=True
    )

    doctor_name = models.CharField(
        max_length=100, verbose_name="담당의", blank=True, db_index=True
    )

    class Meta:
        verbose_name = "내원 경로"
        verbose_name_plural = "내원 경로"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at", "room"]),
            models.Index(fields=["patient_name"]),
        ]

    def __str__(self):
        return f"{self.visit_date}#{self.patient_name} ({self.room})"

    @property
    def created_date(self):
        """생성일 (날짜만)"""
        if self.created_at:
            return self.created_at.date()
        return None

    @property
    def visit_date(self):
        """내원일 (날짜만)"""
        if self.visit_at:
            return self.visit_at.date()
        return None


# ============================================
# 통계 모델들
# ============================================


class DailyStatistics(BaseModel):
    """일별 통계 - ManualRecord 기반 자동 계산"""

    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="daily_statistics",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    manual_record = models.OneToOneField(
        ManualRecord,
        on_delete=models.DO_NOTHING,
        related_name="daily_stats",
        verbose_name="마감일지",
    )

    # 매출 통계
    total_revenue = models.IntegerField(
        default=0, verbose_name="총매출", db_index=True
    )

    # 환자 통계
    new_patient_count = models.IntegerField(default=0, verbose_name="신환 수")
    revisit_patient_count = models.IntegerField(
        default=0, verbose_name="재진 수"
    )
    ninety_day_patient_count = models.IntegerField(
        default=0, verbose_name="90일초진 수"
    )
    total_patient_count = models.IntegerField(
        default=0, verbose_name="총 환자 수"
    )

    # 내원 경로별 통계 (JSON 필드)
    channel_counts = models.JSONField(
        default=dict,
        verbose_name="내원경로별 건수",
        help_text='{"인터넷": 10, "간판": 20, ...}',
    )

    class Meta:
        verbose_name = "일별 통계"
        verbose_name_plural = "일별 통계"
        ordering = ["-manual_record__date"]
        default_permissions = []  # 자동 생성 모델이므로 권한 체크 제거
        indexes = [
            models.Index(fields=["-total_revenue"]),
            models.Index(fields=["manual_record"]),
        ]

    def __str__(self):
        return f"{self.manual_record.date} 통계"


class MonthlyStatistics(BaseModel):
    """월별 통계 - 일별 통계 집계"""

    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="monthly_statistics",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    year = models.IntegerField(verbose_name="년도", db_index=True)
    month = models.IntegerField(verbose_name="월", db_index=True)

    # 근무 일수
    working_days = models.IntegerField(default=0, verbose_name="근무 일수")

    # 매출 통계
    total_revenue = models.BigIntegerField(default=0, verbose_name="총매출")
    avg_daily_revenue = models.IntegerField(
        default=0, verbose_name="일평균 매출"
    )

    # 환자 통계 (총합 + 일평균)
    total_new_patients = models.IntegerField(default=0, verbose_name="총 신환")
    total_revisit_patients = models.IntegerField(
        default=0, verbose_name="총 재진"
    )
    total_ninety_patients = models.IntegerField(
        default=0, verbose_name="총 90일초진"
    )
    total_patients = models.IntegerField(default=0, verbose_name="총 환자")

    avg_new_patients = models.FloatField(default=0, verbose_name="일평균 신환")
    avg_revisit_patients = models.FloatField(
        default=0, verbose_name="일평균 재진"
    )
    avg_ninety_patients = models.FloatField(
        default=0, verbose_name="일평균 90일초진"
    )
    avg_total_patients = models.FloatField(
        default=0, verbose_name="일평균 총환자"
    )

    # 내원 경로별 통계
    channel_counts = models.JSONField(
        default=dict, verbose_name="내원경로별 건수"
    )

    # 건당 진료비
    fee_per_case = models.IntegerField(default=0, verbose_name="건당 진료비")

    class Meta:
        verbose_name = "월별 통계"
        verbose_name_plural = "월별 통계"
        ordering = ["-year", "-month"]
        unique_together = [["hospital", "year", "month"]]  # 병원별 년월 고유
        indexes = [
            models.Index(fields=["-year", "-month"]),
            models.Index(fields=["-total_revenue"]),
        ]

    def __str__(self):
        return f"{self.year}년 {self.month}월 통계"


class GlobalStatistics(BaseModel):
    """병원별 통계 - Key-Value 저장소

    최고/최저 매출, 최고 환자수 등 병원별 통계를 유연하게 저장

    예시 데이터:
    - key: "max_daily_revenue", value: {"amount": 5000000, "date": "2024-12-01"}
    - key: "min_daily_revenue", value: {"amount": 100000, "date": "2024-01-15"}
    - key: "max_monthly_revenue", value: {"amount": 150000000, "year": 2024, "month": 12}
    - key: "max_daily_patients", value: {"count": 150, "date": "2024-12-01"}
    """

    hospital = models.ForeignKey(
        "hospital.Hospital",
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name="병원",
        null=True,
        blank=True,
        db_index=True,
    )

    key = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="통계 키",
        help_text="예: max_daily_revenue, min_daily_revenue 등",
    )

    value = models.JSONField(
        default=dict,
        verbose_name="통계 값",
        help_text="JSON 형태로 유연하게 저장",
    )

    description = models.TextField(
        blank=True, verbose_name="설명", help_text="이 통계의 의미"
    )

    class Meta:
        verbose_name = "병원별 통계"
        verbose_name_plural = "병원별 통계"
        ordering = ["key"]
        unique_together = [["hospital", "key"]]  # 병원별 키 고유

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key, hospital_id, default=None):
        """특정 키의 값을 가져오기"""
        try:
            if hospital_id:
                return cls.objects.get(key=key, hospital_id=hospital_id).value
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, description="", hospital=None):
        """특정 키의 값을 설정"""
        if hospital:
            obj, created = cls.objects.update_or_create(
                key=key,
                hospital=hospital,
                defaults={"value": value, "description": description},
            )
        else:
            obj, created = cls.objects.update_or_create(
                key=key, defaults={"value": value, "description": description}
            )
        return obj
