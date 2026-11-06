/* ==========================================================================
   app.js — router + views. No framework, no build step.
   Routes:
     #/                         فهرست پازل‌ها
     #/p/3x3                    روش‌های یک پازل
     #/learn/3x3/lbl            معرفی یک روش + گام‌ها
     #/learn/3x3/lbl/cross      یک گام (همان قالب شش‌بخشی)
     #/algs                     جست‌وجوی الگوریتم‌ها
   ========================================================================== */

const faNum = (n) => String(n).replace(/[0-9]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[+d]);
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const LEVEL_FA = { beginner: 'مبتدی', mid: 'متوسط', pro: 'حرفه‌ای' };
const STATUS_FA = { ready: 'آماده', outline: 'اسکلت', planned: 'در برنامه' };

const getPuzzle = (id) => CONTENT.puzzles.find(p => p.id === id);
const getMethod = (pid, mid) => (getPuzzle(pid)?.methods || []).find(m => m.id === mid);
const getStep = (pid, mid, sid) => (getMethod(pid, mid)?.steps || []).find(s => s.id === sid);

/* -------------------------------------------------------------- html utils */
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) {
    if (kid == null || kid === false) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(kid));
  }
  return el;
}

const levelChip = (lvl) => h('span', { class: `chip chip--${lvl}` }, LEVEL_FA[lvl] || lvl);

function difficultyDots(n) {
  const wrap = h('span', { class: 'dots', title: `سختی ${n} از ۵` });
  for (let i = 1; i <= 5; i++) wrap.append(h('i', { class: i <= n ? 'on' : '' }));
  return wrap;
}

/* --------------------------------------------------------------- cube views */
const liveViews = [];
function mountCube(parent, opts = {}) {
  const canvas = h('canvas', { 'aria-label': opts.label || 'نمای سه‌بعدی مکعب' });
  parent.append(canvas);
  const view = new CubeView(canvas, { view: opts.view || 'default', interactive: opts.interactive !== false });
  if (opts.alg) view.cube.apply(opts.alg);
  view.draw();
  liveViews.push(view);
  return view;
}

/* --------------------------------------------------------------- theme */
function applyTheme(name) {
  document.documentElement.dataset.theme = name;
  try { localStorage.setItem('robik-theme', name); } catch (e) {}
}
const savedTheme = (() => { try { return localStorage.getItem('robik-theme'); } catch (e) { return null; } })();
applyTheme(savedTheme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
$('#themeBtn')?.addEventListener('click', () => {
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
});

/* --------------------------------------------------------------- views */
function viewHome() {
  const main = $('#main');
  main.innerHTML = '';
  liveViews.length = 0;

  /* hero */
  const hero = h('section', { class: 'hero' });
  const stage = h('div', { class: 'hero__stage' });
  hero.append(
    h('div', {},
      h('span', { class: 'kicker' }, 'آموزش تعاملی'),
      h('h1', { class: 'display' }, 'روبیک را بفهم، نه حفظ کن'),
      h('p', { class: 'lede' },
        'هر گام را با یک مکعب سه‌بعدی می‌بینی، الگوریتم‌ها را با یک کلیک اجرا می‌کنی، ' +
        'و برای هر مرحله چند روش داری تا خودت انتخاب کنی.'),
      h('div', { class: 'hero__cta' },
        h('a', { class: 'btn btn--primary', href: '#/learn/3x3/lbl' }, 'شروع از صفر'),
        h('a', { class: 'btn btn--ghost', href: '#/p/3x3' }, 'همه‌ی روش‌ها')
      )
    ),
    stage
  );
  main.append(hero);
  const heroView = mountCube(stage, { view: 'default' });

  /* puzzles */
  const sec = h('section', { class: 'section' },
    h('div', { class: 'section__head' },
      h('h2', {}, 'پازل‌ها'),
      h('span', { class: 'hint' }, 'اول ۳×۳؛ بعد بقیه یکی‌یکی اضافه می‌شوند.')
    )
  );
  const grid = h('div', { class: 'grid grid--puzzles' });
  for (const p of CONTENT.puzzles) {
    const planned = p.status === 'planned';
    const card = h('a', {
      class: `card puzzle-card ${planned ? 'is-planned' : ''}`,
      href: planned ? '#/p/' + p.id : '#/p/' + p.id,
    });
    const mini = h('div', { class: 'mini' });
    card.append(mini,
      h('h3', {}, p.name, h('span', { class: 'en' }, p.en)),
      h('p', {}, p.intro || ''),
      h('div', { class: 'card__meta' },
        h('span', { class: 'chip' }, `${faNum((p.methods || []).length)} روش`),
        h('span', { class: 'chip chip--muted' }, STATUS_FA[p.status] || '')
      )
    );
    grid.append(card);
    const miniCanvas = h('canvas', { 'aria-hidden': 'true' });
    mini.append(miniCanvas);
    requestAnimationFrame(() => {
      const v = new CubeView(miniCanvas, { interactive: false, view: 'default' });
      v.resize();
      v.draw();
    });
  }
  sec.append(grid);
  main.append(sec);

  /* how it works */
  main.append(h('section', { class: 'section' },
    h('div', { class: 'section__head' }, h('h2', {}, 'هر صفحه‌ی گام، شش بخش ثابت دارد')),
    h('div', { class: 'grid', style: 'grid-template-columns:repeat(auto-fit,minmax(210px,1fr))' },
      ...[
        ['هدف گام', 'در پایان این صفحه چه چیزی حل شده است.'],
        ['چرا این‌جوری', 'منطق پشت روش، بدون فرمول.'],
        ['قدم‌ها', 'شماره‌دار، هر قدم یک کار.'],
        ['الگوریتم', 'با یک کلیک روی مکعب تمرین اجرا می‌شود.'],
        ['اگر گیر کردی', 'خطاهای رایج و راه خروج.'],
        ['جایگزین‌ها', 'تکنیک‌های دیگر همین گام.'],
      ].map(([t, d], i) => h('div', { class: 'card' },
        h('h3', {}, `${faNum(i + 1)}. ${t}`),
        h('p', {}, d)
      ))
    )
  ));

  heroView.resize(); heroView.draw();
}

function viewPuzzle(pid) {
  const p = getPuzzle(pid);
  const main = $('#main');
  main.innerHTML = '';
  liveViews.length = 0;
  if (!p) return viewNotFound();

  main.append(h('div', { class: 'crumbs' },
    h('a', { href: '#/' }, 'پازل‌ها'), '‹', h('span', {}, p.name)));

  main.append(h('div', { class: 'section__head', style: 'margin-bottom:26px' },
    h('div', {},
      h('span', { class: 'kicker' }, STATUS_FA[p.status] || ''),
      h('h1', { class: 'display' }, p.name),
      h('p', { class: 'lede' }, p.intro || '')
    )
  ));

  const grid = h('div', { class: 'grid grid--methods' });
  if (!(p.methods || []).length) {
    grid.append(h('div', { class: 'card' },
      h('h3', {}, 'این پازل در نوبت است'),
      h('p', {}, 'ساختارش آماده است؛ محتوای گام‌به‌گام به‌زودی اضافه می‌شود.')));
  }
  for (const m of p.methods || []) {
    const ready = m.status === 'ready';
    grid.append(h('a', { class: `card ${ready ? '' : 'is-planned'}`, href: `#/learn/${p.id}/${m.id}` },
      h('h3', {}, m.name, h('span', { class: 'en' }, m.en)),
      h('p', {}, m.summary || ''),
      h('div', { class: 'card__meta' },
        levelChip(m.level),
        h('span', { class: 'chip' }, `${faNum(m.algorithms ?? '?')} الگوریتم`),
        h('span', { class: 'chip' }, `${faNum((m.steps || []).length)} گام`),
        h('span', { class: 'chip chip--muted' }, STATUS_FA[m.status] || '')
      )
    ));
  }
  main.append(grid);
}

function viewMethod(pid, mid) {
  const p = getPuzzle(pid), m = getMethod(pid, mid);
  const main = $('#main');
  main.innerHTML = '';
  liveViews.length = 0;
  if (!p || !m) return viewNotFound();

  main.append(h('div', { class: 'crumbs' },
    h('a', { href: '#/' }, 'پازل‌ها'), '‹',
    h('a', { href: `#/p/${p.id}` }, p.name), '‹',
    h('span', {}, m.name)));

  const head = h('div', { class: 'article__head' },
    h('span', { class: 'kicker' }, `${LEVEL_FA[m.level]} · ${faNum(m.algorithms ?? '?')} الگوریتم`),
    h('h1', {}, m.name),
    m.en ? h('div', { class: 'en', style: 'font-size:12px;color:var(--ink-faint)' }, m.en) : null,
    h('p', { class: 'lede', style: 'margin-top:14px' }, m.summary || ''),
    m.why ? h('p', { style: 'margin-top:10px;color:var(--ink-soft);max-width:62ch;font-size:15px' }, m.why) : null
  );

  const steps = m.steps || [];
  const body = h('div', { class: 'article' }, head);

  if (steps.length) {
    body.append(h('div', { class: 'block__label' }, h('span', { class: 'n' }, '۱'), 'گام‌های این روش'));
    const list = h('div', { class: 'grid', style: 'grid-template-columns:repeat(auto-fill,minmax(250px,1fr))' });
    steps.forEach((s, i) => {
      list.append(h('a', { class: 'card', href: `#/learn/${p.id}/${m.id}/${s.id}` },
        h('h3', {}, `${faNum(i + 1)}. ${s.title}`),
        h('p', {}, s.goal || ''),
        h('div', { class: 'card__meta' },
          h('span', { class: 'chip' }, `${faNum((s.algorithms || []).length)} الگوریتم`),
          (s.alternatives || []).length ? h('span', { class: 'chip chip--accent' },
            `${faNum(s.alternatives.length)} جایگزین`) : null
        )
      ));
    });
    body.append(list);
  } else {
    body.append(h('div', { class: 'note' },
      h('strong', {}, 'این روش فعلاً اسکلت دارد'),
      'ساختار گام‌ها مشخص است؛ متن کامل هر گام به‌ترتیب نوشته می‌شود.'));
  }

  main.append(h('div', { class: 'learn' }, h('div', {}), body));
}

function viewStep(pid, mid, sid) {
  const p = getPuzzle(pid), m = getMethod(pid, mid), s = getStep(pid, mid, sid);
  const main = $('#main');
  main.innerHTML = '';
  liveViews.length = 0;
  if (!p || !m || !s) return viewNotFound();

  const steps = m.steps || [];
  const idx = steps.findIndex(x => x.id === s.id);
  const prev = steps[idx - 1];
  const next = steps[idx + 1];

  /* ---------------------------------------------------------- side nav */
  const nav = h('aside', { class: 'sidenav' },
    h('h4', {}, `${p.name} · ${m.name}`),
    h('ol', {}, ...steps.map((x, i) => h('li', {},
      h('a', {
        href: `#/learn/${p.id}/${m.id}/${x.id}`,
        class: x.id === s.id ? 'is-active' : '',
      }, x.title)
    )))
  );

  /* ---------------------------------------------------------- article */
  const art = h('article', { class: 'article' });

  art.append(h('div', { class: 'article__head' },
    h('div', { class: 'crumbs' },
      h('a', { href: `#/p/${p.id}` }, p.name), '‹',
      h('a', { href: `#/learn/${p.id}/${m.id}` }, m.name), '‹',
      h('span', {}, `گام ${faNum(idx + 1)} از ${faNum(steps.length)}`)),
    h('h1', {}, s.title),
    s.goal ? h('p', { class: 'lede', style: 'margin-top:10px' }, s.goal) : null
  ));

  const body = h('div', { class: 'stepbody' });

  /* 1 — figures */
  if ((s.states || []).length) {
    const figs = h('div', { class: 'figs' });
    for (const st of s.states) {
      const fig = h('figure', { class: 'fig' });
      const holder = h('div');
      fig.append(
        h('div', { class: 'fig-top' },
          h('span', {}, st.label || ''),
          st.alg ? h('button', {
            class: 'alg-play', style: 'background:none;border:0;cursor:pointer;color:var(--accent);font-size:11.5px',
            onclick: (e) => { e.preventDefault(); playOn(st.alg, view); },
          }, '▶ اجرا') : null
        ),
        holder,
        st.alg ? h('figcaption', { dir: 'ltr', style: 'font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.04em' }, st.alg) : null
      );
      figs.append(fig);
      const view = new CubeView(h('canvas'), { view: st.view || 'default', interactive: true });
      view.cube.apply(st.alg || '');
      view.draw();
      holder.append(view.canvas);
      requestAnimationFrame(() => { view.resize(); view.draw(); });
      liveViews.push(view);
    }
    body.append(figs);
  }

  /* 2 — why */
  if (s.why) {
    body.append(h('div', { class: 'block' },
      h('div', { class: 'block__label' }, h('span', { class: 'n' }, '۲'), 'چرا این‌جوری؟'),
      h('p', {}, s.why)));
  }

  /* 3 — steps */
  if ((s.steps || []).length) {
    body.append(h('div', { class: 'block' },
      h('div', { class: 'block__label' }, h('span', { class: 'n' }, '۳'), 'قدم‌ها'),
      h('ol', { class: 'steps-list' }, ...s.steps.map(st => h('li', {},
        h('div', {}, h('strong', {}, st.t), h('span', {}, st.d || '')))))));
  }

  /* 4 — algorithms + practice cube */
  if ((s.algorithms || []).length) {
    const algs = h('div', { class: 'algs' });
    algs.append(...s.algorithms.map(a => h('div', {
      class: 'alg',
      role: 'button', tabindex: '0',
      onclick: () => playOn(a.alg, practice),
      onkeydown: (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); playOn(a.alg, practice); } },
    },
      h('code', {}, a.alg),
      h('span', { class: 'alg-label' }, a.label || ''),
      h('span', { class: 'alg-play' }, '▶ تمرین')
    )));

    const practiceHolder = h('div', { class: 'fig', style: 'max-width:230px' });
    const practice = new CubeView(h('canvas'), { view: 'top', interactive: true });
    practiceHolder.append(practice.canvas, h('figcaption', {}, 'جعبه تمرین · الگوریتم را کلیک کن'));
    liveViews.push(practice);
    requestAnimationFrame(() => { practice.resize(); practice.draw(); });

    body.append(h('div', { class: 'block' },
      h('div', { class: 'block__label' }, h('span', { class: 'n' }, '۴'), 'الگوریتم‌های این گام'),
      h('div', { style: 'display:grid;grid-template-columns:minmax(0,1fr) 210px;gap:14px;align-items:start' },
        algs, practiceHolder),
      h('p', { style: 'font-size:12.5px;color:var(--ink-faint);margin-top:8px' },
        'روی هر الگوریتم کلیک کن تا روی جعبه تمرین اجرا شود. مکعب را با انگشت یا ماوس هم می‌توانی بچرخانی.')
    ));
    window.__practice = practice;
  }

  /* 5 — mistakes */
  if ((s.mistakes || []).length) {
    body.append(h('div', { class: 'block' },
      h('div', { class: 'block__label', style: 'color:#9c3f2a' }, h('span', { class: 'n', style: 'background:#9c3f2a' }, '۵'), 'اگر گیر کردی'),
      h('div', { class: 'note note--warn' },
        h('strong', {}, 'خطاهای رایج'),
        h('ul', {}, ...s.mistakes.map(x => h('li', {}, x))))));
  }

  /* 6 — alternatives */
  if ((s.alternatives || []).length) {
    const list = h('div', { class: 'alt-list' });
    for (const a of s.alternatives) {
      const inner = h('div', { class: `alt ${a.recommended ? 'is-recommended' : ''}` },
        h('h4', {}, a.name, a.recommended ? h('span', { class: 'chip chip--beginner' }, 'پیشنهادی') : null),
        h('p', {}, a.why || ''),
        h('div', { class: 'alt__stats' },
          h('span', {}, `${faNum(a.moves)} حرکت`),
          h('span', {}, 'سختی ', difficultyDots(a.difficulty || 1)),
          a.ref && a.ref !== s.id
            ? h('a', { href: `#/learn/${p.id}/${m.id}/${a.ref}`, style: 'color:var(--accent);font-weight:600' }, 'توضیح کامل ›')
            : h('span', { class: 'chip chip--muted' }, 'همین صفحه')
        )
      );
      list.append(a.ref && a.ref !== s.id
        ? h('a', { href: `#/learn/${p.id}/${m.id}/${a.ref}`, style: 'display:block' }, inner)
        : inner);
    }
    body.append(h('div', { class: 'block' },
      h('div', { class: 'block__label' }, h('span', { class: 'n' }, '۶'), 'جایگزین‌های همین گام'),
      h('p', { style: 'font-size:13.5px;color:var(--ink-faint);margin-bottom:10px' },
        'همین گام را چند تکنیک دیگر هم می‌شود زد. سختی از ۱ (ساده) تا ۵ است.'),
      list));
  }

  /* pager */
  body.append(h('div', { class: 'pager' },
    next ? h('a', { class: 'next', href: `#/learn/${p.id}/${m.id}/${next.id}` }, `گام بعدی: ${next.title} ›`) : h('span'),
    prev ? h('a', { class: 'prev', href: `#/learn/${p.id}/${m.id}/${prev.id}` }, `‹ ${prev.title}`) : h('span')
  ));

  art.append(body);
  main.append(h('div', { class: 'learn' }, nav, art));

  // highlight current in the side nav on mobile scroll
  requestAnimationFrame(() => $$('canvas', art).forEach(cv => {
    const v = liveViews.find(x => x.canvas === cv);
    if (v) { v.resize(); v.draw(); }
  }));
}

function viewAlgs() {
  const main = $('#main');
  main.innerHTML = '';
  liveViews.length = 0;

  const rows = [];
  for (const p of CONTENT.puzzles)
    for (const m of p.methods || [])
      for (const s of m.steps || [])
        for (const a of s.algorithms || [])
          rows.push({ puzzle: p.name, method: m.name, step: s.title, alg: a.alg, label: a.label, level: m.level, href: `#/learn/${p.id}/${m.id}/${s.id}` });

  main.append(h('div', { class: 'section__head' },
    h('div', {},
      h('span', { class: 'kicker' }, `${faNum(rows.length)} الگوریتم`),
      h('h1', { class: 'display', style: 'font-size:30px' }, 'الگوریتم‌ها'),
      h('p', { class: 'lede' }, 'همه‌ی الگوریتم‌های پلتفرم، با جست‌وجو. هر ردیف تو را به گام مربوط می‌برد.'))));

  const input = h('input', { type: 'search', placeholder: 'جست‌وجو: R U R یا «صلیب»…', 'aria-label': 'جست‌وجوی الگوریتم' });
  const filters = h('div', { class: 'filters' });
  const levels = ['all', 'beginner', 'mid', 'pro'];
  let active = 'all';
  levels.forEach(l => filters.append(h('button', {
    class: l === 'all' ? 'is-on' : '',
    onclick: (e) => {
      active = l;
      $$('button', filters).forEach(b => b.classList.remove('is-on'));
      e.currentTarget.classList.add('is-on');
      render();
    },
  }, l === 'all' ? 'همه' : LEVEL_FA[l])));

  const tableWrap = h('div');
  main.append(h('div', { class: 'searchbar' }, input, filters), tableWrap);

  function render() {
    const q = input.value.trim().toLowerCase();
    const shown = rows.filter(r =>
      (active === 'all' || r.level === active) &&
      (!q || (r.alg + ' ' + r.label + ' ' + r.step + ' ' + r.method).toLowerCase().includes(q)));
    tableWrap.innerHTML = '';
    if (!shown.length) {
      tableWrap.append(h('div', { class: 'note' }, h('strong', {}, 'چیزی پیدا نشد'), 'عبارت دیگری را امتحان کن.'));
      return;
    }
    const table = h('table', { class: 'alg-table' },
      h('thead', {}, h('tr', {},
        h('th', {}, 'الگوریتم'), h('th', {}, 'توضیح'), h('th', {}, 'گام'), h('th', {}, 'روش'))),
      h('tbody', {}, ...shown.map(r => h('tr', {},
        h('td', {}, h('a', { href: r.href }, h('code', {}, r.alg))),
        h('td', {}, r.label || '—'),
        h('td', {}, r.step),
        h('td', {}, h('span', { class: `chip chip--${r.level}` }, r.method))
      ))));
    tableWrap.append(table);
  }
  input.addEventListener('input', render);
  render();
}

function viewNotFound() {
  const main = $('#main');
  main.innerHTML = '';
  main.append(h('div', { style: 'padding:60px 0;text-align:center' },
    h('h1', { class: 'display', style: 'font-size:26px' }, 'این صفحه پیدا نشد'),
    h('p', { class: 'lede', style: 'margin:10px auto 20px' }, 'شاید آدرس تغییر کرده باشد.'),
    h('a', { class: 'btn btn--primary', href: '#/' }, 'بازگشت به خانه')));
}

/* --------------------------------------------------------------- playback */
let playingToken = 0;
async function playOn(alg, view) {
  if (!view) return;
  const token = ++playingToken;
  const btnEls = $$('.alg.is-playing');
  btnEls.forEach(b => b.classList.remove('is-playing'));
  view.cube = new Cube();
  view.draw();
  const moves = alg.trim().split(/\s+/).filter(Boolean);
  for (const mv of moves) {
    if (token !== playingToken) return;
    view.cube.move(mv);
    view.draw();
    await new Promise(r => setTimeout(r, 150));
  }
}

/* --------------------------------------------------------------- router */
function parse() {
  const hash = location.hash.replace(/^#\/?/, '');
  return hash.split('/').filter(Boolean);
}

function render() {
  const parts = parse();
  $$('.tab').forEach(t => t.classList.remove('is-active'));
  let navKey = null;

  if (!parts.length) { viewHome(); navKey = 'puzzles'; }
  else if (parts[0] === 'p') { viewPuzzle(parts[1]); navKey = 'puzzles'; }
  else if (parts[0] === 'learn') {
    navKey = 'learn';
    if (parts.length >= 4) viewStep(parts[1], parts[2], parts[3]);
    else if (parts.length === 3) viewMethod(parts[1], parts[2]);
    else viewPuzzle(parts[1]);
  }
  else if (parts[0] === 'algs') { viewAlgs(); navKey = 'algs'; }
  else viewNotFound();

  if (navKey) $(`.tab[data-nav="${navKey}"]`)?.classList.add('is-active');
  window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
}

window.addEventListener('hashchange', render);
window.addEventListener('resize', () => {
  clearTimeout(window.__rz);
  window.__rz = setTimeout(() => liveViews.forEach(v => { v.resize(); v.draw(); }), 120);
});
render();
