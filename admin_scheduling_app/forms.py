from django import forms
from schedule_app.models import shift_schedule

class ShiftEditForm(forms.ModelForm):
    class Meta:
        model = shift_schedule
        fields = ['employee', 'schedule_date', 'start_time', 'end_time']
        widgets = {
            'schedule_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end and start >= end:
            raise forms.ValidationError("終了時間は開始時間より後の時刻にしてください。")
        return cleaned_data