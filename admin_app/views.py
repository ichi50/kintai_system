import calendar
from django import template
from datetime import date, datetime, timedelta
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
# from django.utils.timezone import localtime  # USE_TZ=Falseでは不要なためコメントアウトまたは削除

from schedule_app.models import shift_schedule, trn_daily_attendance, mst_employee

register = template.Library()

@staff_member_required
def daily_shift_display(request):
    # 1. URLから日付を取得
    date_str = request.GET.get('date')
    
    # 既存の重複したtry-exceptを整理しました
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            target_date = date.today() # USE_TZ=False時はこれでOK
    else:
        target_date = date.today()

    # 2. 前の日・次の日を計算
    prev_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)

    # 3. データの取得
    shifts = shift_schedule.objects.filter(schedule_date=target_date)
    shift_dict = {str(s.employee.employee): s for s in shifts}

    actuals = trn_daily_attendance.objects.filter(date=target_date)
    actual_dict = {str(a.employee.employee): a for a in actuals}

    employees = mst_employee.objects.all().select_related('user') 

    context = {
        'target_date': target_date,
        'prev_date': prev_date,
        'next_date': next_date,
        'shift_dict': shift_dict,
        'actual_dict': actual_dict,
        'employees': employees,
        'hours': range(24),
    }
    return render(request, 'admin_app/shift_display.html', context)

def shift_display(request):
    """全従業員のシフトを一覧表示する"""
    # timezone.localdate() を date.today() に変更
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    _, num_days = calendar.monthrange(year, month)
    days = range(1, num_days + 1)

    employees = mst_employee.objects.all().select_related('user')
    
    # マトリックス用に整理
    shift_dict = {}
    shifts = shift_schedule.objects.filter(schedule_date__year=year, schedule_date__month=month)

    for s in shifts:
        emp_id = str(s.employee.employee) 
        day = str(s.schedule_date.day)
        key = f"{emp_id},{day}"
        shift_dict[key] = s

    context = {
        'year': year,
        'month': month,
        'days': days,
        'employees': employees,
        'shift_dict': shift_dict,
        'current_month_str': f"{year}年{month}月",
    }
    return render(request, 'admin_app/shift_display.html', context)

@staff_member_required
def get_pending_requests(request):
    return JsonResponse({'requests': []})

def weekly_shift_display(request):
    # 表示基準日の決定
    date_str = request.GET.get('date')
    if date_str:
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            base_date = date.today()
    else:
        base_date = date.today()

    target_date = base_date
    start_date = base_date
    week_days = [start_date + timedelta(days=i) for i in range(7)]
    
    employees = mst_employee.objects.all()
    
    shifts = shift_schedule.objects.filter(
        schedule_date__range=[week_days[0], week_days[-1]]
    )
    
    shift_data = {}
    for s in shifts:
        emp_id = str(s.employee.employee)
        d_str = s.schedule_date.strftime('%Y-%m-%d')
        if emp_id not in shift_data:
            shift_data[emp_id] = {}
        shift_data[emp_id][d_str] = s

    context = {
        'target_date': target_date,
        'week_days': week_days,
        'employees': employees,
        'shift_data': shift_data,
        'base_date': base_date,
        'prev_date': base_date - timedelta(days=1),
        'next_date': base_date + timedelta(days=1),
        'prev_week': base_date - timedelta(days=7),
        'next_week': base_date + timedelta(days=7),
        'hours': range(24),
    }
    return render(request, 'admin_app/weekly_shift.html', context)