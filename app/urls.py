"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

# Admin 사이트 커스터마이징
admin.site.site_header = "병원 ERP 관리 시스템"
admin.site.site_title = "병원 ERP"
admin.site.index_title = "관리자 메뉴"

urlpatterns = [
    # Core views
    path("core/", include("core.urls")),
    # Admin 커스텀 뷰 (admin/ 앞에 위치해야 함)
    path(
        "admin/",
        RedirectView.as_view(
            url="/admin/dashboard/bestrevenue/", permanent=False
        ),
    ),
    path("admin/", admin.site.urls),
    path("record/", include("record.urls")),
]

# Debug Toolbar (개발 환경에서만)
if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
    # 미디어 파일 서빙 (개발 환경에서만)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
