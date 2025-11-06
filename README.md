# Django Template

Django REST API 템플릿 프로젝트입니다. uv를 사용하여 의존성을 관리합니다.

## 사전 요구사항

- Python 3.11 이상
- uv (Python 패키지 매니저)

## uv 설치

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 프로젝트 설정

### 1. 의존성 설치
```bash
uv sync
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 필요한 환경 변수를 설정하세요.

### 3. 데이터베이스 마이그레이션
```bash
uv run python manage.py migrate
```

### 4. 개발 서버 실행
```bash
uv run python manage.py runserver
```

## 주요 명령어

### Django 관리 명령어
```bash
# 마이그레이션 생성
uv run python manage.py makemigrations

# 마이그레이션 적용
uv run python manage.py migrate

# 슈퍼유저 생성
uv run python manage.py createsuperuser

# 정적 파일 수집
uv run python manage.py collectstatic
```

### 의존성 관리
```bash
# 의존성 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>

# 의존성 제거
uv remove <package-name>

# 의존성 업데이트
uv sync --upgrade
```

## Docker 사용

### 이미지 빌드
```bash
docker build -t django-template .
```

### 컨테이너 실행
```bash
docker run -p 8000:8000 django-template
```

## 프로젝트 구조

```
.
├── app/                # 메인 Django 애플리케이션
├── user/               # 사용자 관리 앱
├── manage.py           # Django 관리 스크립트
├── pyproject.toml      # 프로젝트 메타데이터 및 의존성
├── uv.lock             # 의존성 잠금 파일
└── Dockerfile          # Docker 이미지 정의
```

## 포함된 패키지

- Django 5.0.2
- Django REST Framework 3.14.0
- django-cors-headers 4.3.1
- psycopg2-binary 2.9.9
- python-dotenv 1.0.1
- gunicorn 21.2.0
- whitenoise 6.9.0

## 라이선스

MIT
