from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from accounts.decorators import role_required
from django.utils.decorators import method_decorator
from .models import Patient, Ward
from .forms import PatientForm, WardForm


@method_decorator(role_required('ADMIN'), name='dispatch')
class PatientListView(LoginRequiredMixin, ListView):
    model = Patient
    template_name = 'patient/patient_list.html'
    context_object_name = 'patients'
    paginate_by = 10

    def get_queryset(self):
        qs = Patient.objects.select_related('ward', 'assigned_counsellor').all()
        search = self.request.GET.get('search')
        ward = self.request.GET.get('ward')
        if search:
            qs = qs.filter(Q(full_name__icontains=search) | Q(guardian_name__icontains=search))
        if ward:
            qs = qs.filter(ward_id=ward)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wards'] = Ward.objects.all()
        return context


@method_decorator(role_required('ADMIN'), name='dispatch')
class PatientCreateView(LoginRequiredMixin, CreateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patient/patient_form.html'
    success_url = reverse_lazy('patient:patient_list')


@method_decorator(role_required('ADMIN'), name='dispatch')
class PatientUpdateView(LoginRequiredMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    template_name = 'patient/patient_form.html'
    success_url = reverse_lazy('patient:patient_list')


class PatientDetailView(LoginRequiredMixin, DetailView):
    """
    Accessible to Admin (all patients) and Counsellor (only assigned patients) —
    access restriction refined further in Module 4 once observations exist.
    """
    model = Patient
    template_name = 'patient/patient_detail.html'
    context_object_name = 'patient'


@method_decorator(role_required('ADMIN'), name='dispatch')
class WardCreateView(LoginRequiredMixin, CreateView):
    model = Ward
    form_class = WardForm
    template_name = 'patient/ward_form.html'
    success_url = reverse_lazy('patient:ward_list')


@method_decorator(role_required('ADMIN'), name='dispatch')
class WardListView(LoginRequiredMixin, ListView):
    model = Ward
    template_name = 'patient/ward_list.html'
    context_object_name = 'wards'