# achieve_app/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import F, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import timedelta,date
import calendar
from django.db import models
from schedule_app.models import trn_daily_attendance
from common.models import mst_employee

def get_today():
    # USE_TZ=False の場合、単純な date.today() が最も安全です
    return date.today()

def format_hours_to_string(total_hours):
    """Worked_Hours (Float) を受け取り、指定された形式で返す。"""
    if total_hours is None or total_hours < 0:
        return "0h"
        
    return f"{total_hours:.1f}h" 

@login_required
def monthly_work_summary(request):
    # ログインユーザーに関連づけられた従業員マスタを取得
    try:
        employee = mst_employee.objects.get(user=request.user)
    except mst_employee.DoesNotExist:
        return render(request, 'achieve_app/error.html', {'message': '従業員マスタが見つかりません。'})

    now = date.today()

    # ----------------------------------------------------
    # 1. 当月の期間を計算
    # ----------------------------------------------------
    current_month_start = now.replace(day=1)
    # 当月の最終日を取得（翌月1日の00:00:00が終了日）
    # 翌月の1日を計算し、フィルターのend_timeとして利用
    if now.month == 12:
        next_month_start = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month_start = now.replace(month=now.month + 1, day=1)

    # ----------------------------------------------------
    # 2. 前月の期間を計算
    # ----------------------------------------------------
    if now.month == 1:
        prev_month = now.replace(year=now.year - 1, month=12, day=1)
    else:
        prev_month = now.replace(month=now.month - 1, day=1)
        
    prev_month_start = prev_month.replace(day=1)
    prev_month_end = current_month_start # 前月は当月開始日まで

    # ----------------------------------------------------
    # 3. 労働時間の集計
    # ----------------------------------------------------
    
    # 当月のレコードを取得
    current_aggregates = trn_daily_attendance.objects.filter(
        employee=employee,
        attendance_datetime__gte=current_month_start,
        attendance_datetime__lt=next_month_start,
    ).aggregate(
        # 総労働時間 (worked_hours) の合計
        gross_hours=models.Sum('worked_hours'), 
        # 休憩時間 (break_minutes) の合計 (分)
        total_break_minutes=models.Sum('break_minutes')
    )

    # データを取得し、Noneの場合は 0.0 または 0 を設定
    gross_current = current_aggregates.get('gross_hours') or 0.0
    breaks_current = current_aggregates.get('total_break_minutes') or 0

        #  実労働時間の計算: 総時間 - (休憩分の合計 / 60.0)
    current_month_total_hours = gross_current - (breaks_current / 60.0)

    # 前月の worked_hours を合計
    previous_aggregates = trn_daily_attendance.objects.filter(
        employee=employee,
        attendance_datetime__gte=prev_month_start,
        attendance_datetime__lt=prev_month_end,
        # status='approved', # 必要に応じてフィルタリング
    ).aggregate(
        gross_hours=models.Sum('worked_hours'),
        total_break_minutes=models.Sum('break_minutes')
    )

    # データを取得し、Noneの場合は 0.0 または 0 を設定
    gross_prev = previous_aggregates.get('gross_hours') or 0.0
    breaks_prev = previous_aggregates.get('total_break_minutes') or 0

    # 🚨 実労働時間の計算: 総時間 - (休憩分の合計 / 60.0)
    previous_month_total_hours = gross_prev - (breaks_prev / 60.0)

    # ----------------------------------------------------
    # 4. テンプレートに渡すデータを作成
    # ----------------------------------------------------
    context = {
        'current_month_name': current_month_start.strftime('%Y年%m月'),
        'previous_month_name': prev_month_start.strftime('%Y年%m月'),
        # 🚨 修正: 独自のフォーマット関数を使用
        'current_month_work': format_hours_to_string(current_month_total_hours),
        'previous_month_work': format_hours_to_string(previous_month_total_hours),
    }

    return render(request, 'achieve_app/achieve.html', context)