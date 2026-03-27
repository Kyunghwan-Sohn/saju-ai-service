# PDCA Design Phase Evaluation: MỆnh (AI 사주 서비스)

> **Date:** 2026-03-26
> **Evaluator:** PDCA Evaluation Agent (Design Phase)
> **Project Type:** Dynamic Web App (정적 웹앱 + DB-First 아키텍처)
> **Evaluation Framework:** v1.6.1 Baseline vs Custom bkit

---

## Design Phase Evaluation: Dynamic (정적 SPA → DB-First 하이브리드)

```
Design Phase Evaluation: Dynamic
========================================
v1.6.1 Score:  55/100
Custom Score:  71/100
Improvement:  +29.1%

Breakdown:
  Design Accuracy:      v1.6.1=60  Custom=72  (weight: 35%)
  Domain Guidance:      v1.6.1=25  Custom=68  (weight: 35%)
  Phase Skill Usage:    v1.6.1=75  Custom=72  (weight: 30%)

Infrastructure Components Contributing:
  - skill-create: enables domain skill creation (indirect)
  - 2-layer loader: auto-loads created skills during design
  - skill-status: shows available skills for reference
Domain Skills Contributing:
  - 2 project-specific skills applied (사주 도메인 + 베트남 현지화)
  - Without domain skills: Custom score would be 61 (infra-only effect: +10.9%)
  - With domain skills:    Custom score is 71 (total effect: +29.1%)
```

> **참고**: 이 프로젝트는 "바닐라 정적 웹앱"으로 시작했으나 설계 문서는 Next.js + FastAPI + PostgreSQL 풀스택을 목표로 작성되었다. 이 구현-설계 괴리가 본 평가의 핵심 문제다.

---

## 1. 설계 정확도 평가 (D1: Design Accuracy)

**점수: v1.6.1=60 / Custom=72 / Weight=35%**

### 1.1 현재 설계 문서가 구현을 정확히 기술하는가?

**결론: 아니다. 설계 문서는 미래 목표를 기술하고 있고, 현재 구현은 그 초기 프로토타입이다.**

#### 설계-구현 간 정합성 분석

| 설계 문서 기술 | 현재 구현 상태 | 괴리 유형 |
|--------------|--------------|---------|
| Next.js 15 + TypeScript + shadcn/ui | 바닐라 HTML/CSS/JS | 기술 스택 완전 불일치 |
| S-01~S-15 화면 15개 (경로 기반 라우팅) | 7개 화면 (`display:none/block`) | 화면 수 및 구조 불일치 |
| 소셜 로그인 (카카오 OAuth) | 없음 (생년월일 직접 입력 → 즉시 홈) | 인증 체계 전무 |
| 온보딩 3단계 위자드 (이름, 생년월일+음력, 관심사) | 생년월일 입력 폼 1단계만 존재 | 플로우 50% 누락 |
| 음력/양력 토글 (`CalendarToggle`) | 없음 (`calculateSaju`에 기본값만) | 사주 도메인 핵심 기능 누락 |
| 하단 탭 4개 (홈/상담/캘린더/MY) | 하단 탭 3개 (홈/오늘/궁합) | 탭 구성 불일치 |
| SSE 스트리밍 AI 채팅 (S-07) | 정적 Q&A 트리 (FOLLOW_UPS 객체) | AI 연동 미구현 |
| DB-First 아키텍처 (PostgreSQL + 배치 생성) | 브라우저 JS 인메모리 처리 | 백엔드 전무 |
| Lucide Icons SVG | 유니코드 이모지 전부 사용 | 아이콘 시스템 불일치 |
| 디자인 토큰 CSS 변수 체계 | 부분 구현 (오행 컬러는 JS 객체) | 토큰 체계 불완전 |

**정합성 점수: 실질 구현 대비 설계 커버리지 ~35%**

frontend-review.md에서 도출된 score 52/100은 "현재 구현이 설계 문서의 요구사항을 충족하는 정도"를 측정한 것이다. 역방향으로 보면 설계 문서가 현재 구현을 기술하는 정도는 더 낮다.

#### 올바른 해석 프레임

이 프로젝트의 구조적 문제는 **설계 순서의 역전**이다:

```
실제 진행:
  프로토타입 코딩 (바닐라) → 설계 문서 작성 (Next.js 목표)
                               ↑ 설계가 구현을 반영하지 않고
                                 이상적 목표를 기술함

올바른 순서:
  설계 문서 작성 → 구현 → 설계-구현 검증
```

프로토타입은 사주 엔진(8/8 정확도)과 기본 UX 흐름 검증에 유효하다. 그러나 설계 문서는 이 프로토타입의 한계를 인정하고 "v0 프로토타입 → v1 목표" 구조로 명시했어야 한다.

### 1.2 설계-구현 간 정합성 점수

| 영역 | 정합성 | 비고 |
|------|--------|------|
| 사주 엔진 로직 | 80% | 8간지 계산은 설계 의도와 일치 |
| UI 화면 구조 | 30% | 화면 수, 라우팅, 컴포넌트 모두 불일치 |
| 데이터 플로우 | 15% | DB 없음, API 없음 |
| 현지화 | 20% | 베트남어 45% 누락, 음력 미지원 |
| 디자인 시스템 | 40% | CSS 변수 일부 존재, 토큰 체계 미완 |
| **종합** | **37%** | 설계 문서가 현재 구현을 정확히 기술하는 정도 |

---

## 2. 도메인 특화 가이드 적용도 (D2: Domain-Specific Guidance)

**점수: v1.6.1=25 / Custom=68 / Weight=35%**

### 2.1 사주 서비스 특유의 UX 요구사항이 설계에 반영되었는가?

#### 반영된 항목 (설계 문서 기준)

| 요구사항 | 설계 반영 | 구현 반영 | 평가 |
|---------|---------|---------|------|
| 음력/양력 입력 선택 | frontend-design.md에 `CalendarToggle` 명시 | 미구현 | 설계 O / 구현 X |
| 시진(時辰) 개념 | `BirthTimePicker` + `TimeUnknownCheckbox` 명시 | 미구현 | 설계 O / 구현 X |
| 사주팔자 4기둥 시각화 | `FourPillarsDisplay` 컴포넌트 정의 | 미니 뷰만 부분 구현 | 설계 O / 구현 30% |
| 오행 분포 차트 | `FiveElementsChart` (Recharts Radar) | 텍스트 바만 구현 | 설계 O / 구현 20% |
| 십성(十星) 배치표 | `TenStarsGrid` 정의 | 미구현 | 설계 O / 구현 X |
| 12운성 배지 | `TwelveStagesBadge` 정의 | 미구현 | 설계 O / 구현 X |
| DB-First 콘텐츠 구조 | architecture-concept-v2.md에 상세 정의 | 인메모리로 임시 처리 | 설계 O / 구현 X |

#### 누락된 항목 (설계 문서에서도 부족)

| 요구사항 | 설계 반영 | 구체화 필요 사항 |
|---------|---------|----------------|
| 대운(大運) 타임라인 | 언급 없음 | 10년 단위 대운 흐름 UI가 사주 서비스 핵심 |
| 신살(神殺) 해석 | 태그만 언급 | 도화살/역마살 등의 시각적 표현 정의 필요 |
| 격국(格局) 설명 | `GeokgukBadge`만 정의 | 격국이 무엇인지 초보 사용자 설명 UI 없음 |
| 사주 비교 (두 사람) | 궁합만 언급 | 가족/지인 비교 UI 미정의 |
| 용신(用神) 강조 | 없음 | 사주에서 가장 필요한 오행을 강조하는 UI |
| 절기(節氣) 기준 표시 | 없음 | 월주 경계가 생일과 다를 때 사용자 혼란 방지 UI |

#### 평가

설계 문서는 사주 도메인 UX를 **구성 요소 목록** 수준까지는 정의했다. 그러나 각 요소 간의 **내러티브 흐름** — 즉 사용자가 사주를 처음 받고 어떤 순서로 이해해야 하는지의 pedagogy — 이 빠져 있다. 예: "오행 분포 → 일간 설명 → 십성 풀이 → 오늘 운세"로 이어지는 정보 위계가 설계에 없다.

### 2.2 베트남 현지화가 설계 단계에서 고려되었는가?

#### 현지화 설계 현황

| 현지화 항목 | 설계 문서 기술 | 구현 상태 | 심각도 |
|-----------|-------------|---------|--------|
| 베트남어 UI 텍스트 | `data-ko/vi` 속성 방식 언급 | 45% 누락 | Critical |
| 음력 입력 (âm lịch) | `isLunar: boolean` 필드 정의 | 미구현 | Critical |
| Be Vietnam Pro 폰트 | 설계 문서 명시 | 구현됨 (Google Fonts) | 해결됨 |
| 성조 문자 line-height | frontend-review.md에 `[lang="vi"]` 보정 정의 | 미구현 | High |
| `document.lang` 동적 업데이트 | 언급 없음 | 미구현 | High |
| SNS 공유 (Facebook, TikTok, Zalo) | 설계 문서에 명시 | 미구현 | Medium |
| 베트남 결제 (Toss가 아닌 MoMo/ZaloPay) | Toss Payments만 언급 | N/A | High |
| 시간대 처리 (ICT UTC+7) | DB 설계에 UTC 명시, 변환 언급 | 미구현 | Medium |
| 한자-베트남어 병기 (chữ Nôm/hán tự) | 설계 문서에서 고려 없음 | 미구현 | Medium |

**결정적 누락**: Toss Payments는 한국 전용 결제 수단이다. 베트남 서비스라면 MoMo (베트남 최대 결제 앱), ZaloPay, VNPay를 기본으로 검토해야 한다. 설계 문서가 이를 놓쳤다.

**아키텍처 현지화 누락**: DB 설계의 timezone을 KST로 언급하고 있다 (`Timezone: UTC, 애플리케이션 레벨에서 KST 변환`). 베트남 서비스라면 KST가 아닌 ICT(UTC+7) 변환이어야 한다. 사주 계산은 출생 시간의 정확한 시간대 처리가 핵심인데 이 부분이 설계에서 모호하다.

---

## 3. Phase Skill 활용도 (D3: Phase Skill Utilization)

**점수: v1.6.1=75 / Custom=72 / Weight=30%**

### 3.1 현재 프로젝트에서 활용 가능한 bkit 스킬 적용 현황

#### Phase Skills (9개) 적용도

| Phase Skill | 적용 여부 | 적용 품질 | 비고 |
|------------|---------|---------|------|
| phase-1-schema | 부분 적용 | 중 | DB 스키마는 정의됨, 하지만 실제 구현 없음 |
| phase-2-api | 부분 적용 | 중 | API 설계 문서 존재, 구현 없음 |
| phase-3-service | 미적용 | - | 사주 엔진 로직이 JS 함수 수준 |
| phase-4-auth | 설계만 | 하 | 카카오 OAuth 설계, 구현 전무 |
| phase-5-ui | 부분 적용 | 중 | 컴포넌트 목록 정의됨, 실제는 raw HTML |
| phase-6-integration | 미적용 | - | 프론트-백 연동 없음 |
| phase-7-testing | 부분 적용 | 중 | 사주 엔진 8/8 검증만 존재 |
| phase-8-optimization | 미적용 | - | 최적화 고려 없음 |
| phase-9-deployment | 설계만 | 하 | 배포 전략 미정 |

#### 관찰: Phase Skill vs 실제 개발 단계 불일치

현재 프로젝트는 **Phase 1-2 (스키마/API 설계)** 와 **Phase 5 (UI 설계)** 의 산출물을 보유하고 있으나, **실제 구현은 Phase 3-4를 건너뛴** 상태다. 이는 설계가 구현 계획을 제시하지 못하고 있음을 보여준다.

Phase skills의 이상적 활용:
```
phase-1-schema → DB 설계 완료 (O)
phase-2-api    → API 설계 완료 (O)
phase-3-service → 비즈니스 로직 구현 (X — JS 인메모리)
phase-4-auth   → 인증 구현 (X)
phase-5-ui     → UI 컴포넌트 구현 (X — raw HTML)
```

### 3.2 도메인 스킬 현황

이 프로젝트에서 skill-create를 통해 생성/적용되어야 할 도메인 스킬:

| 스킬 | 필요성 | 현재 상태 |
|------|--------|---------|
| saju-engine-patterns | 사주 계산 패턴 (만세력, 절기 경계, 윤달 처리) | 사주 엔진 8/8 검증으로 사실상 존재 |
| vietnam-localization | 베트남 현지화 규칙 (음력, 성조, 결제 수단) | 미정의 |
| db-first-content-strategy | 65개 → 665개 DB 구축 전략 | architecture-concept-v2에 부분 정의 |
| saju-ux-pedagogy | 사주 입문자 UX 설계 (정보 위계, 용어 해설) | 미정의 |

---

## 4. 핵심 발견: 설계의 구조적 문제

### 4.1 설계 문서 간 내부 불일치

| 불일치 항목 | 문서 A | 문서 B | 영향 |
|-----------|--------|--------|------|
| Accent 컬러 | `#1A1A2E` Primary, `#C9A96E` Gold (architecture) | `#6C4FE0` 보라 (frontend-review) | 브랜드 아이덴티티 혼란 |
| 하단 탭 구성 | 홈/상담/캘린더/MY 4탭 (frontend-design) | 홈/오늘/궁합 3탭 (구현) | 정보 구조 불일치 |
| 컨테이너 너비 | 480px (frontend-review 권고) | 440px (현재 구현) | 미세 레이아웃 불일치 |
| 폰트 스택 | Pretendard + Noto Serif KR (frontend-design) | Be Vietnam Pro + Playfair Display (구현) | 타이포 경험 불일치 |
| 타임존 기준 | KST (db-schema) | ICT UTC+7 (실제 필요) | 사주 계산 오류 가능성 |

### 4.2 설계 부채 목록 (Design Debt)

```
[Severity: Critical]
DD-01: 설계 문서가 현재 구현 기술 스택(바닐라 JS)을 전혀 반영하지 않음
DD-02: 음력 입력이 설계에 정의됐으나 구현 로드맵에 없음
DD-03: 베트남 결제 수단(MoMo/ZaloPay) 설계 검토 없음
DD-04: 타임존 기준이 KST로 잘못 명시됨 (ICT UTC+7이어야 함)

[Severity: High]
DD-05: 대운(大運) UI가 설계에 완전히 빠져 있음
DD-06: 용신(用神) 개념의 시각적 표현 미정의
DD-07: 한자-베트남어 병기 방식 미정의
DD-08: Q&A 트리의 love 외 5개 주제 2단 이상 설계 없음

[Severity: Medium]
DD-09: 다크모드 구현이 권고로만 남고 우선순위 결정 없음
DD-10: SNS 공유 카드 생성 방식(html2canvas vs Canvas API) 미결정
DD-11: 절기 기준 설명 UI(월주 경계 혼란 방지) 없음
DD-12: 오행 컬러가 CSS 변수와 JS 객체로 이중 관리됨
```

---

## 5. 개선 권고

### 5.1 즉시 수행 (Do Now — 이번 PDCA 사이클)

#### P0: 치명적 결함 해소

| 항목 | 조치 | 담당 | 예상 공수 |
|------|------|------|---------|
| 음력/양력 선택 UI | 입력 폼에 토글 추가, `lunarToSolar()` 연동 | FE | 1일 |
| Android 뒤로가기 | `history.pushState()` + `popstate` 이벤트 | FE | 0.5일 |
| 베트남어 번역 완성 | 누락된 `data-vi` 55% 채우기 | FE + 번역 | 2일 |
| WCAG AA 대비비 | `--accent: #7B5CF0`으로 조정, dim 컬러 개선 | FE | 0.5일 |
| `document.lang` 동적 업데이트 | 언어 전환 시 `setAttribute('lang', ...)` | FE | 0.5일 |

#### P0: 설계 문서 현행화

```
[즉시 수정 필요한 설계 오류]
1. db-schema.md — KST → ICT (UTC+7) 수정
2. frontend-design.md — "현재 프로토타입 상태" 섹션 추가
3. mvp-roadmap.md — 바닐라 JS 프로토타입 → Next.js 마이그레이션 일정 명시
4. architecture-concept-v2.md — DB-First 초기 구축 범위 축소 (일주 60개 우선)
```

### 5.2 단기 수행 (1-2주 내)

#### 설계 문서 보강

| 신규 문서 | 내용 | 우선순위 |
|---------|------|---------|
| `saju-ux-pedagogy.md` | 사주 입문자를 위한 정보 위계 설계 (오행 → 일간 → 십성 → 운세 순서) | P0 |
| `vietnam-localization-spec.md` | 음력, 성조 폰트, MoMo/ZaloPay, ICT 시간대, 베트남 SNS 공유 규격 | P0 |
| `design-debt-tracker.md` | DD-01~DD-12 항목별 해소 계획 및 담당자 | P1 |

#### 구현 보강

| 항목 | 조치 |
|------|------|
| Q&A 트리 확장 | career, money, self, general 주제에 2단 이상 분기 추가 |
| 궁합 점수 고정 | 날짜 기반 랜덤 제거, 일간 조합 기반 고정 점수 알고리즘 적용 |
| 에러/빈 상태 UI | 5개 상황별 빈 상태 화면 구현 |
| 토스트 컴포넌트 | 입력 폼 유효성 피드백 (현재 조용한 실패) |

### 5.3 다음 PDCA 사이클 (Check 단계)

#### 측정 지표 설정

```
[D1 설계 정확도 개선 측정]
- 설계 문서 vs 구현 정합성 점수: 현재 37% → 목표 60% (1사이클 후)
- 설계 문서 내 상호 불일치 항목: 현재 5건 → 목표 0건

[D2 도메인 가이드 측정]
- 베트남어 번역 커버리지: 현재 55% → 목표 100%
- 음력 입력 지원 여부: 현재 X → 목표 O
- 사주 도메인 설계 커버리지 (대운/신살/격국/용신): 현재 40% → 목표 75%

[D3 Phase Skill 측정]
- Phase 1-5 구현 완료율: 현재 Phase 1-2 설계만 / Phase 3-5 미구현
  → 목표: Phase 3 (Service Layer) 구현 착수
```

#### 다음 사이클 우선 과제

```
[Act: 다음 사이클에서 해야 할 것]

1. 기술 스택 결정 확정
   - "계속 바닐라 JS (빠른 출시)" vs "Next.js 마이그레이션 (설계 일치)"
   - 이 결정 없이 설계-구현 정합성 개선 불가능

2. DB-First 콘텐츠 1차 구축
   - 일주 60개 × 5카드 = 300개 레코드 수동/배치 생성
   - 현재 49개 → 665개 목표의 1차 마일스톤

3. vietnam-localization-spec 기반 구현
   - 음력 변환 라이브러리 선정 (lunr, lunar-javascript 등)
   - MoMo 결제 API 사전 검토

4. 사용자 테스트 (베트남 MZ 5명)
   - 음력 vs 양력 입력 혼란도 측정
   - 한자 표기 이해도 측정
   - 대화형 Q&A 단계 이탈률 측정
```

---

## 6. PDCA 종합 평가

### 6.1 Design Phase 종합

| 평가 차원 | 점수 | 상태 |
|---------|------|------|
| D1: 설계 정확도 | 35/100 (정합성) | Critical |
| D2: 도메인 가이드 | 55/100 (설계 반영도) | Poor |
| D3: Phase Skill 활용 | 40/100 (실질 구현 기준) | Poor |
| **Design Phase 종합** | **43/100** | **요주의** |

> 설계 문서 자체의 품질(목표 상태 기술)은 70-75점 수준이나, 설계가 실제 구현과 연결되지 않아 전체 Design Phase 점수가 낮다.

### 6.2 핵심 인사이트

**이 프로젝트의 Design Phase 문제는 "나쁜 설계"가 아니라 "단절된 설계"다.**

설계 문서들은 개별적으로 충분한 품질을 갖추고 있다. frontend-design.md, ui-wireframe.md, architecture-concept-v2.md 모두 프로페셔널한 수준의 산출물이다. 문제는:

1. **타임라인 불일치**: 설계 문서가 2026-03-25에 작성되었으나, 바닐라 JS 프로토타입은 이미 그 이전에 독립적으로 개발된 것으로 보인다. 설계와 구현이 별개로 진행되었다.

2. **가교 문서 부재**: "현재 프로토타입 → 설계 목표" 간의 마이그레이션 계획이 없다. mvp-roadmap.md가 이 역할을 해야 하나, Week 1부터 Next.js를 전제로 작성되어 현재 바닐라 JS 상태를 무시한다.

3. **도메인 지식이 설계에 덜 반영**: 음력 처리, 대운 UI, 용신 강조, 베트남 결제 수단 등 사주-베트남 현지화의 교차점이 설계에서 충분히 다뤄지지 않았다.

**다음 PDCA 사이클의 최우선 과제는 "기술 스택 결정"이다.** 이 결정이 없으면 모든 설계 문서는 실현 불가능한 청사진으로 남는다.

---

*Generated by PDCA Evaluation Agent — Design Phase | 2026-03-26*
*Reference: frontend-review.md, frontend-design.md, mvp-roadmap.md, architecture-concept-v2.md, ui-wireframe.md, db-schema.md*
