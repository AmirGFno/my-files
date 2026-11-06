/* render every step scene straight from methods.js, so what the site shows is
   what gets inspected */
const fs = require('fs'), zlib = require('zlib');
const src = fs.readFileSync(require('path').join(__dirname, '../../web/js/cube-engine.js'), 'utf8');
const win = {};
new Function('window', 'module', 'exports', 'requestAnimationFrame', 'cancelAnimationFrame', 'devicePixelRatio',
  src + '\nwindow.__x = { Cube, CubeView };')(win, {}, {}, () => {}, () => {}, 1);
const { Cube, CubeView } = win.__x;
const mod = { exports: {} };
new Function('module', 'exports', 'window', fs.readFileSync(require('path').join(__dirname, '../../web/data/methods.js'), 'utf8') + '\nmodule.exports = CONTENT;')(mod, mod.exports, undefined);
const steps = mod.exports.puzzles[0].methods[0].steps;

/* --- tiny raster (same as shot.js) --- */
function raster(W, H, bg) {
  const buf = new Float32Array(W * H * 3).fill(bg);
  let clip = null, g = null;
  const parse = (c) => [parseInt(c.slice(1,3),16)/255, parseInt(c.slice(3,5),16)/255, parseInt(c.slice(5,7),16)/255];
  const api = {
    setTransform() {}, clearRect() {}, beginPath() {}, moveTo(x, y) { this._c.push([x, y]); },
    lineTo(x, y) { this._c.push([x, y]); }, quadraticCurveTo(x1, y1, x, y) { this._c.push([x, y]); },
    _c: [], closePath() { clip = this._c.slice(); this._c = []; },
    createLinearGradient(x0, y0, x1, y1) {
      g = { c0: '#000', c1: '#000', x0, y0, x1, y1, addColorStop(t, c) { if (t === 0) this.c0 = c; else this.c1 = c; } };
      return g;
    },
    fill() {
      if (!clip || clip.length < 3) return;
      const a = g ? parse(g.c0) : [0, 0, 0], b = g ? parse(g.c1) : a;
      const xs = clip.map(p => p[0]), ys = clip.map(p => p[1]);
      const minX = Math.max(0, Math.floor(Math.min(...xs))), maxX = Math.min(W - 1, Math.ceil(Math.max(...xs)));
      const minY = Math.max(0, Math.floor(Math.min(...ys))), maxY = Math.min(H - 1, Math.ceil(Math.max(...ys)));
      const inside = (x, y) => {
        let c = false;
        for (let i = 0, j = clip.length - 1; i < clip.length; j = i++) {
          const [xi, yi] = clip[i], [xj, yj] = clip[j];
          if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) c = !c;
        }
        return c;
      };
      const gx = g ? g.x1 - g.x0 : 1, gy = g ? g.y1 - g.y0 : 1;
      const denom = (gx * gx + gy * gy) || 1;
      for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
        if (!inside(x + 0.5, y + 0.5)) continue;
        let t = g ? ((x - g.x0) * gx + (y - g.y0) * gy) / denom : 0;
        t = Math.max(0, Math.min(1, t));
        const i = (y * W + x) * 3;
        for (let k = 0; k < 3; k++) buf[i + k] = a[k] + (b[k] - a[k]) * t;
      }
    },
    stroke() {},
    ellipse(x, y, rx, ry) {   // support the shadow, so the picture matches the site
      for (let py = Math.max(0, Math.floor(y - ry)); py <= Math.min(H - 1, Math.ceil(y + ry)); py++)
        for (let px = Math.max(0, Math.floor(x - rx)); px <= Math.min(W - 1, Math.ceil(x + rx)); px++) {
          const dx = (px - x) / rx, dy = (py - y) / ry;
          if (dx * dx + dy * dy <= 1) { const i = (py * W + px) * 3; for (let k = 0; k < 3; k++) buf[i + k] *= 0.93; }
        }
    },
    set fillStyle(v) {}, set strokeStyle(v) {}, set lineWidth(v) {},
  };
  return { api, buf };
}
function png(W, H, buf) {
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let y = 0; y < H; y++) {
    raw[y * (W * 3 + 1)] = 0;
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 3, o = y * (W * 3 + 1) + 1 + x * 3;
      for (let k = 0; k < 3; k++) raw[o + k] = Math.round(Math.max(0, Math.min(1, buf[i + k])) * 255);
    }
  }
  const table = (() => { const t = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const body = Buffer.concat([Buffer.from(type), data]);
    let crc = 0xffffffff;
    for (const b of body) crc = table[(crc ^ b) & 0xff] ^ (crc >>> 8);
    const c = Buffer.alloc(4); c.writeUInt32BE((crc ^ 0xffffffff) >>> 0);
    return Buffer.concat([len, body, c]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

const S = 240, GAP = 10, COLS = 3;
const tiles = steps.map(st => st.states.map(s => ({ ...s, step: st.id }))).flat();
const rows = Math.ceil(tiles.length / COLS);
const W = COLS * (S + GAP) + GAP, H = rows * (S + GAP + 16) + GAP;
const canvasBuf = new Float32Array(W * H * 3).fill(0.94);

/* render each tile and blit into the sheet */
tiles.forEach((tile, i) => {
  const { api, buf } = raster(S, S, 0.97);
  const canvas = { width: S, height: S, style: {}, getContext: () => api,
    getBoundingClientRect: () => ({ width: S, height: S }), addEventListener() {}, setPointerCapture() {}, clientWidth: S };
  const v = new CubeView(canvas, { view: tile.view || 'default', interactive: false });
  v.resize(); v.cube.apply(tile.alg || ''); v.draw();
  const cx = GAP + (i % COLS) * (S + GAP), cy = GAP + Math.floor(i / COLS) * (S + GAP + 16);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const a = (y * S + x) * 3, b = ((cy + y) * W + cx + x) * 3;
    for (let k = 0; k < 3; k++) canvasBuf[b + k] = buf[a + k];
  }
});
fs.writeFileSync(require('path').join(__dirname, 'out', 'scenes-sheet.png'), png(W, H, canvasBuf));
console.log('tiles:', tiles.length, '->', W + 'x' + H, 'scenes-sheet.png');
tiles.forEach((t, i) => console.log(String(i + 1).padStart(2), t.step.padEnd(24), (t.label || '').slice(0, 42)));
