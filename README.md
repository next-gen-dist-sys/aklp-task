# AKLP Task Service

학습 과정에서 필요한 할 일(Todo)을 관리하는 서비스입니다. 단일 Task와 Batch(여러 Task 묶음) 관리를 지원합니다.

## 개요

| 항목         | 값                                       |
| ------------ | ---------------------------------------- |
| 포트         | `8001`                                   |
| Base URL     | `/api/v1/tasks`, `/api/v1/batches`       |
| API 문서     | [Swagger UI](http://localhost:8001/docs) |
| 데이터베이스 | `aklp_task`                              |

## 핵심 개념

### Task 상태 (status)

| 상태          | 설명                            |
| ------------- | ------------------------------- |
| `pending`     | 아직 시작하지 않음 (기본값)     |
| `in_progress` | 진행 중                         |
| `completed`   | 완료됨 (completed_at 자동 설정) |

### Task 우선순위 (priority)

| 우선순위 | 설명            |
| -------- | --------------- |
| `high`   | 높은 우선순위   |
| `medium` | 중간 우선순위   |
| `low`    | 낮은 우선순위   |
| `null`   | 우선순위 미설정 |

### Batch

여러 Task를 한 번에 생성하고 그룹화하는 단위입니다. Agent가 학습 단계를 분석하여 여러 Task를 한 번에 생성할 때 사용합니다.

---

## API 엔드포인트

### Task API (`/api/v1/tasks`)

#### 1. Task 생성 (`POST /api/v1/tasks`)

```json
{
  "title": "nginx Pod 생성하기",
  "description": "kubectl run 명령어로 nginx Pod 생성",
  "status": "pending",
  "priority": "high",
  "due_date": "2025-12-07T23:59:59Z",
  "session_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### 2. Task 목록 조회 (`GET /api/v1/tasks`)

| 파라미터     | 타입   | 설명                                                       |
| ------------ | ------ | ---------------------------------------------------------- |
| `page`       | int    | 페이지 번호 (기본: 1)                                      |
| `status`     | string | 상태 필터 (pending/in_progress/completed)                  |
| `session_id` | UUID   | 세션별 필터링                                              |
| `batch_id`   | UUID   | Batch별 필터링                                             |
| `sort_by`    | string | 정렬 기준 (updated_at/created_at/due_date/priority/status) |
| `order`      | string | 정렬 순서 (asc/desc)                                       |

#### 3. Task 상세 조회 (`GET /api/v1/tasks/{task_id}`)

#### 4. Task 수정 (`PUT /api/v1/tasks/{task_id}`)

```json
{
  "status": "completed",
  "priority": "medium"
}
```

> **참고**: `status`를 `completed`로 변경하면 `completed_at`이 자동 설정됩니다.

#### 5. Task 삭제 (`DELETE /api/v1/tasks/{task_id}`)

#### 6. Task 일괄 수정 (`PUT /api/v1/tasks/bulk`)

```json
{
  "tasks": [
    { "id": "uuid-1", "status": "completed" },
    { "id": "uuid-2", "status": "in_progress", "priority": "high" }
  ]
}
```

#### 7. Task 일괄 삭제 (`DELETE /api/v1/tasks/bulk`)

```json
{
  "ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

### Batch API (`/api/v1/batches`)

#### 1. Batch 생성 (`POST /api/v1/batches`)

여러 Task를 한 번에 생성:

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "reason": "Kubernetes 기초 학습을 위한 단계별 과제입니다.",
  "tasks": [
    { "title": "Pod 개념 이해하기", "priority": "high" },
    { "title": "nginx Pod 생성하기", "priority": "high" },
    { "title": "Pod 로그 확인하기", "priority": "medium" },
    { "title": "Pod 삭제하기", "priority": "low" }
  ]
}
```

#### 2. Batch 목록 조회 (`GET /api/v1/batches`)

| 파라미터     | 타입 | 설명                  |
| ------------ | ---- | --------------------- |
| `page`       | int  | 페이지 번호 (기본: 1) |
| `session_id` | UUID | 세션별 필터링         |

#### 3. 최신 Batch 조회 (`GET /api/v1/batches/latest`)

| 파라미터     | 타입 | 설명          |
| ------------ | ---- | ------------- |
| `session_id` | UUID | 세션별 필터링 |

#### 4. Batch 상세 조회 (`GET /api/v1/batches/{batch_id}`)

---

## Agent/CLI 통합 가이드

### session_id 활용

모든 Task와 Batch는 `session_id`로 AI 세션과 연결됩니다. Agent는 세션 시작 시 생성한 UUID를 모든 API 호출에 사용해야 합니다.

### Agent 사용 시나리오

#### 1. 학습 과제 Batch 생성

사용자가 새로운 주제를 학습할 때 단계별 과제 생성:

```bash
curl -X POST http://localhost:8001/api/v1/batches \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440001",
    "reason": "Service와 네트워킹을 학습하기 위한 단계별 과제입니다.",
    "tasks": [
      { "title": "ClusterIP Service 개념 이해", "priority": "high" },
      { "title": "ClusterIP Service YAML 작성", "priority": "high" },
      { "title": "Service 생성 및 테스트", "priority": "medium" },
      { "title": "NodePort Service로 변경", "priority": "medium" }
    ]
  }'
```

#### 2. 현재 진행 상황 확인

세션의 미완료 Task 조회:

```bash
curl "http://localhost:8001/api/v1/tasks?session_id=550e8400-e29b-41d4-a716-446655440001&status=pending"
```

#### 3. Task 완료 처리

사용자가 과제를 완료했을 때:

```bash
curl -X PUT http://localhost:8001/api/v1/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

#### 4. 여러 Task 일괄 완료

```bash
curl -X PUT http://localhost:8001/api/v1/tasks/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      { "id": "uuid-1", "status": "completed" },
      { "id": "uuid-2", "status": "completed" }
    ]
  }'
```

#### 5. 최신 Batch의 진행 상황 확인

```bash
curl "http://localhost:8001/api/v1/batches/latest?session_id=550e8400-e29b-41d4-a716-446655440001"
```

### 권장 사용 패턴

| 상황              | API                   | 설명                      |
| ----------------- | --------------------- | ------------------------- |
| 새 주제 학습 시작 | `POST /batches`       | 단계별 과제 일괄 생성     |
| 추가 과제         | `POST /tasks`         | 개별 Task 추가            |
| 과제 완료         | `PUT /tasks/{id}`     | status를 completed로 변경 |
| 진행 상황 확인    | `GET /batches/latest` | 현재 학습 단계 확인       |
| 완료된 과제 정리  | `DELETE /tasks/bulk`  | 완료된 Task 일괄 삭제     |

### Task 우선순위 가이드라인

| 우선순위 | 사용 시점                         |
| -------- | --------------------------------- |
| `high`   | 다음 단계 진행에 필수인 핵심 과제 |
| `medium` | 학습에 도움이 되는 추가 과제      |
| `low`    | 선택적인 심화 과제                |

---

## 응답 형식

### Task 응답

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "batch_id": "789e0123-e45b-67c8-d901-234567890abc",
  "title": "nginx Pod 생성하기",
  "description": "kubectl run 명령어로 nginx Pod 생성",
  "status": "pending",
  "priority": "high",
  "due_date": "2025-12-07T23:59:59Z",
  "completed_at": null,
  "created_at": "2025-12-06T10:00:00Z",
  "updated_at": "2025-12-06T10:00:00Z"
}
```

### Batch 응답

```json
{
  "id": "789e0123-e45b-67c8-d901-234567890abc",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "reason": "Kubernetes 기초 학습을 위한 단계별 과제입니다.",
  "created_at": "2025-12-06T10:00:00Z",
  "tasks": [...]
}
```

---

## 로컬 개발

```bash
# 의존성 설치
uv sync --all-extras

# 개발 서버 실행
uv run uvicorn app.main:app --reload --port 8001

# 마이그레이션 실행
uv run alembic upgrade head
```

## 라이선스

MIT
