"""
Модели для пользовательского контента сайта «Фронтовой альбом».

Три типа контента, которые пользователи могут добавлять:
  - UserHero      — герой войны (имя, звание, биография, фото)
  - UserKhronika  — фотография для раздела «Фото-хроника»
  - UserLetter    — письмо с фронта

Все записи требуют одобрения администратора (approved=False по умолчанию).
Каждая запись привязана к анонимной сессии пользователя (session_key),
чтобы он мог удалять только свои материалы.
"""
import uuid
from django.db import models


class UserHero(models.Model):
    """Герой войны, добавленный пользователем."""

    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='UUID',
        help_text='Уникальный идентификатор для API'
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        db_index=True,
        verbose_name='Ключ сессии',
        help_text='Анонимная сессия пользователя, добавившего запись'
    )

    # ── Основные поля ──
    name = models.CharField(max_length=200, verbose_name='Полное имя')
    rank = models.CharField(max_length=200, blank=True, verbose_name='Воинское звание')
    years = models.CharField(max_length=100, blank=True, verbose_name='Годы жизни')
    unit = models.CharField(max_length=300, blank=True, verbose_name='Воинская часть')
    award = models.CharField(max_length=500, blank=True, verbose_name='Награды')
    bio = models.TextField(verbose_name='Биография')
    photo_b64 = models.TextField(
        blank=True,
        default='',
        verbose_name='Фото (base64)',
        help_text='Фотография в формате data:image/...;base64,...'
    )

    # ── Модерация ──
    approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Одобрено',
        help_text='Только одобренные записи видны всем пользователям'
    )
    spell_errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Орфографические ошибки',
        help_text='Список слов с возможными ошибками (проверяется автоматически)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Герой войны'
        verbose_name_plural = 'Герои войны (от пользователей)'
        ordering = ['-created_at']

    def __str__(self):
        status = '✓' if self.approved else '⏳'
        return f'{status} {self.name}'


class UserKhronika(models.Model):
    """Фотография для раздела «Фото-хроника», добавленная пользователем."""

    SECTION_MAIN = 'main'
    SECTION_LEN  = 'len'
    SECTION_CHOICES = [
        (SECTION_MAIN, 'Общая хроника войны'),
        (SECTION_LEN,  'Блокада Ленинграда'),
    ]

    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='UUID'
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        db_index=True,
        verbose_name='Ключ сессии'
    )

    # ── Основные поля ──
    title = models.CharField(max_length=300, verbose_name='Подпись к фото')
    bio = models.TextField(verbose_name='История фотографии')
    section = models.CharField(
        max_length=10,
        choices=SECTION_CHOICES,
        default=SECTION_MAIN,
        verbose_name='Раздел'
    )
    photo_b64 = models.TextField(
        verbose_name='Фото (base64)',
        help_text='Фотография обязательна'
    )

    # ── Модерация ──
    approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Одобрено'
    )
    spell_errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Орфографические ошибки'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Фото хроники'
        verbose_name_plural = 'Фото хроники (от пользователей)'
        ordering = ['-created_at']

    def __str__(self):
        status = '✓' if self.approved else '⏳'
        section = dict(self.SECTION_CHOICES).get(self.section, self.section)
        return f'{status} [{section}] {self.title}'


class UserLetter(models.Model):
    """Письмо с фронта, добавленное пользователем."""

    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name='UUID'
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        db_index=True,
        verbose_name='Ключ сессии'
    )

    # ── Основные поля ──
    year = models.CharField(max_length=20, blank=True, verbose_name='Год письма')
    sender = models.CharField(max_length=200, verbose_name='Автор письма')
    to_person = models.CharField(max_length=200, blank=True, verbose_name='Кому адресовано')
    text = models.TextField(verbose_name='Текст письма')

    # ── Модерация ──
    approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Одобрено'
    )
    spell_errors = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Орфографические ошибки'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Письмо с фронта'
        verbose_name_plural = 'Письма с фронта (от пользователей)'
        ordering = ['-created_at']

    def __str__(self):
        status = '✓' if self.approved else '⏳'
        year = f' ({self.year})' if self.year else ''
        return f'{status} {self.sender}{year}'
