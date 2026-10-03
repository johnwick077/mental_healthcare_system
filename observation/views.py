from django.shortcuts import render
from django.http import JsonResponse, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    ListView,
    DetailView,
)
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View

from accounts.decorators import role_required
from patient.models import Patient
from .models import DailyObservation
from .forms import DailyObservationForm

from evidence.trend_analyzer import (
    get_patient_observations,
)

from evidence.pattern_matcher import (
    find_matching_patterns,
    analyze_pattern_match,
    analyze_complete_observations,
)

from evidence.evidence_retriever import (
    get_evidence_for_pattern,
    get_general_research_evidence,
)

from evidence.summary_builder import (
    build_summary_data,
    make_json_safe,
)

from evidence.ai_summarizer import (
    generate_evidence_summary,
)

from evidence.models import AISummaryHistory


# ============================================================
# CREATE DAILY OBSERVATION
# ============================================================

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


# ============================================================
# PATIENT INFORMATION FOR OBSERVATION FORM
# ============================================================

@method_decorator(
    role_required("COUNSELLOR"),
    name="dispatch"
)
class PatientObservationInfoView(
    LoginRequiredMixin,
    View
):
    """
    Returns read-only patient information for the
    selected patient.

    Only the counsellor assigned to the patient can
    retrieve this information.
    """

    def get(
        self,
        request,
        patient_id
    ):

        patient = (
            Patient.objects
            .select_related(
                "ward",
                "assigned_counsellor__user"
            )
            .filter(
                pk=patient_id,
                assigned_counsellor__user=request.user,
                is_active=True
            )
            .first()
        )

        if not patient:

            raise Http404(
                "Patient not found or not assigned to you."
            )

        return JsonResponse({

            "id": patient.id,

            "full_name": patient.full_name,

            "age": patient.age,

            "gender": patient.get_gender_display(),

            "ward": (
                patient.ward.name
                if patient.ward
                else "Not assigned"
            ),

            "known_conditions": (
                patient.known_conditions
                or "Not provided"
            ),

            "notes": (
                patient.notes
                or "Not provided"
            ),

            "care_focus": (
                patient.care_focus
                or "Not provided"
            ),

            "observation_focus": (
                patient.observation_focus
                or "Not provided"
            ),

            "baseline_notes": (
                patient.baseline_notes
                or "Not provided"
            ),
        })


# ============================================================
# OBSERVATION HISTORY
# ============================================================

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


# ============================================================
# PATIENT OBSERVATION HISTORY
# ============================================================

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

        # ----------------------------------------------------
        # ADMIN ACCESS
        # ----------------------------------------------------

        if self.request.user.role == "ADMIN":

            self.patient = Patient.objects.get(
                pk=patient_id
            )

        # ----------------------------------------------------
        # COUNSELLOR ACCESS
        # ----------------------------------------------------

        elif self.request.user.role == "COUNSELLOR":

            self.patient = (
                Patient.objects
                .filter(
                    pk=patient_id,
                    assigned_counsellor__user=(
                        self.request.user
                    ),
                    is_active=True
                )
                .first()
            )

            if not self.patient:

                raise Http404(
                    "You are not authorized to "
                    "view this patient's history."
                )

        else:

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
            DailyObservation.objects
            .filter(
                patient=self.patient,
                date=today
            )
            .count()
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


# ============================================================
# AI OBSERVATION ANALYSIS
# ============================================================

class PatientAIAnalysisView(
    LoginRequiredMixin,
    View
):
    """
    Generate an evidence-grounded AI summary
    for a patient's recent observations.
    """

    def post(
        self,
        request,
        patient_id
    ):

        # ====================================================
        # 1. GET PATIENT
        # ====================================================

        patient = Patient.objects.get(
            pk=patient_id
        )


        # ====================================================
        # 2. GET RECENT OBSERVATIONS
        # ====================================================

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


        # ====================================================
        # 3. ANALYZE ALL OBSERVATION CONDITIONS
        # ====================================================

        complete_analysis = (
            analyze_complete_observations(
                observations,
                minimum_occurrences=2
            )
        )


        # ====================================================
        # 4. FIND RESEARCH-BACKED PATTERNS
        # ====================================================

        matched_patterns = (
            find_matching_patterns(
                observations
            )
        )


        # ====================================================
        # 5. SELECT RESEARCH PATTERN
        # ====================================================

        pattern = (
            matched_patterns[0]
            if matched_patterns
            else None
        )


        # ====================================================
        # 6. ANALYZE RESEARCH PATTERN
        # ====================================================

        if pattern:

            pattern_result = (
                analyze_pattern_match(
                    pattern,
                    observations
                )
            )

            research_evidence = (
                get_evidence_for_pattern(
                    pattern
                )
            )

        else:

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

            research_evidence = (
                get_general_research_evidence()
            )


        # ====================================================
        # 7. CALCULATE OBSERVATION PERIOD
        # ====================================================

        observation_dates = {
            observation.date
            for observation in observations
            if observation.date
        }

        observation_count = len(
            observations
        )

        observation_days = len(
            observation_dates
        )

        average_observations_per_day = (
            round(
                observation_count
                / observation_days,
                2
            )
            if observation_days > 0
            else 0
        )


        # ====================================================
        # 8. BUILD STRUCTURED SUMMARY DATA
        # ====================================================

        summary_data = build_summary_data(
            observations,
            pattern_result,
            research_evidence,
            complete_analysis=complete_analysis
        )


        # Add observation period values explicitly.

        summary_data[
            "observation_count"
        ] = observation_count

        summary_data[
            "observation_days"
        ] = observation_days

        summary_data[
            "average_observations_per_day"
        ] = (
            average_observations_per_day
        )


        # ====================================================
        # 9. GENERATE AI SUMMARY
        # ====================================================

        ai_summary = generate_evidence_summary(
            summary_data
        )


        # ====================================================
        # 10. EXTRACT AI GENERATED VALUES
        # ====================================================

        observation_summary = (
            ai_summary.observation_summary
        )

        ai_repeated_conditions = getattr(
            ai_summary,
            "repeated_conditions",
            []
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


        # ====================================================
        # 11. EXTRACT STRUCTURED ANALYSIS
        # ====================================================

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


        # ====================================================
        # 12. GET COMPLETE CONDITION ANALYSIS
        # ====================================================

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


        # ====================================================
        # 13. BUILD COMPLETE JSON-SAFE HISTORY DATA
        # ====================================================

        structured_analysis = make_json_safe(
            {

                # --------------------------------------------
                # Observation Period
                # --------------------------------------------

                "observation_period": {

                    "observation_count": (
                        observation_count
                    ),

                    "observation_days": (
                        observation_days
                    ),

                    "average_observations_per_day": (
                        average_observations_per_day
                    ),
                },


                # --------------------------------------------
                # System-calculated repeated conditions
                # --------------------------------------------

                "repeated_conditions": (
                    repeated_conditions
                ),


                # --------------------------------------------
                # AI-readable repeated conditions
                # --------------------------------------------

                "ai_repeated_conditions": (
                    ai_repeated_conditions
                ),


                # --------------------------------------------
                # Complete condition analysis
                # --------------------------------------------

                "condition_analysis": (
                    condition_analysis
                ),


                # --------------------------------------------
                # Trends
                # --------------------------------------------

                "trends": (
                    trends
                ),


                # --------------------------------------------
                # Matched fields
                # --------------------------------------------

                "matched_fields": (
                    matched_fields
                ),


                # --------------------------------------------
                # Matched research pattern
                # --------------------------------------------

                "matched_pattern": (
                    matched_pattern_data
                ),


                # --------------------------------------------
                # Research evidence
                # --------------------------------------------

                "research_evidence": (
                    research_evidence
                ),


                # --------------------------------------------
                # Complete AI-generated summary
                # --------------------------------------------

                "ai_summary": {

                    "observation_summary": (
                        observation_summary
                    ),

                    "repeated_conditions": (
                        ai_repeated_conditions
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
                },
            }
        )


        # ====================================================
        # 14. SAVE COMPLETE AI SUMMARY HISTORY
        # ====================================================

        AISummaryHistory.objects.create(

            patient=patient,

            generated_by=request.user,

            observation_count=(
                observation_count
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


        # ====================================================
        # 15. DISPLAY CURRENT ANALYSIS
        # ====================================================

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

                "trends": (
                    trends
                ),

                "matched_fields": (
                    matched_fields
                ),

                "matched_pattern_data": (
                    matched_pattern_data
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

                "observation_count": (
                    observation_count
                ),

                "observation_days": (
                    observation_days
                ),

                "average_observations_per_day": (
                    average_observations_per_day
                ),
            }
        )


# ============================================================
# AI SUMMARY HISTORY
# ============================================================

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


        # ----------------------------------------------------
        # ADMIN ACCESS
        # ----------------------------------------------------

        if self.request.user.is_staff:

            allowed = True


        # ----------------------------------------------------
        # COUNSELLOR ACCESS
        # ----------------------------------------------------

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


# ============================================================
# AI SUMMARY DETAIL
# ============================================================

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


        # ----------------------------------------------------
        # ADMIN ACCESS
        # ----------------------------------------------------

        if self.request.user.is_staff:

            return summary


        # ----------------------------------------------------
        # COUNSELLOR ACCESS
        # ----------------------------------------------------

        if (
            hasattr(
                self.request.user,
                "counsellor_profile"
            )
            and patient.assigned_counsellor
            == self.request.user.counsellor_profile
        ):

            return summary


        raise Http404