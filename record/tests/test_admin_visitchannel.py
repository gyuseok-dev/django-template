"""Tests for VisitChannelRecordAdmin"""

from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from hospital.models import Hospital
from record.admin import VisitChannelRecordAdmin
from record.models import ManualRecord, VisitChannelRecord

from .factories import (
    HospitalFactory,
    ManualRecordFactory,
    VisitChannelRecordFactory,
)

User = get_user_model()


class VisitChannelRecordAdminBaseTest(TestCase):
    """VisitChannelRecordAdmin 테스트를 위한 베이스 클래스"""

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

        # ManualRecord 생성 (VisitChannelRecord의 필수 FK)
        self.manual_record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital
        )

        # Admin 인스턴스
        self.admin = VisitChannelRecordAdmin(
            VisitChannelRecord, django_admin.site
        )


class VisitChannelRecordAdminListTest(VisitChannelRecordAdminBaseTest):
    """목록 페이지 테스트"""

    def test_list_view_displays_records(self):
        """목록 페이지가 정상적으로 표시되는지 테스트"""
        # Given: VisitChannelRecord 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="홍길동",
            chart_number=12345,
            channel="인터넷",
        )

        # When: changelist 페이지 요청
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url)

        # Then: 200 응답 및 레코드 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "홍길동")
        self.assertContains(response, "12345")
        self.assertContains(response, "인터넷")

    def test_list_view_displays_channel(self):
        """목록에 내원경로가 표시되는지 테스트"""
        # Given: 다양한 채널의 레코드 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            channel="간판",
        )

        # When: changelist 페이지 요청
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url)

        # Then: 채널명 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "간판")


class VisitChannelRecordAdminSearchTest(VisitChannelRecordAdminBaseTest):
    """검색 기능 테스트"""

    def test_search_by_patient_name(self):
        """환자명으로 검색이 되는지 테스트"""
        # Given: 여러 환자 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="홍길동",
        )
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="김철수",
        )

        # When: 홍길동 검색
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url, {"q": "홍길동"})

        # Then: 홍길동만 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "홍길동")
        self.assertNotContains(response, "김철수")

    def test_search_by_channel(self):
        """내원경로로 검색이 되는지 테스트"""
        # Given: 다른 채널의 환자 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="인터넷환자",
            channel="인터넷",
        )
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="간판환자",
            channel="간판",
        )

        # When: 인터넷 검색
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url, {"q": "인터넷"})

        # Then: 인터넷 환자만 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "인터넷환자")
        self.assertNotContains(response, "간판환자")


class VisitChannelRecordAdminFilterTest(VisitChannelRecordAdminBaseTest):
    """필터 기능 테스트"""

    def test_filter_by_channel(self):
        """내원경로로 필터링이 되는지 테스트"""
        # Given: 다른 채널의 환자 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="인터넷환자",
            channel="인터넷",
        )
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="소개환자",
            channel="소개",
        )

        # When: 인터넷 필터 적용
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url, {"channel__exact": "인터넷"})

        # Then: 인터넷 환자만 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "인터넷환자")
        self.assertNotContains(response, "소개환자")

    def test_filter_by_visit_type(self):
        """진료유형으로 필터링이 되는지 테스트"""
        # Given: 신환/재진 환자 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="신환환자",
            visit_type="신환",
        )
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="재진환자",
            visit_type="재진",
        )

        # When: 신환 필터 적용
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url, {"visit_type__exact": "신환"})

        # Then: 신환만 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "신환환자")
        self.assertNotContains(response, "재진환자")

    def test_filter_by_room(self):
        """진료과로 필터링이 되는지 테스트"""
        # Given: 다른 진료과 환자 생성
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="내과환자",
            room="내과",
        )
        VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="외과환자",
            room="외과",
        )

        # When: 내과 필터 적용
        url = reverse("admin:record_visitchannelrecord_changelist")
        response = self.client.get(url, {"room__exact": "내과"})

        # Then: 내과만 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "내과환자")
        self.assertNotContains(response, "외과환자")


class VisitChannelRecordAdminCRUDTest(VisitChannelRecordAdminBaseTest):
    """CRUD 기능 테스트"""

    def test_change_view_get(self) -> None:
        """수정 폼이 정상적으로 표시되는지 테스트"""
        # Given: 기존 레코드
        record: VisitChannelRecord = VisitChannelRecordFactory.create(
            hospital=self.hospital,
            manual_record=self.manual_record,
            patient_name="테스트환자",
            channel="전화",
        )

        # When: change 페이지 요청
        url = reverse(
            "admin:record_visitchannelrecord_change", args=[record.pk]
        )
        response = self.client.get(url)

        # Then: 200 응답
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "테스트환자")
        self.assertContains(response, "전화")
