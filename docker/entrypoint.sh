#!/bin/sh
set -e

mkdir -p /app/data /app/media /app/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "$SITE_DOMAIN" ]; then
  python manage.py shell -c "
from django.contrib.sites.models import Site
from django.conf import settings
site = Site.objects.get(pk=settings.SITE_ID)
site.domain = '${SITE_DOMAIN}'.strip()
site.name = 'Claaxy Log'
site.save()
print(f'Site updated: {site.domain}')
"
fi

exec gunicorn claaxy_log.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
