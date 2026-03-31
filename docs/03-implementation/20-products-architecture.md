# 20개 상품 구현 아키텍처 - 실행 명세서

> **Version:** 1.0
> **Date:** 2026-03-28
> **Author:** CTO Lead
> **Status:** Checkpoint 3 (설계안 선택 대기)
> **Depends on:** yongsin-api-architecture.md, content-pipeline-design.md

---

## 목차

1. [기술 아키텍처](#1-기술-아키텍처)
2. [파일 구조 설계](#2-파일-구조-설계)
3. [DB 스키마](#3-db-스키마)
4. [구현 순서 (Phase별 태스크)](#4-구현-순서)
5. [P0 5개 상품 구현 스펙](#5-p0-5개-상품-구현-스펙)

---

## 1. 기술 아키텍처

### 1.1 전체 시스템 구조

```
[Client Browser]
    |
    v
[Next.js 15 App Router]
    |
    +-- /[locale]/           -- 페이지 (SSR + Client)
    |   +-- page.tsx         -- 홈 (상품 카탈로그)
    |   +-- products/[slug]  -- 20개 상품 페이지
    |   +-- result/[id]      -- 결과 보기
    |   +-- my/              -- 마이 (구매내역, 구독)
    |
    +-- /api/v1/             -- Next.js API Routes (Gateway)
    |   +-- saju/            -- YongSin API Proxy
    |   +-- content/         -- LLM Content Pipeline
    |   +-- auth/            -- Supabase Auth Hooks
    |   +-- payment/         -- 결제 Webhook
    |
    +-- [Supabase]           -- Auth + DB + Storage
    |   +-- auth.users       -- 사용자
    |   +-- saju_cache       -- YongSin 응답 캐시
    |   +-- purchases        -- 단건 구매
    |   +-- subscriptions    -- 구독
    |   +-- content_cache    -- LLM 생성 콘텐츠 캐시
    |
    +-- [YongSin API]        -- 외부 사주 계산 API
    +-- [Claude API]         -- LLM (Sonnet 4 / Haiku 3.5)
```

### 1.2 YongSin API Gateway (Next.js API Routes)

모든 YongSin API 호출은 서버에서만 발생한다. API Key가 클라이언트에 노출되면 안 된다.

```
next-app/src/app/api/v1/saju/
├── route.ts                     -- 공용 미들웨어 (인증 확인, rate limit)
├── natal/route.ts               -- 원국 분석 (unified/complete-analysis)
├── fortune/
│   ├── yearly/route.ts          -- 연간 운세 (layer4/comprehensive)
│   ├── daily/route.ts           -- 일일 운세 (layer6/timing/personal/today)
│   ├── hourly/route.ts          -- 12시진 (layer6/timing/personal/hourly)
│   └── weekly/route.ts          -- 주간 흐름 (layer6/timing/personal/weekly)
├── compat/route.ts              -- 궁합 (layer5)
├── timing/
│   ├── taegil/route.ts          -- 택일 (layer6/timing/taegil)
│   └── golden/route.ts          -- 황금시기 (prime-periods)
├── decision/
│   ├── strategy/route.ts        -- 전략 (layer7)
│   └── four-axis/route.ts       -- 4축 성격 (layer7/four-axis)
├── dream/route.ts               -- 꿈 해석 (layer8)
└── weather/route.ts             -- 오늘 날씨/액션 (today/*)
```

**Gateway 핵심 로직:**

```typescript
// app/api/v1/saju/natal/route.ts (예시 구조)
import { NextRequest, NextResponse } from 'next/server';
import { createServerClient } from '@/lib/supabase-server';
import { yongsinClient } from '@/lib/yongsin/client';
import { getCachedNatal, setCachedNatal } from '@/lib/cache/saju-cache';

export async function POST(req: NextRequest) {
  // 1. 인증 확인 (무료 상품은 optional, 유료는 필수)
  const supabase = createServerClient();
  const { data: { user } } = await supabase.auth.getUser();

  // 2. 요청 파싱
  const { year, month, day, hour, gender, isLunar } = await req.json();

  // 3. 캐시 확인 (동일 생년월일시 = 동일 원국)
  const cacheKey = `natal:${year}:${month}:${day}:${hour}:${gender}`;
  const cached = await getCachedNatal(cacheKey);
  if (cached) return NextResponse.json(cached);

  // 4. YongSin API 호출
  const result = await yongsinClient.completeAnalysis({
    year, month, day, hour, gender, isLunar
  });

  // 5. 캐시 저장 (원국은 영구 캐시)
  await setCachedNatal(cacheKey, result);

  // 6. 응답
  return NextResponse.json(result);
}
```

**YongSin Client 래퍼:**

```typescript
// lib/yongsin/client.ts
const BASE_URL = process.env.YONGSIN_API_URL;
const API_KEY = process.env.YONGSIN_API_KEY;

class YongSinClient {
  private async fetch<T>(endpoint: string, body: unknown): Promise<T> {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY!,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new YongSinError(res.status, await res.text());
    return res.json();
  }

  // Layer 1-3: 원국 완전 분석
  async completeAnalysis(params: NatalParams) {
    return this.fetch('/api/v1/unified/complete-analysis', params);
  }

  // Layer 4: 연간 운세
  async yearlyFortune(params: NatalParams & { target_year: number }) {
    return this.fetch('/api/layer4/comprehensive', params);
  }

  // Layer 5: 궁합
  async compatibility(my: NatalParams, partner: NatalParams) {
    return this.fetch('/api/layer5', {
      my_payload: my,
      your_payload: partner,
    });
  }

  // Layer 6: 일상 운세
  async todayFortune(params: NatalParams) {
    return this.fetch('/api/layer6/timing/personal/today', params);
  }

  async hourlyFortune(params: NatalParams) {
    return this.fetch('/api/layer6/timing/personal/hourly', params);
  }

  // Layer 7: 전략/의사결정
  async fourAxis(params: NatalParams) {
    return this.fetch('/api/layer7/four-axis/all', params);
  }

  // Layer 8: 꿈 해석
  async dreamInterpret(params: NatalParams & { dream_text: string }) {
    return this.fetch('/api/layer8/dream-interpret', params);
  }

  // Today: 날씨/액션
  async todayWeather(params: NatalParams) {
    return this.fetch('/api/today/weather', params);
  }

  async todayAction(params: NatalParams) {
    return this.fetch('/api/today/action-item', params);
  }
}

export const yongsinClient = new YongSinClient();
```

### 1.3 캐싱 전략

3-Layer 캐시 아키텍처:

```
Layer 1: React Query (클라이언트)
  - staleTime: 상품별 다름
  - 페이지 이동 시 재활용
  - 새로고침 시 소멸

Layer 2: Supabase DB (서버)
  - saju_cache 테이블: YongSin 원시 응답
  - content_cache 테이블: LLM 생성 콘텐츠
  - TTL 기반 자동 정리 (pg_cron)

Layer 3: Next.js ISR / Route Handler Cache
  - 무료 상품: revalidate = 3600 (1시간)
  - 유료 상품: no-cache (개인화)
```

**캐시 TTL 정책:**

| 데이터 유형 | 키 구조 | TTL | 이유 |
|------------|---------|-----|------|
| 원국(natal) | `natal:{birth_hash}` | 영구 | 생년월일시 불변 |
| 연간운세 | `yearly:{birth_hash}:{year}` | 365일 | 연 1회 갱신 |
| 월간운세 | `monthly:{birth_hash}:{year}:{month}` | 30일 | 월 1회 갱신 |
| 일일운세 | `daily:{birth_hash}:{date}` | 24시간 | 매일 갱신 |
| 12시진 | `hourly:{birth_hash}:{date}` | 24시간 | 매일 갱신 |
| 궁합 | `compat:{hash_a}:{hash_b}` | 영구 | 두 사람 불변 |
| 콘텐츠(LLM) | `content:{product}:{birth_hash}:{period}` | 상품별 | 생성 비용 절감 |

**React Query 설정:**

```typescript
// lib/query/saju-queries.ts
import { useQuery } from '@tanstack/react-query';

export function useNatalAnalysis(birthData: BirthData | null) {
  return useQuery({
    queryKey: ['natal', birthData],
    queryFn: () => fetch('/api/v1/saju/natal', {
      method: 'POST',
      body: JSON.stringify(birthData),
    }).then(r => r.json()),
    enabled: !!birthData,
    staleTime: Infinity,        // 원국은 절대 변하지 않음
    gcTime: 1000 * 60 * 60,     // 1시간 동안 메모리 유지
  });
}

export function useDailyFortune(birthData: BirthData | null) {
  return useQuery({
    queryKey: ['daily', birthData, new Date().toISOString().split('T')[0]],
    queryFn: () => fetch('/api/v1/saju/fortune/daily', {
      method: 'POST',
      body: JSON.stringify(birthData),
    }).then(r => r.json()),
    enabled: !!birthData,
    staleTime: 1000 * 60 * 60,  // 1시간
    gcTime: 1000 * 60 * 60 * 24, // 24시간
  });
}
```

### 1.4 줄글 DB 구조 (전문가별 톤 템플릿)

12명의 전문가 톤을 시스템 프롬프트로 관리한다. 줄글 DB(murakami-db.json 등)는 A소설가 톤 전용이고, 나머지 11명은 LLM 실시간 생성이다.

```
lib/experts/
├── types.ts                -- ExpertPersona 인터페이스
├── registry.ts             -- 12명 전문가 등록
├── prompts/
│   ├── A-novelist.ts       -- A 소설가 (하루키)
│   ├── B-neighbor.ts       -- B 동네형/언니
│   ├── C-planner.ts        -- C 재무설계사
│   ├── D-career.ts         -- D 커리어코치
│   ├── E-love.ts           -- E 연애상담사
│   ├── F-doctor.ts         -- F 한의사
│   ├── G-grandma.ts        -- G 점집할머니
│   ├── H-analyst.ts        -- H 데이터분석가
│   ├── I-professor.ts      -- I 철학교수
│   ├── J-designer.ts       -- J 인테리어디자이너
│   ├── K-coach.ts          -- K 라이프코치
│   └── L-detective.ts      -- L 탐정
└── pipeline.ts             -- 전문가별 콘텐츠 생성 파이프라인
```

**전문가 인터페이스:**

```typescript
// lib/experts/types.ts
export interface ExpertPersona {
  id: string;                    // 'A' | 'B' | ... | 'L'
  name: { ko: string; vi: string };
  tone: string;                  // 톤 설명
  systemPrompt: string;          // LLM 시스템 프롬프트
  exampleOutput: string;         // few-shot 예시
  metaphorDomains: string[];     // 비유 영역
  sentenceStyle: {
    avgLength: 'short' | 'medium' | 'long';
    formality: 'casual' | 'neutral' | 'formal';
    humor: 'none' | 'subtle' | 'frequent';
  };
  outputFormat: 'prose' | 'bullet' | 'mixed' | 'card';
}
```

**P0 상품 전문가 톤 (B 동네형):**

```typescript
// lib/experts/prompts/B-neighbor.ts
export const neighborExpert: ExpertPersona = {
  id: 'B',
  name: { ko: '동네 언니/형', vi: 'Anh/Chi hang xom' },
  tone: '편하고 직설적. 반말. 공감 먼저.',
  systemPrompt: `
당신은 사주를 잘 아는 동네 형(또는 언니)입니다.

말투 규칙:
- 반말을 씁니다 ("~해", "~야", "~거든")
- 첫 마디는 공감으로 시작합니다 ("요즘 좀 힘들지?", "오~ 너 사주 좋은데?")
- 전문 용어는 쉬운 말로 바꿉니다 (편인 -> "공부 머리", 식신 -> "끼")
- 카톡으로 대화하는 것처럼 짧고 리듬감 있게 씁니다
- 가끔 ㅋㅋ, ㅎㅎ 같은 표현을 넣되 과하지 않게
- 마지막은 항상 응원이나 따뜻한 조언으로 마무리합니다
- 이모지는 쓰지 않습니다

금지 사항:
- 존댓말 금지
- 전문 용어 나열 금지
- 부정적/공포 유발 표현 금지
- 모호한 표현 금지 ("~일 수도 있어" 대신 구체적으로)
`,
  exampleOutput: `
오~ 너 갑목이야? 큰 나무. 좋은데.

기본적으로 넌 뿌리가 깊은 사람이야.
한번 정하면 안 흔들려. 리더 타입이라기보다는
방향이 있는 사람이야. 어디로 갈지 아는 사람.

근데 좀 고집이 있어 ㅎㅎ
고집이라기보다는... 한번 자란 방향을 바꾸기 어려운 거지.
그게 장점이기도 하고.

올해는 네 오행에 불기운이 좀 세게 들어와.
쉽게 말하면, 에너지가 넘치는 해야.
하고 싶은 거 있으면 올해 해. 진짜로.
`,
  metaphorDomains: ['일상 대화', '카톡 톤', '학교/직장 비유'],
  sentenceStyle: {
    avgLength: 'short',
    formality: 'casual',
    humor: 'subtle',
  },
  outputFormat: 'prose',
};
```

### 1.5 인증/결제 연동 구조

**인증 (Supabase Auth):**

```
[진입 경로]
  무료 상품 (P0): 인증 불필요 → 로컬 저장 → 결과 즉시
  유료 상품 (P1+): 인증 필수 → 소셜 로그인 → 결제 → 결과

[Supabase Auth 설정]
  - 소셜 로그인: Kakao, Google, Apple
  - Session: JWT (httpOnly cookie)
  - RLS: user_id 기반 행 수준 보안
```

**결제 연동:**

```
[결제 프로바이더]
  - 한국: 포트원(PortOne) v2 — 카카오페이, 토스페이, 카드
  - 베트남: VNPay, MoMo (추후)

[결제 흐름]
  1. 클라이언트: 상품 선택 → /api/v1/payment/prepare (주문 생성)
  2. 서버: Supabase에 order 레코드 생성 (status: pending)
  3. 클라이언트: PortOne SDK 결제창 호출
  4. 결제 완료: PortOne → /api/v1/payment/webhook (서버)
  5. 서버: 결제 검증 → order.status = paid → purchase 레코드 생성
  6. 서버: 콘텐츠 생성 트리거 → 결과 저장
  7. 클라이언트: polling → 결과 페이지 이동

[구독 흐름]
  - PortOne 정기결제 API
  - billing_key 발급 → Supabase subscriptions 테이블
  - 매월 자동 결제 → webhook → 구독 갱신
```

```typescript
// app/api/v1/payment/prepare/route.ts (구조)
export async function POST(req: NextRequest) {
  const supabase = createServerClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { productCode, birthData } = await req.json();
  const product = getProductConfig(productCode);

  // 주문 생성
  const { data: order } = await supabase.from('orders').insert({
    user_id: user.id,
    product_code: productCode,
    amount: product.price,
    status: 'pending',
    birth_data: birthData,
  }).select().single();

  return NextResponse.json({
    orderId: order.id,
    amount: product.price,
    orderName: product.name.ko,
  });
}
```

### 1.6 콘텐츠 생성 파이프라인 (LLM)

P0 무료 상품은 LLM을 호출하지 않는다. YongSin API 데이터 + 줄글 DB 조합으로 즉시 응답한다.
P1+ 유료 상품부터 LLM 파이프라인을 사용한다.

```
[P0 무료 — LLM 미사용]
  YongSin API → Stage 1 (코드 정제) → 줄글 DB 조립 → 화면 렌더링
  - 응답시간: 1-2초
  - 비용: $0 (YongSin API 호출 비용만)

[P1+ 유료 — LLM 사용]
  YongSin API → Stage 1 (코드) → Stage 2 (Sonnet, 해석) → Stage 3 (Sonnet, 서술) → Stage 4 (Haiku, 검증)
  - 응답시간: 8-15초 (SSE 스트리밍)
  - 비용: ~$0.10/리포트
```

**P0 콘텐츠 조립기 (LLM 불필요):**

```typescript
// lib/content/assembler.ts
import type { NatalResult } from '@/lib/yongsin/types';
import { neighborExpert } from '@/lib/experts/prompts/B-neighbor';

// B동네형 톤으로 원국 데이터를 친근한 텍스트로 변환
export function assembleNatalReport(
  natal: NatalResult,
  name: string,
  lang: 'ko' | 'vi'
): NatalReportContent {
  const ilganKey = natal.four_pillars.day.stem.key;  // 'gap', 'eul', etc.

  // 1. 줄글 DB에서 일간별 기본 텍스트 로드
  const ilganText = MURAKAMI_DB.ilgan[ilganKey];

  // 2. B동네형 톤 변환 템플릿 적용
  const sections = [
    {
      title: '너는 이런 사람이야',
      body: neighborToneTransform(ilganText.opening, name),
    },
    {
      title: '타고난 성격',
      body: neighborToneTransform(ilganText.nature, name),
    },
    {
      title: '오행 밸런스',
      body: formatWuxingBalance(natal.wuxing, name, lang),
    },
    {
      title: '올해 한 줄',
      body: formatTodayLine(natal, lang),
    },
  ];

  return { sections, expert: neighborExpert };
}
```

---

## 2. 파일 구조 설계

### 2.1 신규 생성 파일 목록

```
next-app/src/
├── app/
│   ├── api/v1/                              # [신규] API Gateway
│   │   ├── saju/
│   │   │   ├── natal/route.ts               # 원국 분석
│   │   │   ├── fortune/
│   │   │   │   ├── daily/route.ts           # 일일 운세
│   │   │   │   ├── yearly/route.ts          # 연간 운세
│   │   │   │   ├── hourly/route.ts          # 12시진
│   │   │   │   └── weekly/route.ts          # 주간 흐름
│   │   │   ├── compat/route.ts              # 궁합
│   │   │   ├── timing/
│   │   │   │   ├── taegil/route.ts          # 택일
│   │   │   │   └── golden/route.ts          # 황금시기
│   │   │   ├── decision/
│   │   │   │   ├── strategy/route.ts        # 전략
│   │   │   │   └── four-axis/route.ts       # 4축 성격
│   │   │   ├── dream/route.ts               # 꿈 해석
│   │   │   └── weather/route.ts             # 날씨/액션
│   │   ├── content/
│   │   │   └── generate/route.ts            # LLM 콘텐츠 생성 (SSE)
│   │   ├── payment/
│   │   │   ├── prepare/route.ts             # 주문 준비
│   │   │   └── webhook/route.ts             # 결제 확인
│   │   └── auth/
│   │       └── callback/route.ts            # 소셜 로그인 콜백
│   │
│   └── [locale]/
│       ├── products/                        # [신규] 20개 상품 페이지
│       │   ├── layout.tsx                   # 상품 공통 레이아웃
│       │   ├── natal/page.tsx               # P0-1: 원국 리포트
│       │   ├── daily/page.tsx               # P0-2: 오늘의 운세
│       │   ├── myeong-gung/page.tsx         # P0-3: 명궁 분석
│       │   ├── weather-card/page.tsx        # P0-4: 날씨 카드
│       │   ├── type-card/page.tsx           # P0-5: MBTI형 유형 카드
│       │   ├── yearly/page.tsx              # P1-6: 올해 운세
│       │   ├── compat/page.tsx              # P1-7: 궁합 리포트
│       │   ├── wedding-date/page.tsx        # P1-8: 결혼 택일
│       │   ├── yongsin/page.tsx             # P1-9: 용신 분석
│       │   ├── four-axis/page.tsx           # P1-10: 4축 성격
│       │   ├── hourly/page.tsx              # P2-11: 12시진
│       │   ├── warning/page.tsx             # P2-12: 오늘 경고
│       │   ├── daily-tip/page.tsx           # P2-13: 매일 한 줄
│       │   ├── lucky-card/page.tsx          # P2-14: 행운 처방
│       │   ├── relationship/page.tsx        # P2-15: 관계 신호등
│       │   ├── life-novel/page.tsx          # P3-16: 인생 소설
│       │   ├── golden-period/page.tsx       # P3-17: 황금 시기
│       │   ├── startup-timing/page.tsx      # P3-18: 창업 타이밍
│       │   ├── life-cycle/page.tsx          # P3-19: 생애 주기
│       │   └── dream/page.tsx               # P3-20: 꿈 해석
│       │
│       ├── auth/                            # [신규] 인증 페이지
│       │   ├── login/page.tsx
│       │   └── callback/page.tsx
│       │
│       └── share/                           # [신규] SNS 공유 전용
│           └── [type]/[id]/page.tsx         # OG Image + 결과 미리보기
│
├── lib/
│   ├── yongsin/                             # [신규] YongSin API 클라이언트
│   │   ├── client.ts                        # API 래퍼
│   │   ├── types.ts                         # YongSin 응답 타입
│   │   └── distiller.ts                     # Stage 1: 데이터 정제
│   │
│   ├── experts/                             # [신규] 전문가 톤 시스템
│   │   ├── types.ts                         # ExpertPersona 인터페이스
│   │   ├── registry.ts                      # 전문가 등록/조회
│   │   ├── prompts/
│   │   │   ├── A-novelist.ts
│   │   │   ├── B-neighbor.ts
│   │   │   ├── C-planner.ts
│   │   │   ├── D-career.ts
│   │   │   ├── E-love.ts
│   │   │   ├── F-doctor.ts
│   │   │   ├── G-grandma.ts
│   │   │   ├── H-analyst.ts
│   │   │   ├── I-professor.ts
│   │   │   ├── J-designer.ts
│   │   │   ├── K-coach.ts
│   │   │   └── L-detective.ts
│   │   └── pipeline.ts                     # LLM 파이프라인 오케스트레이터
│   │
│   ├── content/                             # [신규] 콘텐츠 조립
│   │   ├── assembler.ts                     # P0용 줄글 DB 조립기
│   │   ├── templates/                       # 상품별 템플릿
│   │   │   ├── natal-report.ts
│   │   │   ├── daily-fortune.ts
│   │   │   ├── myeong-gung.ts
│   │   │   ├── weather-card.ts
│   │   │   └── type-card.ts
│   │   └── tone-transform.ts               # 톤 변환 유틸리티
│   │
│   ├── cache/                               # [신규] 캐시 레이어
│   │   ├── saju-cache.ts                    # Supabase 기반 사주 캐시
│   │   └── content-cache.ts                 # Supabase 기반 콘텐츠 캐시
│   │
│   ├── payment/                             # [신규] 결제
│   │   ├── portone.ts                       # PortOne SDK 래퍼
│   │   └── subscription.ts                  # 구독 관리
│   │
│   ├── query/                               # [신규] React Query hooks
│   │   ├── provider.tsx                     # QueryClientProvider
│   │   ├── saju-queries.ts                  # 사주 데이터 queries
│   │   └── content-queries.ts               # 콘텐츠 queries
│   │
│   ├── supabase-server.ts                   # [신규] 서버사이드 Supabase
│   │
│   └── products-v2.ts                       # [신규] 20개 상품 카탈로그
│
├── components/
│   ├── products/                            # [신규] 상품 전용 컴포넌트
│   │   ├── ProductLayout.tsx                # 상품 공통 레이아웃
│   │   ├── BirthInput.tsx                   # 통합 생년월일 입력
│   │   ├── ResultRenderer.tsx               # 결과 렌더러 (전문가 톤별)
│   │   ├── ExpertBadge.tsx                  # 전문가 뱃지 ("B 동네형")
│   │   ├── ShareButton.tsx                  # SNS 공유 버튼
│   │   └── PaymentGate.tsx                  # 결제 필요 시 게이트
│   │
│   ├── cards/                               # [신규] 카드 컴포넌트
│   │   ├── WeatherCard.tsx                  # 날씨 카드 (공유용)
│   │   ├── TypeCard.tsx                     # 유형 카드 (바이럴)
│   │   ├── LuckyCard.tsx                    # 행운 처방 카드
│   │   └── TrafficLight.tsx                 # 관계 신호등
│   │
│   ├── charts/                              # [신규] 차트/시각화
│   │   ├── WuxingRadar.tsx                  # 오행 레이더 차트
│   │   ├── HourlyTimeline.tsx               # 12시진 타임라인
│   │   ├── MonthlyFlow.tsx                  # 월별 흐름 차트
│   │   └── DaeunTimeline.tsx                # 대운 타임라인
│   │
│   ├── saju/
│   │   └── PillarDisplay.tsx                # [수정] 지장간 표시 추가
│   │
│   └── auth/                                # [신규] 인증 컴포넌트
│       ├── LoginModal.tsx                   # 로그인 모달
│       └── SocialButtons.tsx                # 소셜 로그인 버튼
│
├── stores/
│   ├── saju-store.ts                        # [수정] YongSin 데이터 확장
│   └── auth-store.ts                        # [신규] 인증 상태
│
└── types/
    ├── yongsin.ts                           # [신규] YongSin API 타입
    ├── product.ts                           # [신규] 상품/주문 타입
    └── expert.ts                            # [신규] 전문가 타입
```

### 2.2 기존 파일 수정 목록

| 파일 | 변경 내용 |
|------|----------|
| `next-app/package.json` | `@tanstack/react-query`, `@portone/browser-sdk`, `@anthropic-ai/sdk` 추가 |
| `next-app/next.config.ts` | `output: 'standalone'` (API Routes 사용 위해 static export 해제) |
| `next-app/src/middleware.ts` | 인증 체크 미들웨어 추가 (/products/* 경로) |
| `next-app/src/stores/saju-store.ts` | YongSin 원국 데이터, birthData 필드 추가 |
| `next-app/src/lib/products.ts` | 20개 상품으로 확장 (→ products-v2.ts로 마이그레이션) |
| `next-app/src/components/saju/PillarDisplay.tsx` | 지장간(hidden_stems) 표시 추가 |
| `next-app/src/components/layout/BottomNav.tsx` | 탭 구조 변경 (홈/운세/상품/마이) |
| `next-app/src/app/[locale]/page.tsx` | 20개 상품 카탈로그로 홈 리디자인 |
| `next-app/src/app/[locale]/layout.tsx` | QueryClientProvider 래핑 |
| `next-app/src/lib/supabase.ts` | 서버 클라이언트 분리 (supabase-server.ts) |
| `next-app/.env.local` | ANTHROPIC_API_KEY, PORTONE_API_KEY 추가 |

---

## 3. DB 스키마

### 3.1 Supabase 테이블 설계

```sql
-- ===========================================
-- 1. 사용자 프로필 (auth.users 확장)
-- ===========================================
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  birth_year INT,
  birth_month INT,
  birth_day INT,
  birth_hour INT,          -- NULL = 모름
  gender TEXT CHECK (gender IN ('male', 'female')),
  is_lunar BOOLEAN DEFAULT false,
  locale TEXT DEFAULT 'ko' CHECK (locale IN ('ko', 'vi')),
  natal_cache_key TEXT,    -- saju_cache FK (원국 캐시 키)
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own profile"
  ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own profile"
  ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- ===========================================
-- 2. 사주 API 캐시
-- ===========================================
CREATE TABLE public.saju_cache (
  cache_key TEXT PRIMARY KEY,     -- 'natal:1990:3:15:14:male'
  api_layer TEXT NOT NULL,         -- 'natal', 'yearly', 'daily', 'compat', etc.
  request_hash TEXT NOT NULL,      -- SHA256(요청 바디)
  response_data JSONB NOT NULL,    -- YongSin API 응답 원본
  expires_at TIMESTAMPTZ,          -- NULL = 영구
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_saju_cache_layer ON public.saju_cache(api_layer);
CREATE INDEX idx_saju_cache_expires ON public.saju_cache(expires_at)
  WHERE expires_at IS NOT NULL;

-- 자동 정리 (pg_cron)
-- SELECT cron.schedule('clean-expired-cache', '0 4 * * *',
--   $$DELETE FROM public.saju_cache WHERE expires_at < now()$$);

-- ===========================================
-- 3. LLM 생성 콘텐츠 캐시
-- ===========================================
CREATE TABLE public.content_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_code TEXT NOT NULL,      -- 'natal', 'daily', 'yearly', etc.
  expert_id TEXT NOT NULL,         -- 'A', 'B', 'C', ... 'L'
  birth_hash TEXT NOT NULL,        -- 동일 생년월일시 식별
  period_key TEXT,                 -- '2026', '2026-03', '2026-03-28', NULL
  locale TEXT NOT NULL DEFAULT 'ko',
  content JSONB NOT NULL,          -- { sections: [...], metadata: {...} }
  llm_model TEXT,                  -- 'sonnet-4', NULL(줄글DB조립)
  llm_cost_usd NUMERIC(6,4),      -- 생성 비용 추적
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX idx_content_unique
  ON public.content_cache(product_code, expert_id, birth_hash, period_key, locale);

-- ===========================================
-- 4. 상품 카탈로그
-- ===========================================
CREATE TABLE public.products (
  code TEXT PRIMARY KEY,              -- 'natal', 'daily', ...
  tier TEXT NOT NULL CHECK (tier IN ('free', 'paid', 'subscription', 'premium')),
  name_ko TEXT NOT NULL,
  name_vi TEXT NOT NULL,
  desc_ko TEXT,
  desc_vi TEXT,
  price_krw INT DEFAULT 0,            -- 0 = 무료
  price_vnd INT DEFAULT 0,
  expert_id TEXT NOT NULL,             -- 'A' ~ 'L'
  api_layers TEXT[] NOT NULL,          -- {'natal', 'wuxing'} etc.
  requires_auth BOOLEAN DEFAULT false,
  is_active BOOLEAN DEFAULT true,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ===========================================
-- 5. 주문/구매
-- ===========================================
CREATE TABLE public.orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  product_code TEXT NOT NULL REFERENCES public.products(code),
  amount INT NOT NULL,                 -- 결제 금액 (원)
  currency TEXT DEFAULT 'KRW',
  status TEXT DEFAULT 'pending'
    CHECK (status IN ('pending', 'paid', 'failed', 'refunded', 'cancelled')),
  payment_provider TEXT,               -- 'portone', 'vnpay'
  payment_id TEXT,                     -- 외부 결제 ID
  birth_data JSONB,                    -- 결제 시점의 생년월일시 데이터
  partner_birth_data JSONB,            -- 궁합용 상대방 데이터
  metadata JSONB,                      -- 추가 파라미터
  created_at TIMESTAMPTZ DEFAULT now(),
  paid_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ               -- 유료 콘텐츠 열람 만료
);

ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own orders"
  ON public.orders FOR SELECT USING (auth.uid() = user_id);

CREATE INDEX idx_orders_user ON public.orders(user_id);
CREATE INDEX idx_orders_status ON public.orders(status);

-- ===========================================
-- 6. 구매 내역 (결제 완료된 것)
-- ===========================================
CREATE TABLE public.purchases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  order_id UUID NOT NULL REFERENCES public.orders(id),
  product_code TEXT NOT NULL REFERENCES public.products(code),
  content_cache_id UUID REFERENCES public.content_cache(id),
  birth_hash TEXT NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ              -- NULL = 영구, 구독은 기간 만료
);

ALTER TABLE public.purchases ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own purchases"
  ON public.purchases FOR SELECT USING (auth.uid() = user_id);

CREATE INDEX idx_purchases_user ON public.purchases(user_id);
CREATE INDEX idx_purchases_product ON public.purchases(product_code);

-- ===========================================
-- 7. 구독
-- ===========================================
CREATE TABLE public.subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  plan TEXT NOT NULL CHECK (plan IN ('basic', 'premium')),
  status TEXT DEFAULT 'active'
    CHECK (status IN ('active', 'paused', 'cancelled', 'expired')),
  billing_key TEXT,                    -- PortOne 정기결제 키
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  amount INT NOT NULL,
  currency TEXT DEFAULT 'KRW',
  created_at TIMESTAMPTZ DEFAULT now(),
  cancelled_at TIMESTAMPTZ
);

ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users read own subscription"
  ON public.subscriptions FOR SELECT USING (auth.uid() = user_id);

-- ===========================================
-- 8. 사용자 사주 저장 (비로그인 + 로그인 공용)
-- ===========================================
CREATE TABLE public.saved_saju (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),  -- NULL = 비로그인
  session_id TEXT,                          -- 비로그인 식별용
  label TEXT DEFAULT '나',                   -- '나', '파트너', '엄마' 등
  birth_year INT NOT NULL,
  birth_month INT NOT NULL,
  birth_day INT NOT NULL,
  birth_hour INT,
  gender TEXT NOT NULL,
  is_lunar BOOLEAN DEFAULT false,
  natal_cache_key TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_saved_saju_user ON public.saved_saju(user_id);
CREATE INDEX idx_saved_saju_session ON public.saved_saju(session_id);
```

### 3.2 ER 다이어그램 (텍스트)

```
auth.users (Supabase 관리)
    │
    ├─── profiles (1:1)
    │
    ├─── orders (1:N)
    │    └─── purchases (1:1 per order)
    │         └─── content_cache (N:1)
    │
    ├─── subscriptions (1:N)
    │
    └─── saved_saju (1:N)

saju_cache (독립 — 캐시 키 기반)
content_cache (독립 — 상품+생년월일 기반)
products (독립 — 카탈로그)
```

---

## 4. 구현 순서

### Phase 0: 인프라 (3일)

| # | 태스크 | 입력 | 출력 | 파일 |
|---|--------|------|------|------|
| 0-1 | Next.js 설정 변경 | next.config.ts | standalone output, env 설정 | next.config.ts |
| 0-2 | 패키지 설치 | package.json | @tanstack/react-query, @anthropic-ai/sdk | package.json |
| 0-3 | YongSin Client 구현 | API 문서 | yongsinClient 클래스 | lib/yongsin/client.ts, types.ts |
| 0-4 | Supabase 서버 클라이언트 | .env.local | createServerClient() | lib/supabase-server.ts |
| 0-5 | 캐시 레이어 구현 | Supabase 스키마 | get/set 함수 | lib/cache/*.ts |
| 0-6 | React Query Provider | 없음 | QueryClientProvider | lib/query/provider.tsx |
| 0-7 | Supabase 테이블 생성 | SQL 스키마 | 8개 테이블 | supabase/migrations/ |
| 0-8 | 전문가 B톤 프롬프트 | 컨셉 | systemPrompt | lib/experts/prompts/B-neighbor.ts |
| 0-9 | 상품 카탈로그 v2 | 20개 상품 | products-v2.ts | lib/products-v2.ts |
| 0-10 | YongSin 타입 정의 | API 응답 샘플 | TypeScript 타입 | types/yongsin.ts |

### Phase 1: P0 무료 상품 (Week 1-2, 10일)

| # | 태스크 | 입력 | 출력 | 파일 |
|---|--------|------|------|------|
| 1-1 | 통합 생년월일 입력 컴포넌트 | BirthDateForm 리팩토링 | BirthInput.tsx | components/products/BirthInput.tsx |
| 1-2 | 상품 공통 레이아웃 | 디자인 | ProductLayout | components/products/ProductLayout.tsx |
| 1-3 | 원국 리포트 API Route | NatalParams | NatalResult | app/api/v1/saju/natal/route.ts |
| 1-4 | 원국 리포트 페이지 | NatalResult + B톤 | 원국 리포트 화면 | app/[locale]/products/natal/page.tsx |
| 1-5 | 오늘 운세 API Route | NatalParams | DailyResult | app/api/v1/saju/fortune/daily/route.ts |
| 1-6 | 오늘 운세 페이지 | DailyResult + B톤 | 오늘 운세 화면 | app/[locale]/products/daily/page.tsx |
| 1-7 | 명궁 분석 로직 | NatalResult.myeong_gung | 명궁 유형 | lib/content/templates/myeong-gung.ts |
| 1-8 | 명궁 분석 페이지 | 명궁 유형 + B톤 | MBTI 스타일 화면 | app/[locale]/products/myeong-gung/page.tsx |
| 1-9 | 날씨 카드 API | today/weather | 날씨 데이터 | app/api/v1/saju/weather/route.ts |
| 1-10 | 날씨 카드 컴포넌트 | 날씨 데이터 | 공유 가능 카드 | components/cards/WeatherCard.tsx |
| 1-11 | 날씨 카드 페이지 | WeatherCard | 날씨 카드 화면 | app/[locale]/products/weather-card/page.tsx |
| 1-12 | 유형 카드 생성 로직 | NatalResult | 유형 코드+설명 | lib/content/templates/type-card.ts |
| 1-13 | 유형 카드 컴포넌트 | 유형 데이터 | 바이럴 카드 | components/cards/TypeCard.tsx |
| 1-14 | 유형 카드 페이지 | TypeCard | 유형 카드 화면 | app/[locale]/products/type-card/page.tsx |
| 1-15 | 오행 레이더 차트 | wuxing 데이터 | 시각화 | components/charts/WuxingRadar.tsx |
| 1-16 | PillarDisplay 확장 | hidden_stems | 지장간 표시 | components/saju/PillarDisplay.tsx |
| 1-17 | SNS 공유 기능 | 카드 이미지 | Web Share API | components/products/ShareButton.tsx |
| 1-18 | 홈 페이지 리디자인 | 20개 상품 | 카탈로그 홈 | app/[locale]/page.tsx |
| 1-19 | BottomNav 업데이트 | 4탭 | 신규 탭 구조 | components/layout/BottomNav.tsx |
| 1-20 | P0 통합 테스트 | 모든 P0 | 5개 상품 작동 확인 | tests/p0/ |

### Phase 2: P1 유료 단건 (Week 3-4, 10일)

| # | 태스크 | 입력 | 출력 |
|---|--------|------|------|
| 2-1 | Supabase Auth 설정 | Kakao/Google 설정 | 로그인 플로우 |
| 2-2 | 로그인 모달/페이지 | Auth 설정 | LoginModal |
| 2-3 | PortOne 결제 연동 | API Key | 결제 플로우 |
| 2-4 | 결제 게이트 컴포넌트 | product.tier | PaymentGate |
| 2-5 | LLM 파이프라인 구현 | 4-stage 설계 | pipeline.ts |
| 2-6 | A소설가 톤 프롬프트 | murakami-db.json | A-novelist.ts |
| 2-7 | E연애상담사 톤 프롬프트 | 컨셉 | E-love.ts |
| 2-8 | G점집할머니 톤 프롬프트 | 컨셉 | G-grandma.ts |
| 2-9 | I철학교수 톤 프롬프트 | 컨셉 | I-professor.ts |
| 2-10 | L탐정 톤 프롬프트 | 컨셉 | L-detective.ts |
| 2-11 | 올해 운세 페이지 (리팩토링) | layer4 + A톤 | yearly 페이지 |
| 2-12 | 궁합 리포트 페이지 | layer5 + E톤 | compat 페이지 |
| 2-13 | 결혼 택일 페이지 | taegil + G+E톤 | wedding-date 페이지 |
| 2-14 | 용신 분석 페이지 | unified.yongsin + I톤 | yongsin 페이지 |
| 2-15 | 4축 성격 분석 페이지 | layer7.four-axis + L톤 | four-axis 페이지 |
| 2-16 | SSE 스트리밍 구현 | 긴 리포트 | 점진 표시 |
| 2-17 | 구매내역 페이지 | purchases 테이블 | my 페이지 |
| 2-18 | P1 통합 테스트 | 모든 P1 | 결제+결과 확인 |

### Phase 3: P2 구독 (Week 5-8)

구독 인프라 + 5개 구독 상품 + 알림 시스템

### Phase 4: P3 프리미엄 (Week 9+)

프리미엄 콘텐츠 5개 + B2B 확장

---

## 5. P0 5개 상품 구현 스펙

### 5.1 상품 1: 원국 리포트

**상품 정보:**
- 코드: `natal`
- 전문가: B 동네형
- 가격: 무료
- API: `/api/v1/unified/complete-analysis`
- 캐시: 영구 (원국 불변)

**페이지 구조:**

```
/[locale]/products/natal
├── [Step 1] 생년월일 입력 (BirthInput)
│   - 이름, 성별, 생년/월/일/시(선택)
│   - 양력/음력 토글
│   - "내 사주 보기" CTA
│
├── [Step 2] 로딩 (1-2초)
│   - "사주를 불러오는 중..." 애니메이션
│   - YongSin API 호출 진행
│
└── [Step 3] 결과 화면
    ├── [헤더] 전문가 뱃지 ("동네형이 봐줄게")
    ├── [섹션1] 사주 원국 시각화
    │   - PillarDisplay (4기둥 + 지장간)
    │   - 오행 레이더 차트 (WuxingRadar)
    │
    ├── [섹션2] "너는 이런 사람이야" (B톤)
    │   - 일간 성격 해석 (murakami-db.ilgan → B톤 변환)
    │   - 3~5문단 줄글
    │
    ├── [섹션3] "오행 밸런스" (B톤)
    │   - 강한 오행 / 약한 오행 해석
    │   - 실생활 조언 ("불기운이 센 너는 차가운 거 마셔")
    │
    ├── [섹션4] "올해 한 줄" (B톤)
    │   - 연간 키워드 1줄
    │   - 하단에 "더 자세히 보기 → 올해 운세" 링크
    │
    ├── [하단CTA] "궁합도 볼래? → 궁합 리포트"
    │
    └── [공유] ShareButton (카카오톡, 링크 복사)
```

**API 호출 흐름:**

```
[클라이언트]                         [서버]                          [YongSin]
    |                                 |                                |
    |-- POST /api/v1/saju/natal ----->|                                |
    |   { year, month, day, hour,     |                                |
    |     gender, isLunar }           |                                |
    |                                 |-- 캐시 확인 ------------------>|
    |                                 |   saju_cache[natal:hash]       |
    |                                 |                                |
    |                                 |   [캐시 미스]                   |
    |                                 |-- POST /api/v1/unified/ ------>|
    |                                 |   complete-analysis            |
    |                                 |<-- 원국 데이터 (JSON) ---------|
    |                                 |                                |
    |                                 |-- 캐시 저장 (영구) ----------->|
    |                                 |   saju_cache                   |
    |                                 |                                |
    |<-- NatalResult (JSON) ----------|                                |
    |                                 |                                |
    |-- [클라이언트에서 콘텐츠 조립] --|                                |
    |   assembleNatalReport()         |                                |
    |   (줄글DB + B톤 변환)           |                                |
```

**UI 컴포넌트 트리:**

```tsx
<ProductLayout product={products.natal} expert="B">
  {step === 'input' && (
    <BirthInput
      onSubmit={handleSubmit}
      showPartner={false}
    />
  )}

  {step === 'loading' && (
    <LoadingOverlay message="사주를 불러오는 중..." />
  )}

  {step === 'result' && (
    <>
      <ExpertBadge expert="B" message="동네형이 봐줄게" />

      <PillarDisplay
        pillars={natal.four_pillars}
        hiddenStems={natal.hidden_stems}
      />

      <WuxingRadar data={natal.wuxing} />

      <ResultRenderer
        sections={content.sections}
        expert="B"
      />

      <ShareButton
        title="내 사주 원국"
        description={content.summary}
      />

      <ProductCTA
        target="yearly"
        label="올해 운세도 볼래?"
      />
    </>
  )}
</ProductLayout>
```

**줄글 조립 로직:**

```typescript
// lib/content/templates/natal-report.ts
import murakimiDb from '@/lib/saju/murakami-db.json';
import type { NatalResult } from '@/types/yongsin';

interface NatalSection {
  id: string;
  title: string;
  body: string;
  highlight?: string;
}

export function assembleNatalContent(
  natal: NatalResult,
  name: string,
  lang: 'ko' | 'vi'
): NatalSection[] {
  const ilganKey = getIlganKey(natal.four_pillars.day.stem);
  const ilganData = murakimiDb.ilgan[ilganKey as keyof typeof murakimiDb.ilgan];

  const sections: NatalSection[] = [];

  // 섹션 1: "너는 이런 사람이야" — 일간 성격
  const opening = ilganData.opening.replace(/{P}/g, name);
  sections.push({
    id: 'personality',
    title: lang === 'ko' ? '너는 이런 사람이야' : 'Ban la nguoi nhu the nay',
    body: toNeighborTone(opening + '\n\n' + ilganData.nature, lang),
  });

  // 섹션 2: 약점 (솔직하지만 따뜻하게)
  sections.push({
    id: 'weakness',
    title: lang === 'ko' ? '근데 이것만 조심해' : 'Nhung hay can than dieu nay',
    body: toNeighborTone(ilganData.weakness, lang),
  });

  // 섹션 3: 오행 밸런스
  const wuxing = natal.wuxing;
  const dominant = getDominantElement(wuxing);
  const weak = getWeakElement(wuxing);
  sections.push({
    id: 'wuxing',
    title: lang === 'ko' ? '오행 밸런스' : 'Can bang ngu hanh',
    body: formatWuxingNeighborTone(dominant, weak, name, lang),
    highlight: lang === 'ko'
      ? `${ELEMENT_NAMES[dominant]}이 강하고, ${ELEMENT_NAMES[weak]}이 부족해`
      : `${ELEMENT_NAMES_VI[dominant]} manh, ${ELEMENT_NAMES_VI[weak]} yeu`,
  });

  // 섹션 4: 마무리
  sections.push({
    id: 'closing',
    title: lang === 'ko' ? '정리하면' : 'Tom lai',
    body: toNeighborTone(ilganData.closing, lang),
  });

  return sections;
}

// B톤 변환: 하루키 → 동네형
function toNeighborTone(text: string, lang: 'ko' | 'vi'): string {
  if (lang !== 'ko') return text; // 베트남어는 별도 처리

  return text
    // 존댓말 → 반말
    .replace(/입니다/g, '이야')
    .replace(/합니다/g, '해')
    .replace(/~였다\./g, '~이야.')
    .replace(/것이다\./g, '거야.')
    .replace(/모른다\./g, '몰라.')
    .replace(/않는다\./g, '않아.')
    // 하루키 문체 → 캐주얼
    .replace(/그것은 마치/g, '이게 딱')
    .replace(/~일지도 모른다/g, '~일 수도 있어')
    .replace(/~라고 말할 수 있을지도 모른다/g, '~라고 할 수 있지');
}

function formatWuxingNeighborTone(
  dominant: string,
  weak: string,
  name: string,
  lang: 'ko' | 'vi'
): string {
  if (lang === 'ko') {
    const advice = WUXING_ADVICE[weak as keyof typeof WUXING_ADVICE];
    return `${name}아, 네 오행을 보면 ${ELEMENT_NAMES[dominant]}이 확실히 강해. ` +
      `${ELEMENT_NAMES[weak]}이 좀 부족한 편인데, ` +
      `${advice}\n\n` +
      `걱정 마. 부족하다고 나쁜 게 아니야. ` +
      `그냥 알고 있으면 챙길 수 있으니까.`;
  }
  return ''; // vi 처리
}

const WUXING_ADVICE = {
  '목': '봄에 나무 많은 데 가봐. 녹색 계열 옷도 괜찮아.',
  '화': '따뜻한 거 먹어. 빨간색 소품 하나 갖고 다녀. 남쪽이 좋아.',
  '토': '맨발로 흙 밟아봐. 노란색, 갈색 계열이 너한테 좋아.',
  '금': '금속 액세서리 하나 해. 서쪽 방향이 좋아.',
  '수': '물 많이 마셔 (진심). 검정색 계열이 너를 안정시켜줘.',
};
```

### 5.2 상품 2: 오늘의 운세

**상품 정보:**
- 코드: `daily`
- 전문가: B 동네형
- 가격: 무료
- API: `/api/layer6/timing/personal/today` + `/api/today/weather`
- 캐시: 24시간

**페이지 구조:**

```
/[locale]/products/daily
├── [저장된 사주 있으면] → 바로 결과
├── [없으면] → BirthInput → 결과
│
└── [결과 화면]
    ├── [헤더] 날짜 + "오늘의 운세" + ExpertBadge("B")
    │
    ├── [핵심 한 줄]
    │   - 큰 글씨 카드 형태
    │   - "오늘은 좀 쉬어가는 날이야"
    │
    ├── [분야별 운세] (탭 또는 아코디언)
    │   ├── 연애: 점수 + 한 줄 + 조언
    │   ├── 직업: 점수 + 한 줄 + 조언
    │   ├── 재물: 점수 + 한 줄 + 조언
    │   └── 건강: 점수 + 한 줄 + 조언
    │
    ├── [오늘의 행운]
    │   - 행운 색, 숫자, 방향, 시간대
    │   - 카드 형태 (공유 가능)
    │
    ├── [오늘의 한 마디] (B톤 마무리)
    │
    └── [하단CTA]
        ├── "12시진 시간표 보기 → P2-11"
        └── "올해 전체 흐름 보기 → P1-6"
```

**API 호출 흐름:**

```
클라이언트 → POST /api/v1/saju/fortune/daily
  서버 → 캐시 확인 (daily:{hash}:{today})
    [미스] → YongSin /api/layer6/timing/personal/today
          → YongSin /api/today/weather
          → 병렬 호출, 결과 합성
          → 캐시 저장 (TTL: 24h)
  ← DailyFortuneResult
```

**줄글 조립 로직:**

```typescript
// lib/content/templates/daily-fortune.ts
export function assembleDailyContent(
  daily: DailyFortuneResult,
  weather: WeatherResult,
  name: string,
  lang: 'ko' | 'vi'
): DailySection[] {
  const sections: DailySection[] = [];

  // 핵심 한 줄
  sections.push({
    id: 'headline',
    title: '',
    body: toDailyNeighborTone(daily.today_summary, name, lang),
    style: 'highlight',
  });

  // 분야별 운세 (4개)
  const areas = ['love', 'career', 'wealth', 'health'] as const;
  for (const area of areas) {
    const fortune = daily.areas[area];
    sections.push({
      id: area,
      title: AREA_NAMES[area][lang],
      body: toNeighborTone(fortune.description, lang),
      score: fortune.score,
      advice: fortune.advice,
    });
  }

  // 행운 정보
  sections.push({
    id: 'lucky',
    title: lang === 'ko' ? '오늘의 행운' : 'May man hom nay',
    body: '',
    lucky: {
      color: weather.lucky_color,
      number: weather.lucky_number,
      direction: weather.lucky_direction,
      time: weather.best_time,
    },
  });

  // 마무리
  sections.push({
    id: 'closing',
    title: '',
    body: lang === 'ko'
      ? `${name}아, 오늘 하루도 잘 보내. 내일 또 봐!`
      : `${name} oi, chuc mot ngay tot lanh nhe!`,
    style: 'closing',
  });

  return sections;
}
```

### 5.3 상품 3: 명궁 분석 (사주 MBTI)

**상품 정보:**
- 코드: `myeong-gung`
- 전문가: B 동네형
- 가격: 무료
- API: `/api/v1/unified/complete-analysis` (natal 응답에서 myeong_gung 추출)
- 캐시: 영구 (원국 기반)

**페이지 구조:**

```
/[locale]/products/myeong-gung
├── [입력] BirthInput
│
└── [결과]
    ├── [카드 영웅] 유형 카드 형태
    │   - 큰 유형 이름: "갑목 정인형" (MBTI의 INFJ 같은 느낌)
    │   - 한 줄 소개: "방향이 있는 학자"
    │   - 컬러 배경 (일간 오행색)
    │
    ├── [유형 해설] B톤
    │   - "너는 갑목이면서 정인이 강한 사람이야."
    │   - "쉽게 말하면, 방향도 있고 머리도 좋은 타입."
    │   - 3~4문단
    │
    ├── [강점 / 약점] 카드 2장
    │   - 강점 3개 (아이콘 + 한 줄)
    │   - 약점 3개 (아이콘 + 한 줄)
    │
    ├── [잘 맞는 유형] 궁합 미리보기
    │   - "너랑 잘 맞는 사람은 을목 식신형이야"
    │   - → 궁합 리포트 CTA
    │
    └── [공유] "내 유형 공유하기" (바이럴)
```

**줄글 조립 로직:**

```typescript
// lib/content/templates/myeong-gung.ts
export function assembleMyeongGungContent(
  natal: NatalResult,
  name: string,
  lang: 'ko' | 'vi'
): MyeongGungContent {
  const ilganKey = getIlganKey(natal.four_pillars.day.stem);
  const dominantTenGod = getDominantTenGod(natal.ten_gods);
  const typeCode = `${ilganKey}_${dominantTenGod}`;

  // 사전 정의된 60가지 유형 (10일간 x 6십신그룹)
  const typeData = MYEONG_GUNG_TYPES[typeCode];

  return {
    typeCode,
    typeName: typeData.name[lang],
    typeSubtitle: typeData.subtitle[lang],
    description: formatNeighborTone(typeData.description, name, lang),
    strengths: typeData.strengths.map(s => ({
      icon: s.icon,
      text: s[lang],
    })),
    weaknesses: typeData.weaknesses.map(w => ({
      icon: w.icon,
      text: w[lang],
    })),
    compatType: typeData.bestMatch,
    element: natal.four_pillars.day.stem.element,
    shareImage: `/og/myeong-gung/${typeCode}.png`,
  };
}

// 유형 데이터 예시 (60종)
const MYEONG_GUNG_TYPES: Record<string, MyeongGungType> = {
  'gap_jeong-in': {
    name: { ko: '갑목 정인형', vi: 'Giap Moc Chinh An' },
    subtitle: { ko: '방향이 있는 학자', vi: 'Hoc gia co dinh huong' },
    description: {
      ko: '큰 나무가 책을 품고 있는 모양이야. 넌 기본적으로 방향이 뚜렷한 사람인데, 거기에 정인의 지적 호기심이 더해져 있어. 배우는 걸 좋아하고, 배운 걸 정리하는 것도 잘해. 근데 가끔 머리로만 살려고 하는 경향이 있어. 몸도 좀 써.',
      vi: '...',
    },
    strengths: [
      { icon: 'brain', ko: '분석력과 판단력이 뛰어나', vi: '...' },
      { icon: 'target', ko: '목표가 명확하고 흔들리지 않아', vi: '...' },
      { icon: 'book', ko: '지적 호기심이 강해', vi: '...' },
    ],
    weaknesses: [
      { icon: 'stubborn', ko: '한번 정하면 잘 안 바꿔', vi: '...' },
      { icon: 'alone', ko: '혼자 결정하려는 경향이 있어', vi: '...' },
      { icon: 'overthink', ko: '생각이 너무 많을 때가 있어', vi: '...' },
    ],
    bestMatch: 'eul_sig-sin',
  },
  // ... 59개 더
};
```

### 5.4 상품 4: 날씨 카드 (SNS 공유)

**상품 정보:**
- 코드: `weather-card`
- 전문가: B 동네형
- 가격: 무료
- API: `/api/today/weather` + `/api/today/action-item`
- 캐시: 24시간

**페이지 구조:**

```
/[locale]/products/weather-card
├── [입력] BirthInput (간소화 — 이름, 생년월일만)
│
└── [결과]
    ├── [메인 카드] (16:9 비율, 공유 최적화)
    │   ├── 배경: 날씨 기반 그라디언트
    │   │   - 맑음: 파랑→노랑, 흐림: 회색→남색, 비: 남색→보라
    │   │   - 태풍: 빨강→검정, 눈: 하양→파랑
    │   ├── 중앙: 날씨 아이콘 (큰 이모지 또는 SVG)
    │   ├── 텍스트: "오늘 {이름}의 사주 날씨"
    │   ├── 한 줄: "바람이 살살 부는 날이야"
    │   └── 하단: 행운색 / 행운숫자 / 행운방향
    │
    ├── [상세] B톤 해설
    │   - "오늘 네 사주에 불기운이 좀 세게 들어와서..."
    │   - 3~4줄
    │
    ├── [액션 아이템]
    │   - "오전에 중요한 일 처리해"
    │   - "점심은 따뜻한 거 먹어"
    │   - "저녁에는 산책 추천"
    │
    └── [공유]
        ├── "카카오톡으로 공유" (카드 이미지)
        ├── "인스타 스토리" (카드 이미지)
        └── "링크 복사"
```

**카드 생성:**

```typescript
// lib/content/templates/weather-card.ts
export function assembleWeatherCard(
  weather: WeatherResult,
  action: ActionResult,
  name: string,
  lang: 'ko' | 'vi'
): WeatherCardContent {
  const weatherType = classifyWeather(weather);

  return {
    // 카드 렌더링 데이터
    card: {
      background: WEATHER_GRADIENTS[weatherType],
      icon: WEATHER_ICONS[weatherType],
      title: lang === 'ko'
        ? `오늘 ${name}의 사주 날씨`
        : `Thoi tiet tu tru hom nay cua ${name}`,
      headline: toNeighborTone(weather.headline, lang),
      lucky: {
        color: weather.lucky_color,
        number: weather.lucky_number,
        direction: weather.lucky_direction,
      },
      date: formatDate(new Date(), lang),
    },

    // 상세 해설
    description: toNeighborTone(weather.description, lang),

    // 액션 아이템 (3개)
    actions: action.items.slice(0, 3).map(item => ({
      time: item.time_label,
      text: toNeighborTone(item.description, lang),
    })),
  };
}

const WEATHER_GRADIENTS: Record<string, string> = {
  sunny: 'linear-gradient(135deg, #74b9ff, #fdcb6e)',
  cloudy: 'linear-gradient(135deg, #b2bec3, #2d3436)',
  rainy: 'linear-gradient(135deg, #6c5ce7, #a29bfe)',
  stormy: 'linear-gradient(135deg, #d63031, #2d3436)',
  snowy: 'linear-gradient(135deg, #dfe6e9, #74b9ff)',
  windy: 'linear-gradient(135deg, #00cec9, #81ecec)',
};

const WEATHER_ICONS: Record<string, string> = {
  sunny: 'Sun',      // lucide-react icon name
  cloudy: 'Cloud',
  rainy: 'CloudRain',
  stormy: 'CloudLightning',
  snowy: 'Snowflake',
  windy: 'Wind',
};
```

### 5.5 상품 5: MBTI형 유형 카드 (바이럴)

**상품 정보:**
- 코드: `type-card`
- 전문가: B 동네형
- 가격: 무료
- API: `/api/v1/unified/complete-analysis` (원국에서 유형 추출)
- 캐시: 영구

**페이지 구조:**

```
/[locale]/products/type-card
├── [입력] BirthInput (간소화)
│
└── [결과]
    ├── [유형 카드] (1:1 정사각형, 인스타 최적화)
    │   ├── 배경: 오행 기반 그라디언트
    │   ├── 유형 코드: "갑목-정인" (큰 글씨)
    │   ├── 유형 별명: "조용한 지휘자" (서브 타이틀)
    │   ├── 키워드 태그: #방향감 #학구파 #고집
    │   └── 하단: "MENh 사주 유형 카드"
    │
    ├── [유형 해설] B톤 (짧게, 3문장)
    │   - "넌 갑목-정인이야."
    │   - "큰 나무가 책을 안고 있는 모양이지."
    │   - "방향도 있고, 공부도 좋아하는 타입."
    │
    ├── [유형 비교] (스와이프)
    │   - "같은 유형 유명인: 000"
    │   - "상극 유형: 경금-겁재"
    │   - "환상 궁합: 을목-식신"
    │
    ├── [다른 유형 탐색]
    │   - 10개 일간 유형 미니 카드 그리드
    │   - 각각 클릭하면 해당 유형 설명
    │
    └── [공유]
        ├── "내 유형 카드 공유하기" (1:1 이미지)
        ├── "친구 유형 알아보기" (링크 공유)
        └── "바이럴 문구: 나는 [유형]이래. 너는?"
```

**유형 생성 로직:**

```typescript
// lib/content/templates/type-card.ts
export function assembleTypeCard(
  natal: NatalResult,
  name: string,
  lang: 'ko' | 'vi'
): TypeCardContent {
  const ilgan = natal.four_pillars.day.stem;
  const ilganKey = getIlganKey(ilgan);
  const dominantTenGod = getDominantTenGod(natal.ten_gods);
  const typeCode = `${ilganKey}_${dominantTenGod}`;
  const typeData = SAJU_TYPES[typeCode];

  return {
    card: {
      background: ELEMENT_GRADIENTS[ilgan.element],
      typeCode,
      typeName: typeData.name[lang],
      nickname: typeData.nickname[lang],
      keywords: typeData.keywords[lang],
      brandWatermark: 'MENh',
    },
    description: toNeighborToneShort(typeData.shortDesc, name, lang),
    celebrity: typeData.celebrity?.[lang] || null,
    oppositeType: typeData.opposite,
    bestMatchType: typeData.bestMatch,
    allTypes: getAllTypeCards(lang),  // 10개 간략 버전
  };
}

// 유형 데이터 (발췌)
const SAJU_TYPES: Record<string, SajuType> = {
  'gap_jeong-in': {
    name: { ko: '갑목-정인', vi: 'Giap Moc-Chinh An' },
    nickname: { ko: '조용한 지휘자', vi: 'Chi huy tham lang' },
    keywords: { ko: ['방향감', '학구파', '고집'], vi: ['Dinh huong', 'Hoc gia', 'Co chap'] },
    shortDesc: {
      ko: '큰 나무가 책을 안고 있는 모양이야. 방향도 있고, 공부도 좋아하는 타입. 근데 가끔 너무 혼자 결정하려고 해.',
      vi: '...',
    },
    opposite: 'gyeong_geob-jae',
    bestMatch: 'eul_sig-sin',
  },
  // ... 59종 더
};

const ELEMENT_GRADIENTS: Record<string, string> = {
  '목': 'linear-gradient(135deg, #00b894, #00cec9)',
  '화': 'linear-gradient(135deg, #e17055, #fdcb6e)',
  '토': 'linear-gradient(135deg, #fab1a0, #ffeaa7)',
  '금': 'linear-gradient(135deg, #b2bec3, #dfe6e9)',
  '수': 'linear-gradient(135deg, #0984e3, #6c5ce7)',
};
```

---

## 부록 A: 환경변수 (.env.local)

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# YongSin API
YONGSIN_API_URL=https://dev-yongsin.laimalabs.com
YONGSIN_API_KEY=ys_xxx

# Claude (LLM — P1+ 유료 상품용)
ANTHROPIC_API_KEY=sk-ant-xxx

# PortOne (결제 — P1+ 유료 상품용)
PORTONE_API_KEY=xxx
PORTONE_STORE_ID=xxx
NEXT_PUBLIC_PORTONE_STORE_ID=xxx

# 앱
NEXT_PUBLIC_APP_URL=https://menh.app
```

## 부록 B: 추가 패키지

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.60.0",
    "@anthropic-ai/sdk": "^0.39.0",
    "html-to-image": "^1.11.0"
  },
  "devDependencies": {
    "@portone/browser-sdk": "^2.0.0"
  }
}
```

## 부록 C: 20개 상품 × API 매핑 요약표

| # | 상품 | 코드 | 전문가 | Tier | YongSin API | 캐시 TTL |
|---|------|------|--------|------|-------------|----------|
| 1 | 원국 리포트 | natal | B | free | unified/complete-analysis | 영구 |
| 2 | 오늘의 운세 | daily | B | free | layer6/personal/today + today/weather | 24h |
| 3 | 명궁 분석 | myeong-gung | B | free | unified (myeong_gung) | 영구 |
| 4 | 날씨 카드 | weather-card | B | free | today/weather + today/action-item | 24h |
| 5 | MBTI형 유형 카드 | type-card | B | free | unified (natal + ten_gods) | 영구 |
| 6 | 올해 운세 종합 | yearly | A | paid | layer4/comprehensive | 365d |
| 7 | 궁합 리포트 | compat | E | paid | layer5 | 영구 |
| 8 | 결혼 택일 | wedding-date | G+E | paid | layer6/taegil + layer5 | 90d |
| 9 | 용신 분석 | yongsin | I | paid | unified (yongsin_analysis) | 영구 |
| 10 | 4축 성격 분석 | four-axis | L | paid | layer7/four-axis/all | 영구 |
| 11 | 12시진 시간별 운세 | hourly | H | sub | layer6/personal/hourly | 24h |
| 12 | 오늘 경고 알림 | warning | G | sub | today/warnings | 24h |
| 13 | 매일 한 줄 운세 | daily-tip | K | sub | today/action-item | 24h |
| 14 | 행운 처방 카드 | lucky-card | J | sub | today/lucky_prescriptions | 24h |
| 15 | 관계 신호등 | relationship | E | sub | layer6/relationship-lights | 24h |
| 16 | 인생 소설 | life-novel | A | premium | unified + seun/history | 영구 |
| 17 | 황금 시기 리포트 | golden-period | H | premium | prime-periods + daeun/lifetime | 영구 |
| 18 | 창업 타이밍 분석 | startup-timing | C | premium | strategy + wealth-timing | 365d |
| 19 | 생애 주기 타임라인 | life-cycle | A | premium | life-cycle + daeun/lifetime | 영구 |
| 20 | 꿈 해석 | dream | G | premium | layer8/dream-interpret | 1회성 |

---

## 문서 이력

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-28 | 20개 상품 기술 아키텍처 + P0 구현 스펙 초안 |
