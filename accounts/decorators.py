from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator for views that checks if the logged-in user belongs to allowed roles.
    Usage: @role_required(['ADMIN', 'TEACHER']) or @role_required('STUDENT')
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "Access Denied: You do not have permission to access that area.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required(['ADMIN'])(view_func)


def teacher_required(view_func):
    return role_required(['TEACHER', 'ADMIN'])(view_func)


def student_required(view_func):
    return role_required(['STUDENT'])(view_func)
