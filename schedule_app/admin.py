from django.contrib import admin
from .models import mst_employee, shift_schedule, trn_clocking, trn_daily_attendance
from common.models import mst_shop

admin.site.register(mst_employee)
admin.site.register(mst_shop)
admin.site.register(shift_schedule)
admin.site.register(trn_clocking)
admin.site.register(trn_daily_attendance)
