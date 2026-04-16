from django.contrib.auth.models import AbstractUser
from django.db import models
from .utils import uuid_path_gen


ROLE_CHOICES = [
    ('yosh',     'Iqtidorli Yosh'),
    ('mentor',   'Mentor'),
    ('investor', 'Investor'),
]

REGIONS = [
    ('Toshkent shahri',       'Toshkent shahri'),
    ('Toshkent viloyati',     'Toshkent viloyati'),
    ('Andijon viloyati',      'Andijon viloyati'),
    ("Farg'ona viloyati",     "Farg'ona viloyati"),
    ('Namangan viloyati',     'Namangan viloyati'),
    ('Samarqand viloyati',    'Samarqand viloyati'),
    ('Buxoro viloyati',       'Buxoro viloyati'),
    ('Navoiy viloyati',       'Navoiy viloyati'),
    ('Qashqadaryo viloyati',  'Qashqadaryo viloyati'),
    ('Surxondaryo viloyati',  'Surxondaryo viloyati'),
    ('Jizzax viloyati',       'Jizzax viloyati'),
    ('Sirdaryo viloyati',     'Sirdaryo viloyati'),
    ('Xorazm viloyati',       'Xorazm viloyati'),
    ("Qoraqalpog'iston",      "Qoraqalpog'iston Respublikasi"),
]


class User(AbstractUser):
    phone  = models.CharField(max_length=20, unique=True, verbose_name='Telefon raqam')
    role   = models.CharField(max_length=20, choices=ROLE_CHOICES, default='yosh')
    region = models.CharField(max_length=100, choices=REGIONS, blank=True)
    bio    = models.CharField(max_length=200, blank=True)
    score  = models.PositiveIntegerField(default=0)
    avatar = models.ImageField(upload_to=uuid_path_gen, blank=True, null=True)
    email  = models.EmailField(blank=True)

    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.get_full_name() or self.phone

    def initial(self):
        name = self.get_full_name() or self.phone
        return name[0].upper() if name else '?'

    def unread_notifications(self):
        return self.notifications.filter(is_read=False).count()

    def unread_messages(self):
        return self.received_messages.filter(is_read=False).count()


class Skill(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=80)

    def __str__(self):
        return self.skill_name


class Project(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    link        = models.URLField(blank=True)
    image       = models.ImageField(upload_to='projects/', blank=True, null=True)
    is_startup  = models.BooleanField(default=False, verbose_name="Startapmi?")
    needs_team  = models.BooleanField(default=False, verbose_name="Jamoa kerakmi?")
    STATUS = [
        ('idea',    'G\'oya bosqichi'),
        ('funding', 'Mablag\' yig\'ilmoqda (Crowdfunding)'),
        ('dev',     'Amalga oshirilmoqda (Development)'),
        ('active',  'Ishga tushirilgan (Launched)'),
        ('profit',  'Foydada (Profitable)'),
        ('failed',  'Zararda/To\'xtatilgan'),
    ]
    funding_goal      = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Maqsad qilingan summa")
    funding_collected = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Yig'ilgan summa")
    status            = models.CharField(max_length=20, choices=STATUS, default='idea')
    required_resources = models.TextField(blank=True, verbose_name="Nimalar kerak? (uskunalar, ofis, va h.k.)")
    
    video_url   = models.URLField(blank=True, verbose_name="Video havola (YouTube/Vimeo)")
    is_public   = models.BooleanField(default=True, verbose_name="Ommaviy ko'rinsinmi?")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def funding_percentage(self):
        if not self.funding_goal or self.funding_goal == 0:
            return 0
        return min(int((self.funding_collected / self.funding_goal) * 100), 100)

    def get_status_color(self):
        colors = {
            'idea': '#71717a', 'funding': '#6C63FF', 'dev': '#f59e0b',
            'active': '#10b981', 'profit': '#34d399', 'failed': '#ef4444'
        }
        return colors.get(self.status, '#71717a')


class ProjectMaterial(models.Model):
    TYPES = [
        ('image', 'Rasm'),
        ('video', 'Video'),
        ('file',  'Hujjat/Fayl'),
    ]
    project    = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='materials')
    title      = models.CharField(max_length=100, blank=True)
    file       = models.FileField(upload_to='project_materials/', blank=True, null=True)
    link       = models.URLField(blank=True, verbose_name="Tashqi havola")
    mat_type   = models.CharField(max_length=10, choices=TYPES, default='image')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} — {self.mat_type}"


class Contest(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline    = models.DateField(null=True, blank=True)
    prize       = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MentorRequest(models.Model):
    STATUS = [
        ('pending',  'Kutilmoqda'),
        ('accepted', 'Qabul qilindi'),
        ('rejected', 'Rad etildi'),
    ]
    sender    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    message   = models.TextField(blank=True)
    status    = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"


class Message(models.Model):
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body       = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.body[:40]}"


class Notification(models.Model):
    TYPES = [
        ('mentor_req',  'Mentor so\'rovi'),
        ('msg',         'Yangi xabar'),
        ('contest',     'Yangi tanlov'),
        ('score',       'Ball yangilandi'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=TYPES)
    text       = models.CharField(max_length=300)
    link       = models.CharField(max_length=200, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user}: {self.text[:50]}"


class Resource(models.Model):
    TYPES = [
        ('course',  'Kurs'),
        ('book',    'Kitob'),
        ('video',   'Video'),
        ('article', 'Maqola'),
    ]
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    link        = models.URLField()
    res_type    = models.CharField(max_length=20, choices=TYPES, default='course')
    added_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Certificate(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    title       = models.CharField(max_length=200)
    issuer      = models.CharField(max_length=100, blank=True, verbose_name="Beruvchi tashkilot")
    issued_date = models.DateField(null=True, blank=True)
    image       = models.ImageField(upload_to=uuid_path_gen, blank=True, null=True)
    link        = models.URLField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} — {self.title}"


class ContestApplication(models.Model):
    STATUS = [
        ('pending',   'Ko\'rib chiqilmoqda'),
        ('accepted',  'Qabul qilindi'),
        ('rejected',  'Rad etildi'),
    ]
    contest    = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='applications')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    motivation = models.TextField(blank=True, verbose_name="Motivatsiya xati")
    status     = models.CharField(max_length=20, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return f"{self.user} → {self.contest}"


class Job(models.Model):
    TYPES = [
        ('full',     'To\'liq stavka'),
        ('part',     'Yarim stavka'),
        ('remote',   'Masofaviy'),
        ('intern',   'Amaliyot'),
        ('freelance','Frilanser'),
    ]
    posted_by   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title       = models.CharField(max_length=200)
    company     = models.CharField(max_length=100)
    description = models.TextField()
    job_type    = models.CharField(max_length=20, choices=TYPES, default='full')
    location    = models.CharField(max_length=100, blank=True)
    salary      = models.CharField(max_length=80, blank=True)
    skills_req  = models.CharField(max_length=300, blank=True, verbose_name="Talab qilinadigan ko'nikmalar")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — {self.company}"


class ProfileView(models.Model):
    """Profil ko'rishlar soni"""
    profile    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profile_views')
    viewer_ip  = models.GenericIPAddressField(null=True, blank=True)
    viewed_at  = models.DateTimeField(auto_now_add=True)


# ── KURS TIZIMI ───────────────────────────────────────────────────────────────
class Course(models.Model):
    LEVELS = [
        ('beginner',     'Boshlang\'ich'),
        ('intermediate', 'O\'rta'),
        ('advanced',     'Yuqori'),
    ]
    title       = models.CharField(max_length=200)
    description = models.TextField()
    cover       = models.ImageField(upload_to=uuid_path_gen, blank=True, null=True)
    author      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_courses')
    level       = models.CharField(max_length=20, choices=LEVELS, default='beginner')
    duration    = models.CharField(max_length=50, blank=True, help_text="Masalan: 4 soat")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def lesson_count(self):
        return self.lessons.count()

    def is_enrolled(self, user):
        return self.enrollments.filter(user=user).exists()

    def progress(self, user):
        total = self.lessons.count()
        if not total:
            return 0
        done = LessonProgress.objects.filter(
            lesson__course=self, user=user, completed=True
        ).count()
        return int(done / total * 100)


class Lesson(models.Model):
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title      = models.CharField(max_length=200)
    content    = models.TextField(blank=True)
    video_url  = models.URLField(blank=True, help_text="YouTube yoki boshqa video havolasi")
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class CourseEnrollment(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed   = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} → {self.course}"


class LessonProgress(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson     = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    completed  = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')


class CourseCertificate(models.Model):
    """Kurs tugaganda avtomatik beriladigan sertifikat"""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_certificates')
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at   = models.DateTimeField(auto_now_add=True)
    cert_number = models.CharField(max_length=20, unique=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} — {self.course} sertifikati"


# ── LOGIN TARIXI VA XAVFSIZLIK ────────────────────────────────────────────────
class LoginHistory(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    device      = models.CharField(max_length=100, blank=True)
    os          = models.CharField(max_length=100, blank=True)
    browser     = models.CharField(max_length=100, blank=True)
    location    = models.CharField(max_length=200, blank=True)
    is_success  = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.ip_address} — {self.created_at:%d.%m.%Y %H:%M}"


class FailedLoginAttempt(models.Model):
    """Muvaffaqiyatsiz kirish urinishlari"""
    phone      = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    attempts   = models.PositiveIntegerField(default=1)
    blocked_until = models.DateTimeField(null=True, blank=True)
    last_attempt  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('phone', 'ip_address')

    def is_blocked(self):
        from django.utils import timezone
        if self.blocked_until and self.blocked_until > timezone.now():
            return True
        return False


class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('register',     'Ro\'yxatdan o\'tdi'),
        ('login',        'Tizimga kirdi'),
        ('logout',       'Tizimdan chiqdi'),
        ('profile_edit', 'Profilni tahrirladi'),
        ('skill_add',    'Ko\'nikma qo\'shdi'),
        ('project_add',  'Loyiha qo\'shdi'),
        ('cert_add',     'Sertifikat qo\'shdi'),
        ('contest_apply','Tanlovga ariza topshirdi'),
        ('msg_send',     'Xabar yubordi'),
        ('mentor_req',   'Mentor so\'rovi yubordi'),
        ('course_enroll','Kursga yozildi'),
        ('course_done',  'Kursni tugatdi'),
        ('job_post',     'Ish e\'loni joyladi'),
        ('resource_add', 'Resurs qo\'shdi'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action     = models.CharField(max_length=30, choices=ACTION_TYPES)
    detail     = models.CharField(max_length=300, blank=True)
    link       = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.get_action_display()}"


class SiteSettings(models.Model):
    """Sayt sozlamalari — faqat bitta yozuv bo'ladi"""
    site_name    = models.CharField(max_length=100, default='Iqtidorli Yoshlar')
    site_desc    = models.TextField(blank=True)
    contact_phone= models.CharField(max_length=20, blank=True)
    contact_email= models.EmailField(blank=True)
    telegram     = models.CharField(max_length=100, blank=True)
    instagram    = models.CharField(max_length=100, blank=True)
    maintenance  = models.BooleanField(default=False, verbose_name='Texnik ishlar rejimi')
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sayt Sozlamalari'

    def __str__(self):
        return self.site_name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SystemError(models.Model):
    """500 xatolarni saqlash"""
    path       = models.CharField(max_length=300)
    method     = models.CharField(max_length=10)
    error_type = models.CharField(max_length=200)
    message    = models.TextField()
    traceback  = models.TextField(blank=True)
    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.error_type} — {self.path}"


class TwoFactorCode(models.Model):
    """Telegram orqali 2FA kodlari"""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tfa_codes')
    code       = models.CharField(max_length=6)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.user} — {self.code}"


# ── GAMIFICATION ──────────────────────────────────────────────────────────────

BADGE_DEFINITIONS = {
    # Ro'yxatdan o'tish
    'first_login':      {'name': "Birinchi Qadam",      'icon': '🚀', 'desc': "Platformaga kirdi",                  'xp': 10},
    'profile_complete': {'name': "To'liq Profil",        'icon': '✅', 'desc': "Profilni to'liq to'ldirdi",          'xp': 20},
    # Loyihalar
    'first_project':    {'name': "Birinchi Loyiha",      'icon': '💡', 'desc': "Birinchi loyihasini qo'shdi",        'xp': 30},
    'five_projects':    {'name': "Loyiha Ustasi",        'icon': '🏗️', 'desc': "5 ta loyiha qo'shdi",               'xp': 50},
    # Ko'nikmalar
    'five_skills':      {'name': "Ko'p Qirrali",         'icon': '⚡', 'desc': "5 ta ko'nikma qo'shdi",             'xp': 20},
    # Kurslar
    'first_course':     {'name': "O'quvchi",             'icon': '📚', 'desc': "Birinchi kursni tugatdi",            'xp': 50},
    'three_courses':    {'name': "Bilim Izlovchi",       'icon': '🎓', 'desc': "3 ta kursni tugatdi",               'xp': 100},
    # Tanlovlar
    'first_contest':    {'name': "Jangchi",              'icon': '⚔️', 'desc': "Birinchi tanlovga ariza topshirdi", 'xp': 30},
    'contest_winner':   {'name': "G'olib",               'icon': '🏆', 'desc': "Tanlov g'olibi",                    'xp': 200},
    # Streak
    'streak_3':         {'name': "Izchil",               'icon': '🔥', 'desc': "3 kun ketma-ket kirdi",             'xp': 15},
    'streak_7':         {'name': "Haftalik Chempion",    'icon': '🔥🔥', 'desc': "7 kun ketma-ket kirdi",           'xp': 50},
    'streak_30':        {'name': "Oylik Qahramon",       'icon': '💎', 'desc': "30 kun ketma-ket kirdi",            'xp': 200},
    # Ijtimoiy
    'first_mentor_req': {'name': "Muloqotchi",           'icon': '🤝', 'desc': "Birinchi mentor so'rovi yubordi",   'xp': 20},
    'first_message':    {'name': "Suhbatdosh",           'icon': '💬', 'desc': "Birinchi xabar yubordi",            'xp': 10},
    # Reyting
    'top_10':           {'name': "Top 10",               'icon': '🌟', 'desc': "Reytingda top 10 ga kirdi",         'xp': 100},
    'top_1':            {'name': "Eng Yaxshi",           'icon': '👑', 'desc': "Reytingda 1-o'rin",                 'xp': 500},
}


class Badge(models.Model):
    """Foydalanuvchiga berilgan nishonlar"""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge_key  = models.CharField(max_length=50)
    earned_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge_key')
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user} — {self.badge_key}"

    @property
    def info(self):
        return BADGE_DEFINITIONS.get(self.badge_key, {
            'name': self.badge_key, 'icon': '🎖️', 'desc': '', 'xp': 0
        })


class UserStreak(models.Model):
    """Kunlik kirish streak tizimi"""
    user           = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)
    total_days     = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user} — {self.current_streak} kun"

    def update(self):
        from django.utils import timezone
        today = timezone.now().date()
        if self.last_login_date == today:
            return  # Bugun allaqachon hisoblangan
        if self.last_login_date and (today - self.last_login_date).days == 1:
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.total_days += 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.last_login_date = today
        self.save()


class XPLog(models.Model):
    """XP (tajriba ballari) tarixi"""
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_logs')
    amount    = models.IntegerField()  # manfiy bo'lishi mumkin
    reason    = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} +{self.amount} XP — {self.reason}"


# ── AI CHAT TARIXI ────────────────────────────────────────────────────────────

AI_MODES = [
    ('general',   '✨ Iqtidor AI'),
    ('mentor',    '🎯 Mentor Rejimi'),
    ('talent',    '🧠 Iqtidor Tahlili'),
    ('portfolio', '📋 Portfolio Baholash'),
    ('matching',  '🤝 Smart Matching'),
]


class AIChatSession(models.Model):
    """Har bir suhbat sessiyasi"""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    mode       = models.CharField(max_length=20, choices=AI_MODES, default='general')
    title      = models.CharField(max_length=200, blank=True)
    is_shared  = models.BooleanField(default=False)
    share_token = models.CharField(max_length=32, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} — {self.mode} — {self.title or self.created_at:%d.%m.%Y}"


class AIChatMessage(models.Model):
    """Suhbat xabarlari"""
    ROLES = [('user', 'Foydalanuvchi'), ('assistant', 'AI')]
    session    = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name='messages')
    role       = models.CharField(max_length=10, choices=ROLES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"


# ── IQTIDOR MARKET ────────────────────────────────────────────────────────────

class MarketItem(models.Model):
    CATEGORIES = [
        ('certificate', '📜 Sertifikat'),
        ('mentoring',   '👨‍🏫 Mentoring Sessiyasi'),
        ('course',      '🎓 Kurs Kirish'),
        ('badge',       '🏅 Maxsus Nishon'),
        ('gift',        '🎁 Sovg\'a'),
        ('other',       '✨ Boshqa'),
    ]
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to=uuid_path_gen, blank=True, null=True)
    category    = models.CharField(max_length=20, choices=CATEGORIES, default='gift')
    price       = models.PositiveIntegerField(help_text="Ball narxi")
    stock       = models.IntegerField(default=-1, help_text="-1 = cheksiz")
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.title} ({self.price} ball)"

    def in_stock(self):
        return self.stock == -1 or self.stock > 0


class MarketOrder(models.Model):
    STATUS = [
        ('pending',   '⏳ Kutilmoqda'),
        ('approved',  '✅ Tasdiqlandi'),
        ('rejected',  '❌ Rad etildi'),
        ('delivered', '🎁 Yetkazildi'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='market_orders')
    item       = models.ForeignKey(MarketItem, on_delete=models.CASCADE, related_name='orders')
    price_paid = models.PositiveIntegerField()
    status     = models.CharField(max_length=20, choices=STATUS, default='pending')
    note       = models.TextField(blank=True, help_text="Admin izohi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.item} ({self.status})"

# AIChatSession ga share imkoniyati (migration kerak)
# AIChatSession.is_shared va share_token maydonlari
# core/migrations da yangi migration yaratiladi