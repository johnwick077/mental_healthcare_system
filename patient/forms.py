from django import forms
from .models import Patient, Ward, Counsellor


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient

        fields = [
            'full_name',
            'age',
            'gender',
            'guardian_name',
            'guardian_contact',
            'ward',
            'assigned_counsellor',
            'photo',
            'known_conditions',
            'notes',
            'care_focus',
            'observation_focus',
            'baseline_notes',
        ]

        labels = {
            'known_conditions': 'Known Condition(s)',
            'notes': 'Patient Description',
            'care_focus': 'Care Focus',
            'observation_focus': 'Observation Focus',
            'baseline_notes': 'Baseline Notes',
        }

        widgets = {
            'full_name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'age': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1
                }
            ),

            'gender': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'guardian_name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'guardian_contact': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'ward': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'assigned_counsellor': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'photo': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'known_conditions': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': (
                        'Enter documented condition(s), '
                        'for example: OCD, anxiety disorder...'
                    )
                }
            ),

            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': (
                        'Describe the patient in relation to the '
                        'documented condition(s)...'
                    )
                }
            ),

            'care_focus': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': (
                        'Enter relevant care or support focus...'
                    )
                }
            ),

            'observation_focus': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': (
                        'What behaviours or factors should be observed '
                        'during routine interactions?'
                    )
                }
            ),

            'baseline_notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': (
                        'Describe the patient’s usual baseline '
                        'behaviour or routine...'
                    )
                }
            ),
        }


class WardForm(forms.ModelForm):
    class Meta:
        model = Ward

        fields = [
            'name',
            'capacity',
            'description'
        ]

        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'capacity': forms.NumberInput(
                attrs={
                    'class': 'form-control'
                }
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2
                }
            ),
        }