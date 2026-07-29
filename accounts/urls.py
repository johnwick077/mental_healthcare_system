from django.urls import path
from .views import RoleBasedLoginView, logout_view, UserListView, UserCreateView, UserUpdateView

app_name = 'accounts'

urlpatterns = [
    path('login/', RoleBasedLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/add/', UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_edit'),
]