FROM python:3.12-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /code

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency file
COPY pyproject.toml /code/

# Install Python dependencies (including test dependencies)
RUN uv pip install --system -r pyproject.toml
RUN uv pip install --system factory-boy pytest-django pytest-cov faker

# Copy project files
COPY . /code

# Collect static files
RUN python manage.py collectstatic --noinput

# 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 엔트리포인트 설정
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "app.wsgi"]
