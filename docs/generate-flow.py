#!/usr/bin/env python3
"""
MỆnh App Flow Diagram — Celestial Cartography
Generates a comprehensive flowchart as PNG
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 2400
img = Image.new('RGB', (W, H), '#FEFCFA')
draw = ImageDraw.Draw(img)

# Fonts
FONT_DIR = '/System/Library/Fonts'
try:
    font_b = ImageFont.truetype(f'{FONT_DIR}/AppleSDGothicNeo.ttc', 22, index=3)  # Bold
    font_m = ImageFont.truetype(f'{FONT_DIR}/AppleSDGothicNeo.ttc', 16, index=0)  # Regular
    font_s = ImageFont.truetype(f'{FONT_DIR}/AppleSDGothicNeo.ttc', 13, index=0)
    font_t = ImageFont.truetype(f'{FONT_DIR}/AppleSDGothicNeo.ttc', 32, index=3)  # Title
    font_xs = ImageFont.truetype(f'{FONT_DIR}/AppleSDGothicNeo.ttc', 11, index=0)
except:
    font_b = font_m = font_s = font_t = font_xs = ImageFont.load_default()

# Colors
PURPLE = '#667EEA'
DEEP_PURPLE = '#764BA2'
PINK = '#EC4899'
AMBER = '#F59E0B'
GREEN = '#10B981'
BLUE = '#3B82F6'
RED = '#EF4444'
GRAY = '#94A3B8'
LIGHT_GRAY = '#F1F5F9'
DARK = '#1E293B'
WHITE = '#FFFFFF'
CREAM = '#FEFCFA'

def rounded_rect(x, y, w, h, r, fill, outline=None, width=1):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=outline, width=width)

def text_center(x, y, w, text, font, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + (w - tw) / 2, y), text, font=font, fill=color)

def arrow_down(x, y1, y2, color=GRAY, width=2):
    draw.line([(x, y1), (x, y2)], fill=color, width=width)
    draw.polygon([(x-5, y2-8), (x+5, y2-8), (x, y2)], fill=color)

def arrow_right(x1, x2, y, color=GRAY, width=1):
    draw.line([(x1, y), (x2, y)], fill=color, width=width)
    draw.polygon([(x2-6, y-4), (x2-6, y+4), (x2, y)], fill=color)

def node(x, y, w, h, text, fill=WHITE, border=PURPLE, font=font_m, text_color=DARK, subtitle=None, icon=None):
    rounded_rect(x, y, w, h, 12, fill, border, 2)
    ty = y + 8 if subtitle else y + (h - 18) / 2
    if icon:
        draw.text((x + 12, ty), icon, font=font_m, fill=text_color)
        draw.text((x + 32, ty), text, font=font, fill=text_color)
    else:
        text_center(x, ty, w, text, font, text_color)
    if subtitle:
        text_center(x, ty + 22, w, subtitle, font_xs, GRAY)

def db_node(x, y, name, count, color=PURPLE):
    w, h = 140, 36
    rounded_rect(x, y, w, h, 8, '#F5F3FF', color, 1)
    draw.text((x + 8, y + 4), f'{name}', font=font_xs, fill=color)
    draw.text((x + 8, y + 18), f'{count}개', font=font_xs, fill=GRAY)

# ====== HEADER ======
rounded_rect(0, 0, W, 100, 0, DEEP_PURPLE)
text_center(0, 18, W, 'MỆnh — 전체 기능 흐름도', font_t, WHITE)
text_center(0, 60, W, 'AI 사주 분석 서비스 | 총 DB 2,945 레코드', font_s, '#C4B5FD')

# ====== ENTRY ======
y = 120
text_center(0, y, W, '사용자 진입', font_b, DARK)
y += 32

# Input box
node(350, y, 500, 50, '이름 / 생년월일 / 시간 / 성별 입력', fill='#F5F3FF', border=PURPLE)
y += 58
arrow_down(600, y, y+25, PURPLE, 2)
y += 30

# Button
rounded_rect(430, y, 340, 44, 22, PURPLE)
text_center(430, y+10, 340, '내 사주 보기 →', font_b, WHITE)
y += 52
arrow_down(600, y, y+30, PURPLE, 3)
y += 38

# ====== RESULT SCREEN ======
# Section header
rounded_rect(80, y, W-160, 36, 8, DEEP_PURPLE)
text_center(80, y+6, W-160, '결과 메인 화면 (스크롤)', font_b, WHITE)
y += 50

# ① 사주원국
node(150, y, 900, 50, '① 사주원국 (2×4 매트릭스 + 오행 색상)', fill='#FFF8E1', border=AMBER, font=font_b, text_color=DARK)
db_node(80, y+8, 'DB_ILGAN', '50', AMBER)
y += 60
arrow_down(600, y, y+15, GRAY)
y += 20

# ② 전반적 풀이
node(150, y, 900, 45, '② 전반적 사주 풀이 "OOO님은 이런 사람이에요"', fill='#F5F3FF', border=PURPLE)
db_node(80, y+5, 'DB_INTRO', '50', PURPLE)
y += 55
arrow_down(600, y, y+15, GRAY)
y += 20

# ③ 연대별
node(150, y, 900, 80, '③ 연대별 인생 흐름', fill='#ECFDF5', border=GREEN, subtitle='')
# Decade labels
decades = ['10대', '20대', '30대', '40대', '50대+']
dx = 180
for i, d in enumerate(decades):
    rounded_rect(dx + i*160, y+30, 130, 26, 6, WHITE, GREEN, 1)
    text_center(dx + i*160, y+34, 130, d, font_s, GREEN)
# Expand button
rounded_rect(350, y+62, 500, 24, 6, '#D1FAE5')
text_center(350, y+64, 500, '더 자세히 알아보기 ▼  →  각 연대 상세 설명 확장', font_xs, '#059669')
db_node(80, y+20, 'DB_DECADE', '100', GREEN)
y += 95
arrow_down(600, y, y+15, GRAY)
y += 20

# ④ 오늘의 한 줄
node(150, y, 900, 40, '④ 오늘의 한 줄', fill='#EFF6FF', border=BLUE)
db_node(80, y+3, 'DB_TODAY', '420', BLUE)
y += 50
arrow_down(600, y, y+15, GRAY)
y += 20

# ====== 운세 3종 ======
fortune_types = [
    ('⑤ 오늘의 운세', '☀️', BLUE, 'daily'),
    ('⑥ 이번달 운세', '🌙', AMBER, 'monthly'),
    ('⑦ 올해의 운세', '⭐', DEEP_PURPLE, 'yearly'),
]

for fi, (flabel, ficon, fcolor, fperiod) in enumerate(fortune_types):
    # Fortune header
    rounded_rect(150, y, 900, 36, 8, fcolor)
    text_center(150, y+6, 900, f'{flabel}', font_b, WHITE)
    y += 44

    # Overview
    rounded_rect(180, y, 840, 32, 8, WHITE, fcolor, 1)
    text_center(180, y+5, 840, '전체 설명 (Overview)', font_m, fcolor)
    y += 38

    # 5 topics
    topics_data = [
        ('❤️ 연애', 'love', '#EC4899'),
        ('💼 직업', 'career', '#3B82F6'),
        ('💰 재물', 'money', '#F59E0B'),
        ('🪞 자기관리', 'self', '#10B981'),
        ('🌏 인생', 'general', '#764BA2'),
    ]

    for ti, (tname, tid, tcolor) in enumerate(topics_data):
        tx = 180 + ti * 168
        rounded_rect(tx, y, 160, 30, 8, WHITE, tcolor, 1)
        text_center(tx, y+5, 160, tname, font_s, tcolor)
    y += 36

    # Q&A arrow
    rounded_rect(250, y, 700, 24, 6, '#F5F3FF')
    text_center(250, y+3, 700, '각 분야 → [💬 더 알아보기] → Q&A 대화형 체인 (최대 10단계)', font_xs, PURPLE)
    y += 32

    # DB labels for first fortune only
    if fi == 0:
        db_node(80, y-90, 'DB_OVERVIEW', '30', fcolor)
        db_node(80, y-55, 'DB_AREA', '150', fcolor)

    # Cheer
    rounded_rect(400, y, 400, 22, 6, '#FDF2F8', PINK, 1)
    text_center(400, y+2, 400, '응원 마무리 메시지', font_xs, PINK)
    if fi == 0:
        db_node(80, y-20, 'DB_CHEER', '25', PINK)
    y += 30

    if fi < 2:
        arrow_down(600, y, y+20, GRAY, 2)
        y += 25

# ====== Q&A CHAIN DETAIL ======
y += 30
rounded_rect(80, y, W-160, 36, 8, '#1E293B')
text_center(80, y+6, W-160, 'Q&A 대화형 체인 흐름 (분야별)', font_b, WHITE)
y += 50

# Q&A flow
qa_steps = [
    ('AI 답변 카드', '300자 설명', PURPLE, 180),
    ('질문 선택', '[질문 1]  [질문 2]  [질문 3]', '#E8E0FF', 140),
    ('AI 답변 카드', '질문 기반 상세 답변', PURPLE, 180),
    ('질문 선택', '[질문 4]  [질문 5]', '#E8E0FF', 140),
    ('AI 답변 카드', '더 깊은 답변', PURPLE, 180),
    ('...반복 (최대 10단계)', '', GRAY, 100),
]

for i, (label, sub, color, w) in enumerate(qa_steps):
    bx = 200 + i * 145
    by = y
    if i % 2 == 0:  # Answer
        rounded_rect(bx, by, 135, 55, 10, '#F5F3FF', PURPLE, 2)
        text_center(bx, by+8, 135, label, font_xs, PURPLE)
        text_center(bx, by+25, 135, sub, font_xs, GRAY)
    else:  # Questions
        rounded_rect(bx, by, 135, 55, 10, '#FFFBEB', AMBER, 1)
        text_center(bx, by+8, 135, label, font_xs, AMBER)
        text_center(bx, by+25, 135, sub, font_xs, '#666')

    if i < len(qa_steps) - 1:
        arrow_right(bx + 135, bx + 145, by + 27, GRAY, 1)

db_node(80, y+10, 'DB_QA', '1,500', PURPLE)

y += 70

# Navigation buttons
nav_items = [
    ('다시 알아보기', '해당 분야 처음으로', PURPLE),
    ('다른 분야 알아보기', '분야 선택 화면으로', BLUE),
    ('접기', '콘텐츠 축소', GRAY),
]
nx = 200
for label, sub, color in nav_items:
    rounded_rect(nx, y, 260, 40, 10, WHITE, color, 2)
    draw.text((nx + 12, y + 5), label, font=font_m, fill=color)
    draw.text((nx + 12, y + 23), sub, font=font_xs, fill=GRAY)
    nx += 280

# ====== DB LAYER ======
y += 65
rounded_rect(80, y, W-160, 36, 8, '#0F172A')
text_center(80, y+6, W-160, 'DB 레이어 (총 2,945 레코드)', font_b, WHITE)
y += 50

db_items = [
    ('DB_INTRO', '50', '공감 도입', '#8B5CF6'),
    ('DB_ILGAN', '50', '성격 풀이', '#D97706'),
    ('DB_COMBO', '120', '시기 풀이', '#059669'),
    ('DB_TODAY', '420', '오늘 한 줄', '#2563EB'),
    ('DB_CHEER', '25', '응원 마무리', '#DB2777'),
    ('DB_DECADE', '100', '연대별 흐름', '#059669'),
    ('DB_OVERVIEW', '30', '운세 전체', '#7C3AED'),
    ('DB_AREA', '150', '분야별 설명', '#7C3AED'),
    ('DB_QA', '1,500', 'Q&A 체인', '#7C3AED'),
    ('DB_COMPAT', '500', '궁합 사유', '#DB2777'),
]

cols = 5
for i, (name, count, desc, color) in enumerate(db_items):
    col = i % cols
    row = i // cols
    bx = 100 + col * 210
    by = y + row * 60
    rounded_rect(bx, by, 195, 50, 10, WHITE, color, 2)
    draw.text((bx + 10, by + 5), name, font=font_s, fill=color)
    draw.text((bx + 10, by + 24), f'{count}개 — {desc}', font=font_xs, fill=GRAY)

y += 140

# ====== FOOTER ======
rounded_rect(0, y, W, 50, 0, DEEP_PURPLE)
text_center(0, y+12, W, 'MỆnh © 2026 — AI Saju Analysis Service', font_s, '#C4B5FD')

# Save
out_path = '/Users/kyunghwansohn/Projects/saju-ai-service/docs/menh-flow-diagram.png'
img = img.crop((0, 0, W, y + 50))
img.save(out_path, 'PNG', quality=95)
print(f'Saved: {out_path} ({img.size[0]}x{img.size[1]})')
