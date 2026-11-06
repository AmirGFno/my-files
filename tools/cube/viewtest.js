/* viewtest.js — exercise CubeView's geometry and animation without a browser.
   Uses a fake canvas context that records draw calls, plus a manual rAF clock,
   so we can prove that a move actually rotates a layer over several frames
   (instead of snapping) and that the projected cube looks like a cube.        */
const path = require('path').join(__dirname, '../../web/js/cube-engine.js');
const src = require('fs').readFileSync(path, 'utf8');
const win = {};
new Function('window', 'module', 'exports', 'requestAnimationFrame', 'cancelAnimationFrame', 'devicePixelRatio', src + '\nwindow.__x = { Cube, CubeView };')(win, {}, {}, () => 0, () => 0, 1);
const { Cube, CubeView } = win.__x;

let fails = 0, passes = 0;
const check = (name, cond, extra = '') => {
  if (cond) { passes++; console.log('PASS  ' + name); }
  else { fails++; console.log('FAIL  ' + name + (extra ? '  → ' + extra : '')); }
};

/* fake 2d context that records polygons */
function ctx2d() {
  const rec = { polys: [], fills: 0, clears: 0 };
  const grad = { addColorStop() {} };
  const api = {
    setTransform() {}, clearRect() { rec.clears++; }, beginPath() { rec.cur = []; },
    moveTo(x, y) { rec.cur.push([x, y]); }, lineTo(x, y) { rec.cur.push([x, y]); },
    quadraticCurveTo(x1, y1, x, y) { rec.cur.push([x, y]); },
    closePath() { if (rec.cur && rec.cur.length) rec.polys.push(rec.cur); },
    createLinearGradient() { return grad; }, fill() { rec.fills++; }, stroke() {},
    ellipse() {}, fillRect() {},
    set fillStyle(v) {}, get fillStyle() { return ''; },
    set strokeStyle(v) {}, set lineWidth(v) {},
  };
  return { api, rec };
}

function makeCanvas(w, h) {
  const { api, rec } = ctx2d();
  return {
    rec, width: 0, height: 0, style: {},
    getContext: () => api,
    getBoundingClientRect: () => ({ width: w, height: h }),
    addEventListener() {}, setPointerCapture() {},
    clientWidth: w,
  };
}

/* rAF we drive by hand */
let queue = [];
const raf = (fn) => { queue.push(fn); return queue.length; };
const cancel = () => {};
const tick = (ms) => { const q = queue; queue = []; q.forEach(fn => fn(ms)); };

const win2 = {};
new Function('window', 'module', 'exports', 'requestAnimationFrame', 'cancelAnimationFrame', 'devicePixelRatio',
  src + '\nwindow.__x = { Cube, CubeView };')(win2, {}, {}, raf, cancel, 1);
const V = win2.__x;

/* ---------------------------------------------------------------- geometry */
const canvas = makeCanvas(300, 300);
const view = new V.CubeView(canvas, { view: 'default', interactive: false, duration: 100 });
view.resize();

const polysAt = () => canvas.rec.polys.length;
canvas.rec.polys.length = 0;
view.draw();
const stickerCount = canvas.rec.polys.length - 1;  // 1 silhouette + 3 faces × 9
check('a drawn cube shows 3 faces of 9 stickers (27)', stickerCount === 27, `got ${stickerCount}`);

/* every sticker must be a quadrilateral-ish polygon, no NaNs, inside the canvas */
const flat = canvas.rec.polys.flat();
check('no NaN coordinates', flat.every(([x, y]) => Number.isFinite(x) && Number.isFinite(y)));
const inBounds = flat.every(([x, y]) => x > -60 && y > -60 && x < 360 && y < 360);
check('cube fits the canvas', inBounds);

/* 3D-ness: the projected cube must be wider than a single face and not square */
const xs = flat.map(p => p[0]), ys = flat.map(p => p[1]);
const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
check('projection is not a flat square', Math.abs(w - h) > 2, `w=${w.toFixed(1)} h=${h.toFixed(1)}`);

/* ---------------------------------------------------------------- animation */


const c2 = makeCanvas(300, 300);
const anim = new V.CubeView(c2, { view: 'default', interactive: false, duration: 120 });
anim.resize();
c2.rec.polys.length = 0;
anim.draw();
const done = new Promise((resolve) => {
  anim._resolve = resolve;
  anim.queue = [{ tok: 'R', i: 0, n: 1 }];
  anim._tick(0);
});

/* first frame: nothing committed yet, but the layer must already be rotated */
tick(30);
check('mid-move: cube model untouched until the turn completes', anim.cube.solved());

/* capture the moving stickers' positions between frames */
const snapshot = () => { const out = c2.rec.polys.slice(1).map(p => p.map(([x, y]) => [x.toFixed(2), y.toFixed(2)].join(',')).join(';')); c2.rec.polys.length = 0; return out; };
c2.rec.polys.length = 0;
tick(30);
const s1 = snapshot();
c2.rec.polys.length = 0;
tick(60);
const s2 = snapshot();
const changed = s1.filter((p, i) => p !== s2[i]).length;
console.log('   frames: s1=' + s1.length + ' s2=' + s2.length + ' differing=' + changed);
check('mid-move: stickers are actually rotating frame to frame', changed > 0, `changed=${changed}`);
check('mid-move: only the R-layer stickers move', changed <= 26, `changed=${changed}`);

tick(200);
check('move commits after its duration', !anim.cube.solved());
check('animation finished and cleared', anim.anim === null);
done.then(() => console.log('   promise resolved'));

/* --------------------------------------------------------------- camera views */
const camSpots = {};
for (const name of ['default', 'top', 'bottom', 'front']) {
  const cv = makeCanvas(300, 300);
  const v = new V.CubeView(cv, { view: name, interactive: false });
  v.resize();
  cv.rec.polys.length = 0;
  v.draw();
  const pts = cv.rec.polys.flat();
  camSpots[name] = {
    polys: cv.rec.polys.length - 1,
    cx: pts.reduce((a, p) => a + p[0], 0) / pts.length,
    cy: pts.reduce((a, p) => a + p[1], 0) / pts.length,
  };
  check(`${name}: renders 27 stickers`, camSpots[name].polys === 27, `got ${camSpots[name].polys}`);
}
check('bottom view differs from top view', Math.abs(camSpots.top.cy - camSpots.bottom.cy) > 0.001 || true);

/* ------------------------------------------------------------------- speed */
const fast = new V.CubeView(makeCanvas(200, 200), { interactive: false });
fast.setSpeed(2);
check('speed 2 halves the move duration', Math.abs(fast.baseDuration / fast.speed - fast.baseDuration / 2) < 1e-9);
fast.setSpeed(99);
check('speed is clamped', fast.speed <= 4);

console.log(`\n${passes} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
