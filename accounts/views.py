from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .forms import LoginForm


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

# Create your views here.
