import json
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import PatientRecord


def dashboard_callback(request, context):
    """
    Unfold Admin 대시보드용 데이터 콜백
    통계 데이터를 context에 추가
    """
    today = timezone.now()

    # 당월 데이터
    current_month_records = PatientRecord.objects.filter(
        visit_at__year=today.year, visit_at__month=today.month
    )

    # 당월 진료일 수 (데이터가 있는 날짜만 카운트)
    current_working_days = (
        current_month_records.values("visit_at__date").distinct().count()
    )

    # 당월 통계
    current_new_count = current_month_records.filter(
        Q(visit_type__icontains="신환") | Q(visit_type__icontains="신")
    ).count()
    current_revisit_count = current_month_records.filter(
        Q(visit_type__icontains="재진") | Q(visit_type__icontains="재")
    ).count()
    current_ninety_count = current_month_records.filter(
        Q(visit_type__icontains="90")
    ).count()
    current_total = current_month_records.count()

    # 당월 일 평균
    current_avg_new = (
        round(current_new_count / current_working_days, 1)
        if current_working_days > 0
        else 0
    )
    current_avg_revisit = (
        round(current_revisit_count / current_working_days, 1)
        if current_working_days > 0
        else 0
    )
    current_avg_ninety = (
        round(current_ninety_count / current_working_days, 1)
        if current_working_days > 0
        else 0
    )
    current_avg_total = (
        round(current_total / current_working_days, 1)
        if current_working_days > 0
        else 0
    )

    # 전월 데이터
    prev_month_date = today - relativedelta(months=1)
    prev_month_records = PatientRecord.objects.filter(
        visit_at__year=prev_month_date.year,
        visit_at__month=prev_month_date.month,
    )

    # 전월 진료일 수
    prev_working_days = (
        prev_month_records.values("visit_at__date").distinct().count()
    )

    # 전월 통계
    prev_new_count = prev_month_records.filter(
        Q(visit_type__icontains="신환") | Q(visit_type__icontains="신")
    ).count()
    prev_revisit_count = prev_month_records.filter(
        Q(visit_type__icontains="재진") | Q(visit_type__icontains="재")
    ).count()
    prev_ninety_count = prev_month_records.filter(
        Q(visit_type__icontains="90")
    ).count()
    prev_total = prev_month_records.count()

    # 전월 일 평균
    prev_avg_new = (
        round(prev_new_count / prev_working_days, 1)
        if prev_working_days > 0
        else 0
    )
    prev_avg_revisit = (
        round(prev_revisit_count / prev_working_days, 1)
        if prev_working_days > 0
        else 0
    )
    prev_avg_ninety = (
        round(prev_ninety_count / prev_working_days, 1)
        if prev_working_days > 0
        else 0
    )
    prev_avg_total = (
        round(prev_total / prev_working_days, 1) if prev_working_days > 0 else 0
    )

    # 테이블 데이터 구성
    table_data = {
        "headers": ["시기", "신환", "재진", "90일초진"],
        "rows": [
            [
                "당월",
                f"{current_avg_new}명",
                f"{current_avg_revisit}명",
                f"{current_avg_ninety}명",
            ],
            [
                "전월",
                f"{prev_avg_new}명",
                f"{prev_avg_revisit}명",
                f"{prev_avg_ninety}명",
            ],
        ],
    }

    # 월별 총 환자수 차트 데이터 (최근 6개월)
    labels = []
    total_counts = []

    for i in range(5, -1, -1):  # 6개월 전부터 현재까지
        month_date = today - relativedelta(months=i)
        month_records = PatientRecord.objects.filter(
            visit_at__year=month_date.year, visit_at__month=month_date.month
        )
        count = month_records.count()

        labels.append(month_date.strftime("%Y년 %m월"))
        total_counts.append(count)

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": "총 환자수",
                "data": total_counts,
                "backgroundColor": "rgba(57, 85, 180, 0.5)",  # primary color
                "borderColor": "rgb(57, 85, 180)",
                "borderWidth": 2,
            }
        ],
    }

    # 매출 통계 (환자당 평균 진료비를 5만원으로 가정한 예시)
    # 실제 매출 데이터가 추가되면 이 부분을 실제 계산으로 교체
    avg_payment_per_patient = 50000

    current_total_revenue = current_total * avg_payment_per_patient
    current_avg_daily_revenue = (
        round(current_total_revenue / current_working_days)
        if current_working_days > 0
        else 0
    )

    # 진료과별 매출 통계 (상위 5개)
    room_stats = []
    room_data = (
        current_month_records.values("room")
        .annotate(patient_count=Count("id"))
        .order_by("-patient_count")[:5]
    )

    for item in room_data:
        room_revenue = item["patient_count"] * avg_payment_per_patient
        room_stats.append(
            {
                "room": item["room"],
                "patient_count": item["patient_count"],
                "revenue": room_revenue,
            }
        )

    room_revenue_table_data = {
        "headers": ["진료실", "환자수", "예상매출"],
        "rows": [
            [
                item["room"],
                f"{item['patient_count']}명",
                f"{item['revenue']:,}원",
            ]
            for item in room_stats
        ],
    }

    # 총계
    temp_rows = [454_396_290, 657, 2_265, 30, 15_146_543, 147_810, 76, 19, 4]

    revenue_table_data = {
        "headers": [
            "총 매출",
            "총 초진",
            "총 재진",
            "진료일",
            "매출(평균)",
            "건당진료(평균)",
            "평균 재진",
            "평균 신환",
            "평균 90일 초진",
        ],
        "rows": [temp_rows],
    }

    # 일별 매출 데이터 계산 (캘린더용)
    daily_revenue = {}
    daily_stats = (
        current_month_records.values("visit_at__date")
        .annotate(patient_count=Count("id"))
        .order_by("visit_at__date")
    )

    for item in daily_stats:
        date = item["visit_at__date"]
        patient_count = item["patient_count"]
        revenue = patient_count * avg_payment_per_patient

        daily_revenue[date.day] = {
            "patient_count": patient_count,
            "revenue": revenue,
        }

    context.update(
        {
            "current_month": today.strftime("%Y년 %m월"),
            "prev_month": prev_month_date.strftime("%Y년 %m월"),
            "table_data": table_data,
            "chart_data": json.dumps(chart_data),
            "chart_height": 320,
            # 당월 평균
            "current_avg_new": current_avg_new,
            "current_avg_revisit": current_avg_revisit,
            "current_avg_ninety": current_avg_ninety,
            "current_avg_total": current_avg_total,
            # 전월 평균
            "prev_avg_new": prev_avg_new,
            "prev_avg_revisit": prev_avg_revisit,
            "prev_avg_ninety": prev_avg_ninety,
            "prev_avg_total": prev_avg_total,
            # 매출 통계
            "room_revenue_table_data": room_revenue_table_data,
            "current_total_revenue": current_total_revenue,
            "current_avg_daily_revenue": current_avg_daily_revenue,
            # 총계
            "revenue_table_data": revenue_table_data,
            # 일별 매출 데이터 (캘린더용)
            "daily_revenue_data": json.dumps(daily_revenue),
            "current_year": today.year,
            "current_month_number": today.month,
        }
    )

    return context


@login_required
def patient_records_dashboard(request):
    """환자 진료 기록 대시보드"""

    # 현재 날짜 기준 당월/전월 계산
    today = datetime.now()
    current_month = today.strftime("%Y-%m")

    # 전월 계산
    previous_month_date = today - relativedelta(months=1)
    previous_month = previous_month_date.strftime("%Y-%m")

    # 당월 데이터
    current_month_data = PatientRecord.objects.filter(
        visit_at__year=today.year, visit_at__month=today.month
    )

    # 전월 데이터
    previous_month_data = PatientRecord.objects.filter(
        visit_at__year=previous_month_date.year,
        visit_at__month=previous_month_date.month,
    )

    # 당월 통계 (신환/재진 구분)
    current_new_patients = current_month_data.filter(visit_type="초진").count()
    current_return_patients = current_month_data.filter(
        visit_type="재진"
    ).count()
    current_total = current_month_data.count()
    current_total_payment = (
        current_month_data.aggregate(total=Sum("payment_amount"))["total"] or 0
    )

    # 전월 통계
    previous_new_patients = previous_month_data.filter(
        visit_type="초진"
    ).count()
    previous_return_patients = previous_month_data.filter(
        visit_type="재진"
    ).count()
    previous_total = previous_month_data.count()
    previous_total_payment = (
        previous_month_data.aggregate(total=Sum("payment_amount"))["total"] or 0
    )

    # 당월 일 평균 계산 (현재까지의 날짜로 계산)
    current_day = today.day
    current_avg_new = (
        round(current_new_patients / current_day, 1) if current_day > 0 else 0
    )
    current_avg_return = (
        round(current_return_patients / current_day, 1)
        if current_day > 0
        else 0
    )
    current_avg_total = (
        round(current_total / current_day, 1) if current_day > 0 else 0
    )

    # 전월 일 평균 계산 (전월의 총 일수로 계산)
    previous_month_days = (
        previous_month_date.replace(day=28) + timedelta(days=4)
    ).replace(day=1) - timedelta(days=1)
    previous_days = previous_month_days.day
    previous_avg_new = (
        round(previous_new_patients / previous_days, 1)
        if previous_days > 0
        else 0
    )
    previous_avg_return = (
        round(previous_return_patients / previous_days, 1)
        if previous_days > 0
        else 0
    )
    previous_avg_total = (
        round(previous_total / previous_days, 1) if previous_days > 0 else 0
    )

    # 진료과별 통계 (당월)
    department_stats = (
        current_month_data.values("room")
        .annotate(
            total_count=Count("id"),
            new_count=Count("id", filter=Q(visit_type="신환")),
            return_count=Count("id", filter=Q(visit_type="재진")),
        )
        .order_by("-total_count")
    )

    # 최근 진료 기록 (10개)
    recent_records = PatientRecord.objects.all()[:10]

    context = {
        "current_month": current_month,
        "previous_month": previous_month,
        # 당월 통계
        "current_new_patients": current_new_patients,
        "current_return_patients": current_return_patients,
        "current_total": current_total,
        "current_total_payment": current_total_payment,
        "current_avg_new": current_avg_new,
        "current_avg_return": current_avg_return,
        "current_avg_total": current_avg_total,
        # 전월 통계
        "previous_new_patients": previous_new_patients,
        "previous_return_patients": previous_return_patients,
        "previous_total": previous_total,
        "previous_total_payment": previous_total_payment,
        "previous_avg_new": previous_avg_new,
        "previous_avg_return": previous_avg_return,
        "previous_avg_total": previous_avg_total,
        # 기타
        "department_stats": department_stats,
        "recent_records": recent_records,
    }

    return render(request, "record/patient_records_dashboard.html", context)


@login_required
def patient_monthly_stats_api(request):
    """환자 진료 기록 월별 통계 API (차트용)"""

    # 최근 6개월 데이터
    monthly_data = (
        PatientRecord.objects.annotate(month=TruncMonth("visit_at"))
        .values("month")
        .annotate(
            total_count=Count("id"),
            new_count=Count("id", filter=Q(visit_type="초진")),
            return_count=Count("id", filter=Q(visit_type="재진")),
            total_payment=Sum("payment_amount"),
        )
        .order_by("month")
    )

    # 데이터 포맷팅
    labels = []
    total_patients = []
    new_patients = []
    return_patients = []
    total_payments = []

    for item in monthly_data:
        labels.append(item["month"].strftime("%Y-%m") if item["month"] else "")
        total_patients.append(item["total_count"])
        new_patients.append(item["new_count"])
        return_patients.append(item["return_count"])
        total_payments.append(float(item["total_payment"] or 0))

    data = {
        "labels": labels,
        "total_patients": total_patients,
        "new_patients": new_patients,
        "return_patients": return_patients,
        "total_payments": total_payments,
    }

    return JsonResponse(data)


@login_required
def patient_department_stats_api(request):
    """환자 진료 기록 진료과별 통계 API"""

    department_data = (
        PatientRecord.objects.values("room")
        .annotate(
            total_count=Count("id"),
            new_count=Count("id", filter=Q(visit_type="초진")),
            return_count=Count("id", filter=Q(visit_type="재진")),
            total_payment=Sum("payment_amount"),
        )
        .order_by("-total_count")
    )

    # 데이터 포맷팅
    departments = []
    total_counts = []
    new_counts = []
    return_counts = []
    total_payments = []

    for item in department_data:
        departments.append(item["department"])
        total_counts.append(item["total_count"])
        new_counts.append(item["new_count"])
        return_counts.append(item["return_count"])
        total_payments.append(float(item["total_payment"] or 0))

    data = {
        "departments": departments,
        "total_counts": total_counts,
        "new_counts": new_counts,
        "return_counts": return_counts,
        "total_payments": total_payments,
    }

    return JsonResponse(data)


@login_required
def monthly_comparison_api(request):
    """월별 비교 통계 API (date_filter용)"""
    year = request.GET.get("year")
    month = request.GET.get("month")

    # 파라미터가 없으면 현재 월 사용
    if not year or not month:
        today = timezone.now()
        year = today.year
        month = today.month
    else:
        year = int(year)
        month = int(month)

    # 당월 데이터
    current_month_records = PatientRecord.objects.filter(
        visit_at__year=year, visit_at__month=month
    )
    current_working_days = (
        current_month_records.values("visit_at__date").distinct().count()
    )

    # 일매출 평균

    current_new_count = current_month_records.filter(
        Q(visit_type__icontains="신환") | Q(visit_type__icontains="신")
    ).count()
    current_revisit_count = current_month_records.filter(
        Q(visit_type__icontains="재진") | Q(visit_type__icontains="재")
    ).count()
    current_ninety_count = current_month_records.filter(
        Q(visit_type__icontains="90")
    ).count()

    current_avg_new = (
        round(current_new_count / current_working_days, 1)
        if current_working_days > 0
        else 0
    )
    current_avg_revisit = (
        round(current_revisit_count / current_working_days, 1)
        if current_working_days > 0
        else 0
    )
    current_avg_ninety = (
        round(current_ninety_count / current_working_days, 1)
        if current_working_days > 0
        else 0
    )
    current_avg_total = round(
        current_avg_new + current_avg_revisit + current_avg_ninety, 1
    )

    # 전월 데이터
    current_date = datetime(year, month, 1)
    prev_month_date = current_date - relativedelta(months=1)
    prev_month_records = PatientRecord.objects.filter(
        visit_at__year=prev_month_date.year,
        visit_at__month=prev_month_date.month,
    )
    prev_working_days = (
        prev_month_records.values("visit_at__date").distinct().count()
    )
    prev_new_count = prev_month_records.filter(
        Q(visit_type__icontains="신환") | Q(visit_type__icontains="신")
    ).count()
    prev_revisit_count = prev_month_records.filter(
        Q(visit_type__icontains="재진") | Q(visit_type__icontains="재")
    ).count()
    prev_ninety_count = prev_month_records.filter(
        Q(visit_type__icontains="90")
    ).count()

    prev_avg_new = (
        round(prev_new_count / prev_working_days, 1)
        if prev_working_days > 0
        else 0
    )
    prev_avg_revisit = (
        round(prev_revisit_count / prev_working_days, 1)
        if prev_working_days > 0
        else 0
    )
    prev_avg_ninety = (
        round(prev_ninety_count / prev_working_days, 1)
        if prev_working_days > 0
        else 0
    )
    prev_avg_total = round(prev_avg_new + prev_avg_revisit + prev_avg_ninety, 1)

    data = {
        "current_month": {
            "신환": current_avg_new,
            "재진": current_avg_revisit,
            "90일초진": current_avg_ninety,
            "총합": current_avg_total,
        },
        "prev_month": {
            "신환": prev_avg_new,
            "재진": prev_avg_revisit,
            "90일초진": prev_avg_ninety,
            "총합": prev_avg_total,
        },
        "daily_sales": {
            "curr": 100,
            "prev": 100,
            "curr_cnt": 18,
            "prev_cnt": 23,
        },
    }
    return JsonResponse(data)
