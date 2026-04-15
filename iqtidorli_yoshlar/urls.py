from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

ADMIN_URL = getattr(settings, 'ADMIN_URL', 'admin')
PANEL_URL = getattr(settings, 'PANEL_URL', 'panel')
TIZIM_URL = getattr(settings, 'TIZIM_URL', 'tizim')


@staff_member_required
def admin_stats(request):
    from core.models import User, Project, Contest, Skill, LoginHistory
    from django.db.models import Count
    ctx = {
        'total_users':     User.objects.count(),
        'total_yoshlar':   User.objects.filter(role='yosh').count(),
        'total_mentors':   User.objects.filter(role='mentor').count(),
        'total_investors': User.objects.filter(role='investor').count(),
        'total_projects':  Project.objects.count(),
        'total_contests':  Contest.objects.count(),
        'total_skills':    Skill.objects.count(),
        'top_users':       User.objects.order_by('-score')[:10],
        'by_region':       User.objects.filter(role='yosh').exclude(region='')
                               .values('region').annotate(cnt=Count('id')).order_by('-cnt')[:14],
        'recent_users':    User.objects.order_by('-date_joined')[:8],
        'recent_logins':   LoginHistory.objects.select_related('user').order_by('-created_at')[:20],
        'failed_logins':   LoginHistory.objects.filter(is_success=False).count(),
        'today_logins':    LoginHistory.objects.filter(is_success=True).count(),
    }
    return render(request, 'admin/stats.html', ctx)


from core import panel_views, system_views, tfa_views

urlpatterns = [
    path(f'{ADMIN_URL}/stats/', admin_stats,       name='admin_stats'),
    path(f'{ADMIN_URL}/',       admin.site.urls),

    # Custom Admin Panel
    path(f'{PANEL_URL}/',                              panel_views.dashboard,               name='panel_dashboard'),
    path(f'{PANEL_URL}/users/',                        panel_views.users_view,              name='panel_users'),
    path(f'{PANEL_URL}/users/create/',                 panel_views.user_create_view,        name='panel_user_create'),
    path(f'{PANEL_URL}/users/<int:pk>/',               panel_views.user_detail_view,        name='panel_user_detail'),
    path(f'{PANEL_URL}/users/<int:pk>/edit/',          panel_views.user_edit_view,          name='panel_user_edit'),
    path(f'{PANEL_URL}/users/<int:pk>/delete/',        panel_views.user_delete_view,        name='panel_user_delete'),
    path(f'{PANEL_URL}/activities/',                   panel_views.activities_view,         name='panel_activities'),
    path(f'{PANEL_URL}/logins/',                       panel_views.logins_view,             name='panel_logins'),
    path(f'{PANEL_URL}/contests/',                     panel_views.contests_view,           name='panel_contests'),
    path(f'{PANEL_URL}/applications/',                 panel_views.applications_view,       name='panel_applications'),
    path(f'{PANEL_URL}/courses/',                      panel_views.courses_view,            name='panel_courses'),
    path(f'{PANEL_URL}/courses/create/',               panel_views.course_create_view,      name='panel_course_create'),
    path(f'{PANEL_URL}/courses/<int:pk>/lessons/',     panel_views.course_lessons_view,     name='panel_course_lessons'),
    path(f'{PANEL_URL}/jobs/',                         panel_views.jobs_view,               name='panel_jobs'),
    path(f'{PANEL_URL}/resources/',                    panel_views.resources_view,          name='panel_resources'),
    path(f'{PANEL_URL}/messages/',                     panel_views.messages_view,           name='panel_messages'),
    path(f'{PANEL_URL}/mentor-requests/',              panel_views.mentor_requests_view,    name='panel_mentor_requests'),
    path(f'{PANEL_URL}/broadcast/',                    panel_views.broadcast_view,          name='panel_broadcast'),
    path(f'{PANEL_URL}/notifications/',                panel_views.notifications_panel_view,name='panel_notifications'),
    path(f'{PANEL_URL}/notif-list/',                   panel_views.notif_list_api,          name='panel_notif_list'),
    path(f'{PANEL_URL}/stats-api/',                    panel_views.stats_api,               name='panel_stats_api'),
    path(f'{PANEL_URL}/realtime/',                     panel_views.realtime_api,            name='panel_realtime'),
    path(f'{PANEL_URL}/settings/',                     panel_views.settings_view,           name='panel_settings'),
    path(f'{PANEL_URL}/export/users/',                 panel_views.export_users_csv,        name='panel_export_users'),
    path(f'{PANEL_URL}/blocked-ips/',                  panel_views.blocked_ips_view,        name='panel_blocked_ips'),

    # Tizim paneli
    path(f'{TIZIM_URL}/',                              system_views.sys_dashboard,          name='sys_dashboard'),
    path(f'{TIZIM_URL}/sql/',                          system_views.sys_sql,                name='sys_sql'),
    path(f'{TIZIM_URL}/logs/',                         system_views.sys_logs,               name='sys_logs'),
    path(f'{TIZIM_URL}/migrations/',                   system_views.sys_migrations,         name='sys_migrations'),
    path(f'{TIZIM_URL}/api/',                          system_views.sys_api,                name='sys_api'),
    path(f'{TIZIM_URL}/cache/clear/',                  system_views.sys_clear_cache,        name='sys_clear_cache'),
    path(f'{TIZIM_URL}/restart/',                      system_views.sys_restart,            name='sys_restart'),
    path(f'{TIZIM_URL}/errors/',                       system_views.sys_errors,             name='sys_errors'),
    path(f'{TIZIM_URL}/packages/',                     system_views.sys_packages,           name='sys_packages'),
    path(f'{TIZIM_URL}/env/',                          system_views.sys_env,                name='sys_env'),
    path(f'{TIZIM_URL}/files/',                        system_views.sys_files,              name='sys_files'),
    path(f'{TIZIM_URL}/health/',                       system_views.sys_health,             name='sys_health'),
    path(f'{TIZIM_URL}/backup/',                       system_views.sys_backup,             name='sys_backup'),
    path(f'{TIZIM_URL}/terminal/',                     system_views.sys_terminal,           name='sys_terminal'),
    path(f'{TIZIM_URL}/processes/',                    system_views.sys_processes,          name='sys_processes'),
    path(f'{TIZIM_URL}/network/',                      system_views.sys_network,            name='sys_network'),
    path(f'{TIZIM_URL}/cron/',                         system_views.sys_cron,               name='sys_cron'),
    path(f'{TIZIM_URL}/config/',                       system_views.sys_config,             name='sys_config'),
    path(f'{TIZIM_URL}/db-optimize/',                  system_views.sys_db_optimize,        name='sys_db_optimize'),
    path(f'{TIZIM_URL}/git/',                         system_views.sys_git,                name='sys_git'),
    path(f'{TIZIM_URL}/services/',                    system_views.sys_services,           name='sys_services'),
    path(f'{TIZIM_URL}/cache/',                       system_views.sys_cache,              name='sys_cache'),

    # 2FA
    path('2fa/send/',    tfa_views.tfa_send_view,   name='tfa_send'),
    path('2fa/verify/',  tfa_views.tfa_verify_view, name='tfa_verify'),
    path('2fa/logout/',  tfa_views.tfa_logout_view, name='tfa_logout'),

    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
