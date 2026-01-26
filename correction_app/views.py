# correction_app/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta, date
import calendar
from schedule_app.models import trn_daily_attendance
from achieve_app.views import format_hours_to_string # 時間表示ヘルパー関数を再利用
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.conf import settings
import json

from .models import TrnCorrectionRequest, TrnCorrectionTime, CORRECTION_PUNCH_CHOICES

from .models import mst_employee
def get_today():
    # USE_TZ=False の場合、単純な date.today() が最も安全です
    return date.today()

@require_POST
@login_required
def submit_correction_request(request):
    try:
        # JSONボディをロード
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
    
    # ログインユーザーから従業員マスタを取得
    try:
        employee = mst_employee.objects.get(user=request.user)
    except mst_employee.DoesNotExist:
        return JsonResponse({'error': '従業員マスタが見つかりません。'}, status=403)
        
    # 必須データの確認
    attendance_date_str = data.get('attendance_date')
    reason = data.get('reason')
    correction_times = data.get('correction_times')

    if not all([attendance_date_str, reason, correction_times]):
        return JsonResponse({'error': '必須フィールドが不足しています。'}, status=400)

    if not isinstance(correction_times, list) or len(correction_times) == 0:
        return JsonResponse({'error': '修正打刻項目が不正または不足しています。'}, status=400)

    try:
        # 日付文字列をdateオブジェクトに変換
        attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': '日付の形式が正しくありません。'}, status=400)
        
    # トランザクション処理を開始（データベース操作の原子性を保証）
    try:
        with transaction.atomic():
             # 1. TrnCorrectionRequest（ヘッダー）の取得または作成
            
            # 既存の申請が存在するかを検索
            correction_request, created = TrnCorrectionRequest.objects.get_or_create(
                employee=employee,
                attendance_date=attendance_date,
                defaults={
                    'reason': reason,
                    'status': 'pending'
                }
            )
            
            if created:
                # 新規作成の場合
                print(f"DEBUG: 新しい修正申請ヘッダーを日付 {attendance_date} に作成しました。")
            else:
                # 既存の申請が見つかった場合
                print(f"DEBUG: 既存の修正申請ヘッダーを日付 {attendance_date} に更新します。")
                
                # 理由とステータスを更新
                correction_request.reason = reason
                correction_request.status = 'pending'
                correction_request.save()

                # 🚨 既存の打刻修正履歴 (詳細) をすべて削除してから再登録する
                # これにより、常に最新の打刻項目に置き換えられます。
                TrnCorrectionTime.objects.filter(request=correction_request).delete()

            # 2. TrnCorrectionTime（詳細項目）の作成
            # バリデーションと同時に一括作成の準備
            time_objects = []
            valid_punch_types = [choice[0] for choice in CORRECTION_PUNCH_CHOICES]
            
            for item in correction_times:
                punch_time_str = item.get('punch_time')
                punch_type = item.get('punch_type')
                sequence = item.get('sequence', 0) # sequenceがない場合は0
                
                if not all([punch_time_str, punch_type]):
                    raise ValueError("打刻時間または打刻内容が欠落しています。")

                if punch_type not in valid_punch_types:
                    raise ValueError(f"無効な打刻内容です: {punch_type}")
                
                print(f"DEBUG: Processing punch_time_str: '{punch_time_str}'")

                # punch_time_str は 'YYYY-MM-DDT HH:MM:SS' 形式を想定
                # JavaScriptから 'YYYY-MM-DDT HH:MM:00' の形式で来るはず
                try:
                    # fromisoformatの代わりに、より寛容な strptime を使用して形式を明示
                    punch_datetime = datetime.strptime(punch_time_str, '%Y-%m-%dT%H:%M:%S')
                    # タイムゾーンを強制的に設定する必要があるかもしれません (settings.pyのUSE_TZがTrueの場合)
                    punch_datetime = datetime.strptime(punch_time_str, '%Y-%m-%dT%H:%M:%S') 
                    if settings.USE_TZ:
                        punch_datetime = timezone.make_aware(punch_datetime, timezone.get_current_timezone())
                except ValueError as ve:
                    # 🚨 ValueError発生を検知
                    print(f"DEBUG ERROR: Datetime conversion failed for '{punch_time_str}'. Error: {ve}")
                    raise ValueError(f"時刻の形式が正しくありません: {punch_time_str}") from ve

                time_objects.append(
                    TrnCorrectionTime(
                        request=correction_request,
                        punch_time=punch_datetime,
                        punch_type=punch_type,
                        sequence=sequence
                    )
                )

            # データベースに一括で挿入
            TrnCorrectionTime.objects.bulk_create(time_objects)
            
        # 成功レスポンス
        return JsonResponse({'success': True, 'message': '勤怠修正申請を受け付けました。', 'request_id': correction_request.pk}, status=200)

    except ValueError as e:
        # データバリデーションエラー
        print(f"DEBUG: Data Validation Error: {e}")
        return JsonResponse({'error': f'データ入力エラー: {e}'}, status=400)
    except Exception as e:
        # その他のデータベースエラーなど
        print(f"Database Error: {e}")
        print(f"CRITICAL DATABASE ERROR: {e}")
        return JsonResponse({'error': '申請処理中に予期せぬエラーが発生しました。'}, status=500)

@login_required
def correction_calendar(request, year=None, month=None):
    try:
        employee = mst_employee.objects.get(user=request.user)
    except mst_employee.DoesNotExist:
        # 連携されていない場合はエラーメッセージを表示
        return render(request, 'attendance/index.html', {'error_message': 'アカウントに紐づく従業員情報が見つかりません。'})
    
    # 1. カレンダー表示対象の年/月の決定
    today = get_today()
    if year is None or month is None:
        target_date = today
    else:
        try:
            target_date = date(int(year), int(month), 1)
        except ValueError:
            target_date = today

    # 2. 表示期間の計算
    first_day = target_date.replace(day=1)

    # 週の始まりを日曜(0)とする
    start_weekday = (first_day.weekday() + 1) % 7 # 月曜(0)を日曜(0)に調整
    calendar_start_date = first_day - timedelta(days=start_weekday)
    
    # 翌月の1日を取得
    if target_date.month == 12:
        next_month_day = date(target_date.year + 1, 1, 1)
    else:
        next_month_day = date(target_date.year, target_date.month + 1, 1)

    # 3. 実績データの取得（カレンダー表示に必要なデータ）
    # 1ヶ月分の実績データを一括取得
    attendance_data = trn_daily_attendance.objects.filter(
        employee=employee,
        attendance_datetime__year=target_date.year,
        attendance_datetime__month=target_date.month
    ).select_related('employee') # 従業員情報も同時に取得
    
    # 日付をキーにしたディクショナリに変換
    daily_data = {
    item.attendance_datetime: {
        'start_time': item.attendance_datetime.strftime('%H:%M') if item.attendance_datetime else '―',
        'end_time': item.closing_datetime.strftime('%H:%M') if item.closing_datetime else '―',
        
        'is_punched': item.attendance_datetime is not None or item.closing_datetime is not None, 
        
        'worked_hours': format_hours_to_string(item.worked_hours) if item.worked_hours else '―',
    }
    for item in attendance_data
}

    # 4. カレンダーデータの準備
    cal = calendar.Calendar(firstweekday=6) # 6=日曜始まり
    
    calendar_data = []
    for week in cal.monthdatescalendar(target_date.year, target_date.month):
        week_data = []
        for day in week:
            is_current_month = day.month == target_date.month
            
            # 実績データの有無と詳細
            data_key = day
            attendance_detail = daily_data.get(data_key)
            
            # 既に修正申請が出されているかどうかのフラグも取得すると良いが、一旦スキップ

            week_data.append({
                'date': day,
                'is_current_month': is_current_month,
                'is_today': day == today,
                'attendance': attendance_detail, # 実績データ
                'date_str': day.strftime('%Y-%m-%d')
            })
        calendar_data.append(week_data)

    # 5. コンテキストの準備
    context = {
        'current_year': target_date.year,
        'current_month': target_date.month,
        'current_month_name': target_date.strftime('%Y年%m月'),
        'calendar_data': calendar_data,
        'employee_name': employee.user.username,
        
        # 前月/翌月へのナビゲーション用
        'prev_month': (target_date - timedelta(days=28)).strftime('%Y/%m'),
        'next_month': next_month_day.strftime('%Y/%m'),
    }

    return render(request, 'correction_app/correction_calendar.html', context)