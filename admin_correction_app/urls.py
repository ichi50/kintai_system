from django.urls import path
from . import views

app_name = 'admin_correction_app'

from django.urls import path
from . import views

app_name = 'admin_correction_app'

urlpatterns = [
    # 日次勤怠一覧表示 (例: /admin_correction/daily/)
    path('daily/', views.daily_correction_list, name='daily_attendance_list'),
    
    # 勤怠修正画面 (例: /admin_correction/edit/5/)
    path('edit/<int:attendance_id>/', views.edit_attendance, name='edit_attendance'),
]