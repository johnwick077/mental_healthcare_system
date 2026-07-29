from django import forms
from django.forms import inlineformset_factory
from .models import ResourceRequest, RequestItem, ResourceItem, Inventory


class ResourceRequestForm(forms.ModelForm):
    class Meta:
        model = ResourceRequest
        fields = ['patient', 'remarks']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


RequestItemFormSet = inlineformset_factory(
    ResourceRequest, RequestItem,
    fields=['item', 'quantity_requested'],
    extra=3, can_delete=True,
    widgets={
        'item': forms.Select(attrs={'class': 'form-select'}),
        'quantity_requested': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)


class InventoryUpdateForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['quantity_in_stock']
        widgets = {'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'})}