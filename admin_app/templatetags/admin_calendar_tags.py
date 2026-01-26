from django import template
from datetime import datetime, date
from django.utils import timezone

register = template.Library()

@register.filter
def get_shift_on_day(shift_dict, key):
    # エラー回避のため、辞書（dict）であるかチェックを入れる
    if not isinstance(shift_dict, dict):
        return None
    return shift_dict.get(str(key))

@register.filter(name='get_item')  # 明示的に名前を指定
def get_item(dictionary, key):
    """辞書から変数(key)を使って値を取得する汎用フィルタ"""
    if not dictionary or not isinstance(dictionary, dict):
        return None
    # keyを文字列に変換して検索
    return dictionary.get(str(key))

@register.filter
def get_actual_bar_style(actual):
    """実績バー用 (USE_TZ=False 対応版)"""
    if not actual or not actual.attendance_datetime:
        return "display: none;"

    start_dt = actual.attendance_datetime
    if timezone.is_aware(start_dt):
        start_dt = timezone.localtime(start_dt)
        
    start_float = start_dt.hour + start_dt.minute / 60.0 + start_dt.second / 3600.0
    
    if actual.closing_datetime:
        end_dt = actual.closing_datetime
        if timezone.is_aware(end_dt):
            end_dt = timezone.localtime(end_dt)
            
        if end_dt.date() > start_dt.date():
            end_float = 24.0 + end_dt.hour + end_dt.minute / 60.0
        else:
            end_float = end_dt.hour + end_dt.minute / 60.0
    else:
        end_float = start_float + 1.0

    left = (start_float / 24.0) * 100.0
    width = ((end_float - start_float) / 24.0) * 100.0
    
    width = max(width, 1.0)

    return f"left: {left:.2f}%; width: {width:.2f}%;"

@register.filter
def get_shift_bar_style(shift):
    """予定バー用 (TimeField)"""
    if not shift or not shift.start_time or not shift.end_time:
        return "display: none;"
    
    # 24時間に対する割合計算
    start = shift.start_time.hour + shift.start_time.minute / 60
    end = shift.end_time.hour + shift.end_time.minute / 60
    
    left = (start / 24) * 100
    width = ((end - start) / 24) * 100
    if width < 0: width = 2 # 異常値対策
    
    return f"left: {left}%; width: {width}%;"

@register.filter
def j_weekday(value):
    """
    日付オブジェクトを日本語の曜日（月、火...）に変換するフィルター
    """
    if not value:
        return ""
    weekdays = ["日", "月", "火", "水", "木", "金", "土"]
    try:
        w = int(value.strftime("%w"))
        return weekdays[w]
    except (ValueError, AttributeError):
        return ""