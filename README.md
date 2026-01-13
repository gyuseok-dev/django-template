# 병원 ERP 시스템 <!-- omit from toc -->

Django Unfold 테마를 기반으로 구축된 병원 운영 관리 시스템입니다. 환자 진료 기록, 내원 경로 관리, 엑셀 데이터 업로드 및 실시간 통계 대시보드 기능을 제공합니다.

- [Unfold](https://github.com/unfoldadmin/django-unfold) - Django Admin 테마
- [Django Import-Export](https://github.com/django-import-export/django-import-export) - 엑셀 Import/Export

## 목차 <!-- omit from toc -->

- [설치](#설치)
- [개발 환경](#개발-환경)
- [샘플 데이터 로딩](#샘플-데이터-로딩)
- [테스트](#테스트)
- [통계 데이터 갱신](#통계-데이터-갱신)
- [주요 기능](#주요-기능)
- [커스텀 대시보드](#커스텀-대시보드)
- [프로젝트 구조](#프로젝트-구조)
- [기술 스택](#기술-스택)

## 설치

먼저 `.env` 파일을 생성하여 환경 변수를 설정합니다. 개발 환경에서는 `DEBUG=1`로 설정하고, `SECRET_KEY`는 안전한 랜덤 문자열로 설정하세요.

```bash
git clone <repository-url>
cd hospital-erp
```

### Docker Compose 사용 (권장)

Docker Compose를 사용하여 간단하게 실행할 수 있습니다.

```bash
docker compose up
```

슈퍼유저를 생성합니다 (어드민 접속을 위해 필수).

```bash
docker compose exec web python manage.py createsuperuser
```

### 로컬 환경 설정

Python 3.12 이상과 uv가 설치되어 있어야 합니다.

```bash
# uv 설치 (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync

# 데이터베이스 마이그레이션
uv run python manage.py migrate

# 슈퍼유저 생성
uv run python manage.py createsuperuser

# 개발 서버 실행
uv run python manage.py runserver
```

브라우저에서 http://localhost:8000/admin/ 으로 접속합니다.

## 개발 환경

### Tailwind CSS

프론트엔드 스타일링에 Tailwind CSS v4를 사용합니다.

```bash
# Tailwind CSS 빌드 (프로덕션)
npm run tailwind:build

# Tailwind CSS 개발 모드 (파일 변경 감지)
npm run tailwind:watch
```

### 코드 품질 도구

프로젝트는 다음 도구들을 사용하여 코드 품질을 관리합니다.

#### Pre-commit (권장)

커밋 전에 자동으로 코드 품질 검사를 실행합니다.

```bash
# pre-commit 훅 설치 (최초 1회)
uv run pre-commit install

# 이제 git commit 시 자동으로 다음 검사가 실행됩니다:
# - Ruff 린팅 및 포맷팅
# - mypy 타입 체크
# - 파일 끝 빈 줄, trailing whitespace 등

# 수동으로 모든 파일 검사
uv run pre-commit run --all-files
```

#### 개별 도구 실행

```bash
# Ruff로 코드 린팅
uv run ruff check .

# Ruff로 자동 수정
uv run ruff check --fix .

# 코드 포맷팅
uv run ruff format .

# mypy로 타입 체크
uv run mypy .
```

### 개발 서버 실행

```bash
# Django 개발 서버
uv run python manage.py runserver

# Tailwind CSS watch와 함께 실행 (별도 터미널)
npm run tailwind:watch
```

### 디버깅

#### Docker 환경에서 디버깅

Docker Compose로 실행 중인 애플리케이션을 원격 디버깅할 수 있습니다.

**1. 디버그 모드로 Docker Compose 실행**

```bash
docker compose -f docker-compose.yml -f docker-compose.debug.yml up
```

**2. 디버거 대기 확인**

로그에서 다음 메시지를 확인하세요:
```
Waiting for client to attach...
```

**3. VSCode에서 디버거 연결**

- F5 키를 누르거나 Run and Debug 패널 열기
- "Python Debugger: Docker Remote Attach" 선택
- 디버거가 연결되면 Django 서버가 시작됩니다

**4. Breakpoint 사용**

- VSCode에서 원하는 줄에 breakpoint 설정 (빨간 점 클릭)
- 브라우저에서 해당 코드가 실행되는 페이지 접속
- 코드가 breakpoint에서 멈추고 변수 확인, step over/into 등 가능

**참고**:
- 디버거 포트: 5678
- 코드 변경 시 auto-reload 비활성화됨 (디버깅 안정성)
- 디버거 연결 전까지 서버가 시작되지 않음

#### 로컬 환경에서 디버깅

```bash
# VSCode에서 "Python Debugger: Django (Local)" 실행 (F5)
# 또는 코드에 직접 breakpoint() 추가
```

## 샘플 데이터 로딩

설치 후 데이터베이스가 비어있을 경우, 샘플 데이터를 생성하여 대시보드를 테스트할 수 있습니다.

### 로컬 환경

## 테스트

프로젝트는 Playwright를 사용한 E2E 테스트를 포함합니다.

### 로컬 환경에서 테스트 실행

```bash
# Playwright 브라우저 설치 (최초 1회)
uv run playwright install --with-deps chromium

# 개발 서버가 실행 중인 상태에서 테스트 실행
uv run pytest
```

### Docker 환경에서 테스트 실행

```bash
# Docker Compose로 서비스 시작
docker compose up -d

# 테스트 실행 (호스트에서)
uv run playwright install --with-deps chromium
uv run pytest
```

### CI/CD

GitHub Actions를 통해 자동화된 테스트가 실행됩니다. 모든 브랜치에 대한 push와 pull request에서 다음 작업을 수행합니다:

- **코드 품질 검사**: pre-commit을 통한 린팅, 포맷팅, 타입 체크
- **서비스 시작**: Docker Compose로 애플리케이션 실행
- **E2E 테스트**: Playwright를 사용한 UI 테스트

워크플로우 설정은 `.github/workflows/ci.yml`에서 확인할 수 있습니다.

## 통계 데이터 갱신

통계 데이터는 마감일지 저장 시 자동으로 갱신되지만, 필요한 경우 수동으로 갱신할 수 있습니다.

### Django Shell에서 직접 실행

```bash
# Django shell 실행
uv run python manage.py shell
```

```python
# shell에서 실행
from record.signals import update_global_statistics

# 전역 통계 갱신 (최고 매출, 최고 환자수, 요일별 최고 등)
update_global_statistics()
```

### 특정 월의 통계 갱신

```python
from record.signals import update_monthly_statistics_for_date
from datetime import date

# 특정 날짜가 속한 월의 통계 갱신
update_monthly_statistics_for_date(date(2024, 12, 1))
```

### 일별 통계 갱신

```python
from record.signals import update_daily_statistics
from record.models import ManualRecord

# 특정 마감일지의 통계 갱신
manual_record = ManualRecord.objects.get(date='2024-12-01')
update_daily_statistics(ManualRecord, manual_record, False)
```

## 주요 기능

### 환자 진료 기록 관리
- ✅ 환자별 진료 기록 관리
- ✅ 주민번호 자동 마스킹 처리
- ✅ 엑셀 일괄 업로드/다운로드 (한글 컬럼명 지원)
- ✅ 차트번호, 내원일, 진료실별 필터링
- ✅ 환자 이름 검색 기능
- ✅ 보험 유형 및 담당의 관리

### 내원 경로 관리
- ✅ 환자 내원 경로 추적 (인터넷, 간판, 소개 등)
- ✅ 엑셀 업로드를 통한 대량 데이터 관리
- ✅ 통계 행 자동 제거 (【소계】, 【총계】)
- ✅ 내원 경로별 필터링 및 검색

### 마감일지 관리
- ✅ 일일 마감 데이터 관리
- ✅ 급여/비급여/조합청구액 자동 계산
- ✅ 미수 발생 및 입금 관리
- ✅ 총진료비 및 총매출 자동 계산

### Django Admin
- ✅ Unfold 테마 기반의 현대적인 UI
- ✅ Import/Export 기능으로 엑셀 데이터 관리
- ✅ 한글 컬럼명 자동 매핑
- ✅ 중복 데이터 자동 체크
- ✅ 직관적인 사이드바 네비게이션

## 커스텀 대시보드

이 프로젝트는 여러 커스텀 대시보드를 포함하고 있습니다. 대시보드에 사용된 모든 위젯과 차트는 시연용으로 제작되었으며 Unfold의 기본 기능은 아닙니다. 실제 데이터를 표시하려면 데이터베이스에서 템플릿으로 추가 데이터를 전달해야 합니다.

**포함된 대시보드:**
- 병원 현황 (일평균) - 일평균 내원 환자, 건당 진료비 통계
- 그래프 현황 - 월별 매출 및 환자 추이 그래프
- 비급여 치료 - 비급여 치료 현황
- 환자 차트 - 환자별 진료 기록 조회
- 최고 매출 - 매출 순위 통계
- 병원 일지 - 일별 매출 및 통계 캘린더

모든 커스텀 대시보드 템플릿은 `record/templates/admin/` 디렉토리에 위치합니다. 대시보드 로직은 `record/admin.py`의 각 Dashboard Admin 클래스의 `changelist_view` 메서드에서 처리됩니다.

## 프로젝트 구조

```
.
├── app/                      # Django 프로젝트 설정
│   ├── settings.py          # 설정 파일 (Unfold, CORS, DB 설정 등)
│   ├── urls.py              # URL 라우팅
│   ├── styles.css           # Tailwind CSS 소스
│   └── static/              # 빌드된 CSS
├── core/                     # 공통 모델 (TimeStampedModel 등)
├── dashboard/                # 대시보드 앱
│   ├── models.py            # 통계 관련 모델
│   └── admin.py             # 대시보드 Admin
├── hospital/                 # 병원 관련 앱
│   ├── models.py            # 병원 모델
│   └── admin.py             # 병원 Admin
├── record/                   # 진료 기록 관리 앱
│   ├── models.py            # PatientRecord, VisitChannelRecord, ManualRecord
│   ├── admin.py             # Admin 커스터마이징
│   ├── forms.py             # 폼 정의
│   ├── signals.py           # 통계 자동 갱신 시그널
│   ├── views.py             # API 뷰
│   └── templates/           # 커스텀 템플릿
├── user/                     # 사용자 관리 앱
│   ├── models.py            # CustomUser 모델
│   └── admin.py             # 사용자 Admin
├── tests/                    # Playwright E2E 테스트
├── .github/workflows/        # GitHub Actions CI/CD
├── pyproject.toml           # Python 의존성 (uv)
├── package.json             # Node.js 의존성 (Tailwind CSS)
├── docker-compose.yml       # Docker Compose 설정
└── Dockerfile               # Docker 이미지 정의
```

## 기술 스택

### Backend
- **Framework**: Django 5.0.2
- **API**: Django REST Framework 3.14.0
- **Database**: PostgreSQL 15 (프로덕션), SQLite (개발)
- **Admin UI**: Django Unfold 0.69+
- **데이터 처리**: pandas, openpyxl, django-import-export
- **모니터링**: Sentry SDK

### Frontend
- **CSS Framework**: Tailwind CSS v4
- **Admin 테마**: Django Unfold (현대적이고 반응형 UI)

### 개발 도구
- **의존성 관리**: uv (Python), npm (Node.js)
- **코드 품질**: Ruff (린팅 및 포맷팅), mypy (타입 체크), pre-commit (Git 훅)
- **테스트**: pytest, Playwright (E2E 테스트)
- **CI/CD**: GitHub Actions

### 배포
- **서버**: Gunicorn
- **정적 파일**: Whitenoise
- **컨테이너**: Docker, Docker Compose
- **인프라**: AWS Elastic Beanstalk (선택사항)

## 라이선스

MIT
