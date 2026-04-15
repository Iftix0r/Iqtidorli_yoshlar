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
    """Faqat superuser kirishi mumkin + 2FA (agar yoqilgan bo'lsa)"""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('/login/?next=' + request.path)
        from django.conf import settings
        if getattr(settings, 'TFA_ENABLED', False):
            if not request.session.get('tfa_verified'):
                request.session['tfa_next'] = request.path
                return redirect('tfa_send')
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


# ── XATOLAR MONITORING ────────────────────────────────────────────────────────
@superuser_required
def sys_errors(request):
    from .models import SystemError
    errors = SystemError.objects.order_by('-created_at')[:200]
    if request.method == 'POST' and request.POST.get('action') == 'clear':
        SystemError.objects.all().delete()
        return redirect('sys_errors')
    return render(request, 'tizim/errors.html', {'errors': errors})


# ── PAKETLAR ──────────────────────────────────────────────────────────────────
@superuser_required
def sys_packages(request):
    import subprocess
    result = []
    try:
        out = subprocess.check_output(
            ['pip', 'list', '--format=columns'],
            stderr=subprocess.DEVNULL
        ).decode()
        lines = out.strip().split('\n')[2:]  # header ni o'tkazib yuborish
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                result.append({'name': parts[0], 'version': parts[1]})
    except Exception as e:
        result = [{'name': 'Xato', 'version': str(e)}]
    return render(request, 'tizim/packages.html', {'packages': result})


# ── MUHIT O'ZGARUVCHILARI ─────────────────────────────────────────────────────
@superuser_required
def sys_env(request):
    sensitive = {'password', 'secret', 'key', 'token', 'pass', 'pwd'}
    env_vars = []
    for k, v in sorted(os.environ.items()):
        is_sensitive = any(s in k.lower() for s in sensitive)
        env_vars.append({
            'key': k,
            'value': '***' if is_sensitive else v,
            'sensitive': is_sensitive,
        })
    # .env fayl
    env_file = []
    env_path = os.path.join(settings.BASE_DIR, '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    is_sensitive = any(s in k.lower() for s in sensitive)
                    env_file.append({
                        'key': k.strip(),
                        'value': '***' if is_sensitive else v.strip(),
                        'sensitive': is_sensitive,
                    })
    return render(request, 'tizim/env.html', {
        'env_vars': env_vars, 'env_file': env_file,
    })


# ── FAYLLAR MENEJERI ──────────────────────────────────────────────────────────
@superuser_required
def sys_files(request):
    base = request.GET.get('path', '')
    root = settings.BASE_DIR

    # Path traversal himoyasi
    target = os.path.normpath(os.path.join(root, base))
    if not target.startswith(str(root)):
        target = str(root)
        base = ''

    items = []
    if os.path.isdir(target):
        try:
            for name in sorted(os.listdir(target)):
                full = os.path.join(target, name)
                rel  = os.path.relpath(full, root)
                stat = os.stat(full)
                items.append({
                    'name':     name,
                    'path':     rel,
                    'is_dir':   os.path.isdir(full),
                    'size':     stat.st_size,
                    'modified': timezone.datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M'),
                })
        except PermissionError:
            pass

    # Parent path
    parent = str(os.path.relpath(os.path.dirname(target), root)) if base else None
    if parent == '.':
        parent = ''

    return render(request, 'tizim/files.html', {
        'items': items, 'current': base or '/', 'parent': parent,
    })


# ── HEALTH CHECK ─────────────────────────────────────────────────────────────
@superuser_required
def sys_health(request):
    import urllib.request
    checks = []

    # DB
    try:
        t0 = time.time()
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
        checks.append({'name': 'Database', 'ok': True, 'ms': round((time.time()-t0)*1000,2), 'detail': 'Ulanish muvaffaqiyatli'})
    except Exception as e:
        checks.append({'name': 'Database', 'ok': False, 'ms': 0, 'detail': str(e)})

    # Static fayllar
    checks.append({
        'name': 'Static fayllar',
        'ok': os.path.exists(str(settings.STATIC_ROOT)),
        'ms': 0,
        'detail': str(settings.STATIC_ROOT),
    })

    # Media papka
    checks.append({
        'name': 'Media papka',
        'ok': os.path.exists(str(settings.MEDIA_ROOT)),
        'ms': 0,
        'detail': str(settings.MEDIA_ROOT),
    })

    # Migrations
    from django.db.migrations.loader import MigrationLoader
    loader = MigrationLoader(connection)
    pending = len(loader.disk_migrations) - len(loader.applied_migrations)
    checks.append({
        'name': 'Migratsiyalar',
        'ok': pending == 0,
        'ms': 0,
        'detail': f'{pending} ta bajarilmagan' if pending else 'Hammasi bajarilgan',
    })

    # Debug rejim
    checks.append({
        'name': 'Debug rejim',
        'ok': not settings.DEBUG,
        'ms': 0,
        'detail': 'OFF (xavfsiz)' if not settings.DEBUG else 'ON — production da o\'chiring!',
    })

    all_ok = all(c['ok'] for c in checks)
    return render(request, 'tizim/health.html', {'checks': checks, 'all_ok': all_ok})


# ── DB BACKUP (dump) ──────────────────────────────────────────────────────────
@superuser_required
def sys_backup(request):
    if request.method == 'POST':
        from django.http import HttpResponse
        import json

        # Barcha modellardan ma'lumot olish
        from django.core import serializers
        from .models import (User, Skill, Project, Contest, Course, Lesson,
                             Message, Notification, ActivityLog, Job, Resource)
        data = {}
        for model in [User, Skill, Project, Contest, Course, Lesson,
                      Message, Notification, ActivityLog, Job, Resource]:
            name = model.__name__
            data[name] = json.loads(serializers.serialize('json', model.objects.all()))

        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            content_type='application/json'
        )
        ts = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="backup_{ts}.json"'
        return response

    return render(request, 'tizim/backup.html')


# ── TERMINAL (buyruq bajarish) ─────────────────────────────────────────────────
@superuser_required
def sys_terminal(request):
    output = ''
    command = ''
    error = ''

    # Taqiqlangan buyruqlar
    FORBIDDEN = ['rm -rf /', 'mkfs', 'dd if=', 'shutdown', 'reboot',
                 'passwd', 'userdel', 'chmod 777 /', 'wget http', 'curl http']

    if request.method == 'POST':
        command = request.POST.get('command', '').strip()
        if any(f in command.lower() for f in FORBIDDEN):
            error = f"Bu buyruq taqiqlangan: {command}"
        elif command:
            import subprocess
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True,
                    text=True, timeout=30,
                    cwd=str(settings.BASE_DIR)
                )
                output = result.stdout or ''
                if result.stderr:
                    error = result.stderr
            except subprocess.TimeoutExpired:
                error = "Buyruq 30 soniyadan oshdi."
            except Exception as e:
                error = str(e)

    return render(request, 'tizim/terminal.html', {
        'output': output, 'command': command, 'error': error,
    })


# ── JARAYONLAR ────────────────────────────────────────────────────────────────
@superuser_required
def sys_processes(request):
    import subprocess
    processes = []
    try:
        out = subprocess.check_output(
            ['ps', 'aux', '--sort=-%cpu'],
            stderr=subprocess.DEVNULL
        ).decode()
        lines = out.strip().split('\n')
        headers = lines[0].split()
        for line in lines[1:21]:  # Top 20
            parts = line.split(None, 10)
            if len(parts) >= 11:
                processes.append({
                    'user':    parts[0],
                    'pid':     parts[1],
                    'cpu':     parts[2],
                    'mem':     parts[3],
                    'status':  parts[7],
                    'command': parts[10][:80],
                })
    except Exception as e:
        processes = [{'user': 'xato', 'pid': '', 'cpu': '', 'mem': '', 'status': '', 'command': str(e)}]

    # Disk holati
    disk_info = []
    try:
        out = subprocess.check_output(['df', '-h'], stderr=subprocess.DEVNULL).decode()
        for line in out.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 6:
                disk_info.append({
                    'fs': parts[0], 'size': parts[1],
                    'used': parts[2], 'avail': parts[3],
                    'use_pct': parts[4], 'mount': parts[5],
                })
    except:
        pass

    # RAM holati
    ram_info = {}
    try:
        out = subprocess.check_output(['free', '-h'], stderr=subprocess.DEVNULL).decode()
        lines = out.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            ram_info = {'total': parts[1], 'used': parts[2], 'free': parts[3]}
    except:
        pass

    return render(request, 'tizim/processes.html', {
        'processes': processes, 'disk_info': disk_info, 'ram_info': ram_info,
    })


# ── CRON / REJALASHTIRILGAN VAZIFALAR ─────────────────────────────────────────
@superuser_required
def sys_cron(request):
    import subprocess
    cron_list = []
    cron_output = ''

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            schedule = request.POST.get('schedule', '').strip()
            cmd      = request.POST.get('cmd', '').strip()
            if schedule and cmd:
                # Crontab ga qo'shish
                try:
                    existing = subprocess.check_output(
                        ['crontab', '-l'], stderr=subprocess.DEVNULL
                    ).decode()
                except:
                    existing = ''
                new_line = f"{schedule} {cmd}\n"
                new_cron = existing + new_line
                proc = subprocess.run(
                    ['crontab', '-'], input=new_cron.encode(),
                    capture_output=True
                )
                cron_output = 'Qo\'shildi!' if proc.returncode == 0 else proc.stderr.decode()

    # Mavjud cron larni ko'rish
    try:
        out = subprocess.check_output(['crontab', '-l'], stderr=subprocess.DEVNULL).decode()
        for line in out.strip().split('\n'):
            if line and not line.startswith('#'):
                cron_list.append(line)
    except:
        cron_list = []

    # Tayyor shablonlar
    templates = [
        {'label': 'Har kuni yarim tunda backup', 'schedule': '0 0 * * *',
         'cmd': f'cd {settings.BASE_DIR} && python manage.py shell -c "print(\'backup\')"'},
        {'label': 'Har soatda cache tozalash', 'schedule': '0 * * * *',
         'cmd': f'cd {settings.BASE_DIR} && python manage.py shell -c "from django.core.cache import cache; cache.clear()"'},
        {'label': 'Har 5 daqiqada health check', 'schedule': '*/5 * * * *',
         'cmd': f'curl -s https://yoshiqtidorlar.uz/ > /dev/null'},
    ]

    return render(request, 'tizim/cron.html', {
        'cron_list': cron_list, 'cron_output': cron_output, 'templates': templates,
    })


# ── TARMOQ MA'LUMOTLARI ───────────────────────────────────────────────────────
@superuser_required
def sys_network(request):
    import subprocess
    net_info = {}

    # Ochiq portlar
    open_ports = []
    try:
        out = subprocess.check_output(
            ['ss', '-tlnp'], stderr=subprocess.DEVNULL
        ).decode()
        for line in out.strip().split('\n')[1:]:
            parts = line.split()
            if len(parts) >= 4:
                open_ports.append({
                    'state':   parts[0],
                    'local':   parts[3],
                    'process': parts[6] if len(parts) > 6 else '—',
                })
    except:
        pass

    # IP manzillar
    ip_info = []
    try:
        out = subprocess.check_output(['ip', 'addr'], stderr=subprocess.DEVNULL).decode()
        ip_info = out.strip().split('\n')
    except:
        pass

    # DNS tekshirish
    dns_check = {}
    try:
        import socket
        dns_check['yoshiqtidorlar.uz'] = socket.gethostbyname('yoshiqtidorlar.uz')
        dns_check['api.telegram.org']  = socket.gethostbyname('api.telegram.org')
    except Exception as e:
        dns_check['xato'] = str(e)

    return render(request, 'tizim/network.html', {
        'open_ports': open_ports, 'ip_info': ip_info, 'dns_check': dns_check,
    })


# ── DB OPTIMIZATSIYA ──────────────────────────────────────────────────────────
@superuser_required
def sys_db_optimize(request):
    results = []
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            with connection.cursor() as cur:
                if action == 'analyze':
                    cur.execute("ANALYZE;")
                    results.append(('ANALYZE', 'OK — statistika yangilandi'))
                elif action == 'vacuum':
                    connection.connection.autocommit = True
                    cur.execute("VACUUM ANALYZE;")
                    connection.connection.autocommit = False
                    results.append(('VACUUM ANALYZE', 'OK — bo\'sh joy tozalandi'))
                elif action == 'indexes':
                    cur.execute("""
                        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
                        FROM pg_stat_user_indexes
                        ORDER BY idx_scan DESC LIMIT 20;
                    """)
                    rows = cur.fetchall()
                    results = [('Index', f"{r[1]}.{r[2]} — {r[3]} scan") for r in rows]
        except Exception as e:
            results.append(('Xato', str(e)))

    # Jadval o'lchamlari
    table_sizes = []
    try:
        with connection.cursor() as cur:
            cur.execute("""
                SELECT
                    relname as table_name,
                    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
                    pg_size_pretty(pg_relation_size(relid)) as table_size,
                    n_live_tup as rows
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(relid) DESC
                LIMIT 20;
            """)
            table_sizes = cur.fetchall()
    except:
        pass

    return render(request, 'tizim/db_optimize.html', {
        'results': results, 'table_sizes': table_sizes,
    })
