#!/bin/bash
set -e

echo "=== Simple Hotel Setup ==="

if ! command -v docker &> /dev/null; then
    echo "[*] Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "[*] Docker installed. You may need to re-login."
    echo "[*] Re-run: bash setup.sh"
    exit 0
fi

echo "[1/3] Copy .env.example to .env if missing..."
[ ! -f .env ] && cp .env.example .env && echo "PLEASE EDIT .env with your real keys!" && exit 0 || true

echo "[2/3] Building and starting container..."
docker compose up -d --build

echo "[3/3] Running database migrations..."
docker compose exec web python manage.py migrate --noinput

echo ""
echo "All set! Visit: http://$(curl -s ifconfig.me)"
echo "Admin:   http://$(curl -s ifconfig.me)/admin/"
echo ""
echo "Create superuser: docker compose exec web python manage.py createsuperuser"
