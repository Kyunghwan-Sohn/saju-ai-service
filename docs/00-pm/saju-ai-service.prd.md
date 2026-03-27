# Saju AI Service - Product Requirements Document (PRD)

> **Version:** 1.0
> **Date:** 2026-03-25
> **Author:** PM Lead Agent
> **Status:** Approved

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [Target Users & Personas](#4-target-users--personas)
5. [User Stories & Requirements](#5-user-stories--requirements)
6. [System Architecture & Technical Requirements](#6-system-architecture--technical-requirements)
7. [Data Model & API Specification](#7-data-model--api-specification)
8. [UI/UX Requirements](#8-uiux-requirements)
9. [Release Plan & Milestones](#9-release-plan--milestones)
10. [Risks, Constraints & Appendix](#10-risks-constraints--appendix)

---

## 1. Executive Summary

### 1.1 Product Vision

Saju AI Service는 한국 전통 사주명리학(四柱命理學, Four Pillars of Destiny)을 AI 기술과 결합하여, 사용자에게 개인화된 운세 분석 및 상담 서비스를 제공하는 플랫폼이다. 사용자의 생년월일시(四柱)를 기반으로 LLM(Large Language Model)이 전통 명리학 지식을 활용해 정교한 운세 해석을 생성한다.

### 1.2 Product Overview

- **서비스명:** Saju AI (사주 AI)
- **서비스 유형:** AI 기반 사주명리 상담 웹/모바일 서비스
- **핵심 기술:** LLM (GPT-4 class 또는 동급), 사주명리학 도메인 지식 엔진, 만세력(萬歲曆) 데이터
- **타겟 시장:** 한국어권 사용자 (1차), 글로벌 확장 (2차)
- **비즈니스 모델:** Freemium (기본 무료 + 프리미엄 구독 + 건별 심화 상담)

### 1.3 Scope

본 PRD는 Saju AI Service의 MVP(Minimum Viable Product)부터 v1.0 정식 출시까지의 전체 제품 요구사항을 정의한다.

---

## 2. Problem Statement

### 2.1 현재 시장의 문제점

| 문제 | 설명 |
|------|------|
| **접근성 부족** | 전통 사주 상담은 대면 방문이 필요하고, 유명 역술인은 예약이 어렵다. 비용도 회당 5만~30만원으로 부담이 크다. |
| **품질 편차** | 역술인마다 해석이 크게 다르고, 자격 검증 체계가 없어 신뢰도가 낮다. |
| **디지털 전환 미비** | 기존 온라인 사주 서비스는 대부분 템플릿 기반의 단순 텍스트 생성이며, 맥락을 이해하는 대화형 상담이 불가능하다. |
| **개인화 부재** | 동일 사주에 대해 동일한 결과를 반복 출력하며, 사용자의 현재 상황이나 고민을 반영하지 못한다. |

### 2.2 기회 (Opportunity)

- 한국 운세/점술 시장 규모: 약 4조원 (2025년 기준 추정)
- MZ세대의 MBTI, 타로 등 자기탐구 콘텐츠 수요 급증
- 생성형 AI의 자연어 처리 능력이 복잡한 명리학 해석을 대화형으로 제공할 수준에 도달
- 기존 사주 앱 시장의 AI 전환 초기 단계 -- First Mover Advantage 확보 가능

### 2.3 Solution Hypothesis

LLM에 사주명리학 전문 지식을 주입하고, 만세력 데이터와 연동한 정확한 사주 산출 엔진을 결합하면, 전문 역술인 수준의 개인화된 상담을 24시간 저비용으로 제공할 수 있다.

---

## 3. Goals & Success Metrics

### 3.1 Product Goals

| 우선순위 | 목표 | 설명 |
|----------|------|------|
| P0 | 정확한 사주 산출 | 만세력 기반 사주팔자(四柱八字) 계산의 100% 정확도 보장 |
| P0 | AI 상담 품질 | 전문 역술인 대비 사용자 만족도 80% 이상 달성 |
| P1 | 개인화 경험 | 사용자의 질문과 맥락을 반영한 맞춤형 해석 제공 |
| P1 | 확장 가능한 아키텍처 | 대운/세운/월운 등 다양한 운세 유형으로 확장 가능한 구조 |
| P2 | 글로벌 확장 기반 | 다국어 지원이 가능한 설계 구조 |

### 3.2 Success Metrics (KPIs)

| 지표 | 목표값 | 측정 주기 |
|------|--------|-----------|
| DAU (Daily Active Users) | MVP: 1,000 / v1.0: 10,000 | Daily |
| 상담 완료율 (Completion Rate) | >= 85% | Weekly |
| 사용자 만족도 (CSAT) | >= 4.2 / 5.0 | Monthly |
| 유료 전환율 (Free to Paid) | >= 5% | Monthly |
| 재방문율 (D7 Retention) | >= 40% | Weekly |
| 평균 세션 시간 | >= 5분 | Weekly |
| AI 응답 정확도 (전문가 평가) | >= 80% | Quarterly |
| 시스템 가용성 (Uptime) | >= 99.5% | Monthly |

### 3.3 Non-Goals (v1.0 범위 외)

- 실시간 화상/음성 상담
- 타로, 관상, 풍수 등 사주 외 점술 분야
- 자체 LLM 학습/파인튜닝 (v1.0에서는 프롬프트 엔지니어링 + RAG 방식)
- 네이티브 모바일 앱 (v1.0은 모바일 반응형 웹)

---

## 4. Target Users & Personas

### 4.1 Primary Personas

#### Persona A: "호기심 많은 MZ세대" -- 김지은 (28세, 직장인)

| 항목 | 내용 |
|------|------|
| **배경** | IT 회사 마케터. MBTI, 타로에 관심이 많고 SNS에서 운세 콘텐츠를 자주 공유한다. |
| **동기** | 연애운, 직장운에 대한 가벼운 궁금증. 친구들과 함께 즐길 수 있는 콘텐츠. |
| **Pain Point** | 기존 사주 앱은 결과가 너무 뻔하고 재미없다. 직접 역술인에게 가기는 부담스럽다. |
| **기대** | 대화하듯 자연스럽게 물어볼 수 있는 AI 상담. SNS 공유 가능한 카드형 결과. |
| **사용 빈도** | 주 2~3회, 짧은 세션 (3~5분) |

#### Persona B: "진지한 상담 고객" -- 박상훈 (42세, 자영업자)

| 항목 | 내용 |
|------|------|
| **배경** | 음식점 사장. 사업 확장을 고민 중이며 전통적으로 중요한 결정 전에 사주를 본다. |
| **동기** | 올해 사업운, 투자 시기, 동업자와의 궁합 등 구체적인 의사결정 참고. |
| **Pain Point** | 좋은 역술인을 찾기 어렵고, 한 번 갈 때마다 비용이 크다. |
| **기대** | 깊이 있는 사주 해석. 구체적인 질문에 대한 명리학적 근거가 있는 답변. |
| **사용 빈도** | 월 2~3회, 긴 세션 (10~20분) |

#### Persona C: "가족 걱정하는 부모" -- 이미영 (55세, 주부)

| 항목 | 내용 |
|------|------|
| **배경** | 자녀의 취업, 결혼에 관심이 많다. 주변 지인을 통해 사주를 보는 습관이 있다. |
| **동기** | 자녀 궁합, 이사 방위, 길일(吉日) 선택. |
| **Pain Point** | 스마트폰 사용에 익숙하지 않아 복잡한 UI는 어렵다. |
| **기대** | 쉽고 큰 글씨의 인터페이스. 음성 입력 지원. 가족 사주를 함께 관리. |
| **사용 빈도** | 월 1~2회, 중간 세션 (5~10분) |

### 4.2 User Segmentation

| 세그먼트 | 설명 | 예상 비중 |
|----------|------|-----------|
| Casual | 가벼운 호기심, 무료 사용 위주 | 60% |
| Regular | 주기적 이용, 일부 유료 기능 사용 | 25% |
| Premium | 심화 상담, 구독 결제 | 10% |
| Professional | 역술인/상담사의 보조 도구로 활용 | 5% |

---

## 5. User Stories & Requirements

### 5.1 Epic 1: 사주 프로필 생성

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-101 | 사용자는 생년월일시를 입력하여 자신의 사주팔자를 확인할 수 있다. | P0 | 양력/음력 선택 가능. 시간 미입력 시 시주(時柱) 제외 옵션 제공. 결과에 천간/지지/오행 표시. |
| US-102 | 사용자는 자신의 사주 프로필을 저장하고 관리할 수 있다. | P0 | 회원가입 후 최대 5개 프로필 저장. 본인/가족/지인 구분 태그. |
| US-103 | 사용자는 사주 결과를 시각적 차트로 확인할 수 있다. | P1 | 오행 분포 차트, 십성(十星) 관계도, 12운성 그래프 표시. |
| US-104 | 사용자는 두 사람의 사주를 비교(궁합)할 수 있다. | P1 | 저장된 프로필 간 궁합 분석. 종합 점수 및 항목별 해석 제공. |

### 5.2 Epic 2: AI 상담 (핵심 기능)

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-201 | 사용자는 AI와 대화하며 사주에 대해 질문할 수 있다. | P0 | 채팅 UI. 사용자의 사주 데이터를 컨텍스트로 포함. 한국어 자연어 응답. |
| US-202 | AI는 사용자의 현재 대운/세운/월운을 반영한 해석을 제공한다. | P0 | 현재 날짜 기준 자동 운세 기간 계산. 해당 기간의 특성 해석. |
| US-203 | 사용자는 특정 주제(연애, 직장, 건강, 재물, 학업)를 선택하여 상담받을 수 있다. | P0 | 주제별 프롬프트 분기. 주제에 맞는 심화 질문 및 해석. |
| US-204 | AI는 명리학적 근거를 함께 제시한다. | P1 | 응답에 관련 신살(神煞), 십성, 오행 관계 등을 인라인으로 설명. |
| US-205 | 사용자는 이전 상담 내역을 조회할 수 있다. | P1 | 날짜별 상담 이력 목록. 대화 전문 열람 가능. |
| US-206 | 사용자는 AI 응답에 대해 후속 질문을 이어갈 수 있다. | P0 | 멀티턴 대화. 이전 대화 맥락 유지 (세션당 최대 50턴). |

### 5.3 Epic 3: 운세 콘텐츠

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-301 | 사용자는 오늘의 운세를 확인할 수 있다. | P0 | 매일 자정 갱신. 일간(日干) 기준 일운(日運) 해석. Push 알림 옵션. |
| US-302 | 사용자는 월간/연간 운세를 확인할 수 있다. | P1 | 월운/세운 해석. 주요 이벤트 기간 하이라이트. |
| US-303 | 사용자는 운세 결과를 이미지 카드로 공유할 수 있다. | P1 | SNS 공유용 카드 이미지 자동 생성. 카카오톡/인스타그램 공유 연동. |
| US-304 | 사용자는 길일(吉日) 캘린더를 확인할 수 있다. | P2 | 이사, 결혼, 개업 등 목적별 길일 추천. 월별 캘린더 뷰. |

### 5.4 Epic 4: 사용자 계정 & 결제

| ID | User Story | Priority | Acceptance Criteria |
|----|-----------|----------|-------------------|
| US-401 | 사용자는 소셜 로그인으로 간편하게 가입할 수 있다. | P0 | 카카오/네이버/구글/Apple 로그인 지원. |
| US-402 | 무료 사용자는 일일 AI 상담 3회까지 이용할 수 있다. | P0 | 일일 상담 횟수 카운트. 초과 시 프리미엄 안내. |
| US-403 | 사용자는 프리미엄 구독을 결제할 수 있다. | P1 | 월간/연간 구독. 무제한 상담 + 심화 분석 기능. |
| US-404 | 사용자는 개별 심화 상담을 건별 결제할 수 있다. | P2 | 사주 종합 분석, 궁합 상세 리포트 등 일회성 결제. |

### 5.5 Functional Requirements Summary

| 카테고리 | 요구사항 | Priority |
|----------|---------|----------|
| 사주 엔진 | 만세력 기반 사주팔자 정확 산출 (1900~2100년) | P0 |
| 사주 엔진 | 대운(大運), 세운(歲運), 월운(月運), 일운(日運) 산출 | P0 |
| 사주 엔진 | 십성(十星), 12운성(十二運星), 신살(神煞) 산출 | P0 |
| AI 상담 | LLM 기반 자연어 사주 해석 | P0 |
| AI 상담 | 멀티턴 대화 컨텍스트 유지 | P0 |
| AI 상담 | 주제별 전문 프롬프트 체인 | P1 |
| 콘텐츠 | 일일 운세 자동 생성 및 Push 알림 | P0 |
| 사용자 | 소셜 로그인 (OAuth 2.0) | P0 |
| 결제 | Freemium 과금 모델 (상담 횟수 제한) | P1 |
| 공유 | SNS 공유용 카드 이미지 생성 | P1 |

### 5.6 Non-Functional Requirements

| 카테고리 | 요구사항 | 목표 |
|----------|---------|------|
| 성능 | AI 응답 지연시간 (Latency) | < 3초 (p95) |
| 성능 | 사주 산출 응답시간 | < 500ms |
| 확장성 | 동시 접속자 수 | 10,000명 (v1.0) |
| 가용성 | 서비스 Uptime | >= 99.5% |
| 보안 | 개인정보 암호화 (생년월일시) | AES-256 |
| 보안 | ISMS-P 인증 준비 | v1.0 이후 |
| 접근성 | 모바일 반응형 | 최소 360px 너비 지원 |
| 국제화 | 다국어 지원 구조 | i18n 기반 설계 (v1.0은 한국어만) |

---

## 6. System Architecture & Technical Requirements

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Web App      │  │  Mobile Web  │  │  KakaoTalk Mini App  │  │
│  │  (Next.js)    │  │  (Responsive)│  │  (Future)            │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼────────────────────┼──────────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (Kong / AWS API Gateway)         │
│         Rate Limiting / Auth / Request Routing / CORS            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Auth        │ │  Saju        │ │  AI Counsel  │
│  Service     │ │  Engine      │ │  Service     │
│              │ │  Service     │ │              │
│  - OAuth     │ │              │ │  - LLM Proxy │
│  - JWT       │ │  - 만세력     │ │  - Prompt    │
│  - Session   │ │  - 사주산출    │ │    Engine    │
│              │ │  - 운세계산    │ │  - RAG       │
│              │ │  - 신살판단    │ │  - Streaming │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │PostgreSQL│  │  Redis   │  │ Vector   │  │ Object Store  │  │
│  │(User,    │  │(Cache,   │  │ DB       │  │ (S3)          │  │
│  │ Session, │  │ Rate     │  │(Pinecone/│  │ (Share Cards, │  │
│  │ History) │  │ Limit)   │  │ pgvector)│  │  Assets)      │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | Next.js 15 (App Router) + TypeScript | SSR/SSG 지원, React 생태계, SEO 최적화 |
| **UI Framework** | Tailwind CSS + shadcn/ui | 빠른 UI 개발, 일관된 디자인 시스템 |
| **Backend** | Python 3.12 + FastAPI | AI/ML 생태계 호환, 비동기 처리, 빠른 개발 |
| **Saju Engine** | Python (자체 개발 라이브러리) | 만세력 계산, 사주 산출 로직의 정확도가 핵심 |
| **AI/LLM** | OpenAI GPT-4o / Claude API | 한국어 성능 우수, 프롬프트 엔지니어링 + RAG |
| **Vector DB** | pgvector (PostgreSQL 확장) | 명리학 지식 베이스 RAG용, 인프라 단순화 |
| **Database** | PostgreSQL 16 | 관계형 데이터, JSON 지원, pgvector 통합 |
| **Cache** | Redis 7 | 세션, 일일 운세 캐시, Rate Limiting |
| **Infra** | AWS (ECS Fargate + RDS + ElastiCache) | 관리형 서비스, Auto Scaling, 비용 효율 |
| **CI/CD** | GitHub Actions | 자동 테스트, 빌드, 배포 파이프라인 |
| **Monitoring** | Datadog / CloudWatch | APM, 로그 집계, 알림 |

### 6.3 Saju Engine (사주 산출 엔진) 상세

사주 산출 엔진은 본 서비스의 핵심 차별화 요소이다. 다음 기능을 정확하게 구현해야 한다:

| 기능 | 설명 |
|------|------|
| **만세력 변환** | 양력 <-> 음력 변환. 윤달 처리. 1900~2100년 범위. |
| **사주팔자 산출** | 연주(年柱), 월주(月柱), 일주(日柱), 시주(時柱) -- 각각 천간(天干) + 지지(地支) |
| **절기(節氣) 기반 월주** | 월주는 음력 1일이 아닌 절기 기준으로 산출 (입춘, 경칩 등) |
| **대운(大運) 계산** | 성별 + 연간 양음(陽陰)에 따른 순행/역행 대운 산출 |
| **세운/월운/일운** | 특정 시점의 운세 간지 계산 |
| **십성(十星) 배치** | 일간 기준 비견, 겁재, 식신, 상관, 편재, 정재, 편관, 정관, 편인, 정인 |
| **12운성(十二運星)** | 장생, 목욕, 관대, 건록, 제왕, 쇠, 병, 사, 묘, 절, 태, 양 |
| **신살(神煞)** | 주요 신살 30종 이상 (역마살, 도화살, 천을귀인, 문창귀인 등) |
| **오행(五行) 분석** | 목/화/토/금/수 분포 및 상생/상극 관계 분석 |
| **격국(格局) 판단** | 내격(정격) 8격 + 외격(특별격) 판단 |

### 6.4 AI Counsel Service 상세

```
┌─────────────────────────────────────────────────────┐
│                AI Counsel Service                     │
│                                                       │
│  ┌─────────────┐    ┌─────────────────────────────┐  │
│  │  Prompt      │    │  Knowledge Base (RAG)       │  │
│  │  Manager     │    │                             │  │
│  │             │    │  - 명리학 원전 텍스트          │  │
│  │  - System   │    │  - 해석 가이드라인             │  │
│  │    Prompt   │◄──►│  - 신살/격국 해설             │  │
│  │  - Topic    │    │  - 상담 사례 (익명화)          │  │
│  │    Router   │    │                             │  │
│  │  - Context  │    └─────────────────────────────┘  │
│  │    Builder  │                                     │
│  └──────┬──────┘                                     │
│         │                                            │
│         ▼                                            │
│  ┌─────────────┐    ┌─────────────────────────────┐  │
│  │  LLM        │    │  Response Post-Processor    │  │
│  │  Gateway    │───►│                             │  │
│  │             │    │  - 안전성 필터               │  │
│  │  - OpenAI   │    │  - 명리학 용어 주석           │  │
│  │  - Claude   │    │  - 구조화 포맷팅             │  │
│  │  - Fallback │    │  - 공유 카드 생성             │  │
│  └─────────────┘    └─────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**프롬프트 전략:**

1. **System Prompt**: 사주명리 전문가 페르소나 + 해석 원칙 + 윤리 가이드라인
2. **Context Injection**: 사용자 사주팔자 데이터 + 현재 운세(대운/세운/월운) + 이전 대화 요약
3. **Topic Router**: 주제(연애/직장/건강/재물/학업)에 따른 전문 프롬프트 분기
4. **RAG Retrieval**: 관련 명리학 지식을 벡터 검색으로 주입
5. **Safety Filter**: 건강/법률 조언 방지, 극단적 표현 필터링

### 6.5 Infrastructure Requirements

| 항목 | MVP | v1.0 |
|------|-----|------|
| API Server | ECS Fargate 2 tasks (0.5 vCPU, 1GB) | ECS Fargate 4+ tasks (1 vCPU, 2GB), Auto Scaling |
| Database | RDS PostgreSQL db.t3.medium | RDS PostgreSQL db.r6g.large, Read Replica |
| Cache | ElastiCache Redis t3.micro | ElastiCache Redis r6g.large |
| LLM API | OpenAI API (Pay-per-use) | Multi-provider (OpenAI + Claude), Fallback |
| CDN | CloudFront | CloudFront + Edge Caching |
| Storage | S3 Standard | S3 Standard + Lifecycle Policy |

---

## 7. Data Model & API Specification

### 7.1 Core Data Model (ERD)

```
┌─────────────────┐       ┌─────────────────────┐
│     users        │       │   saju_profiles      │
├─────────────────┤       ├─────────────────────┤
│ id (PK, UUID)   │──┐    │ id (PK, UUID)        │
│ email            │  │    │ user_id (FK)         │
│ nickname         │  └───►│ label (본인/가족/지인) │
│ provider         │       │ name                  │
│ provider_id      │       │ birth_date            │
│ is_premium       │       │ birth_time            │
│ premium_until    │       │ is_lunar              │
│ daily_consult_ct │       │ is_leap_month         │
│ created_at       │       │ gender                │
│ updated_at       │       │ saju_data (JSONB)     │
└─────────────────┘       │ created_at            │
                           └──────────┬────────────┘
                                      │
                           ┌──────────▼────────────┐
                           │   consultations        │
                           ├───────────────────────┤
                           │ id (PK, UUID)          │
                           │ user_id (FK)           │
                           │ profile_id (FK)        │
                           │ topic (ENUM)           │
                           │ status (ENUM)          │
                           │ created_at             │
                           │ updated_at             │
                           └──────────┬────────────┘
                                      │
                           ┌──────────▼────────────┐
                           │   messages             │
                           ├───────────────────────┤
                           │ id (PK, UUID)          │
                           │ consultation_id (FK)   │
                           │ role (user/assistant)  │
                           │ content (TEXT)         │
                           │ metadata (JSONB)       │
                           │ created_at             │
                           └───────────────────────┘

┌─────────────────────┐    ┌───────────────────────┐
│   payments           │    │   daily_fortunes       │
├─────────────────────┤    ├───────────────────────┤
│ id (PK, UUID)        │    │ id (PK, UUID)          │
│ user_id (FK)         │    │ profile_id (FK)        │
│ type (subscription/  │    │ date (DATE)            │
│       one_time)      │    │ fortune_data (JSONB)   │
│ amount               │    │ content (TEXT)         │
│ status               │    │ created_at             │
│ pg_transaction_id    │    └───────────────────────┘
│ created_at           │
└─────────────────────┘
```

### 7.2 saju_data JSONB Schema

```json
{
  "four_pillars": {
    "year":  { "stem": "甲", "branch": "子", "stem_kr": "갑", "branch_kr": "자" },
    "month": { "stem": "丙", "branch": "寅", "stem_kr": "병", "branch_kr": "인" },
    "day":   { "stem": "戊", "branch": "午", "stem_kr": "무", "branch_kr": "오" },
    "hour":  { "stem": "庚", "branch": "申", "stem_kr": "경", "branch_kr": "신" }
  },
  "five_elements": {
    "wood": 2, "fire": 3, "earth": 1, "metal": 2, "water": 0
  },
  "ten_stars": {
    "year_stem": "편인", "year_branch": "편관",
    "month_stem": "겁재", "month_branch": "비견",
    "day_branch": "겁재",
    "hour_stem": "식신", "hour_branch": "식신"
  },
  "twelve_stages": {
    "year": "사", "month": "장생", "day": "제왕", "hour": "병"
  },
  "special_stars": ["역마살", "천을귀인", "문창귀인"],
  "geokguk": "정관격",
  "major_luck_cycles": [
    { "age_start": 3, "age_end": 12, "stem": "丁", "branch": "卯" },
    { "age_start": 13, "age_end": 22, "stem": "戊", "branch": "辰" }
  ]
}
```

### 7.3 REST API Specification

#### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | 소셜 로그인 (OAuth callback) |
| POST | `/api/v1/auth/refresh` | JWT 토큰 갱신 |
| POST | `/api/v1/auth/logout` | 로그아웃 |

#### Saju Profiles

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/profiles` | 사주 프로필 생성 (사주 산출 포함) |
| GET | `/api/v1/profiles` | 내 프로필 목록 조회 |
| GET | `/api/v1/profiles/{id}` | 프로필 상세 조회 |
| DELETE | `/api/v1/profiles/{id}` | 프로필 삭제 |
| POST | `/api/v1/profiles/compatibility` | 궁합 분석 |

#### AI Consultation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/consultations` | 새 상담 세션 시작 |
| GET | `/api/v1/consultations` | 상담 이력 목록 |
| GET | `/api/v1/consultations/{id}` | 상담 상세 (메시지 포함) |
| POST | `/api/v1/consultations/{id}/messages` | 메시지 전송 (SSE 스트리밍 응답) |

#### Fortune Content

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/fortunes/daily` | 오늘의 운세 |
| GET | `/api/v1/fortunes/monthly` | 월간 운세 |
| GET | `/api/v1/fortunes/yearly` | 연간 운세 |
| GET | `/api/v1/fortunes/calendar` | 길일 캘린더 |

#### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/payments/subscribe` | 구독 결제 |
| POST | `/api/v1/payments/one-time` | 건별 결제 |
| GET | `/api/v1/payments/history` | 결제 이력 |

#### Share

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/share/card` | 공유 카드 이미지 생성 |

### 7.4 AI Consultation Message Flow (SSE Streaming)

```
Client                    API Gateway              AI Counsel Service         LLM API
  │                           │                           │                     │
  │  POST /consultations/     │                           │                     │
  │       {id}/messages       │                           │                     │
  │  { "content": "올해      │                           │                     │
  │    재물운이 어떤가요?" }   │                           │                     │
  │ ─────────────────────────►│                           │                     │
  │                           │  Forward + Auth           │                     │
  │                           │──────────────────────────►│                     │
  │                           │                           │  Build Context      │
  │                           │                           │  (사주 + 운세 +     │
  │                           │                           │   이전 대화 + RAG)  │
  │                           │                           │                     │
  │                           │                           │  LLM Request        │
  │                           │                           │────────────────────►│
  │                           │                           │                     │
  │  SSE: data: {"token":     │                           │  Stream tokens      │
  │    "올해"}                │◄──────────────────────────│◄────────────────────│
  │  SSE: data: {"token":     │                           │                     │
  │    " 재물운은"}           │◄──────────────────────────│◄────────────────────│
  │  SSE: data: {"token":     │                           │                     │
  │    "..."}                 │◄──────────────────────────│◄────────────────────│
  │  SSE: data: [DONE]        │                           │  Save to DB         │
  │◄──────────────────────────│◄──────────────────────────│                     │
  │                           │                           │                     │
```

---

## 8. UI/UX Requirements

### 8.1 Design Principles

| 원칙 | 설명 |
|------|------|
| **신뢰감 (Trust)** | 전통적이면서도 현대적인 톤. 한지(韓紙) 텍스처, 먹(墨) 컬러를 모던하게 재해석. |
| **단순함 (Simplicity)** | 사주 정보는 복잡하지만 UI는 단순하게. Progressive Disclosure 적용. |
| **접근성 (Accessibility)** | 연령대가 넓은 사용자층 고려. 큰 터치 영역, 명확한 타이포그래피. |
| **감성적 경험 (Emotional)** | 상담 결과에 감정적 공감과 따뜻함. 부정적 해석도 희망적 맥락으로 전달. |

### 8.2 Color System

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#1A1A2E` (심야 남색) | 메인 배경, 핵심 요소 |
| Secondary | `#E8D5B7` (한지 베이지) | 카드 배경, 보조 영역 |
| Accent | `#C9A96E` (금박 골드) | CTA 버튼, 강조 요소 |
| Text Primary | `#2C2C2C` | 본문 텍스트 |
| Text Secondary | `#8B8B8B` | 보조 텍스트 |
| Wood | `#4CAF50` | 오행 - 목(木) |
| Fire | `#F44336` | 오행 - 화(火) |
| Earth | `#FFC107` | 오행 - 토(土) |
| Metal | `#BDBDBD` | 오행 - 금(金) |
| Water | `#2196F3` | 오행 - 수(水) |

### 8.3 Core Screens

#### Screen 1: 홈 / 대시보드

```
┌──────────────────────────────┐
│  ≡   사주 AI        👤 프로필 │
├──────────────────────────────┤
│                              │
│  🌙 오늘의 운세               │
│  ┌────────────────────────┐  │
│  │  2026년 3월 25일        │  │
│  │  병인(丙寅)일            │  │
│  │                        │  │
│  │  "오늘은 재물운이        │  │
│  │   좋은 하루입니다..."    │  │
│  │                [더보기]  │  │
│  └────────────────────────┘  │
│                              │
│  📊 내 사주 요약              │
│  ┌────────────────────────┐  │
│  │  甲子  丙寅  戊午  庚申   │  │
│  │  갑자  병인  무오  경신   │  │
│  │                        │  │
│  │  [오행 분포 미니 차트]    │  │
│  └────────────────────────┘  │
│                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ │
│  │ 연애  │ │ 직장  │ │ 재물  │ │
│  │  운   │ │  운   │ │  운   │ │
│  └──────┘ └──────┘ └──────┘ │
│  ┌──────┐ ┌──────┐ ┌──────┐ │
│  │ 건강  │ │ 학업  │ │ 궁합  │ │
│  │  운   │ │  운   │ │ 분석  │ │
│  └──────┘ └──────┘ └──────┘ │
│                              │
├──────────────────────────────┤
│  🏠홈  💬상담  📅캘린더  ⚙설정 │
└──────────────────────────────┘
```

#### Screen 2: AI 상담 채팅

```
┌──────────────────────────────┐
│  ←  AI 상담 (재물운)     ···  │
├──────────────────────────────┤
│                              │
│  ┌────────────────────────┐  │
│  │ 🔮 사주AI               │  │
│  │ 안녕하세요! 재물운에     │  │
│  │ 대해 상담해 드릴게요.    │  │
│  │                        │  │
│  │ 현재 무오(戊午)일주에    │  │
│  │ 대운 경신(庚申)이       │  │
│  │ 흐르고 있어 식신생재의   │  │
│  │ 기운이 강합니다.        │  │
│  │                        │  │
│  │ 어떤 점이 궁금하신가요?  │  │
│  └────────────────────────┘  │
│                              │
│         ┌─────────────────┐  │
│         │ 올해 투자를 해도  │  │
│         │ 괜찮을까요?      │  │
│         └─────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │ 🔮 사주AI               │  │
│  │ 좋은 질문이에요.        │  │
│  │                        │  │
│  │ 올해 세운 병오(丙午)에   │  │
│  │ 일간 무토(戊土)가       │  │
│  │ 힘을 받아...            │  │
│  │                        │  │
│  │ 📌 편재(偏財)가 투출되어 │  │
│  │ 투자 의욕이 높아지는    │  │
│  │ 시기입니다. 다만...     │  │
│  └────────────────────────┘  │
│                              │
├──────────────────────────────┤
│  [메시지를 입력하세요...]  ➤  │
│  🎤 음성입력                  │
└──────────────────────────────┘
```

#### Screen 3: 사주 프로필 생성

```
┌──────────────────────────────┐
│  ←  사주 프로필 등록          │
├──────────────────────────────┤
│                              │
│  누구의 사주를 볼까요?        │
│  ○ 본인  ○ 가족  ○ 지인      │
│                              │
│  이름 (별명)                  │
│  ┌────────────────────────┐  │
│  │                        │  │
│  └────────────────────────┘  │
│                              │
│  생년월일                     │
│  ┌────┐ ┌────┐ ┌────┐      │
│  │1998│ │ 05 │ │ 15 │      │
│  └────┘ └────┘ └────┘      │
│  ● 양력  ○ 음력 (□ 윤달)    │
│                              │
│  태어난 시간                  │
│  ┌────┐ : ┌────┐           │
│  │ 14 │   │ 30 │           │
│  └────┘   └────┘           │
│  □ 시간을 모르겠어요         │
│                              │
│  성별                        │
│  ○ 남성  ○ 여성              │
│                              │
│  ┌────────────────────────┐  │
│  │     사주 분석하기 ▶      │  │
│  └────────────────────────┘  │
│                              │
└──────────────────────────────┘
```

### 8.4 Interaction Patterns

| 패턴 | 적용 | 설명 |
|------|------|------|
| Streaming Response | AI 상담 | 토큰 단위 실시간 출력으로 대기 시간 체감 감소 |
| Skeleton Loading | 사주 산출 | 결과 로딩 중 구조 미리보기 표시 |
| Pull to Refresh | 오늘의 운세 | 아래로 당겨 최신 운세 갱신 |
| Bottom Sheet | 용어 설명 | 명리학 용어 탭 시 하단 시트로 해설 표시 |
| Haptic Feedback | 사주 결과 확인 | 결과 생성 완료 시 미세 진동 (모바일) |

### 8.5 Typography

| Role | Font | Size | Weight |
|------|------|------|--------|
| Heading 1 | Pretendard | 28px | Bold (700) |
| Heading 2 | Pretendard | 22px | SemiBold (600) |
| Body | Pretendard | 16px | Regular (400) |
| Caption | Pretendard | 13px | Regular (400) |
| Hanja Display | Noto Serif KR | 32px | Bold (700) |
| Saju Pillar | Noto Serif KR | 24px | Medium (500) |

---

## 9. Release Plan & Milestones

### 9.1 Phase Overview

```
Phase 0        Phase 1          Phase 2         Phase 3         Phase 4
Discovery      MVP              Beta            v1.0 Launch     Growth
(4 weeks)      (8 weeks)        (4 weeks)       (2 weeks)       (Ongoing)
─────────────────────────────────────────────────────────────────────────►
2026 Q2        2026 Q2~Q3       2026 Q3         2026 Q4         2026 Q4~
```

### 9.2 Phase 0: Discovery (4주)

| Week | Deliverable |
|------|------------|
| W1-2 | 사주 엔진 프로토타입 (만세력 변환 + 사주 산출 정확도 검증) |
| W3 | AI 프롬프트 PoC (명리학 해석 품질 평가, 전문가 리뷰) |
| W4 | 기술 아키텍처 확정, 디자인 시스템 초안 |

**Phase Gate:** 사주 산출 정확도 100%, AI 해석 품질 전문가 평가 70% 이상

### 9.3 Phase 1: MVP (8주)

| Week | Backend | Frontend | AI/ML |
|------|---------|----------|-------|
| W1-2 | DB 스키마, Auth API, 프로필 CRUD | 프로젝트 셋업, 디자인 시스템, 로그인 | 프롬프트 v1 작성, RAG 파이프라인 구축 |
| W3-4 | 사주 엔진 API 통합, 상담 세션 API | 사주 입력 폼, 사주 결과 화면 | 주제별 프롬프트 분기, 컨텍스트 빌더 |
| W5-6 | SSE 스트리밍, 상담 이력 API | 채팅 UI, 스트리밍 렌더링 | RAG 지식 베이스 구축 (명리학 원전) |
| W7-8 | 일일 운세 배치, Rate Limiting | 홈 대시보드, 오늘의 운세 | 프롬프트 튜닝, 안전 필터 |

**MVP Scope:**
- 소셜 로그인 (카카오)
- 사주 프로필 생성 및 저장 (1개)
- AI 상담 (일 3회 제한)
- 오늘의 운세
- 모바일 반응형 웹

**Phase Gate:** 내부 QA 완료, 핵심 기능 동작, 크래시 없음

### 9.4 Phase 2: Beta (4주)

| Week | Focus |
|------|-------|
| W1-2 | 클로즈드 베타 (200명). 사용자 피드백 수집. 버그 수정. AI 응답 품질 모니터링. |
| W3 | 피드백 반영 개선. 프롬프트 v2 튜닝. 성능 최적화. |
| W4 | 오픈 베타 (2,000명). 부하 테스트. 결제 시스템 연동 테스트. |

**Phase Gate:** CSAT >= 4.0, 크리티컬 버그 0건, p95 응답시간 < 3초

### 9.5 Phase 3: v1.0 Launch (2주)

| Week | Focus |
|------|-------|
| W1 | 최종 QA, 보안 점검, 결제 PG 연동 완료 (Toss Payments), ASO/SEO 준비 |
| W2 | 프로덕션 배포, 모니터링 대시보드 셋업, 런칭 마케팅, CS 대응 체계 가동 |

**v1.0 Full Scope (MVP 이후 추가분):**
- 소셜 로그인 확대 (네이버, 구글, Apple)
- 사주 프로필 5개까지 저장
- 궁합 분석
- 월간/연간 운세
- 프리미엄 구독 결제
- SNS 공유 카드
- Push 알림 (오늘의 운세)

### 9.6 Phase 4: Growth (지속)

| 분기 | Focus |
|------|-------|
| 2027 Q1 | 길일 캘린더, 건별 심화 상담 결제, 프롬프트 v3 (전문가 피드백 기반) |
| 2027 Q2 | 카카오톡 미니앱, 음성 입력, AI 해석 품질 자동 평가 시스템 |
| 2027 Q3 | 영어 지원 (글로벌 확장 1차), LLM 파인튜닝 검토 |
| 2027 Q4 | 네이티브 앱 (React Native), 커뮤니티 기능 |

---

## 10. Risks, Constraints & Appendix

### 10.1 Risk Assessment

| ID | Risk | Impact | Probability | Mitigation |
|----|------|--------|------------|------------|
| R1 | **LLM 환각 (Hallucination)**: AI가 명리학적으로 틀린 해석을 생성 | High | High | 사주 엔진의 정확한 데이터를 프롬프트에 주입하여 해석의 기반을 고정. RAG로 원전 지식 보강. 전문가 정기 품질 평가. |
| R2 | **사주 산출 오류**: 절기 경계, 자시(子時) 처리 등에서 산출 오류 | Critical | Medium | 기존 검증된 만세력 데이터 활용. 1,000개+ 테스트 케이스. 전문 역술인의 교차 검증. |
| R3 | **LLM API 비용 급증**: 사용자 증가에 따른 API 호출 비용 통제 실패 | High | Medium | 응답 캐싱 전략, 토큰 길이 최적화, 무료 사용자 일일 제한, 비용 모니터링 알림. |
| R4 | **법적 리스크**: 운세 서비스의 법적 지위 불명확, 개인정보 이슈 | Medium | Low | "엔터테인먼트 목적" 면책 조항 명시. 개인정보보호법 준수. 법률 자문. |
| R5 | **LLM 제공사 정책 변경**: OpenAI/Anthropic 가격 인상 또는 서비스 중단 | High | Low | Multi-provider 아키텍처로 fallback 확보. 프롬프트 표준화. |
| R6 | **경쟁사 진입**: 대형 포털(네이버, 카카오)의 AI 운세 서비스 론칭 | High | Medium | 명리학 도메인 전문성 차별화, 사용자 데이터 축적, 빠른 기능 반복. |
| R7 | **사용자 심리적 의존**: 운세 서비스에 과도하게 의존하는 사용자 발생 | Medium | Medium | 사용 빈도 알림, "참고용" 면책 문구, 상담 횟수 soft cap, 전문 상담 안내 연결. |

### 10.2 Constraints

| 제약 사항 | 설명 |
|-----------|------|
| **예산** | 초기 인프라 + LLM API 비용 월 500만원 이내 (MVP 기간) |
| **인력** | Backend 2명, Frontend 2명, AI/ML 1명, 디자인 1명, PM 1명 (총 7명) |
| **일정** | MVP 8주 내 출시 (2026년 Q2 말 목표) |
| **기술** | v1.0에서는 LLM 파인튜닝 없이 프롬프트 엔지니어링 + RAG만 활용 |
| **규제** | 개인정보보호법 준수 필수. 생년월일시 = 민감정보로 암호화 저장. |
| **도메인** | 사주명리학의 유파별 차이 존재. v1.0은 "정통 명리학" 기준 단일 해석 체계 채택. |

### 10.3 Dependencies

| 의존성 | 설명 | Risk Level |
|--------|------|------------|
| OpenAI / Anthropic API | LLM 핵심 기능 제공 | High |
| Toss Payments | 결제 PG 연동 | Medium |
| 카카오 OAuth | 주 로그인 수단 | Medium |
| AWS 인프라 | 전체 서비스 호스팅 | High |
| 만세력 데이터 | 사주 산출 기초 데이터 | Low (Static Data) |

### 10.4 Legal & Ethical Guidelines

1. **면책 조항**: 모든 AI 상담 결과에 "본 서비스는 엔터테인먼트 목적으로 제공되며, 전문적인 의학/법률/재정 조언을 대체하지 않습니다" 문구 상시 노출.
2. **건강/위기 대응**: 사용자가 건강 위기, 자해/자살 암시 키워드를 입력할 경우, 전문 상담 기관 (정신건강위기상담전화 1577-0199 등) 안내로 즉시 전환.
3. **미성년자 보호**: 14세 미만 사용자 가입 제한. 미성년자에게 결제 유도 금지.
4. **부정적 해석 완화**: AI는 지나치게 부정적이거나 공포를 유발하는 표현을 사용하지 않도록 프롬프트 가드레일 적용.
5. **데이터 보호**: 생년월일시 AES-256 암호화 저장. 상담 내역 90일 후 자동 익명화 옵션 제공. GDPR/PIPA 준수.

### 10.5 Glossary

| 용어 | 한자 | 설명 |
|------|------|------|
| 사주 | 四柱 | 네 개의 기둥. 연주, 월주, 일주, 시주를 통칭 |
| 팔자 | 八字 | 사주의 여덟 글자 (천간 4 + 지지 4) |
| 천간 | 天干 | 갑을병정무기경신임계 (10개) |
| 지지 | 地支 | 자축인묘진사오미신유술해 (12개) |
| 오행 | 五行 | 목(木), 화(火), 토(土), 금(金), 수(水) |
| 만세력 | 萬歲曆 | 연월일시의 간지를 기록한 역법 데이터 |
| 대운 | 大運 | 10년 단위의 큰 운의 흐름 |
| 세운 | 歲運 | 1년 단위의 운 (해당 년도의 간지) |
| 월운 | 月運 | 1개월 단위의 운 |
| 일운 | 日運 | 1일 단위의 운 |
| 십성 | 十星 | 일간 기준 다른 간지와의 관계 (비견, 겁재, 식신, 상관, 편재, 정재, 편관, 정관, 편인, 정인) |
| 12운성 | 十二運星 | 오행의 생왕사절 12단계 순환 |
| 신살 | 神煞 | 특정 간지 조합에서 나타나는 특수한 기운/성질 |
| 격국 | 格局 | 사주의 전체 구조와 성격을 판단하는 틀 |
| RAG | - | Retrieval-Augmented Generation. 외부 지식을 검색하여 LLM에 제공하는 기법 |

### 10.6 References

1. 명리학 기초 교재: "적천수(滴天髓)", "자평진전(子平眞詮)", "궁통보감(窮通寶鑑)"
2. 만세력 데이터 출처: 한국천문연구원 천문역법
3. LLM Prompt Engineering: OpenAI Best Practices, Anthropic Claude Documentation
4. 경쟁 서비스 분석: 점신, 사주팔자, 운세알림 등 기존 사주 앱 벤치마크

### 10.7 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-03-25 | PM Lead Agent | Initial draft - all 10 sections |
| 1.0 | 2026-03-25 | PM Lead Agent | Approved and finalized |

---

> **Approval:**
> This PRD has been reviewed and approved for execution. Development may proceed to Phase 0 (Discovery).
