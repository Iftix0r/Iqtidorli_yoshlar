import traceback
import time
import logging
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache

logger = logging.getLogger('django.security')


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


class SecurityHeadersMiddleware:
    """Xavfsizlik headerlarini qo'shadi"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options']    = 'nosniff'
        response['X-Frame-Options']           = 'DENY'
        response['X-XSS-Protection']          = '1; mode=block'
        response['Referrer-Policy']           = 'strict-origin-when-cross-origin'
        response['Permissions-Policy']        = 'geolocation=(), microphone=(), camera=()'
        response['Content-Security-Policy']   = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self';"
        )
        return response


class RateLimitMiddleware:
    """IP bo'yicha so'rovlarni cheklash"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Faqat login va API endpointlarni cheklash
        sensitive_paths = ['/login/', '/2fa/', '/panel/', '/tizim/']
        if any(request.path.startswith(p) for p in sensitive_paths):
            ip  = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
                  or request.META.get('REMOTE_ADDR', '')
            key = f'ratelimit:{ip}:{request.path.split("/")[1]}'
            count = cache.get(key, 0)
            if count >= 60:  # 1 daqiqada 60 ta so'rov
                logger.warning(f"Rate limit: {ip} — {request.path}")
                return HttpResponseForbidden(
                    "Juda ko'p so'rov. Iltimos, bir daqiqa kuting.",
                    content_type='text/plain; charset=utf-8'
                )
            cache.set(key, count + 1, 60)
        return self.get_response(request)
