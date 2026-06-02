import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

def _env_csv(name: str, default: str = '') -> list[str]:
    """Parse comma-separated env var; treat empty string as unset."""
    value = (os.environ.get(name) or default).strip()
    return [part.strip() for part in value.split(',') if part.strip()]


# Always load project .env (mounted in Docker). File wins over empty compose substitutions.
load_dotenv(BASE_DIR / '.env', override=True)


def _clean_secret(value: str) -> str:
    """Strip whitespace and quotes pasted from Word / chat apps."""
    if not value:
        return ''
    value = value.strip()
    for left, right in (
        ('\u201c', '\u201d'),
        ('\u2018', '\u2019'),
        ('"', '"'),
        ("'", "'"),
    ):
        if value.startswith(left) and value.endswith(right):
            value = value[1:-1].strip()
    return value

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-only-change-in-production',
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = _env_csv('ALLOWED_HOSTS', '127.0.0.1,localhost')
_site_domain = (os.environ.get('SITE_DOMAIN') or '').strip()
if _site_domain and _site_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_site_domain)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'apps.core',
    'apps.projects',
    'apps.users',
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
    'allauth.account.middleware.AccountMiddleware',
    'apps.users.middleware.AllowedUserMiddleware',
]

ROOT_URLCONF = 'claaxy_log.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.users.context_processors.user_module_nav',
            ],
        },
    },
]

WSGI_APPLICATION = 'claaxy_log.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(os.environ.get('DATABASE_PATH', str(BASE_DIR / 'db.sqlite3'))),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Toronto'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': (
            'django.contrib.staticfiles.storage.StaticFilesStorage'
            if DEBUG
            else 'whitenoise.storage.CompressedManifestStaticFilesStorage'
        ),
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media')))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
SOCIALACCOUNT_ONLY = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# Avoid SMTP connection errors if any allauth email path is triggered
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@claaxylog.local'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'key': '',
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

ACCOUNT_ADAPTER = 'apps.users.adapters.EmailAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'apps.users.adapters.WhitelistSocialAccountAdapter'

LOGIN_URL = '/accounts/google/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True

USER_MODULE_ADMIN_EMAIL = os.environ.get('USER_MODULE_ADMIN_EMAIL', 'clu@taxnova.ca').lower().strip()

OPENAI_API_KEY = _clean_secret(os.environ.get('OPENAI_API_KEY', ''))
OPENAI_TRANSCRIPTION_MODEL = os.environ.get('OPENAI_TRANSCRIPTION_MODEL', 'whisper-1')
OPENAI_SUMMARY_MODEL = os.environ.get('OPENAI_SUMMARY_MODEL', 'gpt-4o-mini')

VOICE_NOTE_MAX_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_CONTENT_TYPES = {
    'audio/webm',
    'audio/wav',
    'audio/x-wav',
    'audio/mpeg',
    'audio/mp4',
    'audio/ogg',
}

CSRF_TRUSTED_ORIGINS = _env_csv('CSRF_TRUSTED_ORIGINS')
if _site_domain:
    _origin = f'https://{_site_domain}'
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() in (
        'true',
        '1',
        'yes',
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
