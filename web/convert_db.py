"""
실제 saju-db JSON → 웹 서비스용 saju-db.js 변환
7,150 레코드 전체 연동
"""
import json
import os

DB_PATH = os.path.expanduser("~/Downloads/sohn_proj/saju-db/output/saju_db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "data", "saju-db.js")

# 궁합 DB의 키 불일치 보정 매핑
GOONGHAP_KEY_MAP = {
    "byung": "byeong", "gyung": "gyeong", "shin": "sin"
}

def normalize_goonghap_key(key):
    parts = key.split("_")
    return "_".join(str(GOONGHAP_KEY_MAP.get(p, p)) for p in parts)

def load_json(filename):
    with open(os.path.join(DB_PATH, filename), encoding="utf-8") as f:
        return json.load(f)

def build_js():
    # 1. 천간
    cheongan = load_json("01_cheongan.json")["cheongan"]

    # 2. 지지
    jiji = load_json("02_jiji.json")["jiji"]

    # 3. 오행 (상생 + 상극 + 과다부족)
    ohaeng_raw = load_json("03_ohaeng.json")
    ohaeng = {
        "sangsaeng": ohaeng_raw.get("sangsaeng", {}),
        "sanggeuk": ohaeng_raw.get("sanggeuk", {}),
        "ohaeng_excess": ohaeng_raw.get("ohaeng_excess", {}),
    }

    # 4. 일간조합
    ilgan_combo = load_json("04_ilgan_combo.json")["ilgan_combo"]

    # 5. 대운/세운 전체
    daeun_raw = load_json("05_daeun_seun.json")
    daeun = daeun_raw.get("daeun_cheongan", {})
    ilgan_daeun = daeun_raw.get("ilgan_daeun_combo", {})
    saeun = daeun_raw.get("saeun_60gap", {})

    # 6. 궁합 — 전체 카테고리 + 키 정규화
    goonghap_raw = load_json("06_goonghap.json")
    goonghap = {}
    # 일간 궁합
    ic = goonghap_raw.get("ilgan_compatibility", {})
    for k, v in ic.items():
        nk = normalize_goonghap_key(k)
        goonghap[nk] = v
    # 오행 궁합
    ohaeng_compat = goonghap_raw.get("ohaeng_compatibility", {})
    # 삼합/육합/충
    samhap = goonghap_raw.get("samhap", {})
    yukhap = goonghap_raw.get("yukhap", {})
    chung = goonghap_raw.get("chung", {})

    db = {
        "cheongan": cheongan,
        "jiji": jiji,
        "ohaeng": ohaeng,
        "ilgan_combo": ilgan_combo,
        "daeun": daeun,
        "ilgan_daeun": ilgan_daeun,
        "saeun": saeun,
        "goonghap": goonghap,
        "ohaeng_compat": ohaeng_compat,
        "samhap": samhap,
        "yukhap": yukhap,
        "chung": chung,
    }

    # 통계
    def count_versions(obj):
        total = 0
        if isinstance(obj, dict):
            if "versions" in obj:
                total += len(obj["versions"])
            else:
                for v in obj.values():
                    total += count_versions(v)
        return total

    stats = {}
    for name, data in db.items():
        stats[name] = count_versions(data)
    total = sum(stats.values())

    # JS 파일 생성
    js_content = f"/**\n * MỆnh — AI Tứ Trụ : 사주 해석 DB\n * 자동 생성 — convert_db.py\n * 총 {total:,}개 레코드\n */\nconst SAJU_DB = "
    js_content += json.dumps(db, ensure_ascii=False, indent=None, separators=(",", ":"))
    js_content += ";\n"

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"✅ 변환 완료: {OUT_PATH}")
    print(f"   총 레코드: {total:,}")
    for name, cnt in stats.items():
        print(f"   - {name}: {cnt:,}")
    print(f"   파일 크기: {size_kb:.1f} KB")

if __name__ == "__main__":
    build_js()
