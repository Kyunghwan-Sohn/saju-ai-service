# MỆnh Next.js Migration Plan

> **Version:** 1.0
> **Date:** 2026-03-26
> **Author:** CTO Lead
> **Status:** Draft
> **Based on:** PRD v1.0, Frontend Review v1.0, 3-Agent Review Findings, MVP Roadmap v1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Technology Stack Decision](#3-technology-stack-decision)
4. [Project Structure Design](#4-project-structure-design)
5. [Migration Strategy](#5-migration-strategy)
6. [Agent Review Findings Resolution](#6-agent-review-findings-resolution)
7. [MVP Scope (8 Weeks)](#7-mvp-scope-8-weeks)
8. [Risk & Mitigation](#8-risk--mitigation)

---

## 1. Executive Summary

### 1.1 Migration Goal

바닐라 HTML/CSS/JS 기반 "MỆnh" 사주 서비스를 Next.js 15 App Router 기반으로 마이그레이션한다. 기존 사주 계산 엔진(`saju-engine.js`, 8/8 정확도 검증 완료)과 DB JSON(v1 7,150개 + v2 49개 샘플)을 최대한 재활용하면서, 3개 에이전트 검토에서 발견된 8가지 핵심 이슈를 체계적으로 해결한다.

### 1.2 Why Migrate?

| 현행 한계 | Next.js 해결 |
|-----------|-------------|
| 단일 HTML에 7개 화면 `display:none/block` 전환 | App Router 파일 기반 라우팅, URL history 지원 |
| URL 미변경으로 Android 뒤로가기 불가 | 자동 URL 라우팅 + `useRouter` |
| i18n 체계 부재 (data-ko/data-vi 수동 전환) | next-intl 기반 체계적 i18n |
| 전역 CSS 단일 파일, 디자인 토큰 분리 불가 | Tailwind CSS 유틸리티 + CSS 변수 토큰 |
| 상태관리 전역 변수 (`let saju = null`) | Zustand 스토어 + TypeScript 타입 안전 |
| SEO/OG 메타 태그 부재 | Next.js Metadata API |
| PWA manifest 부재 | next-pwa 또는 수동 manifest 설정 |
| 정적 이모지 아이콘 | SVG 컴포넌트 기반 아이콘 시스템 |

### 1.3 Core Principles

1. **엔진 재활용 극대화** -- `saju-engine.js`의 로직을 TypeScript로 1:1 포팅, 기존 테스트 케이스 전체 통과 필수
2. **DB JSON 무변경 사용** -- v2 JSON 파일을 `public/data/` 또는 직접 import로 그대로 활용
3. **점진적 마이그레이션** -- 화면 단위로 하나씩 이전, 전체 동시 전환 금지
4. **Mobile-First** -- 360px~440px 최적화 우선, 태블릿/데스크톱은 스케일업

---

## 2. Current State Analysis

### 2.1 File Inventory

| 파일 | 크기 | 역할 | 마이그레이션 전략 |
|------|------|------|------------------|
| `web/js/saju-engine.js` | 275 lines | 사주팔자 계산 엔진 (년/월/일/시주, 오행, 십성) | TS 포팅 (1:1 변환) |
| `web/js/app.js` | 474 lines | UI 렌더링 + 이벤트 핸들링 + 라우팅 | React 컴포넌트로 분해 |
| `web/css/style.css` | 204 lines | 전역 스타일 | Tailwind + CSS 변수 재설계 |
| `web/index.html` | 147 lines | 7개 화면 단일 HTML | App Router 페이지 분리 |
| `web/data/saju-db-v2.js` | ~10K tokens | v2 5카드 DB (49개 샘플) | JSON import로 변환 |
| `web/data/saju-db.js` | ~3.16M tokens | v1 프리미엄 DB (7,150개) | 그대로 활용 또는 lazy load |
| `saju-db-v2/output/*.json` | 6 files | v2 원본 JSON (index + 5 테이블) | 직접 import |

### 2.2 Engine Analysis (saju-engine.js)

**재활용 가능 핵심 함수:**

| 함수 | 라인 | 의존성 | TS 변환 난이도 |
|------|------|--------|---------------|
| `calculateSaju()` | 167-187 | 모든 calc* 함수 | 낮음 |
| `calcDayPillar()` | 57-63 | STEMS, BRANCHES, REF_DATE | 낮음 |
| `calcYearPillar()` | 68-76 | STEMS, BRANCHES | 낮음 |
| `calcMonthPillar()` | 99-111 | STEMS, BRANCHES, getMonthBranch | 낮음 |
| `calcHourPillar()` | 116-139 | STEMS, BRANCHES | 낮음 |
| `calcFiveElements()` | 144-150 | 없음 | 낮음 |
| `getTenGod()` | 209-260 | STEMS | 중간 (반환 타입 복잡) |
| `getTodayFortune()` | 192-206 | calc* 함수들 | 낮음 |

**재활용 가능 상수:**

- `STEMS` (10 천간) -- 한자/한국어/key/오행/음양 포함
- `BRANCHES` (12 지지) -- 한자/한국어/key/동물/오행/이모지 포함
- `ELEMENT_COLORS` (5 오행 색상) -- bg/text/accent/name/vi 포함
- `LIFE_AREAS` (10 영역) -- icon/ko/vi/category 포함

**비재활용 (재작성 필요):**

- `go()` 함수 -- HTML display 전환 로직, Next.js router로 대체
- `renderHome()`, `renderFortune()`, `renderMiniPillars()` -- DOM 조작, React 컴포넌트로 대체
- `startTopic()`, `showFollowUp()`, `pickFollow()` -- DOM 조작, React state + 컴포넌트로 대체
- `runCompat()` -- DOM 조작 부분만 대체, 계산 로직은 유지
- `updateLang()` -- data-ko/data-vi 수동 전환, next-intl로 대체

### 2.3 DB Structure

**v2 DB (5카드 시스템):**

```
saju-db-v2/output/
  index.json          -- 메타데이터 (테이블 정의, 카운트)
  01_intro.json       -- 상황x일간 공감 카드 (target: 50, current: 5)
  02_ilgan.json       -- 일간x상황 성격 카드 (target: 50, current: 5)
  03_combo.json       -- 일간x월지 시기 카드 (target: 120, current: 4)
  04_today.json       -- 갑자인덱스x요일 오늘 한줄 (target: 420, current: 10)
  05_cheer.json       -- 상황x오행 응원 카드 (target: 25, current: 25)
```

키 패턴: `{situation}_{ilgan}`, `{ilgan}_{wolji}`, `{gapja_index}_{weekday}`

**v1 DB (7,150 레코드):** `SAJU_DB` 객체로 `ilgan_combo` 키 구조, 각 엔트리에 `versions[]` 배열 (카테고리별 한/베 텍스트).

---

## 3. Technology Stack Decision

### 3.1 Core Stack

| Category | Technology | Version | Rationale |
|----------|-----------|---------|-----------|
| **Framework** | Next.js | 15.x | App Router, Server Components, Metadata API |
| **Language** | TypeScript | 5.x | 사주 엔진 타입 안전성, 개발 생산성 |
| **Styling** | Tailwind CSS | 4.x | 유틸리티 퍼스트, 디자인 토큰 CSS 변수 통합 |
| **State** | Zustand | 5.x | 경량, TypeScript 친화, 사주 상태 persist |
| **i18n** | next-intl | 4.x | App Router 네이티브, 메시지 번들, 라우팅 통합 |
| **Animation** | Framer Motion | 12.x | 페이지 전환, 카드 등장, 제스처 |
| **Icons** | Custom SVG + Lucide React | - | 이모지 대체, 트리 셰이킹 지원 |

### 3.2 Development Tools

| Category | Technology | Rationale |
|----------|-----------|-----------|
| **Linting** | ESLint + Prettier | Next.js 기본 ESLint 규칙 + Prettier 포매팅 |
| **Testing** | Vitest + Testing Library | 사주 엔진 유닛 테스트, 컴포넌트 테스트 |
| **E2E** | Playwright | 크로스브라우저 테스트, 모바일 뷰포트 |
| **Bundler** | Turbopack | Next.js 15 기본 dev 서버 번들러 |

### 3.3 Stack Decision Rationale

**왜 Zustand인가 (vs Context)?**

- 사주 결과(`saju` 객체)를 여러 페이지에서 공유해야 함 (홈/주제/운세/궁합)
- `persist` 미들웨어로 localStorage 자동 저장 -- 새로고침 시에도 사주 데이터 유지
- Context는 Provider 중첩 + 리렌더 최적화에 보일러플레이트 과다
- 사주 상태, 언어 설정, 테마(다크모드) 3개 스토어로 분리

**왜 next-intl인가 (vs 커스텀)?**

- App Router의 `[locale]` 세그먼트와 자연스러운 통합
- 메시지 번들 JSON으로 번역 키 관리 (현행 `data-ko`/`data-vi` 인라인 방식 탈피)
- ICU 메시지 포맷 지원 (복수형, 날짜 포맷팅 등)
- 베트남어 45% 누락을 체계적으로 관리 가능 (키 기반 누락 탐지)

**왜 Framer Motion인가?**

- 현행 `@keyframes fadeUp` 한 가지뿐인 애니메이션을 카드 슬라이드업, 페이지 전환, 선택지 등장 등으로 확장
- `AnimatePresence`로 라우트 전환 애니메이션
- `useMotionValue` + `useTransform`으로 인터랙티브 카드 효과
- 베트남 MZ 타겟 앱의 기대 수준에 부합하는 모션 경험

---

## 4. Project Structure Design

### 4.1 Directory Structure (App Router)

```
next-app/
  public/
    data/                          # v2 JSON DB (정적 서빙)
      01_intro.json
      02_ilgan.json
      03_combo.json
      04_today.json
      05_cheer.json
      index.json
    icons/                         # SVG 아이콘 에셋
      elements/                    # 오행 아이콘 (wood/fire/earth/metal/water)
      topics/                      # 주제 아이콘 (love/career/money/self/compat/general)
      nav/                         # 바텀 네비 아이콘
      util/                        # 유틸리티 아이콘
    images/                        # 일러스트레이션, OG 이미지
    manifest.json                  # PWA manifest
    sw.js                          # Service Worker (PWA)
  src/
    app/
      [locale]/                    # i18n 라우팅 (ko, vi)
        layout.tsx                 # 루트 레이아웃 (폰트, 테마, 네비)
        page.tsx                   # / (홈: 오늘의 한줄 + 주제 그리드 + 운세 바로가기)
        input/
          page.tsx                 # /input (생년월일 입력 -- 최초 1회)
        topic/
          [id]/
            page.tsx               # /topic/[id] (대화형 Q&A: love/career/money/self/general)
        fortune/
          daily/
            page.tsx               # /fortune/daily (일운)
          monthly/
            page.tsx               # /fortune/monthly (월운)
          yearly/
            page.tsx               # /fortune/yearly (년운)
        compat/
          page.tsx                 # /compat (궁합)
        not-found.tsx              # 404 페이지
        error.tsx                  # 에러 페이지
        loading.tsx                # 글로벌 로딩 UI
      globals.css                  # Tailwind 디렉티브 + CSS 변수 토큰
      layout.tsx                   # 최상위 레이아웃 (html lang 설정)
    lib/
      saju/
        engine.ts                  # saju-engine.js TS 포팅 (핵심 계산)
        types.ts                   # Stem, Branch, Pillar, SajuResult 타입
        constants.ts               # STEMS, BRANCHES, ELEMENT_COLORS 상수
        ten-gods.ts                # 십성(十星) 계산 로직
        fortune.ts                 # 일/월/년운 계산 로직
        compatibility.ts           # 궁합 계산 로직
        __tests__/
          engine.test.ts           # 8/8 검증 재현 + 확장 테스트
          ten-gods.test.ts
          fortune.test.ts
      db/
        loader.ts                  # DB JSON 로딩 유틸리티
        types.ts                   # IntroCard, IlganCard 등 DB 레코드 타입
        v1-adapter.ts              # v1 SAJU_DB 어댑터
      i18n/
        config.ts                  # next-intl 설정
        request.ts                 # getRequestConfig
      utils/
        lunar-calendar.ts          # 음력 변환 라이브러리 연동
        date.ts                    # 날짜 유틸리티
    components/
      ui/                          # 범용 UI 컴포넌트
        Button.tsx
        Card.tsx
        Input.tsx
        Select.tsx
        Badge.tsx
        Skeleton.tsx
        Loading.tsx                # 로딩 상태 (Lottie/CSS)
        EmptyState.tsx             # 빈 상태 UI
        ErrorState.tsx             # 에러 상태 UI
      saju/                        # 사주 도메인 컴포넌트
        PillarDisplay.tsx          # 사주 기둥 표시 (한자 + 오행 색상)
        FiveElementChart.tsx       # 오행 분포 차트
        ElementBadge.tsx           # 오행 뱃지
        FortuneScoreBar.tsx        # 영역별 운세 점수 바
        CompatScore.tsx            # 궁합 점수 원형 표시
      topic/                       # 대화형 Q&A 컴포넌트
        TopicCard.tsx              # 카드 (intro/ilgan/combo/today/cheer)
        FollowUpQuestion.tsx       # 후속 질문 선택지
        TopicFlow.tsx              # 대화 플로우 컨테이너
      layout/                      # 레이아웃 컴포넌트
        Header.tsx                 # 앱 헤더
        BottomNav.tsx              # 바텀 네비게이션 (5탭)
        TopicGrid.tsx              # 주제 선택 그리드
        FortuneQuickAccess.tsx     # 운세 바로가기 (일/월/년)
      input/                       # 입력 관련 컴포넌트
        BirthDateForm.tsx          # 생년월일 입력 폼
        LunarToggle.tsx            # 양력/음력 전환
        GenderSelect.tsx           # 성별 선택
        HourSelect.tsx             # 출생 시간 선택
      icons/                       # SVG 아이콘 컴포넌트
        ElementIcon.tsx            # 오행 아이콘 (props로 원소 지정)
        TopicIcon.tsx              # 주제 아이콘
    stores/
      saju-store.ts               # Zustand: 사주 결과, 사용자 프로필
      theme-store.ts              # Zustand: 다크/라이트 모드
      topic-store.ts              # Zustand: 대화형 Q&A 상태
    hooks/
      useSaju.ts                   # 사주 계산 + 스토어 연동
      useFortune.ts                # 운세 계산 훅
      useTopicFlow.ts              # 대화형 Q&A 플로우 관리
      useCompat.ts                 # 궁합 계산 훅
    messages/                      # i18n 메시지 번들
      ko.json                     # 한국어 전체 번역
      vi.json                     # 베트남어 전체 번역
    styles/
      tokens.css                   # 디자인 토큰 (컬러, 타이포, 스페이싱)
      dark.css                     # 다크모드 토큰 오버라이드
```

### 4.2 Route Map

| URL Pattern | 페이지 | 컴포넌트 | 설명 |
|-------------|--------|----------|------|
| `/[locale]` | `page.tsx` | HomePage | 홈: 오늘의 한줄 + 주제 그리드 + 운세 바로가기 |
| `/[locale]/input` | `input/page.tsx` | InputPage | 생년월일 입력 (최초 1회, 이후 자동 리다이렉트) |
| `/[locale]/topic/[id]` | `topic/[id]/page.tsx` | TopicPage | 대화형 Q&A (id: love/career/money/self/general) |
| `/[locale]/fortune/daily` | `fortune/daily/page.tsx` | DailyPage | 일운 |
| `/[locale]/fortune/monthly` | `fortune/monthly/page.tsx` | MonthlyPage | 월운 |
| `/[locale]/fortune/yearly` | `fortune/yearly/page.tsx` | YearlyPage | 년운 |
| `/[locale]/compat` | `compat/page.tsx` | CompatPage | 궁합 |

**URL 예시:**
- 한국어: `/ko`, `/ko/topic/love`, `/ko/fortune/daily`
- 베트남어: `/vi`, `/vi/topic/career`, `/vi/compat`

### 4.3 Redirect Logic

```
사용자 첫 방문 → /[locale]/input (사주 데이터 없음)
사주 입력 완료 → /[locale] (홈으로 리다이렉트)
재방문 (localStorage에 사주 있음) → /[locale] (홈 직행)
```

미들웨어(`middleware.ts`)에서 locale prefix 없는 접근을 브라우저 Accept-Language 기반으로 자동 리다이렉트:
- `Accept-Language: vi` → `/vi`
- 기타 → `/ko` (기본값)

---

## 5. Migration Strategy

### 5.1 Phase 1: Engine Porting (TS 포팅)

**원칙:** 로직 무변경, 타입만 추가

```typescript
// lib/saju/types.ts
export interface Stem {
  char: string;      // 한자: "甲"
  kr: string;        // 한국어: "갑"
  key: string;       // 영문키: "gap"
  element: Element;  // 오행: "목"
  yin_yang: YinYang;  // 음양: "양"
}

export interface Branch {
  char: string;      // "子"
  kr: string;        // "자"
  key: string;       // "ja"
  animal: string;    // "쥐"
  element: Element;  // "수"
  emoji: string;     // "🐀" (레거시 호환, SVG로 대체 예정)
}

export type Element = "목" | "화" | "토" | "금" | "수";
export type YinYang = "양" | "음";

export interface Pillar {
  stem: Stem;
  branch: Branch;
  ganjiIdx?: number;
}

export interface SajuResult {
  pillars: {
    year: Pillar;
    month: Pillar;
    day: Pillar;
    hour: Pillar | null;
  };
  ilgan: Stem;
  wolji: Branch;
  fiveElements: Record<Element, number>;
  relations: ElementRelation;
  keys: { ilganKey: string; woljiKey: string; comboKey: string };
  gender: "male" | "female";
}
```

**포팅 체크리스트:**

- [ ] `constants.ts` -- STEMS, BRANCHES, ELEMENT_COLORS, LIFE_AREAS 상수 타입 부여
- [ ] `engine.ts` -- `calculateSaju()`, `calcDayPillar()`, `calcYearPillar()`, `calcMonthPillar()`, `calcHourPillar()`, `calcFiveElements()`, `analyzeRelations()` 1:1 포팅
- [ ] `ten-gods.ts` -- `getTenGod()` 포팅, 반환 타입 `TenGodResult` 정의
- [ ] `fortune.ts` -- `getTodayFortune()`, `getAreaScore()` 포팅
- [ ] `compatibility.ts` -- `runCompat()` 계산 로직 추출
- [ ] `__tests__/engine.test.ts` -- 기존 8개 검증 케이스 + 확장 케이스 20개 이상

### 5.2 Phase 2: DB Layer

```typescript
// lib/db/types.ts
export interface IntroCard {
  id: string;
  situation: string;
  ilgan: string;
  ko: string;
  vi: string;
}

export interface IlganCard {
  id: string;
  ilgan: string;
  situation: string;
  ko: string;
  vi: string;
  keyword?: string[];
}

// ... combo, today, cheer 타입
```

**v2 JSON 로딩 전략:**

```typescript
// lib/db/loader.ts
// 정적 import (빌드타임에 번들링)
import introData from '@/public/data/01_intro.json';
import ilganData from '@/public/data/02_ilgan.json';
// ...

// 또는 런타임 fetch (코드 스플리팅)
export async function loadDB(table: string) {
  const res = await fetch(`/data/${table}.json`);
  return res.json();
}
```

**v1 DB 처리:**

`saju-db.js` (3.16M tokens)는 거대하므로:
1. JS 파일을 JSON으로 변환 (Python 스크립트로 `SAJU_DB` 객체 추출)
2. 주제별로 분할 (`v1-love.json`, `v1-career.json` 등)
3. 동적 `import()`로 필요 시만 로딩 (코드 스플리팅)

### 5.3 Phase 3: Component Migration

현행 `app.js` 함수 -> React 컴포넌트 매핑:

| 현행 함수 | 신규 컴포넌트 | Props/State |
|-----------|-------------|-------------|
| `renderHome()` | `HomePage` | `saju: SajuResult` |
| `renderMiniPillars()` | `PillarDisplay` | `pillars: Pillar[]`, `locale: string` |
| `startTopic() + showFollowUp() + pickFollow()` | `TopicFlow` + `TopicCard` + `FollowUpQuestion` | `situation: string`, topic store |
| `renderFortune()` | `DailyPage` / `MonthlyPage` / `YearlyPage` | `fortune: FortuneResult`, `saju: SajuResult` |
| `runCompat()` | `CompatPage` + `CompatScore` | `mySaju: SajuResult`, `otherSaju: SajuResult` |
| `go(id)` | Next.js `<Link>` + `useRouter()` | -- |
| `updateLang()` | next-intl `useTranslations()` | -- |

### 5.4 Phase 4: State Management

```typescript
// stores/saju-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SajuState {
  saju: SajuResult | null;
  gender: 'male' | 'female';
  birthData: { year: number; month: number; day: number; hour: number | null } | null;
  isLunar: boolean;  // 음력 입력 여부
  setSaju: (result: SajuResult) => void;
  setGender: (g: 'male' | 'female') => void;
  setBirthData: (data: BirthData) => void;
  setIsLunar: (v: boolean) => void;
  reset: () => void;
}

export const useSajuStore = create<SajuState>()(
  persist(
    (set) => ({
      saju: null,
      gender: 'male',
      birthData: null,
      isLunar: false,
      setSaju: (result) => set({ saju: result }),
      setGender: (g) => set({ gender: g }),
      setBirthData: (data) => set({ birthData: data }),
      setIsLunar: (v) => set({ isLunar: v }),
      reset: () => set({ saju: null, birthData: null }),
    }),
    { name: 'menh-saju' }
  )
);
```

```typescript
// stores/theme-store.ts
interface ThemeState {
  mode: 'light' | 'dark' | 'system';
  setMode: (m: 'light' | 'dark' | 'system') => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      mode: 'dark',  // 다크모드 우선 (에이전트 검토 권고)
      setMode: (m) => set({ mode: m }),
    }),
    { name: 'menh-theme' }
  )
);
```

### 5.5 Phase 5: i18n Setup

**메시지 번들 구조:**

```json
// messages/ko.json
{
  "common": {
    "appName": "MỆnh",
    "tagline": "당신의 이야기를 들려드릴게요",
    "back": "돌아가기",
    "start": "시작하기"
  },
  "input": {
    "title": "생년월일을 알려주세요",
    "subtitle": "양력 기준",
    "lunarLabel": "음력으로 입력",
    "year": "년",
    "month": "월",
    "day": "일",
    "hour": "출생 시간 (선택)",
    "hourUnknown": "모름",
    "male": "남성",
    "female": "여성"
  },
  "home": {
    "todayLine": "오늘의 한 줄",
    "topicQuestion": "어떤 이야기가 궁금하세요?",
    "fortune": "운세"
  },
  "topics": {
    "love": "연애",
    "career": "직업·진로",
    "money": "돈·재물",
    "self": "나 자신",
    "compat": "궁합",
    "general": "인생 전반"
  },
  "fortune": {
    "daily": "오늘",
    "monthly": "이달",
    "yearly": "올해",
    "dailyTitle": "오늘의 운세",
    "monthlyTitle": "이달의 운세",
    "yearlyTitle": "올해의 운세",
    "areas": {
      "love": "연애",
      "career": "직업",
      "money": "재물",
      "health": "건강",
      "self": "자기관리"
    },
    "luck": "행운 정보",
    "color": "색",
    "number": "숫자",
    "direction": "방향"
  },
  "compat": {
    "title": "궁합 보기",
    "subtitle": "상대방의 생년월일을 입력하세요",
    "analyze": "궁합 분석"
  },
  "pillars": {
    "hour": "시",
    "day": "일",
    "month": "월",
    "year": "년"
  },
  "followUp": {
    // FOLLOW_UPS 트리의 모든 질문/선택지 텍스트
  },
  "errors": {
    "network": "연결에 문제가 생겼어요",
    "server": "잠시 후 다시 시도해 주세요",
    "inputRequired": "필수 입력 항목이에요"
  },
  "empty": {
    "history": "아직 상담 이력이 없어요",
    "compat": "궁합 볼 상대를 추가해보세요"
  }
}
```

**베트남어 번역 작업:** `vi.json`에 동일 키 구조로 베트남어 번역 채움. 현행 45% 누락 → 100% 목표. 기존 `data-vi` 속성과 `FOLLOW_UPS` 객체에 이미 베트남어가 있는 항목은 추출하여 재활용.

### 5.6 CSS/Design Token Migration

현행 CSS 변수를 Tailwind CSS 변수 기반으로 마이그레이션:

```css
/* globals.css */
@import "tailwindcss";
@import "./tokens.css";
@import "./dark.css";
```

```css
/* styles/tokens.css */
:root {
  /* Brand */
  --color-brand-50:  #F5F0FF;
  --color-brand-100: #EDE8FF;
  --color-brand-500: #7B5CF0;  /* WCAG AA 보정 */
  --color-brand-600: #6C4FE0;
  --color-brand-900: #1A1A2E;

  /* Neutral */
  --color-neutral-0:   #FFFFFF;
  --color-neutral-50:  #F5F3FA;
  --color-neutral-400: #AEA8C4;
  --color-neutral-500: #7B7394;
  --color-neutral-800: #2A2440;

  /* Semantic */
  --color-success: #43A047;
  --color-warning: #D4A843;
  --color-error:   #DC2626;
  --color-info:    #2563EB;

  /* Five Elements */
  --color-wood:  #2E7D32;
  --color-fire:  #C62828;
  --color-earth: #F57F17;
  --color-metal: #757575;
  --color-water: #1565C0;

  /* Typography */
  --font-display: 'Playfair Display', serif;
  --font-body: 'Be Vietnam Pro', -apple-system, sans-serif;

  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* Radius */
  --radius-sm: 14px;
  --radius-md: 20px;
  --radius-full: 9999px;
}
```

```css
/* styles/dark.css */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0F0D1A;
    --color-card: #1A1730;
    --color-text: #E8E4F2;
    --color-sub: #9B93B5;
    --color-border: #2D2854;
  }
}

[data-theme="dark"] {
  --color-bg: #0F0D1A;
  --color-card: #1A1730;
  --color-text: #E8E4F2;
  --color-sub: #9B93B5;
  --color-border: #2D2854;
}
```

---

## 6. Agent Review Findings Resolution

### 6.1 음력 입력 지원

**현황:** 양력 입력만 지원 (`form-sub: "양력 기준"`)
**해결:**

```
BirthDateForm 컴포넌트:
  [양력/음력 토글 스위치]

  음력 선택 시:
    - korean-lunar-calendar 라이브러리 사용 (npm 패키지)
    - 음력 → 양력 변환 후 saju-engine에 양력 전달
    - 윤달 체크박스 추가 (음력 선택 시만 노출)
    - 입력 UI에 "음력 {month}월 {day}일 → 양력 {solarMonth}월 {solarDay}일" 실시간 변환 표시
```

구현: `lib/utils/lunar-calendar.ts`에 음력/양력 변환 함수 래핑

### 6.2 Android 뒤로가기 (URL History)

**현황:** `display:none/block` 전환으로 URL 불변, 뒤로가기 시 앱 이탈
**해결:** Next.js App Router 적용으로 자동 해결.

- 모든 화면이 고유 URL을 가짐 (`/ko/topic/love`, `/ko/fortune/daily` 등)
- 브라우저 history stack에 자동 push
- Android 물리적 뒤로가기 = `history.back()` = 이전 페이지로 자연스럽게 복귀
- 추가: `popstate` 이벤트 리스너로 앱 이탈 방지 확인 모달 (선택적)

### 6.3 베트남어 번역 45% 누락 -> i18n 체계 구축

**현황:** `data-ko`/`data-vi` 인라인 속성, 일부 버튼/라벨에 베트남어 미적용
**해결:**

1. `messages/ko.json`과 `messages/vi.json`으로 전체 UI 텍스트 중앙 관리
2. next-intl의 `useTranslations()` 훅으로 모든 컴포넌트에서 번역 키 참조
3. 빌드 시 번역 키 누락 탐지 스크립트 (`scripts/check-i18n.ts`)
4. 현행 `app.js`의 `FOLLOW_UPS` 객체에 이미 있는 베트남어 텍스트 추출 → `vi.json`에 병합
5. DB JSON의 `ko`/`vi` 필드는 번역 번들이 아닌 컨텐츠 DB이므로 별도 관리

**누락 항목 식별 (현행 코드 분석):**
- 바텀 네비: "홈", "오늘", "궁합" -- `data-vi` 없음
- 월운/년운 "돌아가기" 버튼 -- `data-vi` 없음
- 궁합 "궁합 분석" 버튼 -- 이모지 포함 텍스트, `data-vi` 없음
- 로딩 "분석 중..." -- `data-vi` 없음
- 폴백 텍스트 함수 (`getFallbackIntro` 등) -- 이미 이중 언어이나 체계적이지 않음

### 6.4 WCAG AA 색상 대비 미달

**현황:** 5개 요소에서 AA 기준 4.5:1 미달 (최저 2.4:1)
**해결:**

| 요소 | 현행 | 변경 | 대비비 |
|------|------|------|--------|
| `.cd-t` (카드 타이틀) | `#6C4FE0` on `#FFFFFF` (4.2:1) | `#5A3DC7` on `#FFFFFF` | 6.1:1 |
| 바텀 네비 비활성 | `#AEA8C4` on `#FFFFFF` (2.8:1) | `#7B7394` on `#FFFFFF` | 4.6:1 |
| 헤더 서브텍스트 | `#7B7394` on `#F5F3FA` (3.1:1) | `#5A5272` on `#F5F3FA` | 5.8:1 |
| 미니 기둥 라벨 | `#AEA8C4` on `#F5F3FA` (2.4:1) | `#7B7394` on `#F5F3FA` | 3.9:1 * |
| 키워드 뱃지 | `#6C4FE0` on `#EDE8FF` (4.0:1) | `#5A3DC7` on `#EDE8FF` | 5.6:1 |

*미니 기둥 라벨은 보조 텍스트(font-size < 14px)이므로 WCAG AA Large Text 기준 3:1 적용 가능. 그래도 4.5:1 이상 달성 권장 → `#6B6394` 사용 시 4.6:1 달성.

Tailwind 설정에서 접근성 준수 색상을 기본값으로 적용하여 개발자가 별도 신경 쓸 필요 없게 함.

### 6.5 다크모드 우선 구현

**현황:** 라이트모드만 존재
**해결:**

1. `theme-store.ts`에서 `mode: 'dark'`를 기본값으로 설정
2. CSS 변수 기반 다크모드 토큰 정의 (`styles/dark.css`)
3. `[data-theme]` 속성으로 HTML 루트에 테마 적용
4. `prefers-color-scheme` 미디어 쿼리로 시스템 설정 감지
5. 사용자 선택 > 시스템 설정 우선순위
6. 오행 색상은 다크모드에서도 가독성 유지되도록 별도 팔레트:

```
다크모드 오행 컬러:
  목: bg #1B3A20 / text #6EE07A
  화: bg #3A1B1B / text #FF7B7B
  토: bg #3A3018 / text #FFD54F
  금: bg #2A2A35 / text #C8B8FF
  수: bg #1B2A3A / text #7BB8FF
```

### 6.6 이모지 -> SVG 아이콘 교체

**현황:** 14개 이모지 사용 (주제/운세/네비/기타)
**해결:**

1단계 (MVP): Lucide React 아이콘으로 임시 교체 (Heart, Briefcase, Coins, User, Users, Globe 등)
2단계 (Post-MVP): 커스텀 SVG 아이콘 디자인 (frontend-review.md 2.5절 에셋 정의 참고)

아이콘 컴포넌트 인터페이스:

```typescript
// components/icons/TopicIcon.tsx
interface TopicIconProps {
  topic: 'love' | 'career' | 'money' | 'self' | 'compat' | 'general';
  size?: number;
  className?: string;
}
```

### 6.7 에러/빈/로딩 상태 UI

**현황:** 로딩 컴포넌트 존재하나 미사용, 에러/빈 상태 없음
**해결:**

```
Loading 상태:
  - Skeleton UI (카드 플레이스홀더)
  - 로딩 스피너 (사주 계산 중, 향후 AI API 호출)
  - app/[locale]/loading.tsx 글로벌 로딩

Error 상태:
  - app/[locale]/error.tsx 글로벌 에러 바운더리
  - ErrorState 컴포넌트 (일러스트 + 재시도 버튼)
  - 네트워크/서버/입력 에러별 메시지 분기

Empty 상태:
  - EmptyState 컴포넌트 (일러스트 + 안내 텍스트 + CTA)
  - 궁합 결과 없음, 상담 이력 없음 등
```

### 6.8 PWA Manifest

**현황:** manifest.json 부재
**해결:**

```json
// public/manifest.json
{
  "name": "MỆnh - AI Saju Service",
  "short_name": "MỆnh",
  "description": "AI가 풀어주는 나의 사주 이야기",
  "start_url": "/ko",
  "display": "standalone",
  "background_color": "#0F0D1A",
  "theme_color": "#7B5CF0",
  "orientation": "portrait",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

`layout.tsx`에 메타데이터 추가:
```typescript
export const metadata: Metadata = {
  manifest: '/manifest.json',
  themeColor: '#7B5CF0',
  appleWebApp: { capable: true, statusBarStyle: 'black-translucent' },
};
```

---

## 7. MVP Scope (8 Weeks)

### 7.1 Scope Definition

| 포함 (MVP) | 제외 (Post-MVP) |
|------------|-----------------|
| 사주 엔진 TS 포팅 + 테스트 | 백엔드 API (FastAPI) |
| 7개 화면 Next.js 마이그레이션 | 소셜 로그인 (카카오 OAuth) |
| i18n (한국어 + 베트남어 100%) | AI LLM 상담 (Claude/GPT) |
| 다크모드 | RAG 지식 베이스 |
| 양력/음력 입력 | 프리미엄 구독/결제 |
| PWA manifest + 기본 SW | Push 알림 |
| URL 라우팅 + Android 뒤로가기 | SNS 공유 카드 동적 생성 |
| WCAG AA 색상 대비 보정 | Playwright E2E 테스트 |
| Lucide 아이콘 (임시) | 커스텀 SVG 아이콘 디자인 |
| Skeleton/Error/Empty 상태 UI | Sentry 에러 트래킹 |
| v2 DB 49개 + v1 DB 폴백 | v2 DB 665개 완성 |
| Vercel 배포 (정적 사이트) | AWS 인프라 (ECS/RDS) |

### 7.2 Weekly Roadmap

#### Week 1: Foundation

| Task | Detail | Deliverable |
|------|--------|-------------|
| Next.js 15 프로젝트 초기화 | App Router, TS, Tailwind, src/ | `next-app/` 프로젝트 |
| 디자인 토큰 셋업 | CSS 변수, 다크모드, 오행 컬러 | `tokens.css`, `dark.css` |
| i18n 셋업 | next-intl, `ko.json`/`vi.json` 기본 구조 | 언어 전환 동작 |
| Zustand 스토어 | saju-store, theme-store | 스토어 + persist 동작 |
| 레이아웃 컴포넌트 | Header, BottomNav, 루트 layout | 앱 셸 렌더링 |

**Gate:** 앱 셸 렌더링 + 언어 전환 + 다크/라이트 전환 동작

#### Week 2: Engine + Input

| Task | Detail | Deliverable |
|------|--------|-------------|
| saju-engine.ts 포팅 | constants, engine, ten-gods, fortune | TS 엔진 완성 |
| 엔진 테스트 | Vitest, 8개 기존 케이스 + 20개 확장 | 28+ 테스트 통과 |
| BirthDateForm | 양력/음력 토글, 성별, 시간, 유효성 검증 | Input 페이지 |
| 음력 변환 | korean-lunar-calendar 연동 | 음력 입력 동작 |
| DB 로딩 | v2 JSON import + v1 어댑터 | DB 데이터 서빙 |

**Gate:** 사주 입력 → 계산 → 스토어 저장 동작, 엔진 테스트 전체 통과

#### Week 3: Home + Fortune

| Task | Detail | Deliverable |
|------|--------|-------------|
| HomePage | 오늘의 한줄, 주제 그리드, 운세 바로가기 | 홈 화면 |
| PillarDisplay | 사주 기둥 표시 (한자 + 오행 색상) | 미니 기둥 컴포넌트 |
| FortunePages | Daily/Monthly/Yearly 3개 페이지 | 운세 화면 |
| FortuneScoreBar | 영역별 점수 바 | 점수 시각화 |
| Framer Motion | 페이지 전환, 카드 등장 애니메이션 | 모션 적용 |

**Gate:** 홈 → 운세 플로우 동작, 페이지 전환 애니메이션

#### Week 4: Topic Q&A

| Task | Detail | Deliverable |
|------|--------|-------------|
| TopicFlow | 대화형 Q&A 전체 플로우 | Topic 페이지 |
| TopicCard | intro/ilgan/combo/today/cheer 5카드 | 카드 컴포넌트 |
| FollowUpQuestion | 후속 질문 선택지 + 선택 UX | 선택지 컴포넌트 |
| FOLLOW_UPS 데이터 | 기존 트리 구조 TS 변환 | 5개 주제 대화 트리 |
| 카드 애니메이션 | fadeUp, 선택 시 슬라이드 | 대화형 모션 |

**Gate:** 5개 주제 대화형 Q&A 전체 플로우 동작

#### Week 5: Compat + i18n Complete

| Task | Detail | Deliverable |
|------|--------|-------------|
| CompatPage | 궁합 입력 + 점수 + 해석 | 궁합 화면 |
| CompatScore | 원형 점수 표시 | 점수 컴포넌트 |
| vi.json 완성 | 베트남어 번역 100% | 완전 이중 언어 |
| i18n QA | 모든 화면 ko/vi 전환 테스트 | 번역 누락 0개 |
| 접근성 | ARIA 속성, 키보드 탐색, 포커스 관리 | WCAG AA 준수 |

**Gate:** 궁합 동작, 베트남어 번역 100%, 접근성 기본 준수

#### Week 6: Dark Mode + Polish

| Task | Detail | Deliverable |
|------|--------|-------------|
| 다크모드 완성 | 전체 컴포넌트 다크모드 대응 | 다크/라이트 전환 |
| Skeleton/Empty/Error | 3종 상태 UI | 상태 UI 완성 |
| PWA | manifest.json, 기본 Service Worker | 홈 화면 추가 가능 |
| 아이콘 교체 | Lucide React 적용 | 이모지 0개 |
| 반응형 QA | 360px/390px/414px/768px | 모바일 레이아웃 |

**Gate:** 다크모드 전체 동작, PWA 홈 화면 추가 동작

#### Week 7: Testing + Optimization

| Task | Detail | Deliverable |
|------|--------|-------------|
| 컴포넌트 테스트 | Vitest + Testing Library | 주요 컴포넌트 테스트 |
| 엔진 테스트 확장 | 50+ 케이스 | 엔진 정확도 100% |
| Lighthouse | Performance 90+, Accessibility 90+ | 성능 최적화 |
| 번들 사이즈 | v1 DB 코드 스플리팅, 트리 셰이킹 | 번들 최적화 |
| 크로스브라우저 | Chrome, Safari, Samsung Internet | 호환성 확인 |

**Gate:** 테스트 통과, Lighthouse 90+, 번들 사이즈 적정

#### Week 8: Deploy + Launch

| Task | Detail | Deliverable |
|------|--------|-------------|
| Vercel 배포 | 프로덕션 빌드 + 도메인 연결 | 라이브 배포 |
| OG 메타 태그 | 페이지별 OG 이미지 + 설명 | SEO/소셜 프리뷰 |
| 최종 QA | 전체 플로우 수동 테스트 | 버그 0 |
| 문서화 | 컴포넌트 가이드, 배포 가이드 | 문서 |
| v1 DB 연동 QA | 프리미엄 컨텐츠 폴백 동작 | DB 폴백 확인 |

**Gate:** 프로덕션 배포 완료, 전체 플로우 무결

### 7.3 Deliverable Summary

| Week | Milestone | Success Criteria |
|------|-----------|------------------|
| W1 | App Shell | 앱 셸 + 언어 전환 + 테마 전환 |
| W2 | Engine Ready | TS 엔진 28+ 테스트 통과, 음력 입력 동작 |
| W3 | Home + Fortune | 홈/운세 3개 화면 동작 |
| W4 | Topic Q&A | 5개 주제 대화형 플로우 동작 |
| W5 | Full Feature | 궁합 + 베트남어 100% + 접근성 |
| W6 | Dark + Polish | 다크모드 + 상태 UI + PWA + 아이콘 |
| W7 | Quality | 테스트 + Lighthouse 90+ + 번들 최적화 |
| W8 | Launch | Vercel 프로덕션 배포 + 전체 QA 통과 |

---

## 8. Risk & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| saju-engine TS 포팅 시 계산 오차 | Critical | Low | 기존 8개 검증 케이스 + 20개 확장 테스트로 1:1 검증. 기준일(2000-01-01=戊午) 일치 확인 필수 |
| v1 DB(3.16M tokens) 번들 사이즈 폭발 | High | High | JSON 분할 + dynamic import, 초기 로딩에 v2 DB만 포함 |
| 음력 변환 라이브러리 정확도 | High | Medium | korean-lunar-calendar + 교차 검증 (ytliu0 만세력 대조) |
| 베트남어 번역 품질 | Medium | Medium | 네이티브 스피커 검수 필수, 기계번역 금지 |
| next-intl + App Router 호환 이슈 | Medium | Low | next-intl v4는 App Router 정식 지원, 마이그레이션 가이드 참조 |
| 다크모드 오행 색상 가독성 | Medium | Medium | 다크모드 전용 오행 팔레트 별도 정의, 디자이너 검수 |
| Framer Motion 번들 사이즈 | Low | Medium | 트리 셰이킹 활성화, `AnimatePresence`/`motion` 컴포넌트만 임포트 |
| 8주 일정 초과 | Medium | Medium | Week별 Gate로 조기 감지, Week 7-8 버퍼 활용, 기능 우선순위 컷 |

---

## Appendix A: File-by-File Migration Checklist

- [ ] `saju-engine.js` → `lib/saju/constants.ts` + `engine.ts` + `ten-gods.ts` + `fortune.ts` + `types.ts`
- [ ] `app.js` 홈 렌더링 → `app/[locale]/page.tsx` + `components/layout/TopicGrid.tsx`
- [ ] `app.js` 주제 플로우 → `app/[locale]/topic/[id]/page.tsx` + `components/topic/*`
- [ ] `app.js` 운세 렌더링 → `app/[locale]/fortune/*/page.tsx` + `components/saju/FortuneScoreBar.tsx`
- [ ] `app.js` 궁합 → `app/[locale]/compat/page.tsx` + `components/saju/CompatScore.tsx`
- [ ] `app.js` 미니 기둥 → `components/saju/PillarDisplay.tsx`
- [ ] `style.css` → `globals.css` + `tokens.css` + `dark.css` + Tailwind 유틸리티
- [ ] `index.html` → `app/layout.tsx` + `app/[locale]/layout.tsx` (폰트, 메타, 구조)
- [ ] `saju-db-v2.js` → `saju-db-v2/output/*.json` 직접 import
- [ ] `saju-db.js` → JSON 변환 + 분할 + dynamic import

## Appendix B: Key Decisions Log

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| State Mgmt | Zustand + persist | Context API, Jotai, Redux | 사주 데이터 persist 필요, Context는 boilerplate 과다, Zustand이 가장 경량 |
| i18n | next-intl | react-intl, next-translate, custom | App Router 최적 통합, ICU 메시지 포맷, 타입 안전 |
| CSS | Tailwind + CSS Variables | styled-components, CSS Modules | 유틸리티 퍼스트 + 디자인 토큰 변수로 다크모드/오행 색상 체계적 관리 |
| Icons | Lucide React (MVP) → Custom SVG | Material Icons, Heroicons | Lucide가 가장 경량 + 트리셰이킹, 추후 커스텀 SVG로 교체 용이 |
| Deploy | Vercel (MVP) | AWS CloudFront, Netlify | Next.js 최적화 배포, 무료 tier로 MVP 검증 |
| Animation | Framer Motion | react-spring, GSAP, CSS only | React 생태계 최적, AnimatePresence 라우트 전환, 제스처 지원 |
| Dark Mode Default | Dark | Light | 에이전트 검토 권고 + 신비로운 사주/운세 앱 분위기에 다크 적합 + 베트남 MZ 선호 |
| Lunar Calendar | korean-lunar-calendar npm | 자체 구현, China lunar npm | 한국 음력 특화, 윤달 지원, npm 패키지 안정성 |

---

> **Next Step:** 이 문서를 기반으로 `next-app/` 디렉토리에 Next.js 15 프로젝트를 초기화하고, Week 1 Foundation 태스크를 시작한다.
