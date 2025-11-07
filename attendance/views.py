# attendance/views.py

from datetime import date, datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
# ★★★ models.py にあるすべてのモデルをインポート ★★★
from .models import mst_employee, trn_daily_attendance, AttendanceRecord, shift_schedule
# ↑ shift_scheduleはカレンダータグで必要ですが、ビューでもインポートしておくと便利です

# attendance/views.py の index 関数 (修正版)
@login_required
def index(request):
    # 従業員情報 (mst_employee) の取得
    try:
        employee = mst_employee.objects.get(user=request.user)
    except mst_employee.DoesNotExist:
        # 連携されていない場合はエラーメッセージを表示
        return render(request, 'attendance/index.html', {'error_message': 'アカウントに紐づく従業員情報が見つかりません。'})

    # 勤怠記録 (AttendanceRecord) の取得
    today_date = timezone.localdate() 
    latest_record = AttendanceRecord.objects.filter(
        user=request.user, 
        check_in__date=today_date
    ).order_by('-check_in').first()

    # --- GETリクエスト (画面表示) ---
    if request.method == 'GET':
        
        # 1. カレンダーの年月の取得 (前回の修正ロジック)
        year_param = request.GET.get('year')
        month_param = request.GET.get('month')
        
        year = int(year_param) if year_param else today_date.year
        month = int(month_param) if month_param else today_date.month
        
        # 2. 前月・次月ナビゲーション用の計算
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
        }
        
        return render(request, 'attendance/index.html', context)
        
    # --- POSTリクエスト (打刻処理) ---
    elif request.method == 'POST':
        current_time = timezone.localtime(timezone.now())

        if 'check_in' in request.POST:
            # 1. 出勤ボタンが押された場合
            if latest_record and latest_record.check_out is None:
                pass
            else:
                AttendanceRecord.objects.create(
                    user=request.user,
                    check_in=current_time
                )
                
        elif 'check_out' in request.POST:
            # 2. 退勤ボタンが押された場合
            if latest_record and latest_record.check_out is None:
                latest_record.check_out = current_time
                latest_record.save()
                
        # ★★★ 修正箇所: リダイレクト先を名前空間付きURLに変更 ★★★
        return redirect('kintai:index')
    
# --- 実績リストビュー (変更なし) ---
@login_required
def record_list(request):
    """従業員の実績を確認する画面（仮）"""
    context = {
        'title': '実績の確認',
        'message': 'ここに過去の勤怠実績の一覧を表示します。'
    }
    # 後で record_list.html を作成する必要があります
    return render(request, 'attendance/record_list.html', context)