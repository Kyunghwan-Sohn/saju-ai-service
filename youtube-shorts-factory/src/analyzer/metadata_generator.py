"""LLM으로 유튜브 숏폼 제목/설명/해시태그 자동 생성."""
from __future__ import annotations

import json


def generate_metadata(
    expression_en: str,
    expression_ko: str,
    celebrity: str,
    show_name: str,
    summary: str,
    full_title: str = "",
) -> dict:
    """LLM을 사용해 YouTube Shorts 메타데이터를 생성한다.

    Returns:
        {"title": str, "description": str, "tags": list[str], "hashtags": str}
    """
    from src.analyzer.llm_client import chat as llm_chat

    prompt = f"""YouTube Shorts 영상의 제목, 설명, 해시태그를 만들어줘.

[영상 정보]
- 셀럽: {celebrity}
- 프로그램: {show_name}
- 원본 제목: {full_title}
- 핵심 영어 표현: {expression_en} = {expression_ko}
- 내용 요약: {summary}

[규칙]
1. 제목: 40자 이내, 클릭을 유도하는 한국어 제목
   - 패턴: "셀럽이 말한 'expression' 뜻은?" 또는 "이 표현 아세요?"
   - #Shorts 포함하지 마 (자동 추가됨)
2. 설명: 3~5줄, 자연스러운 한국어
   - 첫 줄: 핵심 표현 + 뜻 (검색 최적화)
   - 본문: 어떤 상황에서 쓰이는지 간단 설명
   - 마지막 줄: CTA (좋아요/구독/댓글 유도)
3. 해시태그: 10~15개 (영어+한국어 혼합)
   - 필수: #Shorts #영어공부 #영어표현 #원어민표현
   - 셀럽 이름, 프로그램명, 표현 관련 태그
4. 태그(tags): SEO용 영어+한국어 키워드 10개

JSON으로만 응답:
{{
  "title": "유튜브 제목",
  "description": "설명 본문 (해시태그 없이)",
  "hashtags": "#Shorts #영어공부 #영어표현 ...",
  "tags": ["tag1", "tag2", ...]
}}"""

    raw = llm_chat([
        {"role": "system", "content": "YouTube SEO 전문가. JSON만 응답. 한자 절대 금지."},
        {"role": "user", "content": prompt},
    ])

    text = raw.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    s, e = text.find("{"), text.rfind("}") + 1
    if s >= 0 and e > s:
        text = text[s:e]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {}

    title = data.get("title", f"{celebrity} - {expression_en}")
    description = data.get("description", f"{expression_en} = {expression_ko}")
    hashtags = data.get("hashtags", "#Shorts #영어공부 #영어표현")
    tags = data.get("tags", [expression_en, celebrity, "영어공부", "Shorts"])

    # 설명에 해시태그 병합
    full_desc = f"{description}\n\n{hashtags}"

    return {
        "title": title[:100],
        "description": full_desc[:5000],
        "tags": tags[:15],
        "hashtags": hashtags,
    }
