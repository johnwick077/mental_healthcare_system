from django.contrib import admin
from .models import Ward, Counsellor, Patient


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity']
    search_fields = ['name']


@admin.register(Counsellor)
class CounsellorAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'specialization', 'date_joined']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'age', 'gender', 'ward', 'assigned_counsellor', 'is_active']
    list_filter = ['ward', 'is_active', 'gender']
    search_fields = ['full_name', 'guardian_name']