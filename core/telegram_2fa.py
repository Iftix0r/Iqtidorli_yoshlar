import secrets
import string
import urllib.request
import urllib.parse
import json
from django.utils import timezone
from django.conf import settings as django_settings
from datetime import timedelta

# Bot token va admin Telegram ID — .env dan o'qiladi
BOT_TOKEN     = getattr(django_settings, 'TFA_BOT_TOKEN', '')
ADMIN_CHAT_ID = getattr(django_settings, 'TFA_CHAT_ID', '')


def send_telegram(chat_id: str, text: str) -> tuple[bool, str]:
    """Telegram ga xabar yuborish — (ok, error_msg)"""
    try:
        url  = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = urllib.parse.urlencode({
            'chat_id':    chat_id,
            'text':       text,
            'parse_mode': 'HTML',
        }).encode()
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get('ok'):
                return True, ''
            return False, str(result.get('description', 'Telegram xato'))
    except urllib.error.URLError as e:
        return False, f'URL xato: {e.reason}'
    except Exception as e:
        return False, f'Xato: {type(e).__name__}: {e}'


def generate_code() -> str:
    """6 xonali raqamli kod"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def parse_user_agent(user_agent: str) -> dict:
    """User-Agent dan qurilma, OS, brauzer ma'lumotlarini ajratish"""
    info = {'device': 'Noma\'lum', 'os': 'Noma\'lum', 'browser': 'Noma\'lum'}

    if not user_agent:
        return info

    ua = user_agent.lower()

    # OS aniqlash
    if 'windows nt 10' in ua or 'windows nt 11' in ua:
        info['os'] = 'Windows 10/11'
    elif 'windows nt 6.3' in ua:
        info['os'] = 'Windows 8.1'
    elif 'windows nt 6.1' in ua:
        info['os'] = 'Windows 7'
    elif 'windows' in ua:
        info['os'] = 'Windows'
    elif 'mac os x' in ua:
        info['os'] = 'macOS'
    elif 'android' in ua:
        # Android versiyasini olish
        import re
        m = re.search(r'android\s*([\d.]+)', ua)
        info['os'] = f"Android {m.group(1)}" if m else 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        info['os'] = 'iOS'
    elif 'linux' in ua:
        info['os'] = 'Linux'
    elif 'ubuntu' in ua:
        info['os'] = 'Ubuntu'
    elif 'cros' in ua:
        info['os'] = 'ChromeOS'

    # Qurilma aniqlash
    if 'iphone' in ua:
        info['device'] = '📱 iPhone'
    elif 'ipad' in ua:
        info['device'] = '📱 iPad'
    elif 'android' in ua and 'mobile' in ua:
        info['device'] = '📱 Android telefon'
    elif 'android' in ua:
        info['device'] = '📱 Android planshet'
    elif 'macintosh' in ua or 'mac os' in ua:
        info['device'] = '💻 Mac'
    elif 'windows' in ua:
        info['device'] = '🖥️ Windows PC'
    elif 'linux' in ua:
        info['device'] = '🖥️ Linux PC'
    else:
        info['device'] = '🖥️ Kompyuter'

    # Brauzer aniqlash
    import re
    if 'edg/' in ua or 'edge/' in ua:
        m = re.search(r'edg[e]?/([\d.]+)', ua)
        info['browser'] = f"Edge {m.group(1).split('.')[0]}" if m else 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        m = re.search(r'opr/([\d.]+)', ua)
        info['browser'] = f"Opera {m.group(1).split('.')[0]}" if m else 'Opera'
    elif 'chrome/' in ua and 'safari/' in ua:
        m = re.search(r'chrome/([\d.]+)', ua)
        info['browser'] = f"Chrome {m.group(1).split('.')[0]}" if m else 'Chrome'
    elif 'firefox/' in ua:
        m = re.search(r'firefox/([\d.]+)', ua)
        info['browser'] = f"Firefox {m.group(1).split('.')[0]}" if m else 'Firefox'
    elif 'safari/' in ua and 'chrome' not in ua:
        m = re.search(r'version/([\d.]+)', ua)
        info['browser'] = f"Safari {m.group(1).split('.')[0]}" if m else 'Safari'
    elif 'yabrowser' in ua:
        info['browser'] = 'Yandex Browser'
    elif 'samsungbrowser' in ua:
        info['browser'] = 'Samsung Browser'
    elif 'ucbrowser' in ua:
        info['browser'] = 'UC Browser'

    return info


def get_ip_location(ip: str) -> str:
    """IP manzildan joy aniqlash (tashqi API orqali)"""
    if not ip or ip in ('127.0.0.1', 'localhost', '::1'):
        return 'Lokal (localhost)'
    try:
        url = f'http://ip-api.com/json/{ip}?fields=country,regionName,city,isp&lang=en'
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            parts = []
            if data.get('city'):
                parts.append(data['city'])
            if data.get('regionName'):
                parts.append(data['regionName'])
            if data.get('country'):
                parts.append(data['country'])
            location = ', '.join(parts)
            if data.get('isp'):
                location += f" ({data['isp']})"
            return location or 'Aniqlanmadi'
    except Exception:
        return 'Aniqlanmadi'


def create_and_send_code(user, request=None) -> tuple[bool, str]:
    """Kod yaratib Telegram ga yuborish — IP va qurilma info bilan"""
    from .models import TwoFactorCode

    # Eski kodlarni o'chirish
    TwoFactorCode.objects.filter(user=user, is_used=False).delete()

    code = generate_code()
    TwoFactorCode.objects.create(
        user       = user,
        code       = code,
        expires_at = timezone.now() + timedelta(minutes=5),
    )

    # IP va qurilma ma'lumotlarini olish
    ip_address  = 'Noma\'lum'
    device_info = {'device': 'Noma\'lum', 'os': 'Noma\'lum', 'browser': 'Noma\'lum'}
    location    = 'Noma\'lum'

    if request:
        # IP manzilni olish
        ip_address = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', 'Noma\'lum')
        )

        # User-Agent dan qurilma info
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_info = parse_user_agent(user_agent)

        # IP lokatsiya
        location = get_ip_location(ip_address)

    now = timezone.now().strftime('%d.%m.%Y %H:%M:%S')

    text = (
        f"🔐 <b>Iqtidorli Yoshlar — 2FA Kirish</b>\n\n"
        f"Kirish kodi: <code>{code}</code>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Foydalanuvchi:</b> {user.get_full_name() or user.phone}\n"
        f"📞 <b>Telefon:</b> {user.phone}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>IP manzil:</b> <code>{ip_address}</code>\n"
        f"📍 <b>Joylashuv:</b> {location}\n"
        f"{device_info['device']} <b>Qurilma:</b> {device_info['os']}\n"
        f"🌍 <b>Brauzer:</b> {device_info['browser']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 <b>Vaqt:</b> {now}\n"
        f"⏰ <b>Amal qilish:</b> 5 daqiqa\n\n"
        f"⚠️ <b>Bu kodni hech kimga bermang!</b>\n"
        f"Agar siz kirmagan bo'lsangiz, parolingizni o'zgartiring!"
    )
    ok, err = send_telegram(ADMIN_CHAT_ID, text)
    if not ok:
        import logging
        logging.getLogger('core').error(f"Telegram 2FA xato: {err}")
    return ok, err


def verify_code(user, code: str) -> bool:
    """Kodni tekshirish"""
    from .models import TwoFactorCode
    try:
        obj = TwoFactorCode.objects.filter(
            user=user, code=code, is_used=False
        ).latest('created_at')
        if obj.is_valid():
            obj.is_used = True
            obj.save()
            return True
    except TwoFactorCode.DoesNotExist:
        pass
    return False
