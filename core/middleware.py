import traceback
from django.utils import timezone


class ErrorLogMiddleware:
    """500 xatolarni DB ga saqlaydi"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        try:
            from .models import SystemError
            ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
                 or request.META.get('REMOTE_ADDR')
            user = request.user if request.user.is_authenticated else None
            SystemError.objects.create(
                path       = request.path[:300],
                method     = request.method,
                error_type = type(exception).__name__,
                message    = str(exception)[:1000],
                traceback  = traceback.format_exc()[:5000],
                user       = user,
                ip_address = ip or None,
            )
        except Exception:
            pass
        return None
