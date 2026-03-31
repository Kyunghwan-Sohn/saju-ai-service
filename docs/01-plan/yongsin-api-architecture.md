# YongSin API 기반 사주 AI 서비스 - 기술 아키텍처 재설계

> **Version:** 3.0 (YongSin API Pivot)
> **Date:** 2026-03-28
> **Author:** CTO Lead
> **Status:** Draft - Checkpoint 1 (요구사항 확인 대기)
> **Supersedes:** v2.0 DB-First + abcllm 배치 방식, v1.0 자체 엔진 + 실시간 LLM 방식

---

## 목차

1. [Executive Summary: 왜 YongSin API인가](#1-executive-summary)
2. [기존 서비스 대비 기술적 차별점](#2-기술적-차별점)
3. [신규 기술 아키텍처](#3-신규-기술-아키텍처)
4. [데이터 전략](#4-데이터-전략)
5. [AI 활용 전략](#5-ai-활용-전략)
6. [리스크 관리](#6-리스크-관리)
7. [PDCA 개발 로드맵](#7-pdca-개발-로드맵)
8. [기술 결정 기록 (ADR)](#8-기술-결정-기록)

---

## 1. Executive Summary

### 1.1 핵심 전환: 자체 엔진에서 전문 API로

```
[v1.0] 자체 engine.ts (간지 계산만)
  - 연주/월주/일주/시주 기본 계산
  - 절기 경계를 하드코딩 (2/4, 3/6, ... 고정일)
  - 지장간 없음, 신살 없음, 용신 없음, 대운 없음
  - 오행 분포: 천간/지지 표면 글자만 카운트
  - 시주 계산 오차 존재

[v2.0] DB-First + abcllm 배치 (현 문서 기준 폐기)
  - 여전히 자체 사주 계산 엔진 사용 계획
  - 518,400개 사주 조합 사전 생성 → 비현실적 규모
  - abcllm 배치 비용 예측 불가

[v3.0] YongSin API 기반 (본 문서)
  - 사주 계산의 정밀도를 외부 전문 API에 위임
  - 지장간/신살/용신/대운/공망/간지상호작용 모두 확보
  - LLM은 "해석의 품질"에만 집중 (계산 정확도 문제 해소)
  - 콘텐츠 생성 비용 최적화 (필요한 사주만 on-demand)
```

### 1.2 근본적인 관점 전환

| 관점 | 기존 (v1.0/v2.0) | 신규 (v3.0 YongSin) |
|------|-------------------|---------------------|
| **사주 계산** | 자체 구현 (불완전) | YongSin API (전문/정밀) |
| **데이터 깊이** | 표면 4기둥 + 기초 오행 | 4기둥 + 지장간 + 십신 + 용신 + 신살 + 대운 + 상호작용 |
| **해석 근거** | 일간(10종류) 기준 템플릿 | 원국 전체 구조 기반 맥락적 해석 |
| **콘텐츠 전략** | 518,400개 사전 생성 시도 | on-demand + 결과 캐싱 |
| **LLM 역할** | 배치 콘텐츠 생성기 | 원국 데이터 기반 실시간 해석 전문가 |
| **운세 정밀도** | 일간 10종류별 일반론 | target_year 기반 개인화된 세운/대운 분석 |
| **궁합 분석** | 일간 x 일간 (100조합) | 두 원국 전체 비교 (합/충/형 포함) |

---

## 2. 기술적 차별점

### 2.1 자체 엔진의 한계 (현재 engine.ts 분석)

현재 `next-app/src/lib/saju/engine.ts` 분석 결과:

```
1. 절기 경계 하드코딩
   - getMonthBranch()에서 "2월 4일", "3월 6일" 등 고정일 사용
   - 실제 절기는 매년 시간이 다름 (예: 입춘이 2/3 23:59일 수 있음)
   - → YongSin: 절기 시간 정밀 계산

2. 시주 계산 단순화
   - 2시간 단위 단순 구간 분할
   - 야자시/조자시 미구분 (23:00~01:00을 하나로 처리)
   - → YongSin: 야자시/조자시 정밀 구분

3. 오행 분석 부재
   - 천간/지지 표면 오행만 카운트 (8개 글자의 오행)
   - 지장간 속 숨은 오행 미반영
   - → YongSin: 지장간 비율 포함 정밀 오행 분포 (wuxing)

4. 핵심 분석 요소 전무
   - 십신(十神): 미구현 → YongSin: ten_gods (기둥별 십신)
   - 용신(用神): 미구현 → YongSin: yongsin_analysis (신뢰도 포함)
   - 신살(神殺): 미구현 → YongSin: sinsal (화개살, 지살, 역마살 등)
   - 대운(大運): 미구현 → YongSin: daeun_periods (10년 단위)
   - 간지 상호작용: 미구현 → YongSin: interactions (합/충/형/파/해)
   - 공망(空亡): 미구현 → YongSin: gongmang
```

### 2.2 YongSin API로 달라지는 것

#### A. 사주 원국 (Layer 1-3) - 계산 정밀도

```
[기존] BirthData → engine.ts → Pillars(4기둥) + 기초 오행
       - 해석 가능 범위: "갑목 일간이므로..."

[YongSin] BirthData → YongSin API → 완전한 원국(原局)
         ├── four_pillars: 연주/월주/일주/시주 (정밀 절기)
         ├── hidden_stems: 지장간 (각 지지 속 숨은 천간 + 비율)
         ├── ten_gods: 십신 (기둥별 관계)
         ├── wuxing: 오행 분포 (지장간 비율 포함)
         ├── yongsin_analysis: 용신 + 신뢰도
         ├── sinsal: 신살 목록
         ├── daeun_periods: 대운 주기
         ├── interactions: 합/충/형/파/해
         └── gongmang: 공망
         - 해석 가능 범위: "갑목 일간에 월지 인목의 지장간 갑병무가
           비겁과 식상을 형성하고, 용신이 금(金)이므로..."
```

#### B. 운세 분석 (Layer 4) - 시간축 분석

```
[기존] 일간 10종류별 고정 텍스트 (gap_daily, eul_daily...)
       - 동일 일간이면 전부 같은 운세

[YongSin Layer 4] 원국 + target_year → 개인화 세운 분석
         ├── 대운 vs 세운 간지 상호작용
         ├── 올해 용신 활성/비활성 판단
         ├── 월별 길흉 변화 예측
         └── 특이 신살 발동 시기
         - "2026년 병오(丙午)년은 당신의 용신인 화(火)가 강해지는 해..."
```

#### C. 궁합 분석 (Layer 5) - 구조적 비교

```
[기존] 일간 x 일간 = 100조합의 사전 텍스트
       - 같은 일간쌍이면 전부 같은 궁합

[YongSin Layer 5] 두 원국 전체 비교
         ├── 오행 상보성 분석
         ├── 간지 합/충 관계 (일간합, 지지삼합 등)
         ├── 용신 상호 보완 여부
         ├── 십신 궁합도
         └── 구체적 주의사항
         - "두 분의 일간이 갑기합토(甲己合土)를 이루어 자연스러운 끌림이..."
```

### 2.3 데이터 심도 비교표

| 분석 요소 | 기존 engine.ts | YongSin API | 해석 영향도 |
|-----------|---------------|-------------|------------|
| 4기둥 계산 | O (오차 있음) | O (정밀) | 기본 |
| 지장간 | X | O (비율 포함) | 높음 - 숨은 역량 분석 |
| 십신 | X | O (기둥별) | 매우 높음 - 관계/직업/재물 |
| 오행 분포 | 표면적 | 지장간 포함 정밀 | 높음 - 균형/불균형 판단 |
| 용신 | X | O (신뢰도 포함) | 최고 - 핵심 처방 근거 |
| 신살 | X | O (화개살,역마살...) | 중간 - 부가 통찰 |
| 대운 | X | O (10년 단위) | 매우 높음 - 인생 흐름 |
| 간지 상호작용 | X | O (합/충/형/파/해) | 높음 - 원국 역학 |
| 공망 | X | O | 중간 - 공허 시기 |
| 세운 분석 | X (고정 텍스트) | O (target_year) | 매우 높음 - 연간 운세 |
| 궁합 비교 | 일간 매칭만 | 원국 전체 비교 | 매우 높음 |

---

## 3. 신규 기술 아키텍처

### 3.1 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  Next.js 15 (App Router)                                     │  │
│   │  ├── Zustand (상태 관리: 사주 데이터 + UI 상태)               │  │
│   │  ├── Tailwind CSS + shadcn/ui                                │  │
│   │  ├── React Query (서버 상태 관리 + 캐싱)                      │  │
│   │  └── next-intl (한국어/베트남어 다국어)                        │  │
│   └──────────────────────────────────────────────────────────────┘  │
│            │ HTTPS                                                   │
└────────────┼─────────────────────────────────────────────────────────┘
             │
┌────────────▼─────────────────────────────────────────────────────────┐
│                          API LAYER (Next.js API Routes)               │
│                                                                       │
│   ┌───────────────────────────────────────────────────────────────┐  │
│   │  /api/v1/                                                      │  │
│   │  ├── saju/analyze     → YongSin Layer 1-3 호출 + 캐시         │  │
│   │  ├── saju/fortune     → YongSin Layer 4 호출 (세운 분석)       │  │
│   │  ├── saju/compat      → YongSin Layer 5 호출 (궁합)           │  │
│   │  ├── saju/calendar    → YongSin Layer 6 호출 (택일)           │  │
│   │  ├── ai/interpret     → LLM 해석 생성 (원국 데이터 기반)       │  │
│   │  ├── ai/chat          → 대화형 AI 상담 (SSE 스트리밍)          │  │
│   │  ├── ai/topic/[id]    → 토픽별 심층 분석                       │  │
│   │  ├── auth/[...flow]   → 인증 (카카오 OAuth)                    │  │
│   │  └── user/[...crud]   → 사용자 프로필 관리                      │  │
│   └───────────────────────────────────────────────────────────────┘  │
│            │                    │                    │                │
│     ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐        │
│     │  YongSin    │     │  LLM        │     │  Supabase   │        │
│     │  Gateway    │     │  Gateway    │     │  Client     │        │
│     │             │     │             │     │             │        │
│     │ - API 호출  │     │ - Claude/   │     │ - Auth      │        │
│     │ - 응답 정규화│    │   GPT-4o    │     │ - DB        │        │
│     │ - 에러 처리 │     │ - 프롬프트  │     │ - Storage   │        │
│     │ - 요금 추적 │     │   관리      │     │ - Realtime  │        │
│     └──────┬──────┘     │ - 스트리밍  │     └──────┬──────┘        │
│            │            │ - 안전 필터 │            │                │
│            │            └──────┬──────┘            │                │
└────────────┼───────────────────┼───────────────────┼────────────────┘
             │                   │                   │
     ┌───────▼───────┐  ┌──────▼──────┐    ┌───────▼───────┐
     │  YongSin API  │  │  LLM APIs   │    │  Supabase     │
     │  (외부)        │  │  (외부)      │    │  (PaaS)       │
     │               │  │             │    │               │
     │  Layer 1-3:   │  │  Claude 4   │    │  PostgreSQL   │
     │   원국 계산    │  │  GPT-4o     │    │  Auth         │
     │  Layer 4:     │  │  (fallback) │    │  Storage      │
     │   세운 분석    │  │             │    │  Edge Func    │
     │  Layer 5:     │  └─────────────┘    │  Realtime     │
     │   궁합 분석    │                     └───────────────┘
     │  Layer 6:     │
     │   택일        │
     └───────────────┘
```

### 3.2 아키텍처 결정: Next.js Fullstack (FastAPI 대체)

**결정: Next.js API Routes를 백엔드로 사용 (별도 FastAPI 서버 불필요)**

| 비교 항목 | FastAPI 별도 서버 (기존 설계) | Next.js API Routes (신규) |
|-----------|-------------------------------|---------------------------|
| 배포 복잡도 | 프론트 + 백엔드 2개 | 단일 배포 (Vercel) |
| 인프라 비용 | ECS Fargate + RDS + Redis | Vercel Pro + Supabase Free/Pro |
| 사주 계산 | 자체 Python 엔진 필요 | YongSin API 호출만 하면 됨 |
| DB | 자체 PostgreSQL 운영 | Supabase 관리형 PostgreSQL |
| 인증 | 자체 JWT 구현 | Supabase Auth (카카오 OAuth) |
| 개발 속도 | 프론트/백 별도 개발 | 풀스택 단일 코드베이스 |
| 캐싱 | 자체 Redis 운영 | Vercel Edge Cache + React Query |
| MVP 속도 | 인프라 2-3주 | 즉시 개발 시작 |
| 확장성 | 높음 (장기적) | 충분 (MAU 10만까지) |

**근거**: 핵심 사주 계산을 YongSin API에 위임하면, Python 기반 자체 엔진이 불필요해지므로
FastAPI의 가장 큰 존재 이유가 사라진다. Next.js API Routes로 충분히 처리 가능하며,
Vercel + Supabase 조합으로 인프라 운영 부담을 최소화한다.

### 3.3 핵심 모듈 설계

```
next-app/
├── src/
│   ├── app/
│   │   ├── [locale]/                    # 다국어 라우팅 (ko/vi)
│   │   │   ├── page.tsx                 # 랜딩 / 홈
│   │   │   ├── input/page.tsx           # 사주 입력 폼
│   │   │   ├── result/[id]/page.tsx     # 사주 분석 결과 (YongSin 기반)
│   │   │   ├── fortune/
│   │   │   │   ├── daily/page.tsx       # 오늘의 운세
│   │   │   │   ├── monthly/page.tsx     # 월간 운세
│   │   │   │   └── yearly/page.tsx      # 연간 운세 (세운 분석)
│   │   │   ├── compat/page.tsx          # 궁합 분석
│   │   │   ├── topic/[id]/page.tsx      # 토픽별 심층 분석
│   │   │   ├── chat/page.tsx            # AI 대화 상담
│   │   │   ├── calendar/page.tsx        # 택일 캘린더 (NEW)
│   │   │   └── my/page.tsx              # 마이페이지
│   │   │
│   │   └── api/v1/                      # API Routes (Backend)
│   │       ├── saju/
│   │       │   ├── analyze/route.ts     # POST: YongSin 원국 분석
│   │       │   ├── fortune/route.ts     # POST: 세운/대운 분석
│   │       │   ├── compat/route.ts      # POST: 궁합 분석
│   │       │   └── calendar/route.ts    # POST: 택일 분석
│   │       ├── ai/
│   │       │   ├── interpret/route.ts   # POST: LLM 기반 해석 생성
│   │       │   ├── chat/route.ts        # POST: 대화형 상담 (SSE)
│   │       │   └── topic/[id]/route.ts  # POST: 토픽별 분석
│   │       ├── auth/
│   │       │   └── [...flow]/route.ts   # 카카오 OAuth 콜백
│   │       └── user/
│   │           ├── profile/route.ts     # 프로필 CRUD
│   │           └── history/route.ts     # 상담/분석 이력
│   │
│   ├── lib/
│   │   ├── yongsin/                     # ★ YongSin API Gateway
│   │   │   ├── client.ts               # API 클라이언트 (인증, 에러 처리)
│   │   │   ├── types.ts                # API 응답 타입 정의
│   │   │   ├── mapper.ts               # API 응답 → 내부 도메인 모델 변환
│   │   │   ├── cache.ts                # 결과 캐싱 전략
│   │   │   └── cost-tracker.ts         # API 호출 비용 추적
│   │   │
│   │   ├── ai/                          # ★ LLM 해석 엔진
│   │   │   ├── llm-gateway.ts          # Claude/GPT-4o 멀티프로바이더
│   │   │   ├── prompt-builder.ts       # 원국 데이터 → 프롬프트 조합
│   │   │   ├── prompt-templates/       # 프롬프트 템플릿 모음
│   │   │   │   ├── system.ts           # 시스템 프롬프트 (명리학 전문가)
│   │   │   │   ├── interpret.ts        # 종합 사주 풀이
│   │   │   │   ├── fortune.ts          # 운세 분석 (일/월/년)
│   │   │   │   ├── compat.ts           # 궁합 분석
│   │   │   │   ├── topic-love.ts       # 연애운 심층
│   │   │   │   ├── topic-career.ts     # 직업운 심층
│   │   │   │   ├── topic-money.ts      # 재물운 심층
│   │   │   │   └── topic-self.ts       # 자기관리 심층
│   │   │   ├── safety-filter.ts        # 안전성 필터
│   │   │   └── stream-handler.ts       # SSE 스트리밍 처리
│   │   │
│   │   ├── saju/                        # 기존 모듈 (축소)
│   │   │   ├── constants.ts            # 천간/지지/오행 상수 (UI 표시용)
│   │   │   ├── types.ts                # 타입 정의 (YongSin 통합)
│   │   │   └── display-helpers.ts      # UI 표시 유틸리티
│   │   │
│   │   ├── supabase.ts                 # Supabase 클라이언트
│   │   ├── products.ts                 # 제품 정의 (total/yearly/compat/daily)
│   │   └── i18n/                       # 다국어
│   │
│   ├── stores/
│   │   ├── saju-store.ts               # 사주 데이터 상태 (확장)
│   │   └── ui-store.ts                 # UI 상태
│   │
│   └── components/
│       ├── saju/
│       │   ├── PillarDisplay.tsx        # 4기둥 표시 (지장간 추가)
│       │   ├── HiddenStemsBar.tsx       # ★ 지장간 비율 시각화 (NEW)
│       │   ├── TenGodsChart.tsx         # ★ 십신 관계도 (NEW)
│       │   ├── WuxingRadar.tsx          # ★ 오행 레이더 차트 (NEW)
│       │   ├── YongsinBadge.tsx         # ★ 용신 표시 배지 (NEW)
│       │   ├── SinsalList.tsx           # ★ 신살 목록 (NEW)
│       │   ├── DaeunTimeline.tsx        # ★ 대운 타임라인 (NEW)
│       │   └── InteractionsMap.tsx      # ★ 합/충/형 관계도 (NEW)
│       ├── fortune/
│       │   ├── FortuneCard.tsx          # 운세 카드
│       │   └── YearlyForecast.tsx       # ★ 세운 기반 연간 예측 (NEW)
│       ├── compat/
│       │   ├── CompatResult.tsx         # 궁합 결과
│       │   └── CompatDeepDive.tsx       # ★ 원국 비교 상세 (NEW)
│       ├── ai/
│       │   ├── ChatInterface.tsx        # AI 상담 채팅
│       │   └── TopicAnalysis.tsx        # 토픽별 분석 결과
│       └── ui/                          # 공통 UI 컴포넌트
```

### 3.4 YongSin API Gateway 설계

```typescript
// lib/yongsin/client.ts (핵심 설계)

interface YongSinConfig {
  baseUrl: string;
  apiKey: string;
  timeout: number;        // 기본 10초
  retryCount: number;     // 기본 2회
  retryDelay: number;     // 기본 1초
}

interface AnalyzeRequest {
  birth_year: number;
  birth_month: number;
  birth_day: number;
  birth_hour?: number;
  birth_minute?: number;
  gender: 'male' | 'female';
  is_lunar?: boolean;
  is_leap_month?: boolean;
}

interface FortuneRequest extends AnalyzeRequest {
  target_year: number;
  target_month?: number;
}

interface CompatRequest {
  person_a: AnalyzeRequest;
  person_b: AnalyzeRequest;
}

class YongSinClient {
  // Layer 1-3: 원국 분석 (사주팔자 + 지장간 + 십신 + 오행 + 용신 + 신살 + 대운)
  async analyzeWonguk(req: AnalyzeRequest): Promise<WongukResult>

  // Layer 4: 운세 분석 (세운/월운/일운)
  async analyzeFortune(req: FortuneRequest): Promise<FortuneAnalysis>

  // Layer 5: 궁합 분석
  async analyzeCompat(req: CompatRequest): Promise<CompatAnalysis>

  // Layer 6: 택일 분석
  async analyzeCalendar(req: CalendarRequest): Promise<CalendarResult>
}
```

### 3.5 요청 흐름 (Sequence)

#### 흐름 A: 종합 사주 분석 (신규 사용자)

```
Client                  API Route              YongSin          LLM           Supabase
  │                        │                      │              │               │
  │  POST /api/v1/saju/    │                      │              │               │
  │  analyze               │                      │              │               │
  │  {birth_data}          │                      │              │               │
  │───────────────────────>│                      │              │               │
  │                        │                      │              │               │
  │                        │  캐시 확인 (hash)     │              │               │
  │                        │─────────────────────────────────────────────────────>│
  │                        │  캐시 MISS           │              │               │
  │                        │<─────────────────────────────────────────────────────│
  │                        │                      │              │               │
  │                        │  Layer 1-3 호출       │              │               │
  │                        │─────────────────────>│              │               │
  │                        │  원국 데이터 반환      │              │               │
  │                        │<─────────────────────│              │               │
  │                        │                      │              │               │
  │                        │  원국 캐시 저장        │              │               │
  │                        │─────────────────────────────────────────────────────>│
  │                        │                      │              │               │
  │  원국 데이터 (즉시)     │                      │              │               │
  │<───────────────────────│                      │              │               │
  │                        │                      │              │               │
  │  POST /api/v1/ai/      │                      │              │               │
  │  interpret             │                      │              │               │
  │  {wonguk_data}         │                      │              │               │
  │───────────────────────>│                      │              │               │
  │                        │  프롬프트 빌드         │              │               │
  │                        │  (원국→프롬프트)       │              │               │
  │                        │                      │              │               │
  │                        │                      │  SSE Stream  │               │
  │                        │──────────────────────────────────>│               │
  │  SSE: 해석 스트리밍     │                      │              │               │
  │<═══════════════════════│<═════════════════════════════════│               │
  │  SSE: [done]           │                      │              │               │
  │                        │                      │              │               │
  │                        │  해석 결과 저장        │              │               │
  │                        │─────────────────────────────────────────────────────>│
```

**핵심**: 원국 데이터는 즉시 반환하여 UI를 먼저 렌더링하고,
LLM 해석은 SSE 스트리밍으로 점진적 표시. 사용자 체감 속도 극대화.

#### 흐름 B: 오늘의 운세

```
Client                  API Route              YongSin          Cache(Supabase)
  │                        │                      │               │
  │  GET /api/v1/saju/     │                      │               │
  │  fortune?type=daily    │                      │               │
  │───────────────────────>│                      │               │
  │                        │                      │               │
  │                        │  캐시 확인             │               │
  │                        │  key: {user_id}:      │               │
  │                        │  {today}:daily        │               │
  │                        │──────────────────────────────────────>│
  │                        │                      │               │
  │                        │  [캐시 HIT]           │               │
  │  캐시된 결과 즉시 반환  │<──────────────────────────────────────│
  │<───────────────────────│                      │               │
  │                        │                      │               │
  │                        │  [캐시 MISS일 경우]    │               │
  │                        │  Layer 4 호출         │               │
  │                        │─────────────────────>│               │
  │                        │  세운 데이터           │               │
  │                        │<─────────────────────│               │
  │                        │                      │               │
  │                        │  LLM 해석 생성         │               │
  │                        │  + 캐시 저장           │               │
  │                        │──────────────────────────────────────>│
  │  운세 결과              │                      │               │
  │<───────────────────────│                      │               │
```

---

## 4. 데이터 전략

### 4.1 데이터 레이어 재설계

```
┌─────────────────────────────────────────────────────────────────┐
│                   v3.0 Data Strategy Layers                       │
│                                                                   │
│  Layer 1: YongSin Raw Data (API 응답 원본)                       │
│  ├── 원국(原局) 캐시 — 생년월일시+성별 해시 기준 영구 캐싱         │
│  ├── 운세 분석 캐시 — target_year 기준 연간 캐싱                   │
│  ├── 궁합 분석 캐시 — 두 사람 조합 기준 영구 캐싱                  │
│  └── TTL: 원국=영구, 운세=1일~1년, 궁합=영구                      │
│                                                                   │
│  Layer 2: Interpreted Content (LLM 해석 결과)                     │
│  ├── 종합 사주 풀이 — 원국 해시별 캐싱                             │
│  ├── 토픽별 심층 분석 — 원국+토픽별 캐싱                           │
│  ├── 운세 해석 — 원국+날짜별 캐싱                                  │
│  ├── 궁합 해석 — 두 원국 조합별 캐싱                               │
│  └── TTL: 풀이=30일, 운세=1일, 궁합=30일                          │
│                                                                   │
│  Layer 3: User Data (Supabase)                                    │
│  ├── 사용자 프로필 (Supabase Auth)                                 │
│  ├── 사주 프로필 (birth_data + 원국 캐시 참조)                     │
│  ├── 상담 이력 (채팅 메시지)                                       │
│  ├── 즐겨찾기 / 저장된 해석                                        │
│  └── 결제/구독 데이터                                              │
│                                                                   │
│  Layer 4: Knowledge Base (명리학 지식)                             │
│  ├── 적천수/자평진전/궁통보감 텍스트 (RAG용)                        │
│  ├── 해석 가이드라인 (프롬프트 참고)                                │
│  └── 용어 사전 (한자-한글-베트남어)                                 │
│                                                                   │
│  Layer 5: Analytics (분석 데이터)                                  │
│  ├── API 호출 비용 추적                                            │
│  ├── 사용자 행동 로그                                              │
│  └── AI 응답 품질 피드백                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 캐싱 전략

#### 원국 캐시 (가장 중요)

```
캐시 키 설계:
  wonguk:{sha256(birth_year + birth_month + birth_day + birth_hour + gender + is_lunar)}

특성:
  - 동일 생년월일시+성별 → 동일 원국 (불변 데이터)
  - 영구 캐시 가능 (원국은 변하지 않음)
  - Supabase DB에 저장 (saju_cache 테이블)

절약 효과:
  - 같은 사주 조합 재요청 시 YongSin API 미호출
  - 부부/친구 궁합에서 한 명은 이미 캐시됨
  - 운세 분석 시에도 원국은 캐시에서 로드
```

#### 해석 캐시 (비용 최적화)

```
캐시 키 설계:
  interpret:{wonguk_hash}:{analysis_type}:{lang}:{version}

특성:
  - 동일 원국 + 동일 분석 유형 → 동일 해석 (LLM 미호출)
  - TTL: 종합풀이 30일, 운세 1일, 궁합 30일
  - version: 프롬프트 변경 시 캐시 무효화

절약 효과:
  - LLM API 비용 최대 80% 절감 (재방문자)
  - 같은 사주를 가진 다른 사용자도 캐시 혜택
```

#### 캐시 레이어 구조

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  React Query     │────>│  Supabase DB     │────>│  YongSin API │
│  (Client Cache)  │     │  (Server Cache)  │     │  (Source)     │
│                  │     │                  │     │              │
│  TTL: 5분        │     │  TTL: 영구/30일   │     │  실시간 호출  │
│  staleTime: 1분  │     │  saju_cache 테이블│     │              │
│  인메모리         │     │  PostgreSQL      │     │              │
└──────────────────┘     └──────────────────┘     └──────────────┘

요청 흐름:
1. React Query 캐시 확인 → HIT: 즉시 반환 (0ms)
2. Supabase 캐시 확인 → HIT: DB 조회 후 반환 (<50ms)
3. 캐시 MISS → YongSin API 호출 → 결과 캐시 저장 → 반환 (1-3초)
```

### 4.3 Supabase DB 스키마 (핵심 테이블)

```sql
-- 사주 원국 캐시 (YongSin API 결과)
CREATE TABLE saju_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cache_key VARCHAR(64) UNIQUE NOT NULL,  -- SHA256 해시
  birth_data JSONB NOT NULL,              -- 요청 파라미터
  wonguk_data JSONB NOT NULL,             -- YongSin 원국 응답 전체
  api_layer VARCHAR(10) NOT NULL,         -- 'layer1-3', 'layer4', 'layer5'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  accessed_at TIMESTAMPTZ DEFAULT NOW(),  -- 최근 접근 (LRU 관리용)
  access_count INT DEFAULT 1
);

-- 사용자 사주 프로필
CREATE TABLE saju_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  label VARCHAR(50) NOT NULL DEFAULT '나',  -- "나", "파트너", "아이"
  name VARCHAR(100),
  birth_year INT NOT NULL,
  birth_month INT NOT NULL,
  birth_day INT NOT NULL,
  birth_hour INT,
  birth_minute INT,
  gender VARCHAR(10) NOT NULL,
  is_lunar BOOLEAN DEFAULT FALSE,
  is_leap_month BOOLEAN DEFAULT FALSE,
  cache_key VARCHAR(64) REFERENCES saju_cache(cache_key),  -- 원국 캐시 참조
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI 해석 캐시
CREATE TABLE interpretation_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cache_key VARCHAR(128) UNIQUE NOT NULL,  -- wonguk_hash:type:lang:version
  wonguk_hash VARCHAR(64) NOT NULL,
  analysis_type VARCHAR(50) NOT NULL,       -- 'total', 'fortune_daily', 'topic_love'...
  lang VARCHAR(5) NOT NULL,
  prompt_version VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,                    -- LLM 생성 해석 텍스트
  model_used VARCHAR(50),                  -- 'claude-4-sonnet', 'gpt-4o'
  token_count INT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ,                  -- TTL 만료 시간
  quality_score FLOAT                      -- 사용자 피드백 기반
);

-- 상담 세션
CREATE TABLE consultations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  profile_id UUID REFERENCES saju_profiles(id),
  topic VARCHAR(50),                        -- 'love', 'career', 'money', 'self', 'general'
  title VARCHAR(200),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 상담 메시지
CREATE TABLE consultation_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  consultation_id UUID REFERENCES consultations(id),
  role VARCHAR(20) NOT NULL,                -- 'user', 'assistant', 'system'
  content TEXT NOT NULL,
  wonguk_context JSONB,                     -- 해당 메시지에 사용된 원국 컨텍스트
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API 비용 추적
CREATE TABLE api_cost_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_type VARCHAR(20) NOT NULL,            -- 'yongsin', 'claude', 'gpt4o'
  endpoint VARCHAR(100),
  user_id UUID,
  cost_usd DECIMAL(10,6),
  tokens_used INT,
  cache_hit BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.4 기존 데이터 마이그레이션

```
기존 콘텐츠 자산 (유지/활용):
├── 01_intro.json    (상황별 x 일간별 소개) → 폴백 콘텐츠로 유지
├── 02_ilgan.json    (일간별 성격)          → 프롬프트 참고 자료
├── 03_combo.json    (일간 x 월지 해석)     → 프롬프트 참고 자료
├── 04_today.json    (갑자 인덱스별 운세)    → 폴백 콘텐츠로 유지
├── 05_cheer.json    (응원 메시지)          → 그대로 사용
├── 06_compat.json   (일간 x 일간 궁합)     → 폴백 콘텐츠로 유지
├── 07_topic_qa.json (토픽별 Q&A 체인)      → Q&A 구조 유지, 답변 LLM 교체
├── 08_decade.json   (일간별 연대기)        → 대운 기반으로 교체
├── 09_fortune.json  (일간별 운세 개요)      → 세운 기반으로 교체
└── 10_fortune_area.json (일간별 영역별 운세) → 세운+토픽 교체

마이그레이션 전략:
  Phase 1: YongSin 원국 데이터로 UI 렌더링, 해석은 기존 JSON 폴백
  Phase 2: LLM 해석 생성 기능 추가, 점진적으로 JSON 대체
  Phase 3: 기존 JSON은 오프라인/에러 시 폴백으로만 유지
```

---

## 5. AI 활용 전략

### 5.1 핵심 전환: LLM의 역할 변화

```
[v1.0/v2.0] LLM = 콘텐츠 생성기 (배치)
  - 일간 10종류별 템플릿 텍스트 대량 생성
  - 표현 다양화(서술 변형) 목적
  - 사주 지식이 LLM에 의존 (환각 위험)

[v3.0] LLM = 원국 데이터 해석 전문가 (실시간)
  - YongSin이 제공하는 정확한 원국 데이터를 "읽고 해석"
  - 계산은 하지 않음 → 계산 오류 0%
  - 명리학 전문 지식으로 해석/조언만 담당
  - 데이터 기반 추론 → 환각 최소화
```

### 5.2 프롬프트 아키텍처

```
[System Prompt]
  명리학 30년 전문가 페르소나
  + 해석 원칙 (긍정적, 균형적, 근거 제시)
  + 금지 사항 (의학/법률/확정 표현)
  + 안전 가이드라인

[Context Injection] ← YongSin 원국 데이터 전체 주입
  ┌─────────────────────────────────────────────────────┐
  │ [사주 원국 데이터 - YongSin API 분석 결과]             │
  │                                                      │
  │ 사주팔자:                                             │
  │   연주: 甲子 (갑자) | 십신: 편인                       │
  │   월주: 丙寅 (병인) | 십신: 식신                       │
  │   일주: 壬午 (임오) | 십신: - (본인)                   │
  │   시주: 庚子 (경자) | 십신: 편인                       │
  │                                                      │
  │ 지장간:                                               │
  │   子: 癸(100%) | 寅: 甲(60%)/丙(20%)/戊(20%)          │
  │   午: 丙(70%)/丁(30%) | 子: 癸(100%)                  │
  │                                                      │
  │ 오행 분포: 목 25 / 화 20 / 토 5 / 금 15 / 수 35       │
  │ 용신: 토(土) - 신뢰도 85%                              │
  │ 신살: 화개살, 역마살                                    │
  │ 대운 (현재): 戊辰 (38~47세)                            │
  │ 간지 상호작용: 자오충(子午沖), 인오삼합화(寅午三合火)    │
  │ 공망: 戌亥                                             │
  │                                                      │
  │ [운세 데이터 - 2026년]                                 │
  │ 세운: 丙午 (병오) - 화(火) 강세                         │
  │ 용신 활성도: 토(土) 약화 → 주의 필요                    │
  │ 특이 사항: 대운 전환기 (37세 → 38세)                    │
  └─────────────────────────────────────────────────────┘

[User Prompt]
  "종합 사주 풀이를 해주세요" / "올해 연애운은?" / "이 사람과 궁합은?"
```

### 5.3 해석 품질이 달라지는 이유

```
[기존] LLM에게 "갑목 일간 사람의 성격을 알려줘"
  → LLM이 학습 데이터에서 "갑목"에 대한 일반론 생성
  → 같은 갑목이면 거의 비슷한 해석 (개인화 불가)
  → 지장간/용신이 없으므로 깊이 있는 분석 불가

[YongSin+LLM] LLM에게 "이 원국 데이터를 해석해줘"
  → LLM이 구체적 데이터를 분석:
    "일간 임수(壬水)에 월지 인목(寅木)의 지장간 갑목(甲木)이
     식신을 형성하여 표현력이 풍부하고,
     자오충(子午沖)으로 인해 감정의 기복이 있으며,
     용신이 토(土)이므로 안정적인 직업 환경에서 역량 발휘..."
  → 동일 일간이라도 원국 구조에 따라 완전히 다른 해석
  → 대운/세운까지 반영한 시기별 조언 가능
```

### 5.4 LLM 비용 최적화

```
전략 1: 해석 캐싱
  - 동일 원국 + 동일 분석 유형 → 캐시된 해석 반환
  - 예상 캐시 히트율: 종합풀이 70%, 운세 50%, 궁합 60%

전략 2: 모델 단계별 사용
  - 종합 풀이 (깊이 필요): Claude Sonnet 4 / GPT-4o
  - 오늘의 운세 (간결): Claude Haiku / GPT-4o-mini
  - 간단 질문 응답: Claude Haiku

전략 3: 프롬프트 최적화
  - 원국 데이터를 구조화된 형식으로 전달 (토큰 절약)
  - 불필요한 데이터 필터링 (분석 유형별 필요 데이터만)
  - 출력 길이 제한 (종합: 1500자, 운세: 500자, 궁합: 800자)

전략 4: 스트리밍
  - SSE 스트리밍으로 사용자 체감 대기 시간 최소화
  - 첫 토큰까지: <1초
  - 전체 생성: 3-8초 (체감은 즉시 시작)

비용 추정 (MAU 10,000 기준):
  YongSin API: ~$200-500/월 (호출당 $0.01~0.05 가정, 캐시 적용)
  LLM API: ~$300-800/월 (캐시 적용 후)
  Supabase: $25/월 (Pro plan)
  Vercel: $20/월 (Pro plan)
  총: ~$545-1,345/월
```

### 5.5 대화형 AI 상담 설계

```
[기존] Q&A 체인 (미리 정의된 트리 구조)
  - 5개 토픽 x 10개 일간 x 3 depth = 150개 고정 노드
  - 사용자가 미리 정의된 질문만 선택 가능
  - 자유 질문 불가

[YongSin+LLM] 컨텍스트 기반 자유 대화
  - 원국 데이터를 시스템 프롬프트에 주입
  - 사용자가 자유롭게 질문 가능
  - 대화 맥락 유지 (이전 대화 요약 참조)
  - 토픽별 전문 프롬프트 활용 (연애/직업/재물/건강/일반)

  대화 예시:
  사용자: "올해 이직하려고 하는데 어떤가요?"
  AI: "원국을 보면 일간 임수(壬水)에 식신(食神)이 강하여
       창의적인 분야에서 두각을 나타내는 구조입니다.
       올해 세운 병오(丙午)는 식신의 기운이 더 강해지는 해로,
       새로운 표현의 장을 찾는 것이 자연스러운 흐름입니다.
       다만 현재 대운이 무진(戊辰)으로 전환된 지 1년차이므로,
       상반기보다는 하반기에 움직이시는 것이 더 안정적입니다..."
```

---

## 6. 리스크 관리

### 6.1 YongSin API 의존성 리스크

| 리스크 | 발생 확률 | 영향도 | 대응 전략 |
|--------|----------|--------|-----------|
| API 장애 (일시) | 중 | 높음 | 캐시된 원국 데이터로 서빙, 기존 JSON 폴백 |
| API 장애 (장기) | 낮 | 매우높음 | 자체 기초 엔진 유지 (현 engine.ts) 폴백 모드 |
| API 요금 인상 | 중 | 중 | 캐시 히트율 극대화, 대안 API 조사 |
| API 응답 스키마 변경 | 중 | 중 | mapper.ts에서 변환 계층 분리, 버전별 매핑 |
| API 서비스 종료 | 매우낮 | 매우높음 | 원국 데이터 전부 캐시 보유, 대안 엔진 전환 |

#### 폴백 전략 상세

```
Level 1 (정상): YongSin API → LLM 해석 → 풀 서비스
Level 2 (API 일시 장애): 캐시된 원국 → LLM 해석 → 거의 정상
Level 3 (API 장기 장애): 캐시된 원국 → 기존 JSON 해석 → 제한적 서비스
Level 4 (캐시도 없는 신규): 자체 engine.ts → 기존 JSON → 기초 서비스

핵심: engine.ts를 삭제하지 않고 "폴백 엔진"으로 유지
  - 정밀도는 떨어지지만 4기둥 계산은 가능
  - YongSin 없이도 기본 서비스 제공 가능
```

### 6.2 LLM API 리스크

| 리스크 | 대응 |
|--------|------|
| Claude API 장애 | GPT-4o 자동 폴백 |
| 비용 폭증 | 해석 캐싱 + 일일 비용 상한 설정 + 모델 다운그레이드 |
| 환각/부적절 해석 | 안전성 필터 + 원국 데이터 기반 검증 |
| 응답 지연 | SSE 스트리밍 + 타임아웃 + 폴백 텍스트 |

### 6.3 비용 리스크

```
비용 시나리오 분석 (MAU 10,000):

낙관적 (캐시 히트율 80%):
  YongSin: 2,000 고유 원국 x $0.03 = $60/월
  LLM: 10,000 고유 해석 x $0.05 = $500/월
  인프라: $45/월
  총: ~$605/월

보수적 (캐시 히트율 50%):
  YongSin: 5,000 원국 x $0.03 = $150/월
  LLM: 25,000 해석 x $0.05 = $1,250/월
  인프라: $45/월
  총: ~$1,445/월

비상 브레이크:
  - 일일 API 비용 상한: $100/일
  - 상한 도달 시: 신규 분석 일시 중단, 캐시만 서빙
  - 알림: Slack 웹훅으로 비용 경고
```

### 6.4 기술 리스크

| 리스크 | 대응 |
|--------|------|
| Vercel 서버리스 Cold Start | Edge Runtime 사용, ISR 활용 |
| Supabase 무료 한도 | Pro 플랜 $25/월 (충분) |
| 데이터 유출 | 생년월일 해시화 저장, Supabase RLS |
| YongSin 응답 시간 지연 | 타임아웃 10초 + 캐시 우선 전략 |

---

## 7. PDCA 개발 로드맵

### 7.1 전체 일정 (12주)

```
Phase     Week 1-2        Week 3-4         Week 5-6         Week 7-8
         ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
PLAN     │ 요구사항  │    │          │    │          │    │          │
         │ + API 검증│    │          │    │          │    │          │
         └──────────┘    │          │    │          │    │          │
                         │          │    │          │    │          │
DO       │          │    │ YongSin  │    │ LLM 해석 │    │ AI 상담  │
         │          │    │ 통합     │    │ + 운세    │    │ + 토픽   │
         │          │    │ + 원국UI │    │ + 궁합    │    │ + 캘린더 │
         │          │    └──────────┘    └──────────┘    └──────────┘

         Week 9-10        Week 11          Week 12
         ┌──────────┐    ┌──────────┐    ┌──────────┐
CHECK    │ QA + 성능 │    │          │    │          │
         │ + 비용    │    │          │    │          │
         └──────────┘    │          │    │          │
                         │          │    │          │
ACT      │          │    │ 버그픽스 │    │ 클로즈드  │
         │          │    │ + 최적화 │    │ 베타 출시 │
         │          │    └──────────┘    └──────────┘
```

### 7.2 Phase 1: PLAN (Week 1-2)

#### P-1: YongSin API 검증 및 계약 (Week 1)

```
[ ] YongSin API 문서 정독 및 엔드포인트 매핑
[ ] Layer 1-3 테스트: 10개 샘플 사주 분석 요청
[ ] Layer 4 테스트: 세운 분석 정확도 검증
[ ] Layer 5 테스트: 궁합 분석 응답 구조 확인
[ ] 응답 지연 시간 측정 (P50, P95, P99)
[ ] API 요금 체계 확인 및 월 예상 비용 산출
[ ] API 키 발급 및 rate limit 확인
[ ] 장애 시 SLA 및 지원 채널 확인
```

#### P-2: 기술 아키텍처 확정 (Week 1)

```
[ ] YongSin 응답 스키마 → TypeScript 타입 정의
[ ] Supabase 프로젝트 생성 및 스키마 마이그레이션
[ ] 캐싱 전략 확정 (캐시 키, TTL, 무효화 정책)
[ ] 프롬프트 v0.1 작성 (원국 데이터 기반)
[ ] 비용 모니터링 대시보드 설계
```

#### P-3: 기존 서비스 분석 및 마이그레이션 계획 (Week 2)

```
[ ] 기존 컴포넌트 재사용 목록 작성
    - 재사용: BirthDateForm, Header, BottomNav, FadeIn, LoadingOverlay
    - 리팩터링: PillarDisplay (지장간 추가), FortuneCard (세운 기반)
    - 신규: HiddenStemsBar, TenGodsChart, WuxingRadar, DaeunTimeline 등
[ ] 기존 JSON 데이터 → 폴백 전략 확정
[ ] 다국어 키 추가 (신규 용어: 지장간, 십신, 용신, 신살, 대운)
```

**PLAN Phase Gate:**
- YongSin API 10개 샘플 테스트 완료
- 응답 스키마 TypeScript 타입 100% 정의
- Supabase 스키마 마이그레이션 완료
- 캐싱 전략 문서화 완료

### 7.3 Phase 2: DO - Sprint 1 (Week 3-4)

**목표: YongSin 통합 + 원국 UI**

#### D-1: YongSin Gateway 구현 (Week 3)

```
[ ] lib/yongsin/client.ts — API 클라이언트 구현
    - 인증 헤더, 타임아웃, 재시도, 에러 처리
[ ] lib/yongsin/types.ts — 응답 타입 정의 (Layer 1-5)
[ ] lib/yongsin/mapper.ts — API 응답 → 내부 도메인 모델 변환
[ ] lib/yongsin/cache.ts — Supabase 캐싱 레이어
[ ] lib/yongsin/cost-tracker.ts — API 호출 비용 추적
[ ] API Route: /api/v1/saju/analyze 구현
[ ] 캐시 히트/미스 로직 검증
[ ] 단위 테스트: 캐시, 에러 처리, 폴백
```

#### D-2: 원국 시각화 컴포넌트 (Week 3-4)

```
[ ] PillarDisplay 리팩터링 (지장간 표시 추가)
[ ] HiddenStemsBar — 지장간 비율 바 차트
[ ] TenGodsChart — 십신 관계도 (4기둥 위 배치)
[ ] WuxingRadar — 오행 레이더 차트 (지장간 포함 정밀)
[ ] YongsinBadge — 용신 강조 배지
[ ] SinsalList — 신살 목록 (아이콘 + 설명)
[ ] DaeunTimeline — 대운 타임라인 (현재 위치 표시)
[ ] InteractionsMap — 합/충/형 관계 시각화
```

#### D-3: 사주 입력 → 결과 플로우 (Week 4)

```
[ ] BirthDateForm 유지 (기존 재사용)
[ ] 결과 페이지 리디자인 (원국 데이터 기반)
    - 원국 정보 탭: 4기둥 + 지장간 + 십신 + 오행 + 용신
    - 신살 탭: 신살 목록 + 설명
    - 대운 탭: 대운 타임라인
    - 상호작용 탭: 합/충/형 관계도
[ ] 폴백 모드: YongSin 실패 시 기존 engine.ts + JSON 표시
```

**Sprint 1 Gate:**
- YongSin API 연동 완료 (분석, 캐시, 폴백)
- 원국 시각화 8개 컴포넌트 구현
- 사주 입력 → 원국 결과 표시 E2E 동작 확인

### 7.4 Phase 2: DO - Sprint 2 (Week 5-6)

**목표: LLM 해석 + 운세 + 궁합**

#### D-4: LLM 해석 엔진 (Week 5)

```
[ ] lib/ai/llm-gateway.ts — Claude/GPT-4o 멀티프로바이더
[ ] lib/ai/prompt-builder.ts — 원국 데이터 → 프롬프트 조합
[ ] lib/ai/prompt-templates/ — 프롬프트 템플릿 모음
[ ] lib/ai/safety-filter.ts — 안전성 필터
[ ] lib/ai/stream-handler.ts — SSE 스트리밍 유틸
[ ] API Route: /api/v1/ai/interpret (종합 풀이)
[ ] 해석 캐싱 구현 (interpretation_cache 테이블)
[ ] 프롬프트 품질 테스트 (10개 원국 x 5개 주제)
```

#### D-5: 운세 분석 (Week 5-6)

```
[ ] API Route: /api/v1/saju/fortune (YongSin Layer 4)
[ ] 오늘의 운세: 원국 + 일운 기반 LLM 해석
[ ] 월간 운세: 원국 + 월운 기반 LLM 해석
[ ] 연간 운세: 원국 + 세운 기반 LLM 해석 (대운 맥락 포함)
[ ] 운세 캐시: 일별/월별/연별 TTL 설정
[ ] 운세 결과 UI (기존 FortunePeriodTabs 확장)
[ ] YearlyForecast 컴포넌트 (세운 기반 신규)
```

#### D-6: 궁합 분석 (Week 6)

```
[ ] API Route: /api/v1/saju/compat (YongSin Layer 5)
[ ] 궁합 결과 UI 리디자인 (원국 비교 기반)
[ ] CompatDeepDive 컴포넌트 (합/충 관계 상세)
[ ] 영역별 궁합: 연애/소통/가치관/생활/비전
[ ] 궁합 해석 LLM 프롬프트
```

**Sprint 2 Gate:**
- LLM 해석 생성 + 캐싱 동작 확인
- 운세 3종 (일/월/년) 동작 확인
- 궁합 분석 동작 확인
- 프롬프트 품질 50개 샘플 평가 완료

### 7.5 Phase 2: DO - Sprint 3 (Week 7-8)

**목표: AI 상담 + 토픽 + 택일**

#### D-7: AI 대화 상담 (Week 7)

```
[ ] API Route: /api/v1/ai/chat (SSE 스트리밍)
[ ] 대화 맥락 관리 (이전 메시지 요약)
[ ] 원국 데이터 자동 주입 (시스템 프롬프트)
[ ] ChatInterface 컴포넌트 (기존 chat/client.tsx 확장)
[ ] 무료 상담 횟수 제한 (일 3회)
[ ] 상담 이력 저장/조회
```

#### D-8: 토픽별 심층 분석 (Week 7-8)

```
[ ] API Route: /api/v1/ai/topic/[id]
[ ] 5개 토픽 프롬프트: love, career, money, self, general
[ ] 원국 데이터 + 토픽 전문 프롬프트 조합
[ ] 기존 Q&A 체인 구조 → 자유 대화로 전환
    (초기 질문 3개 제안 후 자유 질문 가능)
[ ] TopicAnalysis 컴포넌트
```

#### D-9: 택일 캘린더 (Week 8)

```
[ ] API Route: /api/v1/saju/calendar (YongSin Layer 6)
[ ] 캘린더 UI 컴포넌트
[ ] 용도별 택일: 결혼, 이사, 사업 시작, 여행
[ ] 길일/흉일 시각화
```

**Sprint 3 Gate:**
- AI 상담 대화 SSE 스트리밍 동작
- 5개 토픽 심층 분석 동작
- 택일 캘린더 기본 동작

### 7.6 Phase 3: CHECK (Week 9-10)

#### C-1: 기능 검증

```
[ ] E2E 테스트: 전체 사용자 플로우 (입력 → 분석 → 운세 → 궁합 → 상담)
[ ] 다국어 검증: 한국어/베트남어 전체 화면
[ ] 폴백 검증: YongSin 장애 시 기존 엔진 폴백 동작
[ ] LLM 폴백 검증: Claude 장애 시 GPT-4o 전환
[ ] 캐시 검증: 캐시 히트율 측정 (목표 60%+)
```

#### C-2: 성능 테스트

```
[ ] 응답 시간 측정:
    - 원국 분석 (캐시 히트): <200ms
    - 원국 분석 (캐시 미스): <3초
    - LLM 해석 첫 토큰: <1초
    - LLM 해석 전체: <8초
[ ] 동시 접속: 100 concurrent 테스트
[ ] 모바일 성능: Lighthouse 80+ 목표
```

#### C-3: 비용 검증

```
[ ] 1일 시뮬레이션: 100명 사용 시 비용
[ ] 캐시 효과 측정: 캐시 전/후 비용 비교
[ ] 비용 알림 동작 확인
[ ] 비용 대시보드 검증
```

#### C-4: 보안 검증

```
[ ] 생년월일 데이터 암호화 확인
[ ] Supabase RLS 정책 검증
[ ] API 키 노출 방지 확인 (.env / server-only)
[ ] Rate limiting 검증
```

### 7.7 Phase 4: ACT (Week 11-12)

#### A-1: 버그 수정 및 최적화 (Week 11)

```
[ ] CHECK에서 발견된 이슈 수정
[ ] 프롬프트 품질 개선 (피드백 기반)
[ ] 캐시 히트율 최적화
[ ] 비용 최적화 (모델 다운그레이드 적용)
```

#### A-2: 클로즈드 베타 준비 (Week 12)

```
[ ] 베타 사용자 초대 (20-50명)
[ ] 피드백 수집 채널 구축
[ ] 모니터링 대시보드 최종 확인
[ ] 비용 모니터링 실시간 알림
[ ] 에러 트래킹 (Sentry) 설정
[ ] 출시 체크리스트 완료
```

---

## 8. 기술 결정 기록 (ADR)

### ADR-001: YongSin API를 핵심 사주 엔진으로 채택

- **결정**: 자체 engine.ts 대신 YongSin API를 핵심 사주 계산 엔진으로 사용
- **근거**: 지장간/십신/용신/대운/신살 등 자체 구현에 6개월+ 소요되는 기능을 즉시 확보
- **리스크**: 외부 API 의존 → 캐싱 + 폴백 전략으로 완화
- **기존 engine.ts**: 폴백 엔진으로 유지 (삭제하지 않음)

### ADR-002: Next.js Fullstack (FastAPI 폐기)

- **결정**: 별도 FastAPI 서버 없이 Next.js API Routes를 백엔드로 사용
- **근거**: 자체 사주 계산 엔진(Python) 불필요 → FastAPI 존재 이유 소멸. 단일 배포로 운영 복잡도 최소화
- **장점**: Vercel 배포, 프론트/백 통합, 인프라 비용 최소화
- **한계**: CPU 집약 작업에 부적합 (사주 계산은 YongSin이 담당하므로 해당 없음)

### ADR-003: Supabase를 통합 백엔드 서비스로 채택

- **결정**: 자체 PostgreSQL + Redis 운영 대신 Supabase PaaS 사용
- **근거**: Auth(카카오 OAuth), DB, Storage, Realtime을 하나의 서비스에서 관리. 인프라 운영 부담 제거
- **비용**: Free tier → Pro($25/월)로 충분

### ADR-004: 실시간 LLM 해석 (배치 사전생성 폐기)

- **결정**: v2.0의 518,400개 사주 조합 사전생성 방식 폐기 → 실시간 LLM 해석 + 결과 캐싱
- **근거**: YongSin이 원국 데이터를 제공하므로 LLM에게 "정확한 데이터를 해석하라"고 지시 가능. 사전생성의 비현실적 규모/비용 문제 해소
- **비용 대응**: 해석 캐싱으로 재방문자 비용 최소화

### ADR-005: 기존 JSON 콘텐츠를 폴백으로 유지

- **결정**: 08_decade.json, 09_fortune.json 등 기존 콘텐츠를 삭제하지 않고 폴백으로 보존
- **근거**: API 장애 시에도 기초 서비스 제공 가능. 점진적 마이그레이션 안전망

---

## 부록: 기존 서비스 → 신규 서비스 매핑

| 기존 제품 | 기존 데이터 소스 | 신규 데이터 소스 | 변화 |
|-----------|-----------------|-----------------|------|
| 종합사주 (total) | engine.ts + intro/ilgan/combo JSON | YongSin Layer 1-3 + LLM 해석 | 원국 전체 분석으로 깊이 대폭 향상 |
| 신년운세 (yearly) | engine.ts + fortune JSON (일간별 고정) | YongSin Layer 4 (target_year) + LLM | 개인화 세운/대운 분석 |
| 궁합 (compat) | engine.ts + compat_reason JSON (일간쌍 고정) | YongSin Layer 5 + LLM | 원국 전체 비교 (합/충 포함) |
| 오늘의운세 (daily) | engine.ts + today JSON (갑자인덱스별 고정) | YongSin Layer 4 (today) + LLM | 원국 기반 개인화 운세 |
| 토픽 Q&A | topic_qa JSON (일간x토픽 고정 트리) | YongSin 원국 + LLM 자유 대화 | 고정 트리 → 자유 대화 전환 |
| 택일 (NEW) | 없음 | YongSin Layer 6 | 완전 신규 기능 |
| AI 상담 (NEW) | 없음 | YongSin 원국 + LLM SSE 스트리밍 | 완전 신규 기능 |

---

> **다음 단계**: 이 문서가 승인되면 Phase 1(PLAN) Week 1의 YongSin API 검증부터 시작합니다.
> YongSin API 접근 권한(API 키) 확보가 선행 조건입니다.
