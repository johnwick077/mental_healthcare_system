from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (CreateView,ListView,DetailView)
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from accounts.decorators import role_required
from patient.models import Patient
from .models import DailyObservation
from .forms import DailyObservationForm
from evidence.trend_analyzer import (get_patient_observations)
from evidence.pattern_matcher import (find_matching_patterns,analyze_pattern_match,analyze_complete_observations,)
from evidence.evidence_retriever import (get_evidence_for_pattern,get_general_research_evidence,)
from evidence.summary_builder import (build_summary_data)
from evidence.ai_summarizer import (generate_evidence_summary)
from evidence.models import AISummaryHistory
from evidence.summary_builder import (build_summary_data,make_json_safe,)


@method_decorator(
    role_required("COUNSELLOR"),
    name="dispatch"
)
class ObservationCreateView(
    LoginRequiredMixin,
    CreateView
):

    model = DailyObservation

    form_class = DailyObservationForm

    template_name = (
        "observation/observation_form.html"
    )

    success_url = reverse_lazy(
        "observation:observation_list"
    )

    def get_form_kwargs(self):

        kwargs = super().get_form_kwargs()

        kwargs["user"] = self.request.user

        return kwargs

    def form_valid(self, form):

        form.instance.counsellor = (
            self.request.user
        )

        return super().form_valid(form)


@method_decorator(
    role_required("COUNSELLOR"),
    name="dispatch"
)
class ObservationListView(
    LoginRequiredMixin,
    ListView
):

    model = DailyObservation

    template_name = (
        "observation/observation_list.html"
    )

    context_object_name = "observations"

    paginate_by = 10

    def get_queryset(self):

        queryset = (
            DailyObservation.objects
            .filter(
                counsellor=self.request.user
            )
            .select_related("patient")
        )

        search = self.request.GET.get(
            "search"
        )

        priority = self.request.GET.get(
            "priority"
        )

        if search:

            queryset = queryset.filter(
                patient__full_name__icontains=search
            )

        if priority:

            queryset = queryset.filter(
                priority_level=priority
            )

        return queryset

    def get_context_data(
        self,
        **kwargs
    ):

        context = super().get_context_data(
            **kwargs
        )

        context[
            "priority_choices"
        ] = DailyObservation.PRIORITY_CHOICES

        return context


class PatientObservationHistoryView(
    LoginRequiredMixin,
    ListView
):

    model = DailyObservation

    template_name = (
        "observation/patient_history.html"
    )

    context_object_name = "observations"

    paginate_by = 15

    def get_queryset(self):

        patient_id = self.kwargs[
            "patient_id"
        ]

        # ---------------------------------------------
        # Admin access
        # ---------------------------------------------

        if self.request.user.role == "ADMIN":

            self.patient = Patient.objects.get(
                pk=patient_id
            )

        # ---------------------------------------------
        # Counsellor access
        # ---------------------------------------------

        elif self.request.user.role == "COUNSELLOR":

            self.patient = (
                Patient.objects.filter(
                    pk=patient_id,
                    assigned_counsellor__user=(
                        self.request.user
                    ),
                    is_active=True
                )
                .first()
            )

            if not self.patient:

                from django.http import Http404

                raise Http404(
                    "You are not authorized to "
                    "view this patient's history."
                )

        else:

            from django.http import Http404

            raise Http404(
                "You are not authorized to "
                "view this patient's history."
            )

        return (
            DailyObservation.objects
            .filter(
                patient=self.patient
            )
            .select_related(
                "patient",
                "counsellor"
            )
        )

    def get_context_data(
        self,
        **kwargs
    ):

        context = super().get_context_data(
            **kwargs
        )

        context["patient"] = self.patient

        today = timezone.localdate()

        todays_count = (
            DailyObservation.objects.filter(
                patient=self.patient,
                date=today
            ).count()
        )

        minimum_daily_observations = 3

        context[
            "todays_observation_count"
        ] = todays_count

        context[
            "minimum_daily_observations"
        ] = minimum_daily_observations

        context[
            "todays_remaining"
        ] = max(
            0,
            minimum_daily_observations
            - todays_count
        )

        context[
            "daily_target_completed"
        ] = (
            todays_count
            >= minimum_daily_observations
        )

        return context


class PatientAIAnalysisView(
    LoginRequiredMixin,
    View
):
    """
    Generate an evidence-grounded AI summary
    for a patient's recent observations.
    """

    def post(self, request, patient_id):

        # =================================================
        # 1. Get patient
        # =================================================

        patient = Patient.objects.get(
            pk=patient_id
        )

        # =================================================
        # 2. Get recent observations
        # =================================================

        observations = list(
            get_patient_observations(
                patient,
                days=7
            )
        )

        if not observations:
            return render(
                request,
                "observation/ai_analysis.html",
                {
                    "patient": patient,
                    "error": (
                        "No recent observations are "
                        "available for analysis."
                    ),
                }
            )

        # =================================================
        # 3. Analyze ALL observation conditions
        # =================================================

        complete_analysis = analyze_complete_observations(
            observations,
            minimum_occurrences=2
        )

        # =================================================
        # 4. Find research-backed observation patterns
        # =================================================

        matched_patterns = find_matching_patterns(
            observations
        )

        # =================================================
        # 5. Select a research pattern if available
        # =================================================

        pattern = (
            matched_patterns[0]
            if matched_patterns
            else None
        )

        # =================================================
        # 6. Analyze research pattern
        # =================================================

        if pattern:

            pattern_result = analyze_pattern_match(
                pattern,
                observations
            )

            # ---------------------------------------------
            # Retrieve evidence for matched pattern
            # ---------------------------------------------

            research_evidence = (
                get_evidence_for_pattern(
                    pattern
                )
            )

        else:

            # ---------------------------------------------
            # No research pattern matched.
            # This must NOT stop AI analysis.
            # ---------------------------------------------

            pattern_result = {
                "pattern_name": (
                    "Comprehensive Observation Analysis"
                ),

                "pattern_description": (
                    "Analysis of all recorded observation "
                    "parameters during the selected "
                    "observation period."
                ),

                "possible_concern": "",

                "recommendation": (
                    "Continue routine observation and "
                    "compare observed changes with the "
                    "patient's usual baseline."
                ),

                "minimum_days": 0,

                "minimum_occurrences": 2,

                "matched_fields": {},

                "trends": complete_analysis.get(
                    "trends",
                    {}
                ),
            }

            research_evidence = get_general_research_evidence()

        # =================================================
        # 7. Build structured summary data
        # =================================================

        summary_data = build_summary_data(
            observations,
            pattern_result,
            research_evidence,
            complete_analysis=complete_analysis
        )

        # =================================================
        # 8. Generate AI summary
        # =================================================

        ai_summary = generate_evidence_summary(
            summary_data
        )

        # =================================================
        # 9. Extract AI generated values
        # =================================================

        observation_summary = (
            ai_summary.observation_summary
        )

        observed_changes = (
            ai_summary.observed_changes
        )

        evidence_interpretation = (
            ai_summary.evidence_interpretation
        )

        recommended_follow_up = (
            ai_summary.recommended_follow_up
        )

        disclaimer = (
            ai_summary.disclaimer
        )

        # =================================================
        # 10. Extract structured analysis
        # =================================================

        analysis_data = summary_data.get(
            "analysis",
            {}
        )

        trends = analysis_data.get(
            "trends",
            {}
        )

        matched_fields = analysis_data.get(
            "matched_fields",
            {}
        )

        matched_pattern_data = (
            summary_data.get(
                "matched_pattern",
                {}
            )
        )

        # =================================================
        # 11. Get complete condition analysis
        # =================================================

        condition_analysis = (
            complete_analysis.get(
                "condition_analysis",
                {}
            )
        )

        repeated_conditions = (
            complete_analysis.get(
                "repeated_conditions",
                []
            )
        )

        # =================================================
        # 12. Build JSON-safe structured analysis
        # =================================================

        structured_analysis = make_json_safe(
            {
                "trends": trends,

                "matched_fields": (
                    matched_fields
                ),

                "matched_pattern": (
                    matched_pattern_data
                ),

                "condition_analysis": (
                    condition_analysis
                ),

                "repeated_conditions": (
                    repeated_conditions
                ),
            }
        )

        # =================================================
        # 13. Calculate observation days
        # =================================================

        observation_dates = {
            observation.date
            for observation in observations
            if observation.date
        }

        observation_days = len(
            observation_dates
        )

        # =================================================
        # 14. Save AI summary history
        # =================================================

        AISummaryHistory.objects.create(
            patient=patient,

            generated_by=request.user,

            observation_count=len(
                observations
            ),

            observation_days=(
                observation_days
            ),

            matched_pattern=(
                pattern.name
                if pattern
                else "Comprehensive Observation Analysis"
            ),

            observation_summary=(
                observation_summary
            ),

            observed_changes=(
                observed_changes
            ),

            evidence_interpretation=(
                evidence_interpretation
            ),

            recommended_follow_up=(
                recommended_follow_up
            ),

            disclaimer=(
                disclaimer
            ),

            research_evidence=(
                research_evidence
            ),

            structured_analysis=(
                structured_analysis
            ),
        )

        # =================================================
        # 15. Display current analysis
        # =================================================

        return render(
            request,
            "observation/ai_analysis.html",
            {
                "patient": patient,

                "observations": observations,

                "matched_patterns": (
                    matched_patterns
                ),

                "pattern": pattern,

                "pattern_result": (
                    pattern_result
                ),

                "research_evidence": (
                    research_evidence
                ),

                "summary_data": (
                    summary_data
                ),

                "analysis_data": (
                    analysis_data
                ),

                "trends": trends,

                "matched_fields": (
                    matched_fields
                ),

                "matched_pattern_data": (
                    matched_pattern_data
                ),

                "condition_analysis": (
                    condition_analysis
                ),

                "repeated_conditions": (
                    repeated_conditions
                ),

                "ai_summary": (
                    ai_summary
                ),

                "observation_summary": (
                    observation_summary
                ),

                "observed_changes": (
                    observed_changes
                ),

                "evidence_interpretation": (
                    evidence_interpretation
                ),

                "recommended_follow_up": (
                    recommended_follow_up
                ),

                "disclaimer": (
                    disclaimer
                ),
            }
        )
class PatientAISummaryHistoryView(
    LoginRequiredMixin,
    ListView
):

    model = AISummaryHistory

    template_name = (
        "observation/ai_summary_history.html"
    )

    context_object_name = "summaries"

    def get_queryset(self):

        patient_id = self.kwargs[
            "patient_id"
        ]

        patient = Patient.objects.get(
            pk=patient_id
        )

        # ---------------------------------------------
        # Admin access
        # ---------------------------------------------

        if self.request.user.is_staff:

            allowed = True

        # ---------------------------------------------
        # Counsellor access
        # ---------------------------------------------

        elif hasattr(
            self.request.user,
            "counsellor_profile"
        ):

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
            .filter(
                patient=patient
            )
            .order_by(
                "-generated_at"
            )
        )

    def get_context_data(
        self,
        **kwargs
    ):

        context = super().get_context_data(
            **kwargs
        )

        context[
            "patient"
        ] = self.patient

        return context


class PatientAISummaryDetailView(
    LoginRequiredMixin,
    DetailView
):

    model = AISummaryHistory

    template_name = (
        "observation/ai_summary_detail.html"
    )

    context_object_name = "summary"

    def get_object(
        self,
        queryset=None
    ):

        summary = (
            super().get_object(
                queryset
            )
        )

        patient = summary.patient

        # ---------------------------------------------
        # Admin access
        # ---------------------------------------------

        if self.request.user.is_staff:

            return summary

        # ---------------------------------------------
        # Counsellor access
        # ---------------------------------------------

        if (
            hasattr(
                self.request.user,
                "counsellor_profile"
            )
            and patient.assigned_counsellor
            == self.request.user.counsellor_profile
        ):

            return summary

        from django.http import Http404

        raise Http404