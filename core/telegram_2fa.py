import random
import string
import urllib.request
import urllib.parse
import json
from django.utils import timezone
from datetime import timedelta

# Bot token va admin Telegram ID
BOT_TOKEN  = '8737975467:AAE-LrxJbuB-pVAKkS9rDdV0lRAv_Tz9EE4'
ADMIN_CHAT_ID = '2114098498'


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
    return ''.join(random.choices(string.digits, k=6))


def create_and_send_code(user) -> bool:
    """Kod yaratib Telegram ga yuborish"""
    from .models import TwoFactorCode

    # Eski kodlarni o'chirish
    TwoFactorCode.objects.filter(user=user, is_used=False).delete()

    code = generate_code()
    TwoFactorCode.objects.create(
        user       = user,
        code       = code,
        expires_at = timezone.now() + timedelta(minutes=5),
    )

    text = (
        f"🔐 <b>Iqtidorli Yoshlar — Admin Panel</b>\n\n"
        f"Kirish kodi: <code>{code}</code>\n\n"
        f"👤 Foydalanuvchi: <b>{user.get_full_name() or user.phone}</b>\n"
        f"⏰ Amal qilish muddati: <b>5 daqiqa</b>\n\n"
        f"⚠️ Bu kodni hech kimga bermang!"
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
