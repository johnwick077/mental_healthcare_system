from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from accounts.decorators import role_required
from patient.models import Patient
from .models import DailyObservation
from .forms import DailyObservationForm
from django.views import View
from evidence.trend_analyzer import get_patient_observations
from evidence.pattern_matcher import find_matching_patterns, analyze_pattern_match
from evidence.evidence_retriever import get_evidence_for_pattern
from evidence.summary_builder import build_summary_data
from evidence.ai_summarizer import generate_evidence_summary
from django.utils import timezone


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
    Full observation timeline for a single patient.

    Admins can view all patients.
    Counsellors can view only patients assigned to them.
    """

    model = DailyObservation
    template_name = 'observation/patient_history.html'
    context_object_name = 'observations'
    paginate_by = 15

    def get_queryset(self):

        patient_id = self.kwargs['patient_id']

        # Admin can access all patients
        if self.request.user.role == 'ADMIN':

            self.patient = Patient.objects.get(
                pk=patient_id
            )

        # Counsellor can access only assigned patients
        elif self.request.user.role == 'COUNSELLOR':

            self.patient = Patient.objects.filter(
                pk=patient_id,
                assigned_counsellor__user=self.request.user,
                is_active=True
            ).first()

            if not self.patient:
                from django.http import Http404
                raise Http404(
                    "You are not authorized to view this patient's history."
                )

        else:

            from django.http import Http404
            raise Http404(
                "You are not authorized to view this patient's history."
            )

        return DailyObservation.objects.filter(
            patient=self.patient
        ).select_related(
            'patient',
            'counsellor'
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['patient'] = self.patient

        today = timezone.localdate()

        todays_count = DailyObservation.objects.filter(
            patient=self.patient,
            date=today
        ).count()

        minimum_daily_observations = 3

        context['todays_observation_count'] = todays_count

        context['minimum_daily_observations'] = (
            minimum_daily_observations
        )

        context['todays_remaining'] = max(
            0,
            minimum_daily_observations - todays_count
        )

        context['daily_target_completed'] = (
            todays_count >= minimum_daily_observations
        )

        return context


class PatientAIAnalysisView(LoginRequiredMixin, View):
    """
    Generate an evidence-grounded AI summary
    for an authorized patient's recent observations.
    """

    def post(self, request, patient_id):

        # Admin can access all patients
        if request.user.role == 'ADMIN':

            patient = Patient.objects.filter(
                pk=patient_id
            ).first()

        # Counsellor can access only assigned active patients
        elif request.user.role == 'COUNSELLOR':

            patient = Patient.objects.filter(
                pk=patient_id,
                assigned_counsellor__user=request.user,
                is_active=True
            ).first()

        else:

            patient = None

        if not patient:

            from django.http import Http404

            raise Http404(
                "You are not authorized to analyse this patient."
            )


        observations = list(
            get_patient_observations(
                patient,
                days=7
            )
        )


        if not observations:

            return render(
                request,
                'observation/ai_analysis.html',
                {
                    'patient': patient,
                    'error': (
                        'No recent observations are available '
                        'for analysis.'
                    ),
                }
            )


        matched_patterns = find_matching_patterns(
            observations
        )


        if not matched_patterns:

            return render(
                request,
                'observation/ai_analysis.html',
                {
                    'patient': patient,
                    'error': (
                        'No observation pattern matched '
                        'the recent observations.'
                    ),
                }
            )


        pattern = matched_patterns[0]


        pattern_result = analyze_pattern_match(
            pattern,
            observations
        )


        research_evidence = get_evidence_for_pattern(
            pattern
        )


        summary_data = build_summary_data(
            observations,
            pattern_result,
            research_evidence
        )


        ai_summary = generate_evidence_summary(
            summary_data
        )


        return render(
            request,
            'observation/ai_analysis.html',
            {
                'patient': patient,
                'observations': observations,
                'pattern': pattern,
                'pattern_result': pattern_result,
                'research_evidence': research_evidence,
                'summary_data': summary_data,
                'ai_summary': ai_summary,
            }
        )