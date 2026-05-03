"""
Панель администратора для сайта «Фронтовой альбом».

Возможности:
  - Просмотр, редактирование, одобрение/отклонение пользовательских записей
  - Фильтрация по статусу (одобрено / ожидает)
  - Поиск по имени / тексту
  - Просмотр орфографических ошибок
  - Предпросмотр фотографий
  - Массовое одобрение одним действием
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import UserHero, UserKhronika, UserLetter


# ──────────────────────────────────────────────────────────────
# Общие действия (actions)
# ──────────────────────────────────────────────────────────────

@admin.action(description='✅ Одобрить выбранные записи')
def action_approve(modeladmin, request: HttpRequest, queryset: QuerySet):
    count = queryset.update(approved=True)
    modeladmin.message_user(request, f'Одобрено записей: {count}')


@admin.action(description='❌ Снять одобрение (перевести в ожидание)')
def action_unapprove(modeladmin, request: HttpRequest, queryset: QuerySet):
    count = queryset.update(approved=False)
    modeladmin.message_user(request, f'Снято одобрение у записей: {count}')


# ──────────────────────────────────────────────────────────────
# Миксин для общих методов
# ──────────────────────────────────────────────────────────────

class SpellMixin:
    """Добавляет колонку с результатами проверки орфографии."""

    @admin.display(description='Правописание')
    def spell_status(self, obj):
        errors = getattr(obj, 'spell_errors', [])
        if not errors:
            return format_html('<span style="color:#2a8020;font-weight:bold">✓ ОК</span>')
        tip = ', '.join(errors[:5])
        return format_html(
            '<span style="color:#b06010" title="Возможные ошибки: {}">⚠ {} слов</span>',
            tip, len(errors)
        )


class PhotoMixin:
    """Добавляет колонку с превью фотографии."""

    @admin.display(description='Фото')
    def photo_preview_thumb(self, obj):
        src = getattr(obj, 'photo_b64', '')
        if src and src.startswith('data:image'):
            return format_html(
                '<img src="{}" style="height:50px;width:50px;object-fit:cover;border-radius:2px" />',
                src
            )
        return mark_safe('<span style="color:#aaa">нет</span>')

    @admin.display(description='Фотография (большой просмотр)')
    def photo_preview_large(self, obj):
        src = getattr(obj, 'photo_b64', '')
        if src and src.startswith('data:image'):
            return format_html(
                '<img src="{}" style="max-height:300px;max-width:500px;border:1px solid #ccc" />',
                src
            )
        return 'Фото не загружено'


class StatusMixin:
    """Добавляет цветную колонку «Статус»."""

    @admin.display(description='Статус', ordering='approved')
    def status_badge(self, obj):
        if obj.approved:
            return format_html(
                '<span style="background:#2a8020;color:#fff;padding:2px 8px;'
                'border-radius:3px;font-size:11px">ОДОБРЕНО</span>'
            )
        return format_html(
            '<span style="background:#c06010;color:#fff;padding:2px 8px;'
            'border-radius:3px;font-size:11px">ОЖИДАЕТ</span>'
        )


# ──────────────────────────────────────────────────────────────
# ГЕРОИ ВОЙНЫ
# ──────────────────────────────────────────────────────────────

@admin.register(UserHero)
class UserHeroAdmin(SpellMixin, PhotoMixin, StatusMixin, admin.ModelAdmin):
    list_display = [
        'name', 'rank', 'years', 'status_badge',
        'photo_preview_thumb', 'spell_status', 'created_at',
    ]
    list_filter = ['approved', 'created_at']
    search_fields = ['name', 'rank', 'bio', 'award']
    actions = [action_approve, action_unapprove]
    readonly_fields = ['uid', 'session_key', 'spell_errors', 'created_at', 'photo_preview_large']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'rank', 'years', 'unit', 'award'),
        }),
        ('Биография', {
            'fields': ('bio',),
        }),
        ('Фотография', {
            'fields': ('photo_preview_large',),
        }),
        ('Модерация', {
            'fields': ('approved', 'spell_errors'),
            'description': (
                'Поставьте галочку «Одобрено», чтобы запись появилась на сайте для всех. '
                'Сохраните страницу для применения изменений.'
            ),
        }),
        ('Служебная информация', {
            'fields': ('uid', 'session_key', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('approved', '-created_at')


# ──────────────────────────────────────────────────────────────
# ФОТО-ХРОНИКА
# ──────────────────────────────────────────────────────────────

@admin.register(UserKhronika)
class UserKhronikaAdmin(SpellMixin, PhotoMixin, StatusMixin, admin.ModelAdmin):
    list_display = [
        'title', 'get_section_display_col', 'status_badge',
        'photo_preview_thumb', 'spell_status', 'created_at',
    ]
    list_filter = ['approved', 'section', 'created_at']
    search_fields = ['title', 'bio']
    actions = [action_approve, action_unapprove]
    readonly_fields = ['uid', 'session_key', 'spell_errors', 'created_at', 'photo_preview_large']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'section', 'bio'),
        }),
        ('Фотография', {
            'fields': ('photo_preview_large',),
        }),
        ('Модерация', {
            'fields': ('approved', 'spell_errors'),
        }),
        ('Служебная информация', {
            'fields': ('uid', 'session_key', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Раздел', ordering='section')
    def get_section_display_col(self, obj):
        return obj.get_section_display()

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('approved', '-created_at')


# ──────────────────────────────────────────────────────────────
# ПИСЬМА С ФРОНТА
# ──────────────────────────────────────────────────────────────

@admin.register(UserLetter)
class UserLetterAdmin(SpellMixin, StatusMixin, admin.ModelAdmin):
    list_display = [
        'sender', 'year', 'to_person', 'status_badge',
        'text_preview', 'spell_status', 'created_at',
    ]
    list_filter = ['approved', 'year', 'created_at']
    search_fields = ['sender', 'to_person', 'text', 'year']
    actions = [action_approve, action_unapprove]
    readonly_fields = ['uid', 'session_key', 'spell_errors', 'created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Основная информация', {
            'fields': ('sender', 'year', 'to_person'),
        }),
        ('Текст письма', {
            'fields': ('text',),
        }),
        ('Модерация', {
            'fields': ('approved', 'spell_errors'),
        }),
        ('Служебная информация', {
            'fields': ('uid', 'session_key', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Начало текста')
    def text_preview(self, obj):
        return obj.text[:80] + ('...' if len(obj.text) > 80 else '')

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('approved', '-created_at')
