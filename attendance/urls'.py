# attendance/urls.py

from django.urls import path
from django.urls import path, include
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 認証システム（ログイン/ログアウト用）
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html'), name='login'),   
    # path('accounts/', include('django.contrib.auth.urls')), 
    
    # 勤怠アプリのURLをルート（'/'）に接続
    path('', include('attendance.urls')),
]