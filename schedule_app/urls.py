from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    # 勤怠アプリのルートパス。views.index（仮）を参照
    path('', views.index, name='index'),
]