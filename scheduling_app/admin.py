# kintai_app/admin.py

from django.contrib import admin
from django.core.exceptions import ValidationError
from scheduling_app.models import WeeklySchedule, ShiftRequest
# attendance.models から mst_employee をインポートします
try:
    from .models import mst_employee
except ImportError:
    # 実際には ImportError は発生しないはずですが、念のためエラーハンドリング
    mst_employee = None 

# ----------------------------------------------------------------------
# WeeklySchedule の管理クラス
# ----------------------------------------------------------------------

class WeeklyScheduleAdmin(admin.ModelAdmin):
    # 管理画面での表示項目を設定
    list_display = ('user', 'day_of_week', 'start_time', 'end_time', 'is_day_off')
    list_filter = ('user', 'day_of_week')
    
    readonly_fields = ('user', 'employee',)

    fieldsets = (
        (None, {
            'fields': ('user', 'employee', 'day_of_week', 'start_time', 'end_time', 'is_day_off'),
        }),
    )
    
    # ユーザーと従業員IDを保存前に自動設定する
    def save_model(self, request, obj, form, change):
        # 1. user フィールドの設定
        if not obj.user_id:
            obj.user = request.user
        
        if not obj.employee_id and mst_employee:
            try:
                employee_obj = mst_employee.objects.get(user=request.user)
                obj.employee = employee_obj
            except mst_employee.DoesNotExist:
                from django.core.exceptions import ValidationError
                raise ValidationError("従業員情報が未登録です。")

        super().save_model(request, obj, form, change)

class ShiftRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'start_time', 'end_time', 'is_day_off', 'status')
    list_filter = ('user', 'status', 'date')
    ordering = ('date',)
    
    # こちらも user と employee は自動設定が望ましい
    readonly_fields = ('user', 'employee',) 
    
    # ShiftRequest にも save_model のemployee設定ロジックが必要です
    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        
        if not obj.employee_id and mst_employee:
            try:
                employee_obj = mst_employee.objects.get(user=request.user)
                obj.employee = employee_obj
            except mst_employee.DoesNotExist:
                from django.core.exceptions import ValidationError
                raise ValidationError("従業員情報が未登録です。")
                
        super().save_model(request, obj, form, change)
        
# モデルを管理サイトに登録
admin.site.register(WeeklySchedule, WeeklyScheduleAdmin)
admin.site.register(ShiftRequest, ShiftRequestAdmin) # ShiftRequest も登録している場合はそのまま