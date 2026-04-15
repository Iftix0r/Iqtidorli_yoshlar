from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

# Admin URL ni settings dan olish (xavfsizlik uchun)
ADMIN_URL = getattr(settings, 'ADMIN_URL', 'admin')


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
        'today_logins':    LoginHistory.objects.filter(
                               created_at__date=__import__('django.utils.timezone', fromlist=['timezone']).timezone.now().date()
                           ).count() if False else LoginHistory.objects.filter(is_success=True).count(),
    }
    return render(request, 'admin/stats.html', ctx)


urlpatterns = [
    path(f'{ADMIN_URL}/stats/', admin_stats, name='admin_stats'),
    path(f'{ADMIN_URL}/', admin.site.urls),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
