# kintai_app/models.py
from django.db import models
from django.contrib.auth import get_user_model
from common.models import mst_employee

User = get_user_model()

class ShiftRequest(models.Model):
    """
    ユーザーが特定の日付に申請した希望シフトを保存するモデル
    """
    STATUS_CHOICES = [
        ('pending', '承認待ち'),
        ('approved', '承認済み'),
        ('rejected', '却下'),
    ]

    employee = models.ForeignKey(mst_employee, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    date = models.DateField(verbose_name="申請日")

    start_time = models.TimeField(null=True, blank=True, verbose_name="開始時刻")
    end_time = models.TimeField(null=True, blank=True, verbose_name="終了時刻")
    is_day_off = models.BooleanField(default=False, verbose_name="休み希望")

    # 承認ステータス（カレンダーで色分けするために使用）
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="ステータス"
    )

    class Meta:
        # ユーザーと日付の組み合わせは一意 (同じ日に2回申請できない)
        unique_together = ('user', 'date')
        ordering = ['date']
        verbose_name = "シフト申請"
        verbose_name_plural = "シフト申請"

    def __str__(self):
        return f"{self.user.username} - {self.date}"
class WeeklySchedule(models.Model):
    """
    ユーザーごとの一週間の基本シフト設定を保存するモデル
    """
    DAY_OF_WEEK_CHOICES = (
        (0, '月曜'), (1, '火曜'), (2, '水曜'), (3, '木曜'),
        (4, '金曜'), (5, '土曜'), (6, '日曜'),
    )
    
    employee = models.ForeignKey(mst_employee, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    # 0:月曜, 6:日曜 (ISO 8601に基づき、通常月曜を0または1とするが、ここでは0から6で処理)
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES, verbose_name="曜日") 
    
    start_time = models.TimeField(null=True, blank=True, verbose_name="開始時刻")
    end_time = models.TimeField(null=True, blank=True, verbose_name="終了時刻")
    is_day_off = models.BooleanField(default=False, verbose_name="休み希望")

    class Meta:
        unique_together = ('user', 'day_of_week') # ユーザーと曜日で一意
        verbose_name = "基本スケジュール"
        verbose_name_plural = "基本スケジュール"

    def __str__(self):
        return f"{self.user.username} - {self.get_day_of_week_display()}"