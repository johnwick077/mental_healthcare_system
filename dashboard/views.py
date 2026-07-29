from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.utils import timezone
from accounts.decorators import role_required
from patient.models import Patient
from observation.models import DailyObservation
from inventory.models import Inventory, ResourceRequest
from accounts.models import User


@method_decorator(role_required('ADMIN'), name='dispatch')
class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        context['total_patients'] = Patient.objects.filter(is_active=True).count()
        context['total_counsellors'] = User.objects.filter(role='COUNSELLOR').count()
        context['todays_observations'] = DailyObservation.objects.filter(date=today).count()
        context['pending_requests'] = ResourceRequest.objects.filter(status='PENDING').count()
        context['low_stock_items'] = Inventory.objects.filter(
            quantity_in_stock__lte=10  # simplified; refined below with is_low_stock loop
        )
        context['low_stock_count'] = sum(1 for inv in Inventory.objects.all() if inv.is_low_stock())

        # Chart data: last 7 days observation count trend
        from datetime import timedelta
        last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        trend_labels = [d.strftime('%b %d') for d in last_7_days]
        trend_counts = [
            DailyObservation.objects.filter(date=d).count() for d in last_7_days
        ]
        context['trend_labels'] = trend_labels
        context['trend_counts'] = trend_counts

        # Chart data: priority level distribution (today)
        priority_counts = {}
        for choice_val, choice_label in DailyObservation.PRIORITY_CHOICES:
            priority_counts[choice_label] = DailyObservation.objects.filter(
                date=today, priority_level=choice_val
            ).count()
        context['priority_labels'] = list(priority_counts.keys())
        context['priority_counts'] = list(priority_counts.values())

        return context


@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class CounsellorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/counsellor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()

        assigned_patients = Patient.objects.none()
        if hasattr(user, 'counsellor_profile'):
            assigned_patients = user.counsellor_profile.patients.filter(is_active=True)

        context['assigned_patients'] = assigned_patients
        context['assigned_patients_count'] = assigned_patients.count()
        context['todays_observations'] = DailyObservation.objects.filter(
            counsellor=user, date=today
        ).count()
        context['pending_observations'] = assigned_patients.count() - context['todays_observations']
        context['recent_observations'] = DailyObservation.objects.filter(
            counsellor=user
        ).select_related('patient')[:5]

        return context


@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class StoreDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/store_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        inventory_items = Inventory.objects.select_related('item').all()
        context['inventory_items'] = inventory_items
        context['low_stock_items'] = [inv for inv in inventory_items if inv.is_low_stock()]
        context['pending_requests_count'] = ResourceRequest.objects.filter(status='PENDING').count()
        context['issued_requests_count'] = ResourceRequest.objects.filter(status='ISSUED').count()

        # Chart data: stock levels per item
        context['stock_labels'] = [inv.item.name for inv in inventory_items]
        context['stock_values'] = [inv.quantity_in_stock for inv in inventory_items]

        return context