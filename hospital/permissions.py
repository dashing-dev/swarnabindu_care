from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

ROLE_ADMIN = 'Administrator'
ROLE_OPERATOR = 'Vaccination Operator'
ROLE_READONLY = 'Report / Read-only User'

def get_user_role(user):
    if user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists():
        return ROLE_ADMIN
    elif user.groups.filter(name=ROLE_OPERATOR).exists():
        return ROLE_OPERATOR
    elif user.groups.filter(name=ROLE_READONLY).exists():
        return ROLE_READONLY
    return ROLE_OPERATOR # Default fallback for normal staff

def require_role(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")
            role = get_user_role(request.user)
            if role == ROLE_ADMIN or role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this healthcare function.")
        return _wrapped_view
    return decorator
