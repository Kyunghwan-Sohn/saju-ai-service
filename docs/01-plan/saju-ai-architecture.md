# Saju AI Service - Technical Architecture Document

> **Version:** 1.0
> **Date:** 2026-03-25
> **Author:** CTO Lead
> **Status:** Draft
> **Based on:** [PRD v1.0](../00-pm/saju-ai-service.prd.md)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Architecture Decision: Modular Monolith](#2-architecture-decision-modular-monolith)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture Detail](#4-system-architecture-detail)
5. [AI/LLM Integration Design](#5-aillm-integration-design)
6. [Database Architecture](#6-database-architecture)
7. [API Design](#7-api-design)
8. [Authentication & Authorization](#8-authentication--authorization)
9. [Infrastructure & Deployment](#9-infrastructure--deployment)
10. [Scalability Strategy](#10-scalability-strategy)
11. [Security Architecture](#11-security-architecture)
12. [Monitoring & Observability](#12-monitoring--observability)

---

## 1. Architecture Overview

### 1.1 High-Level System Architecture

```
                          ┌─────────────────────────┐
                          │       CDN (CloudFront)   │
                          │   Static Assets, SSR     │
                          └────────────┬────────────┘
                                       │
┌──────────────────────────────────────┼──────────────────────────────────────┐
│                          Client Layer │                                      │
│  ┌──────────────┐  ┌───────────────┐│ ┌─────────────────────────────────┐  │
│  │  Web App      │  │  Mobile Web   ││ │  KakaoTalk Mini App (Future)    │  │
│  │  (Next.js 15) │  │  (Responsive) ││ │                                 │  │
│  └──────┬───────┘  └───────┬───────┘│ └────────────────┬────────────────┘  │
└─────────┼──────────────────┼────────┼──────────────────┼───────────────────┘
          │                  │        │                  │
          └──────────┬───────┘        └─────────┬────────┘
                     ▼                          ▼
        ┌────────────────────────────────────────────────┐
        │         API Gateway (AWS API Gateway)           │
        │   Rate Limiting / JWT Validation / CORS / WAF   │
        └────────────────────────┬───────────────────────┘
                                 │
        ┌────────────────────────▼───────────────────────┐
        │            FastAPI Application (ECS Fargate)    │
        │                                                 │
        │  ┌───────────┐ ┌───────────┐ ┌──────────────┐ │
        │  │   Auth     │ │   Saju    │ │  AI Counsel  │ │
        │  │   Module   │ │  Engine   │ │   Module     │ │
        │  │            │ │  Module   │ │              │ │
        │  │ - OAuth    │ │           │ │ - LLM Gateway│ │
        │  │ - JWT      │ │ - 만세력   │ │ - Prompt Mgr│ │
        │  │ - Session  │ │ - 사주산출  │ │ - RAG Engine│ │
        │  │            │ │ - 운세계산  │ │ - Streaming │ │
        │  │            │ │ - 신살판단  │ │ - Safety    │ │
        │  └───────────┘ └───────────┘ └──────────────┘ │
        │                                                 │
        │  ┌───────────┐ ┌───────────┐ ┌──────────────┐ │
        │  │  Fortune   │ │  Payment  │ │   Share      │ │
        │  │  Module    │ │  Module   │ │   Module     │ │
        │  │            │ │           │ │              │ │
        │  │ - Daily    │ │ - Toss PG │ │ - Card Gen  │ │
        │  │ - Monthly  │ │ - 구독관리 │ │ - SNS Share │ │
        │  │ - Yearly   │ │ - 건별결제 │ │              │ │
        │  └───────────┘ └───────────┘ └──────────────┘ │
        └───────┬──────────────┬──────────────┬──────────┘
                │              │              │
        ┌───────▼──────────────▼──────────────▼──────────┐
        │                   Data Layer                    │
        │  ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
        │  │PostgreSQL │ │  Redis   │ │  S3             │ │
        │  │ 16 + pg-  │ │  7       │ │  (Share Cards,  │ │
        │  │ vector    │ │ (Cache,  │ │   Static Assets)│ │
        │  │ (RDS)     │ │  Rate    │ │                 │ │
        │  │           │ │  Limit,  │ │                 │ │
        │  │           │ │  Session)│ │                 │ │
        │  └──────────┘ └──────────┘ └────────────────┘ │
        └────────────────────────────────────────────────┘
```

### 1.2 Architecture Concept: DB-First + abcllm Batch Transformation

> **v2.0 핵심 변경**: 실시간 LLM 호출 → DB 사전 구축 + abcllm 배치 변형
> 상세: [architecture-concept-v2.md](architecture-concept-v2.md)

**온라인 서빙 (사용자 요청 처리 < 100ms):**
1. 클라이언트(Next.js)가 HTTPS 요청을 CloudFront를 통해 전송
2. API Gateway에서 Rate Limiting, JWT 검증, CORS 처리
3. FastAPI: 사주 계산 엔진으로 사주팔자 산출 (< 10ms)
4. **Redis/PostgreSQL에서 사전 구축된 콘텐츠 조회** (< 50ms)
5. 개인화 조합 (이름, 현재 운세 삽입) 후 즉시 응답

**오프라인 배치 (콘텐츠 생성/변형):**
1. Celery Beat 스케줄러가 배치 트리거
2. abcllm으로 사주 풀이 콘텐츠 생성 및 서술 변형
3. 품질 검증 + 안전성 필터 통과 후 DB 저장
4. 주기적 반복으로 콘텐츠 다양성 확보

---

## 2. Architecture Decision: Modular Monolith

### 2.1 결정

**Modular Monolith (모듈러 모놀리스)** 아키텍처를 MVP 및 v1.0에 채택한다.

### 2.2 결정 근거

| 비교 항목 | Microservices | Modular Monolith | 판단 |
|-----------|--------------|-------------------|------|
| **팀 규모** | 서비스당 2+ 명 필요 (최소 10명) | 7명 팀에 최적 | Monolith 유리 |
| **개발 속도** | 서비스 간 통신, 배포 파이프라인 복잡 | 단일 코드베이스, 빠른 개발 | Monolith 유리 |
| **운영 복잡도** | 서비스 디스커버리, 분산 트레이싱 필수 | 단일 프로세스 관리 | Monolith 유리 |
| **MVP 일정 (8주)** | 인프라 셋업에 2~3주 소모 | 즉시 기능 개발 가능 | Monolith 유리 |
| **비용** | 서비스별 인프라 비용 | 단일 인프라, 월 500만원 제약 충족 | Monolith 유리 |
| **확장성** | 서비스별 독립 스케일링 | 수평 확장(ECS Task 추가)으로 충분 | 동일 |
| **향후 전환** | - | 모듈 경계 명확히 하여 추후 분리 가능 | 전환 비용 낮음 |

### 2.3 모듈 경계 설계 원칙

```
saju-ai-service/
├── app/
│   ├── main.py                    # FastAPI app entrypoint
│   ├── config.py                  # 환경 설정
│   ├── dependencies.py            # 공통 의존성 주입
│   │
│   ├── modules/
│   │   ├── auth/                  # 인증/인가 모듈
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── saju_engine/           # 사주 산출 엔진 모듈
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── calculator.py      # 핵심 사주 계산 로직
│   │   │   ├── manseryeok.py      # 만세력 데이터 처리
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── ai_counsel/            # AI 상담 모듈
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── prompt_manager.py  # 프롬프트 관리
│   │   │   ├── rag_engine.py      # RAG 파이프라인
│   │   │   ├── llm_gateway.py     # LLM 멀티프로바이더 게이트웨이
│   │   │   ├── safety_filter.py   # 안전성 필터
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── fortune/               # 운세 콘텐츠 모듈
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── batch.py           # 일일 운세 배치 생성
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── payment/               # 결제 모듈
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── toss_client.py     # Toss Payments 연동
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   │
│   │   └── share/                 # 공유 모듈
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── card_generator.py  # 공유 카드 이미지 생성
│   │       └── schemas.py
│   │
│   ├── core/                      # 공통 핵심 모듈
│   │   ├── database.py            # DB 연결 관리
│   │   ├── redis.py               # Redis 연결 관리
│   │   ├── security.py            # JWT, 암호화 유틸
│   │   ├── middleware.py          # 공통 미들웨어
│   │   └── exceptions.py         # 공통 예외 정의
│   │
│   └── common/
│       ├── constants.py           # 천간, 지지, 오행 상수
│       ├── enums.py               # 공통 열거형
│       └── utils.py               # 유틸리티 함수
│
├── data/
│   ├── manseryeok/                # 만세력 데이터 (1900~2100)
│   ├── knowledge_base/            # RAG 명리학 지식 베이스
│   └── prompts/                   # 프롬프트 템플릿
│
├── tests/
├── alembic/                       # DB 마이그레이션
├── scripts/                       # 배치/유틸리티 스크립트
└── docker/
```

각 모듈은 자체 router, service, models, schemas를 가지며, 모듈 간 의존성은 service 레이어의 인터페이스를 통해서만 허용한다. 이를 통해 향후 마이크로서비스 분리가 필요할 때 모듈 단위로 추출할 수 있다.

### 2.4 모듈 간 의존성 규칙

```
auth ──────────── (독립, 다른 모듈이 참조)
saju_engine ───── (독립, ai_counsel과 fortune이 참조)
ai_counsel ────── saju_engine, auth에 의존
fortune ────────── saju_engine, auth에 의존
payment ────────── auth에 의존
share ──────────── auth, fortune에 의존
```

**규칙:**
- 순환 의존성 금지
- 모듈 간 통신은 Python import를 통한 service 레이어 호출 (함수 호출)
- 향후 마이크로서비스 전환 시, 함수 호출을 HTTP/gRPC 호출로 교체

---

## 3. Technology Stack

### 3.1 Frontend

| 기술 | 버전 | 선정 이유 |
|------|------|-----------|
| **Next.js** | 15 (App Router) | SSR/SSG로 SEO 최적화 (검색 유입 중요), React Server Components로 성능 최적화, 모바일 우선 반응형 웹 개발에 최적 |
| **TypeScript** | 5.x | 타입 안정성, 사주 데이터 구조(천간/지지/오행)의 복잡한 타입 정의에 필수 |
| **Tailwind CSS** | 3.x | 오행 컬러 시스템 등 커스텀 디자인 토큰 관리 용이, 빠른 UI 개발 |
| **shadcn/ui** | latest | 접근성(a11y) 내장, 디자인 시스템 커스터마이징 자유도 높음 |
| **Zustand** | 5.x | 가벼운 상태 관리, 사주 프로필 캐싱, SSR 호환성 |
| **React Query (TanStack)** | 5.x | 서버 상태 관리, 캐싱, 낙관적 업데이트 |

**모바일 우선 전략 근거:**
- PRD Persona A(MZ세대)의 모바일 사용 비율 예상 80%+
- 360px 최소 너비 지원 요구사항 (PRD 5.6)
- PWA 지원으로 홈 화면 추가 경험 제공

### 3.2 Backend

| 기술 | 버전 | 선정 이유 |
|------|------|-----------|
| **Python** | 3.12 | AI/ML 생태계 (LangChain, OpenAI SDK, 한글 NLP) 완벽 호환, 사주 계산 로직 구현에 적합한 수학 라이브러리 |
| **FastAPI** | 0.115+ | 비동기(async) 네이티브 지원으로 LLM API 호출 시 논블로킹 처리, SSE 스트리밍 내장 지원, 자동 OpenAPI 문서 생성 |
| **SQLAlchemy** | 2.0 | ORM + Raw SQL 혼용 가능, 비동기 세션 지원, Alembic 마이그레이션 |
| **Pydantic** | 2.x | FastAPI 네이티브 통합, 사주 데이터 JSONB 스키마 검증 |
| **Celery** | 5.x | 일일 운세 배치 생성, 공유 카드 이미지 비동기 생성 |
| **LangChain** | 0.3.x | LLM 멀티프로바이더 추상화, RAG 파이프라인, 프롬프트 체이닝 |

**FastAPI 선정 핵심 근거:**
- SSE(Server-Sent Events) 스트리밍이 핵심 요구사항 (PRD US-206, 7.4절)
- `async/await`로 LLM API 응답 대기 중 다른 요청 처리 가능 (동시 접속 10,000명 목표)
- Python AI/ML 생태계 직접 활용 (사주 계산, 벡터 검색, NLP)

### 3.3 Database

| 기술 | 버전 | 용도 | 선정 이유 |
|------|------|------|-----------|
| **PostgreSQL** | 16 | 주 데이터베이스 | JSONB로 사주 데이터 유연 저장, pgvector 확장으로 별도 Vector DB 불필요, 관리형 RDS로 운영 부담 최소화 |
| **pgvector** | 0.7+ | 벡터 검색 (RAG) | PostgreSQL 내 통합으로 인프라 단순화, 명리학 지식 베이스 규모(수천 문서)에 충분한 성능 |
| **Redis** | 7 | 캐시, 세션, Rate Limiting | 일일 운세 캐싱 (TTL 24h), JWT 블랙리스트, API Rate Limiting 카운터, 상담 횟수 일일 제한 추적 |

**pgvector 선택 근거 (vs Pinecone):**
- PRD에서 인프라 비용 월 500만원 제약 명시 -- Pinecone 추가 비용 절감
- 명리학 지식 베이스 규모: 원전 3권(적천수, 자평진전, 궁통보감) + 해설서 = 수천 개 청크
- 이 규모에서 pgvector 성능 충분 (100ms 이내 검색)
- PostgreSQL 하나로 관계형 데이터 + 벡터 검색 통합 관리

### 3.4 AI/LLM

| 기술 | 용도 | 선정 이유 |
|------|------|-----------|
| **abcllm (Primary)** | 사주 콘텐츠 배치 생성/변형 | 서술 변형 능력 우수, 배치 API 지원, 한국어 성능 우수 |
| **text-embedding-3-small** | 벡터 임베딩 | 배치 파이프라인에서 RAG용 명리학 텍스트 임베딩 |
| **LangChain** | 배치 파이프라인 오케스트레이션 | 프롬프트 템플릿 관리, RAG 체인 (배치 시에만 사용, 온라인 서빙 불필요) |

**v2 LLM 사용 전략 (DB-First):**
- **온라인 서빙**: LLM 호출 없음 → DB에서 즉시 송출 (< 100ms)
- **오프라인 배치**: abcllm으로 콘텐츠 사전 생성 및 서술 변형
- **프리미엄 대화 상담**: abcllm 실시간 호출 (프리미엄 플랜 전용)
- 배치 비용은 고정비로 예측 가능 (월 LLM 비용 80%+ 절감)

### 3.5 Infrastructure

| 기술 | 용도 | 선정 이유 |
|------|------|-----------|
| **AWS ECS Fargate** | 컨테이너 오케스트레이션 | 서버리스 컨테이너로 운영 부담 최소화, Auto Scaling 내장, 7명 팀에서 K8s 운영은 과한 부담 |
| **AWS RDS** | PostgreSQL 관리 | 자동 백업, Read Replica, 모니터링 내장 |
| **AWS ElastiCache** | Redis 관리 | 자동 장애 조치, 클러스터 모드 확장 가능 |
| **AWS CloudFront** | CDN | Next.js 정적 자산 배포, 한국 엣지 로케이션 |
| **AWS S3** | 객체 스토리지 | 공유 카드 이미지, 정적 자산 |
| **AWS API Gateway** | API 진입점 | WAF 통합, Rate Limiting, 요청 검증 |
| **GitHub Actions** | CI/CD | 자동 테스트, Docker 빌드, ECS 배포 |

---

## 4. System Architecture Detail

### 4.1 서비스 간 통신 방식

모듈러 모놀리스 구조이므로 모듈 간 통신은 **동기식 함수 호출**이다.

```python
# ai_counsel/service.py 에서 saju_engine 호출 예시
from app.modules.saju_engine.service import SajuEngineService

class AICounselService:
    def __init__(self, saju_engine: SajuEngineService):
        self.saju_engine = saju_engine

    async def start_consultation(self, profile_id: str, topic: str):
        # 사주 데이터 조회 (동기식 함수 호출)
        saju_data = await self.saju_engine.get_saju_data(profile_id)
        current_fortune = await self.saju_engine.calculate_current_fortune(profile_id)
        # ...
```

**외부 서비스 통신:**

| 통신 대상 | 방식 | 프로토콜 |
|-----------|------|----------|
| LLM API (Claude/GPT) | 비동기 HTTP | HTTPS + SSE |
| Toss Payments | 비동기 HTTP | HTTPS (REST) |
| OAuth Provider (Kakao 등) | 비동기 HTTP | HTTPS (OAuth 2.0) |
| S3 | AWS SDK | HTTPS |

### 4.2 비동기 처리 아키텍처

```
┌──────────────────────────────────────────┐
│           Synchronous Path                │
│   (API Request → Business Logic → DB)     │
│                                           │
│   사주 산출, 프로필 CRUD, 로그인           │
│   목표: < 500ms                           │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│           Streaming Path (SSE)            │
│   (API Request → LLM → Token Streaming)   │
│                                           │
│   AI 상담 응답                             │
│   첫 토큰: < 1.5초, 전체: < 30초          │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│           Background Jobs (Celery)        │
│   (Schedule/Trigger → Worker → DB/S3)     │
│                                           │
│   일일 운세 배치 생성 (매일 자정)           │
│   공유 카드 이미지 생성                    │
│   상담 데이터 익명화 (90일 후)             │
└──────────────────────────────────────────┘
```

### 4.3 에러 처리 및 회복 전략

| 장애 유형 | 감지 | 회복 전략 |
|-----------|------|-----------|
| abcllm 배치 실패 | 배치 작업 에러 감지 | 재시도 3회, 실패 시 기존 콘텐츠 유지 (서비스 영향 없음) |
| abcllm API Rate Limit | 429 응답 | 배치 속도 조절, 지수 백오프 (온라인 서빙 영향 없음) |
| DB 연결 실패 | 연결 풀 헬스체크 | 자동 재연결, Read Replica 폴백 |
| Redis 장애 | 연결 에러 | 캐시 우회(DB 직접 조회), Rate Limiting 비활성화 |
| 사주 산출 오류 | 입력 검증 실패 | 상세 에러 메시지 반환, 오류 로깅 |

---

## 5. AI/LLM Integration Design (사주 풀이 엔진)

### 5.1 전체 AI 파이프라인 (v2: DB-First)

> **변경**: 실시간 6단계 파이프라인 → 온라인 서빙(4단계) + 오프라인 배치(별도) 분리

#### 온라인 서빙 파이프라인 (사용자 요청 시, < 100ms)

```
사용자 요청 (생년월일 + 주제)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  1. Saju Calculator (< 10ms)                             │
│     사주팔자 산출 → saju_key 생성                        │
│     (예: '甲子_乙丑_丙寅_丁卯')                          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  2. Content Lookup (< 50ms)                              │
│     Redis 캐시 조회 → 미스 시 PostgreSQL 조회            │
│     saju_contents 테이블에서 해당 조합 + 주제 검색       │
│     복수 버전 중 미노출/랜덤 선택 (다양성 보장)          │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  3. Personalization (< 20ms)                             │
│     ├─ 사용자 이름/성별 삽입                             │
│     ├─ 현재 대운/세운/월운 정보 결합                     │
│     └─ 오늘 날짜 기반 시의성 반영                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  4. Response Assembly (< 20ms)                           │
│     ├─ 포맷팅 (구조화된 JSON/마크다운)                   │
│     └─ 캐시 저장 (Redis, TTL 설정)                       │
└─────────────────────────────────────────────────────────┘
```

#### 오프라인 배치 파이프라인 (Celery Beat 스케줄, 서비스 무관)

```
Scheduler Trigger (Cron)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  1. Combo Generator                                      │
│     대상 사주 조합 + 주제 + 변형 타겟 결정               │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  2. abcllm Batch Engine                                  │
│     ├─ 사주 데이터 + RAG 지식 → 프롬프트 조합            │
│     ├─ abcllm 호출 → 콘텐츠 생성/서술 변형              │
│     ├─ 변형 전략: warm(공감) / expert(분석) / friendly   │
│     └─ 동일 해석, 다른 표현 (다양성 확보)                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  3. Quality Gate                                         │
│     ├─ Safety Filter (유해 콘텐츠 차단)                  │
│     ├─ 명리학 일관성 검증 (오행/십성 정합성)             │
│     ├─ 길이/형식 표준 검증                               │
│     └─ 품질 점수 산출                                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  4. DB Writer                                            │
│     saju_contents 테이블에 새 버전으로 저장              │
│     이전 버전 is_active = false 처리 (보존)              │
│     Redis 캐시 무효화 (다음 조회 시 새 버전 로드)        │
└─────────────────────────────────────────────────────────┘
```

### 5.2 사주 계산 엔진 (Saju Engine) 상세 설계

사주 계산 엔진은 순수 Python으로 구현하며, LLM과 독립적으로 100% 정확한 결과를 보장해야 한다.

#### 5.2.1 핵심 계산 모듈

```python
# 사주 산출 파이프라인
class SajuCalculator:
    """
    사주팔자 산출 핵심 클래스
    1. 양력/음력 변환 (만세력 데이터 기반)
    2. 절기 경계 판단 (월주 산출의 핵심)
    3. 사주팔자(연주/월주/일주/시주) 산출
    4. 십성/12운성/신살/격국 판단
    5. 대운/세운/월운/일운 계산
    """

    def calculate_four_pillars(
        self,
        birth_date: date,
        birth_time: time | None,
        is_lunar: bool,
        is_leap_month: bool,
        gender: str
    ) -> SajuResult:
        # Step 1: 양력 통일
        solar_date = self._to_solar(birth_date, is_lunar, is_leap_month)

        # Step 2: 절기 기반 월주 결정
        month_pillar = self._calculate_month_pillar(solar_date)

        # Step 3: 연주 결정 (입춘 기준)
        year_pillar = self._calculate_year_pillar(solar_date)

        # Step 4: 일주 결정 (만세력 직접 조회)
        day_pillar = self._calculate_day_pillar(solar_date)

        # Step 5: 시주 결정 (일간 기준)
        hour_pillar = self._calculate_hour_pillar(day_pillar.stem, birth_time)

        # Step 6: 파생 데이터 계산
        five_elements = self._analyze_five_elements(pillars)
        ten_stars = self._calculate_ten_stars(day_pillar.stem, pillars)
        twelve_stages = self._calculate_twelve_stages(day_pillar.stem, pillars)
        special_stars = self._find_special_stars(pillars)
        geokguk = self._determine_geokguk(pillars, ten_stars, month_pillar)

        # Step 7: 대운 계산
        major_luck = self._calculate_major_luck(
            year_pillar, month_pillar, gender, solar_date
        )

        return SajuResult(...)
```

#### 5.2.2 만세력 데이터 구조

```
data/manseryeok/
├── solar_terms.json        # 절기 데이터 (1900~2100, 분 단위 정밀도)
├── daily_stems.json        # 일진(일간/일지) 데이터
├── lunar_calendar.json     # 음양력 변환 테이블
└── leap_months.json        # 윤달 데이터
```

절기 데이터는 한국천문연구원 데이터를 기반으로 하며, 1,000개 이상의 테스트 케이스로 교차 검증한다 (PRD Risk R2 대응).

#### 5.2.3 주요 계산 알고리즘

| 계산 | 알고리즘 | 핵심 주의사항 |
|------|----------|--------------|
| 연주 | 입춘(2월 3~5일) 기준 연도 전환 | 1월 1일이 아닌 입춘 기점 |
| 월주 | 24절기 중 절(節) 기준 | 절기 시간이 정확해야 함 |
| 일주 | 만세력 테이블 직접 조회 | 자시(子時, 23:00~01:00) 야자시/조자시 처리 |
| 시주 | 일간(日干)에 따른 시간 천간 결정 | 갑기일 → 갑자시, 을경일 → 병자시... |
| 대운 | 성별 + 연간 양/음 → 순행/역행 | 대운수(절입일 기준) 계산 정밀도 |
| 십성 | 일간 vs 타 천간의 오행 관계 | 음양 구분 필수 (편/정) |
| 12운성 | 일간 오행의 12지지 순환 | 양간/음간 순행/역행 차이 |
| 신살 | 특정 간지 조합 패턴 매칭 | 30종 이상, 기준주(연/일)별 상이 |
| 격국 | 월지 장간 + 투출 + 통근 판단 | 정격 8격 + 외격(종격, 화격 등) |

### 5.3 LLM 프롬프트 전략

#### 5.3.1 System Prompt 구조

```
[역할 정의]
당신은 30년 경력의 사주명리학 전문가입니다. 전통 명리학의 정통 이론을
바탕으로 현대적이고 실용적인 해석을 제공합니다.

[해석 원칙]
1. 반드시 제공된 사주 데이터를 기반으로만 해석합니다.
2. 명리학적 근거(십성, 오행, 신살 등)를 함께 설명합니다.
3. 긍정적이고 건설적인 방향으로 해석을 전달합니다.
4. 부정적 요소는 주의사항과 대처법 중심으로 설명합니다.
5. "~일 수 있습니다", "~경향이 있습니다" 등 확률적 표현을 사용합니다.

[윤리 가이드라인]
- 의학적, 법적, 재정적 전문 조언을 제공하지 않습니다.
- 극단적이거나 공포를 유발하는 표현을 절대 사용하지 않습니다.
- 사용자가 위기 상황을 암시하면 전문 상담 기관을 안내합니다.
- "참고용 엔터테인먼트 서비스"임을 필요 시 상기시킵니다.

[응답 형식]
- 핵심 해석을 먼저 제시합니다 (2~3문장).
- 명리학적 근거를 설명합니다 (관련 십성/오행/신살 언급).
- 구체적 조언이나 시기 안내를 제공합니다.
- 한자 용어 사용 시 한글 병기합니다 (예: 편재(偏財)).
```

#### 5.3.2 Context Injection Template

```
[사용자 사주 정보]
- 사주: {year_pillar} {month_pillar} {day_pillar} {hour_pillar}
- 일간: {day_stem} ({day_stem_element})
- 오행 분포: 목({wood}) 화({fire}) 토({earth}) 금({metal}) 수({water})
- 격국: {geokguk}
- 주요 신살: {special_stars}

[현재 운세]
- 대운 ({major_luck_period}): {major_luck_stem}{major_luck_branch}
  - 대운 십성: {major_luck_ten_star}
- 세운 (2026년): {yearly_luck_stem}{yearly_luck_branch}
  - 세운 십성: {yearly_luck_ten_star}
- 월운 ({current_month}월): {monthly_luck_stem}{monthly_luck_branch}
- 일운 (오늘): {daily_luck_stem}{daily_luck_branch}

[이전 대화 요약]
{conversation_summary}
```

#### 5.3.3 Topic Router 프롬프트 분기

| 주제 | 추가 프롬프트 지시 |
|------|-------------------|
| **연애운** | 일주 궁합, 도화살/홍염살 여부, 편재/정재(남)/편관/정관(여) 중심 해석. 구체적 만남 시기 안내. |
| **직장운** | 관성(편관/정관), 인성(편인/정인) 중심. 승진/이직 시기, 직업 적성. |
| **재물운** | 재성(편재/정재), 식상생재 여부. 투자 시기, 재물 유형(정재=월급, 편재=투자). |
| **건강운** | 오행 과불급 기반 취약 장기 안내. 단, 의학적 진단은 절대 금지. "참고 수준"으로만. |
| **학업운** | 인성(편인=자격증/독학, 정인=정규교육), 식상(창의력) 중심. 수험 시기 안내. |
| **일반** | 종합 운세, 사주 전체 구조 해석. 핵심 특성과 인생 방향. |

### 5.4 RAG Pipeline 설계

```
┌─────────────────────────────────────────────────────┐
│                  Knowledge Base                      │
│                                                      │
│  ┌────────────────┐  청크 분할 (500자)               │
│  │ 적천수 (원전)   │──────────┐                      │
│  └────────────────┘          │                      │
│  ┌────────────────┐          ▼                      │
│  │ 자평진전 (원전) │──► ┌──────────┐  임베딩         │
│  └────────────────┘    │  Text    │──────────┐      │
│  ┌────────────────┐    │  Chunks  │          │      │
│  │ 궁통보감 (원전) │──► │ (~3000개)│          ▼      │
│  └────────────────┘    └──────────┘  ┌────────────┐ │
│  ┌────────────────┐                  │  pgvector   │ │
│  │ 해석 가이드라인  │──────────────►  │  Embeddings │ │
│  └────────────────┘                  │  Table      │ │
│  ┌────────────────┐                  │             │ │
│  │ 신살/격국 해설  │──────────────►  └────────────┘ │
│  └────────────────┘                                  │
└─────────────────────────────────────────────────────┘

검색 쿼리 구성:
  "{사용자 질문} {관련 십성} {관련 신살} {격국}"
  → 벡터 유사도 검색 (cosine similarity)
  → 상위 5개 청크 추출
  → LLM 프롬프트에 "[참고 지식]" 섹션으로 주입
```

**RAG 품질 관리:**
- 청크 크기: 500자 (한국어 기준), 100자 오버랩
- 메타데이터 필터: 출처(원전명), 주제(십성/신살/격국/운세), 연관 오행
- 리랭킹: 사주 데이터와의 관련성으로 재정렬

### 5.5 응답 스트리밍 (SSE) 구현

```python
# ai_counsel/router.py
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

@router.post("/consultations/{consultation_id}/messages")
async def send_message(
    consultation_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
):
    async def event_generator():
        async for token in counsel_service.generate_response(
            consultation_id=consultation_id,
            user_message=message.content,
            user=current_user,
        ):
            yield {
                "event": "token",
                "data": json.dumps({"token": token})
            }
        yield {
            "event": "done",
            "data": json.dumps({"message_id": saved_message_id})
        }

    return EventSourceResponse(event_generator())
```

### 5.6 콘텐츠 안전성 필터

```python
class SafetyFilter:
    """
    PRD 10.4 Legal & Ethical Guidelines 구현
    """

    # 차단 키워드 패턴
    CRISIS_KEYWORDS = ["자살", "자해", "죽고 싶", "살고 싶지 않"]
    MEDICAL_PATTERNS = [r"약\s*처방", r"진단", r"치료\s*방법"]
    LEGAL_PATTERNS = [r"소송", r"법적\s*조언"]

    async def filter_input(self, user_message: str) -> SafetyCheckResult:
        """사용자 입력 안전성 검사"""
        if self._detect_crisis(user_message):
            return SafetyCheckResult(
                blocked=True,
                response="정신건강위기상담전화 1577-0199로 연락해 주세요..."
            )
        return SafetyCheckResult(blocked=False)

    async def filter_output(self, ai_response: str) -> str:
        """AI 응답 후처리 필터"""
        # 의학/법률 조언 감지 시 면책 조항 추가
        # 과도한 부정적 표현 완화
        # 면책 문구 추가
        return filtered_response
```

---

## 6. Database Architecture

> 상세 스키마는 [DB Schema 문서](../02-design/db-schema.md)를 참조한다.

### 6.1 테이블 개요

| 테이블 | 설명 | 주요 특징 |
|--------|------|-----------|
| `users` | 사용자 계정 | OAuth 연동, 프리미엄 상태 |
| `saju_profiles` | 사주 프로필 | 사용자당 최대 5개, JSONB 사주 데이터 |
| `consultations` | 상담 세션 | 주제별 분류, 상태 관리 |
| `messages` | 상담 메시지 | 사용자/AI 메시지, JSONB 메타데이터 |
| `daily_fortunes` | 일일 운세 | 일일 배치 생성, 캐싱 |
| `payments` | 결제 내역 | Toss Payments 연동 |
| `subscriptions` | 구독 정보 | 월간/연간 구독 관리 |
| `knowledge_chunks` | RAG 지식 베이스 | pgvector 임베딩, 메타데이터 |

### 6.2 JSONB 활용 전략

사주 데이터는 구조가 복잡하고 도메인 지식에 따라 스키마가 진화할 수 있으므로 JSONB로 저장한다.

**장점:**
- 사주 데이터 구조 변경 시 마이그레이션 불필요
- 부분 인덱싱으로 특정 필드 검색 가능 (GIN 인덱스)
- PostgreSQL 16의 JSONB 성능 최적화 활용

**단점 및 대응:**
- 타입 안정성: Pydantic 스키마로 애플리케이션 레벨 검증
- 쿼리 복잡도: 자주 조회하는 필드는 별도 컬럼으로 비정규화 검토

### 6.3 인덱싱 전략

| 인덱스 | 테이블 | 컬럼/표현식 | 이유 |
|--------|--------|-------------|------|
| `idx_users_provider` | users | `(provider, provider_id)` UNIQUE | OAuth 로그인 조회 |
| `idx_profiles_user` | saju_profiles | `(user_id)` | 사용자별 프로필 목록 |
| `idx_profiles_saju_day_stem` | saju_profiles | `((saju_data->>'day_stem'))` | 일간 기준 통계/검색 |
| `idx_consultations_user_date` | consultations | `(user_id, created_at DESC)` | 상담 이력 최신순 조회 |
| `idx_messages_consultation` | messages | `(consultation_id, created_at)` | 상담 메시지 시간순 조회 |
| `idx_daily_fortunes_profile_date` | daily_fortunes | `(profile_id, date)` UNIQUE | 프로필별 일일 운세 조회 |
| `idx_knowledge_embedding` | knowledge_chunks | `embedding vector` (ivfflat) | RAG 벡터 유사도 검색 |

---

## 7. API Design

### 7.1 설계 원칙

| 원칙 | 적용 |
|------|------|
| **RESTful** | 리소스 중심 URL 설계, HTTP 메서드 시맨틱 준수 |
| **Versioning** | URL 경로 버전 (`/api/v1/`) |
| **Pagination** | 커서 기반 페이지네이션 (상담 이력, 메시지 목록) |
| **Consistent Response** | 공통 응답 래퍼 (`{ data, meta, errors }`) |
| **HATEOAS Lite** | 관련 리소스 링크 포함 (선택적) |

### 7.2 공통 응답 형식

```json
// 성공 응답
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-03-25T10:30:00Z"
  }
}

// 목록 응답 (커서 페이지네이션)
{
  "data": [ ... ],
  "meta": {
    "cursor": "eyJpZCI6IjEyMyJ9",
    "has_next": true,
    "total_count": 42
  }
}

// 에러 응답
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
    "request_id": "req_def456",
    "timestamp": "2026-03-25T10:30:00Z"
  }
}
```

### 7.3 API Endpoint 상세 (PRD 7.3 기반)

#### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/login` | OAuth 소셜 로그인 콜백 처리 | No |
| POST | `/api/v1/auth/refresh` | Access Token 갱신 | Refresh Token |
| POST | `/api/v1/auth/logout` | 로그아웃 (토큰 무효화) | Bearer |

#### Saju Profiles

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/profiles` | 사주 프로필 생성 + 사주 산출 | Bearer |
| GET | `/api/v1/profiles` | 내 프로필 목록 | Bearer |
| GET | `/api/v1/profiles/{id}` | 프로필 상세 (사주 데이터 포함) | Bearer |
| DELETE | `/api/v1/profiles/{id}` | 프로필 삭제 | Bearer |
| POST | `/api/v1/profiles/compatibility` | 두 프로필 궁합 분석 | Bearer (Premium) |

#### AI Consultation

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/consultations` | 새 상담 세션 생성 | Bearer |
| GET | `/api/v1/consultations` | 상담 이력 목록 (cursor pagination) | Bearer |
| GET | `/api/v1/consultations/{id}` | 상담 상세 + 메시지 목록 | Bearer |
| POST | `/api/v1/consultations/{id}/messages` | 메시지 전송 + SSE 스트리밍 응답 | Bearer |

#### Fortune Content

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/fortunes/daily` | 오늘의 운세 | Bearer |
| GET | `/api/v1/fortunes/monthly` | 월간 운세 | Bearer (Premium) |
| GET | `/api/v1/fortunes/yearly` | 연간 운세 | Bearer (Premium) |
| GET | `/api/v1/fortunes/calendar` | 길일 캘린더 | Bearer (Premium) |

#### Payments

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/payments/subscribe` | 구독 결제 시작 | Bearer |
| POST | `/api/v1/payments/one-time` | 건별 결제 | Bearer |
| GET | `/api/v1/payments/history` | 결제 이력 | Bearer |
| POST | `/api/v1/payments/webhook` | Toss Payments 웹훅 | Webhook Signature |

#### Share

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/share/card` | 공유 카드 이미지 생성 | Bearer |

### 7.4 Rate Limiting 전략

| 사용자 유형 | 제한 | 구현 |
|-------------|------|------|
| 비인증 | 100 req/hour (IP 기반) | API Gateway |
| Free 사용자 | 500 req/hour + 일 3회 상담 | Redis (sliding window) |
| Premium 사용자 | 2000 req/hour + 무제한 상담 | Redis (sliding window) |
| AI 상담 | 분당 5회 (burst 방지) | Redis (token bucket) |

```python
# Rate Limiting 미들웨어 (Redis 기반)
class RateLimiter:
    async def check_consultation_limit(self, user_id: str) -> bool:
        key = f"consult_daily:{user_id}:{today()}"
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, seconds_until_midnight())
        return count <= self.daily_limit  # Free: 3, Premium: unlimited
```

### 7.5 에러 코드 체계

| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| `AUTH_INVALID_TOKEN` | 401 | JWT 유효하지 않음 |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT 만료 |
| `PROFILE_LIMIT_EXCEEDED` | 403 | 프로필 5개 초과 |
| `CONSULTATION_LIMIT_EXCEEDED` | 429 | 일일 상담 횟수 초과 |
| `RATE_LIMIT_EXCEEDED` | 429 | API Rate Limit 초과 |
| `SAJU_CALCULATION_ERROR` | 422 | 사주 산출 오류 (입력 검증 실패) |
| `LLM_UNAVAILABLE` | 503 | LLM API 일시 불가 |
| `PAYMENT_FAILED` | 402 | 결제 실패 |

---

## 8. Authentication & Authorization

### 8.1 인증 흐름 (OAuth 2.0 + JWT)

```
┌────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────┐
│ Client │     │ OAuth   │     │  Auth Module  │     │   DB     │
│(Next.js)│     │Provider │     │  (FastAPI)    │     │          │
└───┬────┘     └────┬────┘     └──────┬───────┘     └────┬─────┘
    │               │                 │                   │
    │  1. 로그인 클릭│                 │                   │
    │──────────────►│                 │                   │
    │               │                 │                   │
    │  2. OAuth 인증│                 │                   │
    │◄──────────────│                 │                   │
    │  (auth code)  │                 │                   │
    │               │                 │                   │
    │  3. POST /auth/login            │                   │
    │    { provider, code }           │                   │
    │────────────────────────────────►│                   │
    │               │                 │                   │
    │               │  4. 토큰 교환    │                   │
    │               │◄────────────────│                   │
    │               │  (access_token) │                   │
    │               │────────────────►│                   │
    │               │ (user_info)     │                   │
    │               │                 │                   │
    │               │                 │  5. 사용자 조회/생성│
    │               │                 │──────────────────►│
    │               │                 │◄──────────────────│
    │               │                 │                   │
    │  6. JWT 발급                    │                   │
    │  { access_token, refresh_token }│                   │
    │◄────────────────────────────────│                   │
    │               │                 │                   │
```

### 8.2 JWT 구조

```json
// Access Token (만료: 1시간)
{
  "sub": "user_uuid",
  "type": "access",
  "is_premium": true,
  "premium_until": "2026-12-31T23:59:59Z",
  "iat": 1711350600,
  "exp": 1711354200
}

// Refresh Token (만료: 30일, Redis 저장)
{
  "sub": "user_uuid",
  "type": "refresh",
  "jti": "unique_token_id",
  "iat": 1711350600,
  "exp": 1713942600
}
```

### 8.3 인가 정책

| 리소스 | Free | Premium | 구현 |
|--------|------|---------|------|
| 사주 프로필 생성 | 1개 (MVP) / 5개 (v1.0) | 5개 | DB count 체크 |
| AI 상담 | 일 3회 | 무제한 | Redis 카운터 |
| 오늘의 운세 | O | O | - |
| 월간/연간 운세 | X | O | JWT is_premium 체크 |
| 궁합 분석 | X | O | JWT is_premium 체크 |
| 길일 캘린더 | X | O | JWT is_premium 체크 |

---

## 9. Infrastructure & Deployment

### 9.1 AWS 인프라 구성

```
                    ┌─────────────────────────────────────┐
                    │           AWS Cloud (ap-northeast-2) │
                    │                                      │
   Internet ──────►│  ┌──────────────┐                    │
                    │  │  CloudFront  │  ← Next.js Static  │
                    │  └──────┬───────┘                    │
                    │         │                            │
                    │  ┌──────▼───────┐                    │
                    │  │ API Gateway  │  ← WAF             │
                    │  └──────┬───────┘                    │
                    │         │                            │
                    │  ┌──────▼───────────────────┐       │
                    │  │      VPC                  │       │
                    │  │                           │       │
                    │  │  ┌─── Public Subnet ───┐  │       │
                    │  │  │  ALB (Internal)     │  │       │
                    │  │  └────────┬────────────┘  │       │
                    │  │           │                │       │
                    │  │  ┌─── Private Subnet ──┐  │       │
                    │  │  │                     │  │       │
                    │  │  │  ECS Fargate        │  │       │
                    │  │  │  ┌──────┐ ┌──────┐  │  │       │
                    │  │  │  │Task 1│ │Task 2│  │  │       │
                    │  │  │  │ API  │ │ API  │  │  │       │
                    │  │  │  └──────┘ └──────┘  │  │       │
                    │  │  │                     │  │       │
                    │  │  │  ┌──────┐            │  │       │
                    │  │  │  │Worker│ (Celery)   │  │       │
                    │  │  │  └──────┘            │  │       │
                    │  │  └─────────────────────┘  │       │
                    │  │                           │       │
                    │  │  ┌─── Data Subnet ─────┐  │       │
                    │  │  │  RDS PostgreSQL 16   │  │       │
                    │  │  │  ElastiCache Redis 7 │  │       │
                    │  │  └─────────────────────┘  │       │
                    │  └───────────────────────────┘       │
                    │                                      │
                    │  S3 (공유 카드, 정적 자산)             │
                    │  ECR (Docker 이미지)                   │
                    │  Secrets Manager (API 키, DB 비밀번호)  │
                    │  CloudWatch (로그, 메트릭, 알림)        │
                    └─────────────────────────────────────┘
```

### 9.2 리소스 스펙 (PRD 6.5 기반)

| 리소스 | MVP | v1.0 | 비용 (월, 추정) |
|--------|-----|------|----------------|
| ECS Fargate (API) | 2 tasks (0.5 vCPU, 1GB) | 4 tasks (1 vCPU, 2GB) + Auto Scaling | 15~60만원 |
| ECS Fargate (Worker) | 1 task (0.25 vCPU, 0.5GB) | 2 tasks | 5~15만원 |
| RDS PostgreSQL | db.t3.medium (2 vCPU, 4GB) | db.r6g.large + Read Replica | 20~80만원 |
| ElastiCache Redis | cache.t3.micro (0.5GB) | cache.r6g.large (13GB) | 5~30만원 |
| CloudFront | 기본 | 기본 + Edge Caching | 5~10만원 |
| S3 | Standard | Standard + Lifecycle | 1~5만원 |
| API Gateway | 기본 | 기본 | 5~10만원 |
| **LLM API** | **Pay-per-use** | **Multi-provider** | **200~300만원** |
| **합계** | | | **~350만원 (MVP)** |

LLM API 비용이 전체 인프라 비용의 60~70%를 차지하므로, 프롬프트 토큰 최적화와 캐싱이 비용 관리의 핵심이다.

### 9.3 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/deploy.yml (요약)
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    # Python 테스트 (pytest)
    # 사주 산출 정확도 테스트 (1000+ 케이스)
    # API 통합 테스트

  build:
    # Docker 이미지 빌드
    # ECR 푸시

  deploy-staging:
    # ECS Staging 배포
    # Smoke 테스트

  deploy-production:
    # ECS Production Blue/Green 배포
    # 헬스체크 확인
    # 롤백 자동화
```

### 9.4 배포 전략

| 환경 | 전략 | 설명 |
|------|------|------|
| Staging | Rolling Update | 빠른 배포, QA 검증 |
| Production | Blue/Green (ECS) | 무중단 배포, 즉시 롤백 가능 |

---

## 10. Scalability Strategy

### 10.1 MVP -> v1.0 -> Scale 확장 계획

```
MVP (DAU 1,000)          v1.0 (DAU 10,000)       Scale (DAU 100,000+)
──────────────────────────────────────────────────────────────────────
ECS 2 tasks              ECS 4+ tasks (Auto)      ECS 20+ tasks
RDS Single               RDS + Read Replica        RDS Multi-AZ + 다중 Replica
Redis micro              Redis large               Redis Cluster
단일 LLM                 Multi-LLM (Fallback)     LLM 로드밸런싱 + 캐싱
pgvector                 pgvector                   전용 Vector DB 검토
Modular Monolith         Modular Monolith          MSA 분리 검토
```

### 10.2 캐싱 전략

| 캐시 대상 | TTL | 키 패턴 | 효과 |
|-----------|-----|---------|------|
| 오늘의 운세 | 24시간 (자정 갱신) | `fortune:daily:{profile_id}:{date}` | DB 조회 제거, 가장 빈번한 요청 |
| 사주 프로필 데이터 | 1시간 | `profile:{profile_id}` | 상담 시 매번 DB 조회 방지 |
| JWT 블랙리스트 | 토큰 만료시까지 | `jwt_blacklist:{jti}` | 로그아웃 처리 |
| Rate Limit 카운터 | 자정까지/1시간 | `ratelimit:{user_id}:{window}` | 상담 횟수 제한 |
| LLM 응답 (동일 사주+동일 질문) | 6시간 | `llm_cache:{hash(context+query)}` | LLM API 비용 절감 |
| 만세력 데이터 | 영구 (서버 메모리) | 인메모리 dict | 사주 산출 속도 최적화 |

**오늘의 운세 캐싱 흐름:**

```
사용자 요청 (GET /fortunes/daily)
    │
    ▼
Redis 캐시 확인 ──── HIT ──── 즉시 응답 (< 10ms)
    │
    MISS
    │
    ▼
DB 조회 (daily_fortunes 테이블)
    │
    ├── 존재 ──── Redis 캐시 저장 + 응답
    │
    └── 없음 ──── 배치 미생성 (자정 배치 스케줄)
                   → 실시간 생성 (Fallback) + DB/Redis 저장
```

### 10.3 CDN 활용

| 콘텐츠 | CDN 캐싱 | TTL |
|--------|----------|-----|
| Next.js 정적 자산 (JS, CSS, 이미지) | CloudFront | 1년 (hash-based) |
| 공유 카드 이미지 (S3) | CloudFront | 30일 |
| 폰트 (Pretendard, Noto Serif KR) | CloudFront | 1년 |
| API 응답 | 캐싱 안 함 | - |

---

## 11. Security Architecture

### 11.1 보안 레이어

```
┌─── Layer 1: Network ────────────────────────────────┐
│  WAF (AWS WAF): SQL Injection, XSS, Bot Protection  │
│  VPC: Private Subnet (API, DB), Public Subnet (ALB)  │
│  Security Groups: 최소 권한 원칙                      │
└─────────────────────────────────────────────────────┘

┌─── Layer 2: Application ────────────────────────────┐
│  JWT 인증, OAuth 2.0                                 │
│  Rate Limiting (API Gateway + Redis)                 │
│  CORS: 허용된 도메인만                               │
│  Input Validation (Pydantic)                         │
│  CSRF 보호 (SameSite Cookie)                         │
└─────────────────────────────────────────────────────┘

┌─── Layer 3: Data ───────────────────────────────────┐
│  생년월일시 AES-256 암호화 저장 (PRD 5.6)             │
│  DB 연결 TLS 암호화                                  │
│  Secrets Manager (API 키, DB 비밀번호)                │
│  상담 내역 90일 후 익명화 옵션 (PRD 10.4)             │
└─────────────────────────────────────────────────────┘
```

### 11.2 개인정보 보호 (PIPA 준수)

| 항목 | 조치 |
|------|------|
| 생년월일시 | AES-256-GCM 암호화 저장, 복호화는 사주 산출 시에만 |
| 상담 내역 | 90일 후 자동 익명화 옵션 제공 |
| 소셜 로그인 | 최소 정보만 수집 (email, nickname) |
| 데이터 삭제 | 회원 탈퇴 시 30일 유예 후 완전 삭제 |
| 로그 | 개인정보 마스킹 처리 후 저장 |

### 11.3 LLM 보안

| 위협 | 대응 |
|------|------|
| 프롬프트 인젝션 | 시스템 프롬프트와 사용자 입력 분리, 입력 sanitize |
| 데이터 유출 | 다른 사용자의 사주 데이터가 컨텍스트에 포함되지 않도록 격리 |
| 유해 콘텐츠 생성 | Safety Filter + LLM 자체 가드레일 |

---

## 12. Monitoring & Observability

### 12.1 모니터링 스택

| 도구 | 용도 |
|------|------|
| **AWS CloudWatch** | 인프라 메트릭 (CPU, Memory, Network), 로그 집계 |
| **Datadog APM** | 애플리케이션 성능 모니터링, 분산 트레이싱 |
| **Sentry** | 에러 트래킹, 실시간 알림 |
| **Custom Dashboard** | 비즈니스 메트릭 (DAU, 상담 완료율, CSAT) |

### 12.2 핵심 메트릭 (PRD 3.2 KPI 기반)

| 메트릭 | 목표 | 알림 기준 |
|--------|------|-----------|
| API 응답 시간 (p95) | < 500ms (일반), < 3초 (AI 상담) | p95 > 5초 시 알림 |
| 사주 산출 시간 | < 500ms | > 1초 시 알림 |
| LLM 첫 토큰 시간 | < 1.5초 | > 3초 시 알림 |
| 서비스 가용성 | >= 99.5% | 5분간 에러율 > 5% 시 알림 |
| LLM API 에러율 | < 1% | > 5% 시 알림 (자동 폴백 트리거) |
| 일일 LLM API 비용 | < 10만원 (MVP) | 일일 한도 80% 도달 시 알림 |

### 12.3 로깅 전략

```python
# 구조화 로그 형식
{
    "timestamp": "2026-03-25T10:30:00Z",
    "level": "INFO",
    "service": "ai_counsel",
    "request_id": "req_abc123",
    "user_id": "usr_***masked***",
    "action": "consultation_message",
    "metadata": {
        "consultation_id": "cons_xyz",
        "topic": "재물",
        "llm_provider": "claude",
        "input_tokens": 2500,
        "output_tokens": 800,
        "latency_ms": 2340
    }
}
```

---

## Appendix A: Technology Decision Records (ADR)

### ADR-001: Modular Monolith over Microservices

- **Status:** Accepted
- **Context:** 7명 팀, 8주 MVP 일정, 월 500만원 인프라 예산
- **Decision:** Modular Monolith
- **Consequences:** 빠른 개발, 낮은 운영 비용. 향후 MSA 전환 비용 발생 가능.

### ADR-002: pgvector over Pinecone

- **Status:** Accepted
- **Context:** 명리학 지식 베이스 ~3,000 문서, 비용 제약
- **Decision:** pgvector (PostgreSQL 확장)
- **Consequences:** 인프라 단순화, 비용 절감. 대규모 확장 시 전용 Vector DB로 전환 검토.

### ADR-003: Claude API as Primary LLM

- **Status:** Accepted
- **Context:** 한국어 명리학 해석 품질, 긴 컨텍스트 윈도우 필요
- **Decision:** Claude API (Primary) + GPT-4o (Fallback)
- **Consequences:** 우수한 한국어 성능, 높은 가용성. 프롬프트 양 프로바이더 호환 필요.

### ADR-004: FastAPI over Django

- **Status:** Accepted
- **Context:** SSE 스트리밍 핵심, AI/ML 라이브러리 연동, 비동기 처리 필요
- **Decision:** FastAPI
- **Consequences:** 네이티브 async/SSE, 빠른 개발. Django 대비 내장 Admin, Auth 부재로 직접 구현 필요.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-25 | CTO Lead | Initial architecture design based on PRD v1.0 |
