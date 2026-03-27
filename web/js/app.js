/**
 * MỆnh v2 — 대화형 Q&A + 일/월/년운 + 궁합
 */
let lang = 'ko';
let saju = null;
let gender = 'male';
let topicDepth = 0; // 현재 대화 깊이

const ILGAN_MAP = {'甲':'gap','乙':'eul','丙':'byeong','丁':'jeong','戊':'mu','己':'gi','庚':'gyeong','辛':'sin','壬':'im','癸':'gye'};
const OHAENG_MAP = {'甲':'mok','乙':'mok','丙':'hwa','丁':'hwa','戊':'to','己':'to','庚':'geum','辛':'geum','壬':'su','癸':'su'};
const WOLJI_MAP = {'子':'ja','丑':'chuk','寅':'in','卯':'myo','辰':'jin','巳':'sa','午':'o','未':'mi','申':'sin','酉':'yu','戌':'sul','亥':'hae'};

// 주제별 후속 질문 트리
const FOLLOW_UPS = {
  love: [
    { q: { ko: "지금 만나는 사람이 있나요?", vi: "Bạn đang có người yêu không?" },
      opts: [
        { label: {ko:"네, 있어요", vi:"Có"}, next: "love_inrel" },
        { label: {ko:"아니요, 싱글이에요", vi:"Không, đang single"}, next: "love_single" },
        { label: {ko:"썸 타는 중이에요", vi:"Đang trong giai đoạn tìm hiểu"}, next: "love_some" }
      ]},
    { id: "love_inrel",
      q: {ko:"관계에서 요즘 어떤 부분이 고민이에요?", vi:"Gần đây bạn lo lắng điều gì trong mối quan hệ?"},
      opts: [
        { label: {ko:"싸움이 잦아요", vi:"Hay cãi nhau"}, next: "love_fight" },
        { label: {ko:"감정이 식은 것 같아요", vi:"Tình cảm dường như nguội lạnh"}, next: "love_cold" },
        { label: {ko:"결혼을 고민 중이에요", vi:"Đang suy nghĩ về kết hôn"}, next: "love_marriage" }
      ]},
    { id: "love_single",
      q: {ko:"연애를 못 하는 이유가 뭘까요?", vi:"Lý do bạn chưa yêu là gì?"},
      opts: [
        { label: {ko:"좋은 사람을 못 만나요", vi:"Chưa gặp được người phù hợp"}, next: "love_nomatch" },
        { label: {ko:"마음을 여는 게 어려워요", vi:"Khó mở lòng"}, next: "love_closed" },
        { label: {ko:"일이 바빠서요", vi:"Bận công việc"}, next: "love_busy" }
      ]},
    { id: "love_some",
      q: {ko:"그 사람에 대해 어떤 게 궁금하세요?", vi:"Bạn muốn biết gì về người đó?"},
      opts: [
        { label: {ko:"나한테 관심이 있을까?", vi:"Người đó có quan tâm mình không?"}, next: "love_interest" },
        { label: {ko:"이 사람이 내 인연일까?", vi:"Người này có phải nhân duyên?"}, next: "love_fate" }
      ]}
  ],
  career: [
    { q: {ko:"직업 관련해서 어떤 상황이에요?", vi:"Tình hình công việc của bạn thế nào?"},
      opts: [
        { label: {ko:"이직을 고민 중이에요", vi:"Đang suy nghĩ chuyển việc"}, next: "career_change" },
        { label: {ko:"지금 하는 일이 맞는지 모르겠어요", vi:"Không biết công việc hiện tại có phù hợp không"}, next: "career_fit" },
        { label: {ko:"사업을 시작하고 싶어요", vi:"Muốn khởi nghiệp"}, next: "career_biz" },
        { label: {ko:"직장에서 인정받고 싶어요", vi:"Muốn được công nhận"}, next: "career_recog" }
      ]}
  ],
  money: [
    { q: {ko:"돈에 대해 어떤 게 고민이에요?", vi:"Bạn lo lắng gì về tiền bạc?"},
      opts: [
        { label: {ko:"돈이 안 모여요", vi:"Tiền không tích được"}, next: "money_save" },
        { label: {ko:"투자를 해볼까 고민이에요", vi:"Đang suy nghĩ có nên đầu tư"}, next: "money_invest" },
        { label: {ko:"지출을 줄이고 싶어요", vi:"Muốn giảm chi tiêu"}, next: "money_spend" },
        { label: {ko:"큰 돈이 필요한 상황이에요", vi:"Cần một khoản lớn"}, next: "money_need" }
      ]}
  ],
  self: [
    { q: {ko:"요즘 어떤 기분이에요?", vi:"Dạo này bạn cảm thấy thế nào?"},
      opts: [
        { label: {ko:"자존감이 낮아요", vi:"Tự tin thấp"}, next: "self_esteem" },
        { label: {ko:"방향을 모르겠어요", vi:"Không biết đi hướng nào"}, next: "self_lost" },
        { label: {ko:"번아웃인 것 같아요", vi:"Có vẻ bị burnout"}, next: "self_burnout" },
        { label: {ko:"나를 더 알고 싶어요", vi:"Muốn hiểu mình hơn"}, next: "self_know" }
      ]}
  ],
  general: [
    { q: {ko:"삶에서 지금 가장 필요한 건 뭘까요?", vi:"Điều bạn cần nhất trong cuộc sống bây giờ là gì?"},
      opts: [
        { label: {ko:"변화가 필요해요", vi:"Cần thay đổi"}, next: "gen_change" },
        { label: {ko:"안정이 필요해요", vi:"Cần ổn định"}, next: "gen_stable" },
        { label: {ko:"용기가 필요해요", vi:"Cần dũng khí"}, next: "gen_courage" },
        { label: {ko:"쉼이 필요해요", vi:"Cần nghỉ ngơi"}, next: "gen_rest" }
      ]}
  ]
};

// ============================================================
// 초기화
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.gen-btn').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.gen-btn').forEach(x => x.classList.remove('on'));
    b.classList.add('on'); gender = b.dataset.g;
  }));
  document.querySelectorAll('.lang-btn').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.lang-btn').forEach(x => x.classList.remove('on'));
    b.classList.add('on'); lang = b.dataset.lang; updateLang();
  }));
  document.getElementById('frm').addEventListener('submit', e => { e.preventDefault(); runCalc(); });
  document.getElementById('frm-compat').addEventListener('submit', e => { e.preventDefault(); runCompat(); });
});

function go(id) {
  if (!saju && id !== 'scr-input') {
    go('scr-input');
    return;
  }
  document.querySelectorAll('.scr').forEach(s => s.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  document.getElementById('ld').classList.remove('on');
  // 화면별 초기화
  if (id === 'scr-home') renderHome();
  if (id === 'scr-daily') renderFortune('daily');
  if (id === 'scr-monthly') renderFortune('monthly');
  if (id === 'scr-yearly') renderFortune('yearly');
  window.scrollTo({top: 0, behavior: 'smooth'});
}

function updateLang() {
  document.querySelectorAll('[data-ko][data-vi]').forEach(el => {
    el.textContent = lang === 'ko' ? el.dataset.ko : el.dataset.vi;
  });
}

// ============================================================
// 사주 계산 → 홈
// ============================================================
function runCalc() {
  const y = parseInt(document.getElementById('f-y').value);
  const m = parseInt(document.getElementById('f-m').value);
  const d = parseInt(document.getElementById('f-d').value);
  const hv = document.getElementById('f-h').value;
  const h = hv === '' ? null : parseInt(hv);
  if (!y || !m || !d) return;
  saju = calculateSaju(y, m, d, h, gender);
  go('scr-home');
}

// ============================================================
// 홈 렌더링
// ============================================================
function renderHome() {
  renderMiniPillars('home-pillars');
  // 오늘의 한 줄
  const td = getTodayKey();
  const today = DB_TODAY[td.key];
  document.getElementById('home-today-text').textContent = today
    ? (lang === 'ko' ? today.ko : today.vi)
    : (lang === 'ko' ? '오늘 하루도 당신은 충분해요.' : 'Hôm nay bạn đã đủ rồi.');
}

// ============================================================
// 대화형 주제 풀이
// ============================================================
function startTopic(situation) {
  topicDepth = 0;
  const cardsEl = document.getElementById('topic-cards');
  const followEl = document.getElementById('topic-follow');
  cardsEl.innerHTML = '';
  followEl.innerHTML = '';
  go('scr-topic');
  renderMiniPillars('topic-pillars');

  // 카드1: INTRO (공감)
  const ilganCode = ILGAN_MAP[saju.ilgan.char];
  const intro = DB_INTRO[`${situation}_${ilganCode}`];
  addCard(cardsEl, 'card-intro', lang === 'ko' ? '혹시 이런 분 아닌가요?' : 'Có phải bạn là người thế này?',
    intro ? (lang === 'ko' ? intro.ko : intro.vi) : getFallbackIntro(situation));

  // 카드2: ILGAN (성격)
  const ilgan = DB_ILGAN[`${ilganCode}_${situation}`];
  addCard(cardsEl, 'card-ilgan', lang === 'ko' ? '당신은 이런 사람' : 'Bạn là người như thế này',
    ilgan ? (lang === 'ko' ? ilgan.ko : ilgan.vi) : getFallbackIlgan(situation),
    ilgan?.keyword);

  // 후속 질문 표시
  showFollowUp(followEl, situation, 0, cardsEl);
}

function showFollowUp(followEl, situation, stepIdx, cardsEl) {
  const steps = FOLLOW_UPS[situation];
  if (!steps || stepIdx >= steps.length) {
    // 마지막: COMBO + CHEER
    showFinalCards(cardsEl, followEl, situation);
    return;
  }

  const step = stepIdx === 0 ? steps[0] : steps.find(s => s.id === stepIdx);
  if (!step) { showFinalCards(cardsEl, followEl, situation); return; }

  const q = lang === 'ko' ? step.q.ko : step.q.vi;

  followEl.innerHTML = `
    <div class="cd" style="border-left:4px solid var(--accent);margin-top:6px">
      <div class="cd-body" style="font-weight:600;font-size:16px;margin-bottom:14px">${q}</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        ${step.opts.map((o, i) => `
          <button class="follow-btn" onclick="pickFollow('${situation}','${o.next}',this)"
            style="padding:14px 16px;border-radius:var(--r-sm);border:1.5px solid var(--border);background:#fff;color:var(--text);font-size:14px;font-weight:500;cursor:pointer;text-align:left;font-family:inherit;transition:.2s">
            ${lang === 'ko' ? o.label.ko : o.label.vi}
          </button>
        `).join('')}
      </div>
    </div>`;

  followEl.scrollIntoView({behavior: 'smooth', block: 'start'});
}

function pickFollow(situation, nextId, btnEl) {
  // 선택된 버튼 강조
  btnEl.parentElement.querySelectorAll('button').forEach(b => {
    b.style.opacity = '0.4';
    b.style.pointerEvents = 'none';
  });
  btnEl.style.opacity = '1';
  btnEl.style.borderColor = 'var(--accent)';
  btnEl.style.color = 'var(--accent)';
  btnEl.style.fontWeight = '700';

  topicDepth++;
  const cardsEl = document.getElementById('topic-cards');
  const followEl = document.getElementById('topic-follow');

  // 선택에 맞는 응답 카드 추가
  const responseText = getFollowResponse(situation, nextId);
  setTimeout(() => {
    addCard(cardsEl, 'card-combo', '', responseText);

    // 다음 후속 질문 또는 마무리
    const steps = FOLLOW_UPS[situation];
    const nextStep = steps?.find(s => s.id === nextId);
    if (nextStep && topicDepth < 3) {
      showFollowUp(followEl, situation, nextId, cardsEl);
    } else {
      showFinalCards(cardsEl, followEl, situation);
    }
  }, 400);
}

function showFinalCards(cardsEl, followEl, situation) {
  followEl.innerHTML = '';
  const ilganCode = ILGAN_MAP[saju.ilgan.char];
  const woljiCode = WOLJI_MAP[saju.wolji.char];
  const ohaengCode = OHAENG_MAP[saju.ilgan.char];

  // COMBO 카드 (시기)
  const combo = DB_COMBO[`${ilganCode}_${woljiCode}`];
  if (combo) {
    addCard(cardsEl, 'card-combo',
      lang === 'ko' ? '지금 이 시기' : 'Giai đoạn hiện tại',
      lang === 'ko' ? combo.ko : combo.vi);
    if (combo.action) {
      const el = document.createElement('div');
      el.className = 'action-box';
      el.textContent = combo.action;
      cardsEl.appendChild(el);
    }
  }

  // TODAY 카드
  const td = getTodayKey();
  const today = DB_TODAY[td.key];
  if (today) {
    const todayCard = document.createElement('div');
    todayCard.className = 'cd card-today';
    todayCard.innerHTML = `<div class="cd-t">${lang === 'ko' ? '오늘의 한 줄' : 'Hôm nay'}</div>
      <div class="cd-body">${lang === 'ko' ? today.ko : today.vi}</div>`;
    cardsEl.appendChild(todayCard);
  }

  // CHEER 카드
  const cheer = DB_CHEER[`${situation}_${ohaengCode}`];
  if (cheer) {
    const cheerCard = document.createElement('div');
    cheerCard.className = 'cd card-cheer';
    cheerCard.innerHTML = `<div class="cd-body">${lang === 'ko' ? cheer.ko : cheer.vi}</div>`;
    cardsEl.appendChild(cheerCard);
  }

  // 버튼
  followEl.innerHTML = `<div style="display:flex;gap:10px;margin-top:10px">
    <button class="btn" style="background:#fff;color:var(--accent);border:1.5px solid var(--accent);box-shadow:none;flex:1" onclick="go('scr-home')">다른 주제</button>
    <button class="btn" style="flex:1" onclick="startTopic('${situation}')">더 알아보기</button>
  </div>`;

  setTimeout(() => cardsEl.lastElementChild?.scrollIntoView({behavior:'smooth'}), 200);
}

// ============================================================
// 일/월/년 운세
// ============================================================
function renderFortune(period) {
  const containerId = `${period}-content`;
  const pillarsId = `${period}-pillars`;
  renderMiniPillars(pillarsId);

  const now = new Date();
  const y = now.getFullYear(), m = now.getMonth()+1, d = now.getDate();
  const fortune = getTodayFortune(saju.ilgan);
  const f = fortune[period];
  const rel = f.relation;

  const titles = { daily: {ko:'오늘의 운세',vi:'Vận hôm nay'}, monthly: {ko:'이달의 운세',vi:'Vận tháng này'}, yearly: {ko:'올해의 운세',vi:'Vận năm nay'} };
  const pLabel = lang === 'ko' ? titles[period].ko : titles[period].vi;

  // 영역별 점수
  const areas = ['love','career','money','health','self'];
  const areaNames = {
    love:{ko:'연애',vi:'Tình duyên',icon:'❤️'}, career:{ko:'직업',vi:'Sự nghiệp',icon:'💼'},
    money:{ko:'재물',vi:'Tiền bạc',icon:'💰'}, health:{ko:'건강',vi:'Sức khỏe',icon:'🏥'},
    self:{ko:'자기관리',vi:'Bản thân',icon:'🪞'}
  };

  let html = `
    <div class="cd card-today">
      <div class="cd-t">${pLabel}</div>
      <div class="cd-body" style="font-size:16px">${lang === 'ko' ? rel.meaning_ko : rel.meaning_vi}</div>
    </div>

    <div class="cd">
      <div class="cd-t" style="color:var(--text)">${lang === 'ko' ? '분야별' : 'Theo lĩnh vực'}</div>
      <div style="margin-top:12px">
  `;

  areas.forEach(a => {
    const an = areaNames[a];
    const score = getAreaScore(saju.ilgan.element, f.pillar.stem.element, a);
    const color = score >= 70 ? 'var(--green)' : score >= 50 ? 'var(--gold)' : 'var(--pink)';
    html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;cursor:pointer" onclick="startTopic('${a === 'money' ? 'money' : a === 'health' ? 'self' : a}')">
      <span style="font-size:20px">${an.icon}</span>
      <span style="min-width:55px;font-size:14px;font-weight:600">${lang === 'ko' ? an.ko : an.vi}</span>
      <div style="flex:1;height:24px;background:var(--bg);border-radius:12px;overflow:hidden">
        <div style="width:${score}%;height:100%;background:${color};border-radius:12px;transition:.5s"></div>
      </div>
      <span style="font-size:14px;font-weight:700;color:${color};min-width:30px">${score}</span>
    </div>`;
  });

  html += `</div></div>`;

  // 행운 정보
  const si = STEMS.indexOf(f.pillar.stem);
  const colors = ['초록','빨강','노랑','보라','파랑'];
  const dirs = ['동','남','중앙','서','북'];
  html += `<div class="cd">
    <div class="cd-t" style="color:var(--text)">🍀 ${lang === 'ko' ? '행운 정보' : 'May mắn'}</div>
    <div style="display:flex;justify-content:space-around;margin-top:14px;text-align:center">
      <div><div style="font-size:22px">🎨</div><div style="font-size:12px;color:var(--dim);margin-top:4px">${lang === 'ko' ? '색' : 'Màu'}</div><div style="font-size:14px;font-weight:700">${colors[si%5]}</div></div>
      <div><div style="font-size:22px">🔢</div><div style="font-size:12px;color:var(--dim);margin-top:4px">${lang === 'ko' ? '숫자' : 'Số'}</div><div style="font-size:14px;font-weight:700">${(si+3)%9+1}</div></div>
      <div><div style="font-size:22px">🧭</div><div style="font-size:12px;color:var(--dim);margin-top:4px">${lang === 'ko' ? '방향' : 'Hướng'}</div><div style="font-size:14px;font-weight:700">${dirs[si%5]}</div></div>
    </div>
  </div>`;

  document.getElementById(containerId).innerHTML = html;
}

// ============================================================
// 궁합
// ============================================================
function runCompat() {
  const y = parseInt(document.getElementById('c-y').value);
  const m = parseInt(document.getElementById('c-m').value);
  const d = parseInt(document.getElementById('c-d').value);
  if (!y || !m || !d || !saju) return;

  const other = calculateSaju(y, m, d, null, 'male');
  const myEl = saju.ilgan.element;
  const otEl = other.ilgan.element;

  // 궁합 점수
  const sg = {"목":"화","화":"토","토":"금","금":"수","수":"목"};
  let score = 58;
  if (myEl === otEl) score = 72;
  else if (sg[myEl] === otEl || sg[otEl] === myEl) score = 85;
  score += (new Date().getDate() % 7) - 3;

  const color = score >= 75 ? 'var(--green)' : score >= 60 ? 'var(--gold)' : 'var(--pink)';

  // 궁합 텍스트
  const compatTexts = {
    high: {ko:"서로를 자연스럽게 채워주는 관계예요. 함께 있으면 부족한 부분이 메워지고, 서로에게 좋은 에너지를 주는 조합이에요. 의견이 다를 때는 상대의 시각이 나를 성장시킨다고 생각해보세요.", vi:"Hai bạn bổ khuyết cho nhau một cách tự nhiên. Khi ở bên nhau, những thiếu sót được lấp đầy và trao cho nhau năng lượng tích cực. Khi ý kiến khác nhau, hãy nghĩ rằng góc nhìn của đối phương giúp mình trưởng thành."},
    mid: {ko:"비슷한 점이 많아서 편안하지만, 그만큼 부딪히기도 쉬운 관계예요. 서로의 영역을 인정해주는 게 핵심이에요. '내가 맞아'보다 '우리가 다른 거구나'로 바꾸면 훨씬 편해져요.", vi:"Có nhiều điểm tương đồng nên thoải mái, nhưng cũng dễ va chạm. Chìa khóa là tôn trọng không gian riêng. Thay vì 'mình đúng', hãy chuyển sang 'chúng mình khác nhau' — sẽ dễ chịu hơn nhiều."},
    low: {ko:"첫인상은 '다르다'일 수 있어요. 하지만 다른 만큼 배울 것도 많은 관계예요. 상대방이 가진 것이 바로 나에게 없는 것이에요. 서로의 차이를 존중하면 오히려 가장 강한 팀이 될 수 있어요.", vi:"Ấn tượng đầu tiên có thể là 'khác biệt'. Nhưng càng khác càng có nhiều điều để học. Điều đối phương có chính là điều bạn thiếu. Tôn trọng sự khác biệt, hai bạn có thể trở thành đội mạnh nhất."}
  };
  const text = score >= 75 ? compatTexts.high : score >= 60 ? compatTexts.mid : compatTexts.low;

  document.getElementById('compat-result').innerHTML = `
    <div style="text-align:center;margin:20px 0">
      <div style="width:110px;height:110px;border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:900;border:3px solid ${color};color:${color};background:#fff;box-shadow:0 4px 20px rgba(0,0,0,.06)">${score}</div>
      <div style="font-size:13px;color:var(--sub)">${saju.ilgan.char} × ${other.ilgan.char}</div>
    </div>
    <div class="cd card-ilgan">
      <div class="cd-body">${lang === 'ko' ? text.ko : text.vi}</div>
    </div>`;
}

// ============================================================
// 유틸리티
// ============================================================
function renderMiniPillars(id) {
  const el = document.getElementById(id);
  if (!el || !saju) return;
  const p = saju.pillars;
  const cols = [
    {lbl:lang==='ko'?'시':'Giờ', d:p.hour}, {lbl:lang==='ko'?'일':'Ngày', d:p.day},
    {lbl:lang==='ko'?'월':'Tháng', d:p.month}, {lbl:lang==='ko'?'년':'Năm', d:p.year}
  ];
  el.innerHTML = cols.map(c => {
    if (!c.d) return `<div class="mini-p"><div class="hz" style="color:var(--dim)">?</div><div class="lbl">${c.lbl}</div></div>`;
    const sc = ELEMENT_COLORS[c.d.stem.element];
    const bc = ELEMENT_COLORS[c.d.branch.element];
    return `<div class="mini-p"><div class="hz"><span style="color:${sc.accent}">${c.d.stem.char}</span><span style="color:${bc.accent}">${c.d.branch.char}</span></div><div class="lbl">${c.lbl}</div></div>`;
  }).join('');
}

function addCard(container, cls, title, body, keywords) {
  const card = document.createElement('div');
  card.className = `cd ${cls}`;
  card.style.animation = 'fadeUp .4s ease';
  card.innerHTML = `${title ? `<div class="cd-t">${title}</div>` : ''}<div class="cd-body">${body}</div>
    ${keywords ? `<div class="cd-kw">${keywords.map(k=>`<span class="kw">${k}</span>`).join('')}</div>` : ''}`;
  container.appendChild(card);
}

function getTodayKey() {
  const now = new Date();
  const dp = calcDayPillar(now.getFullYear(), now.getMonth()+1, now.getDate());
  const days = ['sun','mon','tue','wed','thu','fri','sat'];
  return { key: `${dp.ganjiIdx}_${days[now.getDay()]}`, pillar: dp };
}

function getAreaScore(meEl, targetEl, area) {
  const cycle = ["목","화","토","금","수"];
  const rel = ((cycle.indexOf(targetEl) - cycle.indexOf(meEl)) + 5) % 5;
  const bases = {love:[55,75,70,60,80],career:[65,70,60,85,70],money:[50,65,85,55,60],health:[65,55,60,70,75],self:[70,60,55,65,80]};
  return Math.max(35, Math.min(95, (bases[area]||bases.career)[rel] + (new Date().getDate()%10)-5));
}

// 후속 질문 응답 생성 (DB에 없을 때 폴백)
function getFollowResponse(situation, nextId) {
  const ilganCode = ILGAN_MAP[saju.ilgan.char];
  // v1 DB에서 관련 카테고리 검색
  const combo = typeof SAJU_DB !== 'undefined' && SAJU_DB.ilgan_combo?.[`${ilganCode}_${WOLJI_MAP[saju.wolji.char]}`];
  if (combo?.versions) {
    const catMap = {love:'연애',career:'직업',money:'재물',self:'성격',general:'종합'};
    const cat = catMap[situation] || '종합';
    const matched = combo.versions.find(v => v.category?.includes(cat));
    if (matched) return lang === 'ko' ? matched.ko : matched.vi;
  }
  return getFallbackResponse(situation, nextId);
}

function getFallbackIntro(sit) {
  const map = {
    love: {ko:"연애할 때 마음을 쉽게 주지 않는 편이죠? 아니면 한 번 주면 올인하는 타입이거나. 어느 쪽이든, 지금 답을 찾고 있는 거잖아요.", vi:"Trong tình yêu, bạn không dễ trao tình cảm, hoặc một khi trao thì all-in? Dù thế nào, bạn đang tìm câu trả lời."},
    career: {ko:"지금 하는 일에 대해 '이게 맞나?' 싶은 순간이 있죠. 그 고민 자체가 당신이 진지한 사람이라는 뜻이에요.", vi:"Có lúc bạn tự hỏi 'Đây có đúng không?' về công việc hiện tại. Chính sự trăn trở đó cho thấy bạn là người nghiêm túc."},
    money: {ko:"돈 걱정 없이 살고 싶은 마음, 누구나 같아요. 근데 당신의 돈 습관에는 당신만의 패턴이 있어요.", vi:"Ai cũng muốn sống không lo tiền. Nhưng thói quen tiền bạc của bạn có pattern riêng."},
    self: {ko:"가끔 '나는 왜 이럴까?' 싶을 때가 있죠. 그 질문을 하는 것 자체가 성장이에요.", vi:"Đôi khi bạn tự hỏi 'Sao mình lại thế nhỉ?'. Chính việc đặt câu hỏi đó đã là trưởng thành."},
    general: {ko:"인생에서 지금 어디쯤 와 있는 건지 궁금하죠? 한번 같이 살펴봐요.", vi:"Bạn đang tự hỏi mình đang ở đâu trong cuộc đời? Hãy cùng xem nhé."}
  };
  return (map[sit] || map.general)[lang] || map.general.ko;
}

function getFallbackIlgan(sit) {
  return lang === 'ko'
    ? '당신은 꽤 특별한 조합을 가진 사람이에요. 강점도 있고 조심할 점도 있는데, 결국 그 모든 게 당신을 당신답게 만드는 거예요. 자세한 분석은 곧 업데이트될 예정이에요.'
    : 'Bạn có sự kết hợp khá đặc biệt. Có điểm mạnh và cũng có điều cần chú ý, nhưng tất cả tạo nên con người bạn. Phân tích chi tiết sẽ sớm được cập nhật.';
}

function getFallbackResponse(sit, nextId) {
  return lang === 'ko'
    ? '좋은 질문이에요. 당신의 성향을 보면, 지금 느끼는 감정은 자연스러운 거예요. 중요한 건 그 감정을 인정하고, 한 걸음씩 나아가는 거예요. 당신은 생각보다 잘하고 있어요.'
    : 'Câu hỏi hay đó. Nhìn vào xu hướng của bạn, cảm xúc hiện tại là tự nhiên. Điều quan trọng là thừa nhận cảm xúc đó và tiến từng bước một. Bạn đang làm tốt hơn bạn nghĩ.';
}

// fadeUp 애니메이션
const style = document.createElement('style');
style.textContent = '@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}';
document.head.appendChild(style);
