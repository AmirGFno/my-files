const fs = require('fs');
const { JSDOM } = require('jsdom');
const ROOT = require('path').join(__dirname, '../../web');
const html = fs.readFileSync(ROOT + '/index.html', 'utf8');

const dom = new JSDOM(html, { url: 'http://localhost/#/', pretendToBeVisual: true, runScripts: 'outside-only' });
const { window } = dom;

// canvas 2d stub so CubeView can "draw"
const ctxStub = () => new Proxy({}, {
  get: (t, k) => {
    if (k === 'createLinearGradient') return () => ({ addColorStop() {} });
    if (k === 'canvas') return {};
    return () => {};
  },
  set: () => true,
});
window.HTMLCanvasElement.prototype.getContext = function () { return ctxStub(); };
Object.defineProperty(window.HTMLCanvasElement.prototype, 'clientWidth', { get: () => 240 });
window.HTMLElement.prototype.getBoundingClientRect = function () { return { width: 240, height: 240, top: 0, left: 0 }; };
window.matchMedia = window.matchMedia || (() => ({ matches: false, addEventListener() {} }));
window.devicePixelRatio = 1;
window.scrollTo = () => {};
window.requestAnimationFrame = (cb) => setTimeout(cb, 0);

const errors = [];
window.addEventListener('error', (e) => errors.push(e.message));

// load scripts in order
for (const src of ['js/cube-engine.js', 'data/methods.js', 'js/app.js']) {
  window.eval(fs.readFileSync(ROOT + '/' + src, 'utf8'));
}

const routes = ['#/', '#/p/3x3', '#/learn/3x3/lbl', '#/learn/3x3/lbl/cross',
                '#/learn/3x3/lbl/layer2', '#/learn/3x3/lbl/yellow-edges-permute',
                '#/learn/3x3/cfop', '#/p/2x2', '#/learn/2x2/ortega', '#/algs', '#/nope'];

function check(hash) {
  window.location.hash = hash;
  window.dispatchEvent(new window.Event('hashchange'));
  const main = window.document.querySelector('#main');
  const text = main.textContent.replace(/\s+/g, ' ').trim();
  const cards = main.querySelectorAll('.card').length;
  const alts = main.querySelectorAll('.alt').length;
  const figs = main.querySelectorAll('.fig').length;
  console.log(`${hash.padEnd(42)} text=${String(text.length).padStart(5)} cards=${cards} figs=${figs} alts=${alts} | ${text.slice(0, 46)}`);
  if (text.length < 40) errors.push('empty route: ' + hash);
}

for (const r of routes) check(r);

// check RTL/latin mixing in rendered algorithm rows
window.location.hash = '#/learn/3x3/lbl/cross';
window.dispatchEvent(new window.Event('hashchange'));
const code = window.document.querySelector('.alg code');
console.log('first algorithm code:', code && code.textContent);

// simulate clicking an algorithm (should not throw)
try {
  window.document.querySelector('.alg').dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
  console.log('algorithm click: ok');
} catch (e) { errors.push('click: ' + e.message); }

setTimeout(() => {
  if (errors.length) { console.log('\nERRORS:'); errors.forEach(e => console.log(' -', e)); process.exit(1); }
  console.log('\nAll routes rendered without errors.');
}, 400);

/* ---- extra checks for the new figure player and large mode ---- */
const doc = window.document;
const stepRoutes = ['#/learn/3x3/lbl/cross', '#/learn/3x3/lbl/corners1', '#/learn/3x3/lbl/layer2',
  '#/learn/3x3/lbl/yellow-cross', '#/learn/3x3/lbl/yellow-corners-orient',
  '#/learn/3x3/lbl/yellow-corners-permute', '#/learn/3x3/lbl/yellow-edges-permute'];

function checkStep(hash) {
  window.location.hash = hash;
  window.dispatchEvent(new window.Event('hashchange'));
  const main = doc.querySelector('#main');
  const figs = main.querySelectorAll('.fig');
  const playable = [...main.querySelectorAll('.fig__btn--play')].filter(b => b.textContent.includes('اجرای'));
  const segs = main.querySelectorAll('.fig__seg');
  const big = main.querySelectorAll('.fig__btn--big');
  const canv = main.querySelectorAll('canvas');
  const ok = figs.length >= 1 && playable.length >= 1 && segs.length >= 2 && big.length >= 1 && canv.length >= 1;
  console.log(`${ok ? 'OK  ' : 'BAD '} ${hash.padEnd(46)} figs=${figs.length} playable=${playable.length} segs=${segs.length} big=${big.length} canvas=${canv.length}`);
  if (!ok) errors.push('figure controls missing on ' + hash);
}

for (const r of stepRoutes) checkStep(r);

/* click "run step" and the big button */
window.location.hash = '#/learn/3x3/lbl/yellow-edges-permute';
window.dispatchEvent(new window.Event('hashchange'));
const main = doc.querySelector('#main');
const run = [...main.querySelectorAll('.fig__btn--play')].find(b => b.textContent.includes('اجرای'));
run.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
setTimeout(() => {
  const bigBtn = main.querySelector('.fig__btn--big');
  bigBtn.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
  const modal = doc.querySelector('.modal');
  console.log((modal ? 'OK  ' : 'BAD ') + 'large mode opens a dialog');
  if (!modal) errors.push('modal did not open');
  const close = doc.querySelector('.modal__close');
  if (close) close.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
  console.log((doc.querySelector('.modal') ? 'BAD ' : 'OK  ') + 'large mode closes');

  /* the practice box: click every algorithm row, make sure nothing throws */
  window.location.hash = '#/learn/3x3/lbl/cross';
  window.dispatchEvent(new window.Event('hashchange'));
  const rows = [...doc.querySelectorAll('#main .alg')];
  rows.forEach(r => r.dispatchEvent(new window.MouseEvent('click', { bubbles: true })));
  console.log('clicked ' + rows.length + ' algorithm rows');

  setTimeout(() => {
    console.log('\nerrors: ' + (errors.length ? errors.join(' | ') : 'none'));
    process.exit(errors.length ? 1 : 0);
  }, 300);
}, 200);
