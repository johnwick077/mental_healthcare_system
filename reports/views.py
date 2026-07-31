from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta
from accounts.decorators import role_required
from patient.models import Patient
from observation.models import DailyObservation
from inventory.models import Inventory, ResourceRequest, IssueHistory
from .utils import build_pdf_response


@method_decorator(role_required('ADMIN', 'COUNSELLOR'), name='dispatch')
class DailyObservationReportView(LoginRequiredMixin, View):
    def get(self, request):
        date = request.GET.get('date') or timezone.now().date().isoformat()
        observations = DailyObservation.objects.filter(date=date).select_related('patient', 'counsellor')

        table_data = [['Patient', 'Time', 'Mood', 'POI Score', 'Priority', 'Counsellor']]
        for obs in observations:
            table_data.append([
                obs.patient.full_name, str(obs.time), obs.get_mood_display(),
                str(obs.poi_score), obs.get_priority_level_display(),
                str(obs.counsellor) if obs.counsellor else '-'
            ])

        buffer = build_pdf_response(
            'daily_observation_report.pdf',
            f'Daily Observation Report — {date}',
            table_data,
            extra_note='Note: This report is for observation tracking only and does not represent a clinical diagnosis.'
        )
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="daily_observation_report_{date}.pdf"'
        return response


@method_decorator(role_required('ADMIN', 'COUNSELLOR'), name='dispatch')
class WeeklyObservationReportView(LoginRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        start_date = today - timedelta(days=6)
        observations = DailyObservation.objects.filter(
            date__range=[start_date, today]
        ).select_related('patient')

        table_data = [['Date', 'Patient', 'Mood', 'POI Score', 'Priority']]
        for obs in observations:
            table_data.append([
                str(obs.date), obs.patient.full_name, obs.get_mood_display(),
                str(obs.poi_score), obs.get_priority_level_display()
            ])

        buffer = build_pdf_response(
            'weekly_report.pdf',
            f'Weekly Observation Report ({start_date} to {today})',
            table_data
        )
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="weekly_observation_report.pdf"'
        return response


@method_decorator(role_required('ADMIN', 'COUNSELLOR'), name='dispatch')
class MonthlyObservationReportView(LoginRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        start_date = today.replace(day=1)
        observations = DailyObservation.objects.filter(
            date__range=[start_date, today]
        ).select_related('patient')

        table_data = [['Date', 'Patient', 'Mood', 'POI Score', 'Priority']]
        for obs in observations:
            table_data.append([
                str(obs.date), obs.patient.full_name, obs.get_mood_display(),
                str(obs.poi_score), obs.get_priority_level_display()
            ])

        buffer = build_pdf_response(
            'monthly_report.pdf',
            f'Monthly Observation Report ({start_date.strftime("%B %Y")})',
            table_data
        )
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="monthly_observation_report.pdf"'
        return response


@method_decorator(role_required('ADMIN', 'COUNSELLOR'), name='dispatch')
class PatientProgressReportView(LoginRequiredMixin, View):
    def get(self, request, patient_id):
        patient = Patient.objects.get(pk=patient_id)
        observations = DailyObservation.objects.filter(patient=patient).order_by('date')

        table_data = [['Date', 'Time', 'Mood', 'Sleep', 'Appetite', 'Hygiene', 'POI', 'Priority']]
        for obs in observations:
            table_data.append([
                str(obs.date), str(obs.time), obs.get_mood_display(),
                obs.get_sleep_quality_display(), obs.get_appetite_display(),
                obs.get_personal_hygiene_display(), str(obs.poi_score),
                obs.get_priority_level_display()
            ])

        buffer = build_pdf_response(
            'patient_progress_report.pdf',
            f'Patient Progress Report — {patient.full_name}',
            table_data,
            extra_note='This report tracks observed behavioural patterns only and is not a diagnostic document.'
        )
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="progress_report_{patient.full_name}.pdf"'
        return response


@method_decorator(role_required('ADMIN', 'STORE_MANAGER'), name='dispatch')
class InventoryReportView(LoginRequiredMixin, View):
    def get(self, request):
        items = Inventory.objects.select_related('item').all()

        table_data = [['Item', 'Stock', 'Unit', 'Low Stock Threshold', 'Status']]
        for inv in items:
            table_data.append([
                inv.item.name, str(inv.quantity_in_stock), inv.item.unit,
                str(inv.item.low_stock_threshold),
                'LOW STOCK' if inv.is_low_stock() else 'OK'
            ])

        buffer = build_pdf_response('inventory_report.pdf', 'Inventory Report', table_data)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.pdf"'
        return response


@method_decorator(role_required('ADMIN', 'STORE_MANAGER'), name='dispatch')
class ResourceUsageReportView(LoginRequiredMixin, View):
    def get(self, request):
        logs = IssueHistory.objects.select_related('item', 'request__patient', 'issued_by').order_by('-issued_at')

        table_data = [['Date', 'Item', 'Qty Issued', 'Patient', 'Issued By']]
        for log in logs:
            table_data.append([
                log.issued_at.strftime('%Y-%m-%d'), log.item.name, str(log.quantity_issued),
                log.request.patient.full_name, str(log.issued_by) if log.issued_by else '-'
            ])

        buffer = build_pdf_response('resource_usage_report.pdf', 'Resource Usage Report', table_data)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="resource_usage_report.pdf"'
        return response