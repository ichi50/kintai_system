from django.urls import path
from . import views

app_name = 'scheduling'

urlpatterns = [
    
    path('request/', views.request_shift, name='request_shift'),
    path('submit_individual_shift/', views.submit_individual_shift, name='submit_individual_shift'),
    path('cancel_individual_shift/', views.cancel_individual_shift, name='cancel_individual_shift'),
    path('submit_weekly_shift/', views.submit_weekly_shift, name='submit_weekly_shift'),
]