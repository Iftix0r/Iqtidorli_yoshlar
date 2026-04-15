"""
AI Chat — Gemini uslubida
Rejimlar: general, mentor, talent, portfolio, matching
Tarix DB da saqlanadi (AIChatSession + AIChatMessage)
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone

from .models import AIChatSession, AIChatMessage, AI_MODES


# ── SYSTEM PROMPTLAR ──────────────────────────────────────────────────────────
def _system_prompt(mode, user):
    skills = ', '.join(s.skill_name for s in user.skills.all()) or "yo'q"
    base = (
        f"Foydalanuvchi: {user.get_full_name()}, "
        f"rol: {user.get_role_display()}, "
        f"viloyat: {user.region or 'noaniq'}, "
        f"ko'nikmalar: {skills}. "
        f"O'zbek tilida javob ber. Markdown formatdan foydalanish mumkin."
    )
    prompts = {
        'general': (
            "Sen Iqtidorli Yoshlar platformasining aqlli AI yordamchisan. "
            "Yoshlarga karera, ta'lim, texnologiya va shaxsiy rivojlanish bo'yicha maslahat berasan. " + base
        ),
        'mentor': (
            "Sen tajribali IT mentor va karera maslahatchisin. "
            "Foydalanuvchiga shaxsiy o'quv yo'l xaritasi tuzib berasan, "
            "resurslar va amaliy topshiriqlar taklif qilasan. " + base
        ),
        'talent': (
            "Sen iqtidor tahlilchisi va karera maslahatchisin. "
            "Foydalanuvchining qiziqishlari va ko'nikmalariga qarab "
            "mos kasblar, yo'nalishlar va Uzbekistondagi imkoniyatlarni taklif qilasan. " + base
        ),
        'portfolio': (
            "Sen HR mutaxassisi va portfolio baholovchisan. "
            "Foydalanuvchining loyihalari, sertifikatlari va ko'nikmalarini tahlil qilib, "
            "kuchli/zaif tomonlarini va tavsiyalarni aniq ko'rsatasan. " + base
        ),
        'matching': (
            "Sen smart matching tizimisan. "
            "Foydalanuvchiga mos mentor, investor yoki hamkorlarni topib, "
            "moslik sabablarini tushuntirib berasan. " + base
        ),
    }
    return prompts.get(mode, prompts['general'])


def _context_message(mode, user):
    """Rejimga qarab boshlang'ich kontekst xabari"""
    if mode == 'portfolio':
        projects = user.projects.all()
        certs = user.certificates.all()
        skills = user.skills.all()
        return (
            "Mening portfolio ma'lumotlarim:\n"
            "Ko'nikmalar: " + (', '.join(s.skill_name for s in skills) or "yo'q") + "\n"
            "Loyihalar: " + (', '.join(p.title for p in projects) or "yo'q") + "\n"
            "Sertifikatlar: " + (', '.join(c.title for c in certs) or "yo'q") + "\n"
            "Bio: " + (user.bio or "yo'q")
        )
    if mode == 'matching':
        from .models import User as UserModel
        mentors = UserModel.objects.filter(role='mentor', is_active=True).prefetch_related('skills')[:15]
        mentor_list = '\n'.join(
            "- {} (ID:{}): {}".format(
                m.get_full_name(), m.pk,
                ', '.join(s.skill_name for s in m.skills.all()) or "yo'q"
            ) for m in mentors
        )
        return "Platformadagi mentorlar:\n" + mentor_list
    return None


# ── OPENAI CALL ───────────────────────────────────────────────────────────────
def _call_ai(messages_list: list, max_tokens: int = 1000):
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


# ── ASOSIY CHAT SAHIFASI ──────────────────────────────────────────────────────
@login_required
def ai_chat(request, session_id=None):
    user = request.user

    # Sessiyalar ro'yxati
    sessions = user.ai_sessions.all()[:30]

    # Joriy sessiya
    session = None
    messages_qs = []
    if session_id:
        session = get_object_or_404(AIChatSession, pk=session_id, user=user)
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


# ── YANGI SESSIYA YARATISH ────────────────────────────────────────────────────
@login_required
@require_POST
def ai_new_session(request):
    mode = request.POST.get('mode', 'general')
    session = AIChatSession.objects.create(
        user=request.user,
        mode=mode,
        title='',
    )
    return redirect('ai_chat_session', session_id=session.pk)


# ── SESSIYA O'CHIRISH ─────────────────────────────────────────────────────────
@login_required
@require_POST
def ai_delete_session(request, session_id):
    AIChatSession.objects.filter(pk=session_id, user=request.user).delete()
    return JsonResponse({'ok': True})


# ── XABAR YUBORISH (AJAX) ─────────────────────────────────────────────────────
@login_required
@require_POST
def ai_send_message(request, session_id):
    try:
        data = json.loads(request.body)
        user_text = data.get('message', '').strip()[:1000]
    except Exception:
        return JsonResponse({'error': "Noto'g'ri so'rov"}, status=400)

    if not user_text:
        return JsonResponse({'error': "Xabar bo'sh"}, status=400)

    session = get_object_or_404(AIChatSession, pk=session_id, user=request.user)

    # Foydalanuvchi xabarini saqlash
    AIChatMessage.objects.create(session=session, role='user', content=user_text)

    # Sessiya sarlavhasini birinchi xabardan olish
    if not session.title:
        session.title = user_text[:60]
        session.save(update_fields=['title'])

    # Tarix (oxirgi 20 xabar)
    history = list(session.messages.order_by('created_at')[:20])

    # OpenAI uchun messages ro'yxati
    messages_list = [{'role': 'system', 'content': _system_prompt(session.mode, request.user)}]

    # Kontekst (portfolio, matching uchun)
    ctx = _context_message(session.mode, request.user)
    if ctx and len(history) <= 2:
        messages_list.append({'role': 'user', 'content': ctx})
        messages_list.append({'role': 'assistant', 'content': "Tushundim, ma'lumotlaringizni ko'rib chiqdim."})

    for msg in history:
        messages_list.append({'role': msg.role, 'content': msg.content})

    answer, error = _call_ai(messages_list, max_tokens=1200)

    if error:
        return JsonResponse({'error': error}, status=500)

    # AI javobini saqlash
    ai_msg = AIChatMessage.objects.create(session=session, role='assistant', content=answer)
    session.updated_at = timezone.now()
    session.save(update_fields=['updated_at'])

    return JsonResponse({
        'answer':  answer,
        'msg_id':  ai_msg.pk,
        'session_title': session.title,
    })


# ── SESSIYA TARIXI (JSON) ─────────────────────────────────────────────────────
@login_required
def ai_session_history(request, session_id):
    session = get_object_or_404(AIChatSession, pk=session_id, user=request.user)
    msgs = [
        {
            'role':    m.role,
            'content': m.content,
            'time':    m.created_at.strftime('%H:%M'),
        }
        for m in session.messages.all()
    ]
    return JsonResponse({'messages': msgs, 'mode': session.mode, 'title': session.title})
