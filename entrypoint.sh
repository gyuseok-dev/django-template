#!/bin/sh

# 에러가 나면 스크립트 즉시 종료
set -e

# 마이그레이션 실행
echo "Running migrations..."
uv run python manage.py migrate --noinput

# 원래 실행하려던 명령어 실행 (예: gunicorn ...)
exec "$@"
