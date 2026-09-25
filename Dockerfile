FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x deploy/entrypoint.sh \
    && SECRET_KEY=build-only DEBUG=False python manage.py collectstatic --noinput \
    && useradd --create-home --uid 1000 app \
    && mkdir -p /app/media && chown -R app:app /app/media /app/staticfiles

USER app
EXPOSE 8000
ENTRYPOINT ["deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
