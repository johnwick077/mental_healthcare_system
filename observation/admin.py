from django.contrib import admin
from .models import DailyObservation


@admin.register(DailyObservation)
class DailyObservationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'date', 'time', 'counsellor', 'poi_score', 'priority_level']
    list_filter = ['priority_level', 'date']
    search_fields = ['patient__full_name']
    readonly_fields = ['poi_score', 'priority_level']