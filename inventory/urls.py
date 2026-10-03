from django.urls import path

from .views import (
    ResourceRequestCreateView,
    MyRequestsListView,
    PendingRequestsListView,
    ApprovedRequestsListView,
    ApproveRequestView,
    RejectRequestView,
    IssueRequestView,
    InventoryListView,
    InventoryUpdateView,
)


app_name = 'inventory'


urlpatterns = [

    # --------------------------------------------------------
    # COUNSELLOR
    # --------------------------------------------------------

    path(
        'request/add/',
        ResourceRequestCreateView.as_view(),
        name='request_add'
    ),

    path(
        'request/my/',
        MyRequestsListView.as_view(),
        name='my_requests'
    ),


    # --------------------------------------------------------
    # STORE MANAGER - REQUESTS
    # --------------------------------------------------------

    path(
        'requests/pending/',
        PendingRequestsListView.as_view(),
        name='pending_requests'
    ),

    path(
        'requests/approved/',
        ApprovedRequestsListView.as_view(),
        name='approved_requests'
    ),

    path(
        'requests/<int:pk>/approve/',
        ApproveRequestView.as_view(),
        name='approve_request'
    ),

    path(
        'requests/<int:pk>/reject/',
        RejectRequestView.as_view(),
        name='reject_request'
    ),

    path(
        'requests/<int:pk>/issue/',
        IssueRequestView.as_view(),
        name='issue_request'
    ),


    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    path(
        'stock/',
        InventoryListView.as_view(),
        name='inventory_list'
    ),

    path(
        'stock/<int:pk>/edit/',
        InventoryUpdateView.as_view(),
        name='inventory_update'
    ),
]