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
        from django.utils.crypto import get_random_string
        nonce = get_random_string(32)
        request.csp_nonce = nonce

        response = self.get_response(request)
        response['X-Content-Type-Options']    = 'nosniff'
        response['X-Frame-Options']           = 'DENY'
        response['X-XSS-Protection']          = '1; mode=block'
        response['Referrer-Policy']           = 'strict-origin-when-cross-origin'
        response['Permissions-Policy']        = 'geolocation=(), microphone=(), camera=()'
        
        csp = (
            "default-src 'none'; "
            f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic' 'unsafe-eval' https: http:; "
            f"style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self';"
        )
        response['Content-Security-Policy']   = csp
        return response


class RateLimitMiddleware:
    """DDoS va Brute-force himoyasi: IP bo'yicha cheklash va bloklash"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() \
             or request.META.get('REMOTE_ADDR', '')
        
        # 1. Avval bloklanganligini tekshirish
        block_key = f'blocked_ip:{ip}'
        if cache.get(block_key):
            logger.warning(f"BLOCKED ACCESS ATTEMPT: {ip} - {request.path}")
            return HttpResponseForbidden(
                "Sizning IP manzilingiz shubhali harakatlar tufayli 10 daqiqaga bloklangan.",
                content_type='text/plain; charset=utf-8'
            )

        # 2. So'rovlar sonini hisoblash
        # Muhim yo'llar (login, panel) uchun qat'iyroq limit
        sensitive_paths = ['/login/', '/2fa/', '/panel/', '/tizim/']
        is_sensitive = any(request.path.startswith(p) for p in sensitive_paths)
        
        limit = 30 if is_sensitive else 100 # 1 daqiqaga limitlar
        rate_key = f'ratelimit:{ip}:{"sensitive" if is_sensitive else "global"}'
        
        count = cache.get(rate_key, 0)
        
        if count >= limit:
            # Limitdan oshsa: 10 daqiqaga bloklash
            cache.set(block_key, True, 600) 
            logger.error(f"DDoS/BruteForce Detected! Blocked: {ip} - Path: {request.path}")
            return HttpResponseForbidden(
                "Juda ko'p so'rov! Xavfsizlik maqsadida bloklandingiz.",
                content_type='text/plain; charset=utf-8'
            )
        
        cache.set(rate_key, count + 1, 60)
        
        return self.get_response(request)
