# schedule_app/views.py

from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import mst_employee,shift_schedule
from django.contrib import messages
from datetime import date
from calendar import day_name, MONDAY
from django.http import HttpRequest

def get_today():
    # USE_TZ=False の場合、単純な date.today() が最も安全です
    return date.today()    

@login_required
def index(request):
    today_date = date.today() 
    # 従業員情報 (mst_employee) の取得
    try:
        employee = mst_employee.objects.get(user=request.user)
    except mst_employee.DoesNotExist:
        # 連携されていない場合はエラーメッセージを表示
        return render(request, 'attendance/index.html', {'error_message': 'アカウントに紐づく従業員情報が見つかりません。'})

    # 勤怠記録 (AttendanceRecord) の取得
    latest_record = None

    # --- 当日のシフト情報を取得し、労働時間を計算するロジック ---
    today_shift = None
    today_work_minutes = 0

    try:
        # 当日のシフトをデータベースから取得
        today_shift = shift_schedule.objects.get(
            employee=employee,
            schedule_date=today_date
        )

        # 労働時間（分）の計算
        start_time = today_shift.start_time
        end_time = today_shift.end_time
        
        # date(1, 1, 1) は日付の部分を無視するために使用
        start_dt = datetime.combine(date(1, 1, 1), start_time)
        end_dt = datetime.combine(date(1, 1, 1), end_time)
        
        # 終業時間が始業時間より前の日をまたぐシフトの場合の処理
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
            
        duration = end_dt - start_dt
        today_work_minutes = int(duration.total_seconds() / 60)
    
    except shift_schedule.DoesNotExist:
        # 当日のシフトが登録されていない場合
        pass
    
    # --- GETリクエスト (画面表示) ---
    if request.method == 'GET':
        
        # 1. カレンダーの年月の取得 
        year_param = request.GET.get('year')
        month_param = request.GET.get('month')
        
        year = int(year_param) if year_param else today_date.year
        month = int(month_param) if month_param else today_date.month
        
        # パラメータが不正な場合のデフォルト処理
        try:
            year = int(year_param) if year_param else today_date.year
            month = int(month_param) if month_param else today_date.month
            current_date = date(year, month, 1)
        except (ValueError, TypeError):
            # 不正な値が渡された場合、今日の日付に戻す
            year = today_date.year
            month = today_date.month
            current_date = date(year, month, 1)

        # 前月
        first_day_current = date(year, month, 1)
        # 1ヶ月前の計算：当月1日から1日を引いた前月の最終日を取得し、その月/年を使用
        last_day_prev = first_day_current - timedelta(days=1)
        prev_year = last_day_prev.year
        prev_month = last_day_prev.month
        
        # 次月
        # 2ヶ月後の1日を取得し、そこから1日引いて次月の最終日を取得後、その月/年を使用
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year

        # 3. テンプレートに渡すコンテキスト
        context = {
            'latest_record': latest_record,
            'year': year,
            'month': month,
            'current_month_str': current_date.strftime('%Y年%m月'),
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,

            'today_shift': today_shift,
            'today_work_minutes': today_work_minutes,
        }
        
        return render(request, 'attendance/index.html', context)

# --- 実績リストビュー ---
