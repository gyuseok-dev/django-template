# 병원 ERP 프로젝트 코딩 표준

## CSS 스타일링 규칙

### ✅ Tailwind CSS 전용 사용

**모든 CSS는 Tailwind CSS 유틸리티 클래스로만 작성해야 합니다.**

#### 허용되는 방법:
```html
<!-- ✅ 올바른 방법: Tailwind 유틸리티 클래스 사용 -->
<div class="p-10 max-w-screen-xl mx-auto">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">제목</h1>
    <div class="bg-gray-50 rounded-lg shadow-sm p-5">
        콘텐츠
    </div>
</div>
```

#### 금지되는 방법:
```html
<!-- ❌ 잘못된 방법: 인라인 스타일 -->
<div style="padding: 40px; max-width: 1200px;">
    ...
</div>

<!-- ❌ 잘못된 방법: <style> 태그 사용 -->
<style>
    .custom-container {
        padding: 40px;
    }
</style>

<!-- ❌ 잘못된 방법: 별도 CSS 파일 -->
<link rel="stylesheet" href="custom.css">
```

#### 예외 사항:
- 매우 복잡한 애니메이션이나 Tailwind로 구현이 불가능한 경우에만 `settings.py`의 `UNFOLD['STYLES']`에 추가 가능
- 그러나 대부분의 경우 Tailwind의 `@apply` 디렉티브나 JIT 모드로 해결 가능

### 이유:
1. **일관성**: 프로젝트 전체에서 동일한 디자인 시스템 사용
2. **유지보수성**: Tailwind 클래스는 표준화되어 있어 이해하기 쉬움
3. **성능**: Unfold가 이미 Tailwind를 내장하고 있어 추가 CSS 파일 불필요
4. **개발 속도**: 유틸리티 클래스를 사용하면 빠른 UI 개발 가능

---

## 프레임워크 및 라이브러리

### Django Admin UI
- **django-unfold** 사용 (Tailwind CSS 기반)
- 커스텀 어드민 페이지는 `templates/admin/` 디렉토리에 작성
- Unfold 컴포넌트 우선 사용

### Python 코드 스타일
- **Ruff** 린터 사용
- 타입 힌트 적극 활용
- Docstring 작성 권장

---

## 파일 구조 규칙

### 템플릿
- Admin 템플릿: `templates/admin/`
- 공통 템플릿: `templates/`
- 앱별 템플릿: `<app_name>/templates/<app_name>/`

### Static 파일
- 이미지: `static/images/`
- 생성된 파일: `staticfiles/` (빌드 시 자동 생성)

---

*마지막 업데이트: 2025-12-10*
