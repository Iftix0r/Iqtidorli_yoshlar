from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.utils import timezone
from .models import (
    User, Skill, Project, Contest, Certificate, ContestApplication,
    Job, Course, Lesson, CourseEnrollment, CourseCertificate,
    LoginHistory, FailedLoginAttempt, ActivityLog, Resource,
    MentorRequest, Message, Notification,
    Badge, UserStreak, XPLog,
    AIChatSession, AIChatMessage,
    BADGE_DEFINITIONS,
)

# ── ADMIN SITE ────────────────────────────────────────────────────────────────
admin.site.site_header = '✨ Iqtidorli Yoshlar'
admin.site.site_title  = 'Iqtidorli Yoshlar Admin'
admin.site.index_title = 'Boshqaruv Paneli'


# ── INLINES ───────────────────────────────────────────────────────────────────
class SkillInline(admin.TabularInline):
    model  = Skill
    extra  = 1
    fields = ('skill_name',)


class ProjectInline(admin.StackedInline):
    model            = Project
    extra            = 0
    fields           = ('title', 'description', 'link')
    show_change_link = True


class BadgeInline(admin.TabularInline):
    model     = Badge
    extra     = 0
    fields    = ('badge_key', 'badge_icon', 'earned_at')
    readonly_fields = ('badge_icon', 'earned_at')

    @admin.display(description='Nishon')
    def badge_icon(self, obj):
        info = BADGE_DEFINITIONS.get(obj.badge_key, {})
        return format_html('{} {}', info.get('icon', '🎖️'), info.get('name', obj.badge_key))


class XPLogInline(admin.TabularInline):
    model     = XPLog
    extra     = 0
    fields    = ('amount', 'reason', 'created_at')
    readonly_fields = ('amount', 'reason', 'created_at')
    max_num   = 10
    can_delete = False


# ── USER ADMIN ────────────────────────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('avatar_preview', 'full_name', 'phone', 'role_badge',
                     'region', 'score_bar', 'badge_count', 'streak_days',
                     'is_active', 'date_joined')
    list_filter   = ('role', 'region', 'is_active', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name', 'username')
    ordering      = ('-score',)
    list_per_page = 25
    list_editable = ('is_active',)

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('username', 'phone', 'first_name', 'last_name', 'email', 'avatar')
        }),
        ('Platforma', {
            'fields': ('role', 'region', 'bio', 'score')
        }),
        ('Huquqlar', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Parol', {'fields': ('password',)}),
        ('Sanalar', {
            'classes': ('collapse',),
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'username', 'first_name', 'last_name',
                       'role', 'region', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('last_login', 'date_joined')
    inlines = [SkillInline, ProjectInline, BadgeInline, XPLogInline]

    @admin.display(description='')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;"/>',
                obj.avatar.url
            )
        initial = (obj.get_full_name() or obj.phone or '?')[0].upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6C63FF,#43E97B);'
            'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:14px;">{}</div>',
            initial
        )

    @admin.display(description='Ism')
    def full_name(self, obj):
        return obj.get_full_name() or obj.phone

    @admin.display(description='Rol')
    def role_badge(self, obj):
        colors = {'yosh': '#6C63FF', 'mentor': '#43E97B', 'investor': '#FF9A44'}
        color  = colors.get(obj.role, '#aaa')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_role_display()
        )

    @admin.display(description='Ball')
    def score_bar(self, obj):
        pct = min(obj.score, 1000) / 10
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:70px;height:6px;background:#eee;border-radius:3px;">'
            '<div style="width:{}%;height:100%;background:linear-gradient(90deg,#6C63FF,#43E97B);border-radius:3px;"></div>'
            '</div><b style="font-size:12px;">{}</b></div>',
            pct, obj.score
        )

    @admin.display(description='🎖️')
    def badge_count(self, obj):
        c = obj.badges.count()
        return format_html('<span style="color:#FFD700;font-weight:700;">{}</span>', c) if c else '—'

    @admin.display(description='🔥')
    def streak_days(self, obj):
        try:
            return format_html('<span style="color:#FF6432;font-weight:700;">{}🔥</span>', obj.streak.current_streak)
        except Exception:
            return '—'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('skills', 'badges').select_related('streak')


# ── BADGE ADMIN ───────────────────────────────────────────────────────────────
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display  = ('badge_display', 'user_link', 'earned_at')
    list_filter   = ('badge_key',)
    search_fields = ('user__first_name', 'user__phone', 'badge_key')
    readonly_fields = ('earned_at',)
    list_per_page = 50

    @admin.display(description='Nishon')
    def badge_display(self, obj):
        info = BADGE_DEFINITIONS.get(obj.badge_key, {})
        return format_html(
            '<span style="font-size:1.1rem;">{}</span> <b>{}</b>',
            info.get('icon', '🎖️'), info.get('name', obj.badge_key)
        )

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user)


# ── STREAK ADMIN ──────────────────────────────────────────────────────────────
@admin.register(UserStreak)
class UserStreakAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'streak_display', 'longest_streak', 'total_days', 'last_login_date')
    search_fields = ('user__first_name', 'user__phone')
    ordering      = ('-current_streak',)
    list_per_page = 50
    readonly_fields = ('user', 'current_streak', 'longest_streak', 'total_days', 'last_login_date')

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user)

    @admin.display(description='Joriy Streak')
    def streak_display(self, obj):
        return format_html('<span style="color:#FF6432;font-weight:700;font-size:1rem;">🔥 {}</span>', obj.current_streak)


# ── XP LOG ADMIN ──────────────────────────────────────────────────────────────
@admin.register(XPLog)
class XPLogAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'amount_display', 'reason', 'created_at')
    search_fields = ('user__first_name', 'user__phone', 'reason')
    list_filter   = ('created_at',)
    ordering      = ('-created_at',)
    list_per_page = 50
    readonly_fields = ('user', 'amount', 'reason', 'created_at')

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user)

    @admin.display(description='XP')
    def amount_display(self, obj):
        color = '#43E97B' if obj.amount > 0 else '#FF6584'
        return format_html('<b style="color:{};">+{} XP</b>', color, obj.amount)


# ── AI CHAT ADMIN ─────────────────────────────────────────────────────────────
class AIChatMessageInline(admin.TabularInline):
    model     = AIChatMessage
    extra     = 0
    fields    = ('role', 'content_preview', 'created_at')
    readonly_fields = ('role', 'content_preview', 'created_at')
    can_delete = False
    max_num   = 20

    @admin.display(description='Xabar')
    def content_preview(self, obj):
        return obj.content[:100] + ('...' if len(obj.content) > 100 else '')


@admin.register(AIChatSession)
class AIChatSessionAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'mode_badge', 'title_short', 'msg_count', 'updated_at')
    list_filter   = ('mode', 'created_at')
    search_fields = ('user__first_name', 'user__phone', 'title')
    ordering      = ('-updated_at',)
    list_per_page = 30
    readonly_fields = ('user', 'mode', 'title', 'created_at', 'updated_at')
    inlines       = [AIChatMessageInline]

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user)

    @admin.display(description='Rejim')
    def mode_badge(self, obj):
        colors = {
            'general': '#6C63FF', 'mentor': '#43E97B',
            'talent': '#FF9A44', 'portfolio': '#4FACFE', 'matching': '#F093FB'
        }
        color = colors.get(obj.mode, '#aaa')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;font-size:11px;">{}</span>',
            color, obj.get_mode_display()
        )

    @admin.display(description='Sarlavha')
    def title_short(self, obj):
        return obj.title[:50] or '—'

    @admin.display(description='Xabarlar')
    def msg_count(self, obj):
        return obj.messages.count()


# ── CONTEST ADMIN ─────────────────────────────────────────────────────────────
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display  = ('title', 'deadline_badge', 'prize', 'app_count', 'created_at')
    search_fields = ('title',)
    list_filter   = ('deadline',)
    readonly_fields = ('created_at',)
    ordering      = ('deadline',)

    @admin.display(description='Muddat')
    def deadline_badge(self, obj):
        if not obj.deadline:
            return '—'
        today = timezone.now().date()
        diff  = (obj.deadline - today).days
        if diff < 0:
            color = '#DC2626'
        elif diff <= 7:
            color = '#D97706'
        else:
            color = '#059669'
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, obj.deadline)

    @admin.display(description='Arizalar')
    def app_count(self, obj):
        return obj.applications.count()


@admin.register(ContestApplication)
class ContestApplicationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'contest', 'status_badge', 'created_at')
    list_filter   = ('status', 'contest')
    list_editable = ('status',)
    search_fields = ('user__first_name', 'contest__title')

    @admin.display(description='Holat')
    def status_badge(self, obj):
        colors = {'pending': '#D97706', 'accepted': '#059669', 'rejected': '#DC2626'}
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colors.get(obj.status, '#aaa'), obj.get_status_display()
        )


# ── COURSE ADMIN ──────────────────────────────────────────────────────────────
class LessonInline(admin.TabularInline):
    model  = Lesson
    extra  = 1
    fields = ('order', 'title', 'video_url')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ('title', 'author', 'level_badge', 'lesson_count', 'enroll_count', 'is_active', 'created_at')
    list_filter   = ('level', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title',)
    inlines       = [LessonInline]

    @admin.display(description='Daraja')
    def level_badge(self, obj):
        colors = {'beginner': '#43E97B', 'intermediate': '#FF9A44', 'advanced': '#FF6584'}
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colors.get(obj.level, '#aaa'), obj.get_level_display()
        )

    @admin.display(description='Darslar')
    def lesson_count(self, obj):
        return obj.lessons.count()

    @admin.display(description="Yozilganlar")
    def enroll_count(self, obj):
        return obj.enrollments.count()


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    list_display  = ('cert_number', 'user', 'course', 'issued_at')
    search_fields = ('cert_number', 'user__first_name', 'course__title')
    readonly_fields = ('cert_number', 'issued_at')


# ── LOGIN TARIXI ──────────────────────────────────────────────────────────────
@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'ip_address', 'device_info', 'status_badge', 'created_at')
    list_filter   = ('is_success', 'device', 'os')
    search_fields = ('user__first_name', 'user__phone', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'device', 'os', 'browser', 'is_success', 'created_at')
    ordering      = ('-created_at',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user)

    @admin.display(description='Qurilma')
    def device_info(self, obj):
        icon = {'Mobil': '📱', 'Planshet': '📟', 'Kompyuter': '💻'}.get(obj.device, '❓')
        return format_html('{} {} · {}', icon, obj.os, obj.browser)

    @admin.display(description='Holat')
    def status_badge(self, obj):
        if obj.is_success:
            return format_html('<span style="color:#43E97B;font-weight:700;">✓ Muvaffaqiyatli</span>')
        return format_html('<span style="color:#FF6584;font-weight:700;">✗ Xato</span>')


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    list_display  = ('phone', 'ip_address', 'attempts', 'blocked_until', 'last_attempt')
    search_fields = ('phone', 'ip_address')
    actions       = ['unblock_selected']

    @admin.action(description='Blokdan chiqarish')
    def unblock_selected(self, request, queryset):
        queryset.delete()
        self.message_user(request, "Blokdan chiqarildi.")


# ── ACTIVITY LOG ──────────────────────────────────────────────────────────────
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'action_badge', 'detail', 'ip_address', 'created_at')
    list_filter   = ('action', 'created_at')
    search_fields = ('user__first_name', 'user__phone', 'detail')
    readonly_fields = ('user', 'action', 'detail', 'link', 'ip_address', 'created_at')
    ordering      = ('-created_at',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user)

    @admin.display(description='Amal')
    def action_badge(self, obj):
        colors = {
            'login': '#43E97B', 'logout': '#A7A9BE', 'register': '#6C63FF',
            'profile_edit': '#4FACFE', 'skill_add': '#FFD700',
            'project_add': '#6C63FF', 'cert_add': '#43E97B',
            'contest_apply': '#FF9A44', 'msg_send': '#38F9D7',
            'course_done': '#43E97B', 'job_post': '#F093FB',
        }
        color = colors.get(obj.action, '#A7A9BE')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:20px;font-size:11px;">{}</span>',
            color, obj.get_action_display()
        )


# ── QOLGAN MODELLAR ───────────────────────────────────────────────────────────
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display  = ('title', 'company', 'job_type', 'location', 'is_active', 'created_at')
    list_filter   = ('job_type', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title', 'company')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display  = ('title', 'res_type', 'added_by', 'created_at')
    list_filter   = ('res_type',)
    search_fields = ('title',)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user', 'issuer', 'issued_date')
    search_fields = ('title', 'issuer', 'user__first_name')


@admin.register(MentorRequest)
class MentorRequestAdmin(admin.ModelAdmin):
    list_display  = ('sender', 'receiver', 'status_badge', 'created_at')
    list_filter   = ('status',)
    list_editable = ('status',)
    search_fields = ('sender__first_name', 'receiver__first_name')

    @admin.display(description='Holat')
    def status_badge(self, obj):
        colors = {'pending': '#D97706', 'accepted': '#059669', 'rejected': '#DC2626'}
        return format_html(
            '<span style="color:{};font-weight:600;">{}</span>',
            colors.get(obj.status, '#aaa'), obj.get_status_display()
        )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'notif_type', 'text_short', 'is_read', 'created_at')
    list_filter   = ('notif_type', 'is_read')
    search_fields = ('user__first_name', 'text')
    list_editable = ('is_read',)

    @admin.display(description='Matn')
    def text_short(self, obj):
        return obj.text[:60]
