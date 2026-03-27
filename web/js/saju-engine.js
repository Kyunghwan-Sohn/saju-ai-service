/**
 * 사주 계산 엔진 (JavaScript)
 * 생년월일시 → 사주팔자(년주/월주/일주/시주) 산출
 *
 * 기준일: 2000-01-01 = 戊午 (60갑자 index 54)
 * 검증: 나무위키 무오 항목 + ytliu0 만세력
 */

const STEMS = [
  { char: "甲", kr: "갑", key: "gap",     element: "목", yin_yang: "양" },
  { char: "乙", kr: "을", key: "eul",     element: "목", yin_yang: "음" },
  { char: "丙", kr: "병", key: "byeong",  element: "화", yin_yang: "양" },
  { char: "丁", kr: "정", key: "jeong",   element: "화", yin_yang: "음" },
  { char: "戊", kr: "무", key: "mu",      element: "토", yin_yang: "양" },
  { char: "己", kr: "기", key: "gi",      element: "토", yin_yang: "음" },
  { char: "庚", kr: "경", key: "gyeong",  element: "금", yin_yang: "양" },
  { char: "辛", kr: "신", key: "sin",     element: "금", yin_yang: "음" },
  { char: "壬", kr: "임", key: "im",      element: "수", yin_yang: "양" },
  { char: "癸", kr: "계", key: "gye",     element: "수", yin_yang: "음" }
];

const BRANCHES = [
  { char: "子", kr: "자", key: "ja",   animal: "쥐",     element: "수", emoji: "🐀" },
  { char: "丑", kr: "축", key: "chuk", animal: "소",     element: "토", emoji: "🐂" },
  { char: "寅", kr: "인", key: "in",   animal: "호랑이", element: "목", emoji: "🐅" },
  { char: "卯", kr: "묘", key: "myo",  animal: "토끼",   element: "목", emoji: "🐇" },
  { char: "辰", kr: "진", key: "jin",  animal: "용",     element: "토", emoji: "🐉" },
  { char: "巳", kr: "사", key: "sa",   animal: "뱀",     element: "화", emoji: "🐍" },
  { char: "午", kr: "오", key: "o",    animal: "말",     element: "화", emoji: "🐴" },
  { char: "未", kr: "미", key: "mi",   animal: "양",     element: "토", emoji: "🐏" },
  { char: "申", kr: "신", key: "sin",  animal: "원숭이", element: "금", emoji: "🐵" },
  { char: "酉", kr: "유", key: "yu",   animal: "닭",     element: "금", emoji: "🐔" },
  { char: "戌", kr: "술", key: "sul",  animal: "개",     element: "토", emoji: "🐕" },
  { char: "亥", kr: "해", key: "hae",  animal: "돼지",   element: "수", emoji: "🐖" }
];

const ELEMENT_COLORS = {
  "목": { bg: "#DCFCE7", text: "#16A34A", accent: "#16A34A", name: "木", vi: "Mộc" },
  "화": { bg: "#FEE2E2", text: "#DC2626", accent: "#DC2626", name: "火", vi: "Hỏa" },
  "토": { bg: "#FEF9C3", text: "#CA8A04", accent: "#CA8A04", name: "土", vi: "Thổ" },
  "금": { bg: "#EDE9FE", text: "#7C3AED", accent: "#7C3AED", name: "金", vi: "Kim" },
  "수": { bg: "#DBEAFE", text: "#2563EB", accent: "#2563EB", name: "水", vi: "Thủy" }
};

// ============================================================
// 일주(日柱) 계산 — 60갑자 기반
// 기준: 2000-01-01 = 戊午 = 60갑자 index 54
// ============================================================
const REF_DATE = Date.UTC(2000, 0, 1);  // 2000-01-01 UTC
const REF_GANJI_IDX = 54;               // 戊午 = index 54

function daysBetween(y, m, d) {
  const target = Date.UTC(y, m - 1, d);
  return Math.round((target - REF_DATE) / 86400000);
}

function calcDayPillar(year, month, day) {
  const diff = daysBetween(year, month, day);
  const idx = (((diff + REF_GANJI_IDX) % 60) + 60) % 60;
  const stemIdx = idx % 10;
  const branchIdx = idx % 12;
  return { stem: STEMS[stemIdx], branch: BRANCHES[branchIdx], ganjiIdx: idx };
}

// ============================================================
// 년주(年柱) 계산 — 입춘(2월 4일경) 기준
// ============================================================
function calcYearPillar(year, month, day) {
  let adjYear = year;
  if (month < 2 || (month === 2 && day < 4)) {
    adjYear = year - 1;
  }
  const stemIdx = ((adjYear - 4) % 10 + 10) % 10;
  const branchIdx = ((adjYear - 4) % 12 + 12) % 12;
  return { stem: STEMS[stemIdx], branch: BRANCHES[branchIdx] };
}

// ============================================================
// 월주(月柱) 계산 — 절기 기반 + 오호둔년법
// ============================================================
function getMonthBranch(month, day) {
  // 절기 시작일 (근사값, 양력 기준)
  // 인월(寅)=입춘~경칩, 묘월(卯)=경칩~청명, ...
  if ((month === 2 && day >= 4) || (month === 3 && day < 6))   return 2;  // 인
  if ((month === 3 && day >= 6) || (month === 4 && day < 5))   return 3;  // 묘
  if ((month === 4 && day >= 5) || (month === 5 && day < 6))   return 4;  // 진
  if ((month === 5 && day >= 6) || (month === 6 && day < 6))   return 5;  // 사
  if ((month === 6 && day >= 6) || (month === 7 && day < 7))   return 6;  // 오
  if ((month === 7 && day >= 7) || (month === 8 && day < 8))   return 7;  // 미
  if ((month === 8 && day >= 8) || (month === 9 && day < 8))   return 8;  // 신
  if ((month === 9 && day >= 8) || (month === 10 && day < 8))  return 9;  // 유
  if ((month === 10 && day >= 8) || (month === 11 && day < 7)) return 10; // 술
  if ((month === 11 && day >= 7) || (month === 12 && day < 7)) return 11; // 해
  if ((month === 12 && day >= 7) || (month === 1 && day < 6))  return 0;  // 자
  if ((month === 1 && day >= 6) || (month === 2 && day < 4))   return 1;  // 축
  return 0;
}

function calcMonthPillar(yearStemIdx, month, day) {
  const monthBranchIdx = getMonthBranch(month, day);

  // 오호둔년법: 년간별 인월(寅月) 천간 시작
  // 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
  const inMonthStems = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0];
  const baseMonthStem = inMonthStems[yearStemIdx];

  const offset = ((monthBranchIdx - 2) + 12) % 12;
  const monthStemIdx = (baseMonthStem + offset) % 10;

  return { stem: STEMS[monthStemIdx], branch: BRANCHES[monthBranchIdx] };
}

// ============================================================
// 시주(時柱) 계산 — 오자둔일법
// ============================================================
function calcHourPillar(dayStemIdx, hour) {
  if (hour === null || hour === undefined || hour === -1) return null;

  let branchIdx;
  if (hour >= 23 || hour < 1)  branchIdx = 0;
  else if (hour < 3)  branchIdx = 1;
  else if (hour < 5)  branchIdx = 2;
  else if (hour < 7)  branchIdx = 3;
  else if (hour < 9)  branchIdx = 4;
  else if (hour < 11) branchIdx = 5;
  else if (hour < 13) branchIdx = 6;
  else if (hour < 15) branchIdx = 7;
  else if (hour < 17) branchIdx = 8;
  else if (hour < 19) branchIdx = 9;
  else if (hour < 21) branchIdx = 10;
  else branchIdx = 11;

  // 오자둔일법: 일간별 자시(子時) 천간 시작
  // 甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子
  const hourBaseStems = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8];
  const hourStemIdx = (hourBaseStems[dayStemIdx] + branchIdx) % 10;

  return { stem: STEMS[hourStemIdx], branch: BRANCHES[branchIdx] };
}

// ============================================================
// 오행 분포
// ============================================================
function calcFiveElements(pillars) {
  const counts = { "목": 0, "화": 0, "토": 0, "금": 0, "수": 0 };
  for (const p of pillars) {
    if (p) { counts[p.stem.element]++; counts[p.branch.element]++; }
  }
  return counts;
}

function analyzeRelations(fiveElements, ilganElement) {
  const cycle = ["목", "화", "토", "금", "수"];
  const idx = cycle.indexOf(ilganElement);
  return {
    me: ilganElement,
    generates: cycle[(idx + 1) % 5],
    generated_by: cycle[(idx + 4) % 5],
    controls: cycle[(idx + 2) % 5],
    controlled_by: cycle[(idx + 3) % 5]
  };
}

// ============================================================
// 메인 사주 계산
// ============================================================
function calculateSaju(year, month, day, hour, gender) {
  const yearPillar = calcYearPillar(year, month, day);
  const yearStemIdx = STEMS.indexOf(yearPillar.stem);

  const monthPillar = calcMonthPillar(yearStemIdx, month, day);
  const dayPillar = calcDayPillar(year, month, day);
  const dayStemIdx = STEMS.indexOf(dayPillar.stem);
  const hourPillar = calcHourPillar(dayStemIdx, hour);

  const pillars = [yearPillar, monthPillar, dayPillar, hourPillar];
  const fiveElements = calcFiveElements(pillars.filter(Boolean));
  const relations = analyzeRelations(fiveElements, dayPillar.stem.element);

  const ilganKey = dayPillar.stem.key;
  const woljiKey = monthPillar.branch.key;
  const comboKey = `${ilganKey}_${woljiKey}`;

  return { pillars: { year: yearPillar, month: monthPillar, day: dayPillar, hour: hourPillar },
           ilgan: dayPillar.stem, wolji: monthPillar.branch,
           fiveElements, relations, keys: { ilganKey, woljiKey, comboKey }, gender };
}

// ============================================================
// 오늘/이번달/올해 운세 계산
// ============================================================
function getTodayFortune(ilganStem) {
  const now = new Date();
  const y = now.getFullYear(), m = now.getMonth() + 1, d = now.getDate();

  const todayPillar = calcDayPillar(y, m, d);
  const monthPillar = calcMonthPillar(((y - 4) % 10 + 10) % 10, m, d);
  const yearPillar = calcYearPillar(y, m, d);

  return {
    daily:   { pillar: todayPillar,  relation: getTenGod(ilganStem, todayPillar.stem) },
    monthly: { pillar: monthPillar,  relation: getTenGod(ilganStem, monthPillar.stem) },
    yearly:  { pillar: yearPillar,   relation: getTenGod(ilganStem, yearPillar.stem) },
    dateStr: `${y}.${m}.${d}`
  };
}

// 십성(十星) 계산: 일간 기준으로 대상 천간의 십성
function getTenGod(meStem, targetStem) {
  const meEl = meStem.element;
  const tEl = targetStem.element;
  const meYY = meStem.yin_yang;
  const tYY = targetStem.yin_yang;
  const same = meYY === tYY;

  const cycle = ["목", "화", "토", "금", "수"];
  const mi = cycle.indexOf(meEl);
  const ti = cycle.indexOf(tEl);
  const rel = ((ti - mi) + 5) % 5;

  // 0=비겁, 1=식상, 2=재성, 3=관성, 4=인성
  const names = {
    ko: [
      same ? "비견" : "겁재",
      same ? "식신" : "상관",
      same ? "편재" : "정재",
      same ? "편관" : "정관",
      same ? "편인" : "정인"
    ],
    vi: [
      same ? "Tỷ Kiên" : "Kiếp Tài",
      same ? "Thực Thần" : "Thương Quan",
      same ? "Thiên Tài" : "Chính Tài",
      same ? "Thiên Quan" : "Chính Quan",
      same ? "Thiên Ấn" : "Chính Ấn"
    ],
    meaning_ko: [
      same ? "나와 같은 기운 — 동료, 경쟁" : "나를 빼앗는 기운 — 경쟁, 도전",
      same ? "내가 만들어내는 기운 — 재능, 표현" : "내가 흘려보내는 기운 — 자유, 예술",
      same ? "내가 다스리는 재물 — 뜻밖의 수입" : "내가 관리하는 재물 — 안정적 수입",
      same ? "나를 다스리는 힘 — 변화, 도전" : "나를 지켜주는 힘 — 직장, 안정",
      same ? "나를 도와주는 기운 — 독특한 사고" : "나를 키워주는 기운 — 학업, 지혜"
    ],
    meaning_vi: [
      same ? "Năng lượng giống mình — đồng nghiệp, cạnh tranh" : "Năng lượng tranh giành — thử thách, cạnh tranh",
      same ? "Năng lượng tạo ra — tài năng, biểu đạt" : "Năng lượng tự do — nghệ thuật, sáng tạo",
      same ? "Tài lộc kiểm soát — thu nhập bất ngờ" : "Tài lộc quản lý — thu nhập ổn định",
      same ? "Năng lượng thử thách — thay đổi, đột phá" : "Năng lượng bảo vệ — sự nghiệp, ổn định",
      same ? "Năng lượng hỗ trợ — tư duy độc đáo" : "Năng lượng nuôi dưỡng — học vấn, trí tuệ"
    ]
  };

  return {
    ko: names.ko[rel],
    vi: names.vi[rel],
    meaning_ko: names.meaning_ko[rel],
    meaning_vi: names.meaning_vi[rel],
    type: ["비겁","식상","재성","관성","인성"][rel]
  };
}

// 영역별 운세 키워드
const LIFE_AREAS = {
  love:     { icon: "❤️", ko: "연애운", vi: "Tình Duyên", category: "연애/결혼" },
  marriage: { icon: "💍", ko: "결혼운", vi: "Hôn Nhân", category: "연애/결혼" },
  career:   { icon: "💼", ko: "직업운", vi: "Sự Nghiệp", category: "직업/커리어" },
  business: { icon: "🏢", ko: "사업운", vi: "Kinh Doanh", category: "직업/커리어" },
  wealth:   { icon: "💰", ko: "재물운", vi: "Tài Lộc", category: "재물" },
  family:   { icon: "👨‍👩‍👧‍👦", ko: "가족운", vi: "Gia Đình", category: "종합 조언" },
  friends:  { icon: "🤝", ko: "대인관계", vi: "Quan Hệ", category: "성격" },
  health:   { icon: "🏥", ko: "건강운", vi: "Sức Khỏe", category: "건강" },
  study:    { icon: "📚", ko: "학업운", vi: "Học Vấn", category: "종합 조언" },
  moving:   { icon: "🏠", ko: "이사/이직", vi: "Chuyển Đổi", category: "종합 조언" }
};
