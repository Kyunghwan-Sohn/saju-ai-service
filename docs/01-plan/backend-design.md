# Saju AI Service - Backend Design

> **Version:** 1.0
> **Date:** 2026-03-25
> **Based on:** [PRD v1.0](../00-pm/saju-ai-service.prd.md), [Architecture v1.0](saju-ai-architecture.md), [DB Schema v1.0](../02-design/db-schema.md)

---

## Table of Contents

1. [사주 계산 엔진 상세 설계](#1-사주-계산-엔진-상세-설계)
2. [LLM 프롬프트 설계](#2-llm-프롬프트-설계)
3. [사용자 데이터 관리](#3-사용자-데이터-관리)
4. [결제/구독 시스템](#4-결제구독-시스템)
5. [API 엔드포인트 전체 목록](#5-api-엔드포인트-전체-목록)

---

## 1. 사주 계산 엔진 상세 설계

### 1.1 천간(天干) / 지지(地支) 매핑

#### 천간 10개

| 번호 | 한자 | 한글 | 오행 | 음양 |
|------|------|------|------|------|
| 0 | 甲 | 갑 | wood | 양(陽) |
| 1 | 乙 | 을 | wood | 음(陰) |
| 2 | 丙 | 병 | fire | 양(陽) |
| 3 | 丁 | 정 | fire | 음(陰) |
| 4 | 戊 | 무 | earth | 양(陽) |
| 5 | 己 | 기 | earth | 음(陰) |
| 6 | 庚 | 경 | metal | 양(陽) |
| 7 | 辛 | 신 | metal | 음(陰) |
| 8 | 壬 | 임 | water | 양(陽) |
| 9 | 癸 | 계 | water | 음(陰) |

```python
# app/common/constants.py

HEAVENLY_STEMS = [
    {"hanja": "甲", "kr": "갑", "element": "wood",  "polarity": "yang", "index": 0},
    {"hanja": "乙", "kr": "을", "element": "wood",  "polarity": "yin",  "index": 1},
    {"hanja": "丙", "kr": "병", "element": "fire",  "polarity": "yang", "index": 2},
    {"hanja": "丁", "kr": "정", "element": "fire",  "polarity": "yin",  "index": 3},
    {"hanja": "戊", "kr": "무", "element": "earth", "polarity": "yang", "index": 4},
    {"hanja": "己", "kr": "기", "element": "earth", "polarity": "yin",  "index": 5},
    {"hanja": "庚", "kr": "경", "element": "metal", "polarity": "yang", "index": 6},
    {"hanja": "辛", "kr": "신", "element": "metal", "polarity": "yin",  "index": 7},
    {"hanja": "壬", "kr": "임", "element": "water", "polarity": "yang", "index": 8},
    {"hanja": "癸", "kr": "계", "element": "water", "polarity": "yin",  "index": 9},
]

# 인덱스로 빠른 접근
STEM_BY_INDEX = {s["index"]: s for s in HEAVENLY_STEMS}
```

#### 지지 12개

| 번호 | 한자 | 한글 | 오행 | 음양 | 시간대 | 달(월지 기준) | 방위 |
|------|------|------|------|------|--------|-------------|------|
| 0 | 子 | 자 | water | 양 | 23:00~01:00 | 11월 | 북 |
| 1 | 丑 | 축 | earth | 음 | 01:00~03:00 | 12월 | 북동 |
| 2 | 寅 | 인 | wood | 양 | 03:00~05:00 | 1월 | 동북 |
| 3 | 卯 | 묘 | wood | 음 | 05:00~07:00 | 2월 | 동 |
| 4 | 辰 | 진 | earth | 양 | 07:00~09:00 | 3월 | 동남 |
| 5 | 巳 | 사 | fire | 음 | 09:00~11:00 | 4월 | 남동 |
| 6 | 午 | 오 | fire | 양 | 11:00~13:00 | 5월 | 남 |
| 7 | 未 | 미 | earth | 음 | 13:00~15:00 | 6월 | 남서 |
| 8 | 申 | 신 | metal | 양 | 15:00~17:00 | 7월 | 서남 |
| 9 | 酉 | 유 | metal | 음 | 17:00~19:00 | 8월 | 서 |
| 10 | 戌 | 술 | earth | 양 | 19:00~21:00 | 9월 | 서북 |
| 11 | 亥 | 해 | water | 음 | 21:00~23:00 | 10월 | 북서 |

```python
EARTHLY_BRANCHES = [
    {"hanja": "子", "kr": "자", "element": "water", "polarity": "yang", "index": 0,
     "hour_start": 23, "hour_end": 1,   "month": 11,
     "hidden_stems": [{"stem": 9, "ratio": 100}]},  # 癸
    {"hanja": "丑", "kr": "축", "element": "earth", "polarity": "yin",  "index": 1,
     "hour_start": 1,  "hour_end": 3,   "month": 12,
     "hidden_stems": [{"stem": 5, "ratio": 60}, {"stem": 9, "ratio": 20}, {"stem": 7, "ratio": 20}]},  # 己癸辛
    {"hanja": "寅", "kr": "인", "element": "wood",  "polarity": "yang", "index": 2,
     "hour_start": 3,  "hour_end": 5,   "month": 1,
     "hidden_stems": [{"stem": 0, "ratio": 60}, {"stem": 2, "ratio": 20}, {"stem": 4, "ratio": 20}]},  # 甲丙戊
    {"hanja": "卯", "kr": "묘", "element": "wood",  "polarity": "yin",  "index": 3,
     "hour_start": 5,  "hour_end": 7,   "month": 2,
     "hidden_stems": [{"stem": 1, "ratio": 100}]},  # 乙
    {"hanja": "辰", "kr": "진", "element": "earth", "polarity": "yang", "index": 4,
     "hour_start": 7,  "hour_end": 9,   "month": 3,
     "hidden_stems": [{"stem": 4, "ratio": 60}, {"stem": 1, "ratio": 20}, {"stem": 9, "ratio": 20}]},  # 戊乙癸
    {"hanja": "巳", "kr": "사", "element": "fire",  "polarity": "yin",  "index": 5,
     "hour_start": 9,  "hour_end": 11,  "month": 4,
     "hidden_stems": [{"stem": 2, "ratio": 60}, {"stem": 4, "ratio": 20}, {"stem": 6, "ratio": 20}]},  # 丙戊庚
    {"hanja": "午", "kr": "오", "element": "fire",  "polarity": "yang", "index": 6,
     "hour_start": 11, "hour_end": 13,  "month": 5,
     "hidden_stems": [{"stem": 2, "ratio": 70}, {"stem": 3, "ratio": 30}]},  # 丙丁
    {"hanja": "未", "kr": "미", "element": "earth", "polarity": "yin",  "index": 7,
     "hour_start": 13, "hour_end": 15,  "month": 6,
     "hidden_stems": [{"stem": 5, "ratio": 60}, {"stem": 3, "ratio": 20}, {"stem": 1, "ratio": 20}]},  # 己丁乙
    {"hanja": "申", "kr": "신", "element": "metal", "polarity": "yang", "index": 8,
     "hour_start": 15, "hour_end": 17,  "month": 7,
     "hidden_stems": [{"stem": 6, "ratio": 60}, {"stem": 8, "ratio": 20}, {"stem": 4, "ratio": 20}]},  # 庚壬戊
    {"hanja": "酉", "kr": "유", "element": "metal", "polarity": "yin",  "index": 9,
     "hour_start": 17, "hour_end": 19,  "month": 8,
     "hidden_stems": [{"stem": 7, "ratio": 100}]},  # 辛
    {"hanja": "戌", "kr": "술", "element": "earth", "polarity": "yang", "index": 10,
     "hour_start": 19, "hour_end": 21,  "month": 9,
     "hidden_stems": [{"stem": 4, "ratio": 60}, {"stem": 7, "ratio": 20}, {"stem": 3, "ratio": 20}]},  # 戊辛丁
    {"hanja": "亥", "kr": "해", "element": "water", "polarity": "yin",  "index": 11,
     "hour_start": 21, "hour_end": 23,  "month": 10,
     "hidden_stems": [{"stem": 8, "ratio": 70}, {"stem": 0, "ratio": 30}]},  # 壬甲
]

BRANCH_BY_INDEX = {b["index"]: b for b in EARTHLY_BRANCHES}
```

---

### 1.2 양력→음력 변환 및 절기 기반 월주 결정

#### 만세력 데이터 구조

```
data/manseryeok/
├── solar_terms.json        # 24절기 데이터 (1900~2100, 분 단위 정밀도)
├── daily_pillars.json      # 일진(일간/일지) 순서표 (기준일 기반 오프셋)
├── lunar_calendar.json     # 음양력 변환 테이블 (1900~2100)
└── leap_months.json        # 윤달 연도별 데이터
```

```python
# app/modules/saju_engine/manseryeok.py

import json
from datetime import date, datetime
from pathlib import Path

class Manseryeok:
    """만세력 데이터 로더 및 조회 클래스"""

    DATA_DIR = Path("data/manseryeok")

    def __init__(self):
        self._solar_terms = self._load_json("solar_terms.json")
        self._daily_pillars = self._load_json("daily_pillars.json")
        self._lunar_calendar = self._load_json("lunar_calendar.json")
        self._leap_months = self._load_json("leap_months.json")

    def to_solar(self, lunar_date: date, is_leap: bool = False) -> date:
        """음력 -> 양력 변환"""
        key = f"{lunar_date.year}-{lunar_date.month:02d}-{is_leap}"
        month_data = self._lunar_calendar[key]
        # 음력 일수 오프셋 적용
        solar_start = date.fromisoformat(month_data["solar_start"])
        return solar_start + timedelta(days=lunar_date.day - 1)

    def get_solar_term_for_month(self, solar_date: date) -> dict:
        """
        특정 날짜가 속하는 절기(節)와 중기(中氣) 반환
        월주 산출의 핵심: 24절기 중 절(節, 홀수)만 기준점
        절기 목록: 입춘, 경칩, 청명, 입하, 망종, 소서, 입추, 백로, 한로, 입동, 대설, 소한
        """
        year = solar_date.year
        terms = self._solar_terms[str(year)]
        current_term = None
        for term in sorted(terms, key=lambda t: t["datetime"], reverse=True):
            term_dt = datetime.fromisoformat(term["datetime"])
            if term_dt.date() <= solar_date and term["type"] == "절":
                current_term = term
                break
        return current_term

    def get_day_pillar(self, solar_date: date) -> tuple[int, int]:
        """
        일주(일간, 일지) 반환
        기준일(1900-01-01 = 甲子日, index 0)로부터 경과일수로 계산
        """
        BASE_DATE = date(1900, 1, 1)  # 甲子日 기준
        offset = (solar_date - BASE_DATE).days
        stem_index = offset % 10
        branch_index = offset % 12
        return stem_index, branch_index
```

#### 절기 기반 월주(月柱) 결정 로직

```python
# 절기-월간(月干) 매핑 테이블
# 절기 순서: 소한(子月), 입춘(寅月), 경칩(卯月), 청명(辰月),
#            입하(巳月), 망종(午月), 소서(未月), 입추(申月),
#            백로(酉月), 한로(戌月), 입동(亥月), 대설(子月)

SOLAR_TERM_TO_MONTH_BRANCH = {
    "소한": 11,  # 子 (11월지 -> 지지 인덱스 0)
    "입춘": 2,   # 寅 (지지 인덱스 2)
    "경칩": 3,   # 卯 (지지 인덱스 3)
    "청명": 4,   # 辰 (지지 인덱스 4)
    "입하": 5,   # 巳 (지지 인덱스 5)
    "망종": 6,   # 午 (지지 인덱스 6)
    "소서": 7,   # 未 (지지 인덱스 7)
    "입추": 8,   # 申 (지지 인덱스 8)
    "백로": 9,   # 酉 (지지 인덱스 9)
    "한로": 10,  # 戌 (지지 인덱스 10)
    "입동": 11,  # 亥 (지지 인덱스 11)
    "대설": 0,   # 子 (지지 인덱스 0)
}

# 연간(年干)에 따른 월간(月干) 기준: 오호둔년법(五虎遁年法)
# 갑(0)년/기(5)년: 인월(寅月)이 丙(2)으로 시작
# 을(1)년/경(6)년: 인월(寅月)이 戊(4)으로 시작
# 병(2)년/신(7)년: 인월(寅月)이 庚(6)으로 시작
# 정(3)년/임(8)년: 인월(寅月)이 壬(8)으로 시작
# 무(4)년/계(9)년: 인월(寅月)이 甲(0)으로 시작

MONTH_STEM_BASE = {0: 2, 5: 2,   # 갑기년 -> 병인월
                   1: 4, 6: 4,   # 을경년 -> 무인월
                   2: 6, 7: 6,   # 병신년 -> 경인월
                   3: 8, 8: 8,   # 정임년 -> 임인월
                   4: 0, 9: 0}   # 무계년 -> 갑인월

def calculate_month_pillar(year_stem_index: int, month_branch_index: int) -> tuple[int, int]:
    """
    월주 산출
    - year_stem_index: 연간 인덱스 (0=甲 ~ 9=癸)
    - month_branch_index: 절기로 결정된 월지 인덱스 (0=子 ~ 11=亥)
    반환: (월간 인덱스, 월지 인덱스)
    """
    # 인월(寅月, 인덱스 2)을 기준으로 월간 계산
    base_stem = MONTH_STEM_BASE[year_stem_index]
    # 인(2)부터 시작하는 지지 순서에서 현재 월지의 오프셋
    branch_offset = (month_branch_index - 2) % 12
    month_stem_index = (base_stem + branch_offset) % 10
    return month_stem_index, month_branch_index
```

---

### 1.3 사주팔자 도출 알고리즘

#### 전체 파이프라인

```python
# app/modules/saju_engine/calculator.py

from datetime import date, time
from dataclasses import dataclass
from typing import Optional

@dataclass
class Pillar:
    stem_index: int      # 천간 인덱스 (0~9)
    branch_index: int    # 지지 인덱스 (0~11)
    stem_hanja: str
    branch_hanja: str
    stem_kr: str
    branch_kr: str
    stem_element: str
    branch_element: str

@dataclass
class SajuResult:
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Optional[Pillar]
    five_elements: dict
    ten_stars: dict
    twelve_stages: dict
    special_stars: list
    geokguk: dict
    major_luck_cycles: list

class SajuCalculator:
    def __init__(self, manseryeok: Manseryeok):
        self.manseryeok = manseryeok

    def calculate(
        self,
        birth_date: date,
        birth_time: Optional[time],
        is_lunar: bool,
        is_leap_month: bool,
        gender: str,  # "male" | "female"
    ) -> SajuResult:
        # Step 1: 음력이면 양력으로 변환
        solar_date = (
            self.manseryeok.to_solar(birth_date, is_leap_month)
            if is_lunar else birth_date
        )

        # Step 2: 연주(年柱) 산출 - 입춘(立春) 기준
        year_pillar = self._calc_year_pillar(solar_date)

        # Step 3: 월주(月柱) 산출 - 절기(節氣) 기준
        month_pillar = self._calc_month_pillar(solar_date, year_pillar.stem_index)

        # Step 4: 일주(日柱) 산출 - 만세력 직접 조회
        day_pillar = self._calc_day_pillar(solar_date, birth_time)

        # Step 5: 시주(時柱) 산출 - 일간 기준 오호둔시법
        hour_pillar = (
            self._calc_hour_pillar(day_pillar.stem_index, birth_time)
            if birth_time is not None else None
        )

        pillars = [year_pillar, month_pillar, day_pillar]
        if hour_pillar:
            pillars.append(hour_pillar)

        # Step 6: 오행 분석
        five_elements = self._analyze_five_elements(pillars)

        # Step 7: 십성 계산
        ten_stars = self._calc_ten_stars(day_pillar.stem_index, pillars)

        # Step 8: 12운성 계산
        twelve_stages = self._calc_twelve_stages(day_pillar.stem_index, pillars)

        # Step 9: 신살 판별
        special_stars = self._find_special_stars(pillars, day_pillar, year_pillar)

        # Step 10: 격국 판정
        geokguk = self._determine_geokguk(
            month_pillar, day_pillar, pillars, ten_stars
        )

        # Step 11: 대운 계산
        major_luck_cycles = self._calc_major_luck(
            year_pillar, month_pillar, gender, solar_date
        )

        return SajuResult(
            year_pillar=year_pillar,
            month_pillar=month_pillar,
            day_pillar=day_pillar,
            hour_pillar=hour_pillar,
            five_elements=five_elements,
            ten_stars=ten_stars,
            twelve_stages=twelve_stages,
            special_stars=special_stars,
            geokguk=geokguk,
            major_luck_cycles=major_luck_cycles,
        )
```

#### 연주(年柱) 산출 - 입춘 기준

```python
def _calc_year_pillar(self, solar_date: date) -> Pillar:
    """
    연주 산출 규칙:
    - 입춘(立春) 이전 출생: 전년도 연주
    - 입춘(立春) 이후 출생: 당년 연주
    - 입춘 시각이 정오 이전/이후도 분 단위로 정확히 계산
    60갑자 순환: 1984년 = 甲子년 기준
    """
    year = solar_date.year
    ipchun = self.manseryeok.get_solar_term(year, "입춘")
    if solar_date < ipchun.date():
        year -= 1  # 입춘 이전 -> 전년도

    # 1984년 = 甲子(갑자) 기준 (stem=0, branch=0)
    BASE_YEAR = 1984
    offset = year - BASE_YEAR
    stem_index = offset % 10
    branch_index = offset % 12

    return self._make_pillar(stem_index, branch_index)
```

#### 일주(日柱) 산출 - 자시(子時) 처리

```python
def _calc_day_pillar(self, solar_date: date, birth_time: Optional[time]) -> Pillar:
    """
    일주 산출 규칙:
    - 야자시(夜子時, 23:00~24:00): 날짜 기준 당일 일주 사용, 시주는 子시
    - 조자시(早子時, 00:00~01:00): 날짜 기준 당일 일주 사용, 시주는 子시
    - 일부 학파는 23:00 이후를 다음날로 계산 (설정 옵션 제공)
    """
    effective_date = solar_date
    # 야자시 처리: 기본값은 당일 기준 (통상적 방식)
    stem_idx, branch_idx = self.manseryeok.get_day_pillar(effective_date)
    return self._make_pillar(stem_idx, branch_idx)
```

#### 시주(時柱) 산출 - 오자둔일법(五子遁日法)

```python
# 갑(0)일/기(5)일: 자시(子時)가 甲(0)子
# 을(1)일/경(6)일: 자시(子時)가 丙(2)子
# 병(2)일/신(7)일: 자시(子時)가 戊(4)子
# 정(3)일/임(8)일: 자시(子時)가 庚(6)子
# 무(4)일/계(9)일: 자시(子時)가 壬(8)子

HOUR_STEM_BASE = {0: 0, 5: 0,   # 갑기일 -> 갑자시
                  1: 2, 6: 2,   # 을경일 -> 병자시
                  2: 4, 7: 4,   # 병신일 -> 무자시
                  3: 6, 8: 6,   # 정임일 -> 경자시
                  4: 8, 9: 8}   # 무계일 -> 임자시

def _calc_hour_pillar(self, day_stem_index: int, birth_time: time) -> Pillar:
    """시주 산출: 일간에 따른 시간 천간 결정"""
    base_stem = HOUR_STEM_BASE[day_stem_index]
    hour_branch_index = self._time_to_branch(birth_time)
    hour_stem_index = (base_stem + hour_branch_index) % 10
    return self._make_pillar(hour_stem_index, hour_branch_index)

def _time_to_branch(self, t: time) -> int:
    """시각을 지지 인덱스로 변환"""
    h = t.hour
    if h == 23 or h == 0:   return 0   # 子 (23:00~01:00)
    elif 1  <= h < 3:        return 1   # 丑
    elif 3  <= h < 5:        return 2   # 寅
    elif 5  <= h < 7:        return 3   # 卯
    elif 7  <= h < 9:        return 4   # 辰
    elif 9  <= h < 11:       return 5   # 巳
    elif 11 <= h < 13:       return 6   # 午
    elif 13 <= h < 15:       return 7   # 未
    elif 15 <= h < 17:       return 8   # 申
    elif 17 <= h < 19:       return 9   # 酉
    elif 19 <= h < 21:       return 10  # 戌
    else:                    return 11  # 亥 (21:00~23:00)
```

---

### 1.4 오행(五行) 분석 로직

```python
def _analyze_five_elements(self, pillars: list[Pillar]) -> dict:
    """
    오행 분포 분석
    - 천간(天干): 각 1점
    - 지지(地支): 본기(本氣) 1점, 지장간(支藏干) 가중치 반영
    """
    scores = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}

    for pillar in pillars:
        # 천간 오행
        stem = STEM_BY_INDEX[pillar.stem_index]
        scores[stem["element"]] += 1.0

        # 지지 본기
        branch = BRANCH_BY_INDEX[pillar.branch_index]
        scores[branch["element"]] += 1.0

        # 지장간 가중치 (비율에 따라 부가 점수)
        for hidden in branch["hidden_stems"]:
            hidden_stem = STEM_BY_INDEX[hidden["stem"]]
            scores[hidden_stem["element"]] += hidden["ratio"] / 100 * 0.5

    dominant = max(scores, key=scores.get)
    lacking = min(scores, key=scores.get)

    # 상생(相生) 관계: 목->화->토->금->수->목
    GENERATION = {"wood": "fire", "fire": "earth",
                  "earth": "metal", "metal": "water", "water": "wood"}
    # 상극(相剋) 관계: 목->토->수->화->금->목
    RESTRICTION = {"wood": "earth", "earth": "water",
                   "water": "fire", "fire": "metal", "metal": "wood"}

    return {
        "wood":    round(scores["wood"], 2),
        "fire":    round(scores["fire"], 2),
        "earth":   round(scores["earth"], 2),
        "metal":   round(scores["metal"], 2),
        "water":   round(scores["water"], 2),
        "dominant": dominant,
        "lacking":  lacking,
        "generation_cycle": GENERATION,
        "restriction_cycle": RESTRICTION,
    }
```

---

### 1.5 십성(十星) 계산

십성은 일간(日干)을 기준으로 다른 천간/지지의 관계를 표현한다.

```python
# 십성 결정 매트릭스: [일간 오행][상대 오행] -> 십성 이름 (음양 구분)
# 같은 오행, 같은 음양 -> 비견(比肩)
# 같은 오행, 다른 음양 -> 겁재(劫財)
# 일간이 생하는 오행, 같은 음양 -> 식신(食神)
# 일간이 생하는 오행, 다른 음양 -> 상관(傷官)
# 일간이 극하는 오행, 같은 음양 -> 편재(偏財)
# 일간이 극하는 오행, 다른 음양 -> 정재(正財)
# 일간을 극하는 오행, 같은 음양 -> 편관(偏官)
# 일간을 극하는 오행, 다른 음양 -> 정관(正官)
# 일간을 생하는 오행, 같은 음양 -> 편인(偏印)
# 일간을 생하는 오행, 다른 음양 -> 정인(正印)

GENERATION_ORDER = ["wood", "fire", "earth", "metal", "water"]

def _get_ten_star(self, day_stem_idx: int, target_stem_idx: int) -> str:
    """일간과 대상 천간의 십성 관계 계산"""
    day = STEM_BY_INDEX[day_stem_idx]
    target = STEM_BY_INDEX[target_stem_idx]

    same_polarity = (day["polarity"] == target["polarity"])
    day_el = GENERATION_ORDER.index(day["element"])
    tgt_el = GENERATION_ORDER.index(target["element"])

    if day["element"] == target["element"]:
        return "비견" if same_polarity else "겁재"

    # 일간이 생하는 오행 (식상)
    if GENERATION_ORDER[(day_el + 1) % 5] == target["element"]:
        return "식신" if same_polarity else "상관"

    # 일간이 극하는 오행 (재성)
    if GENERATION_ORDER[(day_el + 2) % 5] == target["element"]:
        return "편재" if same_polarity else "정재"

    # 일간을 극하는 오행 (관성)
    if GENERATION_ORDER[(day_el + 3) % 5] == target["element"]:
        return "편관" if same_polarity else "정관"

    # 일간을 생하는 오행 (인성)
    if GENERATION_ORDER[(day_el + 4) % 5] == target["element"]:
        return "편인" if same_polarity else "정인"

def _calc_ten_stars(self, day_stem_idx: int, pillars: list[Pillar]) -> dict:
    """전체 사주의 십성 배치 계산"""
    result = {}
    pillar_names = ["year", "month", "day", "hour"]

    for i, pillar in enumerate(pillars):
        name = pillar_names[i]
        # 천간 십성
        if name != "day":  # 일간은 자기 자신이므로 제외
            result[f"{name}_stem"] = self._get_ten_star(day_stem_idx, pillar.stem_index)

        # 지지 본기(本氣) 기반 십성
        branch = BRANCH_BY_INDEX[pillar.branch_index]
        main_hidden = branch["hidden_stems"][0]
        result[f"{name}_branch"] = self._get_ten_star(day_stem_idx, main_hidden["stem"])

    # 십성 유형별 집계
    summary = {"비겁": 0, "식상": 0, "재성": 0, "관성": 0, "인성": 0}
    star_group = {
        "비견": "비겁", "겁재": "비겁",
        "식신": "식상", "상관": "식상",
        "편재": "재성", "정재": "재성",
        "편관": "관성", "정관": "관성",
        "편인": "인성", "정인": "인성",
    }
    for v in result.values():
        summary[star_group[v]] += 1

    result["summary"] = summary
    return result
```

---

### 1.6 12운성(十二運星) 계산

12운성은 일간(日干)의 오행이 각 지지(地支)에서 어떤 단계(생장소멸)에 있는지를 나타낸다.

```python
# 양간(陽干: 甲丙戊庚壬)은 순행, 음간(陰干: 乙丁己辛癸)은 역행
# 시작 지지: 양간의 장생(長生) 기준
# 甲: 亥장생, 丙/戊: 寅장생, 庚: 巳장생, 壬: 申장생

TWELVE_STAGES = ["장생", "목욕", "관대", "건록", "제왕", "쇠", "병", "사", "묘", "절", "태", "양"]

YANG_CHANGENG_START = {
    "wood":  11,  # 亥(해, 인덱스 11)에서 장생
    "fire":   2,  # 寅(인, 인덱스 2)에서 장생
    "earth":  2,  # 寅(인, 인덱스 2)에서 장생 (무토 기준)
    "metal":  5,  # 巳(사, 인덱스 5)에서 장생
    "water":  8,  # 申(신, 인덱스 8)에서 장생
}

def _calc_twelve_stage(self, day_stem_idx: int, branch_idx: int) -> str:
    """일간과 지지의 12운성 계산"""
    stem = STEM_BY_INDEX[day_stem_idx]
    is_yang = stem["polarity"] == "yang"
    start = YANG_CHANGENG_START[stem["element"]]

    if is_yang:
        offset = (branch_idx - start) % 12
    else:
        # 음간은 양간의 장생 위치에서 제왕부터 역행
        offset = (start - branch_idx) % 12

    return TWELVE_STAGES[offset]

def _calc_twelve_stages(self, day_stem_idx: int, pillars: list[Pillar]) -> dict:
    names = ["year", "month", "day", "hour"]
    return {
        names[i]: self._calc_twelve_stage(day_stem_idx, p.branch_index)
        for i, p in enumerate(pillars)
    }
```

---

### 1.7 신살(神殺) 판별

주요 신살 30종을 구현한다. 신살은 연주(年柱) 또는 일주(日柱)를 기준으로 특정 간지 조합을 탐지한다.

```python
# app/modules/saju_engine/special_stars.py

class SpecialStarsDetector:

    # 역마살(驛馬殺): 연지/일지가 寅申巳亥일 때 특정 지지
    YEOKMA_MAP = {2: 8, 8: 2, 5: 11, 11: 5}  # 寅->申, 申->寅, 巳->亥, 亥->巳

    # 도화살(桃花殺): 연지/일지 기준
    DOHUA_MAP = {
        0: 9, 4: 9, 8: 9,    # 子辰申년: 酉가 도화
        3: 6, 7: 6, 11: 6,   # 卯未亥년: 午가 도화
        2: 3, 6: 3, 10: 3,   # 寅午戌년: 卯가 도화
        1: 0, 5: 0, 9: 0,    # 丑巳酉년: 子가 도화
    }

    # 천을귀인(天乙貴人): 일간 기준 해당 지지
    CHEONUL_MAP = {
        0: [1, 11],   # 甲: 丑亥
        1: [0, 11],   # 乙: 子亥
        2: [8, 6],    # 丙: 申亥
        3: [8, 6],    # 丁: 申酉
        4: [1, 11],   # 戊: 丑未
        5: [0, 7],    # 己: 子申
        6: [1, 11],   # 庚: 丑未
        7: [0, 2],    # 辛: 子寅
        8: [5, 3],    # 壬: 巳卯
        9: [5, 3],    # 癸: 巳卯
    }

    # 문창귀인(文昌貴人): 일간 기준
    MUNCHANG_MAP = {0: 5, 1: 6, 2: 8, 3: 9, 4: 8,
                    5: 3, 6: 11, 7: 0, 8: 2, 9: 3}

    # 화개살(華蓋殺): 연지/일지 기준
    HWAGAE_MAP = {0: 4, 4: 4, 8: 4,   # 子辰申: 辰
                  3: 7, 7: 7, 11: 7,  # 卯未亥: 未
                  2: 10, 6: 10, 10: 10, # 寅午戌: 戌
                  1: 1, 5: 1, 9: 1}   # 丑巳酉: 丑

    def detect(self, pillars: list[Pillar]) -> list[dict]:
        """모든 신살 탐지 후 목록 반환"""
        results = []
        year_branch = pillars[0].branch_index
        day_branch  = pillars[2].branch_index
        day_stem    = pillars[2].stem_index
        all_branches = [p.branch_index for p in pillars]

        # 역마살
        if year_branch in self.YEOKMA_MAP:
            target = self.YEOKMA_MAP[year_branch]
            if target in all_branches:
                results.append({"name": "역마살", "hanja": "驛馬殺",
                                 "pillar": self._which_pillar(all_branches, target),
                                 "description": "이동과 변화, 해외 인연이 강한 기운"})

        # 도화살
        if year_branch in self.DOHUA_MAP:
            target = self.DOHUA_MAP[year_branch]
            if target in all_branches:
                results.append({"name": "도화살", "hanja": "桃花殺",
                                 "pillar": self._which_pillar(all_branches, target),
                                 "description": "매력과 인기, 이성 인연이 강한 기운"})

        # 천을귀인
        cheonul_branches = self.CHEONUL_MAP.get(day_stem, [])
        for cb in cheonul_branches:
            if cb in all_branches:
                results.append({"name": "천을귀인", "hanja": "天乙貴人",
                                 "pillar": self._which_pillar(all_branches, cb),
                                 "description": "어려울 때 귀인의 도움을 받는 기운"})

        # 문창귀인
        munchang = self.MUNCHANG_MAP.get(day_stem)
        if munchang in all_branches:
            results.append({"name": "문창귀인", "hanja": "文昌貴人",
                             "pillar": self._which_pillar(all_branches, munchang),
                             "description": "학문과 문서, 총명함을 나타내는 기운"})

        # 화개살
        if year_branch in self.HWAGAE_MAP:
            target = self.HWAGAE_MAP[year_branch]
            if target in all_branches:
                results.append({"name": "화개살", "hanja": "華蓋殺",
                                 "pillar": self._which_pillar(all_branches, target),
                                 "description": "예술, 종교, 고독의 기운. 창의성이 뛰어남"})

        # ... 나머지 25종 신살 동일 패턴으로 구현
        # (삼재, 공망, 백호대살, 귀문관살, 원진살, 양인살, 겁살, 재살, 천살, 지살,
        #  년살, 월살, 망신살, 장성살, 반안살, 천마, 홍염살, 음양차착살, 격각살 등)

        return results
```

---

### 1.8 격국(格局) 판정

```python
def _determine_geokguk(
    self,
    month_pillar: Pillar,
    day_pillar: Pillar,
    all_pillars: list[Pillar],
    ten_stars: dict,
) -> dict:
    """
    격국 판정 순서:
    1. 월지(月支)의 장간(藏干) 중 정기(正氣, 본기) 확인
    2. 정기의 십성 도출
    3. 해당 십성이 천간에 투출(透出)되었는지 확인
    4. 통근(通根) 여부 확인
    5. 정격 8격 또는 외격 판정

    정격 8격:
    - 정관격(正官格), 편관격(偏官格), 정재격(正財格), 편재격(偏財格),
      정인격(正印格), 편인격(偏印格), 식신격(食神格), 상관격(傷官格)

    외격(특별격):
    - 종격(從格): 종살격, 종재격, 종아격, 종강격, 종왕격
    - 화격(化格): 갑기합화토격 등
    - 전왕격(專旺格): 곡직격, 염상격, 가색격, 종혁격, 윤하격
    """
    month_branch = BRANCH_BY_INDEX[month_pillar.branch_index]
    # 월지 정기 (hidden_stems[0])
    main_hidden_stem_idx = month_branch["hidden_stems"][0]["stem"]
    main_ten_star = self._get_ten_star(day_pillar.stem_index, main_hidden_stem_idx)

    # 천간 투출 확인 (월지 정기와 같은 십성이 천간에 있는지)
    all_stems = [p.stem_index for p in all_pillars]
    is_projected = any(
        self._get_ten_star(day_pillar.stem_index, s) == main_ten_star
        for s in all_stems if s != day_pillar.stem_index
    )

    geokguk_name = f"{main_ten_star}격"

    # 외격 체크 (오행 편중도 기반)
    outer_format = self._check_outer_format(all_pillars, day_pillar, ten_stars)
    if outer_format:
        return outer_format

    return {
        "type": geokguk_name,
        "hanja": self._to_hanja(geokguk_name),
        "category": "정격",
        "is_projected": is_projected,
        "description": f"월지 정기의 {main_ten_star}이 격을 이룸",
    }
```

---

### 1.9 대운/세운 계산

```python
def _calc_major_luck(
    self,
    year_pillar: Pillar,
    month_pillar: Pillar,
    gender: str,
    birth_date: date,
) -> list[dict]:
    """
    대운(大運) 계산
    - 양남음녀(陽男陰女): 순행(順行) - 생월 이후 다음 절기까지 일수
    - 음남양녀(陰男陽女): 역행(逆行) - 생월 이전 절기까지 일수
    - 3일 = 1년 (절입일수 / 3 = 대운 시작 나이)
    - 이후 10년 단위로 60갑자 순행/역행
    """
    year_stem = STEM_BY_INDEX[year_pillar.stem_index]
    is_yang_year = year_stem["polarity"] == "yang"
    is_male = gender == "male"

    # 순행 조건: 양년 남자 또는 음년 여자
    is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)

    # 대운 시작 나이 계산 (절기까지 일수 / 3)
    if is_forward:
        next_term_date = self.manseryeok.get_next_solar_term_date(birth_date)
        days_to_term = (next_term_date - birth_date).days
    else:
        prev_term_date = self.manseryeok.get_prev_solar_term_date(birth_date)
        days_to_term = (birth_date - prev_term_date).days

    start_age = days_to_term // 3
    remainder_months = (days_to_term % 3) * 4  # 나머지 일 -> 개월 근사

    # 대운 간지: 월주부터 순행/역행으로 10년씩
    cycles = []
    current_stem_idx   = month_pillar.stem_index
    current_branch_idx = month_pillar.branch_index

    for i in range(8):  # 10년 * 8 = 80세까지
        age_start = start_age + i * 10
        age_end   = age_start + 9

        if is_forward:
            stem_idx   = (current_stem_idx + i + 1) % 10
            branch_idx = (current_branch_idx + i + 1) % 12
        else:
            stem_idx   = (current_stem_idx - i - 1) % 10
            branch_idx = (current_branch_idx - i - 1) % 12

        ten_star = self._get_ten_star(
            self.day_stem_idx_placeholder, stem_idx
        )
        twelve_stage = self._calc_twelve_stage(
            self.day_stem_idx_placeholder, branch_idx
        )

        stem   = STEM_BY_INDEX[stem_idx]
        branch = BRANCH_BY_INDEX[branch_idx]

        cycles.append({
            "age_start":     age_start,
            "age_end":       age_end,
            "stem":          stem["hanja"],
            "branch":        branch["hanja"],
            "stem_kr":       stem["kr"],
            "branch_kr":     branch["kr"],
            "ten_star":      ten_star,
            "twelve_stage":  twelve_stage,
        })

    return cycles

def calculate_current_fortune(
    self, saju_result: SajuResult, target_date: date
) -> dict:
    """
    세운(歲運)/월운(月運)/일운(日運) 계산
    - 세운: target_date의 연주
    - 월운: target_date의 월주 (절기 기준)
    - 일운: target_date의 일주 (만세력 직접 조회)
    """
    yearly = self._calc_year_pillar(target_date)
    monthly_branch_idx = self.manseryeok.get_solar_term_for_month(target_date)
    monthly_stem_idx, _ = calculate_month_pillar(yearly.stem_index, monthly_branch_idx)
    monthly = self._make_pillar(monthly_stem_idx, monthly_branch_idx)
    daily_stem, daily_branch = self.manseryeok.get_day_pillar(target_date)
    daily = self._make_pillar(daily_stem, daily_branch)

    # 현재 적용 중인 대운 탐색
    from datetime import date
    birth_year = saju_result.birth_date.year
    current_age = target_date.year - birth_year
    current_major = next(
        (c for c in saju_result.major_luck_cycles
         if c["age_start"] <= current_age <= c["age_end"]),
        None,
    )

    return {
        "major_luck":   current_major,
        "yearly_luck":  self._pillar_to_dict(yearly),
        "monthly_luck": self._pillar_to_dict(monthly),
        "daily_luck":   self._pillar_to_dict(daily),
    }
```

---

## 2. LLM 연동 설계 (v2: DB-First + abcllm Batch)

> **v2.0 핵심 변경**: 실시간 LLM 호출 → **abcllm 배치 생성 + DB 즉시 송출**
> 상세 프롬프트: [LLM 프롬프트 전략 v2](llm-prompt-strategy.md) | 아키텍처: [Concept v2](architecture-concept-v2.md)
>
> **온라인 서빙**: 사주 계산 → DB 조회 → 즉시 응답 (LLM 호출 없음, < 100ms)
> **오프라인 배치**: abcllm으로 콘텐츠 사전 생성/서술 변형 → DB 업데이트 (Celery Beat)

### 2.1 시스템 프롬프트 구조

시스템 프롬프트는 4개 섹션으로 구성한다.

| 섹션 | 내용 | 목적 |
|------|------|------|
| 역할 정의 | 30년 경력 명리학 전문가 페르소나 | LLM 역할 고정 |
| 해석 원칙 | 데이터 기반 해석, 확률적 표현 사용 | 출력 품질 보장 |
| 윤리 가이드라인 | 의료/법적 조언 금지, 극단적 표현 금지 | 안전성 확보 |
| 응답 형식 | 핵심 해석 -> 근거 -> 조언 순서 | 일관성 확보 |

**공감적 어조 원칙:**
- "~일 수 있습니다", "~경향이 있습니다" 등 가능성 표현 사용
- 부정적 요소는 "주의할 점"으로 프레이밍
- 사용자 이름(닉네임) 호명으로 개인화
- 불안 조장 표현 절대 금지: "반드시 ~이 됩니다", "~이 올 것입니다"

### 2.2 사용자 프롬프트 컨텍스트 빌더

```python
# app/modules/ai_counsel/prompt_manager.py

class ContextBuilder:
    def build(self, profile_data: dict, current_fortune: dict,
              conversation_summary: str, topic: str) -> str:
        saju = profile_data["saju_data"]
        fp   = saju["four_pillars"]
        cf   = current_fortune

        return f"""
[사용자 사주 정보]
- 사주팔자: {fp['year']['stem_kr']}{fp['year']['branch_kr']} {fp['month']['stem_kr']}{fp['month']['branch_kr']} {fp['day']['stem_kr']}{fp['day']['branch_kr']} {fp.get('hour', {}).get('stem_kr','시불명')}{fp.get('hour', {}).get('branch_kr','')}
- 일간: {fp['day']['stem_kr']}({fp['day']['stem_kr']}일간, 오행: {fp['day']['stem_element']})
- 오행 분포: 목({saju['five_elements']['wood']}) 화({saju['five_elements']['fire']}) 토({saju['five_elements']['earth']}) 금({saju['five_elements']['metal']}) 수({saju['five_elements']['water']})
- 격국: {saju['geokguk']['type']}
- 주요 신살: {', '.join(s['name'] for s in saju['special_stars'][:5])}

[현재 운세 - 기준일 {datetime.now().strftime('%Y년 %m월 %d일')}]
- 대운: {cf['major_luck']['stem_kr']}{cf['major_luck']['branch_kr']} ({cf['major_luck']['age_start']}~{cf['major_luck']['age_end']}세, 십성: {cf['major_luck']['ten_star']})
- 세운: {cf['yearly_luck']['stem_kr']}{cf['yearly_luck']['branch_kr']} (십성: {cf['yearly_luck'].get('ten_star','')})
- 월운: {cf['monthly_luck']['stem_kr']}{cf['monthly_luck']['branch_kr']}
- 일운: {cf['daily_luck']['stem_kr']}{cf['daily_luck']['branch_kr']}

[상담 주제]
{self._topic_instruction(topic)}

[이전 대화 요약]
{conversation_summary or '(첫 상담)'}
""".strip()

    def _topic_instruction(self, topic: str) -> str:
        INSTRUCTIONS = {
            "romance":  "연애운과 이성 인연을 중심으로 해석해 주세요. 도화살, 홍염살, 일주 궁합, 재성(남성)/관성(여성) 위주로 분석하세요.",
            "career":   "직장운과 직업 적성을 중심으로 해석해 주세요. 관성(편관/정관), 인성(편인/정인)을 위주로 승진과 이직 시기를 안내하세요.",
            "wealth":   "재물운과 투자 시기를 중심으로 해석해 주세요. 재성(편재/정재), 식상생재 여부를 분석하세요.",
            "health":   "오행 과불급에 따른 건강 주의 사항을 안내해 주세요. 단, 의학적 진단이나 처방은 절대 언급하지 마세요.",
            "study":    "학업운과 수험 시기를 중심으로 해석해 주세요. 인성(정인/편인), 식상(창의력)을 위주로 분석하세요.",
            "general":  "사주 전체 구조를 종합적으로 해석해 주세요. 격국의 특성과 인생 전반의 방향을 안내하세요.",
        }
        return INSTRUCTIONS.get(topic, INSTRUCTIONS["general"])
```

### 2.3 주제별 프롬프트 변형

| 주제 | 중심 분석 요소 | 핵심 질문 |
|------|--------------|---------|
| 연애운 (romance) | 도화살, 홍염살, 재성/관성, 일주 궁합 | "언제 만남의 기회가 오는가?" |
| 직업운 (career) | 관성, 인성, 월주, 대운 세력 | "어떤 직업이 맞고, 이직 시기는?" |
| 재물운 (wealth) | 재성, 식상생재, 편재/정재 비중 | "재물 유형과 절호의 투자 시기는?" |
| 건강운 (health) | 오행 부족/과잉, 지지 충/형 | "어떤 부분을 주의해야 하는가?" |
| 학업운 (study) | 정인/편인, 식신, 지혜성 | "수험 시기와 적합한 학습 방향은?" |
| 일반 (general) | 격국, 용신, 오행 균형 전체 | "내 사주의 핵심 특성은?" |

### 2.4 출력 검증 규칙

```python
# app/modules/ai_counsel/safety_filter.py

import re

class SafetyFilter:
    # 위기 감지 패턴 (입력 사전 차단)
    CRISIS_PATTERNS = [
        r"자살", r"자해", r"죽고\s*싶", r"살고\s*싶지\s*않", r"극단적\s*선택"
    ]

    # 의학적 조언 패턴 (출력 후처리)
    MEDICAL_PATTERNS = [
        r"약\s*처방", r"진단\s*결과", r"치료\s*방법", r"병원에서"
    ]

    # 법적 조언 패턴
    LEGAL_PATTERNS = [r"소송", r"법적\s*조언", r"고소"]

    # 확정적 부정 표현 (출력 완화)
    ABSOLUTE_NEGATIVE = [
        r"반드시\s*망", r"틀림없이\s*실패", r"절대\s*안\s*됩니다"
    ]

    DISCLAIMER = "\n\n*본 해석은 참고용 엔터테인먼트 서비스입니다. 중요한 결정은 전문가와 상담하세요.*"

    def check_input(self, text: str) -> tuple[bool, str]:
        """입력 안전성 검사. (차단 여부, 대체 메시지)"""
        for pattern in self.CRISIS_PATTERNS:
            if re.search(pattern, text):
                return True, (
                    "마음이 많이 힘드신가요? 정신건강 위기상담전화 1577-0199(24시간)로 "
                    "연락하시면 전문 상담사가 도와드립니다."
                )
        return False, ""

    def filter_output(self, text: str, add_disclaimer: bool = False) -> str:
        """출력 후처리 필터"""
        # 의료/법적 조언 감지 시 면책 조항 추가
        needs_disclaimer = add_disclaimer
        for pattern in self.MEDICAL_PATTERNS + self.LEGAL_PATTERNS:
            if re.search(pattern, text):
                needs_disclaimer = True
                break

        # 확정적 부정 표현 완화
        for pattern in self.ABSOLUTE_NEGATIVE:
            text = re.sub(pattern, lambda m: m.group().replace("반드시", "경우에 따라"), text)

        if needs_disclaimer:
            text += self.DISCLAIMER

        return text
```

---

## 3. 사용자 데이터 관리

### 3.1 인증/인가 (카카오 OAuth + JWT)

#### OAuth 2.0 흐름

```
클라이언트(Next.js)
  1. 카카오 로그인 버튼 클릭
  2. 카카오 OAuth 서버로 리다이렉트 (code 요청)
  3. 인가 코드(code) 수신 (브라우저 콜백)
  4. POST /api/v1/auth/login { provider: "kakao", code: "..." }

백엔드(FastAPI Auth Module)
  5. 카카오 토큰 교환 (code -> kakao_access_token)
  6. 카카오 사용자 정보 조회 (/v2/user/me)
  7. DB에서 provider+provider_id로 사용자 조회 또는 신규 생성
  8. JWT Access Token (1시간) + Refresh Token (30일) 발급
  9. Refresh Token은 SHA-256 해시 후 DB 저장, Redis에도 캐싱

클라이언트
  10. Access Token: 메모리 변수에 저장 (보안)
  11. Refresh Token: HttpOnly Cookie에 저장
```

#### JWT 발급/검증

```python
# app/core/security.py

from jose import jwt
from datetime import datetime, timedelta
import hashlib, secrets

SECRET_KEY = settings.JWT_SECRET_KEY  # 환경 변수
ALGORITHM  = "HS256"

def create_access_token(user_id: str, is_premium: bool) -> str:
    payload = {
        "sub":           user_id,
        "type":          "access",
        "is_premium":    is_premium,
        "iat":           datetime.utcnow(),
        "exp":           datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> tuple[str, str]:
    """(원본 토큰, SHA-256 해시) 반환. DB에는 해시만 저장."""
    raw_token = secrets.token_urlsafe(64)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="AUTH_INVALID_TOKEN")
        user_id = payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="AUTH_TOKEN_EXPIRED")

    user = await db.get(User, user_id)
    if not user or user.deleted_at:
        raise HTTPException(status_code=401, detail="AUTH_INVALID_TOKEN")
    return user
```

#### 인가 (Role 기반 접근 제어)

```python
# app/core/security.py

def require_premium(current_user: User = Depends(get_current_user)) -> User:
    """프리미엄 전용 엔드포인트 가드"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PREMIUM_REQUIRED",
                "message": "프리미엄 구독이 필요한 기능입니다.",
            }
        )
    return current_user

def check_consult_limit(current_user: User = Depends(get_current_user)) -> User:
    """무료 사용자 일일 상담 횟수 제한 (3회)"""
    if current_user.is_premium:
        return current_user
    if current_user.daily_consult_count >= 3:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "CONSULTATION_LIMIT_EXCEEDED",
                "message": "일일 무료 상담 횟수(3회)를 초과했습니다.",
                "daily_limit": 3,
                "used": current_user.daily_consult_count,
            }
        )
    return current_user
```

### 3.2 사주 프로필 CRUD

```python
# app/modules/saju_engine/service.py

class SajuProfileService:

    async def create_profile(
        self, user_id: str, data: ProfileCreateRequest, db: AsyncSession
    ) -> SajuProfile:
        # 프로필 5개 초과 체크
        count = await db.scalar(
            select(func.count()).where(
                SajuProfile.user_id == user_id,
                SajuProfile.deleted_at.is_(None),
            )
        )
        if count >= 5:
            raise HTTPException(status_code=403, detail="PROFILE_LIMIT_EXCEEDED")

        # 생년월일 AES-256-GCM 암호화
        birth_date_enc = encrypt_aes256(str(data.birth_date))
        birth_time_enc = encrypt_aes256(str(data.birth_time)) if data.birth_time else None

        # 사주 산출
        saju_result = self.calculator.calculate(
            birth_date=data.birth_date,
            birth_time=data.birth_time,
            is_lunar=data.is_lunar,
            is_leap_month=data.is_leap_month,
            gender=data.gender,
        )

        profile = SajuProfile(
            user_id=user_id,
            label=data.label,
            name=data.name,
            birth_date_encrypted=birth_date_enc,
            birth_time_encrypted=birth_time_enc,
            is_lunar=data.is_lunar,
            is_leap_month=data.is_leap_month,
            gender=data.gender,
            saju_data=saju_result.to_jsonb(),
        )
        db.add(profile)
        await db.commit()
        return profile

    async def get_profiles(self, user_id: str, db: AsyncSession) -> list[SajuProfile]:
        result = await db.execute(
            select(SajuProfile)
            .where(SajuProfile.user_id == user_id, SajuProfile.deleted_at.is_(None))
            .order_by(SajuProfile.created_at)
        )
        return result.scalars().all()

    async def soft_delete_profile(
        self, profile_id: str, user_id: str, db: AsyncSession
    ) -> None:
        profile = await self._get_own_profile(profile_id, user_id, db)
        profile.deleted_at = datetime.utcnow()
        await db.commit()
```

### 3.3 상담 이력 관리

```python
# app/modules/ai_counsel/service.py

class AICounselService:

    async def create_consultation(
        self, user_id: str, profile_id: str, topic: str, db: AsyncSession
    ) -> Consultation:
        # 프로필 소유권 확인
        await self._verify_profile_ownership(profile_id, user_id, db)

        consultation = Consultation(
            user_id=user_id,
            profile_id=profile_id,
            topic=topic,
            title=self._generate_title(topic),
            status="active",
        )
        db.add(consultation)
        await db.commit()
        return consultation

    async def get_consultations(
        self, user_id: str, cursor: str | None, limit: int, db: AsyncSession
    ) -> tuple[list[Consultation], str | None]:
        """커서 기반 페이지네이션"""
        query = (
            select(Consultation)
            .where(Consultation.user_id == user_id)
            .order_by(Consultation.created_at.desc())
        )
        if cursor:
            cursor_dt = decode_cursor(cursor)
            query = query.where(Consultation.created_at < cursor_dt)

        consultations = (await db.execute(query.limit(limit + 1))).scalars().all()
        has_next = len(consultations) > limit
        next_cursor = encode_cursor(consultations[limit - 1].created_at) if has_next else None
        return consultations[:limit], next_cursor

    async def get_messages(
        self, consultation_id: str, user_id: str, db: AsyncSession
    ) -> list[Message]:
        """최대 100개(50턴) 메시지 반환, 시간순"""
        await self._verify_consultation_ownership(consultation_id, user_id, db)
        result = await db.execute(
            select(Message)
            .where(Message.consultation_id == consultation_id)
            .order_by(Message.created_at)
            .limit(100)
        )
        return result.scalars().all()
```

---

## 4. 결제/구독 시스템

### 4.1 Toss Payments 연동

```python
# app/modules/payment/toss_client.py

import httpx
import base64

class TossPaymentsClient:
    BASE_URL = "https://api.tosspayments.com/v1"

    def __init__(self, secret_key: str):
        # Toss Payments 인증: Base64(secret_key + ":")
        encoded = base64.b64encode(f"{secret_key}:".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }

    async def confirm_payment(self, payment_key: str, order_id: str, amount: int) -> dict:
        """결제 승인 요청"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments/confirm",
                json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
                headers=self.headers,
                timeout=10.0,
            )
        resp.raise_for_status()
        return resp.json()

    async def issue_billing_key(self, customer_key: str, auth_key: str) -> dict:
        """자동 결제용 빌링키 발급"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/billing/authorizations/issue",
                json={"customerKey": customer_key, "authKey": auth_key},
                headers=self.headers,
            )
        resp.raise_for_status()
        return resp.json()

    async def charge_billing(
        self, billing_key: str, customer_key: str,
        order_id: str, amount: int, order_name: str
    ) -> dict:
        """빌링키로 구독 자동 결제"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/billing/{billing_key}",
                json={
                    "customerKey": customer_key,
                    "amount": amount,
                    "orderId": order_id,
                    "orderName": order_name,
                },
                headers=self.headers,
            )
        resp.raise_for_status()
        return resp.json()

    async def cancel_payment(self, payment_key: str, reason: str) -> dict:
        """결제 취소/환불"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/payments/{payment_key}/cancel",
                json={"cancelReason": reason},
                headers=self.headers,
            )
        resp.raise_for_status()
        return resp.json()
```

### 4.2 3단계 구독 모델

| 플랜 | 가격 | AI 상담 | 운세 | 기능 |
|------|------|---------|------|------|
| 무료 | 0원 | 일 3회 | 오늘의 운세 | 기본 사주 산출, 프로필 1개 |
| 베이직 | 3,900원/월 | 일 10회 | 주간 운세 | 프로필 3개, 기본 신살/격국 |
| 프리미엄 | 9,900원/월 | 무제한 | 월간/연간/길일 | 프로필 5개, 심화 분석, 궁합, 공유 카드 |

```python
# app/modules/payment/service.py

PLAN_LIMITS = {
    "free":    {"daily_consult": 3,  "profiles": 1, "price": 0},
    "basic":   {"daily_consult": 10, "profiles": 3, "price": 3900},
    "premium": {"daily_consult": -1, "profiles": 5, "price": 9900},  # -1 = unlimited
}

class PaymentService:

    async def start_subscription(
        self, user_id: str, plan: str, billing_key: str, db: AsyncSession
    ) -> Subscription:
        """구독 생성 및 즉시 첫 결제"""
        price = PLAN_LIMITS[plan]["price"]
        order_id = f"sub_{user_id}_{int(datetime.utcnow().timestamp())}"

        toss_result = await self.toss_client.charge_billing(
            billing_key=billing_key,
            customer_key=user_id,
            order_id=order_id,
            amount=price,
            order_name=f"Saju AI {plan.capitalize()} 구독",
        )

        now = datetime.utcnow()
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            pg_subscription_id=billing_key,
        )
        db.add(subscription)

        payment = Payment(
            user_id=user_id,
            subscription_id=subscription.id,
            type="subscription",
            amount=price,
            status="completed",
            pg_transaction_id=order_id,
            pg_payment_key=toss_result["paymentKey"],
            paid_at=datetime.utcnow(),
        )
        db.add(payment)

        # 사용자 프리미엄 상태 업데이트
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_premium=True,
                    premium_until=subscription.current_period_end)
        )
        await db.commit()
        return subscription

    async def cancel_subscription(
        self, subscription_id: str, user_id: str, db: AsyncSession
    ) -> Subscription:
        """구독 취소: 현재 기간 종료까지 사용 가능"""
        subscription = await self._get_own_subscription(subscription_id, user_id, db)
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        await db.commit()
        return subscription

    async def handle_webhook(self, payload: dict, db: AsyncSession) -> None:
        """
        Toss Payments 웹훅 처리
        - PAYMENT_STATUS_CHANGED: 결제 상태 변경
        - BILLING_KEY_DELETED: 빌링키 삭제 (구독 만료 처리)
        """
        event_type = payload.get("eventType")
        if event_type == "PAYMENT_STATUS_CHANGED":
            await self._sync_payment_status(payload, db)
        elif event_type == "BILLING_KEY_DELETED":
            await self._expire_subscription(payload["billingKey"], db)
```

### 4.3 사용량 추적 및 제한

```python
# app/modules/auth/service.py

class UsageTracker:
    """Redis 기반 실시간 사용량 추적"""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def increment_consult(self, user_id: str, db: AsyncSession) -> int:
        """상담 횟수 증가. DB와 Redis 동기화."""
        today = date.today().isoformat()
        redis_key = f"consult:{user_id}:{today}"

        # Redis에서 원자적 증가
        count = await self.redis.incr(redis_key)
        if count == 1:
            # 첫 증가 시 자정까지 TTL 설정
            seconds_left = self._seconds_until_midnight()
            await self.redis.expire(redis_key, seconds_left)

        # DB 동기화 (비동기, 실패해도 Redis 기준)
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                daily_consult_count=count,
                consult_reset_at=today,
            )
        )
        return count

    def _seconds_until_midnight(self) -> int:
        from datetime import datetime, time
        now = datetime.now()
        midnight = datetime.combine(now.date() + timedelta(days=1), time.min)
        return int((midnight - now).total_seconds())
```

---

## 5. API 엔드포인트 전체 목록

### 5.1 공통 규격

```
Base URL: /api/v1
Content-Type: application/json
Authorization: Bearer {access_token}

공통 응답:
  성공: { "data": {...}, "meta": { "request_id": "...", "timestamp": "..." } }
  목록: { "data": [...], "meta": { "cursor": "...", "has_next": bool } }
  오류: { "error": { "code": "...", "message": "..." } }
```

### 5.2 인증 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/auth/login` | 없음 | OAuth 소셜 로그인 |
| POST | `/auth/refresh` | Refresh Token (Cookie) | Access Token 갱신 |
| DELETE | `/auth/logout` | Bearer | 로그아웃 |
| GET | `/auth/me` | Bearer | 현재 사용자 정보 |

#### POST /auth/login

```json
// Request
{
  "provider": "kakao",
  "code": "auth_code_from_kakao",
  "redirect_uri": "https://saju-ai.app/auth/callback"
}

// Response 200
{
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "nickname": "김지은",
      "profile_image_url": "https://...",
      "is_premium": false,
      "daily_consult_count": 0
    }
  }
}
// Refresh Token은 HttpOnly Cookie로 설정
```

#### POST /auth/refresh

```json
// Request: Cookie에서 refresh_token 자동 전송

// Response 200
{
  "data": {
    "access_token": "eyJhbGc...",
    "expires_in": 3600
  }
}
```

#### DELETE /auth/logout

```json
// Response 204 No Content
// Refresh Token 쿠키 삭제 및 DB/Redis에서 토큰 무효화
```

---

### 5.3 사주 프로필 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/profiles` | Bearer | 프로필 생성 + 사주 산출 |
| GET | `/profiles` | Bearer | 내 프로필 목록 |
| GET | `/profiles/:id` | Bearer | 프로필 상세 (사주 데이터 포함) |
| DELETE | `/profiles/:id` | Bearer | 프로필 소프트 삭제 |

#### POST /profiles

```json
// Request
{
  "name": "김지은",
  "label": "self",
  "birth_date": "1997-03-15",
  "birth_time": "14:30",
  "is_lunar": false,
  "is_leap_month": false,
  "gender": "female"
}

// Response 201
{
  "data": {
    "id": "uuid",
    "name": "김지은",
    "label": "self",
    "gender": "female",
    "saju_data": {
      "four_pillars": {
        "year":  { "stem": "丁", "branch": "丑", "stem_kr": "정", "branch_kr": "축", "stem_element": "fire", "branch_element": "earth" },
        "month": { "stem": "丙", "branch": "寅", "stem_kr": "병", "branch_kr": "인", "stem_element": "fire", "branch_element": "wood" },
        "day":   { "stem": "戊", "branch": "午", "stem_kr": "무", "branch_kr": "오", "stem_element": "earth", "branch_element": "fire" },
        "hour":  { "stem": "庚", "branch": "申", "stem_kr": "경", "branch_kr": "신", "stem_element": "metal", "branch_element": "metal" }
      },
      "five_elements": { "wood": 1, "fire": 3, "earth": 2, "metal": 2, "water": 0, "dominant": "fire", "lacking": "water" },
      "ten_stars": {
        "year_stem": "정인", "year_branch": "겁재",
        "month_stem": "겁재", "month_branch": "비견",
        "day_branch": "겁재",
        "hour_stem": "식신", "hour_branch": "식신",
        "summary": { "비겁": 3, "식상": 2, "재성": 0, "관성": 0, "인성": 1 }
      },
      "twelve_stages": { "year": "양", "month": "장생", "day": "제왕", "hour": "병" },
      "special_stars": [
        { "name": "도화살", "hanja": "桃花殺", "pillar": "year", "description": "매력과 인기가 강한 기운" }
      ],
      "geokguk": { "type": "겁재격", "hanja": "劫財格", "category": "정격", "description": "월지 정기의 겁재가 격을 이룸" },
      "major_luck_cycles": [
        { "age_start": 5, "age_end": 14, "stem": "乙", "branch": "丑", "stem_kr": "을", "branch_kr": "축", "ten_star": "정인", "twelve_stage": "양" }
      ]
    },
    "created_at": "2026-03-25T10:00:00Z"
  }
}
```

#### GET /profiles

```json
// Response 200
{
  "data": [
    {
      "id": "uuid-1",
      "name": "김지은",
      "label": "self",
      "gender": "female",
      "saju_summary": {
        "day_stem": "戊",
        "day_stem_kr": "무",
        "geokguk": "겁재격",
        "five_elements": { "dominant": "fire", "lacking": "water" }
      },
      "created_at": "2026-03-25T10:00:00Z"
    }
  ]
}
```

---

### 5.4 상담 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/consultations` | Bearer | 상담 세션 생성 |
| GET | `/consultations` | Bearer | 상담 이력 목록 (커서 페이지네이션) |
| GET | `/consultations/:id` | Bearer | 상담 상세 |
| GET | `/consultations/:id/messages` | Bearer | 메시지 목록 |
| POST | `/consultations/:id/messages` | Bearer | 메시지 전송 (SSE 스트리밍) |
| PATCH | `/consultations/:id/messages/:mid/feedback` | Bearer | 메시지 피드백 |
| POST | `/consultations/:id/feedback` | Bearer | 상담 전체 평가 |

#### POST /consultations

```json
// Request
{
  "profile_id": "uuid",
  "topic": "romance"
}

// Response 201
{
  "data": {
    "id": "uuid",
    "profile_id": "uuid",
    "topic": "romance",
    "title": "연애운 상담",
    "status": "active",
    "message_count": 0,
    "created_at": "2026-03-25T10:00:00Z"
  }
}
```

#### POST /consultations/:id/messages (SSE 스트리밍)

```json
// Request
{
  "content": "올해 연애운이 어떤가요? 좋아하는 사람이 생겼어요."
}

// Response: text/event-stream
// Content-Type: text/event-stream
// X-Accel-Buffering: no

event: token
data: {"token": "올해"}

event: token
data: {"token": " 2026년"}

event: token
data: {"token": " 세운은..."}

// ... (스트리밍 토큰 연속)

event: done
data: {"message_id": "uuid", "usage": {"prompt_tokens": 1200, "completion_tokens": 450}}
```

#### PATCH /consultations/:id/messages/:mid/feedback

```json
// Request
{
  "feedback": "thumbs_up"
}

// Response 200
{
  "data": { "message_id": "uuid", "feedback": "thumbs_up" }
}
```

---

### 5.5 운세 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| GET | `/fortunes/daily` | Bearer | 오늘의 운세 |
| GET | `/fortunes/weekly` | Bearer | 주간 운세 |
| GET | `/fortunes/monthly` | Bearer (Premium) | 월간 운세 |
| GET | `/fortunes/yearly` | Bearer (Premium) | 연간 운세 |
| GET | `/fortunes/calendar` | Bearer (Premium) | 길일 캘린더 |

#### GET /fortunes/daily?profile_id=:id

```json
// Response 200
{
  "data": {
    "date": "2026-03-25",
    "day_stem": "甲",
    "day_branch": "子",
    "day_stem_kr": "갑",
    "day_branch_kr": "자",
    "fortune_data": {
      "overall":  { "score": 75, "keywords": ["인내", "준비", "기회"] },
      "romance":  { "score": 80, "keywords": ["설렘", "인연"] },
      "wealth":   { "score": 60, "keywords": ["절약", "신중"] },
      "health":   { "score": 85, "keywords": ["활력", "운동"] },
      "career":   { "score": 70, "keywords": ["집중", "성과"] }
    },
    "content": "오늘은 갑자(甲子)일로, 새로운 시작의 기운이 넘칩니다...",
    "lucky_color": "파란색",
    "lucky_number": 1,
    "advice": "오늘은 적극적으로 의사 표현을 하면 좋은 결과가 있을 수 있습니다."
  }
}
```

---

### 5.6 궁합 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/compatibility` | Bearer | 두 프로필 궁합 분석 |

#### POST /compatibility

```json
// Request
{
  "profile_id_a": "uuid-1",
  "profile_id_b": "uuid-2"
}

// Response 200
{
  "data": {
    "profile_a": { "name": "김지은", "day_stem_kr": "무" },
    "profile_b": { "name": "이민준", "day_stem_kr": "갑" },
    "overall_score": 82,
    "scores": {
      "emotional":  { "score": 85, "description": "갑목과 무토는 상극 관계이나, 갑목이 무토를 다스려 강한 이끌림이 생깁니다." },
      "values":     { "score": 78, "description": "서로 다른 가치관이 보완 관계를 형성합니다." },
      "lifestyle":  { "score": 80, "description": "활동적인 기운이 잘 맞습니다." },
      "future":     { "score": 84, "description": "장기적으로 안정적인 관계를 형성할 수 있습니다." }
    },
    "saju_interaction": {
      "five_elements_balance": "목화토금수 균형이 양호합니다",
      "special_notes": ["두 일주(무오-갑자)의 음양 조화가 좋습니다"]
    },
    "ai_analysis": "두 분의 사주는 갑목(甲木)과 무토(戊土)의 상극 관계...",
    "lucky_period": "2026년 5~6월 대화가 잘 통하는 시기",
    "advice": "상대방의 주도적 성향을 인정하면 좋은 관계를 유지할 수 있습니다."
  }
}
```

---

### 5.7 결제 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| POST | `/subscriptions` | Bearer | 구독 신청 (빌링키 발급 후 호출) |
| GET | `/subscriptions/current` | Bearer | 현재 구독 상태 |
| DELETE | `/subscriptions/current` | Bearer | 구독 취소 |
| POST | `/payments/verify` | Bearer | 단건 결제 검증 및 승인 |
| GET | `/payments/history` | Bearer | 결제 이력 |
| POST | `/payments/webhook` | 없음 (서명 검증) | Toss Payments 웹훅 |

#### POST /subscriptions

```json
// Request
{
  "plan": "premium",
  "billing_key": "toss_billing_key_xxxx",
  "customer_key": "user_uuid"
}

// Response 201
{
  "data": {
    "id": "uuid",
    "plan_type": "premium",
    "status": "active",
    "current_period_start": "2026-03-25T00:00:00Z",
    "current_period_end": "2026-04-25T00:00:00Z",
    "amount_paid": 9900
  }
}
```

#### GET /subscriptions/current

```json
// Response 200
{
  "data": {
    "plan": "premium",
    "status": "active",
    "current_period_end": "2026-04-25T00:00:00Z",
    "features": {
      "daily_consult_limit": -1,
      "max_profiles": 5,
      "monthly_fortune": true,
      "compatibility": true
    }
  }
}
```

#### POST /payments/verify

```json
// Request (Toss Payments 단건 결제 승인)
{
  "payment_key": "toss_payment_key",
  "order_id": "order_uuid",
  "amount": 9900
}

// Response 200
{
  "data": {
    "payment_id": "uuid",
    "status": "completed",
    "amount": 9900,
    "paid_at": "2026-03-25T10:05:00Z"
  }
}
```

---

### 5.8 사용자 API

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| GET | `/users/me` | Bearer | 내 계정 정보 |
| PATCH | `/users/me` | Bearer | 프로필 수정 |
| DELETE | `/users/me` | Bearer | 회원 탈퇴 (소프트 삭제) |

#### GET /users/me

```json
// Response 200
{
  "data": {
    "id": "uuid",
    "nickname": "김지은",
    "email": "jieun@example.com",
    "profile_image_url": "https://...",
    "provider": "kakao",
    "is_premium": true,
    "premium_until": "2026-04-25T00:00:00Z",
    "daily_consult_count": 2,
    "consult_limit": -1,
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### 5.9 에러 코드 전체 목록

| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| `AUTH_INVALID_TOKEN` | 401 | JWT 유효하지 않음 |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT 만료 |
| `AUTH_REFRESH_EXPIRED` | 401 | Refresh Token 만료 |
| `PROFILE_NOT_FOUND` | 404 | 프로필 없음 또는 소유권 없음 |
| `PROFILE_LIMIT_EXCEEDED` | 403 | 프로필 최대 개수(5개) 초과 |
| `PREMIUM_REQUIRED` | 403 | 프리미엄 전용 기능 접근 |
| `CONSULTATION_NOT_FOUND` | 404 | 상담 세션 없음 |
| `CONSULTATION_LIMIT_EXCEEDED` | 429 | 일일 상담 횟수 초과 |
| `RATE_LIMIT_EXCEEDED` | 429 | API Rate Limit 초과 |
| `SAJU_CALCULATION_ERROR` | 422 | 사주 산출 오류 (날짜 범위 오류 등) |
| `LLM_UNAVAILABLE` | 503 | LLM API 일시 불가 |
| `PAYMENT_FAILED` | 402 | 결제 실패 |
| `PAYMENT_AMOUNT_MISMATCH` | 400 | 결제 금액 불일치 |
| `SUBSCRIPTION_NOT_FOUND` | 404 | 구독 없음 |
| `INVALID_INPUT` | 422 | 입력값 검증 실패 |
| `INTERNAL_ERROR` | 500 | 서버 내부 오류 |
