# correction_app/urls.py

from django.urls import path, re_path
from . import views

app_name = 'correction'

urlpatterns = [
    # /correction/ で今月のカレンダー表示
    path('', views.correction_calendar, name='calendar'), 
    # /correction/YYYY/MM/ で指定月のカレンダー表示
    re_path(r'^(?P<year>\d{4})/(?P<month>\d{1,2})/$', views.correction_calendar, name='calendar_month'), 
    
    # 申請処理用のエンドポイント（後で実装）
    path('submit/', views.submit_correction_request, name='submit'),
]