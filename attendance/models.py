from django.db import models

# attendance/models.py

from django.db import models
from django.contrib.auth.models import User # ユーザー認証を使う場合

class AttendanceRecord(models.Model):
    # 誰の記録か (Django標準のUserモデルと連携)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 勤務開始時刻
    check_in = models.DateTimeField(auto_now_add=True)
    
    # 勤務終了時刻
    check_out = models.DateTimeField(null=True, blank=True)
    
    # 備考
    note = models.TextField(blank=True)
    
    def __str__(self):
        return f'{self.user.username} - {self.check_in.strftime("%Y-%m-%d")}'
