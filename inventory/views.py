from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, View
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from accounts.decorators import role_required
from .models import ResourceRequest, RequestItem, Inventory, IssueHistory
from .forms import ResourceRequestForm, RequestItemFormSet, InventoryUpdateForm


# ---------- Counsellor side: create request ----------

@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class ResourceRequestCreateView(LoginRequiredMixin, CreateView):
    model = ResourceRequest
    form_class = ResourceRequestForm
    template_name = 'inventory/request_form.html'
    success_url = reverse_lazy('inventory:my_requests')

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            from accounts.signals import notify_store_managers
            notify_store_managers(
                'PENDING_REQUEST',
                f"New resource request from {self.request.user} for {self.object.patient.full_name}."
            )

            return redirect(self.success_url)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = RequestItemFormSet(self.request.POST)
        else:
            context['formset'] = RequestItemFormSet()
        return context


@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class MyRequestsListView(LoginRequiredMixin, ListView):
    model = ResourceRequest
    template_name = 'inventory/my_requests.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        qs = ResourceRequest.objects.filter(requested_by=self.request.user)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ResourceRequest.STATUS_CHOICES
        return context


@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class PendingRequestsListView(LoginRequiredMixin, ListView):
    model = ResourceRequest
    template_name = 'inventory/pending_requests.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        qs = ResourceRequest.objects.filter(status=ResourceRequest.STATUS_PENDING)
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(patient__full_name__icontains=search)
        return qs


@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class ApproveRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        req = get_object_or_404(ResourceRequest, pk=pk)
        req.status = ResourceRequest.STATUS_APPROVED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save()
        return redirect('inventory:pending_requests')


@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class RejectRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        req = get_object_or_404(ResourceRequest, pk=pk)
        req.status = ResourceRequest.STATUS_REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save()
        return redirect('inventory:pending_requests')


@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class IssueRequestView(LoginRequiredMixin, View):
    """
    Issues all items in an approved request, decrements stock,
    and logs each issue to IssueHistory.
    """
    def post(self, request, pk):
        req = get_object_or_404(ResourceRequest, pk=pk, status=ResourceRequest.STATUS_APPROVED)
        for line in req.items.all():
            inventory, _ = Inventory.objects.get_or_create(item=line.item)
            if inventory.quantity_in_stock >= line.quantity_requested:
                inventory.quantity_in_stock -= line.quantity_requested
                inventory.save()
                IssueHistory.objects.create(
                    request=req,
                    item=line.item,
                    quantity_issued=line.quantity_requested,
                    issued_by=request.user
                )
        req.status = ResourceRequest.STATUS_ISSUED
        req.save()
        return redirect('inventory:pending_requests')


# ---------- Inventory management ----------

@method_decorator(role_required('STORE_MANAGER', 'ADMIN'), name='dispatch')
class InventoryListView(LoginRequiredMixin, ListView):
    model = Inventory
    template_name = 'inventory/inventory_list.html'
    context_object_name = 'inventory_items'
    paginate_by = 10

    def get_queryset(self):
        qs = Inventory.objects.select_related('item').all()
        search = self.request.GET.get('search')
        low_only = self.request.GET.get('low_stock')
        if search:
            qs = qs.filter(item__name__icontains=search)
        if low_only:
            qs = [inv for inv in qs if inv.is_low_stock()]
        return qs