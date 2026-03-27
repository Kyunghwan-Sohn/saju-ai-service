# Architecture Concept v2: DB-First + abcllm Batch Transformation

> **Version:** 2.0
> **Date:** 2026-03-25
> **Status:** Approved (Concept Pivot)
> **Supersedes:** v1.0 실시간 LLM 호출 방식

---

## 1. 컨셉 변경 요약

### v1.0 (폐기)
```
사용자 요청 → 사주 계산 → LLM 실시간 호출 → SSE 스트리밍 → 응답
                              ↑ 느림 (2~10초), 비쌈 (건당 토큰 비용)
```

### v2.0 (채택)
```
[오프라인 배치]
사주 조합 전체 → abcllm 배치 생성 → DB 저장 (사전 구축)
                     ↓ 주기적 재실행
              abcllm 서술 변형 → DB 업데이트 (표현 다양화)

[온라인 서빙]
사용자 요청 → 사주 계산 → DB 조회 → 즉시 응답 (< 100ms)
```

---

## 2. 핵심 설계 원칙

### 2.1 DB-First Architecture
- **모든 사주 해석 콘텐츠는 사전에 DB에 저장**
- 사용자 요청 시 실시간 LLM 호출 없음
- DB에서 바로 송출 → 응답 속도 < 100ms
- LLM 비용은 배치 생성 시에만 발생 (예측 가능한 고정 비용)

### 2.2 abcllm Batch Transformation
- abcllm을 통해 **서술 형태를 지속적으로 변형**
- 같은 사주 조합이라도 매번 다른 표현으로 제공
- 주기적 DB 업데이트로 콘텐츠 신선도 유지
- 변형 스케줄: 일일 운세(매일), 기본 풀이(주간), 상세 풀이(월간)

### 2.3 콘텐츠 매트릭스 (사전 구축 범위)

| 콘텐츠 유형 | 조합 수 | 변형 버전 | 총 레코드 | DB 업데이트 주기 |
|------------|---------|----------|----------|----------------|
| 기본 사주 풀이 | 518,400 (60간지⁴) | 3 ver | ~1,555,200 | 월간 |
| 오늘의 운세 | 60 (일주 기준) × 12 (월운) | 5 ver | ~3,600 | 매일 새 버전 |
| 연애운 | 518,400 | 2 ver | ~1,036,800 | 격주 |
| 재물운 | 518,400 | 2 ver | ~1,036,800 | 격주 |
| 직업운 | 518,400 | 2 ver | ~1,036,800 | 격주 |
| 궁합 | 3,600 (60×60) | 3 ver | ~10,800 | 월간 |
| 신년 운세 | 60 × 10 (대운) | 2 ver | ~1,200 | 연간 |

> **핵심**: 실제 서비스 초기에는 일주(60개) 기준 콘텐츠부터 시작.
> 점진적으로 월주+일주(720개) → 전체 사주(518,400개)로 확장.

---

## 3. 시스템 아키텍처 (v2)

```
┌─────────────────────────────────────────────────────────────────┐
│                     OFFLINE (배치 파이프라인)                      │
│                                                                   │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────────┐  │
│  │  사주     │    │  abcllm       │    │  Content DB          │  │
│  │  조합     │───▶│  Batch Engine │───▶│  (PostgreSQL)        │  │
│  │  Generator│    │               │    │                      │  │
│  │           │    │  - 서술 생성   │    │  - saju_contents     │  │
│  │  60간지   │    │  - 표현 변형   │    │  - daily_fortunes    │  │
│  │  기반     │    │  - 품질 검증   │    │  - compatibility     │  │
│  └──────────┘    │  - 안전성 필터 │    │  - content_versions  │  │
│                   └───────────────┘    └──────────────────────┘  │
│                          ▲                                       │
│                          │ Cron Schedule                         │
│                   ┌──────┴──────┐                                │
│                   │  Scheduler   │                                │
│                   │  (Celery     │                                │
│                   │   Beat)      │                                │
│                   └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     ONLINE (서빙 레이어)                          │
│                                                                   │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────────┐  │
│  │  Client   │    │  FastAPI       │    │  Redis Cache         │  │
│  │  (Next.js)│───▶│  Server        │───▶│  (Hot Content)       │  │
│  │           │◀───│               │◀───│                      │  │
│  │           │    │  - 사주 계산   │    │  - 오늘의 운세       │  │
│  │           │    │  - DB 조회     │    │  - 인기 사주 풀이    │  │
│  │           │    │  - 캐시 조회   │    │  - 세션 데이터       │  │
│  │           │    │  - 응답 조합   │    │                      │  │
│  └──────────┘    └───────┬───────┘    └──────────────────────┘  │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │  Content DB  │                                │
│                   │  (PostgreSQL)│                                │
│                   └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 온라인 서빙 플로우 (사용자 요청 처리)

```
사용자: "내 사주 풀이해줘" (생년월일: 1995-03-15 14:00)
    │
    ▼
[1] 사주 계산 엔진 (순수 로직, < 10ms)
    ├─ 년주: 乙亥 (을해)
    ├─ 월주: 己卯 (기묘)
    ├─ 일주: 甲辰 (갑진)
    └─ 시주: 辛未 (신미)
    │
    ▼
[2] DB 조회 (인덱스 기반, < 50ms)
    ├─ saju_contents에서 해당 사주 조합의 풀이 조회
    ├─ 복수 버전 중 랜덤 or 미노출 버전 선택
    └─ Redis 캐시 히트 시 < 5ms
    │
    ▼
[3] 개인화 조합 (서버 로직, < 20ms)
    ├─ 사용자 이름/성별 삽입
    ├─ 현재 대운/세운 정보 결합
    └─ 오늘 날짜 기준 시의성 반영
    │
    ▼
[4] 응답 반환 (총 < 100ms)
    └─ 완성된 사주 풀이 텍스트 전송
```

---

## 5. abcllm 배치 파이프라인 상세

### 5.1 콘텐츠 생성 배치

```python
# batch/content_generator.py (개념 코드)

class SajuContentBatchGenerator:
    """
    사주 조합별 콘텐츠를 abcllm으로 사전 생성하는 배치 프로세서
    """

    def generate_daily_fortune(self, date: date):
        """매일 자정 실행: 60개 일주별 오늘의 운세 생성"""
        for ilju in ALL_60_GANJI:  # 60간지
            prompt = self.build_daily_prompt(ilju, date)
            content = abcllm.generate(prompt)
            content = self.safety_filter(content)
            self.save_to_db("daily_fortune", ilju, date, content)

    def regenerate_base_readings(self, batch_size: int = 100):
        """주간 실행: 기본 사주 풀이 서술 변형"""
        targets = self.get_stale_contents(older_than_days=7)
        for saju_combo in targets[:batch_size]:
            existing = self.get_current_content(saju_combo)
            prompt = self.build_variation_prompt(saju_combo, existing)
            new_content = abcllm.generate(prompt)
            new_content = self.quality_check(new_content, existing)
            self.save_new_version(saju_combo, new_content)

    def generate_topic_readings(self, topic: str):
        """격주 실행: 주제별(연애/재물/직업) 풀이 변형"""
        for saju_combo in self.get_target_combos(topic):
            prompt = self.build_topic_prompt(saju_combo, topic)
            content = abcllm.generate(prompt)
            self.save_to_db(f"{topic}_reading", saju_combo, content)
```

### 5.2 서술 변형 전략

abcllm에게 같은 사주 데이터로 **다른 표현**을 생성하도록 지시:

```
[변형 지시 프롬프트]
아래 사주 풀이를 다른 어조와 표현으로 다시 작성하세요.
핵심 해석(오행 분석, 십성 의미)은 유지하되:

- 변형 A: 따뜻한 상담사 어조 (공감 중심)
- 변형 B: 명쾌한 전문가 어조 (분석 중심)
- 변형 C: 친근한 친구 어조 (쉬운 설명 중심)

[원본 사주 데이터]
{saju_data}

[기존 풀이]
{existing_content}

[요구사항]
- 핵심 해석의 명리학적 근거 동일하게 유지
- 비유, 예시, 문장 구조를 변경
- 길이는 원본의 90~110% 유지
```

### 5.3 배치 스케줄

| 배치 작업 | 스케줄 | 예상 소요 | abcllm 호출 수 |
|-----------|--------|----------|----------------|
| 오늘의 운세 생성 | 매일 00:00 | ~30분 | 60건 |
| 주간 운세 변형 | 매주 월 02:00 | ~2시간 | 420건 |
| 기본 풀이 변형 | 매주 수 02:00 | ~4시간 | 500건 (로테이션) |
| 주제별 풀이 변형 | 격주 금 02:00 | ~6시간 | 1,000건 |
| 궁합 풀이 변형 | 매월 1일 02:00 | ~3시간 | 600건 |
| 품질 검증 재생성 | 매일 06:00 | ~1시간 | 피드백 기반 |

---

## 6. DB 스키마 변경 (v2 추가 테이블)

### saju_contents (사주 풀이 콘텐츠)
```sql
CREATE TABLE saju_contents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type    VARCHAR(30) NOT NULL,      -- 'base_reading', 'love', 'wealth', 'career', 'health'
    saju_key        VARCHAR(20) NOT NULL,      -- '甲子_乙丑_丙寅_丁卯' (4주 조합키)
    ilju_key        VARCHAR(5) NOT NULL,       -- '甲子' (일주 기준 조회용)
    version         INTEGER NOT NULL DEFAULT 1,
    tone            VARCHAR(20) NOT NULL,      -- 'warm', 'expert', 'friendly'
    content_title   TEXT NOT NULL,
    content_body    TEXT NOT NULL,              -- 사주 풀이 본문
    content_summary TEXT,                       -- 요약 (카드 표시용)
    metadata        JSONB DEFAULT '{}',        -- 오행비율, 키워드 등
    is_active       BOOLEAN DEFAULT true,
    quality_score   FLOAT,                     -- 품질 검증 점수
    view_count      INTEGER DEFAULT 0,
    feedback_score  FLOAT,                     -- 사용자 피드백 평균
    generated_at    TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ,               -- 오늘의 운세 등 만료일
    created_at      TIMESTAMPTZ DEFAULT now(),

    UNIQUE(content_type, saju_key, version, tone)
);

-- 핵심 인덱스
CREATE INDEX idx_saju_contents_lookup
    ON saju_contents(content_type, ilju_key, is_active);
CREATE INDEX idx_saju_contents_full_lookup
    ON saju_contents(content_type, saju_key, is_active, version);
CREATE INDEX idx_saju_contents_daily
    ON saju_contents(content_type, expires_at)
    WHERE content_type = 'daily_fortune';
```

### content_generation_logs (배치 생성 로그)
```sql
CREATE TABLE content_generation_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id        UUID NOT NULL,
    content_type    VARCHAR(30) NOT NULL,
    saju_key        VARCHAR(20) NOT NULL,
    llm_provider    VARCHAR(20) NOT NULL,       -- 'abcllm'
    llm_model       VARCHAR(50) NOT NULL,
    prompt_version  VARCHAR(10) NOT NULL,
    token_input     INTEGER,
    token_output    INTEGER,
    cost_usd        DECIMAL(10, 6),
    quality_score   FLOAT,
    safety_passed   BOOLEAN DEFAULT true,
    error_message   TEXT,
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

---

## 7. v1 → v2 변경 영향 분석

| 항목 | v1 (실시간 LLM) | v2 (DB-First + 배치) | 영향 |
|------|----------------|---------------------|------|
| **응답 속도** | 2~10초 (LLM 대기) | < 100ms (DB 조회) | ✅ 대폭 개선 |
| **LLM 비용** | 사용자당 과금 (변동비) | 배치 고정비 (예측 가능) | ✅ 비용 절감 80%+ |
| **콘텐츠 품질** | 실시간 생성 (불안정) | 사전 검증 완료 (안정적) | ✅ 품질 보장 |
| **개인화** | 높음 (실시간 맥락) | 중간 (조합 기반 + 이름 삽입) | ⚠️ 트레이드오프 |
| **대화형 상담** | 가능 (SSE 스트리밍) | 제한적 (FAQ 기반 or 프리미엄) | ⚠️ 별도 설계 필요 |
| **콘텐츠 다양성** | 매번 다름 | 버전 로테이션 + 주기적 변형 | ✅ abcllm으로 해결 |
| **확장성** | LLM 동시 호출 제한 | DB 스케일 무한 | ✅ 대폭 개선 |
| **장애 영향** | LLM 장애 = 서비스 중단 | LLM 장애 = 배치 지연뿐 | ✅ 안정성 향상 |

### 7.1 대화형 AI 상담 (프리미엄 전용)

대화형 상담은 프리미엄 플랜에서만 실시간 LLM 호출로 제공:

```
무료/베이직: DB 즉시 송출 (사전 구축 콘텐츠)
프리미엄:    DB 즉시 송출 + 실시간 AI 대화 상담 (abcllm 실시간 호출)
```

---

## 8. MVP 단계별 콘텐츠 구축 계획

### Phase 1 (MVP Week 1-2): 일주 기준 60개
- 60간지 일주별 기본 풀이 × 3 버전 = **180건**
- 60간지 일주별 오늘의 운세 템플릿 × 5 = **300건**
- 궁합 60×60 = **3,600건**
- **총 ~4,080건** (abcllm 배치 1회로 생성 가능)

### Phase 2 (MVP Week 3-4): 월주+일주 720개
- 12월주 × 60일주 = 720 조합
- 주제별(연애/재물/직업) 풀이 추가
- **총 ~15,000건**

### Phase 3 (v1.0): 년주+월주+일주 확장
- 점진적 확장, 사용자 요청이 많은 조합부터 우선 생성
- 캐시 미스 시 실시간 생성 후 DB 저장 (Lazy Generation)

---

## 9. 기술 스택 변경사항

| 항목 | v1 | v2 | 변경 이유 |
|------|-----|-----|----------|
| LLM 호출 방식 | 실시간 SSE 스트리밍 | 배치 생성 + DB 저장 | 속도/비용 최적화 |
| LLM 프로바이더 | Claude API + GPT-4o | abcllm (배치) | 사용자 지정 |
| RAG/pgvector | 필수 (실시간 검색) | 배치 시에만 사용 | 온라인 서빙 단순화 |
| Celery | 일일 운세 배치만 | 전체 콘텐츠 배치 관리 | 역할 확대 |
| Redis | 캐시 + Rate Limit | 핫 콘텐츠 캐시 (핵심) | 역할 강화 |
| SSE 스트리밍 | 필수 (모든 상담) | 프리미엄 대화 상담만 | 범위 축소 |
| LangChain | 필수 | 배치 파이프라인에서만 | 온라인 의존성 제거 |
