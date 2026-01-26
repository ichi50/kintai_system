from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from schedule_app.models import trn_daily_attendance, mst_employee ,trn_clocking
from .forms import AttendanceCorrectionForm
from django.shortcuts import redirect
from .forms import ClockingFormSet
from datetime import datetime, date, timedelta,time

def daily_correction_list(request):
    date_str = request.GET.get('date', date.today().isoformat())    

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        target_date = date.today()
    
    # 日付移動用
    prev_date = target_date - timedelta(days=1)
    next_date = target_date + timedelta(days=1)
    
    # データの取得
    attendances = trn_daily_attendance.objects.filter(date=target_date).select_related('employee')  

    return render(request, 'admin_correction_app/daily_list.html', {
        'attendances': attendances,
        'target_date': target_date,
        'prev_date': prev_date,
        'next_date': next_date,
    })

def update_daily_attendance(attendance):
    target_date = attendance.date
    # 修正画面と同じ範囲を取得
    start_range = datetime.combine(target_date, time.min)
    end_range = start_range + timedelta(days=1, hours=9)

    clockings = trn_clocking.objects.filter(
        employee=attendance.employee,
        clocking_datetime__range=(start_range, end_range)
    ).order_by('clocking_datetime')

    work_start = None
    work_end = None
    total_break_sec = 0
    temp_break_start = None

    for c in clockings:
        c_type = str(c.clocking_type) # 確実に文字列として比較
        
        if c_type == '1': # 出勤
            # 最初の出勤時刻を保持（複数あっても最初を優先）
            if work_start is None:
                work_start = c.clocking_datetime
        elif c_type == '2': # 退勤
            # 最後の退勤時刻を保持（上書きしていくことで一番最後が残る）
            work_end = c.clocking_datetime
        elif c_type == '3': # 休憩開始
            temp_break_start = c.clocking_datetime
        elif c_type == '4': # 休憩終了
            if temp_break_start:
                total_break_sec += (c.clocking_datetime - temp_break_start).total_seconds()
                temp_break_start = None

    # 実績モデルへの反映
    attendance.attendance_datetime = work_start  # ここが開始時刻欄
    attendance.closing_datetime = work_end   # ここが終了時刻欄
    attendance.break_minutes = total_break_sec / 60
    
    if work_start and work_end:
        total_work_sec = (work_end - work_start).total_seconds()
        # 実労働時間 = (総時間 - 休憩)
        net_work_sec = total_work_sec - total_break_sec
        attendance.worked_hours = max(0, net_work_sec / 3600)
    else:
        attendance.worked_hours = 0
    
    attendance.save()

def edit_attendance(request, attendance_id):

    attendance = get_object_or_404(trn_daily_attendance, id=attendance_id)
    target_date = attendance.date
    # 翌朝9時までを範囲とする
    start_range = datetime.combine(target_date, time.min)
    end_range = start_range + timedelta(days=1, hours=9)

    queryset = trn_clocking.objects.filter(
        employee=attendance.employee,
        clocking_datetime__range=(start_range, end_range)
    ).order_by('clocking_datetime')

    if request.method == 'POST':
        formset = ClockingFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            # --- 修正ポイント：保存処理を明示的に制御 ---
            
            # 1. 削除チェックされたデータを削除
            for form in formset.deleted_forms:
                if form.instance.pk:
                    form.instance.delete()

            # 2. 変更・新規データを保存
            instances = formset.save(commit=False)
            for instance in instances:
                # 外部キーがないため、ここで確実に従業員を紐付ける
                instance.employee = attendance.employee
                instance.save()

            # 3. 再計算（すべての保存が終わった後に行う）
            update_daily_attendance(attendance)
            
            return redirect(f"{reverse('admin_correction_app:daily_attendance_list')}?date={target_date.isoformat()}")
    else:
        formset = ClockingFormSet(queryset=queryset)

    return render(request, 'admin_correction_app/edit_form.html', {
        'formset': formset,
        'attendance': attendance,
    })