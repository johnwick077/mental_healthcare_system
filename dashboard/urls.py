from django.urls import path
from django.http import HttpResponse

app_name = 'dashboard'

def temp_view(request, name):
    return HttpResponse(f"{name} dashboard placeholder — Module 6 pending")

urlpatterns = [
    path('admin/', lambda r: temp_view(r, 'Admin'), name='admin_dashboard'),
    path('counsellor/', lambda r: temp_view(r, 'Counsellor'), name='counsellor_dashboard'),
    path('store/', lambda r: temp_view(r, 'Store'), name='store_dashboard'),
]