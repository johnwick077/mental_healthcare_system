from django import forms
from .models import Patient, Ward, Counsellor


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'full_name', 'age', 'gender', 'guardian_name', 'guardian_contact',
            'ward', 'assigned_counsellor', 'photo', 'notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.Select(attrs={'class': 'form-select'}),
            'assigned_counsellor': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class WardForm(forms.ModelForm):
    class Meta:
        model = Ward
        fields = ['name', 'capacity', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }