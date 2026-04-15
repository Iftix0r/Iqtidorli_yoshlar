from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .telegram_2fa import create_and_send_code, verify_code, parse_user_agent


def tfa_required(view_func):
    """Panel va tizim uchun 2FA tekshirish decorator"""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('/login/?next=' + request.path)
        # 2FA tasdiqlangan?
        if not request.session.get('tfa_verified'):
            request.session['tfa_next'] = request.path
            return redirect('tfa_send')
        return view_func(request, *args, **kwargs)
    return wrapper


def tfa_send_view(request):
    """Kod yuborish — IP va qurilma info bilan"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/login/')

    error   = ''
    sent    = False
    resent  = request.GET.get('resend') == '1'

    # IP va qurilma info olish (template uchun)
    ip_address = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR', 'Noma\'lum')
    )
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    device_info = parse_user_agent(user_agent)

    if request.method == 'GET' and not resent:
        ok, err = create_and_send_code(request.user, request=request)
        sent  = ok
        error = err if not ok else ''

    if resent:
        ok, err = create_and_send_code(request.user, request=request)
        sent  = ok
        error = err if not ok else ''

    return render(request, 'tfa/send.html', {
        'sent': sent, 'error': error,
        'user': request.user,
        'ip_address': ip_address,
        'device_info': device_info,
    })


def tfa_verify_view(request):
    """Kodni tekshirish"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/login/')

    error = ''
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if not code:
            error = 'Kodni kiriting.'
        elif verify_code(request.user, code):
            request.session['tfa_verified']   = True
            request.session['tfa_verified_at'] = str(timezone.now())
            next_url = request.session.pop('tfa_next', '/panel/')
            return redirect(next_url)
        else:
            error = 'Kod noto\'g\'ri yoki muddati o\'tgan. Qayta kod so\'rang.'

    return render(request, 'tfa/verify.html', {'error': error})


def tfa_logout_view(request):
    """2FA sessiyasini tozalash"""
    request.session.pop('tfa_verified', None)
    request.session.pop('tfa_verified_at', None)
    return redirect('/panel/')
