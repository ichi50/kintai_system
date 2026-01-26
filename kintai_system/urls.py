# kintai_system/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. システムパス
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    #path('account/', include('two_factor.urls')),
    # 2. アプリのインクルード
    path('scheduling/', include('scheduling_app.urls')), 
    path('', include('schedule_app.urls')), 
    path('achieve/', include('achieve_app.urls')),
    path('correction/', include('correction_app.urls')),
    path('admin_panel/', include('admin_app.urls')), 
    path('admin_scheduling/', include('admin_scheduling_app.urls')), 
    path('admin_correction/', include('admin_correction_app.urls')), 
]