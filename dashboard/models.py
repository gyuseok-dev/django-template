from record.models import GlobalStatistics

# ============================================
# 대시보드용 프록시 모델들
# ============================================


class Calendar(GlobalStatistics):
    class Meta:
        proxy = True
        verbose_name = "업무일지 작성 현황"
        verbose_name_plural = "업무일지 작성 현황"


class Graph(GlobalStatistics):
    class Meta:
        proxy = True
        verbose_name = "그래프 현황"
        verbose_name_plural = "그래프 현황"


class Dashboard3(GlobalStatistics):
    class Meta:
        proxy = True
        verbose_name = "비급여 치료"
        verbose_name_plural = "비급여 치료"


class BestRevenue(GlobalStatistics):
    class Meta:
        proxy = True
        verbose_name = "최고매출"
        verbose_name_plural = "최고매출"


class Evaluate(GlobalStatistics):
    class Meta:
        proxy = True
        verbose_name = "병원 현황(일평균)"
        verbose_name_plural = "병원 현황(일평균)"


class ERD(GlobalStatistics):
    """ERD 뷰어용 프록시 모델"""

    class Meta:
        proxy = True
        verbose_name = "ERD"
        verbose_name_plural = "ERD"
