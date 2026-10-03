from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    View,
)

from accounts.decorators import role_required

from .models import (
    ResourceRequest,
    RequestItem,
    Inventory,
    IssueHistory,
)

from .forms import (
    ResourceRequestForm,
    RequestItemFormSet,
    InventoryUpdateForm,
)


# ============================================================
# COUNSELLOR - CREATE RESOURCE REQUEST
# ============================================================

@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class ResourceRequestCreateView(LoginRequiredMixin, CreateView):

    model = ResourceRequest
    form_class = ResourceRequestForm
    template_name = 'inventory/request_form.html'
    success_url = reverse_lazy('inventory:my_requests')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # Send logged-in user to the form
        # so only assigned patients are shown.
        kwargs['user'] = self.request.user

        return kwargs

    def form_valid(self, form):

        # Extra security validation:
        # counsellor can only request resources for assigned patients.
        patient = form.cleaned_data['patient']

        if (
            patient.assigned_counsellor is None
            or patient.assigned_counsellor.user != self.request.user
        ):
            messages.error(
                self.request,
                'You can only create resource requests for patients assigned to you.'
            )
            return redirect('inventory:request_add')

        form.instance.requested_by = self.request.user

        context = self.get_context_data()

        formset = context['formset']

        if formset.is_valid():

            self.object = form.save()

            formset.instance = self.object
            formset.save()

            # Notify store managers
            from accounts.signals import notify_store_managers

            notify_store_managers(
                'PENDING_REQUEST',
                f'New resource request from '
                f'{self.request.user.get_full_name() or self.request.user.username} '
                f'for {self.object.patient.full_name}.'
            )

            messages.success(
                self.request,
                f'Resource request #{self.object.id} created successfully.'
            )

            return redirect(self.success_url)

        return self.render_to_response(
            self.get_context_data(form=form)
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if self.request.POST:

            context['formset'] = RequestItemFormSet(
                self.request.POST
            )

        else:

            context['formset'] = RequestItemFormSet()

        return context


# ============================================================
# COUNSELLOR - MY REQUESTS
# ============================================================

@method_decorator(role_required('COUNSELLOR'), name='dispatch')
class MyRequestsListView(LoginRequiredMixin, ListView):

    model = ResourceRequest

    template_name = 'inventory/my_requests.html'

    context_object_name = 'requests'

    paginate_by = 10

    def get_queryset(self):

        qs = (
            ResourceRequest.objects
            .filter(
                requested_by=self.request.user
            )
            .select_related(
                'patient',
                'requested_by',
                'reviewed_by',
            )
            .prefetch_related(
                'items__item'
            )
        )

        status = self.request.GET.get('status')

        if status:
            qs = qs.filter(
                status=status
            )

        return qs

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['status_choices'] = (
            ResourceRequest.STATUS_CHOICES
        )

        return context


# ============================================================
# STORE MANAGER - PENDING REQUESTS
# ============================================================

@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class PendingRequestsListView(LoginRequiredMixin, ListView):

    model = ResourceRequest

    template_name = 'inventory/pending_requests.html'

    context_object_name = 'requests'

    paginate_by = 10

    def get_queryset(self):

        qs = (
            ResourceRequest.objects
            .filter(
                status=ResourceRequest.STATUS_PENDING
            )
            .select_related(
                'patient',
                'requested_by',
            )
            .prefetch_related(
                'items__item'
            )
        )

        search = self.request.GET.get('search')

        if search:
            qs = qs.filter(
                patient__full_name__icontains=search
            )

        return qs


# ============================================================
# STORE MANAGER - APPROVE REQUEST
# ============================================================

@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class ApproveRequestView(LoginRequiredMixin, View):

    def post(self, request, pk):

        req = get_object_or_404(
            ResourceRequest,
            pk=pk,
            status=ResourceRequest.STATUS_PENDING
        )

        req.status = ResourceRequest.STATUS_APPROVED

        req.reviewed_by = request.user

        req.reviewed_at = timezone.now()

        req.save(
            update_fields=[
                'status',
                'reviewed_by',
                'reviewed_at',
            ]
        )

        messages.success(
            request,
            f'Request #{req.id} approved successfully.'
        )

        return redirect(
            'inventory:pending_requests'
        )


# ============================================================
# STORE MANAGER - REJECT REQUEST
# ============================================================

@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class RejectRequestView(LoginRequiredMixin, View):

    def post(self, request, pk):

        req = get_object_or_404(
            ResourceRequest,
            pk=pk,
            status=ResourceRequest.STATUS_PENDING
        )

        req.status = ResourceRequest.STATUS_REJECTED

        req.reviewed_by = request.user

        req.reviewed_at = timezone.now()

        req.save(
            update_fields=[
                'status',
                'reviewed_by',
                'reviewed_at',
            ]
        )

        messages.success(
            request,
            f'Request #{req.id} rejected.'
        )

        return redirect(
            'inventory:pending_requests'
        )


# ============================================================
# STORE MANAGER - APPROVED REQUESTS
# ============================================================

@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class ApprovedRequestsListView(LoginRequiredMixin, ListView):

    model = ResourceRequest

    template_name = 'inventory/approved_requests.html'

    context_object_name = 'requests'

    paginate_by = 10

    def get_queryset(self):

        qs = (
            ResourceRequest.objects
            .filter(
                status=ResourceRequest.STATUS_APPROVED
            )
            .select_related(
                'patient',
                'requested_by',
                'reviewed_by',
            )
            .prefetch_related(
                'items__item'
            )
        )

        search = self.request.GET.get('search')

        if search:
            qs = qs.filter(
                patient__full_name__icontains=search
            )

        return qs


# ============================================================
# STORE MANAGER - ISSUE REQUEST
# ============================================================

@method_decorator(role_required('STORE_MANAGER'), name='dispatch')
class IssueRequestView(LoginRequiredMixin, View):

    @transaction.atomic
    def post(self, request, pk):

        req = get_object_or_404(
            ResourceRequest.objects.select_for_update(),
            pk=pk,
            status=ResourceRequest.STATUS_APPROVED
        )

        request_items = list(
            req.items.select_related('item')
        )

        # Prevent issuing an empty request
        if not request_items:

            messages.error(
                request,
                f'Request #{req.id} contains no items.'
            )

            return redirect(
                'inventory:approved_requests'
            )

        inventory_records = []

        # ----------------------------------------------------
        # FIRST: VALIDATE ALL ITEMS
        # ----------------------------------------------------

        for line in request_items:

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(
                    item=line.item
                )
                .first()
            )

            if inventory is None:

                messages.error(
                    request,
                    f'No inventory record exists for '
                    f'{line.item.name}.'
                )

                return redirect(
                    'inventory:approved_requests'
                )

            if (
                inventory.quantity_in_stock
                < line.quantity_requested
            ):

                messages.error(
                    request,
                    f'Insufficient stock for '
                    f'{line.item.name}. '
                    f'Required: {line.quantity_requested}, '
                    f'Available: {inventory.quantity_in_stock}.'
                )

                return redirect(
                    'inventory:approved_requests'
                )

            inventory_records.append(
                (line, inventory)
            )

        # ----------------------------------------------------
        # SECOND: DEDUCT STOCK
        # ----------------------------------------------------

        for line, inventory in inventory_records:

            inventory.quantity_in_stock -= (
                line.quantity_requested
            )

            inventory.save(
                update_fields=[
                    'quantity_in_stock',
                    'last_updated',
                ]
            )

            # Create issue history
            IssueHistory.objects.create(
                request=req,
                item=line.item,
                quantity_issued=line.quantity_requested,
                issued_by=request.user,
            )

        # ----------------------------------------------------
        # THIRD: MARK REQUEST AS ISSUED
        # ----------------------------------------------------

        req.status = ResourceRequest.STATUS_ISSUED

        req.save(
            update_fields=[
                'status'
            ]
        )

        messages.success(
            request,
            f'Request #{req.id} issued successfully.'
        )

        return redirect(
            'inventory:approved_requests'
        )


# ============================================================
# INVENTORY LIST
# ============================================================

@method_decorator(
    role_required('STORE_MANAGER', 'ADMIN'),
    name='dispatch'
)
class InventoryListView(LoginRequiredMixin, ListView):

    model = Inventory

    template_name = 'inventory/inventory_list.html'

    context_object_name = 'inventory_items'

    paginate_by = 10

    def get_queryset(self):

        qs = (
            Inventory.objects
            .select_related('item')
            .all()
            .order_by('item__name')
        )

        search = self.request.GET.get('search')

        low_only = self.request.GET.get('low_stock')

        # Search
        if search:

            qs = qs.filter(
                item__name__icontains=search
            )

        # Low stock filter
        if low_only:

            qs = qs.filter(
                quantity_in_stock__lte=F(
                    'item__low_stock_threshold'
                )
            )

        return qs


# ============================================================
# INVENTORY UPDATE
# ============================================================

@method_decorator(
    role_required('STORE_MANAGER', 'ADMIN'),
    name='dispatch'
)
class InventoryUpdateView(
    LoginRequiredMixin,
    UpdateView
):

    model = Inventory

    form_class = InventoryUpdateForm

    template_name = 'inventory/inventory_update.html'

    success_url = reverse_lazy(
        'inventory:inventory_list'
    )

    def form_valid(self, form):

        messages.success(
            self.request,
            f'{form.instance.item.name} stock updated successfully.'
        )

        return super().form_valid(form)