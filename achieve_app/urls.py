from django.urls import path
from . import views

app_name = 'achieve_app'

urlpatterns = [
    path('achieve/', views.monthly_work_summary, name='achieve'),
]