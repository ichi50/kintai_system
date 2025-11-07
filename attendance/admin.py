from django.contrib import admin
from .models import mst_employee, mst_shop, shift_schedule, AttendanceRecord, trn_clocking, trn_daily_attendance, mst_password

admin.site.register(mst_employee)
admin.site.register(mst_shop)
admin.site.register(shift_schedule)
admin.site.register(AttendanceRecord)
admin.site.register(trn_clocking)
admin.site.register(trn_daily_attendance)
admin.site.register(mst_password)
# Register your models here.
