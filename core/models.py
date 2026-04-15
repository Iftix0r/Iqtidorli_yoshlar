from django.contrib.auth.models import AbstractUser
from django.db import models


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
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
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
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


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
    image       = models.ImageField(upload_to='certificates/', blank=True, null=True)
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
    cover       = models.ImageField(upload_to='courses/', blank=True, null=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.get_action_display()}"
