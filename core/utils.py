import os
import uuid
import re
from django.utils import timezone
from datetime import timedelta


def uuid_path_gen(instance, filename):
    """Fayl nomini UUID ga o'zgartiradi (Xavfsizlik uchun)"""
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    folder = instance.__class__.__name__.lower()
    return os.path.join(folder, new_filename)


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


def log_activity(user, action, detail='', link='', request=None):
    from .models import ActivityLog
    ip = None
    ua = ""
    if request:
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')

    ActivityLog.objects.create(
        user=user, action=action, detail=detail, link=link,
        ip_address=ip, user_agent=ua[:500]
    )
    # XP va badge avtomatik
    process_action_xp(user, action)


# ── GAMIFICATION ──────────────────────────────────────────────────────────────

# Har bir harakat uchun XP miqdori
XP_REWARDS = {
    'login':         5,
    'register':      20,
    'profile_edit':  10,
    'skill_add':     5,
    'project_add':   15,
    'cert_add':      10,
    'contest_apply': 20,
    'msg_send':      3,
    'mentor_req':    10,
    'course_enroll': 10,
    'course_done':   50,
    'job_post':      15,
    'resource_add':  10,
}


def award_xp(user, amount, reason):
    """Foydalanuvchiga XP berish va score yangilash"""
    from .models import XPLog
    XPLog.objects.create(user=user, amount=amount, reason=reason)
    user.score = (user.score or 0) + amount
    user.save(update_fields=['score'])


def award_badge(user, badge_key):
    """Badge berish — agar allaqachon yo'q bo'lsa"""
    from .models import Badge, BADGE_DEFINITIONS, Notification
    if Badge.objects.filter(user=user, badge_key=badge_key).exists():
        return False
    Badge.objects.create(user=user, badge_key=badge_key)
    info = BADGE_DEFINITIONS.get(badge_key, {})
    # XP ham berish
    if info.get('xp'):
        award_xp(user, info['xp'], f"Badge: {info.get('name', badge_key)}")
    # Bildirishnoma
    Notification.objects.create(
        user=user, notif_type='score',
        text=f"{info.get('icon', '🎖️')} Yangi nishon: {info.get('name', badge_key)}! +{info.get('xp', 0)} XP",
        link='/profile/',
    )
    return True


def update_streak(user):
    """Login streak yangilash va badge tekshirish"""
    from .models import UserStreak
    streak, _ = UserStreak.objects.get_or_create(user=user)
    streak.update()
    # Streak badge lari
    if streak.current_streak >= 3:
        award_badge(user, 'streak_3')
    if streak.current_streak >= 7:
        award_badge(user, 'streak_7')
    if streak.current_streak >= 30:
        award_badge(user, 'streak_30')
    return streak


def check_badges(user):
    """Foydalanuvchi holatiga qarab badge larni tekshirish"""
    # Profil to'liqligi
    if user.bio and user.avatar and user.region:
        award_badge(user, 'profile_complete')
    # Loyihalar
    proj_count = user.projects.count()
    if proj_count >= 1:
        award_badge(user, 'first_project')
    if proj_count >= 5:
        award_badge(user, 'five_projects')
    # Ko'nikmalar
    if user.skills.count() >= 5:
        award_badge(user, 'five_skills')
    # Kurslar
    from .models import CourseEnrollment
    done = CourseEnrollment.objects.filter(user=user, completed=True).count()
    if done >= 1:
        award_badge(user, 'first_course')
    if done >= 3:
        award_badge(user, 'three_courses')
    # Tanlovlar
    if user.applications.exists():
        award_badge(user, 'first_contest')
    # Mentor so'rovi
    if user.sent_requests.exists():
        award_badge(user, 'first_mentor_req')
    # Xabarlar
    if user.sent_messages.exists():
        award_badge(user, 'first_message')


def process_action_xp(user, action):
    """Harakat uchun XP berish va badge tekshirish"""
    xp = XP_REWARDS.get(action, 0)
    if xp:
        award_xp(user, xp, action)
    check_badges(user)
