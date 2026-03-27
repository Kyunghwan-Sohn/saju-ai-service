# Saju AI Service - API Design

> **Version:** 1.0
> **Date:** 2026-03-25
> **Based on:** [Architecture v1.0](../01-plan/saju-ai-architecture.md), [Backend Design v1.0](../01-plan/backend-design.md), [DB Schema v1.0](db-schema.md)

---

## Table of Contents

1. [API 개요 및 공통 규격](#1-api-개요-및-공통-규격)
2. [인증 API](#2-인증-api)
3. [사주 프로필 API](#3-사주-프로필-api)
4. [상담 API](#4-상담-api)
5. [운세 API](#5-운세-api)
6. [궁합 API](#6-궁합-api)
7. [결제 API](#7-결제-api)
8. [사용자 API](#8-사용자-api)

---

## 1. API 개요 및 공통 규격

### 1.1 Base URL

```
Production:  https://api.saju-ai.app/api/v1
Staging:     https://api-staging.saju-ai.app/api/v1
Development: http://localhost:8000/api/v1
```

### 1.2 공통 헤더

```
Content-Type: application/json
Accept: application/json
Authorization: Bearer {access_token}     # 인증 필요 엔드포인트
X-Request-ID: {uuid}                     # 클라이언트가 생성 (선택, 없으면 서버 생성)
```

### 1.3 공통 응답 구조

모든 응답은 아래 래퍼(wrapper)를 따른다.

#### 단일 객체 응답 (성공)

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123def456",
    "timestamp": "2026-03-25T10:30:00Z"
  }
}
```

#### 목록 응답 - 커서 기반 페이지네이션

```json
{
  "data": [ ... ],
  "meta": {
    "request_id": "req_abc123def456",
    "timestamp": "2026-03-25T10:30:00Z",
    "cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNi0wMy0yNVQxMDowMDowMFoiLCJpZCI6InV1aWQifQ==",
    "has_next": true
  }
}
```

커서 페이지네이션 사용법: `?limit=20&cursor={cursor_value}`

#### 오류 응답

```json
{
  "error": {
    "code": "CONSULTATION_LIMIT_EXCEEDED",
    "message": "일일 무료 상담 횟수(3회)를 초과했습니다.",
    "details": {
      "daily_limit": 3,
      "used": 3,
      "reset_at": "2026-03-26T00:00:00+09:00"
    }
  },
  "meta": {
    "request_id": "req_abc123def456",
    "timestamp": "2026-03-25T10:30:00Z"
  }
}
```

### 1.4 HTTP 상태 코드

| 코드 | 의미 | 사용 상황 |
|------|------|---------|
| 200 | OK | 조회 성공, 수정 성공 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 삭제 성공, 로그아웃 성공 |
| 400 | Bad Request | 입력값 형식 오류 |
| 401 | Unauthorized | 인증 실패, 토큰 만료 |
| 402 | Payment Required | 결제 필요 또는 실패 |
| 403 | Forbidden | 권한 없음 (프리미엄 필요, 소유권 없음) |
| 404 | Not Found | 리소스 없음 |
| 422 | Unprocessable Entity | 입력값 검증 실패 (사주 산출 오류 등) |
| 429 | Too Many Requests | Rate Limit 초과, 일일 상담 횟수 초과 |
| 500 | Internal Server Error | 서버 오류 |
| 503 | Service Unavailable | LLM API 일시 불가 |

### 1.5 에러 코드 전체 목록

| 에러 코드 | HTTP | 설명 |
|---------|------|------|
| `AUTH_INVALID_TOKEN` | 401 | JWT 유효하지 않음 |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT 만료 |
| `AUTH_REFRESH_EXPIRED` | 401 | Refresh Token 만료 |
| `AUTH_PROVIDER_ERROR` | 401 | OAuth 공급자 오류 |
| `PROFILE_NOT_FOUND` | 404 | 프로필 없음 또는 소유권 없음 |
| `PROFILE_LIMIT_EXCEEDED` | 403 | 프로필 최대 개수 초과 |
| `PREMIUM_REQUIRED` | 403 | 프리미엄 전용 기능 |
| `CONSULTATION_NOT_FOUND` | 404 | 상담 세션 없음 |
| `CONSULTATION_LIMIT_EXCEEDED` | 429 | 일일 상담 횟수 초과 |
| `MESSAGE_LIMIT_EXCEEDED` | 403 | 세션당 메시지 수 초과 (100개) |
| `RATE_LIMIT_EXCEEDED` | 429 | API Rate Limit 초과 |
| `SAJU_CALCULATION_ERROR` | 422 | 사주 산출 실패 (날짜 범위 오류 등) |
| `LLM_UNAVAILABLE` | 503 | LLM API 일시 불가 |
| `PAYMENT_FAILED` | 402 | 결제 실패 |
| `PAYMENT_AMOUNT_MISMATCH` | 400 | 결제 금액 불일치 |
| `SUBSCRIPTION_NOT_FOUND` | 404 | 활성 구독 없음 |
| `INVALID_INPUT` | 422 | 입력값 검증 실패 |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |

### 1.6 인증 방식

```
Access Token:
  - 방식: Bearer Token (Authorization 헤더)
  - 만료: 1시간
  - 저장: 클라이언트 메모리 (보안)

Refresh Token:
  - 방식: HttpOnly Cookie (refresh_token)
  - 만료: 30일
  - 저장: DB (SHA-256 해시) + Redis (캐시)
```

### 1.7 Rate Limiting

| 사용자 유형 | API 요청 | 상담 횟수 |
|------------|---------|---------|
| 비인증 (IP 기반) | 100 req/hour | 없음 |
| 무료 사용자 | 500 req/hour | 일 3회 |
| 베이직 구독 | 1000 req/hour | 일 10회 |
| 프리미엄 구독 | 2000 req/hour | 무제한 |

Rate Limit 초과 시 응답:
```
HTTP 429
Retry-After: {seconds}
X-RateLimit-Limit: {limit}
X-RateLimit-Remaining: 0
X-RateLimit-Reset: {unix_timestamp}
```

---

## 2. 인증 API

### POST /auth/login

카카오 OAuth 인가 코드를 Access Token으로 교환한다.

```
POST /api/v1/auth/login
Content-Type: application/json
인증: 불필요
```

**Request Body**

```json
{
  "provider": "kakao",
  "code": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "redirect_uri": "https://saju-ai.app/auth/callback"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `provider` | string | O | `kakao` \| `naver` \| `google` \| `apple` |
| `code` | string | O | OAuth 공급자로부터 받은 인가 코드 |
| `redirect_uri` | string | O | OAuth 등록된 Redirect URI |

**Response 200 - 로그인 성공**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1dWlkLXVzZXItMSIsInR5cGUiOiJhY2Nlc3MiLCJpc19wcmVtaXVtIjpmYWxzZSwiaWF0IjoxNzExMzUwNjAwLCJleHAiOjE3MTEzNTQyMDB9.xxxx",
    "token_type": "Bearer",
    "expires_in": 3600,
    "is_new_user": false,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "nickname": "김지은",
      "email": "jieun@kakao.com",
      "profile_image_url": "https://k.kakaocdn.net/dn/xxxx/profile.jpg",
      "provider": "kakao",
      "is_premium": false,
      "premium_until": null,
      "daily_consult_count": 0,
      "consult_limit": 3,
      "created_at": "2026-03-25T10:00:00Z"
    }
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-25T10:00:00Z"
  }
}
```

Set-Cookie 헤더:
```
Set-Cookie: refresh_token=<raw_refresh_token>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=2592000
```

**Response 401 - OAuth 오류**

```json
{
  "error": {
    "code": "AUTH_PROVIDER_ERROR",
    "message": "카카오 인증에 실패했습니다. 다시 시도해주세요."
  }
}
```

---

### POST /auth/refresh

Refresh Token(Cookie)으로 새 Access Token을 발급한다.

```
POST /api/v1/auth/refresh
인증: HttpOnly Cookie (refresh_token)
```

**Request Body**: 없음 (Cookie에서 자동 추출)

**Response 200**

```json
{
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "meta": { "request_id": "req_def456", "timestamp": "2026-03-25T11:00:00Z" }
}
```

**Response 401 - Refresh Token 만료**

```json
{
  "error": {
    "code": "AUTH_REFRESH_EXPIRED",
    "message": "세션이 만료되었습니다. 다시 로그인해주세요."
  }
}
```

---

### DELETE /auth/logout

현재 사용자의 Refresh Token을 무효화하고 쿠키를 삭제한다.

```
DELETE /api/v1/auth/logout
Authorization: Bearer {access_token}
```

**Response 204 No Content**

Set-Cookie 헤더:
```
Set-Cookie: refresh_token=; HttpOnly; Secure; Path=/api/v1/auth; Max-Age=0
```

---

## 3. 사주 프로필 API

### POST /profiles

사주 프로필을 생성하고 사주팔자를 즉시 산출한다.

```
POST /api/v1/profiles
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "name": "김지은",
  "label": "self",
  "birth_date": "1997-03-15",
  "birth_time": "14:30",
  "is_lunar": false,
  "is_leap_month": false,
  "gender": "female"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | O | 프로필 이름 (1~50자) |
| `label` | string | O | `self` \| `family` \| `friend` |
| `birth_date` | string (YYYY-MM-DD) | O | 생년월일 (1900~2100) |
| `birth_time` | string (HH:MM) | 선택 | 출생 시각. 없으면 시주(時柱) 미산출 |
| `is_lunar` | boolean | O | `true` = 음력, `false` = 양력 |
| `is_leap_month` | boolean | O | 음력 윤달 여부 (`is_lunar=true`일 때만 유효) |
| `gender` | string | O | `male` \| `female` |

**Response 201 - 생성 성공**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "김지은",
    "label": "self",
    "gender": "female",
    "is_lunar": false,
    "is_leap_month": false,
    "saju_data": {
      "four_pillars": {
        "year": {
          "stem": "丁",
          "branch": "丑",
          "stem_kr": "정",
          "branch_kr": "축",
          "stem_element": "fire",
          "branch_element": "earth"
        },
        "month": {
          "stem": "丙",
          "branch": "寅",
          "stem_kr": "병",
          "branch_kr": "인",
          "stem_element": "fire",
          "branch_element": "wood"
        },
        "day": {
          "stem": "戊",
          "branch": "午",
          "stem_kr": "무",
          "branch_kr": "오",
          "stem_element": "earth",
          "branch_element": "fire"
        },
        "hour": {
          "stem": "庚",
          "branch": "申",
          "stem_kr": "경",
          "branch_kr": "신",
          "stem_element": "metal",
          "branch_element": "metal"
        }
      },
      "five_elements": {
        "wood": 1,
        "fire": 3,
        "earth": 2,
        "metal": 2,
        "water": 0,
        "dominant": "fire",
        "lacking": "water"
      },
      "ten_stars": {
        "year_stem": "정인",
        "year_branch": "겁재",
        "month_stem": "겁재",
        "month_branch": "비견",
        "day_branch": "겁재",
        "hour_stem": "식신",
        "hour_branch": "식신",
        "summary": {
          "비겁": 3,
          "식상": 2,
          "재성": 0,
          "관성": 0,
          "인성": 1
        }
      },
      "twelve_stages": {
        "year": "양",
        "month": "장생",
        "day": "제왕",
        "hour": "병"
      },
      "special_stars": [
        {
          "name": "도화살",
          "hanja": "桃花殺",
          "pillar": "year",
          "description": "매력과 인기, 이성 인연이 강한 기운"
        },
        {
          "name": "문창귀인",
          "hanja": "文昌貴人",
          "pillar": "hour",
          "description": "학문과 문서, 총명함을 나타내는 기운"
        }
      ],
      "geokguk": {
        "type": "겁재격",
        "hanja": "劫財格",
        "category": "정격",
        "is_projected": true,
        "description": "월지 정기의 겁재가 격을 이룸"
      },
      "major_luck_cycles": [
        {
          "age_start": 5,
          "age_end": 14,
          "stem": "乙",
          "branch": "丑",
          "stem_kr": "을",
          "branch_kr": "축",
          "ten_star": "정인",
          "twelve_stage": "양"
        },
        {
          "age_start": 15,
          "age_end": 24,
          "stem": "甲",
          "branch": "子",
          "stem_kr": "갑",
          "branch_kr": "자",
          "ten_star": "편인",
          "twelve_stage": "제왕"
        }
      ]
    },
    "created_at": "2026-03-25T10:00:00Z",
    "updated_at": "2026-03-25T10:00:00Z"
  },
  "meta": { "request_id": "req_ghi789", "timestamp": "2026-03-25T10:00:00Z" }
}
```

**Response 403 - 프로필 한도 초과**

```json
{
  "error": {
    "code": "PROFILE_LIMIT_EXCEEDED",
    "message": "프로필은 최대 5개까지 저장할 수 있습니다.",
    "details": { "current_count": 5, "max_count": 5 }
  }
}
```

**Response 422 - 사주 산출 오류**

```json
{
  "error": {
    "code": "SAJU_CALCULATION_ERROR",
    "message": "입력한 생년월일이 지원 범위(1900~2100년)를 벗어났습니다.",
    "details": { "field": "birth_date", "value": "1850-01-01" }
  }
}
```

---

### GET /profiles

현재 사용자의 사주 프로필 목록을 반환한다.

```
GET /api/v1/profiles
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "김지은",
      "label": "self",
      "gender": "female",
      "saju_summary": {
        "day_stem": "戊",
        "day_stem_kr": "무",
        "day_stem_element": "earth",
        "geokguk_type": "겁재격",
        "five_elements": {
          "dominant": "fire",
          "lacking": "water"
        },
        "special_stars_count": 2
      },
      "created_at": "2026-03-25T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "아버지",
      "label": "family",
      "gender": "male",
      "saju_summary": {
        "day_stem": "甲",
        "day_stem_kr": "갑",
        "day_stem_element": "wood",
        "geokguk_type": "정관격",
        "five_elements": {
          "dominant": "wood",
          "lacking": "fire"
        },
        "special_stars_count": 3
      },
      "created_at": "2026-03-20T09:00:00Z"
    }
  ],
  "meta": { "request_id": "req_jkl012", "timestamp": "2026-03-25T10:05:00Z" }
}
```

---

### GET /profiles/:id

특정 프로필의 전체 사주 데이터를 반환한다. 현재 운세(대운/세운/월운/일운)도 포함한다.

```
GET /api/v1/profiles/{profile_id}
Authorization: Bearer {access_token}
```

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `include_fortune` | boolean | `true` | 현재 운세 포함 여부 |

**Response 200**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "김지은",
    "label": "self",
    "gender": "female",
    "saju_data": { ... },
    "current_fortune": {
      "as_of_date": "2026-03-25",
      "major_luck": {
        "age_start": 25,
        "age_end": 34,
        "stem": "壬",
        "branch": "子",
        "stem_kr": "임",
        "branch_kr": "자",
        "ten_star": "편재",
        "twelve_stage": "태"
      },
      "yearly_luck": {
        "year": 2026,
        "stem": "丙",
        "branch": "午",
        "stem_kr": "병",
        "branch_kr": "오",
        "ten_star": "겁재"
      },
      "monthly_luck": {
        "month": 3,
        "stem": "癸",
        "branch": "卯",
        "stem_kr": "계",
        "branch_kr": "묘"
      },
      "daily_luck": {
        "stem": "甲",
        "branch": "子",
        "stem_kr": "갑",
        "branch_kr": "자"
      }
    },
    "created_at": "2026-03-25T10:00:00Z",
    "updated_at": "2026-03-25T10:00:00Z"
  },
  "meta": { "request_id": "req_mno345", "timestamp": "2026-03-25T10:05:00Z" }
}
```

---

### DELETE /profiles/:id

프로필을 소프트 삭제한다 (`deleted_at` 설정).

```
DELETE /api/v1/profiles/{profile_id}
Authorization: Bearer {access_token}
```

**Response 204 No Content**

**Response 404**

```json
{
  "error": {
    "code": "PROFILE_NOT_FOUND",
    "message": "프로필을 찾을 수 없습니다."
  }
}
```

---

## 4. 상담 API

### POST /consultations

새 AI 상담 세션을 생성한다. 이후 `/consultations/:id/messages`로 대화를 이어간다.

```
POST /api/v1/consultations
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "profile_id": "550e8400-e29b-41d4-a716-446655440001",
  "topic": "romance"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `profile_id` | string (UUID) | O | 상담에 사용할 사주 프로필 ID |
| `topic` | string | O | `romance` \| `career` \| `wealth` \| `health` \| `study` \| `general` |

**Response 201**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "profile_id": "550e8400-e29b-41d4-a716-446655440001",
    "topic": "romance",
    "title": "연애운 상담",
    "status": "active",
    "message_count": 0,
    "last_message_at": null,
    "created_at": "2026-03-25T10:10:00Z"
  },
  "meta": { "request_id": "req_pqr678", "timestamp": "2026-03-25T10:10:00Z" }
}
```

**Response 429 - 상담 횟수 초과**

```json
{
  "error": {
    "code": "CONSULTATION_LIMIT_EXCEEDED",
    "message": "일일 무료 상담 횟수(3회)를 초과했습니다.",
    "details": {
      "daily_limit": 3,
      "used": 3,
      "reset_at": "2026-03-26T00:00:00+09:00",
      "upgrade_url": "/pricing"
    }
  }
}
```

---

### GET /consultations

상담 이력 목록을 커서 기반 페이지네이션으로 반환한다.

```
GET /api/v1/consultations?limit=20&cursor={cursor}
Authorization: Bearer {access_token}
```

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `limit` | integer | 20 | 반환할 항목 수 (최대 50) |
| `cursor` | string | 없음 | 이전 응답의 `cursor` 값 |
| `topic` | string | 없음 | 주제로 필터링 |
| `profile_id` | string | 없음 | 특정 프로필로 필터링 |

**Response 200**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "profile_id": "550e8400-e29b-41d4-a716-446655440001",
      "profile_name": "김지은",
      "topic": "romance",
      "title": "연애운 상담",
      "status": "active",
      "message_count": 6,
      "last_message_at": "2026-03-25T10:15:00Z",
      "created_at": "2026-03-25T10:10:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440009",
      "profile_id": "550e8400-e29b-41d4-a716-446655440001",
      "profile_name": "김지은",
      "topic": "career",
      "title": "직장운 상담",
      "status": "completed",
      "message_count": 12,
      "last_message_at": "2026-03-20T14:30:00Z",
      "created_at": "2026-03-20T14:00:00Z"
    }
  ],
  "meta": {
    "request_id": "req_stu901",
    "timestamp": "2026-03-25T10:20:00Z",
    "cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNi0wMy0yMFQxNDowMDowMFoifQ==",
    "has_next": true
  }
}
```

---

### GET /consultations/:id

특정 상담 세션의 상세 정보를 반환한다.

```
GET /api/v1/consultations/{consultation_id}
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "profile_id": "550e8400-e29b-41d4-a716-446655440001",
    "profile_name": "김지은",
    "topic": "romance",
    "title": "연애운 상담",
    "status": "active",
    "message_count": 6,
    "last_message_at": "2026-03-25T10:15:00Z",
    "created_at": "2026-03-25T10:10:00Z",
    "feedback": null
  },
  "meta": { "request_id": "req_vwx234", "timestamp": "2026-03-25T10:20:00Z" }
}
```

---

### GET /consultations/:id/messages

상담 메시지 목록을 시간 순서로 반환한다. 최대 100개(50턴).

```
GET /api/v1/consultations/{consultation_id}/messages
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440020",
      "consultation_id": "550e8400-e29b-41d4-a716-446655440010",
      "role": "user",
      "content": "올해 연애운이 어떤가요? 좋아하는 사람이 생겼어요.",
      "feedback": "none",
      "created_at": "2026-03-25T10:10:30Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440021",
      "consultation_id": "550e8400-e29b-41d4-a716-446655440010",
      "role": "assistant",
      "content": "설레는 감정이 생기셨군요! 지은님의 사주를 보면 올해(2026년 병오년) 연애운이 꽤 활발하게 펼쳐지고 있습니다...",
      "feedback": "thumbs_up",
      "metadata": {
        "llm_provider": "claude",
        "prompt_tokens": 1200,
        "completion_tokens": 420,
        "latency_ms": 2150
      },
      "created_at": "2026-03-25T10:10:35Z"
    }
  ],
  "meta": { "request_id": "req_yz0123", "timestamp": "2026-03-25T10:20:00Z" }
}
```

---

### POST /consultations/:id/messages

사용자 메시지를 전송하고 AI 응답을 SSE(Server-Sent Events) 스트리밍으로 수신한다.

```
POST /api/v1/consultations/{consultation_id}/messages
Authorization: Bearer {access_token}
Content-Type: application/json
Accept: text/event-stream
```

**Request Body**

```json
{
  "content": "올해 연애운이 어떤가요? 좋아하는 사람이 생겼어요."
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `content` | string | O | 사용자 메시지 (1~2000자) |

**Response 200 - text/event-stream**

```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no

event: token
data: {"token": "설레"}

event: token
data: {"token": "는 감정"}

event: token
data: {"token": "이 생기"}

event: token
data: {"token": "셨군요!"}

event: token
data: {"token": " 지은님"}

... (계속)

event: done
data: {"message_id": "550e8400-e29b-41d4-a716-446655440021", "usage": {"prompt_tokens": 1200, "completion_tokens": 420}}
```

SSE 이벤트 타입:

| 이벤트 | 설명 | data 구조 |
|--------|------|---------|
| `token` | 응답 토큰 스트리밍 | `{"token": "string"}` |
| `done` | 스트리밍 완료 | `{"message_id": "uuid", "usage": {...}}` |
| `error` | 스트리밍 오류 | `{"code": "...", "message": "..."}` |

**Response 403 - 메시지 한도 초과**

```json
{
  "error": {
    "code": "MESSAGE_LIMIT_EXCEEDED",
    "message": "세션당 최대 50번의 대화(100개 메시지)까지 가능합니다. 새 상담을 시작해 주세요."
  }
}
```

---

### PATCH /consultations/:id/messages/:message_id/feedback

AI 응답 메시지에 좋아요/싫어요 피드백을 남긴다.

```
PATCH /api/v1/consultations/{consultation_id}/messages/{message_id}/feedback
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "feedback": "thumbs_up"
}
```

`feedback`: `thumbs_up` | `thumbs_down` | `none`

**Response 200**

```json
{
  "data": {
    "message_id": "550e8400-e29b-41d4-a716-446655440021",
    "feedback": "thumbs_up",
    "updated_at": "2026-03-25T10:25:00Z"
  },
  "meta": { "request_id": "req_abc456", "timestamp": "2026-03-25T10:25:00Z" }
}
```

---

### POST /consultations/:id/feedback

상담 세션 전체에 대한 CSAT 평가를 남긴다.

```
POST /api/v1/consultations/{consultation_id}/feedback
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "overall_score": 5,
  "accuracy_score": 4,
  "helpfulness_score": 5,
  "comment": "연애운 해석이 정말 공감됐어요. 도화살 설명이 인상적이었습니다."
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `overall_score` | integer (1~5) | O | 종합 만족도 |
| `accuracy_score` | integer (1~5) | 선택 | 정확도 |
| `helpfulness_score` | integer (1~5) | 선택 | 도움이 된 정도 |
| `comment` | string | 선택 | 자유 의견 (최대 500자) |

**Response 201**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "consultation_id": "550e8400-e29b-41d4-a716-446655440010",
    "overall_score": 5,
    "accuracy_score": 4,
    "helpfulness_score": 5,
    "created_at": "2026-03-25T10:30:00Z"
  },
  "meta": { "request_id": "req_def789", "timestamp": "2026-03-25T10:30:00Z" }
}
```

---

## 5. 운세 API

### GET /fortunes/daily

오늘의 운세를 반환한다. 매일 자정(KST) 배치로 생성되며, Redis에 24시간 캐싱된다.

```
GET /api/v1/fortunes/daily?profile_id={profile_id}
Authorization: Bearer {access_token}
```

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `profile_id` | string (UUID) | O | 운세를 조회할 프로필 ID |
| `date` | string (YYYY-MM-DD) | 선택 | 조회 날짜 (기본: 오늘) |

**Response 200**

```json
{
  "data": {
    "profile_id": "550e8400-e29b-41d4-a716-446655440001",
    "date": "2026-03-25",
    "day_stem": "甲",
    "day_branch": "子",
    "day_stem_kr": "갑",
    "day_branch_kr": "자",
    "fortune_data": {
      "overall": {
        "score": 78,
        "keywords": ["새로운 시작", "인내", "기회"],
        "summary": "오늘은 갑자(甲子)일로 새로운 시작의 기운이 넘칩니다. 목표를 향해 한 발씩 나아가는 하루가 될 것입니다."
      },
      "romance": {
        "score": 82,
        "keywords": ["설렘", "인연"],
        "advice": "오늘은 감정 표현에 좋은 날입니다. 관심 있는 사람에게 먼저 다가가 보세요."
      },
      "wealth": {
        "score": 65,
        "keywords": ["절약", "신중"],
        "advice": "충동적인 지출보다 계획적인 소비가 유리합니다."
      },
      "health": {
        "score": 85,
        "keywords": ["활력", "운동"],
        "advice": "오늘은 에너지가 충분하니 가벼운 운동을 시작해 보세요."
      },
      "career": {
        "score": 72,
        "keywords": ["집중", "성과"],
        "advice": "오전 시간에 중요한 업무를 처리하면 좋은 성과를 낼 수 있습니다."
      }
    },
    "content": "오늘은 갑자(甲子)일로, 60갑자의 첫 번째 일진이자 새로운 시작을 상징합니다. 무(戊)토 일간을 가진 지은님에게 오늘의 갑(甲)목은 편관(偏官)의 기운을 발생시킵니다. 약간의 압박감이 있을 수 있으나, 이를 원동력 삼아 도전하면 좋은 결과를 얻을 수 있습니다.",
    "lucky_color": "파란색",
    "lucky_number": 1,
    "time_advice": "오전 9시~11시(巳時)에 활동적인 에너지가 높습니다.",
    "cached": true,
    "created_at": "2026-03-25T00:05:00Z"
  },
  "meta": { "request_id": "req_ghi012", "timestamp": "2026-03-25T10:30:00Z" }
}
```

---

### GET /fortunes/weekly

이번 주(월~일) 7일간의 운세를 반환한다.

```
GET /api/v1/fortunes/weekly?profile_id={profile_id}
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": {
    "profile_id": "550e8400-e29b-41d4-a716-446655440001",
    "week_start": "2026-03-23",
    "week_end": "2026-03-29",
    "week_summary": "이번 주는 병오(丙午) 세운의 영향으로 활동적인 에너지가 넘칩니다...",
    "best_day": "wednesday",
    "caution_day": "friday",
    "focus_areas": ["업무 효율", "인간관계"],
    "daily": {
      "mon": { "date": "2026-03-23", "score": 70, "day_pillar": "壬戌", "theme": "안정", "advice": "차분하게 마무리에 집중하세요." },
      "tue": { "date": "2026-03-24", "score": 65, "day_pillar": "癸亥", "theme": "휴식", "advice": "에너지를 충전하는 하루로 보내세요." },
      "wed": { "date": "2026-03-25", "score": 78, "day_pillar": "甲子", "theme": "새로운 시작", "advice": "적극적으로 의사 표현을 해보세요." },
      "thu": { "date": "2026-03-26", "score": 75, "day_pillar": "乙丑", "theme": "성실", "advice": "꾸준함이 빛을 발하는 날입니다." },
      "fri": { "date": "2026-03-27", "score": 58, "day_pillar": "丙寅", "theme": "신중", "advice": "중요한 결정은 다음 주로 미루는 것이 좋습니다." },
      "sat": { "date": "2026-03-28", "score": 80, "day_pillar": "丁卯", "theme": "소통", "advice": "소중한 사람과 시간을 보내기에 좋은 날입니다." },
      "sun": { "date": "2026-03-29", "score": 73, "day_pillar": "戊辰", "theme": "정리", "advice": "한 주를 정리하고 다음 주를 준비하세요." }
    }
  },
  "meta": { "request_id": "req_jkl345", "timestamp": "2026-03-25T10:30:00Z" }
}
```

---

### GET /fortunes/monthly (Premium)

이번 달 월간 운세를 반환한다.

```
GET /api/v1/fortunes/monthly?profile_id={profile_id}&year=2026&month=3
Authorization: Bearer {access_token}   (Premium 필요)
```

**Response 200**

```json
{
  "data": {
    "profile_id": "550e8400-e29b-41d4-a716-446655440001",
    "year": 2026,
    "month": 3,
    "month_pillar": { "stem_kr": "계", "branch_kr": "묘", "stem": "癸", "branch": "卯" },
    "monthly_summary": "3월은 계묘(癸卯)월로, 목(木)의 기운이 강해지는 시기입니다...",
    "overall_score": 74,
    "scores": {
      "romance": 80,
      "career": 70,
      "wealth": 65,
      "health": 78
    },
    "highlights": [
      { "period": "3월 1일~10일", "theme": "도전과 시작", "description": "새로운 시도에 좋은 시기" },
      { "period": "3월 11일~20일", "theme": "관계와 소통", "description": "인간관계가 활발해지는 시기" },
      { "period": "3월 21일~31일", "theme": "마무리와 준비", "description": "4월을 준비하는 안정적인 시기" }
    ],
    "content": "3월 전체 운세 해석 텍스트...",
    "lucky_days": ["3월 5일", "3월 12일", "3월 25일"],
    "caution_days": ["3월 8일", "3월 19일"]
  },
  "meta": { "request_id": "req_mno678", "timestamp": "2026-03-25T10:30:00Z" }
}
```

---

## 6. 궁합 API

### POST /compatibility

두 사주 프로필의 궁합을 AI로 분석한다.

```
POST /api/v1/compatibility
Authorization: Bearer {access_token}   (Premium 필요)
```

**Request Body**

```json
{
  "profile_id_a": "550e8400-e29b-41d4-a716-446655440001",
  "profile_id_b": "550e8400-e29b-41d4-a716-446655440002"
}
```

두 프로필 모두 현재 사용자 소유여야 한다 (family/friend 포함).

**Response 200**

```json
{
  "data": {
    "profile_a": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "김지은",
      "day_stem": "戊",
      "day_stem_kr": "무",
      "day_stem_element": "earth"
    },
    "profile_b": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "이민준",
      "day_stem": "甲",
      "day_stem_kr": "갑",
      "day_stem_element": "wood"
    },
    "overall_score": 82,
    "scores": {
      "emotional": {
        "score": 85,
        "description": "갑목(甲木)과 무토(戊土)는 상극 관계이지만, 이 긴장감이 오히려 강한 이끌림을 만들어냅니다. 서로 다른 성향이 보완 관계를 형성합니다."
      },
      "values": {
        "score": 78,
        "description": "삶의 방향에서 차이가 있으나, 서로의 강점이 조화를 이룰 수 있습니다."
      },
      "lifestyle": {
        "score": 80,
        "description": "활동성과 안정성의 균형이 좋은 편입니다."
      },
      "future": {
        "score": 84,
        "description": "장기적으로 안정적이고 성장하는 관계를 기대할 수 있습니다."
      }
    },
    "saju_interaction": {
      "five_elements_combined": {
        "wood": 2,
        "fire": 4,
        "earth": 3,
        "metal": 2,
        "water": 1
      },
      "balance_comment": "합산 오행에서 수(水)가 약간 부족합니다. 함께 있을 때 감정적 유연성을 기르는 연습이 도움됩니다.",
      "special_notes": [
        "두 일주(무오-갑자)의 음양이 조화롭습니다",
        "각자의 신살이 서로 보완하는 구조입니다"
      ]
    },
    "ai_analysis": "두 분의 사주는 갑목(甲木)과 무토(戊土)의 상극(相剋) 구조를 가지고 있습니다. 명리학에서 상극은 갈등이 아니라 '제어와 규율'을 의미하기도 합니다...",
    "lucky_period": "2026년 5~6월, 대화가 특히 잘 통하는 시기",
    "advice": "상대방의 주도적이고 진취적인 성향을 인정하고 지지해 주면, 무토의 안정감이 갑목의 성장을 든든히 받쳐주는 아름다운 관계가 됩니다.",
    "created_at": "2026-03-25T10:35:00Z"
  },
  "meta": { "request_id": "req_pqr901", "timestamp": "2026-03-25T10:35:00Z" }
}
```

---

## 7. 결제 API

### POST /subscriptions

빌링키를 사용해 구독을 시작하고 즉시 첫 결제를 진행한다.

```
POST /api/v1/subscriptions
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "plan": "premium",
  "billing_key": "BILLING_KEY_from_toss",
  "customer_key": "550e8400-e29b-41d4-a716-446655440000"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `plan` | string | O | `basic` (3,900원) \| `premium` (9,900원) |
| `billing_key` | string | O | Toss Payments 빌링키 등록 완료 후 발급된 키 |
| `customer_key` | string | O | 사용자 ID (Toss 고객 식별자) |

**Response 201**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440040",
    "plan_type": "premium",
    "status": "active",
    "current_period_start": "2026-03-25T10:00:00Z",
    "current_period_end": "2026-04-25T10:00:00Z",
    "amount_paid": 9900,
    "currency": "KRW",
    "features": {
      "daily_consult_limit": -1,
      "max_profiles": 5,
      "weekly_fortune": true,
      "monthly_fortune": true,
      "compatibility": true,
      "share_card": true
    }
  },
  "meta": { "request_id": "req_stu234", "timestamp": "2026-03-25T10:40:00Z" }
}
```

**Response 402 - 결제 실패**

```json
{
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "결제에 실패했습니다. 카드 정보를 확인해 주세요.",
    "details": {
      "toss_error_code": "CARD_DECLINED",
      "toss_message": "카드 한도 초과"
    }
  }
}
```

---

### GET /subscriptions/current

현재 사용자의 활성 구독 정보를 반환한다.

```
GET /api/v1/subscriptions/current
Authorization: Bearer {access_token}
```

**Response 200 - 구독 중**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440040",
    "plan_type": "premium",
    "status": "active",
    "current_period_start": "2026-03-25T10:00:00Z",
    "current_period_end": "2026-04-25T10:00:00Z",
    "next_billing_date": "2026-04-25",
    "next_billing_amount": 9900,
    "features": {
      "daily_consult_limit": -1,
      "max_profiles": 5,
      "monthly_fortune": true,
      "compatibility": true
    },
    "created_at": "2026-03-25T10:00:00Z"
  },
  "meta": { "request_id": "req_vwx567", "timestamp": "2026-03-25T10:40:00Z" }
}
```

**Response 200 - 구독 없음**

```json
{
  "data": {
    "plan_type": "free",
    "status": "none",
    "features": {
      "daily_consult_limit": 3,
      "max_profiles": 1,
      "monthly_fortune": false,
      "compatibility": false
    }
  },
  "meta": { "request_id": "req_yz0890", "timestamp": "2026-03-25T10:40:00Z" }
}
```

---

### DELETE /subscriptions/current

구독을 취소한다. 현재 결제 기간 종료일까지 서비스를 계속 사용할 수 있다.

```
DELETE /api/v1/subscriptions/current
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440040",
    "status": "cancelled",
    "access_until": "2026-04-25T10:00:00Z",
    "cancelled_at": "2026-03-25T11:00:00Z",
    "message": "2026년 4월 25일까지 프리미엄 기능을 계속 이용하실 수 있습니다."
  },
  "meta": { "request_id": "req_abc234", "timestamp": "2026-03-25T11:00:00Z" }
}
```

---

### POST /payments/verify

Toss Payments 단건 결제(일회성 결제)를 서버에서 검증하고 승인한다.

```
POST /api/v1/payments/verify
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "payment_key": "5zJ4xY7m0kODnyRpQWGrN2eqXgv1b8Ka",
  "order_id": "ord_2026032510001",
  "amount": 9900
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `payment_key` | string | O | Toss Payments paymentKey |
| `order_id` | string | O | 클라이언트에서 생성한 주문 ID |
| `amount` | integer | O | 결제 금액 (원, 서버에서 재검증) |

**Response 200**

```json
{
  "data": {
    "payment_id": "550e8400-e29b-41d4-a716-446655440050",
    "order_id": "ord_2026032510001",
    "type": "one_time",
    "amount": 9900,
    "currency": "KRW",
    "status": "completed",
    "pg_payment_key": "5zJ4xY7m0kODnyRpQWGrN2eqXgv1b8Ka",
    "paid_at": "2026-03-25T11:05:00Z"
  },
  "meta": { "request_id": "req_def567", "timestamp": "2026-03-25T11:05:00Z" }
}
```

**Response 400 - 금액 불일치**

```json
{
  "error": {
    "code": "PAYMENT_AMOUNT_MISMATCH",
    "message": "결제 금액이 일치하지 않습니다.",
    "details": {
      "expected": 9900,
      "received": 1000
    }
  }
}
```

---

### POST /payments/webhook

Toss Payments 웹훅 수신 엔드포인트. 서명 검증 후 결제 상태를 동기화한다.

```
POST /api/v1/payments/webhook
Content-Type: application/json
Toss-Signature: {hmac_signature}
인증: 없음 (서명으로 검증)
```

**Request Body (Toss Payments 자동 전송)**

```json
{
  "eventType": "PAYMENT_STATUS_CHANGED",
  "createdAt": "2026-03-25T11:05:00+09:00",
  "data": {
    "paymentKey": "5zJ4xY7m0kODnyRpQWGrN2eqXgv1b8Ka",
    "orderId": "ord_2026032510001",
    "status": "DONE"
  }
}
```

**Response 200**

```json
{ "ok": true }
```

웹훅 처리 실패 시에도 200을 반환하고 내부적으로 재처리 큐에 등록한다.

---

### GET /payments/history

결제 이력을 반환한다.

```
GET /api/v1/payments/history?limit=20&cursor={cursor}
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440050",
      "type": "subscription",
      "plan_type": "premium",
      "amount": 9900,
      "currency": "KRW",
      "status": "completed",
      "paid_at": "2026-03-25T11:05:00Z",
      "created_at": "2026-03-25T11:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440049",
      "type": "subscription",
      "plan_type": "premium",
      "amount": 9900,
      "currency": "KRW",
      "status": "completed",
      "paid_at": "2026-02-25T10:00:00Z",
      "created_at": "2026-02-25T10:00:00Z"
    }
  ],
  "meta": {
    "request_id": "req_ghi890",
    "timestamp": "2026-03-25T11:10:00Z",
    "cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNi0wMi0yNVQxMDowMDowMFoifQ==",
    "has_next": false
  }
}
```

---

## 8. 사용자 API

### GET /users/me

현재 인증된 사용자의 계정 정보를 반환한다.

```
GET /api/v1/users/me
Authorization: Bearer {access_token}
```

**Response 200**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nickname": "김지은",
    "email": "jieun@kakao.com",
    "profile_image_url": "https://k.kakaocdn.net/dn/xxxx/profile.jpg",
    "provider": "kakao",
    "is_premium": true,
    "premium_until": "2026-04-25T10:00:00Z",
    "subscription": {
      "plan_type": "premium",
      "status": "active"
    },
    "usage": {
      "daily_consult_count": 2,
      "consult_limit": -1,
      "consult_reset_at": "2026-03-25"
    },
    "profile_count": 2,
    "profile_limit": 5,
    "created_at": "2026-01-01T00:00:00Z"
  },
  "meta": { "request_id": "req_jkl123", "timestamp": "2026-03-25T11:10:00Z" }
}
```

---

### PATCH /users/me

사용자 프로필 정보를 수정한다. 닉네임만 변경 가능.

```
PATCH /api/v1/users/me
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "nickname": "새로운닉네임"
}
```

**Response 200**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nickname": "새로운닉네임",
    "updated_at": "2026-03-25T11:15:00Z"
  },
  "meta": { "request_id": "req_mno456", "timestamp": "2026-03-25T11:15:00Z" }
}
```

---

### DELETE /users/me

회원 탈퇴를 처리한다. `deleted_at`을 설정하는 소프트 삭제 방식. 30일 후 완전 삭제.

```
DELETE /api/v1/users/me
Authorization: Bearer {access_token}
```

**Request Body**

```json
{
  "reason": "서비스가 필요 없어졌습니다."
}
```

**Response 200**

```json
{
  "data": {
    "message": "탈퇴 처리가 완료되었습니다. 30일 이내에 재가입하시면 계정을 복구할 수 있습니다.",
    "deleted_at": "2026-03-25T11:20:00Z",
    "permanent_delete_at": "2026-04-24T11:20:00Z"
  },
  "meta": { "request_id": "req_pqr789", "timestamp": "2026-03-25T11:20:00Z" }
}
```
