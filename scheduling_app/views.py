# kintai_app/views.py
from .models import mst_employee
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, timedelta, datetime, time
import calendar
from django.utils.safestring import mark_safe
from .models import ShiftRequest, WeeklySchedule 
import json

def get_today():
    # USE_TZ=False の場合、単純な date.today() が最も安全です
    return date.today()

# ★★★ ヘルパー関数: 時間解析 ★★★
def parse_time(time_str):
    if not time_str:
        return None
    try:
        dt = datetime.strptime(time_str, '%H:%M')
        return dt.time()
    except ValueError:
        return None

# ★★★ 1. シフト申請カレンダー表示ビュー ★★★
# 希望シフト申請
@login_required
def request_shift(request):
    today_date = date.today()

    # カレンダーの年月の取得とナビゲーション計算 
    year_param = request.GET.get('year')
    month_param = request.GET.get('month')
    
    year = int(year_param) if year_param else today_date.year
    month = int(month_param) if month_param else today_date.month
    
    # 前月・次月ナビゲーションの計算
    try:
        current_date = date(year, month, 1) 
    except ValueError:
        year = today_date.year
        month = today_date.month
        current_date = date(year, month, 1)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # 当月分のシフトデータをデータベースから取得 (user=request.userでフィルタリング)
    user_shifts = ShiftRequest.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    )

    # 週次基本スケジュール取得
    weekly_schedules_queryset = WeeklySchedule.objects.filter(user=request.user)

    initial_weekly_data = {}
    for schedule in weekly_schedules_queryset:
        initial_weekly_data[schedule.day_of_week] = {
            'is_day_off': schedule.is_day_off,
            'start_time': schedule.start_time.strftime('%H:%M') if schedule.start_time else '',
            'end_time': schedule.end_time.strftime('%H:%M') if schedule.end_time else '',
        }

    # テンプレートで安全にパースできるように JSON 文字列に変換
    initial_weekly_data_json = json.dumps(initial_weekly_data)
    
    # 曜日データ (0=月曜、...、6=日曜)
    WEEK_DAYS_JP = ["月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜"]
    weekly_days = [(i, WEEK_DAYS_JP[i]) for i in range(7)]

    context = {
        'year': year,
        'month': month,
        'current_month_str': current_date.strftime('%Y年%m月'),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'weekly_days': weekly_days,
        'initial_weekly_data': initial_weekly_data_json,
    }
    
    # request_shift.html テンプレートをレンダリング
    return render(request, 'kintai_app/request_shift.html', context)

# --- モーダルフォーム処理 ---

#個別申請送信ビュー
@login_required
def submit_individual_shift(request: HttpRequest):
    if request.method == 'POST':
        schedule_date_str = request.POST.get('schedule_date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        is_day_off = 'is_day_off' in request.POST
        
        try:
            employee_obj = mst_employee.objects.get(user=request.user)
            schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
            start_time = parse_time(start_time_str)
            end_time = parse_time(end_time_str)
            
            # 既存の申請を検索または新規作成
            shift,created = ShiftRequest.objects.get_or_create(
                user=request.user,
                date=schedule_date,
                defaults={
                    'employee': employee_obj,
                    'status': 'pending' 
                }
            )

            # データを更新
            shift.employee = employee_obj
            shift.start_time = start_time
            shift.end_time = end_time
            shift.is_day_off = is_day_off
            shift.status = 'pending' # 更新時も承認待ちに戻す
            shift.save()
            
            messages.success(request, f"{schedule_date_str} のシフト申請を送信しました。")

        except Exception as e:
            messages.error(request, f"シフト申請の処理中にエラーが発生しました: {e}")
            
    return redirect('scheduling:request_shift')


# ★★★ 3. 個別申請取り消しビュー ★★★
@login_required
def cancel_individual_shift(request: HttpRequest):
    if request.method == 'POST':
        schedule_date_str = request.POST.get('schedule_date')

        try:
            schedule_date = datetime.strptime(schedule_date_str, '%Y-%m-%d').date()
            
            # 該当する申請データを取得
            shift = get_object_or_404(
                ShiftRequest, 
                user=request.user, 
                date=schedule_date
            )
            
            # 申請を取り消す（レコードを削除）
            shift.delete()
            
            messages.success(request, f"{schedule_date_str} のシフト申請を取り消しました。")

        except Exception as e:
            messages.error(request, f"シフト申請の取り消し中にエラーが発生しました: {e}")
            
    return redirect('kintai:request_shift')


# ★★★ 4. 週次基本スケジュール設定ビュー ★★★
@login_required
def submit_weekly_shift(request: HttpRequest):
    if request.method == 'POST':
        user = request.user

        try:
            employee_obj = mst_employee.objects.get(user=user)
        except mst_employee.DoesNotExist:
            messages.error(request, "従業員情報（mst_employee）が未登録のため、基本スケジュールを保存できません。")
            return redirect('kintai:request_shift')
        
        for day_index in range(7): # 0:月曜 から 6:日曜
            is_day_off = f'is_day_off_{day_index}' in request.POST
            start_time_str = request.POST.get(f'start_time_{day_index}', '')
            end_time_str = request.POST.get(f'end_time_{day_index}', '')
            
            start_time = parse_time(start_time_str)
            end_time = parse_time(end_time_str)

            try:
                # 既存の基本スケジュールを検索し、存在しなければ新規作成
                schedule, created = WeeklySchedule.objects.get_or_create(
                    user=user,
                    day_of_week=day_index,
                    defaults={
                        'employee': employee_obj,
                        'start_time': start_time,
                        'end_time': end_time,
                        'is_day_off': is_day_off
                    }
                )

                # 既存レコードが見つかった場合は更新
                if not created:
                    schedule.employee = employee_obj
                    schedule.start_time = start_time
                    schedule.end_time = end_time
                    schedule.is_day_off = is_day_off
                    schedule.save()
                    
            except Exception as e:
                messages.error(request, f'基本スケジュールの保存中にエラーが発生しました: {e}')
                return redirect('scheduling:request_shift')


        messages.success(request, '一週間の基本スケジュールが正常に保存されました。')
        return redirect('scheduling:request_shift')
    
    return redirect('scheduling:request_shift')