"""
API-представления для пользовательского контента сайта «Фронтовой альбом».

Эндпоинты:
  GET  /api/heroes/          — список героев (одобренные + свои)
  POST /api/heroes/          — добавить героя
  DELETE /api/heroes/<uid>/  — удалить своего героя

  GET  /api/khronika/           — список фото хроники
  POST /api/khronika/           — добавить фото
  DELETE /api/khronika/<uid>/   — удалить своё фото

  GET  /api/letters/         — список писем
  POST /api/letters/         — добавить письмо
  DELETE /api/letters/<uid>/ — удалить своё письмо

  GET  /api/spell-check/?text=... — проверить текст на ошибки
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect

from .models import UserHero, UserKhronika, UserLetter
from .spell_check import check_text, spell_available

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────

def _ensure_session(request) -> str:
    """Создаёт сессию, если её нет, и возвращает session_key."""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _parse_json(request) -> tuple[dict | None, JsonResponse | None]:
    """Парсит JSON-тело запроса. Возвращает (data, None) или (None, error_response)."""
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError('Ожидается JSON-объект')
        return data, None
    except (json.JSONDecodeError, ValueError) as e:
        return None, JsonResponse({'error': f'Неверный JSON: {e}'}, status=400)


def _str(data: dict, key: str) -> str:
    """Безопасно извлекает и обрезает строку из словаря."""
    return str(data.get(key, '') or '').strip()


# ──────────────────────────────────────────────────────────────
# ГЕРОИ ВОЙНЫ
# ──────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def heroes(request):
    if request.method == 'GET':
        return _heroes_list(request)
    return _heroes_create(request)


def _heroes_list(request):
    """GET /api/heroes/ — одобренные + свои (не одобренные) герои."""
    session_key = request.session.session_key

    # Одобренные видны всем
    qs = list(UserHero.objects.filter(approved=True))

    # Свои неодобренные — только текущему пользователю
    if session_key:
        own_pending = UserHero.objects.filter(session_key=session_key, approved=False)
        qs = list(own_pending) + qs

    data = [_hero_to_dict(h, session_key) for h in qs]
    return JsonResponse(data, safe=False)


def _heroes_create(request):
    """POST /api/heroes/ — добавить героя."""
    body, err = _parse_json(request)
    if err:
        return err

    name = _str(body, 'name')
    bio  = _str(body, 'bio')
    if not name:
        return JsonResponse({'error': 'Поле «Имя» обязательно'}, status=400)
    if not bio:
        return JsonResponse({'error': 'Поле «Биография» обязательна'}, status=400)

    session_key = _ensure_session(request)

    # Проверка орфографии
    errors = check_text(f'{name}. {bio}')

    hero = UserHero.objects.create(
        session_key=session_key,
        name=name,
        rank=_str(body, 'rank'),
        years=_str(body, 'years'),
        unit=_str(body, 'unit'),
        award=_str(body, 'award'),
        bio=bio,
        photo_b64=_str(body, 'src'),
        spell_errors=errors,
    )
    logger.info(f'Новый герой: {hero.name} (сессия {session_key[:8]}...)')
    return JsonResponse(_hero_to_dict(hero, session_key), status=201)


@require_http_methods(['DELETE'])
def hero_delete(request, uid):
    """DELETE /api/heroes/<uid>/ — удалить своего героя."""
    session_key = request.session.session_key
    try:
        hero = UserHero.objects.get(uid=uid)
    except UserHero.DoesNotExist:
        return JsonResponse({'error': 'Запись не найдена'}, status=404)

    if hero.session_key != session_key:
        return JsonResponse({'error': 'Нет прав на удаление этой записи'}, status=403)

    hero.delete()
    logger.info(f'Герой удалён: {uid}')
    return JsonResponse({'ok': True})


def _hero_to_dict(h: UserHero, session_key: str) -> dict:
    return {
        'id':          str(h.uid),
        'name':        h.name,
        'rank':        h.rank,
        'years':       h.years,
        'unit':        h.unit,
        'award':       h.award,
        'bio':         h.bio,
        'src':         h.photo_b64 or '',
        'userAdded':   True,
        'pending':     not h.approved,
        'can_delete':  bool(session_key and h.session_key == session_key),
        'spell_errors': h.spell_errors,
    }


# ──────────────────────────────────────────────────────────────
# ФОТО-ХРОНИКА
# ──────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def khronika(request):
    if request.method == 'GET':
        return _khronika_list(request)
    return _khronika_create(request)


def _khronika_list(request):
    """GET /api/khronika/"""
    session_key = request.session.session_key

    qs = list(UserKhronika.objects.filter(approved=True))
    if session_key:
        own = UserKhronika.objects.filter(session_key=session_key, approved=False)
        qs = list(own) + qs

    data = [_khronika_to_dict(p, session_key) for p in qs]
    return JsonResponse(data, safe=False)


def _khronika_create(request):
    """POST /api/khronika/"""
    body, err = _parse_json(request)
    if err:
        return err

    title = _str(body, 'title')
    bio   = _str(body, 'bio')
    src   = _str(body, 'src')

    if not title:
        return JsonResponse({'error': 'Поле «Подпись» обязательно'}, status=400)
    if not bio:
        return JsonResponse({'error': 'Поле «История фотографии» обязательно'}, status=400)
    if not src:
        return JsonResponse({'error': 'Фотография обязательна'}, status=400)

    section = _str(body, 'section')
    if section not in ('main', 'len'):
        section = 'main'

    session_key = _ensure_session(request)
    errors = check_text(f'{title}. {bio}')

    item = UserKhronika.objects.create(
        session_key=session_key,
        title=title,
        bio=bio,
        section=section,
        photo_b64=src,
        spell_errors=errors,
    )
    logger.info(f'Новое фото хроники: «{item.title}» (сессия {session_key[:8]}...)')
    return JsonResponse(_khronika_to_dict(item, session_key), status=201)


@require_http_methods(['DELETE'])
def khronika_delete(request, uid):
    """DELETE /api/khronika/<uid>/"""
    session_key = request.session.session_key
    try:
        item = UserKhronika.objects.get(uid=uid)
    except UserKhronika.DoesNotExist:
        return JsonResponse({'error': 'Запись не найдена'}, status=404)

    if item.session_key != session_key:
        return JsonResponse({'error': 'Нет прав на удаление'}, status=403)

    item.delete()
    return JsonResponse({'ok': True})


def _khronika_to_dict(p: UserKhronika, session_key: str) -> dict:
    return {
        'id':          str(p.uid),
        'title':       p.title,
        'bio':         p.bio,
        'section':     p.section,
        'src':         p.photo_b64,
        'userAdded':   True,
        'pending':     not p.approved,
        'can_delete':  bool(session_key and p.session_key == session_key),
        'spell_errors': p.spell_errors,
    }


# ──────────────────────────────────────────────────────────────
# ПИСЬМА С ФРОНТА
# ──────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def letters(request):
    if request.method == 'GET':
        return _letters_list(request)
    return _letters_create(request)


def _letters_list(request):
    """GET /api/letters/"""
    session_key = request.session.session_key

    qs = list(UserLetter.objects.filter(approved=True))
    if session_key:
        own = UserLetter.objects.filter(session_key=session_key, approved=False)
        qs = list(own) + qs

    data = [_letter_to_dict(lt, session_key) for lt in qs]
    return JsonResponse(data, safe=False)


def _letters_create(request):
    """POST /api/letters/"""
    body, err = _parse_json(request)
    if err:
        return err

    sender = _str(body, 'sender')
    text   = _str(body, 'text')

    if not sender:
        return JsonResponse({'error': 'Поле «Автор» обязательно'}, status=400)
    if not text:
        return JsonResponse({'error': 'Поле «Текст письма» обязательно'}, status=400)

    session_key = _ensure_session(request)
    errors = check_text(f'{sender}. {text}')

    lt = UserLetter.objects.create(
        session_key=session_key,
        year=_str(body, 'year'),
        sender=sender,
        to_person=_str(body, 'to'),
        text=text,
        spell_errors=errors,
    )
    logger.info(f'Новое письмо: {lt.sender} (сессия {session_key[:8]}...)')
    return JsonResponse(_letter_to_dict(lt, session_key), status=201)


@require_http_methods(['DELETE'])
def letter_delete(request, uid):
    """DELETE /api/letters/<uid>/"""
    session_key = request.session.session_key
    try:
        lt = UserLetter.objects.get(uid=uid)
    except UserLetter.DoesNotExist:
        return JsonResponse({'error': 'Запись не найдена'}, status=404)

    if lt.session_key != session_key:
        return JsonResponse({'error': 'Нет прав на удаление'}, status=403)

    lt.delete()
    return JsonResponse({'ok': True})


def _letter_to_dict(lt: UserLetter, session_key: str) -> dict:
    """Конвертирует письмо в формат, совместимый с фронтендом (afRenderLetter)."""
    # preview — первые 130 символов текста
    preview = lt.text[:130] + ('...' if len(lt.text) > 130 else '')

    # text для модала — разбиваем по двойному переносу (как в оригинальном JS)
    paragraphs = [p.strip() for p in lt.text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [lt.text]

    return {
        'id':          str(lt.uid),
        'year':        lt.year,
        'sender':      lt.sender,
        'to':          lt.to_person,
        'preview':     preview,
        'text':        paragraphs,
        'userAdded':   True,
        'pending':     not lt.approved,
        'can_delete':  bool(session_key and lt.session_key == session_key),
        'spell_errors': lt.spell_errors,
    }


# ──────────────────────────────────────────────────────────────
# ПРОВЕРКА ОРФОГРАФИИ (отдельный эндпоинт для JS)
# ──────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def spell_check_view(request):
    """
    GET  /api/spell-check/?text=...  — проверить текст
    POST /api/spell-check/           — тело: {"text": "..."}
    """
    if request.method == 'GET':
        text = request.GET.get('text', '').strip()
    else:
        body, err = _parse_json(request)
        if err:
            return err
        text = _str(body, 'text')

    if not text:
        return JsonResponse({'errors': [], 'available': spell_available()})

    errors = check_text(text)
    return JsonResponse({
        'errors':    errors,
        'count':     len(errors),
        'available': spell_available(),
    })
