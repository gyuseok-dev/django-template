"""Tests for ManualRecordAdmin"""

from datetime import date, timedelta

from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from hospital.models import Hospital
from record.admin import ManualRecordAdmin
from record.models import ManualRecord

from .factories import (
    HospitalFactory,
    ManualRecordFactory,
    PatientRecordFactory,
    VisitChannelRecordFactory,
)

User = get_user_model()


class ManualRecordAdminBaseTest(TestCase):
    """ManualRecordAdmin 테스트를 위한 베이스 클래스"""

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

        # Admin 인스턴스
        self.admin = ManualRecordAdmin(ManualRecord, django_admin.site)


class ManualRecordAdminCRUDTest(ManualRecordAdminBaseTest):
    """CRUD 기본 기능 테스트"""

    def test_list_view_displays_records(self) -> None:
        """목록 페이지가 정상적으로 표시되는지 테스트"""
        # Given: ManualRecord 생성
        record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital, date=date.today()
        )

        # When: changelist 페이지 요청
        url = reverse("admin:record_manualrecord_changelist")
        response = self.client.get(url)

        # Then: 200 응답 및 레코드 표시
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.hospital.name)
        self.assertContains(response, str(record.date))

    def test_list_view_filters_soft_deleted(self) -> None:
        """soft delete된 레코드는 목록에 표시되지 않는지 테스트"""
        # Given: 정상 레코드와 삭제된 레코드
        normal_record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital, date=date.today()
        )
        deleted_record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital, date=date.today() - timedelta(days=1)
        )
        deleted_record.soft_delete()

        # When: changelist 페이지 요청
        url = reverse("admin:record_manualrecord_changelist")
        response = self.client.get(url)

        # Then: 정상 레코드만 표시
        self.assertContains(response, str(normal_record.date))
        self.assertNotContains(response, str(deleted_record.date))

    def test_add_view_get(self) -> None:
        """생성 폼이 정상적으로 표시되는지 테스트"""
        # When: add 페이지 요청
        url = reverse("admin:record_manualrecord_add")
        response = self.client.get(url)

        # Then: 200 응답
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "마감일")

    def test_add_view_post_success(self) -> None:
        """ManualRecord 생성이 정상적으로 동작하는지 테스트"""
        # Given: POST 데이터
        url = reverse("admin:record_manualrecord_add")
        data = {
            "hospital": self.hospital.id,
            "date": "2024-01-15",
        }

        # When: POST 요청
        response = self.client.post(url, data)

        # Then: 리다이렉트 및 레코드 생성
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ManualRecord.objects.count(), 1)
        record = ManualRecord.objects.first()
        assert record is not None
        self.assertEqual(record.hospital, self.hospital)
        self.assertEqual(str(record.date), "2024-01-15")

    def test_add_view_duplicate_date(self) -> None:
        """중복 날짜 생성 시 에러가 발생하는지 테스트"""
        # Given: 기존 레코드
        _: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital, date=date(2024, 1, 15)
        )

        # When: 같은 날짜로 POST 요청
        url = reverse("admin:record_manualrecord_add")
        data = {
            "hospital": self.hospital.id,
            "date": "2024-01-15",
        }
        response = self.client.post(url, data)

        # Then: 에러 표시
        self.assertEqual(response.status_code, 200)  # 폼 재표시
        self.assertContains(response, "이미 존재")  # 에러 메시지 포함

    def test_change_view_get(self) -> None:
        """수정 폼이 정상적으로 표시되는지 테스트"""
        # Given: 기존 레코드
        record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital
        )

        # When: change 페이지 요청
        url = reverse("admin:record_manualrecord_change", args=[record.pk])
        response = self.client.get(url)

        # Then: 200 응답
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(record.date))

    def test_change_view_post_success(self) -> None:
        """ManualRecord 수정이 정상적으로 동작하는지 테스트"""
        # Given: 기존 레코드
        record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital, date=date(2024, 1, 15)
        )

        # When: 날짜 변경 POST 요청
        url = reverse("admin:record_manualrecord_change", args=[record.pk])
        data = {
            "hospital": self.hospital.id,
            "date": "2024-01-16",
        }
        response = self.client.post(url, data)

        # Then: 리다이렉트 및 레코드 수정
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(str(record.date), "2024-01-16")

    def test_get_patient_record_count(self) -> None:
        """환자 진료 기록 개수 표시가 올바른지 테스트"""
        # Given: 환자 진료 기록이 있는 ManualRecord
        record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital
        )
        PatientRecordFactory.create(
            manual_record=record, hospital=self.hospital
        )
        PatientRecordFactory.create(
            manual_record=record, hospital=self.hospital
        )

        # When: get_patient_record_count 호출
        result = self.admin.get_patient_record_count(record)

        # Then: 2건 표시
        self.assertEqual(result, "2건")

    def test_get_visit_channel_record_count(self) -> None:
        """내원 경로 기록 개수 표시가 올바른지 테스트"""
        # Given: 내원 경로 기록이 있는 ManualRecord
        record: ManualRecord = ManualRecordFactory.create(
            hospital=self.hospital
        )
        VisitChannelRecordFactory.create(
            manual_record=record, hospital=self.hospital
        )
        VisitChannelRecordFactory.create(
            manual_record=record, hospital=self.hospital
        )
        VisitChannelRecordFactory.create(
            manual_record=record, hospital=self.hospital
        )

        # When: get_visit_channel_record_count 호출
        result = self.admin.get_visit_channel_record_count(record)

        # Then: 3건 표시
        self.assertEqual(result, "3건")


# TransactionTestCase는 추후 import 테스트에서 사용
# 현재는 기본 CRUD 테스트만 먼저 작성
