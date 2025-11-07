from django.urls import path
from . import views

app_name = 'kintai'

urlpatterns = [
    # 勤怠アプリのルートパス。views.index（仮）を参照
    path('', views.index, name='index'),
    path('records/', views.record_list, name='record_list'),
]