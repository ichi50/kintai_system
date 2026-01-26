from django.db import models
from common.models import mst_employee # 従業員マスターを参照
from schedule_app.models import trn_daily_attendance # 実績データを参照

# Create your models here.
# 勤怠修正の打刻内容の選択肢
CORRECTION_PUNCH_CHOICES = (
    ('start', '出勤'),
    ('end', '退勤'),
    ('break_start', '休憩開始'),
    ('break_end', '休憩終了'),
)

# 申請のステータス
REQUEST_STATUS_CHOICES = (
    ('pending', '申請中'),
    ('approved', '承認済み'),
    ('rejected', '却下'),
)

class TrnCorrectionRequest(models.Model):
    """勤怠修正申請のヘッダー情報"""
    
    employee = models.ForeignKey(
        mst_employee,
        on_delete=models.CASCADE,
        verbose_name="従業員"
    )
    attendance_date = models.DateField("対象日")
    reason = models.TextField("修正理由", max_length=500)
    status = models.CharField(
        "ステータス",
        max_length=10,
        choices=REQUEST_STATUS_CHOICES,
        default='pending'
    )
    # 申請は特定の実績データ（日次）に対する修正として扱うこともできる
    original_attendance = models.ForeignKey(
        trn_daily_attendance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="元実績データ"
    )
    requested_at = models.DateTimeField("申請日時", auto_now_add=True)
    
    class Meta:
        verbose_name = "勤怠修正申請ヘッダー"
        verbose_name_plural = "勤怠修正申請ヘッダー"
        # 従業員は同じ日に対して複数回修正申請を出すことは通常許可しない
        unique_together = ('employee', 'attendance_date') 

    def __str__(self):
        return f"{self.employee.employee} - {self.attendance_date} ({self.get_status_display()})"


class TrnCorrectionTime(models.Model):
    """勤怠修正申請に含まれる個別の打刻修正項目"""
    
    request = models.ForeignKey(
        TrnCorrectionRequest,
        on_delete=models.CASCADE,
        related_name='correction_times',
        verbose_name="修正申請"
    )
    punch_time = models.DateTimeField("打刻時間（修正後）")
    punch_type = models.CharField(
        "打刻内容",
        max_length=15,
        choices=CORRECTION_PUNCH_CHOICES
    )
    # 複数の打刻項目を順番に処理するために、順序フィールドを追加
    sequence = models.IntegerField("順序", default=0)

    class Meta:
        verbose_name = "勤怠修正打刻項目"
        verbose_name_plural = "勤怠修正打刻項目"
        ordering = ['request', 'sequence']

    def __str__(self):
        return f"{self.request.attendance_date}: {self.get_punch_type_display()} at {self.punch_time.strftime('%H:%M')}"