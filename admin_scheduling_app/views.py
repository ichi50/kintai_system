from django.shortcuts import render, redirect, get_object_or_404
from django import template
from django.utils import timezone
from datetime import datetime, timedelta,date
from schedule_app.models import shift_schedule
from scheduling_app.models import ShiftRequest,WeeklySchedule
from common.models import mst_employee
from .forms import ShiftEditForm
from django.urls import reverse
from django.db import transaction

register = template.Library()

def get_today():
    # USE_TZ=False の場合、単純な date.today() が最も安全です
    return date.today()

def daily_scheduling(request):
    # 1. 日付の取得（指定がなければ今日）
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            target_date = get_today()
    else:
        target_date = get_today()

    # 2. 曜日の取得 (Django/Pythonでは 0=月曜日, 6=日曜日)
    weekday_index = target_date.weekday()

    employees = mst_employee.objects.all()
    
    # 3. 特定日のシフト希望 (TrnShiftRequest)
    # 休暇申請や、その日だけの時間変更など
    specific_requests = ShiftRequest.objects.filter(
        date=target_date
    ).select_related('employee')

    requested_employee_ids = [req.employee.employee for req in specific_requests]

    # 4. 曜日の基本スケジュール (WeeklySchedule)
    # 毎週月曜日はこの時間、といった固定シフト
    # モデルのフィールド名が 'weekday' (0-6) であると仮定しています
    weekly_base_schedules = WeeklySchedule.objects.filter(
        day_of_week=target_date.weekday(),
        start_time__isnull=False,  # 開始時間が登録されている
        end_time__isnull=False     # 終了時間も登録されている
    ).exclude(employee__employee__in=requested_employee_ids).select_related('employee')

    # その日の全従業員の確定済みシフトを取得
    shifts = shift_schedule.objects.filter(schedule_date=target_date)
    
    shift_data = {}
    for s in shifts:
        emp_id = str(s.employee.employee) # これが '123456' のような文字列になる
        d_str = target_date.strftime('%Y-%m-%d') # これが '2026-01-13' になる
        
        if emp_id not in shift_data:
            shift_data[emp_id] = {}
        shift_data[emp_id][d_str] = s # 二重辞書構造

    # 【デバッグ】コンソールにデータの中身を出力して確認
    print(f"DEBUG: shift_data = {shift_data}")

    context = {
        'target_date': target_date,
        'employees': employees,
        'shift_data': shift_data,  # これを追加
        'specific_requests': specific_requests,
        'weekly_base_schedules': weekly_base_schedules,
        'hours': range(24),
        'prev_date': target_date - timedelta(days=1),
        'next_date': target_date + timedelta(days=1),
    }
    return render(request, 'admin_scheduling_app/daily_scheduling.html', context)

def weekly_scheduling(request):
    # 1. 基準日の取得（指定がなければ今日）
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            target_date = get_today()
    else:
        target_date = get_today()

    # 2. 表示する7日間を計算
    week_days = [target_date + timedelta(days=i) for i in range(7)]
    
    # サイドバー用に「日付ごとの情報」をまとめたリストを作る
    sidebar_data = []
    for day in week_days:
        daily_requests = ShiftRequest.objects.filter(date=day).select_related('employee')
        req_emp_ids = [r.employee.employee for r in daily_requests]
        
        # 修正：その曜日に有効な時間設定があるデータのみ取得
        daily_bases = WeeklySchedule.objects.filter(
            day_of_week=day.weekday(),
            start_time__isnull=False,  # NULLを除外
            end_time__isnull=False
        ).exclude(employee__employee__in=req_emp_ids).select_related('employee')
        
        sidebar_data.append({
            'date': day,
            'requests': daily_requests,
            'bases': daily_bases,
        })

    start_date = week_days[0]
    end_date = week_days[-1]

    employees = mst_employee.objects.all()
    
    # 3. サイドバー用：期間内のシフト希望を取得
    specific_requests = ShiftRequest.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('employee').order_by('date')

    # 4. 期間内の確定済みシフトを取得
    shifts = shift_schedule.objects.filter(
        schedule_date__range=[start_date, end_date]
    ).select_related('employee')

    # 5. 二重辞書データ作成
    shift_data = {}
    for s in shifts:
        emp_key = str(s.employee.employee)
        d_key = s.schedule_date.strftime('%Y-%m-%d')
        if emp_key not in shift_data:
            shift_data[emp_key] = {}
        shift_data[emp_key][d_key] = s

    context = {
        'target_date': target_date,
        'week_days': week_days,
        'employees': employees,
        'shift_data': shift_data,
        'specific_requests': specific_requests,  # サイドバー用
        'prev_date': target_date - timedelta(days=1), # 1日戻る
        'next_date': target_date + timedelta(days=1), # 1日進む
        'prev_week': target_date - timedelta(days=7), # 1日戻る
        'next_week': target_date + timedelta(days=7), # 1日進む
        'today': get_today(),
        'sidebar_data': sidebar_data,
    }
    return render(request, 'admin_scheduling_app/weekly_scheduling.html', context)

def shift_edit_form(request):
    emp_id = request.GET.get('emp_id') or request.POST.get('employee')
    date_str = request.GET.get('date') or request.POST.get('schedule_date')

    if not date_str:
        return redirect('admin_scheduling_app:daily_scheduling')

    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    employee = get_object_or_404(mst_employee, employee=emp_id)
    
    # 既存のシフト（インスタンス）を取得
    instance = shift_schedule.objects.filter(
        employee=employee, 
        schedule_date=target_date
    ).first()

    if request.method == 'POST':
        # --- ここから削除処理を追加 ---
        if "delete" in request.POST and instance:
            instance.delete()
            url = reverse('admin_scheduling_app:daily_scheduling')
            return redirect(f"{url}?date={date_str}")
        # --- 削除処理ここまで ---

        form = ShiftEditForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            url = reverse('admin_scheduling_app:daily_scheduling')
            return redirect(f"{url}?date={date_str}")
        else:
            print(f"DEBUG: Form Errors = {form.errors}")
    else:
        form = ShiftEditForm(instance=instance, initial={
            'employee': employee, 
            'schedule_date': target_date
        })

    # 希望データの取得
    specific_request = ShiftRequest.objects.filter(employee=employee, date=target_date).first()
    weekly_base = WeeklySchedule.objects.filter(employee=employee, day_of_week=target_date.weekday()).first()

    context = {
        'form': form,
        'employee': employee,
        'shift': instance,              # テンプレートの {% if shift %} 判定に使用
        'is_edit': instance is not None,
        'target_date': target_date,
        'specific_request': specific_request,
        'weekly_base': weekly_base,
    }
    
    return render(request, 'admin_scheduling_app/shift_edit_form.html', context)

def auto_assign_weekly_shifts(request):
    if request.method == "POST":
        date_str = request.POST.get('date')
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        week_days = [target_date + timedelta(days=i) for i in range(7)]
        
        employees = mst_employee.objects.all()
        
        # トランザクションを使用して一括処理（途中で失敗したら全部戻す）
        with transaction.atomic():
            for day in week_days:
                for emp in employees:
                    # すでにその日の確定シフトがある場合はスキップ
                    if shift_schedule.objects.filter(employee=emp, schedule_date=day).exists():
                        continue
                    
                    # 1. 特別希望を確認
                    req = ShiftRequest.objects.filter(employee=emp, date=day).first()
                    
                    # 2. 特別希望がない場合、基本スケジュールを確認
                    base = None
                    if not req:
                        base = WeeklySchedule.objects.filter(
                            employee=emp, 
                            day_of_week=day.weekday(),
                            start_time__isnull=False
                        ).first()
                    
                    # 割り当てるデータ（希望 or 基本）があれば作成
                    source = req or base
                    if source and source.start_time and source.end_time:
                        shift_schedule.objects.create(
                            employee=emp,
                            schedule_date=day,
                            start_time=source.start_time,
                            end_time=source.end_time
                        )
        
        return redirect(f"{reverse('admin_scheduling_app:weekly_scheduling')}?date={date_str}")
    
    return redirect('admin_scheduling_app:weekly_scheduling')