from django.urls import path
from . import views

app_name = 'admin_app'

urlpatterns = [
    # シフト表示画面（今回のメイン）
    path('schedule/daily/', views.daily_shift_display, name='daily_schedule'),
    path('schedule/weekly/', views.weekly_shift_display, name='weekly_schedule'),
    path('create/', views.shift_display, name='create'),      # 仮
    path('correction/', views.shift_display, name='correction'), # 仮
    # 修正依頼の一覧を取得するAPI（サイドバーのモーダル用）
    path('api/requests/', views.get_pending_requests, name='api_requests'),
]