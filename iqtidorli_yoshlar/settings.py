from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── ASOSIY ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-immediately')
DEBUG      = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ── XAVFSIZLIK ────────────────────────────────────────────────────────────────
# HTTPS sozlamalari (production da True)
SECURE_SSL_REDIRECT         = os.getenv('SECURE_SSL', 'False') == 'True'
SECURE_HSTS_SECONDS         = int(os.getenv('HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD         = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER   = True
X_FRAME_OPTIONS             = 'DENY'

# Cookie xavfsizligi
SESSION_COOKIE_SECURE   = os.getenv('COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE      = 3600 * 8  # 8 soat

CSRF_COOKIE_SECURE   = os.getenv('COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Parol siyosati (kamida 12 belgi, murakkab)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Login urinishlari cheklash (brute-force)
LOGIN_ATTEMPTS_LIMIT  = 5
LOGIN_ATTEMPTS_WINDOW = 15  # daqiqa

# ── ILOVALAR ──────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ErrorLogMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RateLimitMiddleware',
]

ROOT_URLCONF = 'iqtidorli_yoshlar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'iqtidorli_yoshlar.wsgi.application'

# ── DATABASE ──────────────────────────────────────────────────────────────────
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE':   DB_ENGINE,
            'NAME':     os.getenv('DB_NAME'),
            'USER':     os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST':     os.getenv('DB_HOST', 'localhost'),
            'PORT':     os.getenv('DB_PORT', '5432'),
            'OPTIONS':  {'connect_timeout': 10},
            'CONN_MAX_AGE': 60,
        }
    }

# ── AUTH ──────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL     = 'core.User'
LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/profile/'
LOGOUT_REDIRECT_URL = '/'

AUTHENTICATION_BACKENDS = [
    'core.backends.PhoneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ── LOGGING ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Logs papkasini yaratish
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ── LOKALIZATSIYA ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'uz'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N      = True
USE_TZ        = True

# ── STATIC VA MEDIA ───────────────────────────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'public' / 'static'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'public' / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CACHE ─────────────────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'iqtidorli-cache',
    }
}

# ── ADMIN URL (xavfsizlik uchun o'zgartirilgan) ───────────────────────────────
ADMIN_URL = os.getenv('ADMIN_URL', 'admin')
PANEL_URL = os.getenv('PANEL_URL', 'panel')
TIZIM_URL = os.getenv('TIZIM_URL', 'tizim')

# ── XAVFSIZLIK (SECURITY HEADERS) ──────────────────────────────────────────
# HTTPS orqali bog'lanishni majburiy qilish
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL', 'False') == 'True'
SECURE_HSTS_SECONDS = int(os.getenv('HSTS_SECONDS', 0))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Brauzer himoyasi
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# Session va Cookie xavfsizligi
SESSION_COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# 2FA — Telegram ishlayotgan bo'lsa True qiling
TFA_ENABLED   = os.getenv('TFA_ENABLED', 'False') == 'True'
TFA_BOT_TOKEN = os.getenv('TFA_BOT_TOKEN', '')
TFA_CHAT_ID   = os.getenv('TFA_CHAT_ID', '')
