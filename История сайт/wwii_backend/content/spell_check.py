"""
Модуль проверки орфографии для русского текста.

Использует библиотеку pyspellchecker с русским словарём.
Если библиотека не установлена — функция тихо возвращает пустой список.

Установка: pip install pyspellchecker
"""
import re
import logging

logger = logging.getLogger(__name__)

# Пытаемся загрузить SpellChecker один раз при старте
try:
    from spellchecker import SpellChecker
    _spell = SpellChecker(language='ru')
    SPELL_AVAILABLE = True
    logger.info('Проверка орфографии: pyspellchecker загружен (язык: ru)')
except Exception as e:
    _spell = None
    SPELL_AVAILABLE = False
    logger.warning(f'Проверка орфографии недоступна: {e}')


# Служебные слова, которые не считаем ошибками
_STOP_WORDS = {
    'в', 'на', 'с', 'по', 'из', 'за', 'к', 'о', 'от', 'до', 'у', 'и', 'а',
    'но', 'или', 'не', 'ни', 'бы', 'же', 'ли', 'то', 'что', 'как', 'так',
    'ещё', 'еще', 'уже', 'вот', 'ведь', 'даже', 'всё', 'все', 'это', 'этот',
    'та', 'тот', 'те', 'со', 'во', 'при', 'под', 'над', 'без', 'для', 'об',
    'же', 'ж', 'бы', 'б',
}

# Паттерн для извлечения русских слов (минимум 3 буквы)
_RU_WORD = re.compile(r'[а-яёА-ЯЁ]{3,}')


def check_text(text: str, max_errors: int = 8) -> list[str]:
    """
    Проверяет текст на орфографические ошибки (только русские слова).

    Args:
        text:       Строка для проверки.
        max_errors: Максимальное количество ошибок в ответе.

    Returns:
        Список слов с возможными ошибками (до max_errors штук).
        Пустой список, если ошибок нет или проверка недоступна.
    """
    if not SPELL_AVAILABLE or not text or not text.strip():
        return []

    # Извлекаем только русские слова (минимум 3 символа)
    words = _RU_WORD.findall(text)
    words_lower = [w.lower() for w in words if w.lower() not in _STOP_WORDS]

    if not words_lower:
        return []

    try:
        misspelled = _spell.unknown(words_lower)
        # Убираем слова из стоп-листа, которые могли просочиться
        misspelled = {w for w in misspelled if w not in _STOP_WORDS}
        return sorted(misspelled)[:max_errors]
    except Exception as e:
        logger.error(f'Ошибка при проверке орфографии: {e}')
        return []


def spell_available() -> bool:
    """Возвращает True, если модуль проверки орфографии загружен."""
    return SPELL_AVAILABLE
