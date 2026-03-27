# Saju AI Service - Frontend Design Document

> **Version:** 1.0
> **Date:** 2026-03-25
> **Author:** Frontend Architect
> **Status:** Draft
> **Based on:** [PRD v1.0](../00-pm/saju-ai-service.prd.md) | [Architecture v1.0](./saju-ai-architecture.md)

---

## Table of Contents

1. [주요 화면 목록 및 플로우](#1-주요-화면-목록-및-플로우)
2. [핵심 UI 컴포넌트](#2-핵심-ui-컴포넌트)
3. [사용자 온보딩 플로우](#3-사용자-온보딩-플로우)
4. [모바일 우선 설계 원칙](#4-모바일-우선-설계-원칙)
5. [결과 표시 형태](#5-결과-표시-형태)
6. [디자인 시스템](#6-디자인-시스템)
7. [기술 스택 상세](#7-기술-스택-상세)

---

## 1. 주요 화면 목록 및 플로우

### 1.1 전체 화면 맵

| ID | 화면명 | 경로 | 설명 | 접근 조건 |
|----|--------|------|------|-----------|
| S-01 | 랜딩 페이지 | `/` | 서비스 소개, 소셜 로그인 CTA | 비인증 |
| S-02 | 소셜 로그인 | `/auth/login` | 카카오/네이버/구글/Apple OAuth | 비인증 |
| S-03 | 온보딩 위자드 | `/onboarding` | 최초 사주 프로필 등록 (3단계) | 신규 인증 사용자 |
| S-04 | 홈 대시보드 | `/home` | 오늘의 운세 + 빠른 메뉴 + 사주 요약 | 인증 |
| S-05 | 사주 입력/편집 | `/profile/new` | 사주 프로필 등록 폼 | 인증 |
| S-06 | 사주 결과 | `/profile/[id]` | 오행 차트, 사주팔자 상세, 십성 | 인증 |
| S-07 | AI 상담 채팅 | `/counsel/[id]` | SSE 스트리밍 채팅 인터페이스 | 인증 |
| S-08 | 상담 이력 | `/counsel/history` | 과거 상담 목록 및 상세 조회 | 인증 |
| S-09 | 궁합 입력 | `/compatibility/new` | 두 사주 프로필 선택 | 인증 |
| S-10 | 궁합 결과 | `/compatibility/[id]` | 궁합 점수 게이지, 항목별 해석 | 인증 |
| S-11 | 운세 캘린더 | `/calendar` | 월간 운세, 길일 캘린더 | 인증 |
| S-12 | 구독 플랜 | `/pricing` | Freemium → 구독 전환 화면 | 인증 |
| S-13 | 결제 처리 | `/payment/checkout` | Toss Payments 내장 결제 | 인증 |
| S-14 | 마이페이지 | `/my` | 프로필 관리, 구독 상태, 설정 | 인증 |
| S-15 | 설정 | `/settings` | 알림, 언어, 계정 관리 | 인증 |

### 1.2 핵심 사용자 플로우

#### 플로우 A: 신규 사용자 첫 경험 (핵심 전환 경로)

```
S-01 (랜딩)
    │ "무료로 시작하기" CTA
    ▼
S-02 (카카오 로그인)
    │ OAuth 콜백 처리
    ▼
S-03 (온보딩 위자드)
    │ Step 1: 이름/별명
    │ Step 2: 생년월일시 + 양/음력 + 성별
    │ Step 3: 관심사 주제 선택 (선택형)
    │ [사주 분석 시작] 버튼
    ▼
S-06 (사주 결과) ← 무료 기본 사주 풀이 제공
    │ 오행 차트 + 사주팔자 + 간략 해석
    │ [AI와 상담하기] CTA (무료 3회)
    ▼
S-07 (AI 상담 채팅)
    │ 무료 3회 소진 시
    ▼
S-12 (구독 플랜) ← 유료 전환 게이트
```

#### 플로우 B: 일상 재방문 사용자

```
S-04 (홈 대시보드)
    │ 오늘의 운세 카드 확인 (매일 갱신)
    ├─► S-07 (AI 상담) - 주제별 빠른 진입
    ├─► S-11 (운세 캘린더) - 이번 달 흐름 확인
    └─► S-10 (궁합 결과) - 저장된 궁합 조회
```

#### 플로우 C: 결제 플로우

```
S-07 (AI 상담) → 일일 한도 초과 알림
    │ "프리미엄 전환" 배너
    ▼
S-12 (구독 플랜 선택)
    │ 월간 / 연간 선택
    ▼
S-13 (결제 체크아웃)
    │ Toss Payments 위젯
    │ 결제 완료 → 리다이렉트
    ▼
S-04 (홈 대시보드) - 프리미엄 배지 표시
```

### 1.3 네비게이션 구조

**하단 탭 바 (모바일 고정):**

```
┌─────┬──────┬──────┬─────┐
│ 홈  │ 상담  │ 캘린더│ MY  │
│ 🏠  │  💬  │  📅  │ 👤  │
└─────┴──────┴──────┴─────┘
```

**탭별 연결 화면:**
- 홈(🏠): S-04 → S-06 → S-09
- 상담(💬): S-07 → S-08
- 캘린더(📅): S-11
- MY(👤): S-14 → S-15 → S-12

**헤더 네비게이션 (서브 화면):**
- 뒤로가기(`←`) + 화면 제목 + 컨텍스트 액션(`···`)
- 상담 화면: 프로필 전환, 주제 변경 메뉴

---

## 2. 핵심 UI 컴포넌트

### 2.1 사주 입력 폼 (`SajuInputForm`)

**컴포넌트 계층:**

```
SajuInputForm
├── ProfileTypeSelector       # 본인 / 가족 / 지인 선택
├── NameInput                 # 이름 또는 별명 입력
├── BirthDatePicker           # 날짜 피커 (드럼롤 스타일)
│   ├── YearDrum
│   ├── MonthDrum
│   └── DayDrum
├── CalendarToggle            # 양력 / 음력 + 윤달 체크박스
├── BirthTimePicker           # 시간 피커 (30분 단위 또는 시진 선택)
│   └── TimeUnknownCheckbox   # 시간 모름 옵션
├── GenderSelector            # 성별 라디오
└── SubmitButton              # 사주 분석하기
```

**주요 Props 인터페이스:**

```typescript
interface SajuInputFormProps {
  mode: 'create' | 'edit';
  initialValues?: Partial<SajuProfile>;
  onSubmit: (data: SajuProfileInput) => Promise<void>;
  isLoading: boolean;
}

interface SajuProfileInput {
  label: 'self' | 'family' | 'acquaintance';
  name: string;
  birthDate: { year: number; month: number; day: number };
  isLunar: boolean;
  isLeapMonth: boolean;
  birthTime: { hour: number; minute: number } | null;
  gender: 'male' | 'female';
}
```

**인터랙션 상세:**
- 날짜 피커: iOS 드럼롤(Picker Wheel) 스타일. 터치 스크롤로 값 선택.
- 시진(時辰) 모드: 23:00~00:59=자시, 01:00~02:59=축시 ... 자동 매핑 토글 제공.
- 음력 선택 시: 윤달 체크박스 활성화. 해당 연월에 윤달이 없으면 자동 비활성.
- 폼 유효성: 실시간 검증. 과거 날짜만 허용 (미래 생일 불가).

### 2.2 사주 결과 카드 (`SajuResultCard`)

**컴포넌트 계층:**

```
SajuResultCard
├── FourPillarsDisplay        # 사주팔자 시각적 표현
│   ├── PillarColumn (x4)     # 연/월/일/시 각 기둥
│   │   ├── StemGlyph         # 천간 한자 (Noto Serif KR)
│   │   └── BranchGlyph       # 지지 한자 (Noto Serif KR)
│   └── PillarLabels          # 연주 / 월주 / 일주 / 시주 레이블
├── FiveElementsChart         # 오행 분포 차트 (Recharts)
├── TenStarsGrid              # 십성(十星) 배치표
├── TwelveStagesBadge         # 12운성 배지
├── SpecialStarsList          # 주요 신살 태그
├── GeokgukBadge              # 격국 표시
└── ShareButton               # SNS 공유 카드 생성
```

**오행 차트 타입:**
- Radar Chart: 목/화/토/금/수 5축 레이더
- Bar Chart (대안): 수평 막대, 오행별 컬러 적용
- 기본: Radar Chart. 모바일 가로 공간 부족 시 Bar Chart 자동 전환.

**사주 기둥 시각적 표현:**

```
  연주    월주    일주    시주
┌──────┬──────┬──────┬──────┐
│  甲  │  丙  │  戊  │  庚  │  ← 천간 (Noto Serif, 32px, Bold)
│  갑  │  병  │  무  │  경  │  ← 한글 독음 (Pretendard, 12px)
│ 목木 │ 화火 │ 토土 │ 금金 │  ← 오행 (오행 컬러 배경)
├──────┼──────┼──────┼──────┤
│  子  │  寅  │  午  │  申  │  ← 지지 (Noto Serif, 32px, Bold)
│  자  │  인  │  오  │  신  │  ← 한글 독음
│ 수水 │ 목木 │ 화火 │ 금金 │  ← 오행 (오행 컬러 배경)
└──────┴──────┴──────┴──────┘
```

### 2.3 AI 상담 채팅 인터페이스 (`CounselChat`)

**컴포넌트 계층:**

```
CounselChat
├── ChatHeader                # 상담 주제 + 상담 횟수 표시
│   ├── TopicBadge            # 현재 주제 (연애/직장/재물...)
│   └── ConsultCountBadge     # 무료 잔여 횟수 (n/3)
├── MessageList               # 가상 스크롤 메시지 목록
│   ├── AIMessage             # AI 응답 버블
│   │   ├── StreamingText     # 타이핑 효과 텍스트
│   │   └── HanjaTerm         # 한자 용어 탭 → 바텀시트
│   └── UserMessage           # 사용자 메시지 버블
├── QuickReplyChips           # 자주 묻는 질문 칩 (첫 메시지)
├── InputToolbar              # 메시지 입력 영역
│   ├── TextInput
│   ├── VoiceInputButton      # 음성 입력 (Web Speech API)
│   └── SendButton
├── TermBottomSheet           # 명리학 용어 해설 시트
└── LimitReachedModal         # 무료 한도 초과 모달
```

**SSE 스트리밍 구현 패턴:**

```typescript
// useSSEStream.ts
function useSSEStream(consultationId: string) {
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = async (content: string) => {
    setIsStreaming(true);
    setStreamingText('');

    const response = await fetch(
      `/api/v1/consultations/${consultationId}/messages`,
      { method: 'POST', body: JSON.stringify({ content }) }
    );

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      // SSE 파싱: "data: {"token": "..."}"\n
      const token = parseSSEToken(chunk);
      if (token) setStreamingText(prev => prev + token);
    }
    setIsStreaming(false);
  };

  return { streamingText, isStreaming, sendMessage };
}
```

**타이핑 이펙트:**
- 토큰이 수신될 때마다 `StreamingText` 컴포넌트가 점진적으로 렌더링.
- 스트리밍 완료 후 마크다운 파싱 (한자 용어 `[편재(偏財)]` → 탭 가능한 `HanjaTerm` 컴포넌트).
- 커서 블링크 애니메이션은 Framer Motion `animate={{ opacity: [1, 0] }}`.

### 2.4 궁합 결과 화면 (`CompatibilityResult`)

**컴포넌트 계층:**

```
CompatibilityResult
├── CoupleHeader              # 두 사람 이름 + 사주 요약
├── TotalScoreGauge           # 종합 궁합 점수 게이지 (0~100)
├── CategoryScoreList         # 항목별 점수
│   ├── ScoreBar (연애궁합)
│   ├── ScoreBar (사업궁합)
│   ├── ScoreBar (결혼궁합)
│   └── ScoreBar (일상궁합)
├── FiveElementsComparison    # 오행 비교 차트 (두 사주 레이더 오버레이)
├── InterpretationSection     # AI 텍스트 해석 (마크다운)
└── ShareButton
```

**점수 게이지 디자인:**
- 원형 게이지 (SVG arc), 0~100 범위.
- 0~40: Water 컬러(#2196F3) - "인연이 약함"
- 41~70: Earth 컬러(#FFC107) - "보통의 인연"
- 71~100: Fire 컬러(#F44336) 또는 Gold(#C9A96E) - "좋은 인연"

### 2.5 구독 플랜 선택 UI (`PricingPage`)

**컴포넌트 계층:**

```
PricingPage
├── UsageLimitBanner          # 현재 무료 사용량 시각화
├── PlanComparisonTable       # 무료 vs 프리미엄 기능 비교
├── PlanCard (Free)           # 무료 플랜 현황
├── PlanCard (Monthly)        # 월 구독 카드 (추천 배지)
├── PlanCard (Yearly)         # 연 구독 카드 (할인율 표시)
├── BillingToggle             # 월간/연간 전환 스위치
└── FAQAccordion              # 자주 묻는 질문
```

**플랜 비교 데이터:**

| 기능 | 무료 | 프리미엄 |
|------|------|----------|
| AI 상담 | 일 3회 | 무제한 |
| 사주 프로필 저장 | 1개 | 5개 |
| 오늘의 운세 | O | O |
| 월간/연간 운세 | X | O |
| 궁합 분석 | 1회/월 | 무제한 |
| 길일 캘린더 | X | O |
| 심화 사주 분석 | X | O |
| 공유 카드 | 기본형 | 프리미엄 디자인 |

### 2.6 오늘의 운세 카드 (`DailyFortuneCard`)

**컴포넌트 계층:**

```
DailyFortuneCard
├── DateHeader                # 날짜 + 일진(日辰) 표시
├── FortuneScore              # 오늘의 운세 별점 (5점)
├── FortuneText               # 핵심 운세 텍스트 (2~3줄)
├── CategoryMiniScores        # 연애/재물/건강 미니 점수
├── LuckyElements             # 행운의 방향, 색상, 숫자
├── ExpandButton              # "더보기" → 전체 운세 표시
└── ShareButton               # SNS 공유
```

**카드 새로고침 패턴:**
- 매일 자정 Redis 캐시 만료(TTL 24h) → 첫 접근 시 백엔드 API 호출.
- TanStack Query `staleTime: 0`, `gcTime: 24 * 60 * 60 * 1000`.
- Pull-to-Refresh: 사용자 수동 갱신 시 캐시 무효화.

---

## 3. 사용자 온보딩 플로우

### 3.1 카카오 소셜 로그인

**구현 전략:**

```
1. 랜딩 페이지 [카카오로 시작하기] 버튼 클릭
2. Next.js Route: GET /api/auth/kakao
   → 카카오 OAuth 2.0 인증 URL 리다이렉트
3. 카카오 로그인 완료 → 콜백: GET /api/auth/kakao/callback
   → 서버에서 access_token 교환
   → 사용자 정보 조회 (이메일, 닉네임, 프로필 이미지)
   → 신규 사용자: users 테이블 생성 → 온보딩으로 리다이렉트
   → 기존 사용자: JWT 발급 → 홈 대시보드로 리다이렉트
4. JWT는 HttpOnly 쿠키로 저장 (XSS 방지)
```

**로그인 화면 레이아웃:**
- 배경: 심야 남색(#1A1A2E) 그라디언트 + 별자리 파티클 애니메이션 (Framer Motion)
- 로고 + 서비스 소개 문구 (3줄)
- [카카오로 시작하기] 버튼 (카카오 노란색, 풀 너비)
- [네이버로 시작하기] 버튼
- [구글로 시작하기] 버튼
- [Apple로 시작하기] 버튼 (iOS Safari 전용 표시)

### 3.2 최초 사주 프로필 등록 (3단계 위자드)

**위자드 컴포넌트 구조:**

```
OnboardingWizard
├── ProgressStepper           # 단계 표시 (1/3, 2/3, 3/3)
├── Step1: WelcomeAndName     # 환영 + 이름 입력
├── Step2: BirthInfoForm      # 생년월일시 + 성별 (핵심 단계)
├── Step3: TopicPreference    # 관심 주제 선택 (멀티 선택)
└── WizardNavigation          # 이전 / 다음 버튼
```

**각 단계 상세:**

**Step 1: 환영 및 이름 입력**
- 애니메이션 환영 메시지: "안녕하세요! 사주 AI가 당신의 사주를 분석할게요."
- 이름 또는 별명 입력 (필수, 최대 10자)
- "누구의 사주인가요?" 선택 → 본인 선택 자동

**Step 2: 생년월일시 및 성별 (핵심)**
- 전체 화면 점유형 입력 폼
- 날짜 피커: 드럼롤 UI (Haptic Feedback 연동)
- 양력/음력 토글 → 음력 선택 시 윤달 옵션 노출
- 시간 피커: 시(時) + 분(分) 또는 시진(時辰) 선택 모드
- "정확한 시간을 모르시면 건너뛰어도 됩니다" 안내 텍스트
- 성별: 남성 / 여성 카드 선택 (큰 터치 영역)

**Step 3: 관심 주제 (선택)**
- 연애운, 직장운, 재물운, 건강운, 학업운 칩 선택
- 최대 3개 선택 가능
- "나중에 선택하기" 스킵 옵션

**Step 2 → 결과 전환 애니메이션:**
```
[사주 분석하기] 버튼 클릭
→ 버튼 로딩 스피너 (API 호출 중)
→ 전체 화면 오버레이: "사주를 분석하고 있어요..."
   + 사주팔자 기둥 4개가 순차적으로 나타나는 애니메이션
→ 완료 시 Haptic Feedback + S-06 (사주 결과) 화면 전환
```

### 3.3 무료 기본 사주 풀이 → 유료 전환 유도

**무료 제공 범위:**
- 사주팔자 시각화 (4기둥 한자 표시)
- 오행 분포 차트
- 핵심 격국 및 특징 요약 (300자 이내)
- AI 상담 3회/일

**유료 게이트 위치:**
1. 사주 결과 화면 하단: "AI와 심층 상담하기" CTA (무료 3회 명시)
2. AI 상담 3회 소진 직후: 업그레이드 모달 (즉시 노출)
3. 월간/연간 운세 섹션 잠금(Lock) 아이콘 탭 시: 구독 안내 바텀시트

**전환 유도 메시지 원칙:**
- 두려움 자극 금지 (PRD 디자인 원칙 "신뢰감, 감성적 경험" 준수)
- "더 깊은 해석이 기다립니다" 긍정적 어조
- 월별 상담 절약액 환산 표시 ("역술인 방문 1회 비용의 1/10")

---

## 4. 모바일 우선 설계 원칙

### 4.1 반응형 브레이크포인트

Tailwind CSS 기본값을 기반으로 사주 서비스에 최적화:

| 이름 | 최소 너비 | 대상 기기 | 레이아웃 전략 |
|------|-----------|-----------|---------------|
| `xs` | 360px | 소형 스마트폰 (갤럭시 A 시리즈) | 단일 컬럼, 압축 UI |
| `sm` | 390px | 표준 스마트폰 (iPhone 14) | 단일 컬럼, 표준 패딩 |
| `md` | 768px | 태블릿 세로 | 2컬럼 가능, 사이드바 노출 |
| `lg` | 1024px | 태블릿 가로 / 소형 데스크톱 | 3컬럼 레이아웃 |
| `xl` | 1280px | 데스크톱 | 최대 너비 고정(480px 컨텐츠) |

**모바일 우선 CSS 전략:**
```css
/* Tailwind 설정 (tailwind.config.ts) */
theme: {
  screens: {
    'xs': '360px',   /* 최소 지원 너비 (PRD 5.6) */
    'sm': '390px',
    'md': '768px',
    'lg': '1024px',
    'xl': '1280px',
  }
}

/* 컨텐츠 최대 너비: 데스크톱에서 모바일 앱처럼 */
.app-container {
  max-width: 480px;
  margin: 0 auto;
}
```

### 4.2 터치 최적화

**터치 타겟 최소 크기:** 44 x 44px (Apple HIG 권장)

| 컴포넌트 | 터치 타겟 크기 | 비고 |
|----------|----------------|------|
| 탭 바 아이템 | 56 x 56px | 충분한 여백 |
| 날짜 피커 드럼롤 | 전체 너비 | 큰 드래그 영역 |
| 성별 선택 카드 | 전체 너비 / 2 | 카드형 선택 |
| 빠른 메뉴 버튼 | 80 x 80px | 3x2 그리드 |
| 채팅 전송 버튼 | 48 x 48px | 원형 버튼 |

**스크롤 최적화:**
- `overflow-y: auto` + `-webkit-overflow-scrolling: touch` (관성 스크롤)
- 채팅 메시지 목록: TanStack Virtual 가상 스크롤 적용 (대화량 많을 때)
- 오행 차트: `touch-action: none` (차트 내 드래그 방지)

**제스처 패턴:**
- 바텀시트: 아래로 스와이프하여 닫기 (`@radix-ui/react-dialog` + 드래그 핸들)
- 카드 사이 전환: 좌우 스와이프 (운세 카테고리 카드)
- 당겨서 새로고침: 오늘의 운세 화면 (`useScrollTrigger` 커스텀 훅)

### 4.3 PWA 전략

**목표:** 홈 화면 추가 → 네이티브 앱 유사 경험

**`manifest.json` 설정:**
```json
{
  "name": "사주 AI",
  "short_name": "사주AI",
  "description": "AI 기반 사주명리 상담 서비스",
  "start_url": "/home",
  "display": "standalone",
  "orientation": "portrait",
  "theme_color": "#1A1A2E",
  "background_color": "#1A1A2E",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**Service Worker 전략 (next-pwa 라이브러리):**

| 리소스 유형 | 캐싱 전략 | TTL |
|-------------|-----------|-----|
| HTML 페이지 | Network First | - |
| JS/CSS 번들 | Cache First | 30일 |
| 폰트 파일 | Cache First | 365일 |
| 오늘의 운세 API | Stale While Revalidate | 1시간 |
| 사주 프로필 API | Network First | - |
| 공유 카드 이미지 | Cache First | 7일 |

**Push Notification:**
- 매일 아침 오늘의 운세 알림 (사용자 동의 후)
- 알림 권한: 첫 앱 설치 후 홈화면에서 자연스럽게 요청 (강요 금지)

### 4.4 성능 최적화 목표 (Core Web Vitals)

| 지표 | 목표값 | 측정 조건 |
|------|--------|-----------|
| LCP (Largest Contentful Paint) | < 2.5초 | 4G 모바일, 홈 화면 |
| FID (First Input Delay) / INP | < 100ms | 채팅 입력 응답 |
| CLS (Cumulative Layout Shift) | < 0.1 | 스켈레톤 로딩 후 전환 |
| FCP (First Contentful Paint) | < 1.8초 | SSR 활용 |
| TTFB (Time to First Byte) | < 600ms | CloudFront + SSR |

**최적화 전략:**

```
1. 이미지 최적화
   - Next.js Image 컴포넌트 (자동 WebP, AVIF 변환)
   - 오행 아이콘: SVG 인라인 (HTTP 요청 제거)
   - 공유 카드: S3 → CloudFront CDN 서빙

2. 코드 스플리팅
   - Recharts: 사주 결과 화면에서만 동적 import
   - Framer Motion: 필요한 모션 컴포넌트만 선택적 import
   - 채팅 화면: 독립 청크

3. 폰트 최적화
   - Pretendard: Variable 폰트 (단일 파일, 전체 굵기)
   - Noto Serif KR: 필요한 글자만 서브셋 (한자 표의 문자 1,000자)
   - `font-display: swap`

4. 서버 컴포넌트 활용 (Next.js App Router)
   - 사주 결과 초기 렌더링: RSC로 서버에서 데이터 페칭
   - 채팅 이력: 서버에서 첫 페이지 하이드레이션
   - 운세 캘린더: ISR (6시간 재검증)

5. 번들 크기 관리
   - 목표: 초기 JS 번들 < 150KB (gzip)
   - recharts tree-shaking: 필요한 차트 컴포넌트만 import
   - lodash 대신 es-toolkit 사용
```

---

## 5. 결과 표시 형태

### 5.1 사주 오행 분석 시각화

**Radar Chart (레이더 차트) - 기본:**

```typescript
// FiveElementsRadarChart.tsx
import { Radar, RadarChart, PolarGrid, ResponsiveContainer } from 'recharts';

const FIVE_ELEMENTS_DATA = (elements: FiveElements) => [
  { element: '목(木)', value: elements.wood, fullMark: 8 },
  { element: '화(火)', value: elements.fire,  fullMark: 8 },
  { element: '토(土)', value: elements.earth, fullMark: 8 },
  { element: '금(金)', value: elements.metal, fullMark: 8 },
  { element: '수(水)', value: elements.water, fullMark: 8 },
];

// 오행 컬러 매핑
const ELEMENT_COLORS = {
  wood:  '#2E7D32',  // 목 - 짙은 청록
  fire:  '#C62828',  // 화 - 짙은 적색
  earth: '#F57F17',  // 토 - 황색
  metal: '#9E9E9E',  // 금 - 회백색
  water: '#1565C0',  // 수 - 짙은 청색
};
```

**Bar Chart (막대 차트) - 모바일 세로 화면 대안:**
- 수평 막대, 오행별 컬러 채우기
- 애니메이션: `Framer Motion` `animate={{ width: '${percent}%' }}`
- 과불급 경고: 한 오행이 50% 이상 시 주황색 강조 + 텍스트 안내

### 5.2 천간지지 시각적 표현

**FourPillarsTable 컴포넌트:**

```
┌──────────┬──────────┬──────────┬──────────┐
│   연주    │   월주    │   일주    │   시주    │
│  年柱     │  月柱     │  日柱     │  時柱     │
├──────────┼──────────┼──────────┼──────────┤
│    甲     │    丙     │    戊     │    庚     │
│   갑(+)   │   병(+)   │   무(+)   │   경(+)   │
│  [목木]   │  [화火]   │  [토土]   │  [금金]   │  ← 오행 배경색
├──────────┼──────────┼──────────┼──────────┤
│    子     │    寅     │    午     │    申     │
│   자      │   인      │   오      │   신      │
│  [수水]   │  [목木]   │  [화火]   │  [금金]   │  ← 오행 배경색
└──────────┴──────────┴──────────┴──────────┘
         일간(日干): 무토(戊土)
```

- 천간 한자: `Noto Serif KR`, 32px, Bold
- 지지 한자: `Noto Serif KR`, 32px, Bold
- 음양 표시: `(+)` 양간/양지, `(-)` 음간/음지
- 오행 배경: 해당 오행 컬러 10% 투명도
- 일주 강조: 테두리 2px 금박 골드(#C9A96E)

**십성 배치 표시:**

```
           연주   월주   일주   시주
천간 십성  편인   겁재    -    식신
지지 십성  편관   비견   겁재  식신
```

십성 배지: 둥근 모서리 태그, 배경 오행 컬러 20%, 텍스트 오행 컬러

### 5.3 궁합 점수 게이지

**CircularGauge 컴포넌트 (SVG 기반):**

```typescript
// CircularGauge.tsx
// SVG arc path로 원형 게이지 구현
// 0점(하단) → 시계방향 → 100점(하단)
// 점수에 따른 컬러 그라디언트:
// 0~40: #2196F3 (수/水)
// 41~70: #FFC107 (토/土)
// 71~100: #C9A96E (금박 골드)
```

**인터랙션:** 화면 진입 시 0에서 최종 점수까지 1.5초 애니메이션 (`Framer Motion`).

### 5.4 AI 응답 스트리밍 타이핑 효과

**StreamingText 컴포넌트:**
- SSE 토큰 수신 시 문자 단위로 추가
- 커서: `|` 블링크 (500ms 주기, `animate={{ opacity: [1, 0] }}`)
- 스트리밍 완료 후: `react-markdown` + `remark-gfm`으로 마크다운 렌더링
- 한자 용어 파싱: `[편재(偏財)]` 패턴 → `<HanjaTerm>` 버튼 컴포넌트

**스켈레톤 로딩 (AI 응답 대기 중):**
```
 🔮  ████████████████████
      ███████████████
      ████████████████████████
      ██████████
```
- 3줄 스켈레톤, 펄스 애니메이션 (`animate-pulse`)
- 첫 토큰 수신 즉시 스켈레톤 → 실제 텍스트 전환

### 5.5 카드 기반 운세 UI

**DailyFortuneCard 레이아웃:**

```
┌─────────────────────────────────────────┐
│  2026년 3월 25일 (수)    병인(丙寅)일     │  ← 날짜 헤더
│                                          │
│  ★★★★☆  오늘의 종합운                   │  ← 별점
│                                          │
│  오늘은 무토(戊土) 일간에 병인(丙寅)의   │
│  기운이 더해져 창의적인 아이디어가       │
│  풍부한 하루입니다.                     │
│                                          │
│  ┌──────┬──────┬──────┐                 │
│  │연애 ♡│재물 💰│건강 💪│                 │
│  │ ★★★★│ ★★★ │ ★★★★★│                 │
│  └──────┴──────┴──────┘                 │
│                                          │
│  행운의 방향: 동쪽  색상: 청색  숫자: 3 │
│                                          │
│  [전체 운세 보기]          [공유하기]    │
└─────────────────────────────────────────┘
```

**카드 컬러 시스템:**
- 배경: 한지 베이지(#E8D5B7) + 미세 텍스처 CSS (`background-image: url(...)`)
- 테두리: 금박 골드(#C9A96E) 1px
- 그림자: `box-shadow: 0 4px 16px rgba(26, 26, 46, 0.12)`

---

## 6. 디자인 시스템

### 6.1 컬러 팔레트

**Tailwind CSS 커스텀 토큰:**

```typescript
// tailwind.config.ts
const colors = {
  // 브랜드 컬러
  'saju-navy':  '#1A1A2E',    // Primary - 심야 남색 (메인 배경)
  'saju-paper': '#E8D5B7',    // Secondary - 한지 베이지 (카드 배경)
  'saju-gold':  '#C9A96E',    // Accent - 금박 골드 (CTA, 강조)
  'saju-ink':   '#2C2C2C',    // Text Primary - 먹색
  'saju-mist':  '#8B8B8B',    // Text Secondary - 안개회색

  // 오행 컬러 (Five Elements)
  'element-wood':  '#2E7D32',  // 목(木) - 짙은 청록
  'element-fire':  '#C62828',  // 화(火) - 짙은 적색
  'element-earth': '#F57F17',  // 토(土) - 황색
  'element-metal': '#9E9E9E',  // 금(金) - 회백색
  'element-water': '#1565C0',  // 수(水) - 짙은 청색

  // 오행 라이트 (배경 사용)
  'element-wood-light':  '#E8F5E9',
  'element-fire-light':  '#FFEBEE',
  'element-earth-light': '#FFFDE7',
  'element-metal-light': '#F5F5F5',
  'element-water-light': '#E3F2FD',

  // 시맨틱 컬러
  'status-success': '#4CAF50',
  'status-warning': '#FF9800',
  'status-error':   '#F44336',
  'status-info':    '#2196F3',
};
```

**다크 모드:**
- v1.0: 단일 다크 테마 (배경 #1A1A2E가 이미 다크)
- 라이트 모드 전환: v1.1 로드맵

### 6.2 타이포그래피

**폰트 패밀리:**

| 용도 | 폰트 | 파일 |
|------|------|------|
| 주요 UI 텍스트 | Pretendard Variable | `PretendardVariable.woff2` |
| 한자/사주 표시 | Noto Serif KR | Google Fonts |
| 코드/숫자 | Pretendard Variable | (동일) |

**타이포그래피 스케일:**

| 토큰 | 폰트 | 크기 | 굵기 | 행간 | 용도 |
|------|------|------|------|------|------|
| `display-hanja` | Noto Serif KR | 32px | 700 | 1.2 | 사주 한자 기둥 |
| `heading-1` | Pretendard | 28px | 700 | 1.3 | 페이지 제목 |
| `heading-2` | Pretendard | 22px | 600 | 1.4 | 섹션 제목 |
| `heading-3` | Pretendard | 18px | 600 | 1.4 | 카드 제목 |
| `body-lg` | Pretendard | 17px | 400 | 1.6 | 본문 (AI 응답) |
| `body` | Pretendard | 15px | 400 | 1.6 | 일반 본문 |
| `body-sm` | Pretendard | 13px | 400 | 1.5 | 보조 설명 |
| `caption` | Pretendard | 12px | 400 | 1.4 | 레이블, 날짜 |
| `pillar` | Noto Serif KR | 24px | 500 | 1.3 | 사주 기둥 소형 |

**접근성 최소 크기:** 본문 텍스트 최소 15px (Persona C 55세 사용자 고려).

### 6.3 아이콘 시스템

**아이콘 라이브러리:** `lucide-react` (Tree-shakeable, TypeScript 지원)

**커스텀 아이콘 (SVG Sprite):**
- 오행 아이콘 5종 (木/火/土/金/水 전통 문양)
- 천간 아이콘 10종 (甲乙丙丁戊己庚辛壬癸)
- 지지 아이콘 12종 (子丑寅卯辰巳午未申酉戌亥)

**아이콘 사용 원칙:**
- 탭 바: Lucide 아이콘 (선 아이콘, 24px)
- 오행 표시: 커스텀 오행 SVG (32px)
- 상태/피드백: Lucide 아이콘 (CheckCircle, AlertCircle, Info)
- 모든 아이콘에 `aria-label` 또는 `title` 필수

### 6.4 컴포넌트 라이브러리 구조

**디렉토리 구조 (Atomic Design 변형):**

```
src/
├── components/
│   ├── ui/                         # shadcn/ui 기반 원자 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Sheet.tsx               # 바텀시트
│   │   ├── Dialog.tsx              # 모달
│   │   ├── Tabs.tsx
│   │   ├── Badge.tsx
│   │   ├── Skeleton.tsx
│   │   └── Toast.tsx
│   │
│   ├── saju/                       # 사주 도메인 컴포넌트
│   │   ├── FourPillarsTable.tsx    # 사주팔자 표
│   │   ├── FiveElementsChart.tsx   # 오행 레이더/막대 차트
│   │   ├── TenStarsGrid.tsx        # 십성 배치
│   │   ├── DailyFortuneCard.tsx    # 오늘의 운세 카드
│   │   ├── FortuneScoreBar.tsx     # 운세 항목 점수 바
│   │   ├── CircularGauge.tsx       # 궁합 원형 게이지
│   │   └── SajuInputForm.tsx       # 사주 입력 폼
│   │
│   ├── chat/                       # 채팅 도메인 컴포넌트
│   │   ├── MessageBubble.tsx       # 메시지 버블 (AI/User)
│   │   ├── StreamingText.tsx       # 타이핑 스트리밍 텍스트
│   │   ├── HanjaTerm.tsx           # 한자 용어 탭 버튼
│   │   ├── ChatInput.tsx           # 메시지 입력 영역
│   │   ├── QuickReplyChips.tsx     # 빠른 답변 칩
│   │   └── CounselChat.tsx         # 채팅 페이지 컨테이너
│   │
│   ├── layout/                     # 레이아웃 컴포넌트
│   │   ├── AppShell.tsx            # 전체 앱 레이아웃
│   │   ├── BottomTabBar.tsx        # 하단 탭 바
│   │   ├── PageHeader.tsx          # 페이지 헤더
│   │   └── AuthGuard.tsx           # 인증 가드
│   │
│   └── common/                     # 공통 컴포넌트
│       ├── LoadingOverlay.tsx      # 전체 화면 로딩
│       ├── ErrorBoundary.tsx       # 에러 바운더리
│       ├── PremiumGate.tsx         # 유료 잠금 래퍼
│       └── ShareCard.tsx           # SNS 공유 카드
│
├── hooks/                          # 커스텀 훅
│   ├── useSSEStream.ts             # SSE 스트리밍 훅
│   ├── useSajuProfile.ts           # 사주 프로필 TanStack Query
│   ├── useDailyFortune.ts          # 오늘의 운세 훅
│   ├── useAuth.ts                  # 인증 상태 훅
│   ├── usePullToRefresh.ts         # 당겨서 새로고침
│   └── useHaptic.ts                # 진동 피드백 훅
│
├── stores/                         # Zustand 스토어
│   ├── authStore.ts                # 인증 상태 (사용자 정보)
│   ├── profileStore.ts             # 활성 사주 프로필
│   └── uiStore.ts                  # UI 상태 (모달, 바텀시트)
│
├── lib/
│   ├── api/                        # API 클라이언트
│   │   ├── client.ts               # Axios 기반 HTTP 클라이언트
│   │   ├── saju.ts                 # 사주 API 함수
│   │   ├── counsel.ts              # 상담 API 함수
│   │   └── fortune.ts              # 운세 API 함수
│   ├── utils/
│   │   ├── formatSaju.ts           # 사주 데이터 포맷팅
│   │   ├── elementColor.ts         # 오행 → 컬러 매핑
│   │   └── parseSSE.ts             # SSE 이벤트 파싱
│   └── constants/
│       ├── stems.ts                # 천간 상수
│       ├── branches.ts             # 지지 상수
│       └── elements.ts             # 오행 상수
│
└── types/                          # TypeScript 타입 정의
    ├── SajuTypes.ts                # 사주 관련 타입
    ├── CounselTypes.ts             # 상담 관련 타입
    ├── FortuneTypes.ts             # 운세 관련 타입
    └── UserTypes.ts                # 사용자/인증 타입
```

**shadcn/ui 컴포넌트 커스터마이징 원칙:**
- CSS Variables로 테마 오버라이드 (`--primary: #1A1A2E`)
- 컴포넌트 소스 코드 직접 수정 (shadcn 철학 준수)
- 새 variant 추가 시 `cva()` 함수 활용

---

## 7. 기술 스택 상세

### 7.1 Next.js 14 App Router

**디렉토리 구조 (App Router):**

```
app/
├── (auth)/
│   ├── login/
│   │   └── page.tsx              # S-02: 로그인
│   └── callback/
│       └── kakao/
│           └── route.ts          # OAuth 콜백 핸들러
├── (app)/
│   ├── layout.tsx                # 앱 쉘 레이아웃 (탭바)
│   ├── home/
│   │   └── page.tsx              # S-04: 홈 대시보드
│   ├── profile/
│   │   ├── new/
│   │   │   └── page.tsx          # S-05: 사주 입력
│   │   └── [id]/
│   │       └── page.tsx          # S-06: 사주 결과
│   ├── counsel/
│   │   ├── [id]/
│   │   │   └── page.tsx          # S-07: AI 채팅
│   │   └── history/
│   │       └── page.tsx          # S-08: 상담 이력
│   ├── compatibility/
│   │   ├── new/
│   │   │   └── page.tsx          # S-09: 궁합 입력
│   │   └── [id]/
│   │       └── page.tsx          # S-10: 궁합 결과
│   ├── calendar/
│   │   └── page.tsx              # S-11: 운세 캘린더
│   ├── pricing/
│   │   └── page.tsx              # S-12: 구독 플랜
│   ├── payment/
│   │   └── checkout/
│   │       └── page.tsx          # S-13: 결제
│   ├── my/
│   │   └── page.tsx              # S-14: 마이페이지
│   └── settings/
│       └── page.tsx              # S-15: 설정
├── onboarding/
│   └── page.tsx                  # S-03: 온보딩 위자드
├── page.tsx                      # S-01: 랜딩 페이지 (SSG)
├── layout.tsx                    # 루트 레이아웃
├── not-found.tsx
└── error.tsx
```

**렌더링 전략:**

| 화면 | 전략 | 근거 |
|------|------|------|
| 랜딩 페이지 | SSG (Static) | SEO 최적화, 변동 없음 |
| 홈 대시보드 | SSR | 오늘의 운세 서버 페칭 |
| 사주 결과 | SSR | 사주 데이터 초기 페칭 |
| AI 채팅 | CSR | SSE 스트리밍, 실시간 상호작용 |
| 운세 캘린더 | ISR (6h) | 당일 업데이트 충분 |
| 구독 플랜 | SSG | 정적 콘텐츠 |

### 7.2 Tailwind CSS

**설정 파일 (`tailwind.config.ts`) 핵심:**

```typescript
import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.tsx', './components/**/*.tsx'],
  theme: {
    extend: {
      colors: { /* 6.1절 컬러 토큰 */ },
      fontFamily: {
        sans: ['Pretendard Variable', 'system-ui', 'sans-serif'],
        serif: ['Noto Serif KR', 'serif'],
      },
      animation: {
        'typing-cursor': 'blink 0.5s step-end infinite',
        'skeleton-pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fortune-slide': 'slideUp 0.4s ease-out',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'), // AI 응답 마크다운 스타일
  ],
} satisfies Config;
```

### 7.3 Zustand 상태 관리

**스토어 설계:**

```typescript
// stores/authStore.ts
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isPremium: boolean;
  dailyConsultCount: number;
  setUser: (user: User) => void;
  clearAuth: () => void;
  decrementConsultCount: () => void;
}

// stores/profileStore.ts
interface ProfileState {
  activeProfileId: string | null;
  profiles: SajuProfile[];
  setActiveProfile: (id: string) => void;
  addProfile: (profile: SajuProfile) => void;
  removeProfile: (id: string) => void;
}

// stores/uiStore.ts
interface UIState {
  bottomSheet: { isOpen: boolean; content: 'term' | 'limit' | null };
  openBottomSheet: (content: UIState['bottomSheet']['content']) => void;
  closeBottomSheet: () => void;
}
```

**SSR 호환성:** `zustand/middleware`의 `persist` 미들웨어 + `skipHydration` 옵션으로 하이드레이션 불일치 방지.

### 7.4 TanStack Query (React Query)

**쿼리 키 체계:**

```typescript
// lib/queryKeys.ts
export const queryKeys = {
  profile: {
    all: ['profiles'] as const,
    list: () => [...queryKeys.profile.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.profile.all, id] as const,
  },
  fortune: {
    daily: (profileId: string) => ['fortune', 'daily', profileId] as const,
    monthly: (profileId: string, year: number, month: number) =>
      ['fortune', 'monthly', profileId, year, month] as const,
  },
  counsel: {
    history: () => ['consultations', 'history'] as const,
    detail: (id: string) => ['consultations', id] as const,
  },
};
```

**캐싱 전략:**

| 쿼리 | staleTime | gcTime | refetchOnWindowFocus |
|------|-----------|--------|----------------------|
| 사주 프로필 | 5분 | 10분 | false |
| 오늘의 운세 | 1시간 | 24시간 | false |
| 상담 이력 | 1분 | 5분 | true |
| 구독 상태 | 30초 | 5분 | true |

### 7.5 Recharts (차트 시각화)

**사용 차트 컴포넌트:**

| 차트 | 컴포넌트 | 용도 |
|------|----------|------|
| 오행 레이더 | `RadarChart` | 사주 결과 - 오행 분포 |
| 오행 막대 | `BarChart` + `Bar` | 모바일 대안 / 궁합 비교 |
| 운세 점수 | 커스텀 SVG | 원형 게이지 (CircularGauge) |
| 대운 타임라인 | `LineChart` | 대운 흐름 시각화 |

**동적 import (성능 최적화):**
```typescript
// app/(app)/profile/[id]/page.tsx
const FiveElementsChart = dynamic(
  () => import('@/components/saju/FiveElementsChart'),
  { loading: () => <Skeleton className="h-64 w-full rounded-xl" /> }
);
```

### 7.6 Framer Motion (애니메이션)

**사용 시나리오:**

| 애니메이션 | 컴포넌트 | 구현 |
|-----------|----------|------|
| 사주 결과 진입 | `FourPillarsTable` | 4기둥 stagger 등장 |
| 타이핑 커서 | `StreamingText` | opacity 0↔1 반복 |
| 궁합 게이지 | `CircularGauge` | 0→최종값 arc 애니메이션 |
| 바텀시트 | `Sheet` | y 슬라이드 업/다운 |
| 페이지 전환 | `AnimatePresence` | fade + slide |
| 운세 카드 | `DailyFortuneCard` | 카드 플립 (오늘 결과 공개) |

**성능 원칙:**
- `will-change: transform` 필요한 곳에만 적용 (GPU 과사용 방지)
- `layout` 애니메이션은 목록 재정렬에만 사용
- `ReducedMotion` 미디어 쿼리 존중 (`useReducedMotion` 훅)

---

*이 문서는 PRD v1.0 및 아키텍처 v1.0을 기반으로 작성되었으며, 개발 진행에 따라 업데이트됩니다.*
