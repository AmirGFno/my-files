/* verifies the live move announcement actually advances during playback */
const fs = require('fs');
const { JSDOM } = require('jsdom');
const ROOT = require('path').join(__dirname, '../../web');
const dom = new JSDOM(fs.readFileSync(ROOT + '/index.html', 'utf8'), {
  url: 'http://localhost/#/learn/3x3/lbl/yellow-edges-permute',
  pretendToBeVisual: true, runScripts: 'outside-only',
});
const { window } = dom;
window.HTMLCanvasElement.prototype.getContext = function () {
  return new Proxy({}, {
    get: (t, k) => (k === 'createLinearGradient' ? () => ({ addColorStop() {} }) : () => {}),
    set: () => true,
  });
};
Object.defineProperty(window.HTMLCanvasElement.prototype, 'clientWidth', { get: () => 240 });
window.HTMLElement.prototype.getBoundingClientRect = () => ({ width: 240, height: 240, top: 0, left: 0 });
window.matchMedia = () => ({ matches: false, addEventListener() {} });
window.devicePixelRatio = 1;
window.scrollTo = () => {};
window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
for (const src of ['js/cube-engine.js', 'data/methods.js', 'js/app.js']) {
  window.eval(fs.readFileSync(ROOT + '/' + src, 'utf8'));
}
const doc = window.document;
const playBtn = [...doc.querySelectorAll('.fig__btn--play')].find(b => b.textContent.includes('اجرای'));
if (!playBtn) { console.log('BAD no play button'); process.exit(1); }
playBtn.dispatchEvent(new window.MouseEvent('click', { bubbles: true }));
const live = doc.querySelector('.fig__live');
setTimeout(() => {
  const mid = live.textContent;
  console.log('after ~350ms:', JSON.stringify(mid));
  setTimeout(() => {
    console.log('after ~7s  :', JSON.stringify(live.textContent));
    console.log('button now  :', JSON.stringify(playBtn.textContent));
    const okMid = /حرکت/.test(mid);
    const okEnd = /تمام/.test(live.textContent) && /دوباره/.test(playBtn.textContent);
    console.log((okMid ? 'OK  ' : 'BAD ') + 'announces move numbers');
    console.log((okEnd ? 'OK  ' : 'BAD ') + 'announces completion and offers replay');
    process.exit(okMid && okEnd ? 0 : 1);
  }, 6500);
}, 350);
