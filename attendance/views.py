# attendance/views.py

from django.shortcuts import render, redirect
from django.utils import timezone
from .models import AttendanceRecord
from django.contrib.auth.decorators import login_required # ログイン必須に

# ユーザーがログインしていることを要求する
@login_required
def check_in_out(request):
    if request.method == 'POST':
        # ユーザーの最新の未完了の記録を探す
        latest_record = AttendanceRecord.objects.filter(
            user=request.user, 
            check_out__isnull=True
        ).first()

        if latest_record:
            # 最新の記録があれば、退勤として処理
            latest_record.check_out = timezone.now()
            latest_record.save()
        else:
            # なければ、出勤として新しい記録を作成
            AttendanceRecord.objects.create(user=request.user)
            
        return redirect('attendance_list') # 処理後、一覧画面にリダイレクト

    # GETリクエストの場合はテンプレートを表示
    context = {
        'latest_record': latest_record
    }
    return render(request, 'attendance/home.html', context)