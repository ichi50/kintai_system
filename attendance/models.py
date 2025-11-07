from django.db import models

# attendance/models.py

from django.db import models
from django.contrib.auth.models import User # ユーザー認証を使う場合

class mst_shop(models.Model):
    shop_id = models.CharField('Shop_ID',max_length=6,primary_key=True)
    shop_name = models.CharField('Shop_Name',max_length=10)
    shop_addres = models.CharField('Shop_Address',max_length=20)
    shop_tel = models.CharField('Shop_Tel',max_length=11)

class mst_employee(models.Model):
    emp_id = models.CharField('Emp_ID',max_length=6,primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, unique=True)    
    emp_name = models.CharField('Emp_Name',max_length=30)
    emp_age = models.IntegerField('Emp_Age')
    emp_email = models.CharField('Emp_Email',max_length=50)
    affiliated_store = models.ForeignKey(mst_shop,on_delete=models.PROTECT)
    emp_status = models.CharField("Emp_Status",max_length=1)
    hire_date = models.DateField("Hire_Date")
    def __str__(self):
        return self.emp_name

class mst_password(models.Model):
    emp_id = models.ForeignKey(mst_employee,on_delete=models.CASCADE)
    emp_pass = models.CharField("Emp_Pass",max_length=50)
    file_count = models.IntegerField("Fail_Count")

class shift_schedule(models.Model):
    emp_id = models.ForeignKey(mst_employee,on_delete=models.CASCADE)
    schedule_date = models.DateField("Schedule_Date",primary_key=True)
    start_time = models.TimeField("Start_Time")
    end_time = models.TimeField("End_Time")
    def show_schedule_data(self):
        return self.start_time,self.end_time
    
    class Meta:
        # 同じユーザーの同じ日のシフトは一つだけ
        unique_together = ('emp_id', 'schedule_date') 
        ordering = ['schedule_date']

class trn_clocking(models.Model):
    clocking_id = models.BigIntegerField("Clocking_ID",primary_key=True)
    emp_id = models.ForeignKey(mst_employee,on_delete=models.CASCADE)
    clocking_type = models.CharField("Clocking_Type",max_length=1)
    clocking_datetime = models.DateTimeField("Clocking_DateTime")


class trn_daily_attendance(models.Model):
    attendance_date = models.DateField("Attendance_Date")
    emp_id = models.ForeignKey(mst_employee,on_delete=models.CASCADE)
    scheduled_start = models.TimeField("Scheduled_Start")
    scheduled_end = models.TimeField("Scheduled_End")
    attendance_datetime = models.DateTimeField("Attendance_Datetime")
    closing_datetime = models.DateTimeField("Closing_Datetime")
    worked_hours = models.FloatField(" Worked_Hours")

    #def aggregation(self):
        #return self.worked_hours

class AttendanceRecord(models.Model):
    # 誰の記録か (Django標準のUserモデルと連携)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 勤務開始時刻
    check_in = models.DateTimeField(auto_now_add=True)
    
    # 勤務終了時刻
    check_out = models.DateTimeField(null=True, blank=True)
    
    # 備考
    note = models.TextField(blank=True)
    
    def calculate_work_duration(self):
            """出勤から退勤までの労働時間を計算し、文字列で返す"""
            if self.check_out:
                duration = self.check_out - self.check_in
                total_seconds = int(duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                # 休憩時間を考慮した複雑な計算は後で実装できますが、
                # まずはシンプルな経過時間を返します
                return f"{hours}時間{minutes}分"
            return None

    def __str__(self):
        return f'{self.user.username} - {self.check_in.strftime("%Y-%m-%d")}'
