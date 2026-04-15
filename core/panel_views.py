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


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@panel_required
def dashboard(request):
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)

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
    }
    return render(request, 'panel/dashboard.html', ctx)


# ── FOYDALANUVCHILAR ──────────────────────────────────────────────────────────
@panel_required
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
@panel_required
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
@panel_required
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
@panel_required
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
@panel_required
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
@panel_required
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
@panel_required
def resources_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            Resource.objects.filter(pk=request.POST.get('resource_id')).delete()
        return redirect('panel_resources')

    resources = Resource.objects.select_related('added_by').order_by('-created_at')
    return render(request, 'panel/resources.html', {'resources': resources})
