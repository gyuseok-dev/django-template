"""Test factories for record app models"""

from datetime import date
from typing import Any, ClassVar

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from hospital.models import Hospital, Room
from record.models import (
    ManualRecord,
    PatientRecord,
    RoomRecord,
    VisitChannelRecord,
)


class HospitalFactory(DjangoModelFactory[Hospital]):
    """Hospital 모델 팩토리"""

    class Meta:
        model = Hospital

    name: ClassVar[Any] = factory.Sequence(lambda n: f"테스트병원{n}")
    code: ClassVar[Any] = factory.Sequence(lambda n: f"TEST{n:03d}")
    address: ClassVar[str] = "서울시 강남구 테스트로 123"
    phone: ClassVar[str] = "02-1234-5678"
    is_active: ClassVar[bool] = True


class RoomFactory(DjangoModelFactory[Room]):
    """Room 모델 팩토리"""

    class Meta:
        model = Room

    hospital: ClassVar[Any] = factory.SubFactory(HospitalFactory)
    name: ClassVar[Any] = factory.Sequence(lambda n: f"진료실{n}")
    is_active: ClassVar[bool] = True
    order: ClassVar[Any] = factory.Sequence(lambda n: n)


class ManualRecordFactory(DjangoModelFactory[ManualRecord]):
    """ManualRecord 모델 팩토리"""

    class Meta:
        model = ManualRecord

    hospital: ClassVar[Any] = factory.SubFactory(HospitalFactory)
    date: ClassVar[Any] = factory.LazyFunction(lambda: date.today())
    total_revenue: ClassVar[int] = 0


class RoomRecordFactory(DjangoModelFactory[RoomRecord]):
    """RoomRecord 모델 팩토리"""

    class Meta:
        model = RoomRecord

    hospital: ClassVar[Any] = factory.SelfAttribute("manual_record.hospital")
    manual_record: ClassVar[Any] = factory.SubFactory(ManualRecordFactory)
    room: ClassVar[Any] = factory.SubFactory(
        RoomFactory, hospital=factory.SelfAttribute("..hospital")
    )

    # 통계 데이터
    급여: ClassVar[int] = 1000000
    비급여: ClassVar[int] = 500000
    조합청구액: ClassVar[int] = 200000
    단위절사: ClassVar[int] = 340
    전액본인: ClassVar[int] = 100000

    미수_발생금액: ClassVar[int] = 50000
    미수_발생건수: ClassVar[int] = 2
    미수_입금금액: ClassVar[int] = 30000
    미수_입금건수: ClassVar[int] = 1


class PatientRecordFactory(DjangoModelFactory[PatientRecord]):
    """PatientRecord 모델 팩토리"""

    class Meta:
        model = PatientRecord

    hospital: ClassVar[Any] = factory.SelfAttribute("manual_record.hospital")
    manual_record: ClassVar[Any] = factory.SubFactory(ManualRecordFactory)
    chart_number: ClassVar[Any] = factory.Sequence(lambda n: 10000 + n)
    patient_name: ClassVar[Any] = factory.Faker("name", locale="ko_KR")
    patient_id: ClassVar[str] = "800101-1234567"
    insurance_type: ClassVar[str] = "국민건강보험"
    room: ClassVar[str] = "내과"
    doctor_name: ClassVar[str] = "김의사"
    visit_type: ClassVar[str] = "신환"
    visit_at: ClassVar[Any] = factory.LazyFunction(timezone.now)


class VisitChannelRecordFactory(DjangoModelFactory[VisitChannelRecord]):
    """VisitChannelRecord 모델 팩토리"""

    class Meta:
        model = VisitChannelRecord

    hospital: ClassVar[Any] = factory.SelfAttribute("manual_record.hospital")
    manual_record: ClassVar[Any] = factory.SubFactory(ManualRecordFactory)
    chart_number: ClassVar[Any] = factory.Sequence(lambda n: 10000 + n)
    patient_name: ClassVar[Any] = factory.Faker("name", locale="ko_KR")
    insurance_type: ClassVar[str] = "국민건강보험"
    room: ClassVar[str] = "내과"
    doctor_name: ClassVar[str] = "김의사"
    visit_type: ClassVar[str] = "신환"
    visit_at: ClassVar[Any] = factory.LazyFunction(timezone.now)
    channel: ClassVar[str] = "인터넷"
