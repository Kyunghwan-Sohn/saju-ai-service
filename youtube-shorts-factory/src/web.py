"""YouTube Shorts Factory — 로컬 웹 UI (v2)

큰 글자, 한 줄씩 영/한 분리, 핵심 표현 강조, 자동 구간 결정.
"""
from __future__ import annotations

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gradio as gr

from src.config import settings

_search_cache: list[dict] = []
_transcript_cache: list[dict] = []
_video_meta: dict = {}
_video_path: Path | None = None
_kr_translations: dict[str, str] = {}
_analysis: dict = {}


# ─── Custom CSS ──────────────────────────────────────────────────────

CUSTOM_CSS = """
/* 전체 폰트 키우기 */
.gradio-container { font-size: 17px !important; max-width: 1100px !important; }
.gr-button { font-size: 18px !important; font-weight: 700 !important; padding: 14px 28px !important; }
.gr-input, .gr-textbox textarea, .gr-textbox input { font-size: 17px !important; }
label { font-size: 15px !important; font-weight: 600 !important; }

/* 섹션 헤더 */
.section-title {
    font-size: 26px !important; font-weight: 800 !important;
    margin: 32px 0 12px !important; padding: 12px 0 !important;
    border-bottom: 3px solid #7c3aed !important; color: #1a1a2e !important;
}
.section-num {
    display: inline-block; background: #7c3aed; color: #fff;
    width: 36px; height: 36px; line-height: 36px; text-align: center;
    border-radius: 50%; font-size: 18px; margin-right: 10px;
}

/* 스크립트 한줄 카드 */
.line-card {
    border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 18px;
    margin-bottom: 8px; background: #fff; transition: all 0.15s;
}
.line-card:hover { border-color: #7c3aed; box-shadow: 0 2px 8px rgba(124,58,237,0.08); }
.line-card.highlight { border-color: #f59e0b; background: #fffbeb; border-width: 2px; }
.line-card.in-range { background: #f5f3ff; border-color: #c4b5fd; }
.line-num { color: #9ca3af; font-size: 13px; font-weight: 600; margin-right: 8px; min-width: 36px; display: inline-block; }
.line-time { color: #a78bfa; font-size: 12px; font-weight: 500; margin-right: 12px; }
.line-en { font-size: 18px; font-weight: 600; color: #1e293b; line-height: 1.5; }
.line-ko { font-size: 16px; color: #6b7280; margin-top: 4px; line-height: 1.5; }
.line-expr-mark { background: #fef3c7; padding: 2px 6px; border-radius: 4px; font-weight: 700; color: #92400e; }

/* 핵심 표현 카드 */
.expr-card {
    border: 2px solid #7c3aed; border-radius: 16px; padding: 24px;
    margin-bottom: 16px; background: linear-gradient(135deg, #f5f3ff 0%, #fff 100%);
}
.expr-en { font-size: 32px; font-weight: 900; color: #7c3aed; }
.expr-ko { font-size: 22px; font-weight: 700; color: #1e293b; margin-top: 4px; }
.expr-sentence { font-size: 15px; color: #6b7280; margin-top: 10px; padding: 10px; background: #f8fafc; border-radius: 8px; }
.expr-reason { font-size: 14px; color: #a78bfa; margin-top: 6px; }
.expr-badge {
    display: inline-block; background: #7c3aed; color: #fff;
    padding: 4px 14px; border-radius: 20px; font-size: 14px; font-weight: 700; margin-bottom: 10px;
}

/* 구간 표시 */
.range-info {
    background: #ecfdf5; border: 2px solid #10b981; border-radius: 12px;
    padding: 16px 20px; font-size: 18px; font-weight: 700; color: #065f46;
}
"""


# ─── Step 1: 검색 ─────────────────────────────────────────────────────

def search_videos(keyword: str):
    from src.trending.youtube_api import search_talkshows
    global _search_cache
    if not keyword.strip():
        return gr.update(choices=[], value=None)
    videos = search_talkshows(query=keyword, limit=5)
    _search_cache = videos
    choices = [
        f"{i+1}. {v['title'][:60]} | {v['channel']} | {v['views']:,}views"
        for i, v in enumerate(videos)
    ]
    return gr.update(choices=choices, value=None)


def on_video_select(selected):
    if not selected or not _search_cache:
        return ""
    try:
        return _search_cache[int(selected.split(".")[0]) - 1]["url"]
    except Exception:
        return ""


# ─── Step 2: STT + 분석 ───────────────────────────────────────────────

def load_and_analyze(url: str, progress=gr.Progress()):
    try:
        return _load_inner(url, progress)
    except Exception as e:
        return f"<div style='color:red;font-size:20px'>오류: {e}</div>", "", "", 1, 10, "", ""


def _load_inner(url, progress):
    global _transcript_cache, _video_meta, _video_path, _kr_translations, _analysis

    t0 = time.time()
    video_id = url.split("v=")[-1].split("&")[0]
    dl_dir = settings.downloads_dir
    settings.ensure_dirs()

    _video_path = dl_dir / f"{video_id}.mp4"
    audio_path = dl_dir / f"{video_id}_audio.wav"
    meta_path = dl_dir / f"{video_id}.json"

    # 다운로드
    progress(0.05, desc="다운로드 중...")
    if not audio_path.exists():
        if _video_path.exists():
            subprocess.run([
                "ffmpeg", "-y", "-i", str(_video_path),
                "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le",
                str(audio_path),
            ], capture_output=True, timeout=60)
        else:
            cmd = [
                "yt-dlp", "--js-runtimes", "node", "--remote-components", "ejs:github",
                "--cookies-from-browser", "chrome",
                "-f", f"bestvideo[height<={settings.video_quality}]+bestaudio/best[height<={settings.video_quality}]",
                "--merge-output-format", "mp4",
                "-o", str(dl_dir / "%(id)s.%(ext)s"), url,
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                return "다운로드 실패", "", "", 1, 10, "", ""
            subprocess.run([
                "ffmpeg", "-y", "-i", str(_video_path),
                "-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le",
                str(audio_path),
            ], capture_output=True, timeout=60)

    # 메타데이터 + STT 병렬
    progress(0.2, desc="STT 처리 중...")

    def _meta():
        if meta_path.exists():
            return json.loads(meta_path.read_text())
        cmd = ["yt-dlp", "--js-runtimes", "node", "--remote-components", "ejs:github",
               "--cookies-from-browser", "chrome", "--print-json", "--skip-download", url]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        try:
            info = json.loads(r.stdout)
            d = info.get("upload_date", "")
            meta = {"video_id": video_id, "title": info.get("title", ""),
                    "duration": info.get("duration", 0), "channel": info.get("uploader", ""),
                    "upload_date": f"{d[:4]}.{d[4:6]}.{d[6:]}" if len(d) == 8 else ""}
        except Exception:
            meta = {"video_id": video_id, "title": "", "duration": 0, "channel": "", "upload_date": ""}
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        return meta

    def _stt():
        from src.transcriber.whisper_local import transcribe
        return transcribe(audio_path, language="en")

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1, f2 = ex.submit(_stt), ex.submit(_meta)
        tr = f1.result()
        _video_meta = f2.result()

    _transcript_cache = tr["segments"]

    # 비디오 백그라운드 다운로드
    if not _video_path.exists():
        ThreadPoolExecutor(1).submit(lambda: subprocess.run([
            "yt-dlp", "--js-runtimes", "node", "--remote-components", "ejs:github",
            "--cookies-from-browser", "chrome",
            "-f", f"bestvideo[height<={settings.video_quality}]+bestaudio/best",
            "--merge-output-format", "mp4", "-o", str(dl_dir / "%(id)s.%(ext)s"), url,
        ], capture_output=True, timeout=300))

    # LLM 분석
    progress(0.7, desc="AI 분석 중 (번역+요약+표현추천)...")
    _kr_translations, _analysis = _analyze_all(_transcript_cache)

    elapsed = time.time() - t0

    # 자동 구간 결정
    first_expr = _analysis.get("expressions", [{}])[0] if _analysis.get("expressions") else {}
    suggested_expr = first_expr.get("expression_en", "")
    suggested_kr = first_expr.get("expression_ko", "")

    if first_expr and _transcript_cache:
        auto_start, auto_end = _calc_clip_range(first_expr, _transcript_cache)
    else:
        auto_start, auto_end = 1, min(15, len(_transcript_cache))

    # ── 핵심 표현 카드 HTML ──
    expr_html = _build_expression_cards_html()

    # ── 스크립트 HTML (한 줄씩, 영/한 분리, 구간 하이라이트) ──
    expr_lines = {e.get("line", -1) for e in _analysis.get("expressions", [])}
    expr_map = {e.get("line", -1): e for e in _analysis.get("expressions", [])}
    script_html = _build_script_html(auto_start, auto_end, expr_lines, expr_map)

    # 상태
    dur = _transcript_cache[min(auto_end - 1, len(_transcript_cache) - 1)]["end"] - _transcript_cache[auto_start - 1]["start"]
    status_html = (
        f"<div style='font-size:20px;font-weight:700;color:#065f46;'>"
        f"✅ {len(_transcript_cache)}개 문장 · {elapsed:.0f}초 · "
        f"{_video_meta.get('title', '')[:50]}</div>"
    )

    return status_html, expr_html, script_html, auto_start, auto_end, suggested_expr, suggested_kr


def _build_expression_cards_html() -> str:
    """핵심 표현 3개를 큰 카드로 렌더링."""
    expressions = _analysis.get("expressions", [])
    if not expressions:
        return "<p style='color:#9ca3af;font-size:18px;'>추천 표현 없음</p>"

    cards = []
    for j, rec in enumerate(expressions):
        en = rec.get("expression_en", "")
        ko = rec.get("expression_ko", "")
        sentence = rec.get("full_sentence", "")
        reason = rec.get("reason", "")
        line = rec.get("line", "")

        # 문장에서 표현 하이라이트
        if en and sentence:
            sentence_hl = sentence.replace(en, f"<b style='color:#7c3aed;text-decoration:underline;'>{en}</b>")
        else:
            sentence_hl = sentence

        cards.append(f"""
        <div class="expr-card">
            <span class="expr-badge">표현 {j+1}</span>
            <div class="expr-en">{en}</div>
            <div class="expr-ko">{ko}</div>
            <div class="expr-sentence">" {sentence_hl} " <span style="color:#a78bfa;">— 줄 {line}</span></div>
            <div class="expr-reason">💡 {reason}</div>
        </div>
        """)
    return "\n".join(cards)


def _build_script_html(auto_start: int, auto_end: int,
                       expr_lines: set, expr_map: dict) -> str:
    """스크립트를 한 줄씩 카드로 렌더링. 구간/표현 하이라이트."""
    html_parts = []

    # 구간 안내
    if auto_start and auto_end:
        dur = _transcript_cache[min(auto_end - 1, len(_transcript_cache) - 1)]["end"] - _transcript_cache[auto_start - 1]["start"]
        html_parts.append(
            f'<div class="range-info">'
            f'🎬 자동 선택 구간: <b>{auto_start}~{auto_end}줄</b> ({dur:.0f}초) '
            f'— 아래 보라색 배경 줄이 선택 구간입니다'
            f'</div><br>'
        )

    for i, seg in enumerate(_transcript_cache):
        line_num = i + 1
        en = seg["text"]
        ko = _kr_translations.get(en, "")
        ts = seg["start"]

        # CSS 클래스 결정
        classes = ["line-card"]
        if auto_start <= line_num <= auto_end:
            classes.append("in-range")
        if line_num in expr_lines:
            classes.append("highlight")

        # 표현 하이라이트
        en_display = en
        expr_badge = ""
        if line_num in expr_lines:
            expr_info = expr_map[line_num]
            expr_en = expr_info.get("expression_en", "")
            if expr_en and expr_en.lower() in en.lower():
                idx = en.lower().find(expr_en.lower())
                matched = en[idx:idx + len(expr_en)]
                en_display = en[:idx] + f'<span class="line-expr-mark">{matched}</span>' + en[idx + len(expr_en):]
            expr_badge = f' <span style="background:#7c3aed;color:#fff;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:700;margin-left:8px;">핵심 표현</span>'

        html_parts.append(
            f'<div class="{" ".join(classes)}">'
            f'  <span class="line-num">{line_num}</span>'
            f'  <span class="line-time">[{ts:.1f}s]</span>{expr_badge}<br>'
            f'  <div class="line-en">{en_display}</div>'
            f'  <div class="line-ko">{ko}</div>'
            f'</div>'
        )

    return "\n".join(html_parts)


# ─── 자동 구간 ────────────────────────────────────────────────────────

def _calc_clip_range(expression_info: dict, segments: list[dict], target_duration: float = 60.0) -> tuple[int, int]:
    expr_line = expression_info.get("line", 1) - 1
    expr_line = max(0, min(expr_line, len(segments) - 1))
    expr_ts = segments[expr_line]["start"]

    before_sec = target_duration * 0.4
    target_start_ts = max(expr_ts - before_sec, 0)

    start_idx = 0
    for i, seg in enumerate(segments):
        if seg["start"] >= target_start_ts:
            start_idx = i
            break
    if start_idx > expr_line:
        start_idx = max(0, expr_line - 3)

    start_ts = segments[start_idx]["start"]
    target_end_ts = start_ts + target_duration

    end_idx = start_idx
    for i in range(start_idx, len(segments)):
        if segments[i]["end"] <= target_end_ts + 5:
            end_idx = i
        else:
            break
    end_idx = max(end_idx, min(expr_line + 5, len(segments) - 1))

    actual_dur = segments[end_idx]["end"] - segments[start_idx]["start"]
    if actual_dur < 45 and end_idx < len(segments) - 1:
        for i in range(end_idx + 1, len(segments)):
            end_idx = i
            if segments[i]["end"] - segments[start_idx]["start"] >= 50:
                break
    elif actual_dur > 75:
        for i in range(end_idx, expr_line, -1):
            if segments[i]["end"] - segments[start_idx]["start"] <= 70:
                end_idx = i
                break

    return start_idx + 1, end_idx + 1


# ─── LLM 분석 ────────────────────────────────────────────────────────

def _analyze_all(segments):
    from src.analyzer.llm_client import chat as llm_chat

    lines = [seg["text"] for seg in segments]
    numbered = "\n".join(f"{i+1}. {l}" for i, l in enumerate(lines))

    prompt = f"""셀럽/유명인 인터뷰 스크립트를 분석해줘.

[절대 규칙]
- 한자 절대 사용 금지. 순한글만
- 자연스러운 구어체 한국어로 번역
- 모든 줄을 빠짐없이 번역

[스크립트]
{numbered}

아래 JSON으로만 응답:
{{
  "summary": "이 인터뷰의 주요 내용 3줄 요약 (순한글)",
  "translations": [
    {{"line": 1, "ko": "한국어 번역"}},
    ...모든 줄 번역...
  ],
  "expressions": [
    {{
      "line": 줄번호,
      "expression_en": "핵심 영어 표현 (동사구/숙어/원어민 표현, 2-5단어)",
      "expression_ko": "한국어 뜻 (간결하게, 10자 이내)",
      "full_sentence": "해당 표현이 사용된 문장 전체 (자막 원문 그대로)",
      "reason": "왜 이 표현이 학습 가치가 높은지 (1줄)",
      "suggested_start": 해당 줄 3줄 전 번호,
      "suggested_end": 해당 줄 5줄 후 번호
    }}
  ]
}}

[핵심 표현 선택 기준 - 반드시 아래 유형만]
1. 동사구 (phrasal verb): get through, pull off, come up with 등
2. 숙어/관용 표현 (idiom): at the end of the day, break the ice 등
3. 원어민 표현 (native expression): 교과서에 없지만 원어민이 자주 쓰는 표현
- 정확히 3개 추천
- 가장 학습 가치가 높은 것 먼저
- 단순 단어(명사/형용사 단독)는 제외, 반드시 구(phrase) 단위"""

    raw = llm_chat([
        {"role": "system", "content": "영한 번역가 겸 영어표현 전문가. JSON만 응답. 모든 줄 빠짐없이 번역. 한자 절대 금지, 순한글만."},
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

    translations = {}
    analysis = {"summary": "", "expressions": []}

    try:
        data = json.loads(text)
        analysis["summary"] = data.get("summary", "")
        for item in data.get("translations", []):
            idx = item.get("line", 0) - 1
            if 0 <= idx < len(lines):
                translations[lines[idx]] = item.get("ko", "")
        analysis["expressions"] = data.get("expressions", [])
    except json.JSONDecodeError:
        pass

    return translations, analysis


# ─── Step 3: 숏폼 생성 ────────────────────────────────────────────────

def generate_short(
    start_line: int, end_line: int,
    expression: str, korean_meaning: str,
    kr_font_size: int,
    progress=gr.Progress(),
):
    global _transcript_cache, _video_meta, _video_path, _kr_translations, _analysis

    if not _video_path or not _video_path.exists():
        import time as _t
        for _ in range(30):
            if _video_path and _video_path.exists():
                break
            _t.sleep(2)
        if not _video_path or not _video_path.exists():
            return "영상 다운로드 대기 중... 잠시 후 다시 시도하세요.", None

    si, ei = int(start_line) - 1, int(end_line) - 1
    if si < 0 or ei >= len(_transcript_cache) or si > ei:
        return f"줄 번호 오류 (1~{len(_transcript_cache)})", None

    clip_segs = _transcript_cache[si:ei + 1]
    cs, ce = clip_segs[0]["start"], clip_segs[-1]["end"]

    sub_tr = [{"en": s["text"], "ko": _kr_translations.get(s["text"], "")} for s in clip_segs]

    expressions_list = []
    for expr_info in _analysis.get("expressions", []):
        expr_en = expr_info.get("expression_en", "")
        expr_ko = expr_info.get("expression_ko", "")
        if not expr_en:
            continue
        for seg in clip_segs:
            if expr_en.lower() in seg["text"].lower():
                expressions_list.append({
                    "expression_en": expr_en, "expression_ko": expr_ko,
                    "start": seg["start"], "end": seg["end"],
                })
                break

    expr_s, expr_e = cs, cs + 3
    if expression.strip():
        for seg in clip_segs:
            if expression.lower() in seg["text"].lower():
                expr_s, expr_e = seg["start"], seg["end"]
                break

    highlight = {
        "clip_start": cs, "clip_end": ce,
        "expression": expression, "expression_sentence": "",
        "expr_start": expr_s, "expr_end": expr_e,
        "korean_meaning": korean_meaning,
        "example": "",
        "subtitle_translations": sub_tr,
        "expressions": expressions_list,
    }

    progress(0.5, desc="숏폼 편집 중...")
    from src.editor.clip_extractor import create_shorts
    srt = settings.transcripts_dir / f"{_video_meta['video_id']}.srt"
    results = create_shorts(_video_path, srt, [highlight], video_info=_video_meta)
    progress(1.0, desc="완료!")

    if not results:
        return "생성 실패.", None
    return f"✅ 완료: {results[0].parent.name}/{results[0].name}", str(results[0])


# ─── Step 5: 메타데이터 ──────────────────────────────────────────────

def generate_metadata_ui(progress=gr.Progress()):
    if not _analysis or not _video_meta:
        return "먼저 스크립트를 로드하세요.", "", ""

    progress(0.3, desc="메타데이터 생성 중...")
    from src.analyzer.metadata_generator import generate_metadata

    first_expr = _analysis.get("expressions", [{}])[0] if _analysis.get("expressions") else {}
    celebrity = _extract_celebrity_from_meta()
    show_name = _extract_show_from_meta()

    meta = generate_metadata(
        expression_en=first_expr.get("expression_en", ""),
        expression_ko=first_expr.get("expression_ko", ""),
        celebrity=celebrity,
        show_name=show_name,
        summary=_analysis.get("summary", ""),
        full_title=_video_meta.get("title", ""),
    )

    progress(1.0, desc="완료!")
    return meta["title"], meta["description"], ", ".join(meta["tags"])


def _extract_celebrity_from_meta() -> str:
    if not _video_meta:
        return ""
    title = _video_meta.get("title", "")
    for sep in [" with ", " w/ ", " ft. ", " feat. "]:
        if sep in title:
            return title.split(sep, 1)[1].split(" |")[0].split(" -")[0].strip()
    if " Interview" in title:
        return title.split(" Interview")[0].strip()
    words = title.split(" ")
    stop_words = {"Answers", "Plays", "Takes", "Reveals", "Opens", "Tries", "Does", "Reacts", "Goes", "Joins", "on", "at", "in"}
    name_parts = []
    for w in words:
        if w in stop_words:
            break
        name_parts.append(w)
    return " ".join(name_parts).strip()[:30]


def _extract_show_from_meta() -> str:
    if not _video_meta:
        return "Talk Show"
    channel = _video_meta.get("channel", "")
    for name in ["Tonight Show", "Graham Norton", "Jimmy Kimmel", "Ellen", "Hot Ones", "WIRED", "C-SPAN"]:
        if name in channel:
            return name
    return channel[:20] if channel else "Talk Show"


# ─── UI ───────────────────────────────────────────────────────────────

with gr.Blocks(title="YouTube Shorts Factory") as app:

    gr.HTML("<h1 style='text-align:center;font-size:36px;font-weight:900;margin:20px 0 4px;'>🎬 YouTube Shorts Factory</h1>")
    gr.HTML("<p style='text-align:center;color:#6b7280;font-size:16px;margin-bottom:24px;'>영어 인터뷰 → 핵심 표현 추출 → 60초 숏폼 자동 생성</p>")

    # ── Step 1 ──
    gr.HTML("<div class='section-title'><span class='section-num'>1</span>영상 검색</div>")
    with gr.Row():
        keyword = gr.Textbox(label="검색어", placeholder="Jennie interview, Elon Musk podcast", scale=4, elem_classes=["gr-textbox"])
        search_btn = gr.Button("🔍 검색", variant="primary", scale=1)
    search_radio = gr.Radio(choices=[], label="검색 결과", type="value")
    with gr.Row():
        url_input = gr.Textbox(label="YouTube URL (직접 입력 가능)", placeholder="https://www.youtube.com/watch?v=...", scale=4)
        load_btn = gr.Button("📝 스크립트 분석", variant="primary", scale=1)

    # ── Step 2 ──
    gr.HTML("<div class='section-title'><span class='section-num'>2</span>AI 분석 결과</div>")
    status_html = gr.HTML(value="")

    gr.HTML("<h3 style='font-size:22px;font-weight:800;margin:16px 0 8px;'>🔥 핵심 표현 TOP 3</h3>")
    expr_html = gr.HTML(value="<p style='color:#9ca3af;'>스크립트 로드 후 표시됩니다</p>")

    gr.HTML("<h3 style='font-size:22px;font-weight:800;margin:24px 0 8px;'>📜 전체 스크립트</h3>")
    script_html = gr.HTML(value="<p style='color:#9ca3af;'>스크립트 로드 후 표시됩니다</p>")

    # ── Step 3 ──
    gr.HTML("<div class='section-title'><span class='section-num'>3</span>숏폼 생성</div>")

    with gr.Row():
        start_num = gr.Number(label="시작 줄", value=1, precision=0, elem_classes=["gr-input"])
        end_num = gr.Number(label="끝 줄", value=10, precision=0, elem_classes=["gr-input"])
    with gr.Row():
        expr_input = gr.Textbox(label="메인 표현 (영어)", placeholder="예: get through")
        kr_input = gr.Textbox(label="한국어 뜻", placeholder="예: 극복하다")
    kr_slider = gr.Slider(20, 60, value=36, step=2, label="한국어 자막 크기")
    gen_btn = gr.Button("🎬 숏폼 생성", variant="primary", size="lg")

    # ── Step 4 ──
    gr.HTML("<div class='section-title'><span class='section-num'>4</span>결과 확인</div>")
    with gr.Row():
        result_box = gr.Textbox(label="상태", lines=2, interactive=False)
        result_video = gr.Video(label="생성된 숏폼")

    # ── Step 5 ──
    gr.HTML("<div class='section-title'><span class='section-num'>5</span>유튜브 제목 · 설명 · 해시태그</div>")
    meta_btn = gr.Button("✨ 자동 생성", variant="secondary")
    yt_title = gr.Textbox(label="유튜브 제목", interactive=True)
    yt_desc = gr.Textbox(label="설명 (해시태그 포함)", lines=6, interactive=True)
    yt_tags = gr.Textbox(label="태그 (쉼표 구분)", interactive=True)

    # ── 이벤트 ──
    search_btn.click(search_videos, keyword, search_radio)
    keyword.submit(search_videos, keyword, search_radio)
    search_radio.change(on_video_select, search_radio, url_input)
    load_btn.click(
        load_and_analyze, url_input,
        [status_html, expr_html, script_html, start_num, end_num, expr_input, kr_input],
    )
    gen_btn.click(
        generate_short,
        [start_num, end_num, expr_input, kr_input, kr_slider],
        [result_box, result_video],
    )
    meta_btn.click(generate_metadata_ui, [], [yt_title, yt_desc, yt_tags])


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, css=CUSTOM_CSS)
