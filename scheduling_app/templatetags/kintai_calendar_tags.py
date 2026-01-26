# kintai_app/templatetags/kintai_calendar_tags.py

import calendar
import datetime
from datetime import date
from django import template
from django.utils.safestring import mark_safe
from scheduling_app.models import ShiftRequest, WeeklySchedule
from django.contrib.auth import get_user_model
import json

User = get_user_model() # 必要に応じて

register = template.Library()

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

class ShiftRequestCalendar(calendar.HTMLCalendar):
    """希望シフト申請 (shift_request) のデータを表示するためのカレンダー"""
    
    def __init__(self, request_shifts=None,weekly_schedules=None):
        super().__init__(firstweekday=6)
        # データベースから取得した希望シフトデータを 'YYYY-MM-DD' をキーとする辞書に変換
        self.request_shifts = {
            s.date.strftime('%Y-%m-%d'): s
            for s in request_shifts
        } if request_shifts else {}

        self.weekly_schedules = {
            schedule.day_of_week: schedule 
            for schedule in weekly_schedules
        } if weekly_schedules else {}

    def formatweekheader(self):
        # ★★★ 追加: 日本語の曜日ヘッダーを設定 ★★★
        DAYS = ['日', '月', '火', '水', '木', '金', '土'] 
        s = ''.join(f'<th class="text-center">{day}</th>' for day in DAYS)
        return f'<thead><tr>{s}</tr></thead>'

    def formatday(self, day_obj, weekday,):
        
        # 1. 変数の初期化
        shift_info_html = ''
        data_shift_detail = '{}'
        css_class = self.cssclasses[weekday]
        
        # 2. 無効な日付のチェック
        if day_obj is None:
            return '<td class="noday">&nbsp;</td>'

        # カレンダーの該当月以外は非表示
        if day_obj.month != self.month: 
             return '<td class="noday">&nbsp;</td>'

        # 3. 日付とCSSクラスの設定
        current_date_str = day_obj.strftime('%Y-%m-%d')
        
        if weekday == 6: # 日曜日
            css_class += ' weekend sunday'
        elif weekday == 5: # 土曜日
             css_class += ' weekend saturday'

        is_today = (date.today() == day_obj)
        if is_today:
            css_class += ' today'
            
        # 4. データを取得
        request_shift = self.request_shifts.get(current_date_str)

        basic_schedule = self.weekly_schedules.get(day_obj.weekday())
     
        if not basic_schedule:
            basic_schedule = self.weekly_schedules.get(weekday)

        # ----------------------------------------------------
        # 5. 表示ロジック: 個別申請シフト (最優先)
        # ----------------------------------------------------
        if request_shift:
            css_class += ' has-request-shift'
        
            status_text = {
                'pending': '申請中',
                'approved': '承認済',
                'rejected': '却下',
            }.get(request_shift.status, '不明')
            
            shift_info_html += f'<div class="shift-status status-{request_shift.status}">{status_text}</div>'
            
            if request_shift.is_day_off:
                shift_info_html += '<div class="shift-time text-danger">休み希望</div>'
                data_shift_detail_dict = {'is_day_off': True, 'status': request_shift.status}
            else:
                start_time_str = request_shift.start_time.strftime('%H:%M') if request_shift.start_time else '00:00'
                end_time_str = request_shift.end_time.strftime('%H:%M') if request_shift.end_time else '00:00'
                
                shift_info_html += f'<div class="shift-time">{start_time_str}〜{end_time_str}</div>'
                
                data_shift_detail_dict = {
                    ''
                    'start_time': start_time_str,
                    'end_time': end_time_str,
                    'is_day_off': False,
                    'status': request_shift.status,
                }
            
            data_shift_detail = json.dumps(data_shift_detail_dict, ensure_ascii=False).replace('"', '&quot;')
        
        # ----------------------------------------------------
        # 6. 表示ロジック: 個別申請がない場合、基本スケジュールを参照
        # ----------------------------------------------------
        elif basic_schedule: # request_shift がない場合のみチェック
            css_class += ' has-basic-shift'
            
            # 休み希望のチェックを優先
            if basic_schedule.is_day_off:
                data_shift_detail = json.dumps({
                    'is_day_off': True, 
                    'is_basic_schedule': True
                }, ensure_ascii=False).replace('"', '&quot;')
            
            # 勤務時間の設定がある場合
            elif basic_schedule.start_time and basic_schedule.end_time:
                basic_start = basic_schedule.start_time.strftime('%H:%M')
                basic_end = basic_schedule.end_time.strftime('%H:%M')
                
                shift_info_html += f'<div class="shift-time basic-shift">{basic_start}〜{basic_end}</div>'
                
                data_shift_detail = json.dumps({
                    'start_time': basic_start,
                    'end_time': basic_end,
                    'is_day_off': False,
                    'is_basic_schedule': True
                }, ensure_ascii=False).replace('"', '&quot;')

            # それ以外は data_shift_detail = '{}' のまま

        # 7. <td> タグを構築
        html = f'<td class="{css_class} clickable-cell calendar-day" data-date="{current_date_str}" data-shift-detail="{data_shift_detail}">'
        html += f'<span class="day-num">{day_obj.day}</span>'
        html += shift_info_html
        html += '</td>'
        
        return html

    def formatweek(self, theweek):
        """週をフォーマットするロジック（そのまま使用）"""
        return '<tr>%s</tr>' % ''.join(self.formatday(day_obj, day_obj.weekday()) for day_obj in theweek)

    def formatmonth(self, theyear, themonth):
        """月全体のテーブルを構築するロジック（そのまま使用）"""

        try:
            self.year = int(theyear)
            self.month = int(themonth)
        except ValueError:
             return '<div class="alert alert-danger">カレンダーの年/月の値が無効です。</div>'

        # formatmonthname() の呼び出しは不要、HTMLテンプレート側で行うため
        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar table table-bordered table-sm">\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdatescalendar(theyear, themonth):
            cal += self.formatweek(week)
        cal += '</table>'
        return mark_safe(cal)


@register.simple_tag
def get_shift_request_calendar(user, year, month):
    """
    指定されたユーザーの、指定された月の希望シフトカレンダーを生成する
    """
    # 該当月の希望シフトデータを全て取得 (効率化のため)
    start_date = date(year, month, 1)
    # 翌月1日を取得 (月末は考慮しなくてよい)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
        
    requested_shifts = ShiftRequest.objects.filter(
        user=user,
        date__gte=start_date,
        date__lt=end_date,
    )

    weekly_schedules = WeeklySchedule.objects.filter(user=user)

    # ShiftRequestCalendar クラスをインスタンス化
    cal = ShiftRequestCalendar(requested_shifts,weekly_schedules)
    
    # HTMLを生成して安全なマークとして返す
    return cal.formatmonth(year, month)