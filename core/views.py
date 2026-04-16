from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Max
from django.http import JsonResponse

from .models import User, Contest, MentorRequest, Message, Notification, Resource, Certificate, ContestApplication, Job, ProfileView, ActivityLog
from .forms  import (RegisterForm, ProfileForm, SkillForm, ProjectForm,
                     ContestForm, MessageForm, ResourceForm,
                     CertificateForm, ContestApplicationForm, JobForm)
from .utils  import get_client_ip, record_login, check_brute_force, record_failed_attempt, reset_failed_attempts, log_activity


# ── HELPERS ───────────────────────────────────────────────────────────────────
def notify(user, notif_type, text, link=''):
    Notification.objects.create(user=user, notif_type=notif_type, text=text, link=link)

def privacy_view(request):
    """Maxfiylik siyosati sahifasi"""
    return render(request, 'privacy.html')


# ── HOME ──────────────────────────────────────────────────────────────────────
def index(request):
    top_talents = (
        User.objects.filter(role='yosh')
        .prefetch_related('skills')
        .order_by('-score')[:4]
    )
    stats = {
        'yoshlar':   User.objects.filter(role='yosh').count() or 10000,
        'mentors':   User.objects.filter(role='mentor').count() or 500,
        'investors': User.objects.filter(role='investor').count() or 150,
    }
    features = [
        ('target',         'Shaxsiy Portfolio',      "Yutuqlar, sertifikatlar va loyihalarni professional namoyish eting."),
        ('trophy',         'Reyting Tizimi',          "Top Iqtidorlar ro'yxatiga kiring va e'tirof qozonin."),
        ('graduation-cap', 'Tanlovlar va Grantlar',   "Barcha tanlov va grantlarni bir joyda kuzating."),
        ('message-circle', 'Xabar Yuborish',          "Mentor va investorlar bilan to'g'ridan-to'g'ri muloqot."),
        ('book-open',      'Bilim Xazinasi',          "Kurslar va kitoblar bazasidan bepul foydalaning."),
        ('handshake',      "Mentor So'rovi",          "Tajribali mentorlardan yordam so'rang."),
    ]
    return render(request, 'index.html', {
        'top_talents': top_talents,
        'stats': stats,
        'features': features,
    })


# ── AUTH ──────────────────────────────────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        log_activity(user, 'register', 'Platformaga ro\'yxatdan o\'tdi')
        messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz!")
        return redirect('profile')
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    error = ''
    if request.method == 'POST':
        from .forms import normalize_phone
        from .utils import get_client_ip, record_login, check_brute_force, record_failed_attempt, reset_failed_attempts

        phone    = normalize_phone(request.POST.get('phone', ''))
        password = request.POST.get('password', '')
        ip       = get_client_ip(request)

        # Brute-force tekshirish
        allowed, block_msg = check_brute_force(phone, ip)
        if not allowed:
            error = block_msg
        else:
            user = authenticate(request, phone=phone, password=password)
            if user:
                login(request, user)
                reset_failed_attempts(phone, ip)
                record_login(request, user, success=True)
                log_activity(user, 'login', f'IP: {ip}')
                # Streak va birinchi login badge
                from .utils import update_streak, award_badge
                update_streak(user)
                award_badge(user, 'first_login')
                return redirect(request.GET.get('next', 'profile'))
            else:
                record_failed_attempt(phone, ip)
                error = "Telefon raqam yoki parol noto'g'ri."

    return render(request, 'login.html', {'error': error})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, 'logout', 'Tizimdan chiqdi')
    logout(request)
    return redirect('index')


# ── PROFILE (o'z profili) ─────────────────────────────────────────────────────
@login_required
def profile_view(request):
    user         = request.user
    profile_form = ProfileForm(instance=user)
    skill_form   = SkillForm()
    project_form = ProjectForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'profile':
            profile_form = ProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                log_activity(user, 'profile_edit', 'Profil ma\'lumotlari yangilandi')
                messages.success(request, 'Profil yangilandi.')
                return redirect('profile')

        elif action == 'skill':
            skill_form = SkillForm(request.POST)
            if skill_form.is_valid():
                s = skill_form.save(commit=False)
                s.user = user
                s.save()
                log_activity(user, 'skill_add', f'Ko\'nikma: {s.skill_name}')
                return redirect('profile')

        elif action == 'project':
            project_form = ProjectForm(request.POST)
            if project_form.is_valid():
                p = project_form.save(commit=False)
                p.user = user
                p.save()
                log_activity(user, 'project_add', f'Loyiha: {p.title}', f'/profile/')
                return redirect('profile')

        elif action == 'del_skill':
            user.skills.filter(pk=request.POST.get('skill_id')).delete()
            return redirect('profile')

        elif action == 'certificate':
            cert_form = CertificateForm(request.POST, request.FILES)
            if cert_form.is_valid():
                c = cert_form.save(commit=False)
                c.user = user
                c.save()
                log_activity(user, 'cert_add', f'Sertifikat: {c.title}')
                return redirect('profile')

    cert_form = CertificateForm()
    return render(request, 'profile.html', {
        'profile_form':    profile_form,
        'skill_form':      skill_form,
        'project_form':    project_form,
        'cert_form':       cert_form,
        'skills':          user.skills.all(),
        'projects':        user.projects.order_by('-created_at'),
        'certificates':    user.certificates.order_by('-issued_date'),
        'notifs':          user.notifications.all()[:10],
        'unread_notif':    user.unread_notifications(),
        'mentor_requests': user.received_requests.filter(status='pending'),
        'login_history':   user.login_history.all()[:5],
        'activities':      user.activities.all()[:15],
    })


# ── PUBLIC PROFILE ────────────────────────────────────────────────────────────
def public_profile(request, pk):
    target = get_object_or_404(User, pk=pk)
    # Ko'rishlar sonini saqlash
    ip = request.META.get('REMOTE_ADDR')
    ProfileView.objects.get_or_create(profile=target, viewer_ip=ip)

    already_sent = False
    already_applied_ids = []
    if request.user.is_authenticated:
        already_sent = MentorRequest.objects.filter(
            sender=request.user, receiver=target
        ).exists()

    view_count = target.profile_views.count()
    return render(request, 'public_profile.html', {
        'target':       target,
        'skills':       target.skills.all(),
        'projects':     target.projects.order_by('-created_at'),
        'certificates': target.certificates.order_by('-issued_date'),
        'already_sent': already_sent,
        'view_count':   view_count,
    })


# ── TALENTS ───────────────────────────────────────────────────────────────────
def talents_view(request):
    qs     = User.objects.filter(role='yosh').prefetch_related('skills').order_by('-score')
    q      = request.GET.get('q', '').strip()
    region = request.GET.get('region', '').strip()
    skill  = request.GET.get('skill', '').strip()

    if q:
        qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(bio__icontains=q))
    if region:
        qs = qs.filter(region=region)
    if skill:
        qs = qs.filter(skills__skill_name__icontains=skill)

    regions = (User.objects.exclude(region='')
               .values_list('region', flat=True).distinct().order_by('region'))
    return render(request, 'talents.html', {
        'talents': qs, 'regions': regions,
        'q': q, 'selected_region': region, 'selected_skill': skill,
    })


# ── LEADERBOARD ───────────────────────────────────────────────────────────────
def leaderboard_view(request):
    role   = request.GET.get('role', 'yosh')
    region = request.GET.get('region', '')
    qs     = User.objects.filter(role=role).prefetch_related('skills').order_by('-score')
    if region:
        qs = qs.filter(region=region)
    regions = (User.objects.exclude(region='')
               .values_list('region', flat=True).distinct().order_by('region'))
    return render(request, 'leaderboard.html', {
        'users': qs[:50], 'role': role, 'regions': regions, 'selected_region': region,
    })


# ── CONTESTS ──────────────────────────────────────────────────────────────────
def contests_view(request):
    contests = Contest.objects.order_by('deadline')
    applied_ids = []
    if request.user.is_authenticated:
        applied_ids = list(
            ContestApplication.objects.filter(user=request.user)
            .values_list('contest_id', flat=True)
        )
    return render(request, 'contests.html', {
        'contests': contests, 'applied_ids': applied_ids
    })


@login_required
def apply_contest(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if ContestApplication.objects.filter(contest=contest, user=request.user).exists():
        messages.info(request, "Siz allaqachon ariza topshirgansiz.")
        return redirect('contests')
    form = ContestApplicationForm(request.POST or None)
    if form.is_valid():
        app = form.save(commit=False)
        app.contest = contest
        app.user    = request.user
        app.save()
        log_activity(request.user, 'contest_apply', f'Tanlov: {contest.title}', f'/contests/')
        messages.success(request, f"'{contest.title}' tanloviga arizangiz qabul qilindi!")
        return redirect('contests')
    return render(request, 'apply_contest.html', {'contest': contest, 'form': form})


@login_required
def add_contest_view(request):
    if not request.user.is_staff:
        return redirect('contests')
    form = ContestForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Tanlov qo'shildi.")
        return redirect('contests')
    return render(request, 'add_contest.html', {'form': form})


# ── MENTOR SO'ROVI ────────────────────────────────────────────────────────────
@login_required
def send_mentor_request(request, pk):
    receiver = get_object_or_404(User, pk=pk)
    if receiver == request.user:
        messages.error(request, "O'zingizga so'rov yubora olmaysiz.")
        return redirect('public_profile', pk=pk)

    obj, created = MentorRequest.objects.get_or_create(
        sender=request.user, receiver=receiver,
        defaults={'message': request.POST.get('message', '')}
    )
    if created:
        notify(receiver, 'mentor_req',
               f"{request.user} mentor so'rovi yubordi.",
               f"/profile/user/{receiver.pk}/")
        messages.success(request, "So'rov yuborildi.")
    else:
        messages.info(request, "So'rov allaqachon yuborilgan.")
    return redirect('public_profile', pk=pk)


@login_required
def handle_mentor_request(request, req_id, action):
    req = get_object_or_404(MentorRequest, pk=req_id, receiver=request.user)
    if action == 'accept':
        req.status = 'accepted'
        notify(req.sender, 'mentor_req',
               f"{request.user} mentor so'rovingizni qabul qildi.", '/messages/')
        messages.success(request, "So'rov qabul qilindi.")
    else:
        req.status = 'rejected'
        notify(req.sender, 'mentor_req',
               f"{request.user} mentor so'rovingizni rad etdi.", '/')
        messages.info(request, "So'rov rad etildi.")
    req.save()
    return redirect('profile')


# ── XABARLAR ──────────────────────────────────────────────────────────────────
@login_required
def inbox_view(request):
    # Suhbatdoshlar ro'yxati
    contacts = (
        User.objects.filter(
            Q(sent_messages__receiver=request.user) |
            Q(received_messages__sender=request.user)
        ).distinct().exclude(pk=request.user.pk)
    )
    return render(request, 'inbox.html', {'contacts': contacts})


@login_required
def conversation_view(request, pk):
    other = get_object_or_404(User, pk=pk)
    msgs  = Message.objects.filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user)
    )
    # O'qilmagan xabarlarni o'qilgan deb belgilash
    msgs.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.sender   = request.user
            m.receiver = other
            m.save()
            log_activity(request.user, 'msg_send', f'{other.get_full_name()} ga xabar', f'/messages/{other.pk}/')
            notify(other, 'msg',
                   f"{request.user} sizga xabar yubordi.", f'/messages/{request.user.pk}/')
            return redirect('conversation', pk=pk)
    else:
        form = MessageForm()

    return render(request, 'conversation.html', {
        'other': other, 'msgs': msgs, 'form': form,
    })


# ── BILDIRISHNOMALAR ──────────────────────────────────────────────────────────
@login_required
def notifications_view(request):
    notifs = request.user.notifications.all()
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifs': notifs})


# ── RESURSLAR ─────────────────────────────────────────────────────────────────
def resources_view(request):
    rtype = request.GET.get('type', '')
    qs    = Resource.objects.order_by('-created_at')
    if rtype:
        qs = qs.filter(res_type=rtype)
    form = ResourceForm() if request.user.is_authenticated else None

    if request.method == 'POST' and request.user.is_authenticated:
        form = ResourceForm(request.POST)
        if form.is_valid():
            r = form.save(commit=False)
            r.added_by = request.user
            r.save()
            messages.success(request, "Resurs qo'shildi.")
            return redirect('resources')

    return render(request, 'resources.html', {
        'resources':     qs,
        'form':          form,
        'selected_type': rtype,
        'type_choices':  Resource.TYPES,
    })


# ── ISH E'LONLARI ─────────────────────────────────────────────────────────────
def jobs_view(request):
    jtype = request.GET.get('type', '')
    q     = request.GET.get('q', '').strip()
    qs    = Job.objects.filter(is_active=True).order_by('-created_at')
    if jtype:
        qs = qs.filter(job_type=jtype)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__icontains=q) | Q(skills_req__icontains=q))

    form = JobForm() if request.user.is_authenticated else None
    if request.method == 'POST' and request.user.is_authenticated:
        form = JobForm(request.POST)
        if form.is_valid():
            j = form.save(commit=False)
            j.posted_by = request.user
            j.save()
            messages.success(request, "Ish e'loni joylashtirildi.")
            return redirect('jobs')

    return render(request, 'jobs.html', {
        'jobs': qs, 'form': form,
        'selected_type': jtype, 'q': q,
        'job_types': Job.TYPES,
    })


# ── GLOBAL QIDIRUV ────────────────────────────────────────────────────────────
def search_view(request):
    q = request.GET.get('q', '').strip()
    
    # Input validation: g'ayritabiiy uzunlikdagi so'rovlarni va zararli belgilarni kesish
    if len(q) > 50:
        q = q[:50]
        
    results = {'users': [], 'contests': [], 'jobs': [], 'resources': []}
    if q:
        results['users']     = User.objects.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(bio__icontains=q)
        )[:8]
        results['contests']  = Contest.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )[:5]
        results['jobs']      = Job.objects.filter(
            Q(title__icontains=q) | Q(company__icontains=q) | Q(skills_req__icontains=q),
            is_active=True
        )[:5]
        results['resources'] = Resource.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q)
        )[:5]
    return render(request, 'search.html', {'q': q, 'results': results})


# ── KURSLAR ───────────────────────────────────────────────────────────────────
from .models import Course, Lesson, CourseEnrollment, LessonProgress, CourseCertificate
import uuid
from django.utils import timezone


def courses_view(request):
    level  = request.GET.get('level', '')
    qs     = Course.objects.filter(is_active=True).order_by('-created_at')
    if level:
        qs = qs.filter(level=level)
    return render(request, 'courses/list.html', {
        'courses': qs, 'selected_level': level,
        'levels': Course.LEVELS,
    })


def course_detail(request, pk):
    course  = get_object_or_404(Course, pk=pk, is_active=True)
    lessons = course.lessons.all()
    enrolled = False
    progress = 0
    done_ids = []
    certificate = None

    if request.user.is_authenticated:
        enrolled = CourseEnrollment.objects.filter(user=request.user, course=course).exists()
        if enrolled:
            progress = course.progress(request.user)
            done_ids = list(
                LessonProgress.objects.filter(
                    user=request.user, lesson__course=course, completed=True
                ).values_list('lesson_id', flat=True)
            )
            certificate = CourseCertificate.objects.filter(
                user=request.user, course=course
            ).first()

    return render(request, 'courses/detail.html', {
        'course': course, 'lessons': lessons,
        'enrolled': enrolled, 'progress': progress,
        'done_ids': done_ids, 'certificate': certificate,
    })


@login_required
def course_enroll(request, pk):
    course = get_object_or_404(Course, pk=pk, is_active=True)
    CourseEnrollment.objects.get_or_create(user=request.user, course=course)
    log_activity(request.user, 'course_enroll', f'Kurs: {course.title}', f'/courses/{course.pk}/')
    messages.success(request, f"'{course.title}' kursiga yozildingiz!")
    return redirect('course_detail', pk=pk)


@login_required
def lesson_done(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course

    # Kursga yozilganligini tekshirish
    if not CourseEnrollment.objects.filter(user=request.user, course=course).exists():
        return redirect('course_detail', pk=course.pk)

    # Darsni tugallangan deb belgilash
    prog, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    if not prog.completed:
        prog.completed    = True
        prog.completed_at = timezone.now()
        prog.save()

    # Barcha darslar tugallanganmi?
    total = course.lessons.count()
    done  = LessonProgress.objects.filter(
        user=request.user, lesson__course=course, completed=True
    ).count()

    if total > 0 and done >= total:
        # Kursni tugallangan deb belgilash
        enrollment = CourseEnrollment.objects.get(user=request.user, course=course)
        if not enrollment.completed:
            enrollment.completed    = True
            enrollment.completed_at = timezone.now()
            enrollment.save()

            # Sertifikat yaratish
            cert_num = f"IY-{uuid.uuid4().hex[:8].upper()}"
            cert, created = CourseCertificate.objects.get_or_create(
                user=request.user, course=course,
                defaults={'cert_number': cert_num}
            )
            if created:
                # Ball qo'shish
                request.user.score += 50
                request.user.save()
                log_activity(request.user, 'course_done', f'Kurs tugatildi: {course.title}', f'/certificate/{cert.cert_number}/')
                notify(request.user, 'score',
                       f"'{course.title}' kursini tugatdingiz! +50 ball va sertifikat olindiz.",
                       f"/certificate/{cert.cert_number}/")
                messages.success(request,
                    f"Tabriklaymiz! Kursni tugatdingiz. Sertifikatingiz: #{cert.cert_number}")
                return redirect('certificate_view', cert_number=cert.cert_number)

    return redirect('course_detail', pk=course.pk)


def certificate_view(request, cert_number):
    cert = get_object_or_404(CourseCertificate, cert_number=cert_number)
    return render(request, 'courses/certificate.html', {'cert': cert})


# ── ERROR HANDLERS ────────────────────────────────────────────────────────────
def error_404(request, exception):
    return render(request, '404.html', status=404)


def error_500(request):
    return render(request, '500.html', status=500)


def error_403(request, exception):
    return render(request, '404.html', status=403)


# ── PORTAL ────────────────────────────────────────────────────────────────────
@login_required
def portal_view(request, section='home'):
    user = request.user

    # POST — profil tahrirlash
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            from .forms import ProfileForm
            form = ProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                log_activity(user, 'profile_edit', 'Profil yangilandi')
                messages.success(request, 'Profil yangilandi.')
            return redirect('portal_section', section='settings')
        elif action == 'skill':
            from .forms import SkillForm
            form = SkillForm(request.POST)
            if form.is_valid():
                s = form.save(commit=False); s.user = user; s.save()
                log_activity(user, 'skill_add', s.skill_name)
            return redirect('portal_section', section='skills')
        elif action == 'del_skill':
            user.skills.filter(pk=request.POST.get('skill_id')).delete()
            return redirect('portal_section', section='skills')
        elif action == 'project':
            from .forms import ProjectForm
            form = ProjectForm(request.POST)
            if form.is_valid():
                p = form.save(commit=False); p.user = user; p.save()
                log_activity(user, 'project_add', p.title)
            return redirect('portal_section', section='projects')
        elif action == 'certificate':
            from .forms import CertificateForm
            form = CertificateForm(request.POST, request.FILES)
            if form.is_valid():
                c = form.save(commit=False); c.user = user; c.save()
                log_activity(user, 'cert_add', c.title)
            return redirect('portal_section', section='certs')

    from .forms import ProfileForm, SkillForm, ProjectForm, CertificateForm
    from .models import (CourseEnrollment, MarketOrder, Badge,
                         UserStreak, XPLog, AIChatSession)

    ctx = {
        'section':       section,
        'profile_form':  ProfileForm(instance=user),
        'skill_form':    SkillForm(),
        'project_form':  ProjectForm(),
        'cert_form':     CertificateForm(),
        'skills':        user.skills.all(),
        'projects':      user.projects.order_by('-created_at'),
        'certificates':  user.certificates.order_by('-issued_date'),
        'activities':    user.activities.all()[:20],
        'login_history': user.login_history.all()[:10],
        'notifs':        user.notifications.all()[:15],
        'enrollments':   CourseEnrollment.objects.filter(user=user).select_related('course'),
        'orders':        MarketOrder.objects.filter(user=user).select_related('item')[:10],
        'badges':        user.badges.all(),
        'ai_sessions':   AIChatSession.objects.filter(user=user)[:5],
        'mentor_requests': user.received_requests.filter(status='pending'),
    }
    try:
        ctx['streak'] = user.streak
    except Exception:
        ctx['streak'] = None
    ctx['total_xp'] = sum(x.amount for x in user.xp_logs.all())

    return render(request, 'portal/index.html', ctx)
