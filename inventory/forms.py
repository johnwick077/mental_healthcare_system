from django import forms
from django.forms import inlineformset_factory

from .models import (
    ResourceRequest,
    RequestItem,
    ResourceItem,
    Inventory,
)


class ResourceRequestForm(forms.ModelForm):

    class Meta:
        model = ResourceRequest
        fields = ['patient', 'remarks']

        widgets = {
            'patient': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'remarks': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Enter any additional remarks...',
                }
            ),
        }

        labels = {
            'patient': 'Patient',
            'remarks': 'Remarks',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

        super().__init__(*args, **kwargs)

        # Only show patients assigned to this counsellor
        if self.user and self.user.is_authenticated:

            if getattr(self.user, 'role', None) == 'COUNSELLOR':
                self.fields['patient'].queryset = (
                    self.fields['patient']
                    .queryset
                    .filter(
                        assigned_counsellor__user=self.user,
                        is_active=True
                    )
                    .select_related(
                        'ward',
                        'assigned_counsellor__user'
                    )
                    .order_by('full_name')
                )

            else:
                self.fields['patient'].queryset = (
                    self.fields['patient']
                    .queryset
                    .filter(is_active=True)
                    .order_by('full_name')
                )

    def clean_patient(self):
        patient = self.cleaned_data['patient']

        # Extra security check
        if self.user and getattr(self.user, 'role', None) == 'COUNSELLOR':

            if patient.assigned_counsellor is None:
                raise forms.ValidationError(
                    'This patient is not assigned to you.'
                )

            if patient.assigned_counsellor.user != self.user:
                raise forms.ValidationError(
                    'You can only create resource requests for patients assigned to you.'
                )

            if not patient.is_active:
                raise forms.ValidationError(
                    'This patient is inactive.'
                )

        return patient


class RequestItemForm(forms.ModelForm):

    class Meta:
        model = RequestItem

        fields = [
            'item',
            'quantity_requested',
        ]

        widgets = {
            'item': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'quantity_requested': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1,
                }
            ),
        }

    def clean_quantity_requested(self):
        quantity = self.cleaned_data.get('quantity_requested')

        if quantity is not None and quantity < 1:
            raise forms.ValidationError(
                'Quantity must be at least 1.'
            )

        return quantity


RequestItemFormSet = inlineformset_factory(
    ResourceRequest,
    RequestItem,
    form=RequestItemForm,
    fields=[
        'item',
        'quantity_requested',
    ],
    extra=3,
    can_delete=True,
)


class InventoryUpdateForm(forms.ModelForm):

    class Meta:
        model = Inventory

        fields = [
            'quantity_in_stock',
        ]

        widgets = {
            'quantity_in_stock': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                }
            ),
        }

        labels = {
            'quantity_in_stock': 'Quantity in Stock',
        }

    def clean_quantity_in_stock(self):
        quantity = self.cleaned_data.get('quantity_in_stock')

        if quantity is not None and quantity < 0:
            raise forms.ValidationError(
                'Stock quantity cannot be negative.'
            )

        return quantity