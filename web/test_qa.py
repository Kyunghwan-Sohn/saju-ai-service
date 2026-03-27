"""
MỆnh 사주 서비스 전체 QA 테스트
Playwright 기반 — 모든 화면 + 기능 + 데이터 검증
"""
from playwright.sync_api import sync_playwright
import json, sys, os

BASE = "http://localhost:8080"
SCREENSHOTS = "/tmp/menh_qa"
os.makedirs(SCREENSHOTS, exist_ok=True)

results = []

def log(test_name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((test_name, passed, detail))
    print(f"  {'✅' if passed else '❌'} {test_name}" + (f" — {detail}" if detail else ""))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 470, "height": 900})

    # ============================================================
    # TEST 1: 홈 화면 로드
    # ============================================================
    print("\n=== TEST 1: 홈 화면 ===")
    page.goto(BASE)
    page.wait_for_load_state("networkidle")
    page.screenshot(path=f"{SCREENSHOTS}/01_home.png", full_page=True)

    title = page.title()
    log("페이지 타이틀", "MỆnh" in title, title)

    header = page.locator("h1").text_content()
    log("헤더 MỆnh 표시", "MỆnh" in header, header)

    fortune_card = page.locator(".daily-fortune-card")
    log("오늘의 운세 카드 존재", fortune_card.count() > 0)

    quick_items = page.locator("#screen-home .quick-item")
    log("퀵메뉴 15개 (운세3+영역12)", quick_items.count() == 15, f"실제: {quick_items.count()}")

    nav_items = page.locator(".nav-item")
    log("바텀 네비 4개", nav_items.count() == 4, f"실제: {nav_items.count()}")

    # ============================================================
    # TEST 2: 사주 입력 화면 이동
    # ============================================================
    print("\n=== TEST 2: 사주 입력 화면 ===")
    page.locator(".nav-item[data-screen='screen-saju']").click()
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SCREENSHOTS}/02_saju_input.png", full_page=True)

    saju_screen = page.locator("#screen-saju")
    log("사주 화면 표시", saju_screen.is_visible())

    year_input = page.locator("#birth-year")
    log("출생년도 입력 존재", year_input.is_visible())

    hour_select = page.locator("#birth-hour")
    hour_options = hour_select.locator("option")
    hour_count = hour_options.count()
    log("출생 시간 옵션 25개 (모름+24시간)", hour_count == 25, f"실제: {hour_count}")

    # 시간 옵션에 동물 이름 없는지 확인
    all_options = [hour_options.nth(i).text_content() for i in range(hour_count)]
    has_animal = any(animal in opt for opt in all_options for animal in ["자시","축시","인시","묘시","쥐","소","호랑이","Tý","Sửu"])
    log("출생 시간에 동물/지지명 없음", not has_animal, f"첫3개: {all_options[:3]}")

    # ============================================================
    # TEST 3: 사주 풀이 실행 (1995.3.15 14시)
    # ============================================================
    print("\n=== TEST 3: 사주 풀이 실행 ===")
    page.locator("#birth-year").fill("1995")
    page.locator("#birth-month").select_option("3")
    page.locator("#birth-day").fill("15")
    page.locator("#birth-hour").select_option("14")

    page.locator("#saju-form button[type='submit']").click()
    page.wait_for_timeout(1500)
    page.screenshot(path=f"{SCREENSHOTS}/03_saju_result.png", full_page=True)

    result_section = page.locator("#result-section")
    log("결과 섹션 표시", result_section.is_visible())

    # 사주원국 테이블 확인
    saju_table = page.locator(".saju-table-wrap")
    log("사주원국 테이블 존재", saju_table.count() > 0)

    saju_header = page.locator(".saju-header-cell")
    log("사주 헤더 4열", saju_header.count() == 4, f"실제: {saju_header.count()}")

    saju_rows = page.locator(".saju-row")
    log("사주 십성+천간+지지 3행", saju_rows.count() == 3, f"실제: {saju_rows.count()}")

    # 사주원국 정확도 검증 (1995.3.15 14시 = 乙亥 己卯 乙巳 癸未)
    hanja_cells = page.locator(".saju-cell .hanja")
    all_hanja = [hanja_cells.nth(i).text_content().strip() for i in range(hanja_cells.count())]
    print(f"    사주원국 한자: {all_hanja}")

    # 천간행: 癸(시) 乙(일) 己(월) 乙(년) / 지지행: 未(시) 巳(일) 卯(월) 亥(년)
    expected_stems = ["癸", "乙", "己", "乙"]
    expected_branches = ["未", "巳", "卯", "亥"]
    actual_stems = all_hanja[0:4] if len(all_hanja) >= 8 else []
    actual_branches = all_hanja[4:8] if len(all_hanja) >= 8 else []

    log("천간 정확도 (癸乙己乙)", actual_stems == expected_stems, f"실제: {actual_stems}")
    log("지지 정확도 (未巳卯亥)", actual_branches == expected_branches, f"실제: {actual_branches}")

    # 오행 분포 차트
    ohaeng_inline = page.locator("#ohaeng-container div[style*='display:flex']")
    log("오행 인라인 표시", ohaeng_inline.count() >= 1, f"실제: {ohaeng_inline.count()}")

    # 해석 카드
    reading_cards = page.locator(".reading-card")
    reading_count = reading_cards.count()
    log("해석 카드 1개 이상", reading_count >= 1, f"실제: {reading_count}개")

    # 해석 텍스트에 구어체 확인 (이에요/어요/해요 포함)
    if reading_count > 0:
        first_reading = reading_cards.nth(0).locator(".reading-text").text_content()
        has_casual = any(w in first_reading for w in ["이에요","어요","해요","예요","돼요","거든요","죠"])
        log("해석 텍스트 구어체", has_casual, f"텍스트 앞부분: {first_reading[:60]}...")

    # 주제별 바로가기
    shortcuts = page.locator("#topic-shortcuts")
    log("주제별 바로가기 표시", shortcuts.is_visible())

    # 공유 카드
    share_card = page.locator("#share-card")
    log("공유 카드 표시", share_card.is_visible())

    page.screenshot(path=f"{SCREENSHOTS}/03_saju_result_full.png", full_page=True)

    # ============================================================
    # TEST 4: 궁합 화면
    # ============================================================
    print("\n=== TEST 4: 궁합 화면 ===")
    page.locator(".nav-item[data-screen='screen-compat']").click()
    page.wait_for_timeout(500)

    compat_screen = page.locator("#screen-compat")
    log("궁합 화면 표시", compat_screen.is_visible())

    page.locator("#compat-year1").fill("1995")
    page.locator("#compat-month1").fill("3")
    page.locator("#compat-day1").fill("15")
    page.locator("#compat-year2").fill("1997")
    page.locator("#compat-month2").fill("8")
    page.locator("#compat-day2").fill("22")

    page.locator("#compat-form button[type='submit']").click()
    page.wait_for_timeout(1000)
    page.screenshot(path=f"{SCREENSHOTS}/04_compat.png", full_page=True)

    compat_result = page.locator("#compat-result")
    log("궁합 결과 표시", compat_result.is_visible())

    score_circle = page.locator(".score-circle")
    if score_circle.count() > 0:
        score = (score_circle.text_content() or "").strip()
        is_number = score.isdigit()
        log("궁합 점수 숫자 표시", is_number, f"점수: {score}")

    # ============================================================
    # TEST 5: 오행 가이드 화면
    # ============================================================
    print("\n=== TEST 5: 오행 가이드 ===")
    page.locator(".nav-item[data-screen='screen-home']").click()
    page.wait_for_timeout(300)
    page.locator("text=오행").first.click()
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SCREENSHOTS}/05_ohaeng.png", full_page=True)

    ohaeng_screen = page.locator("#screen-ohaeng-guide")
    log("오행 가이드 화면 표시", ohaeng_screen.is_visible())

    # ============================================================
    # TEST 6: 프리미엄 화면
    # ============================================================
    print("\n=== TEST 6: 프리미엄 ===")
    page.locator(".nav-item[data-screen='screen-profile']").click()
    page.wait_for_timeout(300)
    page.locator("#screen-profile .mi-label:has-text('Premium')").click()
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SCREENSHOTS}/06_premium.png", full_page=True)

    plan_cards = page.locator(".plan-card")
    log("구독 플랜 3개", plan_cards.count() == 3, f"실제: {plan_cards.count()}")

    featured = page.locator(".plan-card.featured")
    log("추천 플랜 강조", featured.count() == 1)

    # ============================================================
    # TEST 7: 프로필 화면
    # ============================================================
    print("\n=== TEST 7: 프로필 ===")
    page.locator(".nav-item[data-screen='screen-profile']").click()
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SCREENSHOTS}/07_profile.png", full_page=True)

    profile_screen = page.locator("#screen-profile")
    log("프로필 화면 표시", profile_screen.is_visible())

    menu_items = page.locator(".menu-item")
    log("프로필 메뉴 7개", menu_items.count() == 7, f"실제: {menu_items.count()}")

    # ============================================================
    # TEST 8: 언어 전환 (한국어 → 베트남어)
    # ============================================================
    print("\n=== TEST 8: 언어 전환 ===")
    page.locator(".nav-item[data-screen='screen-home']").click()
    page.wait_for_timeout(300)

    page.locator("button[data-lang='vi']").click()
    page.wait_for_timeout(500)
    page.screenshot(path=f"{SCREENSHOTS}/08_vietnamese.png", full_page=True)

    fortune_text = page.locator("#dfc-text").text_content()
    has_vi = any(w in fortune_text for w in ["Hôm nay", "bạn", "năng lượng", "cơ hội"])
    log("베트남어 전환 확인", has_vi, f"텍스트: {fortune_text[:50]}...")

    # 다시 한국어로
    page.locator("button[data-lang='ko']").click()
    page.wait_for_timeout(300)

    # ============================================================
    # TEST 9: DB 데이터 로드 확인
    # ============================================================
    print("\n=== TEST 9: DB 데이터 ===")
    db_size = page.evaluate("() => JSON.stringify(SAJU_DB).length")
    log("DB 로드됨", db_size > 1000000, f"크기: {db_size:,} 바이트")

    cheongan_count = page.evaluate("() => Object.keys(SAJU_DB.cheongan).length")
    log("천간 10개", cheongan_count == 10, f"실제: {cheongan_count}")

    jiji_count = page.evaluate("() => Object.keys(SAJU_DB.jiji).length")
    log("지지 12개", jiji_count == 12, f"실제: {jiji_count}")

    combo_count = page.evaluate("() => Object.keys(SAJU_DB.ilgan_combo).length")
    log("일간조합 120개", combo_count == 120, f"실제: {combo_count}")

    goonghap_count = page.evaluate("() => Object.keys(SAJU_DB.goonghap).length")
    log("궁합 100개", goonghap_count == 100, f"실제: {goonghap_count}")

    # ============================================================
    # SUMMARY
    # ============================================================
    browser.close()

print("\n" + "=" * 55)
print("  QA 테스트 결과")
print("=" * 55)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
total = len(results)
print(f"  통과: {passed}/{total}")
print(f"  실패: {failed}/{total}")

if failed > 0:
    print("\n  실패 항목:")
    for name, ok, detail in results:
        if not ok:
            print(f"    ❌ {name} — {detail}")

print("=" * 55)
print(f"  스크린샷: {SCREENSHOTS}/")
sys.exit(0 if failed == 0 else 1)
