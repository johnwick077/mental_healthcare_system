from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .forms import LoginForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.utils.decorators import method_decorator
from .decorators import role_required
from .models import User
from .forms import AdminUserCreateForm, AdminUserEditForm
from .models import Notification


@method_decorator(role_required('ADMIN'), name='dispatch')
class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.all().order_by('username')
        role = self.request.GET.get('role')
        search = self.request.GET.get('search')
        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(username__icontains=search)
        return qs


@method_decorator(role_required('ADMIN'), name='dispatch')
class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = AdminUserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')


@method_decorator(role_required('ADMIN'), name='dispatch')
class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = AdminUserEditForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

class RoleBasedLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        user = self.request.user
        if user.is_admin():
            return reverse_lazy('dashboard:admin_dashboard')
        elif user.is_counsellor():
            return reverse_lazy('dashboard:counsellor_dashboard')
        elif user.is_store_manager():
            return reverse_lazy('dashboard:store_dashboard')
        return reverse_lazy('accounts:login')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'accounts/notifications.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


def mark_notification_read(request, pk):
    notif = Notification.objects.filter(pk=pk, recipient=request.user).first()
    if notif:
        notif.is_read = True
        notif.save()
    return redirect('accounts:notifications')