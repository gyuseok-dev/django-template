"""통계 자동 갱신을 위한 Django Signals"""

from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import (
    DailyStatistics,
    GlobalStatistics,
    ManualRecord,
    MonthlyStatistics,
    PatientRecord,
    RoomRecord,
    VisitChannelRecord,
)


@receiver(post_save, sender=ManualRecord)
def update_daily_statistics(sender, instance, created, **_kwargs):
    """ManualRecord 저장 시 DailyStatistics 업데이트"""
    # DailyStatistics 가져오기 또는 생성
    daily_stat, _ = DailyStatistics.objects.get_or_create(manual_record=instance)

    # 총매출 계산
    daily_stat.total_revenue = instance.total_revenue
    daily_stat.hospital = instance.hospital

    # 환자 통계 계산
    patient_records = PatientRecord.objects.filter(manual_record=instance)
    daily_stat.new_patient_count = patient_records.filter(
        Q(visit_type__icontains="신환") | Q(visit_type__icontains="신")
    ).count()
    daily_stat.revisit_patient_count = patient_records.filter(
        Q(visit_type__icontains="재진") | Q(visit_type__icontains="재")
    ).count()
    daily_stat.ninety_day_patient_count = patient_records.filter(Q(visit_type__icontains="90")).count()
    daily_stat.total_patient_count = (
        daily_stat.new_patient_count + daily_stat.revisit_patient_count + daily_stat.ninety_day_patient_count
    )

    # 내원 경로 통계
    visit_records = VisitChannelRecord.objects.filter(manual_record=instance)
    channel_counts = {}
    for channel in ["인터넷", "간판", "소개", "전화", "재방문", "기타"]:
        channel_counts[channel] = visit_records.filter(channel=channel).count()
    daily_stat.channel_counts = channel_counts

    daily_stat.save()

    # 월별 통계도 업데이트
    update_monthly_statistics_for_date(instance.date, instance.hospital)

    # 병원별 통계 업데이트
    update_global_statistics(instance.hospital)


@receiver(post_delete, sender=ManualRecord)
def delete_daily_statistics(_sender, instance, **_kwargs):
    """ManualRecord 삭제 시 DailyStatistics도 삭제하고 월별 통계 업데이트"""
    try:
        daily_stat = DailyStatistics.objects.get(manual_record=instance)
        daily_stat.delete()
    except DailyStatistics.DoesNotExist:
        pass

    # 월별 통계 업데이트
    update_monthly_statistics_for_date(instance.date, instance.hospital)

    # 병원별 통계 업데이트
    update_global_statistics(instance.hospital)


@receiver(post_save, sender=PatientRecord)
@receiver(post_delete, sender=PatientRecord)
def update_stats_on_patient_change(_sender, instance, **_kwargs):
    """PatientRecord 변경 시 통계 업데이트"""
    if instance.manual_record:
        # ManualRecord의 post_save 시그널을 직접 호출하지 않고
        # DailyStatistics만 업데이트
        update_daily_statistics(ManualRecord, instance.manual_record, False)


@receiver(post_save, sender=VisitChannelRecord)
@receiver(post_delete, sender=VisitChannelRecord)
def update_stats_on_visit_change(sender, instance, **_kwargs):
    """VisitChannelRecord 변경 시 통계 업데이트"""
    if instance.manual_record:
        update_daily_statistics(ManualRecord, instance.manual_record, False)


@receiver(post_save, sender=RoomRecord)
@receiver(post_delete, sender=RoomRecord)
def update_stats_on_room_change(sender, instance, **_kwargs):
    """RoomRecord 변경 시 ManualRecord의 total_revenue 재계산 및 통계 업데이트"""
    if instance.manual_record:
        manual_record = instance.manual_record
        # total_revenue 재계산
        manual_record.total_revenue = manual_record.calculate_total_revenue()
        # update_fields를 사용하여 무한 루프 방지
        ManualRecord.objects.filter(pk=manual_record.pk).update(total_revenue=manual_record.total_revenue)
        # 통계 업데이트
        update_daily_statistics(ManualRecord, manual_record, False)


def update_monthly_statistics_for_date(date, hospital):
    """특정 날짜가 속한 월의 통계 업데이트 (병원별)"""
    if not hospital:
        return

    year = date.year
    month = date.month

    # 해당 월의 모든 ManualRecord 조회 (병원별)
    manual_records = ManualRecord._default_manager.filter(hospital=hospital, date__year=year, date__month=month)

    if not manual_records.exists():
        # 데이터가 없으면 통계 삭제
        MonthlyStatistics._default_manager.filter(hospital=hospital, year=year, month=month).delete()
        return

    # 월별 통계 가져오기 또는 생성
    monthly_stat, _ = MonthlyStatistics._default_manager.get_or_create(hospital=hospital, year=year, month=month)

    # 근무 일수
    monthly_stat.working_days = manual_records.count()

    # 일별 통계 집계 (병원별)
    daily_stats = DailyStatistics._default_manager.filter(hospital=hospital, manual_record__in=manual_records)

    # 매출 통계
    monthly_stat.total_revenue = sum(ds.total_revenue for ds in daily_stats)
    monthly_stat.avg_daily_revenue = (
        monthly_stat.total_revenue // monthly_stat.working_days if monthly_stat.working_days > 0 else 0
    )

    # 환자 통계
    monthly_stat.total_new_patients = sum(ds.new_patient_count for ds in daily_stats)
    monthly_stat.total_revisit_patients = sum(ds.revisit_patient_count for ds in daily_stats)
    monthly_stat.total_ninety_patients = sum(ds.ninety_day_patient_count for ds in daily_stats)
    monthly_stat.total_patients = sum(ds.total_patient_count for ds in daily_stats)

    if monthly_stat.working_days > 0:
        monthly_stat.avg_new_patients = round(monthly_stat.total_new_patients / monthly_stat.working_days, 1)
        monthly_stat.avg_revisit_patients = round(monthly_stat.total_revisit_patients / monthly_stat.working_days, 1)
        monthly_stat.avg_ninety_patients = round(monthly_stat.total_ninety_patients / monthly_stat.working_days, 1)
        monthly_stat.avg_total_patients = round(monthly_stat.total_patients / monthly_stat.working_days, 1)

    # 내원 경로 집계
    channel_counts = {"인터넷": 0, "간판": 0, "소개": 0, "전화": 0, "재방문": 0, "기타": 0}
    for ds in daily_stats:
        for channel, count in ds.channel_counts.items():
            channel_counts[channel] = channel_counts.get(channel, 0) + count
    monthly_stat.channel_counts = channel_counts

    # 건당 진료비
    monthly_stat.fee_per_case = (
        monthly_stat.total_revenue // monthly_stat.total_patients if monthly_stat.total_patients > 0 else 0
    )

    monthly_stat.save()


def update_global_statistics(hospital):
    """병원별 통계 업데이트 (최고/최저 매출 등)"""
    if not hospital:
        return

    # 1. 최고 일일 매출
    max_daily = DailyStatistics._default_manager.filter(hospital=hospital).order_by("-total_revenue").first()
    if max_daily:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="max_daily_revenue",
            defaults={
                "value": {"amount": max_daily.total_revenue, "date": str(max_daily.manual_record.date)},
                "description": "역대 최고 일일 매출",
            },
        )

    # 2. 최저 일일 매출 (매출이 0보다 큰 경우만)
    min_daily = (
        DailyStatistics._default_manager.filter(hospital=hospital, total_revenue__gt=0)
        .order_by("total_revenue")
        .first()
    )
    if min_daily:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="min_daily_revenue",
            defaults={
                "value": {"amount": min_daily.total_revenue, "date": str(min_daily.manual_record.date)},
                "description": "역대 최저 일일 매출 (0 제외)",
            },
        )

    # 3. 최고 일일 환자수
    max_daily_patients = (
        DailyStatistics._default_manager.filter(hospital=hospital).order_by("-total_patient_count").first()
    )
    if max_daily_patients:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="max_daily_patients",
            defaults={
                "value": {
                    "count": max_daily_patients.total_patient_count,
                    "date": str(max_daily_patients.manual_record.date),
                },
                "description": "역대 최고 일일 환자수",
            },
        )

    # 4. 최고 월간 매출
    max_monthly = MonthlyStatistics._default_manager.filter(hospital=hospital).order_by("-total_revenue").first()
    if max_monthly:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="max_monthly_revenue",
            defaults={
                "value": {"amount": int(max_monthly.total_revenue), "year": max_monthly.year, "month": max_monthly.month},
                "description": "역대 최고 월간 매출",
            },
        )

    # 5. 최저 월간 매출 (매출이 0보다 큰 경우만)
    min_monthly = (
        MonthlyStatistics._default_manager.filter(hospital=hospital, total_revenue__gt=0)
        .order_by("total_revenue")
        .first()
    )
    if min_monthly:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="min_monthly_revenue",
            defaults={
                "value": {"amount": int(min_monthly.total_revenue), "year": min_monthly.year, "month": min_monthly.month},
                "description": "역대 최저 월간 매출 (0 제외)",
            },
        )

    # 6. 최고 월간 환자수
    max_monthly_patients = (
        MonthlyStatistics._default_manager.filter(hospital=hospital).order_by("-total_patients").first()
    )
    if max_monthly_patients:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="max_monthly_patients",
            defaults={
                "value": {
                    "count": max_monthly_patients.total_patients,
                    "year": max_monthly_patients.year,
                    "month": max_monthly_patients.month,
                },
                "description": "역대 최고 월간 환자수",
            },
        )

    # 7. 최고 일평균 환자수
    max_avg_patients = (
        MonthlyStatistics._default_manager.filter(hospital=hospital).order_by("-avg_total_patients").first()
    )
    if max_avg_patients:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="max_avg_daily_patients",
            defaults={
                "value": {
                    "count": max_avg_patients.avg_total_patients,
                    "year": max_avg_patients.year,
                    "month": max_avg_patients.month,
                },
                "description": "역대 최고 일평균 환자수",
            },
        )

    # 8. 최고 건당 진료비
    max_fee = MonthlyStatistics._default_manager.filter(hospital=hospital).order_by("-fee_per_case").first()
    if max_fee:
        GlobalStatistics._default_manager.update_or_create(
            hospital=hospital,
            key="max_fee_per_case",
            defaults={
                "value": {"amount": max_fee.fee_per_case, "year": max_fee.year, "month": max_fee.month},
                "description": "역대 최고 건당 진료비",
            },
        )

    # 9. 요일별 최고 매출 (0=월요일, 6=일요일)
    weekday_revenue = {}
    for weekday in range(7):
        # Python weekday (0=월~6=일) -> Django week_day (1=일~7=토) 변환
        django_week_day = ((weekday + 1) % 7) + 1

        max_weekday_revenue = (
            DailyStatistics._default_manager.filter(
                hospital=hospital, manual_record__date__week_day=django_week_day
            )
            .order_by("-total_revenue")
            .first()
        )

        if max_weekday_revenue:
            weekday_revenue[str(weekday)] = {
                "amount": max_weekday_revenue.total_revenue,
                "date": str(max_weekday_revenue.manual_record.date),
            }
        else:
            weekday_revenue[str(weekday)] = {"amount": 0, "date": "-"}

    GlobalStatistics._default_manager.update_or_create(
        hospital=hospital,
        key="max_weekday_revenue",
        defaults={
            "value": weekday_revenue,
            "description": "요일별 최고 매출 (0=월요일, 6=일요일)",
        },
    )

    # 10. 요일별 최고 환자수 (0=월요일, 6=일요일)
    weekday_patients = {}
    for weekday in range(7):
        django_week_day = ((weekday + 1) % 7) + 1

        max_weekday_patients = (
            DailyStatistics._default_manager.filter(
                hospital=hospital, manual_record__date__week_day=django_week_day
            )
            .order_by("-total_patient_count")
            .first()
        )

        if max_weekday_patients:
            weekday_patients[str(weekday)] = {
                "count": max_weekday_patients.total_patient_count,
                "date": str(max_weekday_patients.manual_record.date),
            }
        else:
            weekday_patients[str(weekday)] = {"count": 0, "date": "-"}

    GlobalStatistics._default_manager.update_or_create(
        hospital=hospital,
        key="max_weekday_patients",
        defaults={
            "value": weekday_patients,
            "description": "요일별 최고 환자수 (0=월요일, 6=일요일)",
        },
    )
