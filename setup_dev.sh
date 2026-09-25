#!/usr/bin/env bash
# Lokal ishga tushirish: venv, .env, baza, boshlang'ich ma'lumotlar, admin (admin / admin12345)
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || sed "s/change-me/$(.venv/bin/python -c 'import secrets;print(secrets.token_urlsafe(40))')/" .env.example > .env
.venv/bin/python manage.py migrate -v0
.venv/bin/python manage.py seed_catalog
[ "${DEMO:-1}" = 1 ] && .venv/bin/python manage.py demo_products
DJANGO_SUPERUSER_PASSWORD=${ADMIN_PASSWORD:-admin12345} .venv/bin/python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>/dev/null || true
echo "Tayyor. Ishga tushirish: .venv/bin/python manage.py runserver 0.0.0.0:8000"
