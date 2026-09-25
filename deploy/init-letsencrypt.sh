#!/usr/bin/env bash
# Birinchi marta Let's Encrypt SSL sertifikatini olish.
# Ishlatish:  ./deploy/init-letsencrypt.sh        (loyiha ildizida, .env tayyor bo'lganda)
#   STAGING=1 ./deploy/init-letsencrypt.sh       — sinov uchun (limitga tushmaslik)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then echo "❌ .env topilmadi (.env.example dan nusxa oling)"; exit 1; fi
# .env ichida probelli qiymatlar bo'lishi mumkin, shuning uchun faqat keraklilarini o'qiymiz
env_get() { grep -E "^$1=" .env | tail -n1 | cut -d= -f2- | sed -e 's/^["\x27]//' -e 's/["\x27]$//'; }
DOMAIN="${DOMAIN:-$(env_get DOMAIN)}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-$(env_get LETSENCRYPT_EMAIL)}"

: "${DOMAIN:?DOMAIN .env da berilmagan}"
: "${LETSENCRYPT_EMAIL:?LETSENCRYPT_EMAIL .env da berilmagan}"
STAGING="${STAGING:-0}"
RSA_KEY_SIZE=4096
DATA_PATH="./deploy/certbot"
DOMAINS=("$DOMAIN" "www.$DOMAIN")

if docker compose version >/dev/null 2>&1; then DC="docker compose"; else DC="docker-compose"; fi

if [ -d "$DATA_PATH/conf/live/$DOMAIN" ]; then
  read -rp "Sertifikat allaqachon bor ($DOMAIN). Qayta olinsinmi? (y/N) " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ] || exit 0
fi

mkdir -p "$DATA_PATH/conf" "$DATA_PATH/www"

echo "### $DOMAIN uchun vaqtinchalik (dummy) sertifikat yaratish..."
LIVE="/etc/letsencrypt/live/$DOMAIN"
mkdir -p "$DATA_PATH/conf/live/$DOMAIN"
$DC run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '$LIVE/privkey.pem' -out '$LIVE/fullchain.pem' -subj '/CN=localhost'" certbot

echo "### nginx va ilovani ishga tushirish..."
$DC up -d --build db web nginx

echo "### Vaqtinchalik sertifikatni o'chirish..."
$DC run --rm --entrypoint "\
  rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

echo "### Let's Encrypt sertifikatini so'rash..."
domain_args=""
for d in "${DOMAINS[@]}"; do domain_args="$domain_args -d $d"; done
staging_arg=""
[ "$STAGING" != "0" ] && staging_arg="--staging"

$DC run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg $domain_args \
    --email $LETSENCRYPT_EMAIL --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos --no-eff-email --force-renewal" certbot

echo "### nginx'ni qayta yuklash..."
$DC exec nginx nginx -s reload
$DC up -d certbot
echo "✅ Tayyor: https://$DOMAIN"
