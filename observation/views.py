from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from accounts.decorators import role_required
from patient.models import Patient
from .models import DailyObservation
from .forms import DailyObservationForm


@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class ObservationCreateView(LoginRequiredMixin, CreateView):
    model = DailyObservation
    form_class = DailyObservationForm
    template_name = 'observation/observation_form.html'
    success_url = reverse_lazy('observation:observation_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.counsellor = self.request.user
        return super().form_valid(form)


@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class ObservationListView(LoginRequiredMixin, ListView):
    model = DailyObservation
    template_name = 'observation/observation_list.html'
    context_object_name = 'observations'
    paginate_by = 10

    def get_queryset(self):
        qs = DailyObservation.objects.filter(
            counsellor=self.request.user
        ).select_related('patient')
        search = self.request.GET.get('search')
        priority = self.request.GET.get('priority')
        if search:
            qs = qs.filter(patient__full_name__icontains=search)
        if priority:
            qs = qs.filter(priority_level=priority)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['priority_choices'] = DailyObservation.PRIORITY_CHOICES
        return context


class PatientObservationHistoryView(LoginRequiredMixin, ListView):
    """
    Full observation timeline for a single patient (used on patient detail page).
    """
    model = DailyObservation
    template_name = 'observation/patient_history.html'
    context_object_name = 'observations'
    paginate_by = 15

    def get_queryset(self):
        self.patient = Patient.objects.get(pk=self.kwargs['patient_id'])
        return DailyObservation.objects.filter(patient=self.patient)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.patient
        return context