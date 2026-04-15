import os
import sys
import platform
import time
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.conf import settings


def superuser_required(view_func):
    """Faqat superuser kirishi mumkin"""
    from functools import wraps
    from django.contrib.auth import REDIRECT_FIELD_NAME
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('/login/?next=' + request.path)
        return view_func(request, *args, **kwargs)
    return wrapper


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@superuser_required
def sys_dashboard(request):
    # DB ulanish tekshirish
    db_ok = True
    db_ms = 0
    try:
        t0 = time.time()
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        db_ms = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        db_ok = False

    # DB jadvallar soni
    table_count = 0
    db_size = '—'
    try:
        with connection.cursor() as cur:
            if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
                table_count = cur.fetchone()[0]
                cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size = cur.fetchone()[0]
            else:
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cur.fetchone()[0]
    except:
        pass

    # Python va Django versiyalari
    import django
    py_version  = sys.version.split()[0]
    dj_version  = django.__version__
    os_info     = platform.platform()

    # Installed apps
    apps = settings.INSTALLED_APPS

    # Static va media
    static_root = str(settings.STATIC_ROOT)
    media_root  = str(settings.MEDIA_ROOT)
    static_exists = os.path.exists(static_root)
    media_exists  = os.path.exists(media_root)

    # Model statistikasi
    from .models import (User, Skill, Project, Contest, Course, Lesson,
                         CourseEnrollment, CourseCertificate, Message,
                         Notification, ActivityLog, LoginHistory,
                         MentorRequest, ContestApplication, Job, Resource)
    model_stats = [
        ('User',              User.objects.count()),
        ('Skill',             Skill.objects.count()),
        ('Project',           Project.objects.count()),
        ('Contest',           Contest.objects.count()),
        ('ContestApplication',ContestApplication.objects.count()),
        ('Course',            Course.objects.count()),
        ('Lesson',            Lesson.objects.count()),
        ('CourseEnrollment',  CourseEnrollment.objects.count()),
        ('CourseCertificate', CourseCertificate.objects.count()),
        ('Message',           Message.objects.count()),
        ('Notification',      Notification.objects.count()),
        ('ActivityLog',       ActivityLog.objects.count()),
        ('LoginHistory',      LoginHistory.objects.count()),
        ('MentorRequest',     MentorRequest.objects.count()),
        ('Job',               Job.objects.count()),
        ('Resource',          Resource.objects.count()),
    ]

    ctx = {
        'db_ok': db_ok, 'db_ms': db_ms,
        'db_size': db_size, 'table_count': table_count,
        'py_version': py_version, 'dj_version': dj_version,
        'os_info': os_info, 'apps': apps,
        'static_root': static_root, 'static_exists': static_exists,
        'media_root': media_root, 'media_exists': media_exists,
        'debug': settings.DEBUG,
        'model_stats': model_stats,
        'base_dir': str(settings.BASE_DIR),
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'db_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'db_name': settings.DATABASES['default'].get('NAME', ''),
    }
    return render(request, 'tizim/dashboard.html', ctx)


# ── SQL KONSOL ────────────────────────────────────────────────────────────────
@superuser_required
def sys_sql(request):
    result = None
    error  = None
    query  = ''
    cols   = []

    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if query:
            # Xavfli operatsiyalarni bloklash
            forbidden = ['drop ', 'truncate ', 'delete from auth_', 'delete from core_user']
            if any(f in query.lower() for f in forbidden):
                error = "Bu operatsiya taqiqlangan."
            else:
                try:
                    with connection.cursor() as cur:
                        t0 = time.time()
                        cur.execute(query)
                        ms = round((time.time() - t0) * 1000, 2)
                        if cur.description:
                            cols   = [d[0] for d in cur.description]
                            result = cur.fetchall()
                        else:
                            result = [(f"OK — {cur.rowcount} qator ta'sirlandi ({ms}ms)",)]
                            cols   = ['Natija']
                except Exception as e:
                    error = str(e)

    return render(request, 'tizim/sql.html', {
        'query': query, 'result': result, 'cols': cols, 'error': error,
    })


# ── LOGLAR ────────────────────────────────────────────────────────────────────
@superuser_required
def sys_logs(request):
    from .models import ActivityLog, LoginHistory
    log_type = request.GET.get('type', 'activity')
    limit    = int(request.GET.get('limit', 100))

    if log_type == 'login':
        logs = LoginHistory.objects.select_related('user').order_by('-created_at')[:limit]
        headers = ['Foydalanuvchi', 'IP', 'Qurilma', 'OS', 'Brauzer', 'Holat', 'Vaqt']
        rows = [(
            str(l.user), l.ip_address, l.device, l.os, l.browser,
            '✓' if l.is_success else '✗', l.created_at.strftime('%d.%m.%Y %H:%M:%S')
        ) for l in logs]
    else:
        logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:limit]
        headers = ['Foydalanuvchi', 'Amal', 'Tafsilot', 'Vaqt']
        rows = [(
            str(l.user), l.action, l.detail, l.created_at.strftime('%d.%m.%Y %H:%M:%S')
        ) for l in logs]

    return render(request, 'tizim/logs.html', {
        'headers': headers, 'rows': rows,
        'log_type': log_type, 'limit': limit,
    })


# ── MIGRATSIYALAR ─────────────────────────────────────────────────────────────
@superuser_required
def sys_migrations(request):
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(connection)
    applied = set(loader.applied_migrations)
    all_migrations = []
    for (app, name), migration in loader.disk_migrations.items():
        all_migrations.append({
            'app': app, 'name': name,
            'applied': (app, name) in applied,
        })
    all_migrations.sort(key=lambda x: (x['app'], x['name']))

    return render(request, 'tizim/migrations.html', {
        'migrations': all_migrations,
        'applied_count': len(applied),
        'total_count': len(all_migrations),
    })


# ── TIZIM API (real-time) ─────────────────────────────────────────────────────
@superuser_required
def sys_api(request):
    db_ok = True
    db_ms = 0
    try:
        t0 = time.time()
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        db_ms = round((time.time() - t0) * 1000, 2)
    except:
        db_ok = False

    from .models import ActivityLog, LoginHistory
    today = timezone.now().date()

    return JsonResponse({
        'db_ok':        db_ok,
        'db_ms':        db_ms,
        'debug':        settings.DEBUG,
        'today_errors': LoginHistory.objects.filter(
                            created_at__date=today, is_success=False).count(),
        'today_logins': LoginHistory.objects.filter(
                            created_at__date=today, is_success=True).count(),
        'last_activity': ActivityLog.objects.order_by('-created_at').values(
                            'action', 'detail', 'created_at').first(),
    }, json_dumps_params={'default': str})


# ── CACHE TOZALASH ────────────────────────────────────────────────────────────
@superuser_required
def sys_clear_cache(request):
    if request.method == 'POST':
        from django.core.cache import cache
        cache.clear()
        return JsonResponse({'ok': True, 'msg': 'Cache tozalandi.'})
    return JsonResponse({'ok': False})


# ── DEPLOY TRIGGER ────────────────────────────────────────────────────────────
@superuser_required
def sys_restart(request):
    if request.method == 'POST':
        try:
            restart_file = os.path.join(settings.BASE_DIR, 'tmp', 'restart.txt')
            os.makedirs(os.path.dirname(restart_file), exist_ok=True)
            with open(restart_file, 'w') as f:
                f.write(str(timezone.now()))
            return JsonResponse({'ok': True, 'msg': 'Server qayta ishga tushirilmoqda...'})
        except Exception as e:
            return JsonResponse({'ok': False, 'msg': str(e)})
    return JsonResponse({'ok': False})
