from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


def games_home(request):
    return render(request, 'games/home.html')

def game_snake(request):
    return render(request, 'games/snake.html')

def game_2048(request):
    return render(request, 'games/2048.html')

def game_typing(request):
    return render(request, 'games/typing.html')

def game_memory(request):
    return render(request, 'games/memory.html')

def game_ttt(request):
    return render(request, 'games/tictactoe.html')


@login_required
@require_POST
def game_score(request):
    """O'yin natijasini saqlash va XP berish"""
    try:
        data  = json.loads(request.body)
        game  = data.get('game', '')
        score = int(data.get('score', 0))
    except Exception:
        return JsonResponse({'error': 'bad'}, status=400)

    # XP berish (kuniga bir marta, har o'yin uchun)
    from django.core.cache import cache
    cache_key = f"game_xp_{request.user.pk}_{game}"
    xp_earned = 0

    if not cache.get(cache_key):
        xp_map = {'snake': 10, '2048': 15, 'typing': 10, 'memory': 10, 'ttt': 5}
        xp = xp_map.get(game, 5)
        from .utils import award_xp
        award_xp(request.user, xp, f"O'yin: {game}")
        cache.set(cache_key, True, 86400)  # 24 soat
        xp_earned = xp

    return JsonResponse({'ok': True, 'xp': xp_earned, 'score': score})


def game_math(request):
    return render(request, 'games/mathquiz.html')

def game_code(request):
    return render(request, 'games/codequiz.html')

def game_geo(request):
    return render(request, 'games/geoguess.html')

def game_word(request):
    return render(request, 'games/wordscramble.html')

def game_color(request):
    return render(request, 'games/colormatch.html')
