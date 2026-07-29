from django.urls import path
from .views import ObservationCreateView, ObservationListView, PatientObservationHistoryView

app_name = 'observation'

urlpatterns = [
    path('add/', ObservationCreateView.as_view(), name='observation_add'),
    path('history/', ObservationListView.as_view(), name='observation_list'),
    path('patient/<int:patient_id>/history/', PatientObservationHistoryView.as_view(), name='patient_history'),
]