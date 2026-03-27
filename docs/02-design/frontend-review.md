# MỆnh — 프론트엔드 현황 검토 보고서

> **Version:** 1.0
> **Date:** 2026-03-26
> **Author:** Frontend Architect
> **대상 파일:** `web/index.html`, `web/css/style.css`, `web/js/app.js`, `web/js/saju-engine.js`
> **기준 문서:** PRD v1.0, Frontend Design v1.0, UI Wireframe v1.0

---

## 목차

1. [현재 UI/UX 문제점 분석](#1-현재-uiux-문제점-분석)
2. [필요한 이미지 에셋 정의](#2-필요한-이미지-에셋-정의)
3. [디자인 시스템 산출물 정의](#3-디자인-시스템-산출물-정의)
4. [화면별 디자인 산출물 목록](#4-화면별-디자인-산출물-목록)
5. [애니메이션/모션 정의](#5-애니메이션모션-정의)
6. [현재 구현 vs 목표 설계 갭 요약](#6-현재-구현-vs-목표-설계-갭-요약)

---

## 1. 현재 UI/UX 문제점 분석

### 1.1 레이아웃 문제

**단일 HTML 파일 구조의 한계**

현재 전체 앱이 `index.html` 하나에 7개 화면이 `display:none/block`으로 전환되는 SPA 흉내 구조다. 이는 다음 문제를 일으킨다.

- 화면 전환 시 스크롤 위치가 항상 맨 위로 초기화됨 (`window.scrollTo` 호출로 임시 처리 중이나 근본 해결이 아님)
- 각 화면의 DOM이 항상 렌더링되어 있어 메모리 낭비 발생
- URL이 변경되지 않아 뒤로가기 버튼이 동작하지 않음 — 베트남 Android 사용자 다수가 물리적 뒤로가기를 사용하므로 심각한 UX 결함

**헤더-콘텐츠-바텀 네비 레이아웃 충돌**

```
현재 구조:
  <header class="hdr">  ← static, 항상 표시
  <div class="wrap">    ← padding-bottom: 120px (과도함)
  <nav class="bnav">    ← fixed bottom
```

- `hdr`가 모든 화면에서 동일하게 표시되므로 사주 입력 화면에서도 "당신의 이야기를 들려드릴게요" 문구가 보임 — 온보딩 맥락과 어울리지 않음
- `max-width: 440px`인 `.wrap`과 `max-width: 440px`인 `.bnav`가 각각 별도로 중앙 정렬되어 있어 화면 너비가 정확히 440px이 아닌 경우 미세 정렬 불일치 가능
- `padding-bottom: 120px`은 iOS Safe Area를 고려한 것이나 `env(safe-area-inset-bottom)` CSS 변수를 `.wrap`에 직접 적용하지 않아 다양한 기기에서 콘텐츠가 네비에 가릴 수 있음

**그리드 시스템 부재**

- 6개 주제 버튼이 `grid-template-columns: repeat(2, 1fr)` 2열 고정으로, 360px 미만 기기에서 텍스트 줄바꿈 발생
- 운세 3버튼은 `.row`에 `flex:1`을 각 버튼에 부여하는 방식으로, 주제 그리드와 간격 체계가 일치하지 않음 (gap: 10px vs gap: 없음)
- 화면 구조마다 margin/padding이 인라인 스타일(`style="margin-top:4px"`, `style="padding:4px 2px"`)로 박혀 있어 일관성 없음

### 1.2 비주얼 디자인 완성도

**컬러 시스템 불완전**

현재 정의된 CSS 변수:
```css
--bg, --card, --text, --sub, --dim, --accent, --accent-light,
--accent-glow, --gold, --gold-light, --pink, --green, --green-light, --border
```

- `--pink: #F06292`가 "점수 낮음"의 의미로만 쓰임 — 연애 테마 컬러와 혼용 가능성
- `--green: #43A047`과 오행 "목(木)"의 그린이 별도로 존재 (`ELEMENT_COLORS["목"] = #16A34A`) — 두 그린이 시각적으로 충분히 구별되지 않으면서 의미가 다름
- 오행 5색이 CSS 변수가 아닌 JS 객체(`ELEMENT_COLORS`)로만 관리되어 CSS와 JS 간 디자인 토큰 분리 불가
- 에러/성공/경고 상태 색상(Semantic 컬러) 정의 없음
- `--energy-up/stable/change/rest` 4가지 에너지 뱃지 색상이 클래스로만 존재하고 CSS 변수화되지 않음

**타이포그래피 스케일 불규칙**

코드 내 발견된 폰트 크기 목록 (중복 포함):
```
10px, 11px, 12px, 13px, 14px, 15px, 15.5px, 16px, 18px, 20px, 22px, 28px, 36px
```

- `15.5px`은 명백한 임의 수치 — 타이포 스케일 정의 없이 눈대중 조정
- `font-weight`도 300/400/500/600/700/800/900을 혼용 중이나 각 weight의 사용 맥락이 정의되지 않음
- 행간(`line-height`)이 `1.7`, `1.8`, `1.3` 등 비일관적으로 적용됨
- 베트남어와 한국어의 자소 높이 차이로 인해 동일 폰트 크기에서 베트남어 텍스트가 더 크게 보이는 현상 미처리

**카드 디자인 위계 불명확**

카드 클래스: `.card-intro`(보라 좌측 보더), `.card-ilgan`(금 좌측 보더), `.card-combo`(초록 좌측 보더), `.card-today`(보라 풀컬러), `.card-cheer`(금 배경)

- 5개 카드 타입 중 어떤 게 더 중요한지 시각적 위계 불명확 — `card-today`만 배경이 꽉 차 있고 나머지는 좌측 보더로만 구분
- `.cd` 공통 카드에 `box-shadow: 0 2px 12px rgba(0,0,0,.04)` 적용 중이나 그림자가 너무 약해 카드-배경 구분이 모바일 화면에서 어려움
- 카드 내부 패딩이 `24px 22px`로 비대칭 (수직 24px, 수평 22px) — 의도적 비대칭이면 이유 없음

**이모지 의존성**

현재 모든 아이콘이 유니코드 이모지: ❤️ 💼 💰 🪞 💑 🌏 ☀️ 🌙 ⭐ 🏠 등

- iOS/Android/Windows 간 이모지 렌더링이 다름 — 특히 💑 이모지는 iOS 15 이후 스킨톤 변경 정책으로 표시 방식이 달라짐
- 이모지는 크기 조절 시 계단 현상 발생 가능, 고해상도 디스플레이에서 선명도 저하
- 앱의 프리미엄 감을 저해 — 베트남 MZ 타겟 경쟁 앱(AstroSage, TimePassages 등)은 모두 커스텀 SVG 아이콘 사용

### 1.3 UX 플로우 문제

**온보딩 맥락 단절**

현재 플로우: 생년월일 입력 → 즉시 홈

- 이름/별명 입력 없음 — 모든 풀이가 "당신"으로 시작하여 개인화 느낌 약함
- 관심사 선택 단계 없음 — 첫 홈에서 6개 주제 중 무엇을 먼저 볼지 방향 제시 없음
- 양력/음력 선택 없음 — 베트남은 음력 생일(âm lịch)을 매우 중시하는 문화. 이 부재는 현지화 치명 결함
- 입력 성공/실패 피드백 없음 (`if (!y || !m || !d) return;`으로 조용히 실패)

**대화형 플로우 끊김**

`FOLLOW_UPS` 트리 구현 분석:
- `love`만 3단 깊이(level 0 → love_inrel/love_single/love_some → fight/cold/marriage 등) 구현
- `career`, `money`, `self`, `general`은 모두 level 0 하나만 있고 2단 이후 없음 → `showFinalCards`로 바로 점프
- 사용자가 답변 선택 후 `topicDepth < 3` 조건으로 다음 질문 분기하는데, 실제로 2단 이후 데이터 없으면 `showFinalCards`가 즉시 실행 — 1번 답하면 바로 결과가 나와 "대화형" 경험이 무색

**네비게이션 불완전**

현재 바텀 네비: 홈 / 오늘 / 궁합 — 3탭만 존재

- "상담하기(주제 선택)" 탭 없음 — 메인 기능이 홈에 숨어있음
- 활성 탭 상태(`.on` 클래스)가 `go()` 함수 내에서 화면 전환 시 자동 업데이트 되지 않음 — 예: `go('scr-monthly')` 호출 시 바텀 네비는 여전히 "홈"이 활성 상태
- 뒤로가기 버튼이 각 화면 하단에 `<button onclick="go('scr-home')">` 형태로 존재하나 "monthly/yearly" 화면에는 `data-ko/vi` 국제화 속성이 누락되어 베트남어 전환 시 한국어 노출

**궁합 화면 UX 미흡**

- 상대방 성별 선택 없음 (`calculateSaju`에 `'male'` 하드코딩)
- 궁합 점수 계산: `58 + (new Date().getDate() % 7) - 3` 에서 날짜에 따라 ±3 변동 — 같은 두 사람인데 날짜마다 점수가 달라지는 것은 신뢰성 저하
- 궁합 결과 텍스트가 3종(high/mid/low)으로 고정 — 일간 조합이 100가지인 것에 비해 너무 단순

**로딩 상태 처리**

`.ld` 로딩 컴포넌트가 존재하나 현재 `runCalc()`에서 전혀 사용하지 않음 — 사주 계산이 동기 처리라 실제로 로딩이 필요 없지만, 향후 AI API 연동 시 로딩 UI 연결 구조가 없음

### 1.4 모바일 최적화 이슈

**터치 타겟 크기 미달**

- `.bnav-i` 바텀 네비 버튼: 높이 `8px padding + 22px icon + 2px gap + 10px font + 8px padding` ≈ 52px — Apple HIG 기준 44pt, Material 기준 48dp 겨우 충족
- `.lang-btn`: `padding: 5px 16px` → 높이 약 28px — 터치 타겟 최소 기준 미달
- `.follow-btn` (inline style): `padding: 14px 16px` — 적절
- `.sit-btn`: `padding: 18px 14px` — 적절하나 360px 기기에서 2열 배치 시 각 버튼 너비가 약 160px으로 작아짐

**입력 폼 모바일 UX**

- 년도 입력이 `type="number"` — 모바일에서 숫자 키패드 열리나 +/- 버튼이 같이 표시됨, iOS에서는 키패드 위 도구 모음이 뜨는 문제
- 원/열 드롭다운(`<select>`)이 24개 옵션 — iOS에서는 드럼롤, Android에서는 다이얼로그로 보여 크로스플랫폼 경험 불일치
- 베트남 사용자 기준으로 `placeholder="1995"` 같은 힌트가 한국 기준 기본값 — 베트남 MZ 평균 출생연도 고려 필요

**스크롤 UX**

- `window.scrollTo({top: 0, behavior: 'smooth'})` — `scr.on` 전환 시 매번 최상단 이동. 이 방식은 화면 전환 애니메이션 없이 즉시 전환 후 스크롤 이동이라 깜빡임 느낌
- `followEl.scrollIntoView({behavior: 'smooth', block: 'start'})` — 질문 선택 후 다음 질문이 뷰에 들어오도록 스크롤하나, 때로 바텀 네비에 가려질 수 있음 (바텀 네비가 fixed이므로)
- `-webkit-overflow-scrolling: touch` 미설정 (오래된 iOS 관성 스크롤 이슈)

**폰트 로딩**

- `<head>`에서 Google Fonts를 `<link>` 태그로 로드 — 콜드 스타트 시 FOUT(Flash of Unstyled Text) 발생
- `display=swap` 파라미터 사용 중이나 Be Vietnam Pro가 없을 때 `-apple-system`으로 폴백하면 베트남어 자소 일부가 깨질 수 있음 (`ệ`, `ắ`, `ổ` 등 성조 문자)

### 1.5 접근성 이슈

**시맨틱 HTML 부재**

```html
<div class="sit-btn" onclick="startTopic('love')">  <!-- div에 click 핸들러 -->
<div class="sit-btn" onclick="go('scr-compat')">
```

- 버튼 역할을 하는 `<div>`에 `role="button"`, `tabindex="0"`, `aria-label`이 없음
- 키보드 탐색 불가 — Tab 키로 포커스 이동 시 이 요소들을 건너뜀

**색상 대비 미달 항목**

| 요소 | 전경 | 배경 | 대비비(추정) | 기준 |
|------|------|------|------------|------|
| `.cd-t` | `#6C4FE0` | `#FFFFFF` | 4.2:1 | AA 4.5:1 미달 |
| `.bnav-i` 비활성 | `#AEA8C4(--dim)` | `#FFFFFF` | 2.8:1 | AA 4.5:1 미달 |
| `.hdr p` | `#7B7394(--sub)` | `#F5F3FA(--bg)` | 3.1:1 | AA 4.5:1 미달 |
| `.mini-p .lbl` | `#AEA8C4(--dim)` | `#F5F3FA(--bg)` | 2.4:1 | AA 4.5:1 미달 |
| `.kw` 키워드 뱃지 | `#6C4FE0` | `#EDE8FF` | 4.0:1 | AA 4.5:1 미달 |

**폼 접근성**

- `<label for>` 연결 없음 — 현재 label이 input과 시각적으로 인접해 있으나 `for/id` 연결이 없어 스크린리더에서 입력 필드와 레이블이 연결되지 않음
- 필수 입력 항목에 `aria-required="true"` 없음
- 에러 상태(`aria-invalid`, `aria-describedby`)가 전혀 없음
- 선택된 언어 버튼에 `aria-pressed="true"` 없음

**포커스 관리**

- 화면 전환 시(`go()`) 포커스가 이전 화면 마지막 위치에 남음 — 스크린리더 사용자는 새 화면의 H1으로 포커스가 이동해야 함
- 모달성 플로우(주제 선택 → 결과 카드 추가)에서 새로 추가된 카드로 포커스 이동 없음

**다국어 HTML Lang 속성**

```html
<html lang="ko">  <!-- 고정 -->
```

- 언어 전환 버튼 클릭 시 `document.documentElement.lang` 속성이 업데이트되지 않음 — 스크린리더가 베트남어 텍스트를 한국어로 잘못 읽음

---

## 2. 필요한 이미지 에셋 정의

### 2.1 앱 아이콘 / 파비콘

현재 상태: `favicon.ico` 없음 (브라우저 기본 아이콘 표시)

| 에셋명 | 규격 | 포맷 | 용도 | 우선순위 |
|--------|------|------|------|---------|
| `icon-16.png` | 16x16px | PNG | 브라우저 탭 파비콘 | P0 |
| `icon-32.png` | 32x32px | PNG | 브라우저 탭 파비콘 (레티나) | P0 |
| `icon-180.png` | 180x180px | PNG | iOS 홈 화면 추가 (apple-touch-icon) | P0 |
| `icon-192.png` | 192x192px | PNG | Android PWA 아이콘 | P0 |
| `icon-512.png` | 512x512px | PNG | PWA 스플래시 / 앱스토어 | P0 |
| `icon-maskable-512.png` | 512x512px | PNG | Android Adaptive Icon (safe zone 80%) | P1 |
| `favicon.svg` | 벡터 | SVG | 모던 브라우저 벡터 파비콘 | P1 |

**디자인 방향:** "MỆnh" 타이틀의 "M"자 또는 오행 원(五行圓) 모티프. 배경 `#1A1A2E`, 아이콘 `#C9A96E` 금박 라인아트. 성조 부호(ệ)가 포함된 로고타입보다 단순한 심볼 마크 권장.

### 2.2 온보딩 일러스트레이션

| 에셋명 | 규격 | 포맷 | 내용 | 우선순위 |
|--------|------|------|------|---------|
| `onboarding-step1.svg` | 280x200px | SVG/Lottie | 별자리/밤하늘 + 사람 실루엣 — "당신의 별자리를 찾아요" | P0 |
| `onboarding-step2.svg` | 280x200px | SVG/Lottie | 달력 + 오행 원소 아이콘들 — "생년월일로 사주를 계산해요" | P0 |
| `onboarding-step3.svg` | 280x200px | SVG/Lottie | AI 채팅 말풍선 + 카드 — "당신만을 위한 풀이를 드려요" | P0 |
| `landing-hero.svg` | 390x480px | SVG | 랜딩 히어로 이미지 — 밤하늘 배경 + 사주 팔자 카드 3장 부유 | P0 |
| `empty-state-history.svg` | 200x160px | SVG | 빈 상담 이력 — "첫 상담을 시작해보세요" | P1 |
| `empty-state-compat.svg` | 200x160px | SVG | 빈 궁합 — "궁합 볼 상대를 추가해보세요" | P1 |

**스타일 가이드:** 미니멀 라인아트 + 부드러운 그라데이션 음영. 한복/동양화 요소 금지 (베트남 MZ에게 이질감). 별, 달, 구름, 수정구 같은 신비 판타지 요소 활용. 컬러 팔레트는 `#1A1A2E ~ #2D2D5E` 배경에 `#C9A96E`, `#E8D5B7` 골드 포인트.

### 2.3 카드 배경 패턴/텍스처

| 에셋명 | 규격 | 포맷 | 내용 | 우선순위 |
|--------|------|------|------|---------|
| `card-bg-wood.svg` | 타일 패턴 | SVG | 목(木) — 대나무/잎사귀 미세 패턴, 녹색 계열 | P1 |
| `card-bg-fire.svg` | 타일 패턴 | SVG | 화(火) — 불꽃/파동 미세 패턴, 붉은 계열 | P1 |
| `card-bg-earth.svg` | 타일 패턴 | SVG | 토(土) — 산/육각형 미세 패턴, 황토 계열 | P1 |
| `card-bg-metal.svg` | 타일 패턴 | SVG | 금(金) — 기하학/원 미세 패턴, 회금 계열 | P1 |
| `card-bg-water.svg` | 타일 패턴 | SVG | 수(水) — 파도/물결 미세 패턴, 청남색 계열 | P1 |
| `card-bg-premium.png` | 800x400px | PNG | 프리미엄 카드 배경 — 밤하늘 그라데이션 + 금박 별 | P0 |
| `noise-texture.png` | 200x200px | PNG | 카드 오버레이 노이즈 텍스처 — 인쇄물 느낌 (opacity 4%) | P2 |

**활용 방법:** SVG 패턴을 CSS `background-image`로 연결, 투명도 6-8%로 카드 배경에 오버레이. 과도한 패턴은 텍스트 가독성 저해 — 반드시 opacity 제한.

### 2.4 오행 아이콘 세트

5개 원소 × 3가지 변형 = 15개 SVG 파일

| 원소 | 파일명 | 심볼 모티프 | 컬러 |
|------|--------|------------|------|
| 목(木) | `element-wood.svg` | 나뭇잎/새싹 — 성장, 생명력 | `#2E7D32` |
| 화(火) | `element-fire.svg` | 불꽃/태양 — 열정, 활동성 | `#C62828` |
| 토(土) | `element-earth.svg` | 산/사각형 — 안정, 중심 | `#F57F17` |
| 금(金) | `element-metal.svg` | 원/보석 — 정밀함, 가치 | `#757575` |
| 수(水) | `element-water.svg` | 파도/물방울 — 지혜, 흐름 | `#1565C0` |

각 원소별 3가지 변형:
- `element-{name}-filled.svg` — 솔리드 아이콘 (24x24px, 대형 표시)
- `element-{name}-outline.svg` — 아웃라인 아이콘 (24x24px, 일반 표시)
- `element-{name}-badge.svg` — 배지형 원형 아이콘 (32x32px, 뱃지/태그 용도)

### 2.5 상황별 아이콘 (주제 선택 그리드)

현재 이모지 대체 커스텀 SVG:

| 주제 | 파일명 | 모티프 | 현재 이모지 |
|------|--------|--------|------------|
| 연애 | `topic-love.svg` | 하트 + 두 별 | ❤️ |
| 직업·진로 | `topic-career.svg` | 나침반 + 화살표 | 💼 |
| 돈·재물 | `topic-money.svg` | 동전 + 상승 그래프 | 💰 |
| 나 자신 | `topic-self.svg` | 연꽃/자아 원 | 🪞 |
| 궁합 | `topic-compat.svg` | 음양 + 두 별 | 💑 |
| 인생 전반 | `topic-general.svg` | 지구/우주 원 | 🌏 |

바텀 네비 아이콘:
| 탭 | 파일명 |
|---|--------|
| 홈 | `nav-home.svg` |
| 오늘운세 | `nav-today.svg` |
| 상담 | `nav-counsel.svg` |
| 궁합 | `nav-compat.svg` |
| 마이 | `nav-my.svg` |

유틸리티 아이콘 (16x16, 20x20, 24x24 3종 세트):
`icon-arrow-right.svg`, `icon-arrow-left.svg`, `icon-close.svg`, `icon-share.svg`, `icon-copy.svg`, `icon-refresh.svg`, `icon-lock.svg`, `icon-star.svg`, `icon-star-filled.svg`, `icon-chevron-down.svg`, `icon-info.svg`

### 2.6 로딩 애니메이션

| 에셋명 | 포맷 | 내용 | 우선순위 |
|--------|------|------|---------|
| `loading-crystal.json` | Lottie JSON | 수정구 빛나는 애니메이션 — AI 분석 중 (2-3초 루프) | P0 |
| `loading-stars.json` | Lottie JSON | 별 반짝임 + 오행 원소 순환 — 사주 계산 중 (1.5초 루프) | P0 |
| `loading-dots.svg` | CSS 애니메이션 | 현재 `.dots span` 구현 업그레이드 — 사용 빈도 높음 | P0 |
| `skeleton-card.svg` | SVG | 카드 스켈레톤 UI — 콘텐츠 로딩 플레이스홀더 | P1 |

**현재 로딩 구현 문제:** `.ld` 로딩 컴포넌트가 `runCalc()` 함수에서 전혀 호출되지 않음. 향후 AI API 비동기 처리 시 로딩 표시가 필요.

### 2.7 빈 상태(Empty State) 일러스트

| 에셋명 | 규격 | 내용 | 노출 조건 |
|--------|------|------|---------|
| `empty-counsel-history.svg` | 160x120px | 빈 책 + 별 — "아직 상담 이력이 없어요" | 상담 이력 없을 때 |
| `empty-compatibility.svg` | 160x120px | 빈 하트 두 개 — "궁합 볼 상대를 찾아보세요" | 저장된 궁합 없을 때 |
| `empty-search.svg` | 160x120px | 돋보기 + 별 — "찾는 결과가 없어요" | 검색 결과 없을 때 |
| `error-network.svg` | 160x120px | 번개 + 구름 — "연결에 문제가 생겼어요" | 네트워크 오류 |
| `error-server.svg` | 160x120px | 로봇 + 물음표 — "잠시 후 다시 시도해 주세요" | 서버 오류 |

### 2.8 공유 카드 템플릿 (SNS용)

베트남 MZ 주요 SNS: Facebook, TikTok, Zalo, Instagram

| 에셋명 | 규격 | 포맷 | 용도 |
|--------|------|------|------|
| `share-card-result.png` | 1080x1080px | PNG (동적 생성) | 사주 결과 Instagram/Facebook 정사각형 | P0 |
| `share-card-daily.png` | 1080x1080px | PNG (동적 생성) | 오늘의 운세 한 줄 공유 | P0 |
| `share-card-compat.png` | 1080x1920px | PNG (동적 생성) | 궁합 점수 TikTok/Instagram Story | P1 |
| `share-card-cheer.png` | 1080x1080px | PNG (동적 생성) | 응원 메시지 카드 공유 | P1 |

**구현 방식:** `html2canvas` 또는 Canvas API를 통해 클라이언트에서 동적 생성. 템플릿 PSD/Figma 파일을 별도 보관하여 디자이너가 시즌 변경 가능하도록.

**카드 레이아웃 공통 구성:**
- 상단: MỆnh 로고 + 브랜드 컬러 배경
- 중앙: 사주/결과 핵심 내용 (한국어 또는 베트남어)
- 하단: "menhapp.com 에서 무료로 확인하기" CTA

### 2.9 OG 이미지 (Open Graph)

| 에셋명 | 규격 | 포맷 | 내용 |
|--------|------|------|------|
| `og-default.jpg` | 1200x630px | JPG | 기본 OG — MỆnh 로고 + "AI가 풀어주는 나의 사주 이야기" | P0 |
| `og-counsel.jpg` | 1200x630px | JPG | 상담 페이지 OG — AI 채팅 인터페이스 미리보기 | P1 |
| `og-compat.jpg` | 1200x630px | JPG | 궁합 페이지 OG — 두 사람 별자리 결합 이미지 | P1 |

---

## 3. 디자인 시스템 산출물 정의

### 3.1 컬러 팔레트

기존 메모리(`project_saju_ai.md`)에 Primary `#1A1A2E`, Accent `#C9A96E`로 정의되어 있으나, 현재 구현은 `#6C4FE0`(보라 계열)을 accent로 사용. 두 디자인 간 브랜드 컬러 불일치 → 아래는 현행 구현 기반으로 정리하되 권고 방향 명시.

#### 브랜드 코어 컬러

```
현행: --accent #6C4FE0 (보라-인디고)
권고: --accent #7B5CF0 (더 밝고 생동감 있는 보라, MZ 타겟 적합)

이유: #6C4FE0은 배경 #FFFFFF 위에서 대비비 4.2:1로 WCAG AA 미달.
     #7B5CF0으로 조정 시 4.6:1 달성.
```

#### 전체 컬러 토큰 체계

```css
/* === 브랜드 === */
--color-brand-50:  #F5F0FF;
--color-brand-100: #EDE8FF;   /* 현행 --accent-light */
--color-brand-200: #D4C4FF;
--color-brand-300: #B39DFF;
--color-brand-400: #9575FF;
--color-brand-500: #7B5CF0;   /* Primary Accent (권고) */
--color-brand-600: #6C4FE0;   /* 현행 --accent */
--color-brand-700: #5A3DC7;
--color-brand-800: #462EA0;
--color-brand-900: #1A1A2E;   /* 설계 문서 Primary */

/* === 골드 (보조 강조) === */
--color-gold-50:  #FFF8EC;    /* 현행 --gold-light */
--color-gold-100: #FFECC8;
--color-gold-200: #FFD98A;
--color-gold-300: #FFC24D;
--color-gold-400: #E8A830;
--color-gold-500: #D4A843;    /* 현행 --gold */
--color-gold-600: #C9A96E;    /* 설계 문서 Accent Gold */
--color-gold-700: #A07C35;

/* === 중립 (Neutral) === */
--color-neutral-0:   #FFFFFF;
--color-neutral-50:  #F5F3FA;   /* 현행 --bg */
--color-neutral-100: #ECEAF5;
--color-neutral-200: #E8E4F2;   /* 현행 --border */
--color-neutral-300: #D0CAE8;
--color-neutral-400: #AEA8C4;   /* 현행 --dim */
--color-neutral-500: #7B7394;   /* 현행 --sub */
--color-neutral-600: #5A5272;
--color-neutral-700: #3D3558;
--color-neutral-800: #2A2440;   /* 현행 --text */
--color-neutral-900: #1A1530;

/* === 오행 컬러 (Five Elements) === */
--color-wood-bg:      #DCFCE7;
--color-wood-text:    #16A34A;
--color-wood-accent:  #2E7D32;   /* 설계 문서 기준 (짙은 녹) */

--color-fire-bg:      #FEE2E2;
--color-fire-text:    #DC2626;
--color-fire-accent:  #C62828;

--color-earth-bg:     #FEF9C3;
--color-earth-text:   #CA8A04;
--color-earth-accent: #F57F17;

--color-metal-bg:     #EDE9FE;
--color-metal-text:   #7C3AED;
--color-metal-accent: #757575;   /* 은/회색 계열로 통일 */

--color-water-bg:     #DBEAFE;
--color-water-text:   #2563EB;
--color-water-accent: #1565C0;

/* === 시맨틱 컬러 === */
--color-success-bg:   #E8F5E9;
--color-success:      #2E7D32;   /* 성공/긍정 */
--color-warning-bg:   #FFF8E1;
--color-warning:      #F57F17;   /* 주의/중간 */
--color-danger-bg:    #FFEBEE;
--color-danger:       #C62828;   /* 오류/부정 */
--color-info-bg:      #E3F2FD;
--color-info:         #1565C0;   /* 안내/정보 */
```

#### 다크모드 대응

현재 다크모드 미지원. 베트남 MZ 사용 행태상 야간 사용 빈도가 높고, 사주/신비 콘텐츠는 어두운 배경이 컨셉에도 맞음. **다크모드 우선 구현 권고.**

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg:           #0F0D1A;
    --card:         #1C1830;
    --text:         #F0EEF8;
    --sub:          #A89FC0;
    --dim:          #6B6480;
    --border:       #2D2850;
    --accent-light: #1E1540;
  }
}
```

### 3.2 타이포그래피 스케일

#### 폰트 패밀리

```css
/* UI 텍스트 — 베트남어/한국어 모두 지원 */
--font-sans: 'Be Vietnam Pro', 'Pretendard Variable', -apple-system, BlinkMacSystemFont, sans-serif;

/* 장식/타이틀 — 영문 로고/대형 숫자 */
--font-serif: 'Playfair Display', 'Noto Serif KR', serif;

/* 사주 한자 표시 전용 */
--font-hanja: 'Noto Serif KR', 'Noto Serif SC', serif;

/* 숫자/코드 */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

**주의:** 현재 Be Vietnam Pro + Playfair Display 조합은 유지. 단, Pretendard를 fallback으로 추가하여 한국어 최적화. 설계 문서(Pretendard + Noto Serif KR)와 통합 필요.

#### 타입 스케일 (8pt 그리드 기반)

| 토큰명 | 크기 | Line-height | Weight | 용도 |
|--------|------|------------|--------|------|
| `--text-xs` | 11px | 1.5 | 400 | 레이블, 타임스탬프 |
| `--text-sm` | 13px | 1.6 | 400/500 | 보조 텍스트, 캡션 |
| `--text-base` | 15px | 1.7 | 400 | 본문 (현행 15.5px → 15px 통일) |
| `--text-md` | 16px | 1.7 | 500/600 | 강조 본문, 버튼 |
| `--text-lg` | 18px | 1.6 | 600 | 카드 헤드라인 |
| `--text-xl` | 20px | 1.4 | 700 | 폼 타이틀, 섹션 제목 |
| `--text-2xl` | 24px | 1.3 | 700/800 | 화면 타이틀 |
| `--text-3xl` | 30px | 1.2 | 800 | 히어로 타이틀 |
| `--text-4xl` | 36px | 1.1 | 900 | 브랜드 로고 (현행 유지) |

**삭제 대상:** `15.5px` → `15px`로 통일, `22px` → `--text-2xl(24px)` 또는 `--text-xl(20px)` 중 선택.

#### 베트남어 타이포 보정

```css
/* 베트남어 성조 부호가 있는 텍스트의 line-height 보정 */
[lang="vi"] .cd-body,
[lang="vi"] .follow-btn {
  line-height: 1.9;   /* 기본 1.7에서 0.2 증가 */
}
```

### 3.3 아이콘 시스템

| 항목 | 결정 사항 |
|------|---------|
| 기본 아이콘 라이브러리 | Lucide Icons (MIT, React/SVG 지원, shadcn/ui 기본 의존) |
| 커스텀 아이콘 | 오행 5종 + 주제 6종 + SNS 공유 3종 = 총 14종 커스텀 SVG |
| 이모지 완전 제거 | 바텀 네비, 주제 그리드, 행운 정보 섹션의 모든 이모지를 SVG로 대체 |
| 크기 규격 | 16px(소), 20px(중), 24px(대), 32px(XL — 주제 카드) |
| 색상 방식 | `currentColor` 사용 — 컨텍스트 색상 자동 상속 |
| 파일 구조 | `/public/icons/` 폴더, SVG sprite 또는 개별 import |

### 3.4 컴포넌트 목록

#### P0 (MVP 필수)

| 컴포넌트명 | 파일명 | 현재 상태 | 설명 |
|-----------|--------|---------|------|
| Button | `Button.tsx` | `.btn` CSS만 있음 | variant(primary/secondary/ghost/danger), size(sm/md/lg), loading state |
| Card | `Card.tsx` | `.cd` + 5가지 variant | 카드 래퍼, type(intro/ilgan/combo/today/cheer/fortune) |
| Input | `Input.tsx` | `.grp input` CSS만 | text/number, label, error state, hint text |
| Select | `Select.tsx` | `<select>` raw HTML | 드럼롤 스타일 커스텀 드롭다운 |
| Badge | `Badge.tsx` | `.kw` CSS만 | 키워드 뱃지, 오행 뱃지, 점수 뱃지 |
| BottomNav | `BottomNav.tsx` | `.bnav` CSS + HTML | 4탭 (설계 문서 기준), 활성 상태 관리 |
| LoadingSpinner | `LoadingSpinner.tsx` | `.dots` CSS 있음 | Lottie + dots fallback |
| FortuneScoreBar | `FortuneScoreBar.tsx` | inline HTML/CSS | 분야별 운세 점수 바 |
| ElementBadge | `ElementBadge.tsx` | `.energy-badge` | 오행 원소 뱃지 (목/화/토/금/수) |
| LanguageToggle | `LanguageToggle.tsx` | `.lang-btn` CSS | ko/vi 토글, i18n 연동 |

#### P1 (1차 릴리즈)

| 컴포넌트명 | 파일명 | 설명 |
|-----------|--------|------|
| DatePickerDrum | `DatePickerDrum.tsx` | iOS 드럼롤 스타일 날짜 선택 |
| CompatibilityScore | `CompatibilityScore.tsx` | 원형 점수 게이지 + 일간 표시 |
| MiniPillars | `MiniPillars.tsx` | 사주 4기둥 미니 표시 (현행 renderMiniPillars 리팩터) |
| FollowUpQuestion | `FollowUpQuestion.tsx` | 대화형 질문-선택지 카드 |
| ShareCard | `ShareCard.tsx` | Canvas 기반 SNS 공유 카드 생성 |
| SkeletonCard | `SkeletonCard.tsx` | 카드 로딩 스켈레톤 UI |
| Toast | `Toast.tsx` | 피드백 토스트 메시지 |
| BottomSheet | `BottomSheet.tsx` | 한자 용어 해설, 추가 정보 바텀시트 |
| OnboardingStep | `OnboardingStep.tsx` | 스텝 인디케이터 + 일러스트 |
| EnergyBadge | `EnergyBadge.tsx` | 에너지 상태 뱃지 (상승/안정/변화/휴식) |

#### P2 (2차)

| 컴포넌트명 | 설명 |
|-----------|------|
| `OhaengRadarChart.tsx` | 오행 레이더 차트 (Recharts) |
| `CalendarGrid.tsx` | 운세 캘린더 월간 그리드 |
| `ChatBubble.tsx` | AI 채팅 말풍선 (SSE 스트리밍) |
| `PricingCard.tsx` | 구독 플랜 카드 |
| `ProgressSteps.tsx` | 온보딩 진행 단계 |

### 3.5 간격/그리드 체계

#### 8pt 기반 스페이싱 스케일

```css
--space-1:  4px;    /* 아이콘-텍스트 내부 간격 */
--space-2:  8px;    /* 뱃지 내부 패딩 */
--space-3:  12px;   /* 컴포넌트 내 소간격 */
--space-4:  16px;   /* 섹션 내부 패딩 */
--space-5:  20px;   /* 카드 내부 패딩 (현행 22px/24px → 20px 통일) */
--space-6:  24px;   /* 카드 간 간격 */
--space-8:  32px;   /* 섹션 간 간격 */
--space-10: 40px;   /* 대형 여백 */
--space-12: 48px;   /* 헤더/푸터 높이 기준 */
--space-14: 56px;   /* 바텀 네비 높이 */
```

#### 그리드 시스템

```
모바일 컨테이너: max-width 480px (설계 문서) — 현행 440px에서 조정 필요
좌우 패딩: 16px (현행 유지)
콘텐츠 영역 너비: 480 - 32 = 448px
6개 주제 그리드: 2열 × 3행, gap 10px
운세 3버튼: 3열, gap 10px (현행 gap 없음에서 수정)
```

#### 보더 반경

```css
--radius-sm:  8px;    /* 인라인 요소, 인풋 내부 */
--radius-md:  14px;   /* 현행 --r-sm, 버튼, 입력 필드 */
--radius-lg:  20px;   /* 현행 --r, 카드 */
--radius-xl:  24px;   /* 바텀시트 상단 모서리 */
--radius-full: 9999px; /* 뱃지, 필 버튼, 토글 */
```

### 3.6 다크모드 대응 여부

**결정: 다크모드 우선 구현 (Dark-first)**

근거:
1. 베트남 MZ의 야간 스마트폰 사용률이 높음
2. 사주/신비 컨셉이 어두운 배경에 더 어울림
3. 경쟁 앱(Co Star, The Pattern 등 글로벌 점성술 앱) 모두 다크 테마 기본
4. 현재 `--bg: #F5F3FA` 라이트 배경보다 `#0F0D1A` 다크 배경이 오행 컬러를 더 선명하게 표현

구현 방식:
- CSS Custom Properties + `@media (prefers-color-scheme: dark)` 기본 대응
- 수동 토글 버튼 (설정 화면)으로 사용자 오버라이드 가능
- `localStorage`에 사용자 선택 저장

---

## 4. 화면별 디자인 산출물 목록

설계 문서(Frontend Design v1.0)의 S-01~S-15 기준으로 각 화면의 디자인 시안 우선순위와 현재 구현 상태를 정리한다.

### 화면 산출물 매트릭스

| ID | 화면명 | 현재 구현 | 필요 디자인 시안 | 우선순위 |
|----|--------|---------|----------------|---------|
| S-01 | 랜딩 페이지 | 없음 | 히어로 섹션, 소셜 증거(리뷰), Feature 3종, CTA 섹션 | P0 |
| S-02 | 소셜 로그인 | 없음 | 로그인 카드, 소셜 버튼 4종, 이용약관 동의 | P0 |
| S-03 | 온보딩 위자드 | 일부(입력 폼) | Step 1(이름), Step 2(생년월일+성별), Step 3(관심사), 완료 화면 | P0 |
| S-04 | 홈 대시보드 | 부분 구현 | 오늘의 운세 카드, 사주 미니뷰, 빠른 메뉴 그리드, 이번달 흐름 | P0 |
| S-05 | 사주 입력/편집 | 부분 구현 | 음력/양력 탭, 드럼롤 날짜 피커, 시간 모름 처리 | P0 |
| S-06 | 사주 결과 | 없음 (설계만) | 오행 레이더 차트, 사주팔자 4기둥 카드, 십성 설명, 특성 태그 | P0 |
| S-07 | AI 상담 채팅 | 부분 구현 (Q&A) | 채팅 UI, SSE 스트리밍 말풍선, 주제 선택 칩, 무료 횟수 표시 | P0 |
| S-08 | 상담 이력 | 없음 | 상담 목록 카드, 빈 상태 일러스트, 상세 조회 | P1 |
| S-09 | 궁합 입력 | 구현됨 | 상대 성별 추가, 프로필 선택 UI, 저장된 프로필 목록 | P0 |
| S-10 | 궁합 결과 | 부분 구현 | 원형 점수 게이지, 항목별 해석 카드, 공유 버튼 | P0 |
| S-11 | 운세 캘린더 | 없음 | 월간 캘린더 그리드, 날짜 운세 점수 도트, 길일 표시 | P1 |
| S-12 | 구독 플랜 | 없음 | 플랜 비교 카드, 무료 → 유료 전환 CTA, 결제 버튼 | P1 |
| S-13 | 결제 처리 | 없음 | Toss Payments 내장 UI (외부 SDK) | P1 |
| S-14 | 마이페이지 | 없음 | 프로필 카드, 구독 상태 뱃지, 메뉴 리스트 | P1 |
| S-15 | 설정 | 없음 | 알림 토글, 언어 선택, 계정 삭제 | P2 |

### 각 화면 상세 시안 목록

#### S-03 온보딩 위자드 (현재 가장 큰 UX 갭)

필요한 디자인 시안:
```
[S-03-A] Step 1 — 이름/별명 입력
  - 프로그레스 인디케이터 (1/3)
  - 온보딩 일러스트 (onboarding-step1.svg)
  - 이름 입력 필드 + 앱 소개 1줄

[S-03-B] Step 2 — 생년월일 + 성별
  - 프로그레스 인디케이터 (2/3)
  - 양력/음력 탭 전환
  - 드럼롤 날짜 피커 (년/월/일)
  - 시간 선택 (선택, 모름 옵션 유지)
  - 성별 선택 (남/여/선택 안 함)

[S-03-C] Step 3 — 관심사 선택
  - 프로그레스 인디케이터 (3/3)
  - 주제 6개 멀티 선택 (연애/직업/돈/나/궁합/인생)
  - "시작하기" CTA

[S-03-D] 완료 화면
  - 사주 계산 로딩 (loading-crystal.json)
  - "{이름}님의 사주를 분석했어요" 완료 메시지
```

#### S-07 AI 상담 채팅 (핵심 가치 제공 화면)

필요한 디자인 시안:
```
[S-07-A] 주제 선택 진입 화면
  - 현행 sit-grid 개선 버전
  - 각 주제 아이콘 + 라벨 + 마지막 상담 날짜 표시

[S-07-B] 채팅 인터페이스
  - AI 메시지 말풍선 (왼쪽 정렬, 브랜드 배경)
  - 사용자 선택지 버튼 (오른쪽 정렬, 선택 후 비활성)
  - 타이핑 인디케이터 (SSE 스트리밍 중)
  - 무료 잔여 횟수 표시 (상단 고정 배너)

[S-07-C] 결과 카드 스택
  - 공감 카드 (card-intro)
  - 성격 카드 (card-ilgan)
  - 시기 카드 (card-combo)
  - 오늘의 한 줄 카드 (card-today)
  - 응원 카드 (card-cheer)
  - 공유 + 다른 주제 CTA

[S-07-D] 프리미엄 게이트
  - 무료 3회 소진 시 블러 처리된 결과 미리보기
  - "더 깊은 이야기 듣기" 구독 CTA
```

---

## 5. 애니메이션/모션 정의

### 5.1 카드 등장 효과

현재 구현:
```css
/* app.js line 413 */
card.style.animation = 'fadeUp .4s ease';

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px) }
  to   { opacity: 1; transform: translateY(0) }
}
```

**문제점:** `ease` 함수가 카드 등장에 약간 딱딱한 느낌. MZ 대상 앱에서는 스프링 물리 기반 곡선이 더 자연스러움.

**개선안:**

```css
/* 개선된 카드 등장 */
@keyframes cardReveal {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.97);
    filter: blur(2px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

.card-enter {
  animation: cardReveal 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  /* cubic-bezier(0.34, 1.56, 0.64, 1) = spring-like 오버슈팅 곡선 */
}
```

**카드 순차 등장 (stagger):**
```css
.card-enter:nth-child(1) { animation-delay: 0ms; }
.card-enter:nth-child(2) { animation-delay: 80ms; }
.card-enter:nth-child(3) { animation-delay: 160ms; }
.card-enter:nth-child(4) { animation-delay: 240ms; }
.card-enter:nth-child(5) { animation-delay: 320ms; }
```

### 5.2 화면 전환 효과

현재: `display:none/block` 즉시 전환 (애니메이션 없음)

**개선안 — 슬라이드 전환:**

```css
/* 화면 전환 기본 */
.scr {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
  transform: translateX(30px);
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.scr.on {
  opacity: 1;
  pointer-events: auto;
  transform: translateX(0);
}

.scr.leaving {
  opacity: 0;
  transform: translateX(-30px);
}
```

**전환 방향 규칙:**
- 홈 → 서브 화면: 오른쪽으로 슬라이드인 (`translateX(30px) → 0`)
- 서브 → 홈: 왼쪽으로 슬라이드인 (`translateX(-30px) → 0`)
- 동급 화면 간 전환: Fade only

**`go()` 함수 리팩터:**
```javascript
function go(id, direction = 'forward') {
  const current = document.querySelector('.scr.on');
  const next = document.getElementById(id);

  if (current) {
    current.classList.add(direction === 'forward' ? 'leaving' : 'leaving-back');
    setTimeout(() => current.classList.remove('on', 'leaving', 'leaving-back'), 250);
  }

  next.classList.add('on');
  // direction에 따라 시작 위치 설정
}
```

**주의:** `prefers-reduced-motion` 미디어 쿼리로 애니메이션 비활성화 옵션 필수 제공.

```css
@media (prefers-reduced-motion: reduce) {
  .scr, .card-enter, .dots span {
    animation: none !important;
    transition: opacity 0.1s !important;
  }
}
```

### 5.3 로딩 상태

| 상황 | 현재 | 개선안 |
|------|------|--------|
| 사주 계산 중 | 미처리 (즉시 완료) | 0.8초 인위적 딜레이 + loading-stars Lottie |
| AI 응답 대기 | `.ld` 도트 애니메이션 | loading-crystal Lottie (풀 화면) |
| 카드 로딩 | 없음 | SkeletonCard 컴포넌트 |
| 이미지 로딩 | 없음 | blur-up 기법 (저해상도 → 고해상도 전환) |

**타이핑 인디케이터 (AI 스트리밍):**
```css
@keyframes typingDot {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.typing-indicator span:nth-child(1) { animation-delay: 0ms; }
.typing-indicator span:nth-child(2) { animation-delay: 150ms; }
.typing-indicator span:nth-child(3) { animation-delay: 300ms; }
```

### 5.4 마이크로 인터랙션

#### 버튼 탭 효과

```css
/* 현행 */
.btn:active { transform: scale(.97); }

/* 개선 — haptic 느낌 강화 */
.btn {
  transition: transform 0.1s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.15s ease,
              background-color 0.15s ease;
}
.btn:active {
  transform: scale(0.95);
  box-shadow: 0 2px 6px var(--accent-glow);
}
```

#### 선택지 버튼 선택 애니메이션

현재: `opacity: 0.4` + `border-color/color` 변경 (즉시)

개선안:
```css
.follow-btn {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.follow-btn.selected {
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 700;
  background: var(--accent-light);
  transform: scale(1.01);
}

.follow-btn.dimmed {
  opacity: 0.35;
  pointer-events: none;
  filter: grayscale(0.3);
}
```

#### 궁합 점수 원형 게이지 애니메이션

현재: 원형 div에 점수 숫자만 표시 (정적)

개선안: SVG `stroke-dasharray` 기반 원형 프로그레스 바
```javascript
// 점수가 0에서 최종값까지 카운트 업
function animateScore(targetScore, duration = 1200) {
  let current = 0;
  const step = targetScore / (duration / 16);
  const interval = setInterval(() => {
    current = Math.min(current + step, targetScore);
    scoreEl.textContent = Math.round(current);
    // SVG stroke-dashoffset 업데이트
    if (current >= targetScore) clearInterval(interval);
  }, 16);
}
```

#### 운세 점수 바 애니메이션

현재: `transition: .5s` (CSS만)

개선안: Intersection Observer로 뷰포트 진입 시 트리거
```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.width = entry.target.dataset.score + '%';
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.3 });
```

#### 오행 뱃지 호버/탭 효과

```css
.element-badge {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.element-badge:active {
  transform: scale(0.94);
}

/* 탭 시 원소 색상 글로우 */
.element-badge.wood:active  { box-shadow: 0 0 12px rgba(46, 125, 50, 0.4); }
.element-badge.fire:active  { box-shadow: 0 0 12px rgba(198, 40, 40, 0.4); }
.element-badge.earth:active { box-shadow: 0 0 12px rgba(245, 127, 23, 0.4); }
.element-badge.metal:active { box-shadow: 0 0 12px rgba(117, 117, 117, 0.4); }
.element-badge.water:active { box-shadow: 0 0 12px rgba(21, 101, 192, 0.4); }
```

#### 언어 전환 토글

현재: `.on` 클래스 토글만 (즉시)

개선안: 콘텐츠 fade-out → 언어 변경 → fade-in
```javascript
async function updateLang(newLang) {
  document.querySelector('.wrap').style.opacity = '0';
  await delay(150);
  lang = newLang;
  document.querySelectorAll('[data-ko][data-vi]').forEach(/* ... */);
  document.documentElement.lang = newLang;
  document.querySelector('.wrap').style.opacity = '1';
}
```

---

## 6. 현재 구현 vs 목표 설계 갭 요약

### 기술 스택 갭

| 항목 | 현재 | 목표 (설계 문서) | 갭 심각도 |
|------|------|----------------|---------|
| 프레임워크 | Vanilla JS + HTML | Next.js 15 App Router | Critical |
| 스타일링 | CSS (단일 파일) | Tailwind CSS + shadcn/ui | High |
| 상태 관리 | 전역 변수 (`saju`, `lang`) | Zustand | High |
| 서버 상태 | 없음 | TanStack Query | High |
| 애니메이션 | CSS 키프레임 | Framer Motion | Medium |
| 차트 | 없음 | Recharts | Medium |
| 타입 안전성 | 없음 | TypeScript strict | High |
| 라우팅 | display:none 전환 | Next.js App Router | Critical |
| 인증 | 없음 | OAuth (카카오/구글) | High |
| AI 연동 | 없음 | SSE 스트리밍 | High |

### UX 품질 갭

| 항목 | 현재 | 목표 | 갭 |
|------|------|------|---|
| 온보딩 | 1단계 (날짜 입력만) | 3단계 위자드 | 2단계 누락 |
| 바텀 탭 수 | 3탭 | 4탭 | 상담 탭 누락 |
| 바텀 탭 상태 | 수동 관리 미흡 | 자동 활성화 | 버그 |
| 뒤로가기 | 미지원 | History API | Critical |
| 음력 지원 | 없음 | 양력/음력 선택 | 베트남 현지화 결함 |
| 개인화 | 없음 | 이름 기반 | Medium |
| 공유 기능 | 없음 | SNS 카드 공유 | Medium |
| 오프라인 | 미지원 | Service Worker | Low |

### 접근성 갭

| 항목 | 현재 | 목표 | 우선순위 |
|------|------|------|---------|
| 키보드 탐색 | 불가 | 완전 지원 | P0 |
| 스크린리더 | 미지원 | WCAG 2.1 AA | P0 |
| 색상 대비 | 4/6항목 미달 | 4.5:1 이상 | P0 |
| lang 속성 | 고정 `ko` | 동적 업데이트 | P0 |
| 포커스 관리 | 없음 | 화면 전환 시 이동 | P1 |
| 오류 안내 | 없음 | aria-invalid | P1 |

---

*문서 끝 — 다음 단계: Figma 디자인 시스템 파일 생성 및 위 컴포넌트 목록 기준 설계 시작*
