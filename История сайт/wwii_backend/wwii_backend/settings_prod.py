"""
settings_prod.py — настройки для production (арендованный сервер).

Использование:
    export DJANGO_SETTINGS_MODULE=wwii_backend.settings_prod
    gunicorn wwii_backend.wsgi:application

Или в systemd-сервисе:
    Environment="DJANGO_SETTINGS_MODULE=wwii_backend.settings_prod"
"""

from .settings import *   # берём все базовые настройки и переопределяем нужные

import os

# ──────────────────────────────────────────────
# Безопасность
# ──────────────────────────────────────────────

# ОБЯЗАТЕЛЬНО: замените на уникальную строку (50+ символов)
# Сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'ЗАМЕНИТЕ-ЭТУ-СТРОКУ-НА-СЛУЧАЙНУЮ-50-СИМВОЛОВ'
)

DEBUG = False

# Укажите IP или домен вашего сервера (оба сразу, если есть)
# Примеры: '95.142.45.10'  или  'frontalnyalbum.ru'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ──────────────────────────────────────────────
# Статические файлы (Nginx отдаёт их напрямую)
# ──────────────────────────────────────────────
STATIC_ROOT = BASE_DIR / 'staticfiles'   # куда collectstatic сложит всё
STATIC_URL  = '/static/'

# ──────────────────────────────────────────────
# Безопасные заголовки (когда за Nginx)
# ──────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST    = True

# Логирование ошибок в файл
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django_errors.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR',
    },
}
