"""WSGI-конфигурация для проекта «Фронтовой альбом»."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wwii_backend.settings')
application = get_wsgi_application()
