from django import forms
from schedule_app.models import trn_daily_attendance,trn_clocking

class ClockingForm(forms.ModelForm):
    class Meta:
        model = trn_clocking
        fields = ['clocking_datetime', 'clocking_type']
        widgets = {
            'clocking_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'clocking_type': forms.Select(
                choices=trn_clocking.CLOCKING_CHOICES, # モデルで定義した選択肢
                attrs={'class': 'form-select'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.clocking_datetime:
            self.initial['clocking_datetime'] = self.instance.clocking_datetime.strftime('%Y-%m-%dT%H:%M')

# フォームセットのベースを作成
ClockingFormSet = forms.modelformset_factory(
    trn_clocking,
    form=ClockingForm,
    extra=1,
    can_delete=True
)

class AttendanceCorrectionForm(forms.ModelForm):
    class Meta:
        model = trn_daily_attendance
        fields = ['attendance_datetime', 'closing_datetime']
        labels = {
            'attendance_datetime': '出勤日時',
            'closing_datetime': '退勤日時',
        }
        widgets = {
            # HTML5のdatetime-local入力を使用してカレンダー選択を可能にする
            'attendance_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control form-control-lg'},
                format='%Y-%m-%dT%H:%M'
            ),
            'closing_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control form-control-lg'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初期表示時に秒を切り捨てて表示するための設定
        if self.instance and self.instance.attendance_datetime:
            self.initial['attendance_datetime'] = self.instance.attendance_date.strftime('%Y-%m-%dT%H:%M')
        if self.instance and self.instance.closing_datetime:
            self.initial['closing_datetime'] = self.instance.closing_datetime.strftime('%Y-%m-%dT%H:%M')