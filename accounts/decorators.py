from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Usage: @role_required('ADMIN', 'STORE_MANAGER')
    """
    def check(user):
        if user.is_authenticated and user.role in roles:
            return True
        raise PermissionDenied
    return user_passes_test(check)