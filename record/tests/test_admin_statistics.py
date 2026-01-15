"""Tests for Statistics Admin classes (DailyStatistics, MonthlyStatistics, GlobalStatistics)"""

from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from hospital.models import Hospital
from record.admin import (
    DailyStatisticsAdmin,
    GlobalStatisticsAdmin,
    MonthlyStatisticsAdmin,
)
from record.models import (
    DailyStatistics,
    GlobalStatistics,
    ManualRecord,
    MonthlyStatistics,
)

from .factories import HospitalFactory, ManualRecordFactory

User = get_user_model()


class StatisticsAdminBaseTest(TestCase):
    """통계 Admin 테스트를 위한 베이스 클래스"""

    def setUp(self) -> None:
        # 슈퍼유저 생성
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
            name="관리자",
        )
        self.client = Client()
        self.client.force_login(self.superuser)

        # 병원 생성
        self.hospital: Hospital = HospitalFactory.create()

        # 세션에 병원 설정 (멀티테넌시)
        session = self.client.session
        session["selected_hospital_id"] = self.hospital.id
        session.save()


class DailyStatisticsAdminTest(StatisticsAdminBaseTest):
    """DailyStatisticsAdmin 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.admin = DailyStatisticsAdmin(DailyStatistics, django_admin.site)

        # ManualRecord 생성 (signal로 DailyStatistics 자동 생성됨)
        self.manual_record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital, total_revenue=1500000
        )
        # signal로 자동 생성된 DailyStatistics 가져오기
        self.daily_stats = DailyStatistics.objects.get(
            manual_record=self.manual_record
        )

    def test_list_view_displays_records(self):
        """목록 페이지가 정상적으로 표시되는지 테스트"""
        # When: changelist 페이지 요청
        url = reverse("admin:record_dailystatistics_changelist")
        response = self.client.get(url)

        # Then: 200 응답 및 레코드 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hospital.name)

    def test_get_date_display(self):
        """날짜 표시가 올바른지 테스트"""
        # When: get_date 호출
        result = self.admin.get_date(self.daily_stats)

        # Then: manual_record의 날짜 반환
        self.assertEqual(result, self.manual_record.date)

    def test_has_no_add_permission(self):
        """추가 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 추가 권한 없음
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_no_change_permission(self):
        """수정 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 수정 권한 없음
        self.assertFalse(
            self.admin.has_change_permission(request, self.daily_stats)
        )

    def test_has_no_delete_permission(self):
        """삭제 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 삭제 권한 없음
        self.assertFalse(
            self.admin.has_delete_permission(request, self.daily_stats)
        )

    def test_add_view_redirects(self):
        """추가 페이지 접근 시 거부되는지 테스트"""
        # When: add 페이지 요청
        url = reverse("admin:record_dailystatistics_add")
        response = self.client.get(url)

        # Then: 403 Forbidden
        self.assertEqual(response.status_code, 403)


class MonthlyStatisticsAdminTest(StatisticsAdminBaseTest):
    """MonthlyStatisticsAdmin 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.admin = MonthlyStatisticsAdmin(
            MonthlyStatistics, django_admin.site
        )

        # MonthlyStatistics 생성
        self.monthly_stats: MonthlyStatistics = (
            MonthlyStatistics.objects.create(
                hospital=self.hospital,
                year=2024,
                month=12,
                working_days=22,
                total_revenue=50000000,
                total_patients=500,
                avg_total_patients=22.7,
                fee_per_case=100000,
            )
        )

    def test_list_view_displays_records(self):
        """목록 페이지가 정상적으로 표시되는지 테스트"""
        # When: changelist 페이지 요청
        url = reverse("admin:record_monthlystatistics_changelist")
        response = self.client.get(url)

        # Then: 200 응답 및 레코드 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hospital.name)

    def test_get_year_month_display(self):
        """년월 표시가 올바른지 테스트"""
        # When: get_year_month 호출
        result = self.admin.get_year_month(self.monthly_stats)

        # Then: 포맷팅된 년월 반환
        self.assertEqual(result, "2024년 12월")

    def test_has_no_add_permission(self):
        """추가 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 추가 권한 없음
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_no_change_permission(self):
        """수정 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 수정 권한 없음
        self.assertFalse(
            self.admin.has_change_permission(request, self.monthly_stats)
        )

    def test_has_no_delete_permission(self):
        """삭제 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 삭제 권한 없음
        self.assertFalse(
            self.admin.has_delete_permission(request, self.monthly_stats)
        )


class GlobalStatisticsAdminTest(StatisticsAdminBaseTest):
    """GlobalStatisticsAdmin 테스트"""

    def setUp(self) -> None:
        super().setUp()
        self.admin = GlobalStatisticsAdmin(GlobalStatistics, django_admin.site)

        # GlobalStatistics 생성
        self.global_stats_amount: GlobalStatistics = (
            GlobalStatistics.objects.create(
                hospital=self.hospital,
                key="max_daily_revenue",
                value={"amount": 5000000, "date": "2024-12-01"},
                description="일일 최고 매출",
            )
        )
        self.global_stats_count: GlobalStatistics = (
            GlobalStatistics.objects.create(
                hospital=self.hospital,
                key="max_daily_patients",
                value={"count": 150, "date": "2024-12-01"},
                description="일일 최고 환자수",
            )
        )

    def test_list_view_displays_records(self):
        """목록 페이지가 정상적으로 표시되는지 테스트"""
        # When: changelist 페이지 요청
        url = reverse("admin:record_globalstatistics_changelist")
        response = self.client.get(url)

        # Then: 200 응답 및 레코드 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "max_daily_revenue")
        self.assertContains(response, "max_daily_patients")

    def test_get_value_display_amount(self):
        """금액 값이 올바르게 포맷팅되는지 테스트"""
        # When: get_value_display 호출
        result = self.admin.get_value_display(self.global_stats_amount)

        # Then: 금액 포맷팅
        self.assertEqual(result, "5,000,000원")

    def test_get_value_display_count(self):
        """건수 값이 올바르게 포맷팅되는지 테스트"""
        # When: get_value_display 호출
        result = self.admin.get_value_display(self.global_stats_count)

        # Then: 건수 포맷팅
        self.assertEqual(result, "150명")

    def test_has_no_add_permission(self):
        """추가 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 추가 권한 없음
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_no_change_permission(self):
        """수정 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 수정 권한 없음
        self.assertFalse(
            self.admin.has_change_permission(request, self.global_stats_amount)
        )

    def test_has_no_delete_permission(self):
        """삭제 권한이 없는지 테스트"""
        # Given: request 객체 생성
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = self.superuser

        # Then: 삭제 권한 없음
        self.assertFalse(
            self.admin.has_delete_permission(request, self.global_stats_amount)
        )
