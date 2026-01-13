import json
from datetime import datetime
from typing import TypedDict

from dateutil.relativedelta import relativedelta
from django.contrib import admin
from django.shortcuts import render
from django.utils import timezone
from unfold.admin import ModelAdmin
from unfold.components import BaseComponent, register_component

from record.models import DailyStatistics, GlobalStatistics, MonthlyStatistics

from .models import ERD, BestRevenue, Dashboard1, Evaluate, Graph


@register_component
class LineChartComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "height": 320,
                "data": json.dumps({"labels": context["data"]["labels"], "datasets": context["data"]["datasets"]}),
            }
        )

        return context


@register_component
class BarChartComponent(BaseComponent):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chart_data = context["data"]

        context.update(
            {
                "height": 320,
                "data": json.dumps({"labels": chart_data["labels"], "datasets": chart_data["datasets"]}),
                "options": json.dumps(chart_data.get("options", {})),
            }
        )

        return context


class Dashboard(ModelAdmin):  # 대쉬보드용 base component
    def has_add_permission(self, request):
        """추가 권한 없음 (읽기 전용)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 권한 없음 (읽기 전용)"""
        return False

    def has_change_permission(self, request, obj=None):
        """수정 권한 없음 (읽기 전용)"""
        return False


@admin.register(BestRevenue)
class BestRevenueAdmin(Dashboard):
    """최고 매출 Dashboard"""

    def changelist_view(self, request, extra_context=None):
        """커스텀 빈 페이지를 렌더링"""
        context = {
            **self.admin_site.each_context(request),
            "title": "최고매출",
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }
        if extra_context:
            context.update(extra_context)

        # TODO 이럴때 그냥 "관리자에게 문의하십시오" 페이지로 보내기, sentry 연동 고려
        selected_hospital_id = request.session.get("selected_hospital_id")
        if not selected_hospital_id:
            raise ValueError("Selected hospital ID not found in session.")

        # 월별 최고 데이터
        max_monthly_patients = GlobalStatistics.get_value("max_monthly_patients", selected_hospital_id, {})
        max_monthly_revenue = GlobalStatistics.get_value("max_monthly_revenue", selected_hospital_id, {})

        # 일별 최고 데이터
        max_daily_patients = GlobalStatistics.get_value("max_daily_patients", selected_hospital_id, {})
        max_daily_revenue = GlobalStatistics.get_value("max_daily_revenue", selected_hospital_id, {})

        # 요일별 최고 데이터 (GlobalStatistics에서 조회)
        weekday_revenue_data = GlobalStatistics.get_value("max_weekday_revenue", selected_hospital_id, {})
        weekday_patients_data = GlobalStatistics.get_value("max_weekday_patients", selected_hospital_id, {})
        # 데이터 변환 (admin.py에서 사용하는 형식으로)
        weekday_stats = {
            "revenue": [weekday_revenue_data.get(str(i), {"amount": 0, "date": "-"}) for i in range(7)],
            "patients": [weekday_patients_data.get(str(i), {"count": 0, "date": "-"}) for i in range(7)],
        }

        # 최근 12개월 월별 매출 차트 데이터
        monthly_revenue_chart = self._get_monthly_revenue_chart_data(selected_hospital_id)

        # 최근 7일 일별 매출 차트 데이터
        daily_revenue_chart = self._get_daily_revenue_chart_data(selected_hospital_id)

        context.update(
            {
                "table_month": {  # 월 최고
                    "headers": ["병원이름", "최고환자수(월)", "갱신일", "최고매출(월)", "갱신일"],
                    "rows": [
                        [
                            "오픈 정형외과 압구정",
                            f"{max_monthly_patients.get('count', 0):,}명",
                            f"{max_monthly_patients.get('year', 0)}.{max_monthly_patients.get('month', 0):02d}",
                            f"{max_monthly_revenue.get('amount', 0):,}원",
                            f"{max_monthly_revenue.get('year', 0)}.{max_monthly_revenue.get('month', 0):02d}",
                        ],
                    ],
                },
                "cohort_week": {
                    "headers": [
                        {"title": "일"},
                        {"title": "월"},
                        {"title": "화"},
                        {"title": "수"},
                        {"title": "목"},
                        {"title": "금"},
                        {"title": "토"},
                    ],
                    "rows": [
                        # 최고환자수 행
                        {
                            "header": {
                                "title": "최고환자수",
                                "subtitle": "갱신일",
                            },
                            "cols": [
                                {
                                    "value": f"{weekday_stats['patients'][6]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][6]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['patients'][0]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][0]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['patients'][1]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][1]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['patients'][2]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][2]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['patients'][3]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][3]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['patients'][4]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][4]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['patients'][5]['count']:,}명",
                                    "subtitle": weekday_stats["patients"][5]["date"],
                                },
                            ],
                        },
                        # 최고매출 행
                        {
                            "header": {
                                "title": "최고매출",
                                "subtitle": "갱신일",
                            },
                            "cols": [
                                {
                                    "value": f"{weekday_stats['revenue'][6]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][6]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['revenue'][0]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][0]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['revenue'][1]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][1]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['revenue'][2]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][2]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['revenue'][3]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][3]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['revenue'][4]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][4]["date"],
                                },
                                {
                                    "value": f"{weekday_stats['revenue'][5]['amount']:,}원",
                                    "subtitle": weekday_stats["revenue"][5]["date"],
                                },
                            ],
                        },
                    ],
                },
                "table_day": {
                    "headers": ["", "최고환자수", "갱신일", "최고매출", "갱신일"],
                    "rows": [
                        [
                            "일별 최고",
                            f"{max_daily_patients.get('count', 0):,}명",
                            max_daily_patients.get("date", "-"),
                            f"{max_daily_revenue.get('amount', 0):,}원",
                            max_daily_revenue.get("date", "-"),
                        ],
                    ],
                },
                "monthly_revenue_chart": monthly_revenue_chart,
                "daily_revenue_chart": daily_revenue_chart,
            }
        )

        return render(request, "admin/dashboard/bestrevenue.html", context)

    def _get_monthly_revenue_chart_data(self, hospital_id=None):
        """최근 12개월 월별 매출 차트 데이터 생성"""
        today = timezone.now()
        labels = []
        revenue_data = []

        # 최근 12개월 데이터 조회
        for i in range(11, -1, -1):  # 12개월 전부터 현재까지
            month_date = today - relativedelta(months=i)
            year = month_date.year
            month = month_date.month

            # 월별 통계 조회
            try:
                monthly_stat = MonthlyStatistics.objects.get(year=year, month=month, hospital_id=hospital_id)
                revenue = int(monthly_stat.total_revenue)
            except MonthlyStatistics.DoesNotExist:
                revenue = 0

            labels.append(f"{year}.{month:02d}")
            revenue_data.append(revenue)

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "월별 매출",
                    "data": revenue_data,
                    "type": "line",
                    "borderColor": "rgb(34, 197, 94)",
                    "backgroundColor": "rgba(34, 197, 94, 0.1)",
                    "tension": 0.4,
                }
            ],
        }

    def _get_daily_revenue_chart_data(self, hospital_id=None):
        """최근 7일 일별 매출 차트 데이터 생성"""
        from datetime import timedelta

        today = timezone.now().date()
        labels = []
        revenue_data = []

        # 최근 7일 데이터 조회
        for i in range(6, -1, -1):  # 7일 전부터 오늘까지
            date = today - timedelta(days=i)

            # 일별 통계 조회
            try:
                daily_stat = DailyStatistics.objects.select_related("manual_record").get(
                    manual_record__date=date, manual_record__hospital_id=hospital_id
                )
                revenue = daily_stat.total_revenue
            except DailyStatistics.DoesNotExist:
                revenue = 0

            labels.append(f"{date.month}/{date.day}")
            revenue_data.append(revenue)

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "일별 매출",
                    "data": revenue_data,
                    "type": "line",
                    "borderColor": "rgb(34, 197, 94)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4,
                }
            ],
        }


class MonthlyStats(TypedDict):
    """월별 통계 데이터 구조"""

    working_days: int
    new_count: int
    revisit_count: int
    ninety_count: int
    total_count: int
    avg_new: float
    avg_revisit: float
    avg_ninety: float
    avg_total: float
    channel_counts: dict[str, int]
    total_revenue: int


@admin.register(Evaluate)
class EvaluateAdmin(Dashboard):
    """병원 현황 (일평균) Dashboard"""

    # 내원 경로 채널 목록
    VISIT_CHANNELS = ["인터넷", "간판", "소개", "전화", "재방문", "기타"]

    def changelist_view(self, request, extra_context=None):
        context = {
            **self.admin_site.each_context(request),
            "title": "병원 현황 (일평균)",
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }
        if extra_context:
            context.update(extra_context)

        # GET 파라미터에서 year/month 가져오기
        year = request.GET.get("year")
        month = request.GET.get("month")
        hospital_id = request.session.get("selected_hospital_id")
        if not hospital_id:
            raise ValueError("Selected hospital ID not found in session.")

        if not year or not month:
            today = timezone.now()
            year = today.year
            month = today.month
        else:
            year = int(year)
            month = int(month)
            today = datetime(year, month, 1)
            today = timezone.make_aware(today)

        # 당월 통계
        curr_stats = self.calculate_monthly_stats(year, month, hospital_id=hospital_id)
        curr_working_days = curr_stats["working_days"]
        curr_total_count = curr_stats["total_count"]
        curr_avg_new = curr_stats["avg_new"]
        curr_avg_revisit = curr_stats["avg_revisit"]
        curr_avg_ninety = curr_stats["avg_ninety"]
        curr_avg_total = curr_stats["avg_total"]
        curr_channel_counts = curr_stats["channel_counts"]
        curr_total_revenue = curr_stats["total_revenue"]

        # 전월 통계
        prev_month_date = today - relativedelta(months=1)
        prev_stats = self.calculate_monthly_stats(prev_month_date.year, prev_month_date.month, hospital_id=hospital_id)
        prev_working_days = prev_stats["working_days"]
        prev_total_count = prev_stats["total_count"]
        prev_avg_new = prev_stats["avg_new"]
        prev_avg_revisit = prev_stats["avg_revisit"]
        prev_avg_ninety = prev_stats["avg_ninety"]
        prev_avg_total = prev_stats["avg_total"]
        prev_channel_counts = prev_stats["channel_counts"]
        prev_total_revenue = curr_stats["total_revenue"]

        # 건당 진료비 (총 매출 / 총 진료 건수)
        current_fee_per_case = round(curr_total_revenue / curr_total_count) if curr_total_count > 0 else 0
        prev_fee_per_case = round(prev_total_revenue / prev_total_count) if prev_total_count > 0 else 0
        # 테이블 데이터 구성
        curr_total_visits = sum(curr_channel_counts.values())
        prev_total_visits = sum(prev_channel_counts.values())

        table_visit = {
            "headers": ["", "인터넷", "간판", "소개", "전화", "재방문", "기타", "합계"],
            "rows": [
                # 월건수(당월)
                [
                    "월건수(당월)",
                    *[f"{curr_channel_counts[ch]}건" for ch in self.VISIT_CHANNELS],
                    f"{curr_total_visits}건",
                ],
                # 일건수(당월) - 마감일지 수로 나눔
                [
                    "일건수(당월)",
                    *[
                        f"{round(curr_channel_counts[ch] / curr_working_days, 1) if curr_working_days > 0 else 0}건"
                        for ch in self.VISIT_CHANNELS
                    ],
                    f"{round(curr_total_visits / curr_working_days, 1) if curr_working_days > 0 else 0}건",
                ],
                # 월건수(전월)
                [
                    "월건수(전월)",
                    *[f"{prev_channel_counts[ch]}건" for ch in self.VISIT_CHANNELS],
                    f"{prev_total_visits}건",
                ],
                # 일건수(전월) - 마감일지 수로 나눔
                [
                    "일건수(전월)",
                    *[
                        f"{round(prev_channel_counts[ch] / prev_working_days, 1) if prev_working_days > 0 else 0}건"
                        for ch in self.VISIT_CHANNELS
                    ],
                    f"{round(prev_total_visits / prev_working_days, 1) if prev_working_days > 0 else 0}건",
                ],
            ],
        }

        context.update(
            {
                "current_month": today.strftime("%Y년 %m월"),
                "prev_month": prev_month_date.strftime("%Y년 %m월"),
                # 당월 평균
                "current_avg_new": curr_avg_new,
                "current_avg_revisit": curr_avg_revisit,
                "current_avg_ninety": curr_avg_ninety,
                "current_avg_total": curr_avg_total,
                # 전월 평균
                "prev_avg_new": prev_avg_new,
                "prev_avg_revisit": prev_avg_revisit,
                "prev_avg_ninety": prev_avg_ninety,
                "prev_avg_total": prev_avg_total,
                # 건당 진료비
                "current_fee_per_case": current_fee_per_case,
                "prev_fee_per_case": prev_fee_per_case,
                # 내원 경로
                "table_visit": table_visit,
                # 일 매출 평균
                "current_avg_daily_revenue": curr_total_revenue / curr_working_days if curr_working_days > 0 else 0,
                "prev_avg_daily_revenue": prev_total_revenue / prev_working_days if prev_working_days > 0 else 0,
            }
        )

        return render(request, "admin/dashboard6.html", context)
        # 월별 통계 계산 함수

    def calculate_monthly_stats(self, year: int, month: int, hospital_id=None) -> MonthlyStats:
        """특정 월의 환자 통계 조회 (캐시된 데이터 사용)"""
        from record.models import MonthlyStatistics

        try:
            # 월별 통계 테이블에서 직접 조회 (95% 이상 빠름)
            monthly_stat = MonthlyStatistics.objects.get(year=year, month=month, hospital_id=hospital_id)

            return {
                "working_days": monthly_stat.working_days,
                "new_count": monthly_stat.total_new_patients,
                "revisit_count": monthly_stat.total_revisit_patients,
                "ninety_count": monthly_stat.total_ninety_patients,
                "total_count": monthly_stat.total_patients,
                "avg_new": monthly_stat.avg_new_patients,
                "avg_revisit": monthly_stat.avg_revisit_patients,
                "avg_ninety": monthly_stat.avg_ninety_patients,
                "avg_total": monthly_stat.avg_total_patients,
                "channel_counts": monthly_stat.channel_counts,
                "total_revenue": int(monthly_stat.total_revenue),
            }
        except MonthlyStatistics.DoesNotExist:
            # 데이터가 없으면 빈 통계 반환
            return {
                "working_days": 0,
                "new_count": 0,
                "revisit_count": 0,
                "ninety_count": 0,
                "total_count": 0,
                "avg_new": 0,
                "avg_revisit": 0,
                "avg_ninety": 0,
                "avg_total": 0,
                "channel_counts": dict.fromkeys(self.VISIT_CHANNELS, 0),
                "total_revenue": 0,
            }


@admin.register(Dashboard1)
class Dashboard1Admin(ModelAdmin):
    """병원 일지 Admin"""

    def changelist_view(self, request, extra_context=None):
        """커스텀 빈 페이지를 렌더링"""
        from django.shortcuts import render

        context = {
            **self.admin_site.each_context(request),
            "title": "병원 현황(일평균)",
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }
        if extra_context:
            context.update(extra_context)

        # Mock Data
        context["table_1"] = {  # 일 평균 내원 환자
            "headers": ["시기", "신환", "재진", "90일초진"],
            "rows": [
                [
                    "당월",
                    "10명",
                    "20명",
                    "30명",
                ],
                [
                    "전월",
                    "15명",
                    "25명",
                    "35명",
                ],
            ],
        }

        context["table_2"] = {  # 건당 진료비 / 일매출
            "headers": ["시기", "건당진료비", "일매출(30일)"],
            "rows": [
                [
                    "당월",
                    "147,810원",
                    "15,147,543원",
                ],
                [
                    "전월",
                    "147,810원",
                    "15,147,543원",
                ],
            ],
        }

        context["table_3"] = {  # 연령별 월건수/일건수
            "headers": ["", "~10", "10대", "20대", "30대", "40대", "50대", "60대", "70대", "80대"],
            "rows": [
                [
                    "월건수(당월)",
                    "10명",
                    "25명",
                    "42명",
                    "55명",
                    "68명",
                    "73명",
                    "51명",
                    "32명",
                    "15명",
                ],
                [
                    "일건수(당월)",
                    "8명",
                    "22명",
                    "38명",
                    "52명",
                    "65명",
                    "70명",
                    "48명",
                    "30명",
                    "12명",
                ],
                [
                    "월건수(전월)",
                    "10명",
                    "25명",
                    "42명",
                    "55명",
                    "68명",
                    "73명",
                    "51명",
                    "32명",
                    "15명",
                ],
                [
                    "일건수(전월)",
                    "8명",
                    "22명",
                    "38명",
                    "52명",
                    "65명",
                    "70명",
                    "48명",
                    "30명",
                    "12명",
                ],
            ],
        }

        context["table_4"] = {  # 내원 경로
            "headers": ["", "인터넷", "간판", "소개", "전화", "재방문", "기타", "합계"],
            "rows": [
                [
                    "월건수(당월)",
                    "150건",
                    "230건",
                    "180건",
                    "95건",
                    "340건",
                    "45건",
                    "1,040건",
                ],
                [
                    "일건수(당월)",
                    "5건",
                    "8건",
                    "6건",
                    "3건",
                    "11건",
                    "2건",
                    "35건",
                ],
                [
                    "월금액(당월)",
                    "22,500,000원",
                    "34,500,000원",
                    "27,000,000원",
                    "14,250,000원",
                    "51,000,000원",
                    "6,750,000원",
                    "156,000,000원",
                ],
                [
                    "월건수(전월)",
                    "145건",
                    "220건",
                    "175건",
                    "90건",
                    "330건",
                    "40건",
                    "1,000건",
                ],
                [
                    "일건수(전월)",
                    "5건",
                    "7건",
                    "6건",
                    "3건",
                    "11건",
                    "1건",
                    "33건",
                ],
                [
                    "월금액(전월)",
                    "21,750,000원",
                    "33,000,000원",
                    "26,250,000원",
                    "13,500,000원",
                    "49,500,000원",
                    "6,000,000원",
                    "150,000,000원",
                ],
            ],
        }

        return render(request, "admin/dashboard1.html", context)


@admin.register(Graph)
class GraphAdmin(Dashboard):
    """그래프 현황 Admin"""

    # 차트 색상 상수
    CHART_PRIMARY_COLOR = "rgb(59, 130, 246)"
    CHART_PRIMARY_BG_COLOR = "rgba(59, 130, 246, 0.1)"

    def changelist_view(self, request, extra_context=None):
        """커스텀 빈 페이지를 렌더링"""
        from dateutil.relativedelta import relativedelta
        from django.shortcuts import render

        context = {
            **self.admin_site.each_context(request),
            "title": "그래프 현황",
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }
        if extra_context:
            context.update(extra_context)

        # GET 파라미터에서 날짜 범위 가져오기
        start_year = request.GET.get("start_year")
        start_month = request.GET.get("start_month")
        end_year = request.GET.get("end_year")
        end_month = request.GET.get("end_month")

        today = timezone.now()

        # 파라미터가 있으면 해당 범위 사용, 없으면 최근 12개월
        if start_year and start_month and end_year and end_month:
            start_date = datetime(int(start_year), int(start_month), 1)
            end_date = datetime(int(end_year), int(end_month), 1)
            start_date = timezone.make_aware(start_date)
            end_date = timezone.make_aware(end_date)
        else:
            # 최근 12개월 (11개월 전부터 현재까지)
            start_date = today - relativedelta(months=11)
            end_date = today

        # 한 번에 MonthlyStatistics 조회 (성능 최적화)
        monthly_stats_queryset = MonthlyStatistics.objects.filter(
            year__gte=start_date.year,
            year__lte=end_date.year,
        ).order_by("year", "month")

        # 딕셔너리로 변환하여 빠른 조회
        stats_dict = {(stat.year, stat.month): stat for stat in monthly_stats_queryset}

        # 차트 데이터 생성
        patient_type_chart_data = self._get_patient_type_chart_data(start_date, end_date, stats_dict)
        total_count_chart_data = self._get_total_count_chart_data(start_date, end_date, stats_dict)
        revenue_per_case_chart_data = self._get_revenue_per_case_chart_data(start_date, end_date, stats_dict)
        daily_avg_revenue_chart_data = self._get_daily_avg_revenue_chart_data(start_date, end_date, stats_dict)

        context.update(
            {
                "patient_type_chart_data": patient_type_chart_data,
                "total_count_chart_data": total_count_chart_data,
                "revenue_per_case_chart_data": revenue_per_case_chart_data,
                "daily_avg_revenue_chart_data": daily_avg_revenue_chart_data,
                "chart_height": 300,
            }
        )

        return render(request, "admin/dashboard/graph.html", context)

    def _generate_chart_data(self, start_date, end_date, stats_dict, label, data_calculator):
        """공통 차트 데이터 생성 로직"""
        labels = []
        data = []

        current_date = start_date
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month

            # 딕셔너리에서 조회 (이미 로드된 데이터)
            monthly_stat = stats_dict.get((year, month))
            value = data_calculator(monthly_stat)

            labels.append(current_date.strftime("%Y-%m"))
            data.append(value)

            current_date += relativedelta(months=1)

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": label,
                    "data": data,
                    "borderColor": self.CHART_PRIMARY_COLOR,
                    "backgroundColor": self.CHART_PRIMARY_BG_COLOR,
                    "type": "line",
                    "tension": 0.4,
                    "fill": True,
                }
            ],
        }

    def _get_patient_type_chart_data(self, start_date, end_date, stats_dict):
        """월별 환자 유형별 차트 데이터 생성 (Stacked Bar Chart)"""
        labels = []
        new_patients = []
        revisit_patients = []
        ninety_patients = []
        no_billing_patients = []

        current_date = start_date
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month

            # 딕셔너리에서 조회 (이미 로드된 데이터)
            monthly_stat = stats_dict.get((year, month))
            if monthly_stat:
                new_count = monthly_stat.total_new_patients
                revisit_count = monthly_stat.total_revisit_patients
                ninety_count = monthly_stat.total_ninety_patients
                total_count = monthly_stat.total_patients
                # 산정안함 = 총환자 - (신환 + 재진 + 90일초진)
                no_billing_count = total_count - (new_count + revisit_count + ninety_count)
            else:
                new_count = revisit_count = ninety_count = no_billing_count = 0

            labels.append(current_date.strftime("%Y-%m"))
            new_patients.append(new_count)
            revisit_patients.append(revisit_count)
            ninety_patients.append(ninety_count)
            no_billing_patients.append(no_billing_count)

            current_date += relativedelta(months=1)

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "신환",
                    "data": new_patients,
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgb(59, 130, 246)",
                    "borderWidth": 1,
                },
                {
                    "label": "재진",
                    "data": revisit_patients,
                    "backgroundColor": "rgba(34, 197, 94, 0.8)",
                    "borderColor": "rgb(34, 197, 94)",
                    "borderWidth": 1,
                },
                {
                    "label": "90일초진",
                    "data": ninety_patients,
                    "backgroundColor": "rgba(168, 85, 247, 0.8)",
                    "borderColor": "rgb(168, 85, 247)",
                    "borderWidth": 1,
                },
                {
                    "label": "산정안함",
                    "data": no_billing_patients,
                    "backgroundColor": "rgba(239, 68, 68, 0.8)",
                    "borderColor": "rgb(239, 68, 68)",
                    "borderWidth": 1,
                },
            ],
            "options": {
                "scales": {
                    "x": {
                        "stacked": True,
                    },
                    "y": {
                        "stacked": True,
                    },
                },
            },
        }

    def _get_total_count_chart_data(self, start_date, end_date, stats_dict):
        """월별 총환자수 차트 데이터 생성"""
        return self._generate_chart_data(
            start_date,
            end_date,
            stats_dict,
            "총환자수",
            lambda stat: stat.total_patients if stat else 0,
        )

    def _get_revenue_per_case_chart_data(self, start_date, end_date, stats_dict):
        """월별 건당진료비 차트 데이터 생성"""

        def calculate_revenue_per_case(stat):
            if stat and stat.total_patients > 0:
                return round(stat.total_revenue / stat.total_patients)
            return 0

        return self._generate_chart_data(start_date, end_date, stats_dict, "건당진료비", calculate_revenue_per_case)

    def _get_daily_avg_revenue_chart_data(self, start_date, end_date, stats_dict):
        """월별 일평균 매출 차트 데이터 생성"""

        def calculate_daily_avg_revenue(stat):
            if stat and stat.working_days > 0:
                return round(stat.total_revenue / stat.working_days)
            return 0

        return self._generate_chart_data(start_date, end_date, stats_dict, "일평균 매출", calculate_daily_avg_revenue)


@admin.register(ERD)
class ERDAdmin(Dashboard):
    """ERD 뷰어 (슈퍼유저 전용)"""

    # superuser 전용 권한 (user/admin.py 패턴)
    def has_module_permission(self, request):
        """슈퍼유저만 사이드바에 표시"""
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        """슈퍼유저만 조회 가능"""
        return request.user.is_superuser

    def changelist_view(self, request, extra_context=None):
        """ERD 생성 및 표시"""
        from django.core.cache import cache

        context = {
            **self.admin_site.each_context(request),
            "title": "데이터베이스 ERD",
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }
        if extra_context:
            context.update(extra_context)

        # 캐시 키
        cache_key = "admin_erd_svg"

        # 캐시에서 ERD 가져오기
        erd_svg = cache.get(cache_key)

        # 캐시 미스 시 생성
        if erd_svg is None:
            erd_svg, error = self._generate_erd()
            if error:
                context["error"] = error
            else:
                # 24시간 캐싱
                cache.set(cache_key, erd_svg, 60 * 60 * 24)

        context["erd_svg"] = erd_svg

        return render(request, "admin/dashboard/erd.html", context)

    def _generate_erd(self):
        """django-extensions의 graph_models를 사용하여 ERD 생성"""
        import subprocess

        try:
            # GraphViz 설치 확인
            try:
                subprocess.run(["dot", "-V"], capture_output=True, check=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None, ("GraphViz가 설치되어 있지 않습니다. 다음 명령어로 설치해주세요: brew install graphviz")

            # graph_models 실행 (DOT 형식 출력)
            result = subprocess.run(
                [
                    "python",
                    "manage.py",
                    "graph_models",
                    "-a",  # 모든 앱
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd="/Users/jang-gyuseog/Workspace/opn/hospital-erp",
            )

            if result.returncode != 0:
                return None, f"ERD 생성 실패: {result.stderr}"

            # DOT 출력이 비어있는지 확인
            if not result.stdout or len(result.stdout.strip()) == 0:
                return None, "ERD 데이터가 생성되지 않았습니다."

            # DOT 형식을 SVG로 변환
            svg_result = subprocess.run(
                ["dot", "-Tsvg"], input=result.stdout, capture_output=True, text=True, timeout=30
            )

            if svg_result.returncode != 0:
                return None, f"SVG 변환 실패: {svg_result.stderr}"

            return svg_result.stdout, None

        except subprocess.TimeoutExpired:
            return None, "ERD 생성 시간 초과 (30초)"
        except Exception as e:
            return None, f"예상치 못한 오류: {str(e)}"
