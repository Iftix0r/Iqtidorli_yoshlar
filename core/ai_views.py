import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone

from .models import AIChatSession, AIChatMessage, AI_MODES


def _system_prompt(mode, user):
    skills = ', '.join(s.skill_name for s in user.skills.all()) or "yo'q"
    base = (
        f"Foydalanuvchi haqida: ismi {user.get_full_name()}, "
        f"roli {user.get_role_display()}, "
        f"viloyat: {user.region or 'noaniq'}, "
        f"ko'nikmalar: {skills}."
    )
    identity = (
        "Sen 'Iqtidor' — yoshiqtidorlar.uz saytining rasmiy sun'iy intellekt yordamchisisisan. "
        "Ismingni so'rashsa: 'Mening ismim Iqtidor' deb javob ber. "
        "Qaysi kompaniya yoki model ekanligingni so'rashsa: 'Men Iqtidor — yoshiqtidorlar.uz ning AI yordamchisiman' de. "
        "yoshiqtidorlar.uz — O'zbekiston iqtidorli yoshlari uchun platforma: "
        "tanlovlar, kurslar, mentorlar, investorlar, ish o'rinlari, reyting, market va AI imkoniyatlari bor. "
        "Har doim O'zbek tilida, qisqa, aniq va do'stona javob ber. "
        "Markdown formatdan foydalanish mumkin. "
    )
    modes = {
        'general':   "Yoshlarga karera, ta'lim, texnologiya va shaxsiy rivojlanish bo'yicha maslahat berasan. ",
        'mentor':    "Mentor rejimida ishlaysan — tajribali IT mentor sifatida shaxsiy o'quv yo'l xaritasi tuzib berasan, resurslar va amaliy topshiriqlar taklif qilasan. ",
        'talent':    "Iqtidor tahlili rejimida ishlaysan — foydalanuvchining qiziqishlari va ko'nikmalariga qarab mos kasblar va O'zbekistondagi imkoniyatlarni taklif qilasan. ",
        'portfolio': "Portfolio baholash rejimida ishlaysan — loyihalar, sertifikatlar va ko'nikmalarni tahlil qilib kuchli/zaif tomonlarini ko'rsatasan. ",
        'matching':  "Smart matching rejimida ishlaysan — foydalanuvchiga yoshiqtidorlar.uz dagi mos mentor, investor yoki hamkorlarni topib moslik sabablarini tushuntirib berasan. ",
    }
    return identity + modes.get(mode, modes['general']) + base


def _context_message(mode, user):
    if mode == 'portfolio':
        skills   = ', '.join(s.skill_name for s in user.skills.all()) or "yo'q"
        projects = ', '.join(p.title for p in user.projects.all()) or "yo'q"
        certs    = ', '.join(c.title for c in user.certificates.all()) or "yo'q"
        return f"Mening portfolio ma'lumotlarim:\nKo'nikmalar: {skills}\nLoyihalar: {projects}\nSertifikatlar: {certs}\nBio: {user.bio or 'yo\'q'}"
    if mode == 'matching':
        from .models import User as U
        mentors = U.objects.filter(role='mentor', is_active=True).prefetch_related('skills')[:15]
        lst = '\n'.join(
            "- {} (ID:{}): {}".format(m.get_full_name(), m.pk,
                ', '.join(s.skill_name for s in m.skills.all()) or "yo'q")
            for m in mentors
        )
        return "Platformadagi mentorlar:\n" + lst
    return None


def _call_ai(messages_list, max_tokens=1200):
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return '', "OPENAI_API_KEY sozlanmagan."
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
        return '', f'AI xato: {e}'


@login_required
def ai_chat(request, session_id=None):
    user     = request.user
    sessions = user.ai_sessions.all()[:30]
    session  = None
    messages_qs = []
    if session_id:
        session     = get_object_or_404(AIChatSession, pk=session_id, user=user)
        messages_qs = session.messages.all()
    mode = request.GET.get('mode', session.mode if session else 'general')
    return render(request, 'ai/chat.html', {
        'sessions':    sessions,
        'session':     session,
        'messages':    messages_qs,
        'mode':        mode,
        'ai_modes':    AI_MODES,
        'mode_labels': dict(AI_MODES),
    })


@login_required
@require_POST
def ai_new_session(request):
    mode    = request.POST.get('mode', 'general')
    session = AIChatSession.objects.create(user=request.user, mode=mode, title='')
    return redirect('ai_chat_session', session_id=session.pk)


@login_required
@require_POST
def ai_delete_session(request, session_id):
    AIChatSession.objects.filter(pk=session_id, user=request.user).delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def ai_send_message(request, session_id):
    try:
        data      = json.loads(request.body)
        user_text = data.get('message', '').strip()[:1000]
    except Exception:
        return JsonResponse({'error': "Noto'g'ri so'rov"}, status=400)

    if not user_text:
        return JsonResponse({'error': "Xabar bo'sh"}, status=400)

    session = get_object_or_404(AIChatSession, pk=session_id, user=request.user)
    AIChatMessage.objects.create(session=session, role='user', content=user_text)

    if not session.title:
        session.title = user_text[:60]
        session.save(update_fields=['title'])

    history = list(session.messages.order_by('created_at')[:20])
    msgs    = [{'role': 'system', 'content': _system_prompt(session.mode, request.user)}]

    ctx = _context_message(session.mode, request.user)
    if ctx and len(history) <= 2:
        msgs.append({'role': 'user',      'content': ctx})
        msgs.append({'role': 'assistant', 'content': "Tushundim, ma'lumotlaringizni ko'rib chiqdim."})

    for m in history:
        msgs.append({'role': m.role, 'content': m.content})

    answer, error = _call_ai(msgs)
    if error:
        return JsonResponse({'error': error}, status=500)

    ai_msg = AIChatMessage.objects.create(session=session, role='assistant', content=answer)
    session.updated_at = timezone.now()
    session.save(update_fields=['updated_at'])

    return JsonResponse({'answer': answer, 'msg_id': ai_msg.pk, 'session_title': session.title})


@login_required
def ai_session_history(request, session_id):
    session = get_object_or_404(AIChatSession, pk=session_id, user=request.user)
    msgs = [{'role': m.role, 'content': m.content, 'time': m.created_at.strftime('%H:%M')}
            for m in session.messages.all()]
    return JsonResponse({'messages': msgs, 'mode': session.mode, 'title': session.title})
