#!/bin/bash
# ============================================================
#  deploy_server.sh — автоматическая настройка VPS-сервера
#  Запускать на сервере под root (или через sudo)
#  Ubuntu 22.04 LTS
#
#  Использование:
#    chmod +x deploy_server.sh
#    sudo ./deploy_server.sh
# ============================================================

set -e   # остановить скрипт при любой ошибке

# ── Переменные — измените под свой проект ────────────────────
PROJECT_DIR="/home/ubuntu/wwii_backend"   # куда загрузить проект
PYTHON="python3"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="wwii"                        # имя systemd-сервиса
NGINX_CONF="/etc/nginx/sites-available/wwii"

echo "======================================"
echo "  Деплой «Фронтовой альбом»"
echo "======================================"

# ── 1. Обновление системы ────────────────────────────────────
echo "[1/7] Обновление системы..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv nginx

# ── 2. Создание виртуального окружения ───────────────────────
echo "[2/7] Создание виртуального окружения..."
cd "$PROJECT_DIR"
$PYTHON -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# ── 3. Установка зависимостей ────────────────────────────────
echo "[3/7] Установка Python-пакетов..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# ── 4. Подготовка Django ─────────────────────────────────────
echo "[4/7] Подготовка Django..."
export DJANGO_SETTINGS_MODULE=wwii_backend.settings_prod

mkdir -p logs
python setup_template.py
python manage.py migrate --run-syncdb
python manage.py collectstatic --noinput

# ── 5. Systemd-сервис для Gunicorn ───────────────────────────
echo "[5/7] Настройка systemd-сервиса..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Gunicorn — Фронтовой альбом
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment="DJANGO_SETTINGS_MODULE=wwii_backend.settings_prod"
Environment="DJANGO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --workers 2 \\
    --bind 127.0.0.1:8000 \\
    --timeout 120 \\
    --access-logfile $PROJECT_DIR/logs/access.log \\
    --error-logfile  $PROJECT_DIR/logs/gunicorn.log \\
    wwii_backend.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# ── 6. Nginx ─────────────────────────────────────────────────
echo "[6/7] Настройка Nginx..."
SERVER_IP=$(hostname -I | awk '{print $1}')

cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name $SERVER_IP _;

    # Статические файлы — Nginx отдаёт напрямую (быстро)
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 7d;
    }

    # Все остальные запросы → Gunicorn
    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              \$host;
        proxy_set_header   X-Real-IP         \$remote_addr;
        proxy_set_header   X-Forwarded-For   \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;

        # Увеличенный таймаут для большого HTML-файла (9.5 MB)
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;

        # Буферизация ответа — важно для большого файла
        proxy_buffering    on;
        proxy_buffer_size  16k;
        proxy_buffers      8 64k;
    }

    # Увеличить лимит размера загружаемых файлов (фото пользователей)
    client_max_body_size 10M;
}
EOF

# Включить сайт
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/wwii
rm -f /etc/nginx/sites-enabled/default   # убрать тестовую страницу Nginx
nginx -t && systemctl reload nginx

# ── 7. Firewall ──────────────────────────────────────────────
echo "[7/7] Настройка firewall..."
ufw allow OpenSSH   2>/dev/null || true
ufw allow 'Nginx HTTP' 2>/dev/null || true
ufw --force enable  2>/dev/null || true

# ── Готово ───────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  Деплой завершён!"
echo "======================================"
echo ""
echo "  Сайт:    http://$SERVER_IP"
echo "  Админка: http://$SERVER_IP/admin"
echo ""
echo "  Логи Gunicorn: $PROJECT_DIR/logs/gunicorn.log"
echo "  Логи Nginx:    /var/log/nginx/error.log"
echo ""
echo "  Следующий шаг — создать администратора:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  export DJANGO_SETTINGS_MODULE=wwii_backend.settings_prod"
echo "  python manage.py createsuperuser"
echo "======================================"
