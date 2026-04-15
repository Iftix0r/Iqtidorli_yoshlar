from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (User, Contest, Course, Job, Resource,
                     LoginHistory, ActivityLog, ContestApplication,
                     CourseEnrollment, CourseCertificate, Message)


def panel_required(view_func):
    return staff_member_required(view_func, login_url='/login/')


def panel_tfa_required(view_func):
    """Panel uchun login + 2FA tekshirish"""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('/login/?next=' + request.path)
        # 2FA faqat Telegram ishlayotgan bo'lsa
        from django.conf import settings
        if getattr(settings, 'TFA_ENABLED', False):
            if not request.session.get('tfa_verified'):
                request.session['tfa_next'] = request.path
                return redirect('tfa_send')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@panel_tfa_required
def dashboard(request):
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)

    # Grafiklar uchun oxirgi 7 kunlik ma'lumotlar
    from django.db.models.functions import TruncDate
    reg_stats = (
        User.objects.filter(date_joined__gte=week_ago)
        .annotate(day=TruncDate('date_joined'))
        .values('day').annotate(cnt=Count('id')).order_by('day')
    )
    login_stats = (
        LoginHistory.objects.filter(created_at__gte=week_ago, is_success=True)
        .annotate(day=TruncDate('created_at'))
        .values('day').annotate(cnt=Count('id')).order_by('day')
    )

    ctx = {
        'total_users':    User.objects.count(),
        'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'total_yoshlar':  User.objects.filter(role='yosh').count(),
        'total_mentors':  User.objects.filter(role='mentor').count(),
        'total_investors':User.objects.filter(role='investor').count(),
        'total_contests': Contest.objects.count(),
        'total_courses':  Course.objects.count(),
        'total_jobs':     Job.objects.filter(is_active=True).count(),
        'today_logins':   LoginHistory.objects.filter(
                              created_at__date=today, is_success=True).count(),
        'failed_logins':  LoginHistory.objects.filter(
                              created_at__date=today, is_success=False).count(),
        'recent_users':   User.objects.order_by('-date_joined')[:8],
        'recent_activities': ActivityLog.objects.select_related('user').order_by('-created_at')[:15],
        'by_region':      User.objects.filter(role='yosh').exclude(region='')
                              .values('region').annotate(cnt=Count('id')).order_by('-cnt')[:10],
        'top_users':      User.objects.order_by('-score')[:5],
        'chart_labels':   [str(r['day']) for r in reg_stats],
        'chart_reg_data': [r['cnt'] for r in reg_stats],
        'chart_login_labels': [str(l['day']) for l in login_stats],
        'chart_login_data':   [l['cnt'] for l in login_stats],
    }
    return render(request, 'panel/dashboard.html', ctx)


# ── FOYDALANUVCHILAR ──────────────────────────────────────────────────────────
@panel_tfa_required
def users_view(request):
    q      = request.GET.get('q', '').strip()
    role   = request.GET.get('role', '')
    region = request.GET.get('region', '')

    qs = User.objects.order_by('-date_joined')
    if q:
        qs = qs.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(phone__icontains=q))
    if role:
        qs = qs.filter(role=role)
    if region:
        qs = qs.filter(region=region)

    # Ball yangilash
    if request.method == 'POST':
        uid   = request.POST.get('user_id')
        score = request.POST.get('score')
        role_new = request.POST.get('role_new')
        action = request.POST.get('action')
        user = get_object_or_404(User, pk=uid)
        if action == 'score' and score:
            user.score = int(score)
            user.save()
        elif action == 'role' and role_new:
            user.role = role_new
            user.save()
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
        return redirect('panel_users')

    regions = User.objects.exclude(region='').values_list('region', flat=True).distinct()
    return render(request, 'panel/users.html', {
        'users': qs, 'q': q, 'role': role, 'region': region, 'regions': regions,
    })


# ── FAOLIYAT TARIXI ───────────────────────────────────────────────────────────
@panel_tfa_required
def activities_view(request):
    action = request.GET.get('action', '')
    q      = request.GET.get('q', '').strip()
    qs     = ActivityLog.objects.select_related('user').order_by('-created_at')
    if action:
        qs = qs.filter(action=action)
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q)|Q(user__phone__icontains=q)|Q(detail__icontains=q))
    return render(request, 'panel/activities.html', {
        'activities': qs[:200], 'action': action, 'q': q,
        'action_choices': ActivityLog.ACTION_TYPES,
    })


# ── KIRISH TARIXI ─────────────────────────────────────────────────────────────
@panel_tfa_required
def logins_view(request):
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    qs     = LoginHistory.objects.select_related('user').order_by('-created_at')
    if status == 'success':
        qs = qs.filter(is_success=True)
    elif status == 'failed':
        qs = qs.filter(is_success=False)
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q)|Q(ip_address__icontains=q))
    return render(request, 'panel/logins.html', {
        'logins': qs[:200], 'q': q, 'status': status,
    })


# ── TANLOVLAR ─────────────────────────────────────────────────────────────────
@panel_tfa_required
def contests_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Contest.objects.filter(pk=request.POST.get('contest_id')).delete()
        elif action == 'add':
            Contest.objects.create(
                title       = request.POST.get('title'),
                description = request.POST.get('description',''),
                deadline    = request.POST.get('deadline') or None,
                prize       = request.POST.get('prize',''),
            )
        return redirect('panel_contests')

    contests = Contest.objects.annotate(app_count=Count('applications')).order_by('-created_at')
    return render(request, 'panel/contests.html', {'contests': contests})


# ── KURSLAR ───────────────────────────────────────────────────────────────────
@panel_tfa_required
def courses_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle':
            c = get_object_or_404(Course, pk=request.POST.get('course_id'))
            c.is_active = not c.is_active
            c.save()
        elif action == 'delete':
            Course.objects.filter(pk=request.POST.get('course_id')).delete()
        return redirect('panel_courses')

    courses = Course.objects.annotate(
        enroll_count=Count('enrollments'),
        cert_count=Count('certificates')
    ).order_by('-created_at')
    return render(request, 'panel/courses.html', {'courses': courses})


# ── ISH E'LONLARI ─────────────────────────────────────────────────────────────
@panel_tfa_required
def jobs_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle':
            j = get_object_or_404(Job, pk=request.POST.get('job_id'))
            j.is_active = not j.is_active
            j.save()
        elif action == 'delete':
            Job.objects.filter(pk=request.POST.get('job_id')).delete()
        return redirect('panel_jobs')

    jobs = Job.objects.select_related('posted_by').order_by('-created_at')
    return render(request, 'panel/jobs.html', {'jobs': jobs})


# ── RESURSLAR ─────────────────────────────────────────────────────────────────
@panel_tfa_required
def resources_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Resource.objects.filter(pk=request.POST.get('resource_id')).delete()
        return redirect('panel_resources')

    resources = Resource.objects.select_related('added_by').order_by('-created_at')
    return render(request, 'panel/resources.html', {'resources': resources})


# ── XABARLAR MONITORING ───────────────────────────────────────────────────────
@panel_tfa_required
def messages_view(request):
    from .models import Message
    q  = request.GET.get('q', '').strip()
    qs = Message.objects.select_related('sender', 'receiver').order_by('-created_at')
    if q:
        qs = qs.filter(
            Q(sender__first_name__icontains=q) |
            Q(receiver__first_name__icontains=q) |
            Q(body__icontains=q)
        )
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        Message.objects.filter(pk=request.POST.get('msg_id')).delete()
        return redirect('panel_messages')
    return render(request, 'panel/messages.html', {'messages': qs[:200], 'q': q})


# ── MENTOR SO'ROVLARI ─────────────────────────────────────────────────────────
@panel_tfa_required
def mentor_requests_view(request):
    from .models import MentorRequest
    status = request.GET.get('status', '')
    qs = MentorRequest.objects.select_related('sender', 'receiver').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    if request.method == 'POST':
        req = get_object_or_404(MentorRequest, pk=request.POST.get('req_id'))
        req.status = request.POST.get('new_status', req.status)
        req.save()
        return redirect('panel_mentor_requests')
    return render(request, 'panel/mentor_requests.html', {
        'requests': qs, 'status': status,
        'status_choices': MentorRequest.STATUS,
    })


# ── TANLOV ARIZALARI ──────────────────────────────────────────────────────────
@panel_tfa_required
def applications_view(request):
    contest_id = request.GET.get('contest', '')
    status     = request.GET.get('status', '')
    qs = ContestApplication.objects.select_related('user', 'contest').order_by('-created_at')
    if contest_id:
        qs = qs.filter(contest_id=contest_id)
    if status:
        qs = qs.filter(status=status)
    if request.method == 'POST':
        app = get_object_or_404(ContestApplication, pk=request.POST.get('app_id'))
        app.status = request.POST.get('new_status', app.status)
        app.save()
        from .utils import log_activity
        from .models import Notification
        if app.status == 'accepted':
            Notification.objects.create(
                user=app.user, notif_type='contest',
                text=f"'{app.contest.title}' tanloviga arizangiz qabul qilindi!",
                link='/contests/'
            )
            app.user.score += 20
            app.user.save()
        return redirect('panel_applications')
    contests = Contest.objects.all()
    return render(request, 'panel/applications.html', {
        'applications': qs, 'contests': contests,
        'selected_contest': contest_id, 'status': status,
        'status_choices': ContestApplication.STATUS,
    })


# ── KURS DARSLARI ─────────────────────────────────────────────────────────────
@panel_tfa_required
def course_lessons_view(request, pk):
    from .models import Lesson
    course  = get_object_or_404(Course, pk=pk)
    lessons = course.lessons.order_by('order')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            Lesson.objects.create(
                course    = course,
                title     = request.POST.get('title'),
                content   = request.POST.get('content', ''),
                video_url = request.POST.get('video_url', ''),
                order     = course.lessons.count() + 1,
            )
        elif action == 'delete':
            Lesson.objects.filter(pk=request.POST.get('lesson_id'), course=course).delete()
        return redirect('panel_course_lessons', pk=pk)

    return render(request, 'panel/course_lessons.html', {
        'course': course, 'lessons': lessons,
    })


# ── OMMAVIY XABAR ─────────────────────────────────────────────────────────────
@panel_tfa_required
def broadcast_view(request):
    from .models import Notification
    sent_count = 0
    if request.method == 'POST':
        text    = request.POST.get('text', '').strip()
        role    = request.POST.get('role', '')
        link    = request.POST.get('link', '')
        if text:
            users = User.objects.filter(is_active=True)
            if role:
                users = users.filter(role=role)
            notifs = [
                Notification(user=u, notif_type='contest', text=text, link=link)
                for u in users
            ]
            Notification.objects.bulk_create(notifs)
            sent_count = len(notifs)
    return render(request, 'panel/broadcast.html', {
        'sent_count': sent_count,
        'roles': User.objects.values_list('role', flat=True).distinct(),
    })


# ── FOYDALANUVCHI BATAFSIL ────────────────────────────────────────────────────
@panel_tfa_required
def user_detail_view(request, pk):
    from .models import LoginHistory, ActivityLog
    target   = get_object_or_404(User, pk=pk)
    logins   = LoginHistory.objects.filter(user=target).order_by('-created_at')[:20]
    acts     = ActivityLog.objects.filter(user=target).order_by('-created_at')[:30]
    projects = target.projects.order_by('-created_at')
    certs    = target.certificates.order_by('-issued_date')
    course_certs = target.course_certificates.select_related('course').order_by('-issued_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'score':
            target.score = int(request.POST.get('score', target.score))
            target.save()
        elif action == 'role':
            target.role = request.POST.get('role', target.role)
            target.save()
        elif action == 'toggle':
            target.is_active = not target.is_active
            target.save()
        elif action == 'notify':
            from .models import Notification
            Notification.objects.create(
                user=target, notif_type='score',
                text=request.POST.get('msg', ''),
            )
        return redirect('panel_user_detail', pk=pk)

    return render(request, 'panel/user_detail.html', {
        'target': target, 'logins': logins, 'acts': acts,
        'projects': projects, 'certs': certs, 'course_certs': course_certs,
    })


# ── FOYDALANUVCHI YARATISH ────────────────────────────────────────────────────
@panel_tfa_required
def user_create_view(request):
    from .forms import RegisterForm
    import re
    error = ''
    if request.method == 'POST':
        phone    = request.POST.get('phone', '').strip()
        fname    = request.POST.get('first_name', '').strip()
        lname    = request.POST.get('last_name', '').strip()
        role     = request.POST.get('role', 'yosh')
        region   = request.POST.get('region', '')
        password = request.POST.get('password', '')
        is_staff = request.POST.get('is_staff') == 'on'

        if not phone or not fname or not password:
            error = 'Telefon, ism va parol majburiy.'
        elif User.objects.filter(phone=phone).exists():
            error = 'Bu telefon raqam allaqachon mavjud.'
        else:
            username = re.sub(r'\D', '', phone)
            user = User.objects.create_user(
                username   = username,
                phone      = phone,
                first_name = fname,
                last_name  = lname,
                role       = role,
                region     = region,
                password   = password,
                is_staff   = is_staff,
            )
            return redirect('panel_user_detail', pk=user.pk)

    from .models import REGIONS, ROLE_CHOICES
    return render(request, 'panel/user_create.html', {
        'error': error, 'regions': REGIONS, 'roles': ROLE_CHOICES,
    })


# ── FOYDALANUVCHI TAHRIRLASH ──────────────────────────────────────────────────
@panel_tfa_required
def user_edit_view(request, pk):
    target = get_object_or_404(User, pk=pk)
    error  = ''
    if request.method == 'POST':
        target.first_name = request.POST.get('first_name', target.first_name)
        target.last_name  = request.POST.get('last_name', target.last_name)
        target.bio        = request.POST.get('bio', target.bio)
        target.role       = request.POST.get('role', target.role)
        target.region     = request.POST.get('region', target.region)
        target.score      = int(request.POST.get('score', target.score) or 0)
        target.is_staff   = request.POST.get('is_staff') == 'on'
        target.is_active  = request.POST.get('is_active') == 'on'

        new_pass = request.POST.get('new_password', '').strip()
        if new_pass:
            if len(new_pass) < 6:
                error = 'Parol kamida 6 ta belgi bo\'lishi kerak.'
            else:
                target.set_password(new_pass)

        if not error:
            if request.FILES.get('avatar'):
                target.avatar = request.FILES['avatar']
            target.save()
            return redirect('panel_user_detail', pk=pk)

    from .models import REGIONS, ROLE_CHOICES
    return render(request, 'panel/user_edit.html', {
        'target': target, 'error': error,
        'regions': REGIONS, 'roles': ROLE_CHOICES,
    })


# ── FOYDALANUVCHI O'CHIRISH ───────────────────────────────────────────────────
@panel_tfa_required
def user_delete_view(request, pk):
    target = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        target.delete()
        return redirect('panel_users')
    return render(request, 'panel/user_delete.html', {'target': target})


# ── STATISTIKA (JSON API) ─────────────────────────────────────────────────────
@panel_tfa_required
def stats_api(request):
    from django.http import JsonResponse
    from django.db.models.functions import TruncDate
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)

    # Kunlik ro'yxatdan o'tishlar
    reg_data = (
        User.objects.filter(date_joined__gte=since)
        .annotate(day=TruncDate('date_joined'))
        .values('day').annotate(cnt=Count('id'))
        .order_by('day')
    )
    # Kunlik kirishlar
    login_data = (
        LoginHistory.objects.filter(created_at__gte=since, is_success=True)
        .annotate(day=TruncDate('created_at'))
        .values('day').annotate(cnt=Count('id'))
        .order_by('day')
    )
    return JsonResponse({
        'registrations': [{'day': str(r['day']), 'cnt': r['cnt']} for r in reg_data],
        'logins':        [{'day': str(r['day']), 'cnt': r['cnt']} for r in login_data],
    })


# ── KURS YARATISH ─────────────────────────────────────────────────────────────
@panel_tfa_required
def course_create_view(request):
    error = ''
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        desc  = request.POST.get('description', '').strip()
        level = request.POST.get('level', 'beginner')
        dur   = request.POST.get('duration', '').strip()
        if not title:
            error = 'Kurs nomi majburiy.'
        else:
            course = Course.objects.create(
                title       = title,
                description = desc,
                level       = level,
                duration    = dur,
                author      = request.user,
                is_active   = True,
            )
            if request.FILES.get('cover'):
                course.cover = request.FILES['cover']
                course.save()
            return redirect('panel_course_lessons', pk=course.pk)
    return render(request, 'panel/course_create.html', {
        'error': error, 'levels': Course.LEVELS,
    })


# ── SAYT SOZLAMALARI ──────────────────────────────────────────────────────────
@panel_tfa_required
def settings_view(request):
    from .models import SiteSettings
    settings = SiteSettings.get()
    saved = False
    if request.method == 'POST':
        settings.site_name     = request.POST.get('site_name', settings.site_name)
        settings.site_desc     = request.POST.get('site_desc', settings.site_desc)
        settings.contact_phone = request.POST.get('contact_phone', '')
        settings.contact_email = request.POST.get('contact_email', '')
        settings.telegram      = request.POST.get('telegram', '')
        settings.instagram     = request.POST.get('instagram', '')
        settings.maintenance   = request.POST.get('maintenance') == 'on'
        settings.save()
        saved = True
    return render(request, 'panel/settings.html', {'settings': settings, 'saved': saved})


# ── CSV EKSPORT ───────────────────────────────────────────────────────────────
@panel_tfa_required
def export_users_csv(request):
    import csv
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(['ID', 'Ism', 'Familiya', 'Telefon', 'Rol', 'Viloyat', 'Ball', 'Faol', 'Sana'])
    for u in User.objects.all().order_by('-date_joined'):
        writer.writerow([
            u.pk, u.first_name, u.last_name, u.phone,
            u.get_role_display(), u.region, u.score,
            'Ha' if u.is_active else "Yo'q",
            u.date_joined.strftime('%d.%m.%Y'),
        ])
    return response


# ── BLOKLANGAN IPlar ──────────────────────────────────────────────────────────
@panel_tfa_required
def blocked_ips_view(request):
    from .models import FailedLoginAttempt
    if request.method == 'POST':
        FailedLoginAttempt.objects.filter(pk=request.POST.get('id')).delete()
        return redirect('panel_blocked_ips')
    blocked = FailedLoginAttempt.objects.filter(
        blocked_until__isnull=False
    ).order_by('-last_attempt')
    all_attempts = FailedLoginAttempt.objects.order_by('-last_attempt')[:50]
    return render(request, 'panel/blocked_ips.html', {
        'blocked': blocked, 'all_attempts': all_attempts,
    })


# ── REAL-TIME API ─────────────────────────────────────────────────────────────
@panel_tfa_required
def realtime_api(request):
    from django.http import JsonResponse
    from .models import ActivityLog, LoginHistory, Message, MentorRequest, ContestApplication, Notification

    today = timezone.now().date()
    return JsonResponse({
        'total_users':     User.objects.count(),
        'today_logins':    LoginHistory.objects.filter(created_at__date=today, is_success=True).count(),
        'failed_logins':   LoginHistory.objects.filter(created_at__date=today, is_success=False).count(),
        'unread_messages': Message.objects.filter(is_read=False).count(),
        'pending_mentor':  MentorRequest.objects.filter(status='pending').count(),
        'pending_apps':    ContestApplication.objects.filter(status='pending').count(),
        'unread_notifs':   Notification.objects.filter(is_read=False).count(),
        'last_activity':   list(
            ActivityLog.objects.select_related('user')
            .order_by('-created_at')
            .values('user__first_name', 'user__last_name', 'action', 'detail', 'created_at')[:5]
        ),
        'last_logins': list(
            LoginHistory.objects.select_related('user')
            .order_by('-created_at')
            .values('user__first_name', 'user__phone', 'ip_address', 'device', 'is_success', 'created_at')[:5]
        ),
    }, json_dumps_params={'default': str})


# ── ADMIN BILDIRISHNOMALAR ────────────────────────────────────────────────────
@panel_tfa_required
def notifications_panel_view(request):
    from .models import Notification
    q      = request.GET.get('q', '').strip()
    ntype  = request.GET.get('type', '')
    status = request.GET.get('status', '')

    qs = Notification.objects.select_related('user').order_by('-created_at')
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q) | Q(text__icontains=q))
    if ntype:
        qs = qs.filter(notif_type=ntype)
    if status == 'read':
        qs = qs.filter(is_read=True)
    elif status == 'unread':
        qs = qs.filter(is_read=False)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Notification.objects.filter(pk=request.POST.get('notif_id')).delete()
        elif action == 'delete_all':
            Notification.objects.filter(is_read=True).delete()
        elif action == 'mark_all_read':
            Notification.objects.filter(is_read=False).update(is_read=True)
        return redirect('panel_notifications')

    unread_count = Notification.objects.filter(is_read=False).count()
    return render(request, 'panel/notifications.html', {
        'notifications': qs[:300],
        'q': q, 'ntype': ntype, 'status': status,
        'unread_count': unread_count,
        'type_choices': Notification.TYPES,
    })


# ── NOTIF LIST API (dropdown uchun) ──────────────────────────────────────────
@panel_tfa_required
def notif_list_api(request):
    from django.http import JsonResponse
    from .models import Notification
    notifs = Notification.objects.select_related('user').order_by('-created_at')[:15]
    return JsonResponse({
        'notifications': [
            {
                'id':        n.pk,
                'text':      n.text,
                'notif_type':n.notif_type,
                'is_read':   n.is_read,
                'link':      n.link,
                'user':      n.user.get_full_name() or n.user.phone,
                'time':      n.created_at.strftime('%d.%m %H:%M'),
            }
            for n in notifs
        ]
    })


# ── SERTIFIKATLAR MONITORINGI ────────────────────────────────────────────────
@panel_tfa_required
def certificates_view(request):
    """Barcha berilgan kurs sertifikatlarini ko'rish"""
    q      = request.GET.get('q', '').strip()
    course_id = request.GET.get('course', '')
    
    qs = CourseCertificate.objects.select_related('user', 'course').order_by('-issued_at')
    
    if q:
        qs = qs.filter(Q(user__first_name__icontains=q) | Q(cert_number__icontains=q))
    if course_id:
        qs = qs.filter(course_id=course_id)
        
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        CourseCertificate.objects.filter(pk=request.POST.get('cert_id')).delete()
        return redirect('panel_certificates')

    courses = Course.objects.all()
    return render(request, 'panel/certificates.html', {
        'certificates': qs,
        'courses': courses,
        'q': q,
        'selected_course': course_id
    })


# ── MARKET BOSHQARUVI ─────────────────────────────────────────────────────────
@panel_tfa_required
def market_items_view(request):
    from .models import MarketItem
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            item = MarketItem.objects.create(
                title       = request.POST.get('title', '').strip(),
                description = request.POST.get('description', '').strip(),
                category    = request.POST.get('category', 'gift'),
                price       = int(request.POST.get('price', 100)),
                stock       = int(request.POST.get('stock', -1)),
                is_active   = request.POST.get('is_active') == 'on',
            )
            if request.FILES.get('image'):
                item.image = request.FILES['image']
                item.save()
        elif action == 'toggle':
            item = get_object_or_404(MarketItem, pk=request.POST.get('item_id'))
            item.is_active = not item.is_active
            item.save()
        elif action == 'delete':
            MarketItem.objects.filter(pk=request.POST.get('item_id')).delete()
        elif action == 'edit':
            item = get_object_or_404(MarketItem, pk=request.POST.get('item_id'))
            item.title       = request.POST.get('title', item.title).strip()
            item.description = request.POST.get('description', item.description).strip()
            item.category    = request.POST.get('category', item.category)
            item.price       = int(request.POST.get('price', item.price))
            item.stock       = int(request.POST.get('stock', item.stock))
            item.is_active   = request.POST.get('is_active') == 'on'
            if request.FILES.get('image'):
                item.image = request.FILES['image']
            item.save()
        return redirect('panel_market_items')

    items = MarketItem.objects.annotate(order_count=Count('orders')).order_by('price')
    return render(request, 'panel/market_items.html', {
        'items': items,
        'categories': MarketItem.CATEGORIES,
    })


@panel_tfa_required
def market_orders_view(request):
    from .models import MarketOrder, Notification
    status = request.GET.get('status', '')
    qs = MarketOrder.objects.select_related('user', 'item').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)

    if request.method == 'POST':
        order = get_object_or_404(MarketOrder, pk=request.POST.get('order_id'))
        old_status = order.status
        new_status = request.POST.get('status', order.status)
        note       = request.POST.get('note', '').strip()
        order.status = new_status
        order.note   = note
        order.save()

        # Bildirishnoma
        text_map = {
            'approved':  f"'{order.item.title}' buyurtmangiz tasdiqlandi! 🎉",
            'rejected':  f"'{order.item.title}' buyurtmangiz rad etildi.",
            'delivered': f"'{order.item.title}' yetkazildi! Tabriklaymiz 🎁",
        }
        if new_status in text_map and old_status != new_status:
            Notification.objects.create(
                user=order.user, notif_type='score',
                text=text_map[new_status], link='/market/orders/'
            )
            # Rad etilsa — ballarni qaytarish
            if new_status == 'rejected' and old_status == 'pending':
                order.user.score += order.price_paid
                order.user.save(update_fields=['score'])

        return redirect('panel_market_orders')

    pending_count = MarketOrder.objects.filter(status='pending').count()
    return render(request, 'panel/market_orders.html', {
        'orders':        qs[:200],
        'status':        status,
        'status_choices': MarketOrder.STATUS,
        'pending_count': pending_count,
    })
