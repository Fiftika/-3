"""URL-конфигурация проекта «Фронтовой альбом»."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie

# Кастомизируем заголовки панели администратора
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title  = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

# Главная страница — index.html с установкой CSRF-cookie
index_view = ensure_csrf_cookie(TemplateView.as_view(template_name='index.html'))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('content.urls')),
    path('', index_view, name='index'),
]

# В режиме разработки Django сам отдаёт медиафайлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
