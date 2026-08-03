from django.db import models
from django.conf import settings
from patient.models import Patient
from django.db.models.signals import post_save
from django.dispatch import receiver

class ResourceItem(models.Model):
    """
    Master list of personal care items (Soap, Shampoo, Blanket, etc.)
    """
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20, default='pcs')  # e.g. pcs, kg, litres
    low_stock_threshold = models.PositiveIntegerField(default=10)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    """
    Current stock level for each resource item.
    """
    item = models.OneToOneField(ResourceItem, on_delete=models.CASCADE, related_name='inventory')
    quantity_in_stock = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def is_low_stock(self):
        return self.quantity_in_stock <= self.item.low_stock_threshold

    def __str__(self):
        return f"{self.item.name}: {self.quantity_in_stock} {self.item.unit}"


class ResourceRequest(models.Model):
    """
    A request raised by a counsellor for personal care items for a patient.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_ISSUED = 'ISSUED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_ISSUED, 'Issued'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='resource_requests')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='requests_made'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    remarks = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='requests_reviewed'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request #{self.id} - {self.patient.full_name} ({self.status})"

    class Meta:
        ordering = ['-requested_at']


class RequestItem(models.Model):
    """
    Individual line items within a ResourceRequest.
    """
    request = models.ForeignKey(ResourceRequest, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(ResourceItem, on_delete=models.CASCADE)
    quantity_requested = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity_requested} x {self.item.name}"


class IssueHistory(models.Model):
    """
    Log of items actually issued once a request is approved and fulfilled.
    Keeps a permanent audit trail even if stock later changes.
    """
    request = models.ForeignKey(ResourceRequest, on_delete=models.CASCADE, related_name='issue_logs')
    item = models.ForeignKey(ResourceItem, on_delete=models.CASCADE)
    quantity_issued = models.PositiveIntegerField()
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity_issued} x {self.item.name} -> {self.request.patient.full_name}"

@receiver(post_save, sender=Inventory)
def check_low_stock(sender, instance, **kwargs):
    if instance.is_low_stock():
        from accounts.signals import notify_store_managers
        notify_store_managers(
            'LOW_STOCK',
            f"{instance.item.name} is low on stock ({instance.quantity_in_stock} {instance.item.unit} left)."
        )