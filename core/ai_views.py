"""
AI imkoniyatlari — OpenAI GPT orqali:
  - AI Mentor: shaxsiy o'quv yo'l xaritasi
  - Iqtidor Tahlili: kasblar taklifi
  - Portfolio Baholash: kuchli/zaif tomonlar
  - Smart Matching: yosh + mentor + investor moslash
"""
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST


def _openai_chat(messages_list: list, max_tokens: int = 800) -> tuple[str, str]:
    """OpenAI API ga so'rov yuborish — (javob, xato)"""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return '', 'OPENAI_API_KEY sozlanmagan. .env faylga qo\'shing.'
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
            messages=messages_list,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip(), ''
    except Exception as e:
        return '', f'OpenAI xato: {type(e).__name__}: {e}'


# ── AI MENTOR ─────────────────────────────────────────────────────────────────
@login_required
def ai_mentor(request):
    """Foydalanuvchi sohasini kiritsa, AI shaxsiy o'quv yo'l xaritasi tuzadi"""
    result = ''
    error  = ''
    field  = ''

    if request.method == 'POST':
        field    = request.POST.get('field', '').strip()
        level    = request.POST.get('level', 'boshlang\'ich')
        goal     = request.POST.get('goal', '').strip()
        user     = request.user

        # Foydalanuvchi ma'lumotlari
        skills = ', '.join(s.skill_name for s in user.skills.all()) or 'ko\'nikmalar kiritilmagan'

        prompt = (
            f"Sen Iqtidorli Yoshlar platformasining AI Mentorisan. "
            f"Foydalanuvchi: {user.get_full_name()}, daraja: {level}, soha: {field}. "
            f"Mavjud ko'nikmalar: {skills}. Maqsad: {goal or 'aniqlanmagan'}.\n\n"
            f"Ushbu foydalanuvchi uchun 3-6 oylik shaxsiy o'quv yo'l xaritasini tuz. "
            f"Har bir bosqich uchun: maqsad, resurslar (kurslar, kitoblar), amaliy topshiriqlar. "
            f"O'zbek tilida, aniq va qisqa yoz."
        )
        result, error = _openai_chat([
            {'role': 'system', 'content': 'Sen tajribali IT mentor va karera maslahatchisin. O\'zbek tilida javob ber.'},
            {'role': 'user',   'content': prompt},
        ], max_tokens=1000)

    return render(request, 'ai/mentor.html', {
        'result': result, 'error': error, 'field': field,
    })


# ── IQTIDOR TAHLILI ───────────────────────────────────────────────────────────
@login_required
def ai_talent_analysis(request):
    """Yosh yutuq va qiziqishlarini kiritsa, AI mos kasblarni taklif qiladi"""
    result = ''
    error  = ''

    if request.method == 'POST':
        interests  = request.POST.get('interests', '').strip()
        achievements = request.POST.get('achievements', '').strip()
        user       = request.user
        skills     = ', '.join(s.skill_name for s in user.skills.all()) or 'yo\'q'

        prompt = (
            f"Foydalanuvchi: {user.get_full_name()}, yosh: {user.role}.\n"
            f"Ko'nikmalar: {skills}\n"
            f"Qiziqishlar: {interests}\n"
            f"Yutuqlar: {achievements}\n\n"
            f"Ushbu ma'lumotlar asosida:\n"
            f"1. Eng mos 5 ta kasb/yo'nalishni taklif qil\n"
            f"2. Har bir kasb uchun nima uchun mos ekanligini tushuntir\n"
            f"3. Har bir kasb uchun Uzbekistondagi ish imkoniyatlari va maosh darajasini ko'rsat\n"
            f"O'zbek tilida yoz."
        )
        result, error = _openai_chat([
            {'role': 'system', 'content': 'Sen karera maslahatchi va iqtidor tahlilchisan. O\'zbek tilida javob ber.'},
            {'role': 'user',   'content': prompt},
        ], max_tokens=900)

    return render(request, 'ai/talent_analysis.html', {
        'result': result, 'error': error,
    })


# ── PORTFOLIO BAHOLASH ────────────────────────────────────────────────────────
@login_required
def ai_portfolio_review(request):
    """AI portfolioni tahlil qilib, kuchli va zaif tomonlarini ko'rsatadi"""
    result = ''
    error  = ''
    user   = request.user

    if request.method == 'POST':
        projects = user.projects.all()
        certs    = user.certificates.all()
        skills   = user.skills.all()

        proj_list = '\n'.join(f"- {p.title}: {p.description[:100]}" for p in projects) or 'Loyihalar yo\'q'
        cert_list = '\n'.join(f"- {c.title} ({c.issuer})" for c in certs) or 'Sertifikatlar yo\'q'
        skill_list = ', '.join(s.skill_name for s in skills) or 'Ko\'nikmalar yo\'q'

        prompt = (
            f"Foydalanuvchi: {user.get_full_name()}, rol: {user.get_role_display()}, "
            f"viloyat: {user.region or 'ko\'rsatilmagan'}.\n"
            f"Bio: {user.bio or 'yo\'q'}\n\n"
            f"Ko'nikmalar: {skill_list}\n\n"
            f"Loyihalar:\n{proj_list}\n\n"
            f"Sertifikatlar:\n{cert_list}\n\n"
            f"Ushbu portfolio ni professional nuqtai nazardan baholang:\n"
            f"1. Kuchli tomonlar (nima yaxshi)\n"
            f"2. Zaif tomonlar (nima yetishmaydi)\n"
            f"3. Konkret tavsiyalar (nima qo'shish/yaxshilash kerak)\n"
            f"4. Umumiy baho (10 dan)\n"
            f"O'zbek tilida yoz."
        )
        result, error = _openai_chat([
            {'role': 'system', 'content': 'Sen HR mutaxassisi va portfolio baholovchisan. O\'zbek tilida javob ber.'},
            {'role': 'user',   'content': prompt},
        ], max_tokens=900)

    return render(request, 'ai/portfolio_review.html', {
        'result': result, 'error': error, 'user': user,
    })


# ── SMART MATCHING ────────────────────────────────────────────────────────────
@login_required
def ai_smart_match(request):
    """AI yosh + mentor + investor uchun eng mos juftlikni topadi"""
    result = ''
    error  = ''
    user   = request.user

    if request.method == 'POST':
        from .models import User
        match_type = request.POST.get('match_type', 'mentor')

        # Foydalanuvchi profili
        skills = ', '.join(s.skill_name for s in user.skills.all()) or 'yo\'q'

        # Potentsial moslar
        if match_type == 'mentor':
            candidates = User.objects.filter(role='mentor', is_active=True).prefetch_related('skills')[:20]
            role_label = 'mentor'
        elif match_type == 'investor':
            candidates = User.objects.filter(role='investor', is_active=True).prefetch_related('skills')[:20]
            role_label = 'investor'
        else:
            candidates = User.objects.filter(role='yosh', is_active=True).prefetch_related('skills')[:20]
            role_label = 'hamkor yosh'

        cand_list = '\n'.join(
            f"- {c.get_full_name()} (ID:{c.pk}): ko'nikmalar: {', '.join(s.skill_name for s in c.skills.all()) or 'yo\'q'}, bio: {c.bio[:80] or 'yo\'q'}"
            for c in candidates
        ) or 'Nomzodlar topilmadi'

        prompt = (
            f"Foydalanuvchi: {user.get_full_name()}, rol: {user.get_role_display()}\n"
            f"Ko'nikmalar: {skills}\n"
            f"Bio: {user.bio or 'yo\'q'}\n\n"
            f"Quyidagi {role_label}lar ro'yxatidan eng mos 3 tasini tanlang va nima uchun mos ekanligini tushuntiring:\n"
            f"{cand_list}\n\n"
            f"Har bir tavsiya uchun: ism, ID, moslik sababi. O'zbek tilida yoz."
        )
        result, error = _openai_chat([
            {'role': 'system', 'content': 'Sen smart matching tizimisan. O\'zbek tilida javob ber.'},
            {'role': 'user',   'content': prompt},
        ], max_tokens=700)

    return render(request, 'ai/smart_match.html', {
        'result': result, 'error': error,
    })


# ── AI CHAT (umumiy savol-javob) ──────────────────────────────────────────────
@login_required
@require_POST
def ai_chat_api(request):
    """AJAX orqali AI bilan suhbat"""
    try:
        data    = json.loads(request.body)
        message = data.get('message', '').strip()[:500]
    except Exception:
        return JsonResponse({'error': 'Noto\'g\'ri so\'rov'}, status=400)

    if not message:
        return JsonResponse({'error': 'Xabar bo\'sh'}, status=400)

    user = request.user
    skills = ', '.join(s.skill_name for s in user.skills.all()) or 'yo\'q'

    answer, error = _openai_chat([
        {
            'role': 'system',
            'content': (
                f"Sen Iqtidorli Yoshlar platformasining AI yordamchisan. "
                f"Foydalanuvchi: {user.get_full_name()}, rol: {user.get_role_display()}, "
                f"ko'nikmalar: {skills}. "
                f"Qisqa, aniq va foydali javob ber. O'zbek tilida."
            )
        },
        {'role': 'user', 'content': message},
    ], max_tokens=500)

    if error:
        return JsonResponse({'error': error}, status=500)
    return JsonResponse({'answer': answer})
