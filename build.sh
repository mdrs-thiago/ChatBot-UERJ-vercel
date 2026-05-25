#!/bin/bash
echo "==> Starting build.sh..."

# 1. Collect static files
echo "==> Collecting static files..."
python myapi/manage.py collectstatic --noinput --clear

# 2. Run database migrations
echo "==> Running migrations..."
python myapi/manage.py migrate --noinput

echo "==> build.sh complete!"
