#!/bin/bash
echo "==> Starting build.sh..."

# 1. Install dependencies from requirements.txt
echo "==> Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "==> Using uv to install dependencies..."
    uv pip install --system -r requirements.txt
else
    echo "==> Using pip to install dependencies..."
    pip install -r requirements.txt --break-system-packages
fi

# 2. Collect static files
echo "==> Collecting static files..."
python myapi/manage.py collectstatic --noinput --clear

# 3. Run database migrations
echo "==> Running migrations..."
python myapi/manage.py migrate --noinput

echo "==> build.sh complete!"
