from django.contrib import admin
from .models import ResourceItem, Inventory, ResourceRequest, RequestItem, IssueHistory


@admin.register(ResourceItem)
class ResourceItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'low_stock_threshold']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity_in_stock', 'last_updated']
    list_filter = ['item']


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 1


@admin.register(ResourceRequest)
class ResourceRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'requested_by', 'status', 'requested_at']
    list_filter = ['status']
    inlines = [RequestItemInline]


@admin.register(IssueHistory)
class IssueHistoryAdmin(admin.ModelAdmin):
    list_display = ['request', 'item', 'quantity_issued', 'issued_by', 'issued_at']