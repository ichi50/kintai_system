# attendance/templatetags/calendar_tags.py

import calendar
import datetime
from datetime import date
from django import template
from django.utils.safestring import mark_safe
from common.models import mst_employee
from schedule_app.models import shift_schedule

import json

register = template.Library()
@register.simple_tag
def test_output():
    return mark_safe("<h1>TEST SUCCESS</h1>")

# HTMLカレンダーを生成するためのカスタムクラス
class ShiftCalendar(calendar.HTMLCalendar):
    def __init__(self, shifts=None, *args, **kwargs):
        # 0=月曜日, 6=日曜日
        super().__init__(firstweekday=6, *args, **kwargs) 
        self.shifts = {shift.schedule_date: shift for shift in shifts}

    def formatweekheader(self):
        # firstweekday=6 (日曜始まり) に合わせた曜日のリスト
        DAYS = ['日', '月', '火', '水', '木', '金', '土'] 
        s = ''.join(f'<th class="text-center">{day}</th>' for day in DAYS)
        return f'<thead><tr>{s}</tr></thead>'
    
    def formatday(self, day, weekday):
        # 1. 'day == 0' のチェックは最初に実行
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        # 2. 基本変数の定義
        date_obj = date(self.year, self.month, day)
        cssclass = self.cssclasses[weekday]
        
        # 週末のクラスを追加
        if weekday == 6 or weekday == 0: # 土・日曜日
            cssclass += ' weekend'

        shift = self.shifts.get(date_obj)
        
        # 3. シフト情報によるデータ作成と労働時間の計算
        shift_detail_data = {}
        shift_output = '<div class="shift-info no-shift"></div>'
        
        if shift:

            time_str = f'{shift.start_time.strftime("%H:%M")} ~ {shift.end_time.strftime("%H:%M")}'
            
            # 労働時間計算ロジック（そのまま）
            start_dt = datetime.datetime.combine(date(1, 1, 1), shift.start_time)
            end_dt = datetime.datetime.combine(date(1, 1, 1), shift.end_time)
            
            if end_dt < start_dt:
                end_dt += datetime.timedelta(days=1)
                
            duration = end_dt - start_dt
            work_minutes = int(duration.total_seconds() / 60) 
            
            shift_output = f'<div class="shift-info">{time_str}</div>'
            
            # モーダルに渡す詳細情報
            shift_detail_data = {
                'date': date_obj.isoformat(),
                'time_str': time_str,
                'work_minutes': work_minutes, 
            }
            cssclass += ' has-shift'

        #JSONデータの作成
        json_data = json.dumps(shift_detail_data, ensure_ascii=False).replace('"', '&quot;')
            
        #統合・整理: style属性とdata属性をまとめて一度だけ定義
        inline_style = "width: 14.28% !important; height: 70px !important; box-sizing: border-box !important;"
        data_attrs = f'style="{inline_style}" data-date="{date_obj.isoformat()}" data-shift-detail="{json_data}" class="calendar-day {cssclass} clickable-cell"'

        # セル内のコンテンツ
        content = f'<div class="day-num">{day}</div>{shift_output}'
            
        return f'<td {data_attrs}>{content}</td>'
        
    
    # formatmonth メソッドをオーバーライドして、年/月を安全に設定
    # formatmonth メソッドをオーバーライドして、年/月を安全に設定
    def formatmonth(self, theyear, themonth, withyear=True):
        
        # 1. 安全チェック (以前の修正と同じ)
        try:
            self.year = int(theyear)
            self.month = int(themonth)
            date(self.year, self.month, 1) # ValueErrorチェック
        except (TypeError, ValueError):
            return f'<div class="alert alert-danger">カレンダーの年/月の値が無効です。</div>'
        
        # 2. カスタムHTML生成ロジックを実行 (最初の return を削除し、こちらを採用)
        v = []
        a = v.append
        
        # Bootstrapのテーブルクラスで囲む
        a('<div class="calendar-wrapper table-responsive">') 
        a('<table class="calendar table table-sm table-bordered">')
        
        # 月名と年のヘッダー
        #a(self.formatmonthname(theyear, themonth, withyear=withyear))
        
        # カスタム曜日ヘッダー (日〜土)
        a(self.formatweekheader()) 
        
        # 日付とシフト情報のセル
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            
        a('</table>')
        a('</div>') # calendar-wrapper の終了タグ
        
        final_output = '\n'.join(v)
        return mark_safe(final_output)

@register.simple_tag
def get_shift_calendar(user, year, month):
    """指定された年月のユーザーのシフトカレンダーHTMLを生成するタグ"""

    try:
    # ログインUserに対応する mst_employee インスタンスを取得
        employee = mst_employee.objects.get(user=user)
    except mst_employee.DoesNotExist:
    # 連携されていない場合は空のカレンダーを返すか、エラーメッセージを表示
        return f'<div class="alert alert-warning">従業員情報がアカウントに紐づいていません。</div>'

    shifts = shift_schedule.objects.filter(
    employee=employee,
    schedule_date__year=year,
    schedule_date__month=month
    )

    cal = ShiftCalendar(shifts=shifts)
    return cal.formatmonth(year, month)

@register.filter
def format_minutes_to_hours(minutes):
    """
    分を「Xh Ym」形式の文字列に変換する
    """
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return ""
        
    if minutes == 0:
        return "0h"
        
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    result = ""
    if hours > 0:
        result += f"{hours}h"
    if remaining_minutes > 0:
        if result:
            result += " "
        result += f"{remaining_minutes}m"
        
    return result