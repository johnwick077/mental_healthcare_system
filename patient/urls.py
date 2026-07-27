from django.urls import path
from .views import (
    PatientListView, PatientCreateView, PatientUpdateView, PatientDetailView,
    WardListView, WardCreateView
)

app_name = 'patient'

urlpatterns = [
    path('', PatientListView.as_view(), name='patient_list'),
    path('add/', PatientCreateView.as_view(), name='patient_add'),
    path('<int:pk>/edit/', PatientUpdateView.as_view(), name='patient_edit'),
    path('<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),
    path('wards/', WardListView.as_view(), name='ward_list'),
    path('wards/add/', WardCreateView.as_view(), name='ward_add'),
]