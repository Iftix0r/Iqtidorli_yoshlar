from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q

from .models import User, Badge, UserStreak, XPLog, BADGE_DEFINITIONS, REGIONS


def leaderboard_view(request):
    """Hududiy va umumiy reyting"""
    role   = request.GET.get('role', 'yosh')
    region = request.GET.get('region', '')
    tab    = request.GET.get('tab', 'global')  # global | region | streak

    qs = User.objects.filter(role=role, is_active=True).prefetch_related('skills', 'badges')

    if region:
        qs = qs.filter(region=region)

    if tab == 'streak':
        # Streak bo'yicha reyting
        users = (
            qs.filter(streak__isnull=False)
            .order_by('-streak__current_streak', '-score')[:50]
        )
    else:
        users = qs.order_by('-score')[:50]

    # Hududiy mini-reyting (top 5 har viloyatdan)
    region_leaders = []
    if tab == 'region' and not region:
        for reg_val, reg_label in REGIONS:
            top = User.objects.filter(role='yosh', region=reg_val, is_active=True).order_by('-score').first()
            if top:
                region_leaders.append({'region': reg_label, 'user': top})

    regions = (
        User.objects.exclude(region='')
        .values_list('region', flat=True).distinct().order_by('region')
    )

    # Joriy foydalanuvchi reytingi
    my_rank = None
    if request.user.is_authenticated and request.user.role == role:
        better = User.objects.filter(role=role, score__gt=request.user.score, is_active=True).count()
        my_rank = better + 1

    return render(request, 'leaderboard.html', {
        'users': users, 'role': role, 'regions': regions,
        'selected_region': region, 'tab': tab,
        'region_leaders': region_leaders,
        'my_rank': my_rank,
    })


@login_required
def my_badges(request):
    """Foydalanuvchining barcha badge lari"""
    user   = request.user
    earned = {b.badge_key for b in user.badges.all()}
    all_badges = []
    for key, info in BADGE_DEFINITIONS.items():
        all_badges.append({
            'key':    key,
            'info':   info,
            'earned': key in earned,
        })
    # Streak
    streak = getattr(user, 'streak', None)
    # XP tarixi
    xp_logs = user.xp_logs.all()[:20]
    total_xp = sum(x.amount for x in user.xp_logs.all())

    return render(request, 'gamification/badges.html', {
        'all_badges': all_badges,
        'earned_count': len(earned),
        'total_count': len(BADGE_DEFINITIONS),
        'streak': streak,
        'xp_logs': xp_logs,
        'total_xp': total_xp,
    })


@login_required
def streak_checkin(request):
    """Kunlik check-in (AJAX)"""
    if request.method == 'POST':
        from .utils import update_streak, award_xp
        streak = update_streak(request.user)
        award_xp(request.user, 5, 'Kunlik kirish')
        return JsonResponse({
            'ok': True,
            'current': streak.current_streak,
            'longest': streak.longest_streak,
            'xp': 5,
        })
    return JsonResponse({'ok': False})
