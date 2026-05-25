#!/bin/bash
echo "==> Starting build.sh..."

# 1. Install dependencies from requirements.txt
echo "==> Installing Python dependencies..."
pip install -r requirements.txt

# 2. Collect static files
echo "==> Collecting static files..."
python myapi/manage.py collectstatic --noinput --clear

# 3. Run database migrations
echo "==> Running migrations..."
python myapi/manage.py migrate --noinput

echo "==> build.sh complete!"
