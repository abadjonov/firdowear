# Firdo — VPS'ga deploy (Docker Compose)

Stek: **PostgreSQL 16** (`db`) · **Django + Gunicorn** (`web`) · **Nginx** (`nginx`) · **Certbot / Let's Encrypt** (`certbot`).
Statik fayllar WhiteNoise orqali, media fayllar nginx orqali beriladi.

## 1. Server tayyorlash (Ubuntu 22.04/24.04)

```bash
sudo apt update && sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # qayta login qiling
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

DNS: `firdo.uz` va `www.firdo.uz` uchun **A-yozuv** server IP manziliga yo'naltirilgan bo'lishi shart.

## 2. Kodni olish va `.env`

```bash
git clone https://github.com/abadjonov/firdowear.git && cd firdowear
cp .env.example .env
nano .env
```

Production uchun majburiy qiymatlar:

```ini
SECRET_KEY=<python3 -c "import secrets;print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=firdo.uz,www.firdo.uz
CSRF_TRUSTED_ORIGINS=https://firdo.uz,https://www.firdo.uz
SITE_URL=https://firdo.uz
DOMAIN=firdo.uz
LETSENCRYPT_EMAIL=siz@example.com
POSTGRES_PASSWORD=<kuchli-parol>
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

`DATABASE_URL` ni yozish shart emas — compose uni `db` servisiga avtomatik o'rnatadi.
(Lokalda `DATABASE_URL` bo'sh bo'lsa SQLite ishlatiladi.)

## 3. SSL va birinchi ishga tushirish

```bash
./deploy/init-letsencrypt.sh              # haqiqiy sertifikat
# STAGING=1 ./deploy/init-letsencrypt.sh  # avval sinab ko'rish uchun
```

Skript: vaqtinchalik sertifikat yaratadi → `db`, `web`, `nginx` ni ko'taradi → Let's Encrypt'dan
haqiqiy sertifikat oladi → nginx'ni qayta yuklaydi. Keyinchalik `certbot` har 12 soatda yangilashni
tekshiradi, nginx esa har 12 soatda konfiguratsiyani qayta o'qiydi.

Migratsiyalar `web` konteyneri ishga tushganda avtomatik bajariladi.

## 4. Admin va boshlang'ich ma'lumotlar

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_catalog     # kategoriyalar, o'lchamlar, ranglar
```

Admin: `https://firdo.uz/admin/`

## 5. Yangilash (yangi versiya)

```bash
git pull
docker compose up -d --build web
docker compose image prune -f
```

## 6. Zaxira nusxa (backup)

```bash
# Baza
docker compose exec -T db pg_dump -U firdo firdo | gzip > backup_$(date +%F).sql.gz
# Tiklash
gunzip -c backup_2026-01-01.sql.gz | docker compose exec -T db psql -U firdo firdo
# Media (rasmlar)
docker run --rm -v firdowear_media:/m -v $PWD:/b alpine tar czf /b/media_$(date +%F).tgz -C /m .
```

Cron misoli (har kuni 03:00): `0 3 * * * cd /home/USER/firdowear && docker compose exec -T db pg_dump -U firdo firdo | gzip > ~/backups/db_$(date +\%F).sql.gz`

## 7. Foydali buyruqlar

| Vazifa | Buyruq |
|---|---|
| Loglar | `docker compose logs -f web nginx` |
| Holat | `docker compose ps` |
| Django shell | `docker compose exec web python manage.py shell` |
| Tarjimalarni yangilash | `docker compose exec web python manage.py compilemessages` |
| Health-check | `curl https://firdo.uz/healthz` → `ok` |

## Xavfsizlik (DEBUG=False bo'lganda avtomatik)

HTTPS redirect, HSTS (30 kun, `SECURE_HSTS_SECONDS` bilan o'zgartiriladi), secure cookie'lar,
`X-Forwarded-Proto` orqali proxy SSL, `X-Frame-Options: DENY`, nosniff. Tekshirish:
`docker compose exec web python manage.py check --deploy`.

Brendlangan xato sahifalari: `templates/404.html`, `templates/500.html` (500 — mustaqil, bazaga murojaat qilmaydi).
