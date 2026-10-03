from django.urls import path

from .views import (
    ObservationCreateView,
    ObservationListView,
    PatientObservationHistoryView,
    PatientAIAnalysisView,
    PatientAISummaryHistoryView,
    PatientAISummaryDetailView,
    PatientObservationInfoView,
)


app_name = 'observation'


urlpatterns = [

    # --------------------------------------------------------
    # DAILY OBSERVATION
    # --------------------------------------------------------

    path(
        'add/',
        ObservationCreateView.as_view(),
        name='observation_add'
    ),

    path(
        'history/',
        ObservationListView.as_view(),
        name='observation_list'
    ),


    # --------------------------------------------------------
    # PATIENT INFORMATION
    # --------------------------------------------------------

    path(
        'patient/<int:patient_id>/info/',
        PatientObservationInfoView.as_view(),
        name='patient_observation_info'
    ),


    # --------------------------------------------------------
    # PATIENT OBSERVATION HISTORY
    # --------------------------------------------------------

    path(
        'patient/<int:patient_id>/history/',
        PatientObservationHistoryView.as_view(),
        name='patient_history'
    ),


    # --------------------------------------------------------
    # AI ANALYSIS
    # --------------------------------------------------------

    path(
        'patient/<int:patient_id>/ai-analysis/',
        PatientAIAnalysisView.as_view(),
        name='patient_ai_analysis'
    ),

    path(
        'patient/<int:patient_id>/ai-history/',
        PatientAISummaryHistoryView.as_view(),
        name='patient_ai_history'
    ),

    path(
        'ai-summary/<int:pk>/',
        PatientAISummaryDetailView.as_view(),
        name='patient_ai_summary_detail'
    ),
]