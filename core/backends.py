from django.contrib.auth.backends import ModelBackend
from .models import User


class PhoneBackend(ModelBackend):
    """Telefon raqam orqali autentifikatsiya"""

    def authenticate(self, request, phone=None, password=None, **kwargs):
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None
