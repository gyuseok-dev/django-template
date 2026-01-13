# 권한 체계 (Permission System)

## 개요

Hospital ERP 시스템은 멀티테넌시(Multi-tenancy) 환경에서 4가지 사용자 역할을 지원합니다.

## 사용자 역할 (User Roles)

### 1. 슈퍼유저 (Superuser)
- **권한**: 모든 권한 (Django 기본)
- **병원 접근**: 모든 병원 접근 가능
- **병원 선택**: 세션에서 병원 선택 가능, 선택하지 않으면 전체 병원 데이터 조회
- **설정**: Django Admin에서 "슈퍼유저" 체크박스

### 2. 대표 (Representative)
- **권한**: 모든 권한 (슈퍼유저와 동일)
- **병원 접근**: 모든 병원 접근 가능
- **병원 선택**: 세션에서 병원 선택 가능, 선택하지 않으면 전체 병원 데이터 조회
- **설정**: Django Admin에서 "대표" 그룹에 추가

### 3. 관리자 (Manager)
- **권한**: 모든 권한 (슈퍼유저와 동일)
- **병원 접근**: **연결된 병원만** 접근 가능
- **병원 선택**: 세션에서 자신의 병원 중 선택, 없으면 첫 번째 병원 자동 선택
- **설정**: Django Admin에서 "관리자" 그룹에 추가 + 병원 연결

### 4. 일반 사용자 (Staff)
- **권한**: 제한된 권한 (필요에 따라 개별 권한 부여)
- **병원 접근**: **연결된 병원만** 접근 가능
- **병원 선택**: 첫 번째 병원 자동 선택
- **설정**: Django Admin에서 필요한 권한만 부여 + 병원 연결

## 권한 설정 방법

### 1. 초기 설정 (자동)

마이그레이션 실행 시 자동으로 "대표", "관리자" 그룹이 생성되고 모든 권한이 부여됩니다.

```bash
python manage.py migrate
```

### 2. 사용자에게 역할 부여

#### Django Admin에서 설정:

1. **대표 권한 부여**
   ```
   Admin > 사용자 > [사용자 선택]
   - "그룹" 섹션에서 "대표" 선택
   - "소속 병원"은 비워두어도 됨 (모든 병원 접근)
   ```

2. **관리자 권한 부여**
   ```
   Admin > 사용자 > [사용자 선택]
   - "그룹" 섹션에서 "관리자" 선택
   - "소속 병원"에서 접근 가능한 병원 선택 (필수)
   ```

3. **일반 사용자**
   ```
   Admin > 사용자 > [사용자 선택]
   - "사용자 권한" 섹션에서 필요한 권한만 선택
   - "소속 병원"에서 접근 가능한 병원 선택 (필수)
   ```

### 3. 권한 재설정 (필요 시)

새로운 모델이 추가되어 권한을 업데이트해야 하는 경우:

```python
# Django Shell
python manage.py shell

from django.contrib.auth.models import Group, Permission

# 모든 권한 가져오기
all_permissions = Permission.objects.all()

# 대표 그룹 업데이트
representative = Group.objects.get(name='대표')
representative.permissions.set(all_permissions)

# 관리자 그룹 업데이트
manager = Group.objects.get(name='관리자')
manager.permissions.set(all_permissions)
```

## 병원 접근 제어 흐름

### Middleware 동작:

```
1. 사용자 로그인
2. TenantMiddleware 실행
   - 세션에서 선택된 병원 ID 확인
   - 슈퍼유저/대표: 모든 병원 접근 가능
   - 관리자/일반: 연결된 병원만 접근 가능
3. Thread-local에 병원 정보 저장
4. View 실행 시 자동으로 병원별 필터링
5. 요청 종료 후 Thread-local 초기화
```

### 쿼리 자동 필터링:

```python
# View에서
patients = Patient.objects.all()

# 자동으로 변환됨
# 슈퍼유저/대표 (병원 선택 안 함): 모든 병원 데이터
# 슈퍼유저/대표 (병원 선택): 선택한 병원 데이터
# 관리자/일반: 연결된 병원 데이터
patients = Patient.objects.filter(hospital=현재병원)
```

## 사용자 메서드

```python
# user/models.py

user.is_representative()        # 대표 여부
user.is_manager()               # 관리자 여부
user.can_access_all_hospitals() # 모든 병원 접근 가능 여부
```

## 예시 시나리오

### 시나리오 1: 대표가 여러 병원 관리

```
1. user1을 "대표" 그룹에 추가
2. 로그인 후 병원 선택 UI에서 "A병원" 선택
3. A병원 데이터만 조회
4. 병원 변경 → "B병원" 선택
5. B병원 데이터만 조회
6. 병원 선택 해제 → 모든 병원 데이터 조회
```

### 시나리오 2: 관리자가 특정 병원만 관리

```
1. user2를 "관리자" 그룹에 추가
2. "소속 병원"에 A병원, B병원 추가
3. 로그인 시 자동으로 A병원 선택 (첫 번째)
4. A병원 데이터만 조회
5. 병원 변경 → B병원 선택 가능
6. C병원은 접근 불가 (소속되지 않음)
```

### 시나리오 3: 동시 로그인

```
# A 컴퓨터
1. user1 로그인
2. 세션에 "A병원" 저장
3. A병원 데이터 조회

# B 컴퓨터 (동일 user1)
1. user1 로그인 (새 세션)
2. 세션에 "B병원" 저장
3. B병원 데이터 조회

→ 각 브라우저 세션이 독립적으로 동작 ✅
```

## 트러블슈팅

### Q: 새로운 모델을 추가했는데 대표/관리자가 접근할 수 없어요

A: 위의 "권한 재설정" 스크립트를 실행하거나, Django Admin에서 수동으로 권한을 추가하세요.

### Q: 사용자가 병원 데이터를 볼 수 없어요

A: 다음을 확인하세요:
1. 사용자가 병원에 연결되어 있는지 ("소속 병원")
2. 세션에 병원 ID가 저장되어 있는지
3. 사용자가 로그아웃 후 다시 로그인했는지

### Q: 슈퍼유저인데 특정 병원 데이터만 보고 싶어요

A: Django Admin에서 병원 선택 UI를 추가하거나, 세션에 `selected_hospital_id`를 설정하세요.

## 참고

- **Middleware**: `core/middleware.py` - TenantMiddleware
- **Manager**: `core/managers.py` - TenantManager, SoftDeleteTenantManager
- **User Model**: `user/models.py` - is_representative(), is_manager(), can_access_all_hospitals()
- **Migration**: `user/migrations/0006_create_role_groups.py` - 그룹 생성
