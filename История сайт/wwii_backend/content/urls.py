"""URL-маршруты для API контента сайта «Фронтовой альбом»."""
from django.urls import path
from . import views

urlpatterns = [
    # ── Герои войны ──
    path('heroes/',           views.heroes,       name='api-heroes'),
    path('heroes/<uuid:uid>/', views.hero_delete, name='api-hero-delete'),

    # ── Фото-хроника ──
    path('khronika/',              views.khronika,        name='api-khronika'),
    path('khronika/<uuid:uid>/',   views.khronika_delete, name='api-khronika-delete'),

    # ── Письма с фронта ──
    path('letters/',           views.letters,       name='api-letters'),
    path('letters/<uuid:uid>/', views.letter_delete, name='api-letter-delete'),

    # ── Проверка орфографии ──
    path('spell-check/', views.spell_check_view, name='api-spell-check'),
]
