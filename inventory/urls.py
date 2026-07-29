from django.urls import path
from .views import (
    ResourceRequestCreateView, MyRequestsListView, PendingRequestsListView,
    ApproveRequestView, RejectRequestView, IssueRequestView, InventoryListView
)

app_name = 'inventory'

urlpatterns = [
    path('request/add/', ResourceRequestCreateView.as_view(), name='request_add'),
    path('request/my/', MyRequestsListView.as_view(), name='my_requests'),
    path('requests/pending/', PendingRequestsListView.as_view(), name='pending_requests'),
    path('requests/<int:pk>/approve/', ApproveRequestView.as_view(), name='approve_request'),
    path('requests/<int:pk>/reject/', RejectRequestView.as_view(), name='reject_request'),
    path('requests/<int:pk>/issue/', IssueRequestView.as_view(), name='issue_request'),
    path('stock/', InventoryListView.as_view(), name='inventory_list'),
]