# Saju AI Service - Database Schema Design

> **Version:** 1.0
> **Date:** 2026-03-25
> **Author:** CTO Lead
> **Based on:** [PRD v1.0](../00-pm/saju-ai-service.prd.md), [Architecture v1.0](../01-plan/saju-ai-architecture.md)

---

## Table of Contents

1. [Overview](#1-overview)
2. [ERD (Entity Relationship Diagram)](#2-erd)
3. [Table Definitions](#3-table-definitions)
4. [JSONB Schema Definitions](#4-jsonb-schema-definitions)
5. [Indexing Strategy](#5-indexing-strategy)
6. [Migration Strategy](#6-migration-strategy)

---

## 1. Overview

### 1.1 Database Configuration

- **Engine:** PostgreSQL 16
- **Extensions:** pgvector (벡터 검색), pgcrypto (UUID 생성), pg_trgm (텍스트 검색)
- **Hosting:** AWS RDS (ap-northeast-2)
- **Character Set:** UTF-8
- **Timezone:** UTC (애플리케이션 레벨에서 KST 변환)

### 1.2 Convention

| 항목 | 규칙 |
|------|------|
| 테이블명 | 복수형 snake_case (`users`, `saju_profiles`) |
| 컬럼명 | snake_case (`birth_date`, `created_at`) |
| Primary Key | `id` (UUID v4) |
| Foreign Key | `{referenced_table_singular}_id` (`user_id`, `profile_id`) |
| Timestamp | `created_at`, `updated_at` (UTC, timestamptz) |
| Soft Delete | `deleted_at` (nullable timestamptz) |
| ENUM | PostgreSQL ENUM type |
| JSONB | 복잡한 도메인 데이터 저장 (사주 데이터, 운세 데이터) |

---

## 2. ERD

```
┌─────────────────────┐        ┌──────────────────────────┐
│       users          │        │     saju_profiles         │
├─────────────────────┤        ├──────────────────────────┤
│ id (PK, UUID)        │───┐    │ id (PK, UUID)             │
│ email                │   │    │ user_id (FK) ◄────────────┤
│ nickname             │   │    │ label                     │
│ profile_image_url    │   │    │ name                      │
│ provider             │   │    │ birth_date_encrypted      │
│ provider_id          │   │    │ birth_time_encrypted      │
│ is_premium           │   │    │ is_lunar                  │
│ premium_until        │   │    │ is_leap_month             │
│ daily_consult_count  │   │    │ gender                    │
│ consult_reset_at     │   │    │ saju_data (JSONB)         │
│ created_at           │   │    │ created_at                │
│ updated_at           │   │    │ updated_at                │
│ deleted_at           │   │    │ deleted_at                │
└─────────────────────┘   │    └────────────┬─────────────┘
                           │                 │
                           │    ┌────────────▼─────────────┐
                           │    │     consultations         │
                           │    ├──────────────────────────┤
                           ├───►│ id (PK, UUID)             │
                           │    │ user_id (FK)              │
                           │    │ profile_id (FK)           │
                           │    │ topic                     │
                           │    │ title                     │
                           │    │ status                    │
                           │    │ message_count             │
                           │    │ last_message_at           │
                           │    │ created_at                │
                           │    │ updated_at                │
                           │    └────────────┬─────────────┘
                           │                 │
                           │    ┌────────────▼─────────────┐
                           │    │       messages            │
                           │    ├──────────────────────────┤
                           │    │ id (PK, UUID)             │
                           │    │ consultation_id (FK)      │
                           │    │ role                      │
                           │    │ content                   │
                           │    │ metadata (JSONB)          │
                           │    │ feedback                  │
                           │    │ created_at                │
                           │    └──────────────────────────┘
                           │
┌─────────────────────┐    │    ┌──────────────────────────┐
│    subscriptions     │    │    │     daily_fortunes        │
├─────────────────────┤    │    ├──────────────────────────┤
│ id (PK, UUID)        │    │    │ id (PK, UUID)             │
│ user_id (FK) ◄───────┤    │    │ profile_id (FK)           │
│ plan_type            │    │    │ date                      │
│ status               │    │    │ day_stem                  │
│ current_period_start │    │    │ day_branch                │
│ current_period_end   │    │    │ fortune_data (JSONB)      │
│ pg_subscription_id   │    │    │ content                   │
│ created_at           │    │    │ created_at                │
│ updated_at           │    │    └──────────────────────────┘
│ cancelled_at         │    │
└─────────────────────┘    │    ┌──────────────────────────┐
                           │    │      payments             │
┌─────────────────────┐    │    ├──────────────────────────┤
│  knowledge_chunks    │    ├───►│ id (PK, UUID)             │
├─────────────────────┤    │    │ user_id (FK)              │
│ id (PK, UUID)        │    │    │ subscription_id (FK, NUL) │
│ content              │    │    │ type                      │
│ embedding (vector)   │    │    │ amount                    │
│ source               │    │    │ currency                  │
│ category             │    │    │ status                    │
│ metadata (JSONB)     │    │    │ pg_transaction_id         │
│ created_at           │    │    │ pg_payment_key            │
│ updated_at           │    │    │ paid_at                   │
└─────────────────────┘    │    │ created_at                │
                           │    │ updated_at                │
┌─────────────────────┐    │    └──────────────────────────┘
│ consultation_feedbacks│   │
├─────────────────────┤    │    ┌──────────────────────────┐
│ id (PK, UUID)        │    │    │    refresh_tokens         │
│ consultation_id (FK) │    │    ├──────────────────────────┤
│ user_id (FK) ◄───────┘    └───►│ id (PK, UUID)             │
│ overall_score        │         │ user_id (FK)              │
│ accuracy_score       │         │ token_hash                │
│ helpfulness_score    │         │ expires_at                │
│ comment              │         │ is_revoked                │
│ created_at           │         │ created_at                │
└─────────────────────┘         └──────────────────────────┘
```

---

## 3. Table Definitions

### 3.1 users

사용자 계정 정보. OAuth 소셜 로그인 기반.

```sql
CREATE TYPE auth_provider AS ENUM ('kakao', 'naver', 'google', 'apple');

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255),
    nickname        VARCHAR(50) NOT NULL,
    profile_image_url VARCHAR(500),

    -- OAuth
    provider        auth_provider NOT NULL,
    provider_id     VARCHAR(255) NOT NULL,

    -- Premium Status
    is_premium      BOOLEAN NOT NULL DEFAULT FALSE,
    premium_until   TIMESTAMPTZ,

    -- Daily Consultation Limit
    daily_consult_count INTEGER NOT NULL DEFAULT 0,
    consult_reset_at    DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT uq_users_provider UNIQUE (provider, provider_id)
);

COMMENT ON TABLE users IS '사용자 계정. OAuth 소셜 로그인 기반.';
COMMENT ON COLUMN users.daily_consult_count IS '오늘 사용한 AI 상담 횟수. consult_reset_at 날짜가 변경되면 0으로 리셋.';
COMMENT ON COLUMN users.consult_reset_at IS '상담 횟수 리셋 기준 날짜 (KST 기준 자정).';
COMMENT ON COLUMN users.deleted_at IS 'Soft delete. 탈퇴 후 30일 유예 기간.';
```

### 3.2 saju_profiles

사주 프로필. 사용자당 최대 5개 (MVP: 1개). 생년월일시는 AES-256 암호화 저장.

```sql
CREATE TYPE profile_label AS ENUM ('self', 'family', 'friend');
CREATE TYPE gender_type AS ENUM ('male', 'female');

CREATE TABLE saju_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Profile Info
    label               profile_label NOT NULL DEFAULT 'self',
    name                VARCHAR(50) NOT NULL,

    -- Birth Info (Encrypted)
    birth_date_encrypted BYTEA NOT NULL,       -- AES-256-GCM 암호화된 생년월일
    birth_time_encrypted BYTEA,                -- AES-256-GCM 암호화된 태어난 시간 (nullable: 시간 모름)
    is_lunar            BOOLEAN NOT NULL DEFAULT FALSE,
    is_leap_month       BOOLEAN NOT NULL DEFAULT FALSE,
    gender              gender_type NOT NULL,

    -- Saju Calculation Result (JSONB)
    saju_data           JSONB NOT NULL,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_profile_limit CHECK (
        -- 애플리케이션 레벨에서 user당 최대 5개 제한 (DB 레벨은 트리거 또는 앱 체크)
        TRUE
    )
);

COMMENT ON TABLE saju_profiles IS '사주 프로필. 생년월일시 AES-256 암호화. saju_data에 산출 결과 JSONB 저장.';
COMMENT ON COLUMN saju_profiles.birth_date_encrypted IS 'AES-256-GCM 암호화된 생년월일. 복호화는 사주 산출 시에만.';
COMMENT ON COLUMN saju_profiles.saju_data IS '사주팔자, 오행, 십성, 12운성, 신살, 격국, 대운 등 전체 산출 결과. 스키마: 4.1 참조.';
```

### 3.3 consultations

AI 상담 세션. 주제별 분류, 멀티턴 대화 관리.

```sql
CREATE TYPE consultation_topic AS ENUM (
    'romance',    -- 연애운
    'career',     -- 직장운
    'wealth',     -- 재물운
    'health',     -- 건강운
    'study',      -- 학업운
    'general'     -- 일반/종합
);

CREATE TYPE consultation_status AS ENUM (
    'active',     -- 진행 중
    'completed',  -- 완료
    'archived'    -- 보관 (90일 후)
);

CREATE TABLE consultations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id      UUID NOT NULL REFERENCES saju_profiles(id) ON DELETE CASCADE,

    -- Consultation Info
    topic           consultation_topic NOT NULL DEFAULT 'general',
    title           VARCHAR(100),          -- 자동 생성 또는 사용자 지정 제목
    status          consultation_status NOT NULL DEFAULT 'active',

    -- Denormalized Counters
    message_count   INTEGER NOT NULL DEFAULT 0,
    last_message_at TIMESTAMPTZ,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE consultations IS 'AI 상담 세션. 세션당 최대 50턴 (100 messages).';
COMMENT ON COLUMN consultations.message_count IS '비정규화된 메시지 수. messages INSERT 시 트리거로 증가.';
```

### 3.4 messages

상담 메시지. 사용자 메시지와 AI 응답을 시간순 저장.

```sql
CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE message_feedback AS ENUM ('thumbs_up', 'thumbs_down', 'none');

CREATE TABLE messages (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id     UUID NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,

    -- Message Content
    role                message_role NOT NULL,
    content             TEXT NOT NULL,

    -- AI Response Metadata
    metadata            JSONB,

    -- User Feedback (for AI responses)
    feedback            message_feedback NOT NULL DEFAULT 'none',

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE messages IS '상담 메시지. role=user(사용자), assistant(AI), system(시스템 메시지).';
COMMENT ON COLUMN messages.metadata IS 'AI 응답 메타데이터: LLM 프로바이더, 토큰 수, 지연시간, RAG 출처 등. 스키마: 4.2 참조.';
COMMENT ON COLUMN messages.feedback IS '사용자의 응답별 피드백 (좋아요/싫어요). AI 응답(assistant)에만 적용.';
```

### 3.5 daily_fortunes

일일 운세. 매일 자정 배치 생성.

```sql
CREATE TABLE daily_fortunes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID NOT NULL REFERENCES saju_profiles(id) ON DELETE CASCADE,

    -- Fortune Info
    date            DATE NOT NULL,
    day_stem        VARCHAR(2) NOT NULL,    -- 일간 (甲~癸)
    day_branch      VARCHAR(2) NOT NULL,    -- 일지 (子~亥)

    -- Fortune Content
    fortune_data    JSONB NOT NULL,         -- 구조화된 운세 데이터
    content         TEXT NOT NULL,           -- LLM 생성 운세 텍스트

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_daily_fortune UNIQUE (profile_id, date)
);

COMMENT ON TABLE daily_fortunes IS '일일 운세. 매일 자정(KST) 배치 생성. 프로필+날짜 유니크.';
COMMENT ON COLUMN daily_fortunes.fortune_data IS '구조화된 운세 데이터: 종합운, 재물운, 연애운, 건강운 점수 및 키워드. 스키마: 4.3 참조.';
```

### 3.6 subscriptions

프리미엄 구독 관리.

```sql
CREATE TYPE subscription_plan AS ENUM ('monthly', 'yearly');
CREATE TYPE subscription_status AS ENUM (
    'active',       -- 활성
    'past_due',     -- 결제 지연
    'cancelled',    -- 취소 (기간 만료까지 사용 가능)
    'expired'       -- 만료
);

CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Subscription Info
    plan_type               subscription_plan NOT NULL,
    status                  subscription_status NOT NULL DEFAULT 'active',

    -- Billing Period
    current_period_start    TIMESTAMPTZ NOT NULL,
    current_period_end      TIMESTAMPTZ NOT NULL,

    -- PG Integration
    pg_subscription_id      VARCHAR(255),       -- Toss Payments 빌링키 또는 구독 ID

    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cancelled_at            TIMESTAMPTZ
);

COMMENT ON TABLE subscriptions IS '프리미엄 구독. Toss Payments 연동. 구독 취소 시 기간 종료까지 사용 가능.';
```

### 3.7 payments

결제 내역. 구독 결제 및 건별 결제.

```sql
CREATE TYPE payment_type AS ENUM ('subscription', 'one_time');
CREATE TYPE payment_status AS ENUM (
    'pending',      -- 결제 대기
    'completed',    -- 결제 완료
    'failed',       -- 결제 실패
    'refunded',     -- 환불
    'cancelled'     -- 취소
);

CREATE TABLE payments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id     UUID REFERENCES subscriptions(id),   -- 구독 결제 시

    -- Payment Info
    type                payment_type NOT NULL,
    amount              INTEGER NOT NULL,                     -- 원 단위 (KRW)
    currency            VARCHAR(3) NOT NULL DEFAULT 'KRW',
    status              payment_status NOT NULL DEFAULT 'pending',

    -- PG Integration (Toss Payments)
    pg_transaction_id   VARCHAR(255),       -- Toss Payments orderId
    pg_payment_key      VARCHAR(255),       -- Toss Payments paymentKey

    -- Timestamps
    paid_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE payments IS '결제 내역. Toss Payments PG 연동. amount는 원(KRW) 단위 정수.';
```

### 3.8 consultation_feedbacks

상담 세션 전체에 대한 CSAT 평가.

```sql
CREATE TABLE consultation_feedbacks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultation_id     UUID NOT NULL REFERENCES consultations(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Scores (1-5)
    overall_score       SMALLINT NOT NULL CHECK (overall_score BETWEEN 1 AND 5),
    accuracy_score      SMALLINT CHECK (accuracy_score BETWEEN 1 AND 5),
    helpfulness_score   SMALLINT CHECK (helpfulness_score BETWEEN 1 AND 5),

    -- Free Text
    comment             TEXT,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_consultation_feedback UNIQUE (consultation_id, user_id)
);

COMMENT ON TABLE consultation_feedbacks IS '상담 세션 종료 후 CSAT 평가. 세션당 1회.';
```

### 3.9 knowledge_chunks

RAG용 명리학 지식 베이스. pgvector 임베딩.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    content         TEXT NOT NULL,
    embedding       vector(1536) NOT NULL,  -- text-embedding-3-small 차원

    -- Metadata
    source          VARCHAR(100) NOT NULL,   -- 'jeokcheonsu', 'japyeongjinjeon', etc.
    category        VARCHAR(50) NOT NULL,    -- 'geokguk', 'ten_stars', 'special_stars', etc.
    metadata        JSONB,                   -- 추가 메타데이터 (관련 오행, 십성 등)

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE knowledge_chunks IS 'RAG용 명리학 지식 베이스. pgvector 임베딩(1536차원). 원전+해설 청크.';
COMMENT ON COLUMN knowledge_chunks.source IS '출처: jeokcheonsu(적천수), japyeongjinjeon(자평진전), gungtonbogam(궁통보감), guide(해석가이드), sinsal(신살사전)';
COMMENT ON COLUMN knowledge_chunks.category IS '분류: geokguk(격국론), ten_stars(십성론), special_stars(신살론), five_elements(오행론), luck_cycle(운세론), general(통변)';
```

### 3.10 refresh_tokens

JWT Refresh Token 관리.

```sql
CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Token
    token_hash      VARCHAR(128) NOT NULL,   -- SHA-256 해시 저장 (원본 토큰 저장 금지)
    expires_at      TIMESTAMPTZ NOT NULL,
    is_revoked      BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE refresh_tokens IS 'JWT Refresh Token 관리. 토큰은 SHA-256 해시로 저장.';
```

---

## 4. JSONB Schema Definitions

### 4.1 saju_data (saju_profiles.saju_data)

PRD 7.2 기반 사주 산출 결과 전체 데이터.

```json
{
  "$schema": "saju_data_v1",

  "four_pillars": {
    "year": {
      "stem": "甲",
      "branch": "子",
      "stem_kr": "갑",
      "branch_kr": "자",
      "stem_element": "wood",
      "branch_element": "water"
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
    "wood": 2,
    "fire": 3,
    "earth": 1,
    "metal": 2,
    "water": 0,
    "dominant": "fire",
    "lacking": "water"
  },

  "ten_stars": {
    "year_stem": "편인",
    "year_branch": "편관",
    "month_stem": "겁재",
    "month_branch": "비견",
    "day_branch": "겁재",
    "hour_stem": "식신",
    "hour_branch": "식신",
    "summary": {
      "비겁": 2,
      "식상": 2,
      "재성": 0,
      "관성": 1,
      "인성": 1
    }
  },

  "twelve_stages": {
    "year": "사",
    "month": "장생",
    "day": "제왕",
    "hour": "병"
  },

  "special_stars": [
    {
      "name": "역마살",
      "hanja": "驛馬殺",
      "pillar": "year",
      "description": "이동과 변화가 많은 기운"
    },
    {
      "name": "천을귀인",
      "hanja": "天乙貴人",
      "pillar": "day",
      "description": "어려울 때 귀인의 도움을 받는 기운"
    },
    {
      "name": "문창귀인",
      "hanja": "文昌貴人",
      "pillar": "hour",
      "description": "학문과 문서에 밝은 기운"
    }
  ],

  "geokguk": {
    "type": "정관격",
    "hanja": "正官格",
    "category": "정격",
    "description": "월지 정기의 정관이 투출하여 격을 이룸"
  },

  "major_luck_cycles": [
    {
      "age_start": 3,
      "age_end": 12,
      "stem": "丁",
      "branch": "卯",
      "stem_kr": "정",
      "branch_kr": "묘",
      "ten_star": "겁재",
      "twelve_stage": "관대"
    },
    {
      "age_start": 13,
      "age_end": 22,
      "stem": "戊",
      "branch": "辰",
      "stem_kr": "무",
      "branch_kr": "진",
      "ten_star": "비견",
      "twelve_stage": "쇠"
    }
  ],

  "day_master": {
    "stem": "戊",
    "element": "earth",
    "yin_yang": "yang",
    "strength": "strong",
    "description": "무토(戊土) 일간. 양의 토 기운. 산, 제방과 같은 큰 흙의 성질."
  }
}
```

### 4.2 messages.metadata (AI 응답 메타데이터)

```json
{
  "llm_provider": "claude",
  "model": "claude-sonnet-4-20250514",
  "input_tokens": 2500,
  "output_tokens": 800,
  "total_tokens": 3300,
  "latency_ms": 2340,
  "first_token_ms": 890,
  "rag_sources": [
    {
      "chunk_id": "chunk_abc123",
      "source": "jeokcheonsu",
      "category": "ten_stars",
      "similarity": 0.87
    },
    {
      "chunk_id": "chunk_def456",
      "source": "japyeongjinjeon",
      "category": "geokguk",
      "similarity": 0.82
    }
  ],
  "topic_detected": "wealth",
  "safety_filtered": false,
  "prompt_version": "v1.2"
}
```

### 4.3 daily_fortunes.fortune_data (일일 운세 데이터)

```json
{
  "overall": {
    "score": 78,
    "keyword": "전진",
    "color": "#4CAF50",
    "direction": "동쪽"
  },
  "categories": {
    "wealth": {
      "score": 85,
      "summary": "편재의 기운이 강하여 예상치 못한 수입이 있을 수 있습니다."
    },
    "romance": {
      "score": 65,
      "summary": "도화살의 기운이 약해 조용한 하루가 될 수 있습니다."
    },
    "health": {
      "score": 70,
      "summary": "토 기운 과다로 소화기 건강에 유의하세요."
    },
    "career": {
      "score": 80,
      "summary": "정관의 기운이 도와 업무에서 인정받을 수 있습니다."
    }
  },
  "day_interaction": {
    "day_stem": "甲",
    "day_branch": "午",
    "interaction_with_day_master": "편재",
    "description": "일간 무토(戊土)에게 갑목(甲木)은 편관이 되어..."
  },
  "lucky_numbers": [3, 7, 8],
  "lucky_time": "사시(巳時, 09:00~11:00)"
}
```

### 4.4 knowledge_chunks.metadata (RAG 청크 메타데이터)

```json
{
  "related_elements": ["wood", "fire"],
  "related_stars": ["정관", "편인"],
  "related_special_stars": ["천을귀인"],
  "applicable_topics": ["career", "general"],
  "original_text": "甲木參天...",
  "chapter": "천간론",
  "section": "갑목(甲木)",
  "page": 15
}
```

---

## 5. Indexing Strategy

### 5.1 Primary Indexes (자동 생성)

모든 테이블의 `id (PK)` 컬럼에 자동 생성되는 B-tree 인덱스.

### 5.2 Custom Indexes

```sql
-- ===== users =====

-- OAuth 로그인 조회 (UNIQUE 제약 조건으로 자동 생성)
-- CREATE UNIQUE INDEX idx_users_provider ON users(provider, provider_id);

-- 이메일 조회
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;

-- Soft delete 필터 (활성 사용자만)
CREATE INDEX idx_users_active ON users(id) WHERE deleted_at IS NULL;


-- ===== saju_profiles =====

-- 사용자별 프로필 목록
CREATE INDEX idx_profiles_user ON saju_profiles(user_id) WHERE deleted_at IS NULL;

-- 일간(日干) 기반 통계 (JSONB 경로)
CREATE INDEX idx_profiles_day_stem ON saju_profiles(
    (saju_data->'day_master'->>'stem')
) WHERE deleted_at IS NULL;

-- 격국 기반 통계 (JSONB 경로)
CREATE INDEX idx_profiles_geokguk ON saju_profiles(
    (saju_data->'geokguk'->>'type')
) WHERE deleted_at IS NULL;


-- ===== consultations =====

-- 사용자별 상담 이력 (최신순, cursor pagination)
CREATE INDEX idx_consultations_user_date ON consultations(user_id, created_at DESC);

-- 프로필별 상담 이력
CREATE INDEX idx_consultations_profile ON consultations(profile_id, created_at DESC);

-- 활성 상담 세션
CREATE INDEX idx_consultations_active ON consultations(user_id, status)
    WHERE status = 'active';


-- ===== messages =====

-- 상담별 메시지 시간순
CREATE INDEX idx_messages_consultation ON messages(consultation_id, created_at);

-- 피드백 분석 (thumbs_up/down 응답만)
CREATE INDEX idx_messages_feedback ON messages(feedback, created_at)
    WHERE role = 'assistant' AND feedback != 'none';


-- ===== daily_fortunes =====

-- 프로필별 일일 운세 (UNIQUE 제약 조건으로 자동 생성)
-- CREATE UNIQUE INDEX idx_daily_fortune ON daily_fortunes(profile_id, date);

-- 날짜별 운세 조회 (배치 생성 확인용)
CREATE INDEX idx_daily_fortunes_date ON daily_fortunes(date);


-- ===== payments =====

-- 사용자별 결제 이력
CREATE INDEX idx_payments_user ON payments(user_id, created_at DESC);

-- PG 트랜잭션 조회 (웹훅 처리)
CREATE INDEX idx_payments_pg_key ON payments(pg_payment_key) WHERE pg_payment_key IS NOT NULL;

-- 상태별 조회
CREATE INDEX idx_payments_status ON payments(status, created_at)
    WHERE status IN ('pending', 'completed');


-- ===== subscriptions =====

-- 사용자별 활성 구독
CREATE INDEX idx_subscriptions_user_active ON subscriptions(user_id)
    WHERE status IN ('active', 'past_due');

-- 만료 예정 구독 (배치 처리용)
CREATE INDEX idx_subscriptions_expiring ON subscriptions(current_period_end)
    WHERE status = 'active';


-- ===== knowledge_chunks =====

-- pgvector 벡터 인덱스 (IVFFlat)
-- 참고: 데이터 삽입 후 생성해야 최적 성능
CREATE INDEX idx_knowledge_embedding ON knowledge_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);  -- sqrt(총 청크 수) 기준. ~2500 청크 → ~50 lists

-- 메타데이터 필터 (출처별, 카테고리별)
CREATE INDEX idx_knowledge_source ON knowledge_chunks(source);
CREATE INDEX idx_knowledge_category ON knowledge_chunks(category);

-- JSONB GIN 인덱스 (메타데이터 내 배열/키 검색)
CREATE INDEX idx_knowledge_metadata ON knowledge_chunks USING GIN (metadata);


-- ===== refresh_tokens =====

-- 토큰 해시 조회
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash)
    WHERE is_revoked = FALSE;

-- 사용자별 토큰 (로그아웃 시 일괄 무효화)
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id)
    WHERE is_revoked = FALSE;

-- 만료 토큰 정리 (배치)
CREATE INDEX idx_refresh_tokens_expired ON refresh_tokens(expires_at)
    WHERE is_revoked = FALSE;
```

### 5.3 인덱스 전략 요약

| 인덱스 유형 | 사용 테이블 | 목적 |
|-------------|------------|------|
| **B-tree** | 대부분 | 등치/범위 검색 (PK, FK, 날짜) |
| **Partial (WHERE)** | users, consultations, payments, refresh_tokens | 활성 데이터만 인덱싱하여 크기 절감 |
| **Expression** | saju_profiles | JSONB 내부 필드 인덱싱 |
| **GIN** | knowledge_chunks | JSONB 메타데이터 배열/키 검색 |
| **IVFFlat (pgvector)** | knowledge_chunks | 벡터 유사도 검색 (RAG) |

---

## 6. Migration Strategy

### 6.1 Alembic 마이그레이션 관리

```
alembic/
├── versions/
│   ├── 001_create_users.py
│   ├── 002_create_saju_profiles.py
│   ├── 003_create_consultations_messages.py
│   ├── 004_create_daily_fortunes.py
│   ├── 005_create_payments_subscriptions.py
│   ├── 006_create_knowledge_chunks.py
│   ├── 007_create_consultation_feedbacks.py
│   ├── 008_create_refresh_tokens.py
│   └── 009_create_indexes.py
├── env.py
└── alembic.ini
```

### 6.2 마이그레이션 순서

```
Phase 1 (Week 1): 기본 테이블
  001: users (인증 모듈 즉시 필요)
  002: saju_profiles (사주 엔진 연동)
  008: refresh_tokens (인증 모듈)

Phase 2 (Week 3): 상담 테이블
  003: consultations + messages
  007: consultation_feedbacks

Phase 3 (Week 5): 운세 + 지식 베이스
  004: daily_fortunes
  006: knowledge_chunks (pgvector extension 포함)

Phase 4 (Week 5-6): 결제 테이블
  005: payments + subscriptions

Phase 5 (Week 7): 인덱스 최적화
  009: 모든 커스텀 인덱스 생성 (데이터 삽입 후)
```

### 6.3 데이터 보관 정책

| 테이블 | 보관 기간 | 정책 |
|--------|----------|------|
| users | 탈퇴 후 30일 | Soft delete -> 30일 후 Hard delete (배치) |
| saju_profiles | 사용자 삭제 시 CASCADE | 암호화 데이터 완전 삭제 |
| consultations | 90일 후 익명화 옵션 | user_id NULL 처리 + 내용 마스킹 |
| messages | consultations와 동일 | 상담 익명화 시 함께 처리 |
| daily_fortunes | 90일 보관 | 오래된 운세 자동 삭제 (배치) |
| payments | 5년 보관 (법적) | 아카이브 테이블로 이동 |
| knowledge_chunks | 영구 | 버전 관리로 업데이트 |
| refresh_tokens | 만료 후 7일 | 만료 토큰 배치 삭제 |

### 6.4 배치 작업 스케줄

```python
# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    # 매일 자정 (KST)
    'generate-daily-fortunes': {
        'task': 'fortune.tasks.generate_daily_fortunes',
        'schedule': crontab(hour=0, minute=0),  # UTC 15:00 = KST 00:00
    },

    # 매일 새벽 3시 (KST)
    'cleanup-expired-tokens': {
        'task': 'auth.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=18, minute=0),  # UTC 18:00 = KST 03:00
    },

    # 매일 새벽 4시 (KST)
    'reset-daily-consult-count': {
        'task': 'auth.tasks.reset_daily_consult_count',
        'schedule': crontab(hour=19, minute=0),  # UTC 19:00 = KST 04:00
    },

    # 매주 일요일 새벽 2시 (KST)
    'cleanup-old-fortunes': {
        'task': 'fortune.tasks.cleanup_old_fortunes',
        'schedule': crontab(hour=17, minute=0, day_of_week=0),
    },

    # 매월 1일 새벽 5시 (KST)
    'anonymize-old-consultations': {
        'task': 'consultation.tasks.anonymize_old_consultations',
        'schedule': crontab(hour=20, minute=0, day_of_month=1),
    },

    # 매월 1일 새벽 6시 (KST)
    'hard-delete-expired-users': {
        'task': 'auth.tasks.hard_delete_expired_users',
        'schedule': crontab(hour=21, minute=0, day_of_month=1),
    },
}
```

---

## Appendix: Quick Reference

### A. Table Count Summary

| Table | Estimated Rows (MVP) | Estimated Rows (v1.0) |
|-------|---------------------|----------------------|
| users | 1,000 | 50,000 |
| saju_profiles | 1,000 | 100,000 |
| consultations | 10,000 | 500,000 |
| messages | 100,000 | 5,000,000 |
| daily_fortunes | 30,000 | 1,500,000 |
| payments | 100 | 10,000 |
| subscriptions | 50 | 5,000 |
| knowledge_chunks | 730 | 1,500 |
| consultation_feedbacks | 2,000 | 100,000 |
| refresh_tokens | 2,000 | 100,000 |

### B. Storage Estimate

| Component | MVP | v1.0 |
|-----------|-----|------|
| 테이블 데이터 | ~500 MB | ~10 GB |
| 인덱스 | ~200 MB | ~5 GB |
| pgvector 임베딩 | ~50 MB | ~100 MB |
| WAL/로그 | ~1 GB | ~5 GB |
| **총합** | **~2 GB** | **~20 GB** |

RDS db.t3.medium (20 GB SSD)는 MVP에 충분하며, v1.0에서 db.r6g.large (100 GB)로 확장한다.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-25 | CTO Lead | Initial DB schema design based on PRD v1.0 |
