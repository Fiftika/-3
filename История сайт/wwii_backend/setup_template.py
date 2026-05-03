"""
setup_template.py — подготовка HTML-шаблона для Django.

Копирует wwii_album.html → templates/index.html
и добавляет в него:
  1. {% load static %}  — в самое начало файла
  2. <script src="{% static 'api_override.js' %}"></script>  — перед </body>

Запускать ОДИН РАЗ из папки wwii_backend/:
    python setup_template.py
"""
import shutil
from pathlib import Path

# ── Пути ─────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent                        # wwii_backend/
SOURCE_HTML  = SCRIPT_DIR.parent / 'wwii_album.html'       # wwii_album.html рядом
TEMPLATE_DIR = SCRIPT_DIR / 'templates'
TARGET_HTML  = TEMPLATE_DIR / 'index.html'

# ── Проверки ─────────────────────────────────────────────────
if not SOURCE_HTML.exists():
    print(f'ОШИБКА: файл не найден → {SOURCE_HTML}')
    print('Убедитесь, что wwii_album.html лежит в папке «История сайт»')
    raise SystemExit(1)

TEMPLATE_DIR.mkdir(exist_ok=True)

# ── Копируем HTML ─────────────────────────────────────────────
print(f'Копирую {SOURCE_HTML.name} -> templates/index.html ...')
shutil.copy2(SOURCE_HTML, TARGET_HTML)

# ── Читаем содержимое ─────────────────────────────────────────
print('Добавляю Django-теги...')
content = TARGET_HTML.read_text(encoding='utf-8')

# 1. {% load static %} в самое начало (только если ещё нет)
LOAD_STATIC = "{% load static %}\n"
if LOAD_STATIC not in content:
    content = LOAD_STATIC + content
    print('  + {% load static %} добавлен в начало файла')
else:
    print('  ✓ {% load static %} уже есть')

# 2. <script> с api_override.js перед </body> (только если ещё нет)
OVERRIDE_SCRIPT = '<script src="{% static \'api_override.js\' %}"></script>'
if OVERRIDE_SCRIPT not in content:
    if '</body>' in content:
        content = content.replace(
            '</body>',
            f'\n<!-- Django API override -->\n{OVERRIDE_SCRIPT}\n</body>',
            1  # только первое вхождение
        )
        print('  + api_override.js добавлен перед </body>')
    else:
        # Файл не заканчивается на </body> — добавляем в конец
        content += f'\n{OVERRIDE_SCRIPT}\n'
        print('  + api_override.js добавлен в конец файла (</body> не найден)')
else:
    print('  ✓ api_override.js уже подключён')

# ── Сохраняем ─────────────────────────────────────────────────
TARGET_HTML.write_text(content, encoding='utf-8')

size_mb = TARGET_HTML.stat().st_size / 1024 / 1024
print(f'\nГотово! templates/index.html создан ({size_mb:.1f} MB)')
print('\nСледующие шаги:')
print('  1. pip install -r requirements.txt')
print('  2. python manage.py migrate')
print('  3. python manage.py createsuperuser')
print('  4. python manage.py runserver')
print('  5. Откройте http://127.0.0.1:8000')
print('  6. Панель администратора: http://127.0.0.1:8000/admin')
