import re
from django.utils import timezone
from datetime import timedelta


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def parse_user_agent(ua_string):
    """User-Agent dan qurilma, OS, brauzer aniqlaymiz"""
    ua = ua_string.lower()

    # Qurilma
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        device = 'Mobil'
    elif 'tablet' in ua or 'ipad' in ua:
        device = 'Planshet'
    else:
        device = 'Kompyuter'

    # OS
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    elif 'mac' in ua:
        os_name = 'macOS'
    elif 'linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'Noma\'lum'

    # Brauzer
    if 'chrome' in ua and 'edg' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    elif 'edg' in ua:
        browser = 'Edge'
    elif 'opera' in ua or 'opr' in ua:
        browser = 'Opera'
    else:
        browser = 'Noma\'lum'

    return device, os_name, browser


def record_login(request, user, success=True):
    from .models import LoginHistory
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')
    device, os_name, browser = parse_user_agent(ua)

    LoginHistory.objects.create(
        user       = user,
        ip_address = ip,
        user_agent = ua[:500],
        device     = device,
        os         = os_name,
        browser    = browser,
        is_success = success,
    )


def check_brute_force(phone, ip):
    """5 marta xato kirishda 15 daqiqa bloklash"""
    from .models import FailedLoginAttempt
    obj, _ = FailedLoginAttempt.objects.get_or_create(phone=phone, ip_address=ip)

    if obj.is_blocked():
        remaining = int((obj.blocked_until - timezone.now()).total_seconds() / 60)
        return False, f"Kirish {remaining} daqiqaga bloklangan."

    return True, None


def record_failed_attempt(phone, ip):
    from .models import FailedLoginAttempt
    obj, _ = FailedLoginAttempt.objects.get_or_create(phone=phone, ip_address=ip)

    if not obj.is_blocked():
        obj.attempts += 1
        if obj.attempts >= 5:
            obj.blocked_until = timezone.now() + timedelta(minutes=15)
        obj.save()


def reset_failed_attempts(phone, ip):
    from .models import FailedLoginAttempt
    FailedLoginAttempt.objects.filter(phone=phone, ip_address=ip).delete()


def log_activity(user, action, detail='', link=''):
    from .models import ActivityLog
    ActivityLog.objects.create(user=user, action=action, detail=detail, link=link)
