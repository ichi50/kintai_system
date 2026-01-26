# schedule_app/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.fields.related import OneToOneField
from common.models import mst_employee

class shift_schedule(models.Model):
    employee = models.ForeignKey(mst_employee,on_delete=models.CASCADE,related_name='schedules',verbose_name="従業員")
    schedule_date = models.DateField("Schedule Date")
    start_time = models.TimeField("Start_Time")
    end_time = models.TimeField("End_Time")
    
    class Meta:
        # 従業員と日付の組み合わせは一意
        unique_together = ('employee', 'schedule_date') 
        verbose_name = "シフトスケジュール"
        verbose_name_plural = "シフトスケジュール"
    
    def __str__(self):
        # 適切な文字列でモデルインスタンスを表現
        return f"{self.employee.user.username} の {self.schedule_date}"

class trn_clocking(models.Model):
    CLOCKING_CHOICES = [
        ('1', '出勤'),
        ('2', '退勤'),
        ('3', '休憩開始'),
        ('4', '休憩終了'),
    ]
    clocking_id = models.BigAutoField("Clocking ID", primary_key=True) 
    employee = models.ForeignKey(mst_employee, on_delete=models.CASCADE)
    clocking_type = models.CharField("Clocking Type", max_length=1, choices=CLOCKING_CHOICES)
    clocking_datetime = models.DateTimeField("Clocking DateTime")
    def __str__(self):
        return f"{self.employee.user.username} - {self.get_clocking_type_display()} ({self.clocking_datetime})"
    

class trn_daily_attendance(models.Model):
    employee = models.ForeignKey(mst_employee, on_delete=models.CASCADE)
    date = models.DateField()
    attendance_datetime = models.DateTimeField("Attendance Datetime",null=True, blank=True)
    closing_datetime = models.DateTimeField("Closing Datetime", null=True, blank=True)
    worked_hours = models.FloatField("Worked Hours",default=0.0)
    break_minutes = models.IntegerField("Break Minute",default=0)

APPROVAL_STATUS_CHOICES = [
    ('pending', '申請中 (Pending)'),
    ('approved', '承認済み (Approved)'),
    ('rejected', '却下 (Rejected)'),
]