from django.urls import path
from django.http import HttpResponse
from .views import AdminDashboardView, CounsellorDashboardView, StoreDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('counsellor/', CounsellorDashboardView.as_view(), name='counsellor_dashboard'),
    path('store/', StoreDashboardView.as_view(), name='store_dashboard'),
]