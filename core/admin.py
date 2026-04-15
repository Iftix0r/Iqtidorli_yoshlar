from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count
from .models import User, Skill, Project, Contest, Certificate, ContestApplication, Job, ProfileView, Course, Lesson, CourseEnrollment, CourseCertificate, LoginHistory, FailedLoginAttempt, ActivityLog


# ── INLINE lar ────────────────────────────────────────────────────────────────
class SkillInline(admin.TabularInline):
    model  = Skill
    extra  = 1
    fields = ('skill_name',)


class ProjectInline(admin.StackedInline):
    model       = Project
    extra       = 0
    fields      = ('title', 'description', 'link', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True


# ── USER ADMIN ────────────────────────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('avatar_preview', 'full_name', 'phone', 'role_badge',
                     'region', 'score_bar', 'is_active', 'date_joined')
    list_filter   = ('role', 'region', 'is_active', 'is_staff')
    search_fields = ('phone', 'first_name', 'last_name', 'username')
    ordering      = ('-score',)
    list_per_page = 25
    list_editable = ('is_active',)

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('username', 'phone', 'first_name', 'last_name', 'avatar')
        }),
        ('Platforma', {
            'fields': ('role', 'region', 'bio', 'score')
        }),
        ('Huquqlar', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Parol', {
            'fields': ('password',)
        }),
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
    inlines         = [SkillInline, ProjectInline]

    @admin.display(description='Rasm')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;"/>',
                obj.avatar.url
            )
        initial = (obj.get_full_name() or obj.phone or '?')[0].upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#6C63FF,#43E97B);'
            'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">{}</div>',
            initial
        )

    @admin.display(description='Ism Familiya')
    def full_name(self, obj):
        return obj.get_full_name() or obj.phone

    @admin.display(description='Rol')
    def role_badge(self, obj):
        colors = {
            'yosh':     '#6C63FF',
            'mentor':   '#43E97B',
            'investor': '#FF9A44',
        }
        color = colors.get(obj.role, '#aaa')
        return format_html(
            '<span style="background:{};color:white;padding:2px 10px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_role_display()
        )

    @admin.display(description='Ball')
    def score_bar(self, obj):
        pct = min(obj.score, 1000) / 10
        return format_html(
            '<div style="display:flex;align-items:center;gap:6px;">'
            '<div style="width:80px;height:8px;background:#eee;border-radius:4px;">'
            '<div style="width:{}%;height:100%;background:linear-gradient(90deg,#6C63FF,#43E97B);border-radius:4px;"></div>'
            '</div><span style="font-size:12px;">{}</span></div>',
            pct, obj.score
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('skills', 'projects')


# ── SKILL ADMIN ───────────────────────────────────────────────────────────────
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ('skill_name', 'user_link')
    search_fields = ('skill_name', 'user__first_name', 'user__last_name', 'user__phone')
    list_per_page = 30

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/core/user/{}/change/">{}</a>',
            obj.user.pk, obj.user
        )


# ── PROJECT ADMIN ─────────────────────────────────────────────────────────────
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user_link', 'link_btn', 'created_at')
    search_fields = ('title', 'user__first_name', 'user__last_name')
    list_filter   = ('created_at',)
    readonly_fields = ('created_at',)
    list_per_page = 20

    @admin.display(description='Muallif')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/core/user/{}/change/">{}</a>',
            obj.user.pk, obj.user
        )

    @admin.display(description='Havola')
    def link_btn(self, obj):
        if obj.link:
            return format_html('<a href="{}" target="_blank">Ko\'rish →</a>', obj.link)
        return '—'


# ── CONTEST ADMIN ─────────────────────────────────────────────────────────────
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display  = ('title', 'deadline_badge', 'prize', 'created_at')
    search_fields = ('title',)
    list_filter   = ('deadline',)
    readonly_fields = ('created_at',)
    list_per_page = 20
    ordering      = ('deadline',)

    fields = ('title', 'description', 'deadline', 'prize', 'created_at')

    @admin.display(description='Muddat')
    def deadline_badge(self, obj):
        if not obj.deadline:
            return '—'
        from django.utils import timezone
        today = timezone.now().date()
        diff  = (obj.deadline - today).days
        if diff < 0:
            color, label = '#DC2626', f'Tugagan ({obj.deadline})'
        elif diff <= 7:
            color, label = '#D97706', f'{obj.deadline} ({diff} kun)'
        else:
            color, label = '#059669', str(obj.deadline)
        return format_html(
            '<span style="color:{};">{}</span>', color, label
        )


# ── ADMIN SITE SOZLAMALARI ────────────────────────────────────────────────────
admin.site.site_header  = '⚡ Iqtidorli Yoshlar — Admin'
admin.site.site_title   = 'Iqtidorli Yoshlar'
admin.site.index_title  = 'Boshqaruv Paneli'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user', 'issuer', 'issued_date')
    search_fields = ('title', 'issuer', 'user__first_name')
    list_filter   = ('issued_date',)


@admin.register(ContestApplication)
class ContestApplicationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'contest', 'status', 'created_at')
    list_filter   = ('status', 'contest')
    list_editable = ('status',)
    search_fields = ('user__first_name', 'contest__title')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display  = ('title', 'company', 'job_type', 'location', 'is_active', 'created_at')
    list_filter   = ('job_type', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title', 'company')


# Admin index sahifasiga stats havolasi
from django.urls import reverse
from django.utils.html import format_html

original_index = admin.AdminSite.index

def custom_index(self, request, extra_context=None):
    extra_context = extra_context or {}
    extra_context['stats_url'] = '/admin/stats/'
    return original_index(self, request, extra_context)

admin.AdminSite.index = custom_index


class LessonInline(admin.TabularInline):
    from .models import Lesson
    model  = Lesson
    extra  = 1
    fields = ('order', 'title', 'video_url')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ('title', 'author', 'level', 'lesson_count', 'is_active', 'created_at')
    list_filter   = ('level', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('title',)
    inlines       = [LessonInline]

    @admin.display(description='Darslar')
    def lesson_count(self, obj):
        return obj.lessons.count()


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    list_display  = ('cert_number', 'user', 'course', 'issued_at')
    search_fields = ('cert_number', 'user__first_name', 'course__title')
    readonly_fields = ('cert_number', 'issued_at')


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'ip_address', 'device_info', 'is_success', 'created_at')
    list_filter   = ('is_success', 'device', 'os', 'browser')
    search_fields = ('user__first_name', 'user__phone', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'device', 'os', 'browser', 'is_success', 'created_at')
    ordering      = ('-created_at',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/core/user/{}/change/">{}</a>',
            obj.user.pk, obj.user
        )

    @admin.display(description='Qurilma')
    def device_info(self, obj):
        icon = {'Mobil': '📱', 'Planshet': '📟', 'Kompyuter': '💻'}.get(obj.device, '❓')
        color = '#43E97B' if obj.is_success else '#FF6584'
        return format_html(
            '<span style="color:{};">{} {} · {} · {}</span>',
            color, icon, obj.device, obj.os, obj.browser
        )


@admin.register(FailedLoginAttempt)
class FailedLoginAttemptAdmin(admin.ModelAdmin):
    list_display  = ('phone', 'ip_address', 'attempts', 'blocked_until', 'last_attempt')
    list_filter   = ('last_attempt',)
    search_fields = ('phone', 'ip_address')
    actions       = ['unblock_selected']

    @admin.action(description='Blokdan chiqarish')
    def unblock_selected(self, request, queryset):
        queryset.delete()
        self.message_user(request, "Tanlangan IP lar blokdan chiqarildi.")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ('user_link', 'action_badge', 'detail', 'created_at')
    list_filter   = ('action', 'created_at')
    search_fields = ('user__first_name', 'user__phone', 'detail')
    readonly_fields = ('user', 'action', 'detail', 'link', 'created_at')
    ordering      = ('-created_at',)
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    @admin.display(description='Foydalanuvchi')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/core/user/{}/change/">{}</a>',
            obj.user.pk, obj.user
        )

    @admin.display(description='Amal')
    def action_badge(self, obj):
        colors = {
            'login': '#43E97B', 'logout': '#A7A9BE',
            'register': '#6C63FF', 'profile_edit': '#4FACFE',
            'skill_add': '#FFD700', 'project_add': '#6C63FF',
            'cert_add': '#43E97B', 'contest_apply': '#FF9A44',
            'msg_send': '#38F9D7', 'course_done': '#43E97B',
        }
        color = colors.get(obj.action, '#A7A9BE')
        return format_html(
            '<span style="background:{};color:white;padding:2px 10px;border-radius:10px;font-size:11px;">{}</span>',
            color, obj.get_action_display()
        )
