"""
사주 DB 구어체 변환 스크립트
- ko: 문어체 → 자연스러운 구어체
- vi: 직역체 → 두괄식 + 친근한 베트남어
"""
import json, os, re, copy

DB_PATH = os.path.expanduser("~/Downloads/sohn_proj/saju-db/output/saju_db")
OUT_PATH = DB_PATH  # 원본 덮어쓰기 (백업 먼저)
BACKUP_SUFFIX = ".bak"

# ============================================================
# 한국어 구어체 변환 패턴
# ============================================================
KO_PATTERNS = [
    # 문어체 종결 → 구어체
    (r'입니다\.', '이에요.'),
    (r'입니다, ', '이에요. '),
    (r'습니다\.', '어요.'),
    (r'됩니다\.', '돼요.'),
    (r'있습니다\.', '있어요.'),
    (r'없습니다\.', '없어요.'),
    (r'됩니다\.', '돼요.'),
    (r'합니다\.', '해요.'),
    (r'옵니다\.', '와요.'),
    (r'집니다\.', '져요.'),
    (r'납니다\.', '나요.'),
    (r'갑니다\.', '가요.'),
    (r'줍니다\.', '줘요.'),
    (r'냅니다\.', '내요.'),
    (r'봅니다\.', '봐요.'),
    (r'십니다\.', '세요.'),

    # ~ㅂ니다 → ~요 (일반)
    (r'([가-힣])ㅂ니다', r'\1요'),

    # 문어체 연결 → 구어체
    (r'지닙니다', '지니고 있어요'),
    (r'을 지니고', '이 있고'),
    (r'를 지니고', '가 있고'),
    (r'을 갖추고', '이 있고'),
    (r'를 갖추고', '가 있고'),
    (r'에 해당합니다', '에 가까워요'),
    (r'에 해당하는', '에 해당하는'),
    (r'라 할 수 있습니다', '라고 할 수 있어요'),
    (r'라 할 수 있다', '라고 할 수 있어요'),
    (r'것이 중요합니다', '게 중요해요'),
    (r'것이 필요합니다', '게 필요해요'),
    (r'하여야 합니다', '하는 게 좋아요'),
    (r'해야 합니다', '하는 게 좋아요'),
    (r'이 우려됩니다', '일 수 있으니 조심하세요'),
    (r'을 의미합니다', '라는 뜻이에요'),
    (r'를 의미합니다', '라는 뜻이에요'),
    (r'을 상징합니다', '을 나타내요'),
    (r'를 상징합니다', '를 나타내요'),
    (r'뛰어납니다', '뛰어나요'),
    (r'풍부합니다', '풍부해요'),
    (r'강합니다', '강해요'),
    (r'약합니다', '약해요'),
    (r'높습니다', '높아요'),
    (r'낮습니다', '낮아요'),
    (r'많습니다', '많아요'),
    (r'적습니다', '적어요'),
    (r'좋습니다', '좋아요'),
    (r'나쁩니다', '나빠요'),
    (r'큽니다', '커요'),
    (r'작습니다', '작아요'),
    (r'깊습니다', '깊어요'),
    (r'넓습니다', '넓어요'),

    # ~하며 → ~하고
    (r'하며,', '하고,'),
    (r'하며 ', '하고 '),
    (r'이며,', '이고,'),
    (r'이며 ', '이고 '),
    (r'으며,', '고,'),
    (r'으며 ', '고 '),

    # 한자 과다 제거 — 첫 등장 외 괄호 한자 축소
    # (한자는 첫 등장 시만 유지, 반복 시 제거는 수동으로)

    # 전문용어 → 쉬운 말
    (r'편재\(偏財\)', '예상 밖 재물'),
    (r'정재\(正財\)', '안정적 재물'),
    (r'편관\(偏官\)', '도전적 에너지'),
    (r'정관\(正官\)', '안정적 직업운'),
    (r'식신\(食神\)', '표현력과 창의력'),
    (r'상관\(傷官\)', '자유로운 기질'),
    (r'비견\(比肩\)', '동료/경쟁 관계'),
    (r'겁재\(劫財\)', '경쟁적 에너지'),
    (r'편인\(偏印\)', '독특한 사고방식'),
    (r'정인\(正印\)', '학문적 재능'),
    (r'投出', '드러남'),
    (r'투출', '드러남'),
    (r'통근\(通根\)', '뿌리가 깊은'),
]

# 2차 변환: 남은 ~ㅂ니다/~습니다 처리
KO_FINAL_PATTERNS = [
    (r'([가-힣]+)니다\.', lambda m: m.group(0).replace('니다.', '어요.')),
]

def transform_ko(text):
    result = text
    for pattern, replacement in KO_PATTERNS:
        if callable(replacement):
            result = re.sub(pattern, replacement, result)
        else:
            result = re.sub(pattern, replacement, result)

    # 마지막 남은 ~ㅂ니다 → ~요 (정규식 기반)
    result = re.sub(r'ㅂ니다\.', '요.', result)
    result = re.sub(r'ㅂ니다, ', '요. ', result)
    result = re.sub(r'습니다\.', '어요.', result)
    result = re.sub(r'습니다, ', '어요. ', result)

    return result

# ============================================================
# 베트남어 변환 패턴
# ============================================================
VI_PATTERNS = [
    # 격식체 → 친근체
    (r'^Theo phân tích', 'Dựa vào lá số của bạn,'),
    (r'Quý khách', 'Bạn'),
    (r'của quý vị', 'của bạn'),

    # 두괄식 변환 보조 (문장 재배치는 어려우므로 톤 변환 위주)
    (r'cho thấy rằng', 'cho thấy'),
    (r'điều này cho thấy', '— điều này có nghĩa là'),
    (r'Tuy nhiên,', 'Nhưng'),
    (r'Mặc dù vậy,', 'Dù vậy,'),
    (r'Ngoài ra,', 'Thêm nữa,'),
    (r'Vì vậy,', 'Nên'),

    # 친근 감탄사 추가 (문장 끝)
    (r'(\.)(\s*)$', r' đó.\2'),  # 마지막 문장에 "đó" 추가

    # 직역 패턴 수정
    (r'sở hữu khả năng', 'có khả năng'),
    (r'thiên bẩm', 'bẩm sinh'),
    (r'được ban phú', 'có sẵn'),
    (r'mang trong mình', 'có'),
    (r'tượng trưng cho', 'đại diện cho'),
    (r'hàm chứa', 'chứa đựng'),
]

def transform_vi(text):
    result = text
    for pattern, replacement in VI_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result

# ============================================================
# JSON 처리
# ============================================================
def process_versions(versions):
    for v in versions:
        if 'ko' in v and v['ko']:
            v['ko'] = transform_ko(v['ko'])
        if 'vi' in v and v['vi']:
            v['vi'] = transform_vi(v['vi'])
    return versions

def process_dict(obj):
    """재귀적으로 versions 배열을 찾아서 변환"""
    if isinstance(obj, dict):
        if 'versions' in obj and isinstance(obj['versions'], list):
            obj['versions'] = process_versions(obj['versions'])
        else:
            for k, v in obj.items():
                if k == 'meta' or k == '_meta':
                    continue
                process_dict(v)
    elif isinstance(obj, list):
        for item in obj:
            process_dict(item)
    return obj

def process_file(filename):
    filepath = os.path.join(DB_PATH, filename)
    backup_path = filepath + BACKUP_SUFFIX

    # 백업
    if not os.path.exists(backup_path):
        with open(filepath, 'r', encoding='utf-8') as f:
            backup_data = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_data)
        print(f"  백업: {backup_path}")

    # 로드
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 변환
    data = process_dict(data)

    # 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 레코드 수 카운트
    count = 0
    def count_v(o):
        nonlocal count
        if isinstance(o, dict):
            if 'versions' in o:
                count += len(o['versions'])
            else:
                for v in o.values():
                    count_v(v)
    count_v(data)

    return count

# ============================================================
# 메인
# ============================================================
if __name__ == "__main__":
    files = [
        '01_cheongan.json',
        '02_jiji.json',
        '03_ohaeng.json',
        '04_ilgan_combo.json',
        '05_daeun_seun.json',
        '06_goonghap.json',
    ]

    print("=" * 50)
    print("  사주 DB 구어체 변환")
    print("=" * 50)

    total = 0
    for f in files:
        print(f"\n처리 중: {f}")
        count = process_file(f)
        total += count
        print(f"  ✅ {f} 완료: {count:,}개 레코드 변환")

    print("\n" + "=" * 50)
    print(f"  전체 완료: {total:,}개 레코드")
    print("=" * 50)
