from django.urls import path
from . import views

app_name = 'admin_scheduling_app'

urlpatterns = [
    path('daily/', views.daily_scheduling, name='daily_scheduling'),
    path('weekly/', views.weekly_scheduling, name='weekly_scheduling'),
    # シフト設定画面（フォームを表示する画面）
    path('edit/', views.shift_edit_form, name='edit_shift'), 
    path('auto-assign/', views.auto_assign_weekly_shifts, name='auto_assign'),
]