from django import forms
from .models import DailyObservation


class DailyObservationForm(forms.ModelForm):

    class Meta:
        model = DailyObservation

        fields = [
            'patient',
            'mood',
            'behaviour',
            'sleep_quality',
            'appetite',
            'personal_hygiene',
            'communication',
            'participation',
            'remarks',
        ]

        widgets = {

            'patient': forms.Select(
                attrs={
                    'class': 'form-select',
                    'id': 'id_patient',
                }
            ),

            'mood': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'behaviour': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'sleep_quality': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'appetite': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'personal_hygiene': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'communication': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'participation': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': (
                        'Add any relevant observation remarks...'
                    )
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        # Logged-in counsellor
        user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # Only show active patients assigned
        # to the logged-in counsellor.
        if user and hasattr(user, 'counsellor_profile'):

            self.fields['patient'].queryset = (
                user.counsellor_profile.patients
                .filter(
                    is_active=True
                )
                .select_related(
                    'ward'
                )
                .order_by(
                    'full_name'
                )
            )