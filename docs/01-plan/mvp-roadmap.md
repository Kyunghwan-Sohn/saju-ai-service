# Saju AI Service - MVP Roadmap (8 Weeks)

> **Version:** 1.0
> **Date:** 2026-03-25
> **Author:** CTO Lead
> **Based on:** [PRD v1.0](../00-pm/saju-ai-service.prd.md), [Architecture v1.0](./saju-ai-architecture.md)

---

## Overview

MVP 기간: **8주 (2026년 Q2)**
팀 구성: Backend 2명, Frontend 2명, AI/ML 1명, Design 1명, PM 1명 (총 7명)
목표: 핵심 기능 동작 확인 + 내부 QA 완료 + 클로즈드 베타 준비

### MVP Scope (PRD 9.3 기준)

| 포함 | 제외 (v1.0 이후) |
|------|-----------------|
| 소셜 로그인 (카카오) | 네이버/구글/Apple 로그인 |
| 사주 프로필 생성 및 저장 (1개) | 프로필 5개, 궁합 분석 |
| AI 상담 (일 3회 제한) | 무제한 상담, 심화 분석 |
| 오늘의 운세 | 월간/연간 운세, 길일 캘린더 |
| 모바일 반응형 웹 | SNS 공유 카드, Push 알림 |
| 기본 안전성 필터 | 프리미엄 구독, 결제 |

---

## Week 1-2: Foundation (기반 구축)

### 목표
프로젝트 기반 구조 수립, 사주 엔진 핵심 구현, LLM 연동 PoC, 인증 시스템 구현

### Backend (2명)

#### BE-1: 프로젝트 셋업 & 인프라 (Week 1)
- [ ] FastAPI 프로젝트 구조 생성 (모듈러 모놀리스 구조)
- [ ] Docker 개발 환경 구성 (docker-compose: API + PostgreSQL + Redis)
- [ ] Alembic 마이그레이션 셋업
- [ ] DB 스키마 초기 마이그레이션 (users, saju_profiles 테이블)
- [ ] 공통 모듈 구현 (config, database, redis, exceptions, middleware)
- [ ] 구조화 로깅 셋업 (JSON 로그)
- [ ] CI 파이프라인 (GitHub Actions: lint, test, build)

#### BE-2: 인증 모듈 구현 (Week 1-2)
- [ ] 카카오 OAuth 2.0 연동 (`POST /api/v1/auth/login`)
- [ ] JWT 발급/검증 (Access Token 1h, Refresh Token 30d)
- [ ] Refresh Token 관리 (`POST /api/v1/auth/refresh`)
- [ ] 로그아웃 (JWT 블랙리스트, `POST /api/v1/auth/logout`)
- [ ] 인증 미들웨어 (`get_current_user` dependency)
- [ ] 단위 테스트 (인증 흐름 전체)

#### BE-3: 사주 엔진 핵심 구현 (Week 1-2)
- [ ] 만세력 데이터 로드 (solar_terms.json, daily_stems.json, lunar_calendar.json)
- [ ] 양력/음력 변환 로직 (윤달 처리 포함)
- [ ] 절기 경계 판단 로직
- [ ] 사주팔자 산출 (연주/월주/일주/시주)
  - [ ] 입춘 기준 연주 전환
  - [ ] 절기 기준 월주 산출
  - [ ] 만세력 기반 일주 조회
  - [ ] 일간 기반 시주 산출
  - [ ] 자시(야자시/조자시) 처리
- [ ] 오행 분석 (목/화/토/금/수 분포 계산)
- [ ] 정확도 테스트 (최소 500 케이스)

**Phase Gate (Week 2 end):**
- 사주 산출 정확도 테스트 500 케이스 중 100% 통과
- 카카오 로그인 -> JWT 발급 흐름 동작 확인

### Frontend (2명)

#### FE-1: 프로젝트 셋업 & 디자인 시스템 (Week 1)
- [ ] Next.js 15 (App Router) + TypeScript 프로젝트 생성
- [ ] Tailwind CSS + shadcn/ui 셋업
- [ ] 디자인 토큰 정의 (PRD 8.2 컬러 시스템: 심야남색, 한지베이지, 금박골드)
- [ ] 오행 컬러 매핑 (Wood: #4CAF50, Fire: #F44336, Earth: #FFC107, Metal: #BDBDBD, Water: #2196F3)
- [ ] 타이포그래피 셋업 (Pretendard, Noto Serif KR)
- [ ] 공통 컴포넌트 라이브러리 시작 (Button, Input, Card, Modal)
- [ ] 반응형 레이아웃 (360px ~ 1440px)
- [ ] API 클라이언트 셋업 (axios + React Query)

#### FE-2: 로그인 & 온보딩 화면 (Week 1-2)
- [ ] 카카오 로그인 페이지
- [ ] OAuth 콜백 처리
- [ ] JWT 토큰 관리 (httpOnly cookie 또는 secure storage)
- [ ] 인증 상태 관리 (Zustand)
- [ ] 로그인 후 리다이렉트 처리
- [ ] 로딩/에러 상태 UI

### AI/ML (1명)

#### AI-1: LLM 연동 PoC (Week 1-2)
- [ ] Claude API 연동 테스트 (스트리밍 모드)
- [ ] GPT-4o API 연동 테스트 (폴백용)
- [ ] System Prompt v0.1 작성 (명리학 전문가 페르소나)
- [ ] 사주 데이터 Context Injection 템플릿 설계
- [ ] 주제 분류 로직 PoC (연애/직장/건강/재물/학업/일반)
- [ ] 프롬프트 품질 평가 (10개 샘플 사주 x 5개 주제 = 50개 응답 생성)
- [ ] RAG 파이프라인 PoC (pgvector + LangChain)
  - [ ] 명리학 텍스트 청크 분할 (적천수 일부)
  - [ ] text-embedding-3-small 임베딩 생성
  - [ ] 벡터 유사도 검색 테스트

### Design (1명)
- [ ] Figma 디자인 시스템 구축 (컬러, 타이포, 컴포넌트)
- [ ] 로그인/온보딩 화면 디자인
- [ ] 사주 입력 폼 디자인
- [ ] 사주 결과 화면 디자인 (오행 차트, 사주 기둥 표시)

---

## Week 3-4: Core Features (핵심 기능)

### 목표
사주 프로필 CRUD, AI 상담 핵심 플로우, 사주 결과 시각화

### Backend

#### BE-4: 사주 엔진 고급 기능 (Week 3)
- [ ] 십성(十星) 계산 로직 (일간 기준 10종)
- [ ] 12운성(十二運星) 계산 로직 (양간/음간 구분)
- [ ] 신살(神煞) 판단 로직 (30종 이상)
- [ ] 격국(格局) 판단 로직 (정격 8격 + 외격)
- [ ] 대운(大運) 계산 (순행/역행, 대운수 산출)
- [ ] 세운/월운/일운 계산
- [ ] 정확도 테스트 확장 (1,000 케이스 이상)

#### BE-5: 프로필 API & 상담 API (Week 3-4)
- [ ] 사주 프로필 CRUD API
  - [ ] `POST /api/v1/profiles` (사주 산출 + 저장)
  - [ ] `GET /api/v1/profiles` (목록 조회)
  - [ ] `GET /api/v1/profiles/{id}` (상세 조회)
  - [ ] `DELETE /api/v1/profiles/{id}` (삭제)
  - [ ] 프로필 개수 제한 (MVP: 1개)
- [ ] saju_data JSONB 스키마 설계 및 Pydantic 검증
- [ ] 상담 세션 API
  - [ ] `POST /api/v1/consultations` (세션 생성)
  - [ ] `GET /api/v1/consultations` (이력 조회, cursor pagination)
  - [ ] `GET /api/v1/consultations/{id}` (상세 + 메시지)
- [ ] 상담 메시지 API + SSE 스트리밍
  - [ ] `POST /api/v1/consultations/{id}/messages` (SSE 응답)
- [ ] 일일 상담 횟수 제한 (Redis 카운터, Free: 3회)

### Frontend

#### FE-3: 사주 입력 & 결과 화면 (Week 3)
- [ ] 사주 프로필 등록 폼 (PRD Screen 3)
  - [ ] 이름/별명 입력
  - [ ] 생년월일 날짜 선택기 (양력/음력/윤달)
  - [ ] 태어난 시간 선택 (시간 모름 옵션)
  - [ ] 성별 선택
  - [ ] 대상 구분 (본인/가족/지인)
- [ ] 사주 결과 화면
  - [ ] 사주 기둥 표시 (한자 + 한글, 천간/지지)
  - [ ] 오행 분포 차트 (도넛 차트 또는 바 차트)
  - [ ] 십성 배치 표시
  - [ ] 격국/신살 요약
  - [ ] Skeleton Loading 적용

#### FE-4: AI 상담 채팅 UI (Week 3-4)
- [ ] 채팅 화면 레이아웃 (PRD Screen 2)
- [ ] 주제 선택 화면 (연애/직장/건강/재물/학업)
- [ ] 메시지 입력 & 전송
- [ ] SSE 스트리밍 응답 렌더링 (토큰 단위 실시간 출력)
- [ ] 타이핑 인디케이터 (AI 응답 생성 중)
- [ ] 이전 대화 이력 표시
- [ ] 일일 상담 제한 안내 UI (3회 초과 시)
- [ ] 명리학 용어 탭 시 하단 시트 (Bottom Sheet) 설명

### AI/ML

#### AI-2: 프롬프트 엔진 v1 & Context Builder (Week 3-4)
- [ ] System Prompt v1 완성 (해석 원칙 + 윤리 가이드라인 + 응답 형식)
- [ ] Topic Router 구현 (사용자 질문 -> 주제 분류)
- [ ] 주제별 전문 프롬프트 6종 작성 (연애/직장/건강/재물/학업/일반)
- [ ] Context Builder 구현
  - [ ] 사주 데이터 포맷팅 (사주팔자 + 오행 + 십성 + 신살 + 격국)
  - [ ] 현재 운세 주입 (대운/세운/월운/일운)
  - [ ] 이전 대화 요약 (최근 10턴)
- [ ] LLM Gateway 구현 (Claude Primary, GPT-4o Fallback)
- [ ] SSE 스트리밍 파이프라인 구현

### Design
- [ ] AI 상담 채팅 화면 디자인
- [ ] 상담 이력 목록 화면 디자인
- [ ] 주제 선택 화면 디자인
- [ ] 상담 제한 안내 모달 디자인

**Phase Gate (Week 4 end):**
- 사주 입력 -> 산출 -> 저장 -> AI 상담 전체 플로우 동작
- SSE 스트리밍으로 AI 응답 실시간 출력 확인
- 1,000 케이스 사주 정확도 테스트 통과

---

## Week 5-6: Content & Polish (콘텐츠 & 완성도)

### 목표
RAG 지식 베이스 구축, 일일 운세, 홈 대시보드, 응답 품질 향상

### Backend

#### BE-6: 운세 콘텐츠 시스템 (Week 5)
- [ ] daily_fortunes 테이블 마이그레이션
- [ ] 일일 운세 배치 생성 (Celery Beat, 매일 자정 KST)
  - [ ] 일간(日干)별 10종 일운 해석 생성 (LLM 배치 호출)
  - [ ] 프로필별 개인화 운세 저장
- [ ] `GET /api/v1/fortunes/daily` API
- [ ] 운세 캐싱 (Redis, TTL 24h)
- [ ] 운세 미생성 시 실시간 Fallback 생성

#### BE-7: Rate Limiting & 최적화 (Week 5-6)
- [ ] Redis 기반 Rate Limiting 미들웨어
  - [ ] IP 기반 (비인증: 100 req/h)
  - [ ] 사용자 기반 (Free: 500 req/h)
  - [ ] AI 상담 burst 방지 (분당 5회)
- [ ] API 응답 캐싱 (사주 프로필 데이터)
- [ ] DB 쿼리 최적화 (N+1 방지, eager loading)
- [ ] 생년월일시 AES-256 암호화 저장 구현

### Frontend

#### FE-5: 홈 대시보드 (Week 5)
- [ ] 홈 화면 구현 (PRD Screen 1)
  - [ ] 오늘의 운세 카드 (일간 + 간단 해석)
  - [ ] 내 사주 요약 (사주 기둥, 오행 미니 차트)
  - [ ] 주제별 바로가기 (연애/직장/재물/건강/학업/궁합)
- [ ] 하단 탭 네비게이션 (홈/상담/캘린더/설정)
- [ ] Pull to Refresh (오늘의 운세)
- [ ] Skeleton Loading 전체 적용

#### FE-6: 프로필 관리 & 설정 (Week 5-6)
- [ ] 프로필 목록 화면
- [ ] 프로필 상세 화면 (사주 전체 데이터)
- [ ] 설정 화면 (계정 정보, 로그아웃)
- [ ] 에러 처리 UI (네트워크 에러, 서버 에러)
- [ ] 빈 상태 (empty state) UI
- [ ] 반응형 레이아웃 최종 QA (360px ~ 1440px)

### AI/ML

#### AI-3: RAG 지식 베이스 구축 (Week 5-6)
- [ ] 명리학 원전 텍스트 수집 및 정리
  - [ ] 적천수(滴天髓) 전문 + 해설
  - [ ] 자평진전(子平眞詮) 전문 + 해설
  - [ ] 궁통보감(窮通寶鑑) 핵심 발췌
- [ ] 청크 분할 (500자, 100자 오버랩)
- [ ] 메타데이터 태깅 (출처, 주제, 관련 오행/십성)
- [ ] 벡터 임베딩 생성 (text-embedding-3-small)
- [ ] pgvector 테이블 구축 (knowledge_chunks)
- [ ] 검색 품질 테스트 (적중률 평가)
- [ ] RAG 파이프라인 통합 (Context Builder에 연결)

#### AI-4: 안전성 필터 구현 (Week 6)
- [ ] 위기 키워드 감지 (자살/자해 관련)
- [ ] 전문 상담 기관 안내 메시지 (정신건강위기상담전화 1577-0199)
- [ ] 의학/법률 조언 차단 필터
- [ ] 부정적 해석 완화 후처리
- [ ] 면책 조항 자동 삽입
- [ ] 명리학 용어 주석 삽입 로직

### Design
- [ ] 홈 대시보드 디자인
- [ ] 프로필 관리 화면 디자인
- [ ] 설정 화면 디자인
- [ ] 에러/빈 상태 디자인
- [ ] 안전성 경고 메시지 디자인

**Phase Gate (Week 6 end):**
- 홈 -> 운세 확인 -> AI 상담 전체 사용자 여정 완성
- RAG 적용 후 AI 응답 품질 향상 확인 (전문가 샘플 리뷰)
- 안전성 필터 동작 확인

---

## Week 7-8: Stabilization & Launch Prep (안정화 & 출시 준비)

### 목표
통합 테스트, 성능 최적화, 배포 파이프라인 완성, 클로즈드 베타 준비

### Backend

#### BE-8: 테스트 & 최적화 (Week 7)
- [ ] 통합 테스트 (API E2E 테스트)
  - [ ] 인증 흐름 E2E
  - [ ] 프로필 생성 -> 상담 -> 운세 E2E
  - [ ] Rate Limiting 테스트
  - [ ] SSE 스트리밍 E2E
- [ ] 사주 산출 정확도 최종 검증 (1,000+ 케이스)
- [ ] 성능 테스트 (부하 테스트)
  - [ ] 동시 접속 100명 (MVP 수준)
  - [ ] SSE 스트리밍 동시 처리
- [ ] API 응답 시간 최적화 (p95 < 500ms 일반, < 3초 AI)
- [ ] 메모리 누수 점검

#### BE-9: 배포 & 인프라 (Week 7-8)
- [ ] AWS 인프라 프로비저닝 (Terraform/CDK)
  - [ ] VPC, Subnet, Security Group
  - [ ] ECS Fargate Cluster + Task Definition
  - [ ] RDS PostgreSQL 16 (db.t3.medium)
  - [ ] ElastiCache Redis 7 (cache.t3.micro)
  - [ ] S3 Bucket
  - [ ] API Gateway
  - [ ] CloudFront Distribution
- [ ] Secrets Manager 설정 (API 키, DB 비밀번호)
- [ ] CD 파이프라인 (GitHub Actions -> ECR -> ECS)
- [ ] Staging 환경 배포 및 검증
- [ ] Production 환경 배포
- [ ] 헬스체크 엔드포인트 (`/health`, `/ready`)

### Frontend

#### FE-7: 테스트 & 반응형 QA (Week 7)
- [ ] 컴포넌트 테스트 (Jest + Testing Library)
- [ ] E2E 테스트 (Playwright)
  - [ ] 로그인 -> 프로필 생성 -> 상담 플로우
  - [ ] 모바일 뷰포트 (360px, 390px, 414px)
  - [ ] 태블릿 뷰포트 (768px)
  - [ ] 데스크톱 뷰포트 (1024px, 1440px)
- [ ] 크로스 브라우저 테스트 (Chrome, Safari, Samsung Internet)
- [ ] Lighthouse 성능 점수 최적화 (목표: 90+)
- [ ] 접근성 점검 (큰 터치 영역, 명확한 타이포그래피)

#### FE-8: 배포 & 모니터링 (Week 8)
- [ ] Next.js 빌드 최적화 (번들 사이즈 분석, 코드 스플리팅)
- [ ] CloudFront 배포 설정
- [ ] 에러 트래킹 연동 (Sentry)
- [ ] 웹 성능 모니터링 (Core Web Vitals)
- [ ] PWA 기본 설정 (manifest, service worker)
- [ ] 메타 태그 / OG 태그 (SEO)

### AI/ML

#### AI-5: 프롬프트 튜닝 & 최종 검증 (Week 7-8)
- [ ] 프롬프트 v1 최종 튜닝
  - [ ] 50개 사주 x 6개 주제 = 300개 응답 생성 및 품질 평가
  - [ ] 응답 일관성 검증 (동일 사주에 대한 일관된 해석)
  - [ ] 토큰 사용량 최적화 (비용 절감)
- [ ] LLM Fallback 테스트 (Claude 장애 -> GPT-4o 전환)
- [ ] 안전성 필터 최종 검증 (엣지 케이스)
- [ ] RAG 검색 품질 최종 검증

### Infra / Ops

#### OPS-1: 모니터링 & 알림 (Week 8)
- [ ] CloudWatch 대시보드 셋업
  - [ ] ECS CPU/Memory 메트릭
  - [ ] RDS 성능 메트릭
  - [ ] Redis 메트릭
- [ ] 알림 설정
  - [ ] 에러율 > 5% (5분 기준)
  - [ ] API p95 > 5초
  - [ ] LLM API 비용 일일 한도 80%
- [ ] 로그 수집 (CloudWatch Logs)
- [ ] Sentry 에러 트래킹 (Backend + Frontend)

**Phase Gate (Week 8 end):**
- 전체 기능 통합 동작 확인 (크래시 없음)
- 사주 산출 정확도 1,000 케이스 100% 통과
- Production 환경 배포 완료
- 모니터링/알림 시스템 가동

---

## Milestone Summary

| Week | Milestone | Deliverable | Gate Criteria |
|------|-----------|-------------|---------------|
| W2 | Foundation Complete | 사주 엔진 + 인증 동작 | 사주 500 케이스 100%, 로그인 동작 |
| W4 | Core Flow Complete | 사주 입력 -> AI 상담 E2E | 전체 플로우 동작, SSE 스트리밍 확인 |
| W6 | Content Complete | 운세 + RAG + 안전 필터 | 사용자 여정 완성, 품질 샘플 리뷰 통과 |
| W8 | MVP Ready | Production 배포 완료 | 무크래시, 1000 케이스, 모니터링 가동 |

---

## Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| 사주 엔진 정확도 미달 | Critical | W1-2에 최우선 착수, 외부 만세력 데이터 교차 검증 |
| LLM 응답 품질 불안정 | High | W3-4 프롬프트 집중 튜닝, RAG 보강, Fallback LLM |
| 절기 경계 엣지 케이스 | High | 경계 케이스 전용 테스트 세트 100+ 작성 |
| SSE 스트리밍 불안정 | Medium | W3-4 초기 검증, 타임아웃/재연결 로직 |
| 8주 일정 초과 | Medium | Week별 Phase Gate로 조기 감지, 기능 우선순위 컷 |

---

## Success Criteria (MVP Exit)

- [ ] 사주팔자 산출 정확도 100% (1,000+ 테스트 케이스)
- [ ] 카카오 로그인 -> 프로필 생성 -> AI 상담 -> 오늘의 운세 전체 플로우 동작
- [ ] AI 상담 SSE 스트리밍 첫 토큰 < 1.5초 (p95)
- [ ] API p95 응답시간 < 500ms (일반 API)
- [ ] 모바일 360px 레이아웃 정상 표시
- [ ] 안전성 필터 동작 (위기 키워드 -> 전문 상담 안내)
- [ ] Production 환경 안정 운영 (24시간 무크래시)
- [ ] 모니터링/알림 시스템 정상 동작

---

## Post-MVP: Beta Phase (Week 9-12)

MVP 완료 후 바로 Beta Phase로 전환한다 (PRD 9.4 참조).

| Week | Focus |
|------|-------|
| W9-10 | 클로즈드 베타 (200명), 피드백 수집, 버그 수정 |
| W11 | 프롬프트 v2 튜닝, 성능 최적화, 피드백 반영 |
| W12 | 오픈 베타 (2,000명), 부하 테스트, 결제 시스템 준비 |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-25 | CTO Lead | Initial MVP roadmap based on PRD v1.0 |
