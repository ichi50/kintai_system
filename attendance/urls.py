# attendance/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.check_in_out, name='check_in_out'),
    # 他のURL (例: 記録一覧 path('list/', views.AttendanceListView.as_view(), name='attendance_list'))
    path('', include('attendance.urls')),
]