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
from evidence.models import AISummaryHistory


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

    def post(self, request, patient_id):

        # --------------------------------------------------
        # 1. Get patient
        # --------------------------------------------------
        patient = Patient.objects.get(pk=patient_id)

        # --------------------------------------------------
        # 2. Access control
        # --------------------------------------------------
        if request.user.is_staff:
            allowed = True

        elif hasattr(request.user, 'counsellor_profile'):
            allowed = patient.assigned_counsellor == request.user.counsellor_profile

        else:
            allowed = False

        if not allowed:
            from django.http import Http404
            raise Http404

        # --------------------------------------------------
        # 3. Get recent observations
        # --------------------------------------------------
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
                    'error': 'No observations available for AI analysis.'
                }
            )

        # --------------------------------------------------
        # 4. Find matching observation patterns
        # --------------------------------------------------
        matched_patterns = find_matching_patterns(observations)

        if not matched_patterns:
            return render(
                request,
                'observation/ai_analysis.html',
                {
                    'patient': patient,
                    'error': 'No matching observation pattern was found.'
                }
            )

        # --------------------------------------------------
        # 5. Analyze the first matched pattern
        # --------------------------------------------------
        pattern = matched_patterns[0]

        pattern_result = analyze_pattern_match(
            pattern,
            observations
        )

        # --------------------------------------------------
        # 6. Retrieve research evidence
        # --------------------------------------------------
        research_evidence = get_evidence_for_pattern(
            pattern
        )

        # --------------------------------------------------
        # 7. Build AI input
        # --------------------------------------------------
        summary_data = build_summary_data(
            observations,
            pattern_result,
            research_evidence
        )

        # --------------------------------------------------
        # 8. Generate AI summary
        # --------------------------------------------------
        ai_summary = generate_evidence_summary(
            summary_data
        )

        # --------------------------------------------------
        # 9. Calculate observation days
        # --------------------------------------------------
        observation_days = len(
            set(
                observation.date
                for observation in observations
            )
        )

        # --------------------------------------------------
        # 10. SAVE AI SUMMARY HISTORY
        # --------------------------------------------------
        AISummaryHistory.objects.create(
            patient=patient,
            generated_by=request.user,
            observation_count=len(observations),
            observation_days=observation_days,
            matched_pattern=pattern.name,
            observation_summary=ai_summary.observation_summary,
            observed_changes=ai_summary.observed_changes,
            evidence_interpretation=ai_summary.evidence_interpretation,
            recommended_follow_up=ai_summary.recommended_follow_up,
            disclaimer=ai_summary.disclaimer,
            research_evidence=research_evidence,
        )

        # --------------------------------------------------
        # 11. Show current result
        # --------------------------------------------------
        return render(
            request,
            'observation/ai_analysis.html',
            {
                'patient': patient,
                'observations': observations,
                'matched_patterns': matched_patterns,
                'pattern_result': pattern_result,
                'research_evidence': research_evidence,
                'ai_summary': ai_summary,
            }
        )

class PatientAISummaryHistoryView(LoginRequiredMixin, ListView):

    model = AISummaryHistory
    template_name = 'observation/ai_summary_history.html'
    context_object_name = 'summaries'

    def get_queryset(self):

        patient_id = self.kwargs['patient_id']

        patient = Patient.objects.get(pk=patient_id)

        # Admin can view all patients
        if self.request.user.is_staff:
            allowed = True

        # Counsellor can view only assigned patients
        elif hasattr(self.request.user, 'counsellor_profile'):
            allowed = (
                patient.assigned_counsellor
                == self.request.user.counsellor_profile
            )

        else:
            allowed = False

        if not allowed:
            from django.http import Http404
            raise Http404

        self.patient = patient

        return (
            AISummaryHistory.objects
            .filter(patient=patient)
            .order_by('-generated_at')
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['patient'] = self.patient

        return context

class PatientAISummaryDetailView(LoginRequiredMixin, DetailView):

    model = AISummaryHistory
    template_name = 'observation/ai_summary_detail.html'
    context_object_name = 'summary'

    def get_object(self, queryset=None):

        summary = super().get_object(queryset)

        patient = summary.patient

        if self.request.user.is_staff:
            return summary

        if (
            hasattr(self.request.user, 'counsellor_profile')
            and patient.assigned_counsellor
            == self.request.user.counsellor_profile
        ):
            return summary

        from django.http import Http404
        raise Http404