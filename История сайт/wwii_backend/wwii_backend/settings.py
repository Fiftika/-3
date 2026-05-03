"""
Django settings for wwii_backend — «Фронтовой альбом».
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# БЕЗОПАСНОСТЬ — в продакшне замените на случайную строку и уберите из репо
SECRET_KEY = 'django-insecure-wwii-album-school-project-change-me-in-production'

# Для разработки — True; для продакшна — False
DEBUG = True

ALLOWED_HOSTS = ['*']   # в продакшне укажите конкретные хосты

# ──────────────────────────────────────────────
# Приложения
# ──────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'content',          # наше приложение
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wwii_backend.urls'

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

WSGI_APPLICATION = 'wwii_backend.wsgi.application'

# ──────────────────────────────────────────────
# База данных — SQLite (удобно для школьного проекта)
# ──────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ──────────────────────────────────────────────
# Валидация паролей (для панели администратора)
# ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ──────────────────────────────────────────────
# Локализация
# ──────────────────────────────────────────────
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# Статические файлы (CSS, JS, изображения)
# ──────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # для collectstatic

# ──────────────────────────────────────────────
# Медиафайлы (загруженные пользователями)
# ──────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ──────────────────────────────────────────────
# Сессии — храним в БД, живут 30 дней
# ──────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30   # 30 дней
SESSION_SAVE_EVERY_REQUEST = True

# CSRF cookie доступен из JavaScript (для fetch-запросов)
CSRF_COOKIE_HTTPONLY = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────────────
# Заголовок панели администратора
# ──────────────────────────────────────────────
ADMIN_SITE_HEADER = 'Фронтовой альбом — Панель управления'
ADMIN_SITE_TITLE  = 'Фронтовой альбом'
ADMIN_INDEX_TITLE = 'Управление контентом'
