/* strip.js — six frames of one turn, side by side, for eyeballing the animation.
   Usage: node tools/cube/strip.js R   →  tools/cube/out/strip-R.png */
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const src = fs.readFileSync(path.join(__dirname, '../../web/js/cube-engine.js'), 'utf8');
const win = {};
new Function('window', 'module', 'exports', 'requestAnimationFrame', 'cancelAnimationFrame', 'devicePixelRatio',
  src + '\nwindow.__x = { Cube, CubeView };')(win, {}, {}, () => {}, () => {}, 1);
const { Cube, CubeView } = win.__x;

function raster(W, H, bg) {
  const buf = new Float32Array(W * H * 3).fill(bg);
  let clip = null, g = null;
  const parse = (c) => [parseInt(c.slice(1, 3), 16) / 255, parseInt(c.slice(3, 5), 16) / 255, parseInt(c.slice(5, 7), 16) / 255];
  const api = {
    _c: [], setTransform() {}, clearRect() {}, beginPath() { this._c = []; },
    moveTo(x, y) { this._c.push([x, y]); }, lineTo(x, y) { this._c.push([x, y]); },
    quadraticCurveTo(a, b, x, y) { this._c.push([x, y]); },
    closePath() { clip = this._c.slice(); this._c = []; },
    createLinearGradient(x0, y0, x1, y1) {
      g = { c0: '#000', c1: '#000', x0, y0, x1, y1, addColorStop(t, c) { if (t === 0) this.c0 = c; else this.c1 = c; } };
      return g;
    },
    fill() {
      if (!clip || clip.length < 3) return;
      const a = g ? parse(g.c0) : [0, 0, 0], b = g ? parse(g.c1) : a;
      const xs = clip.map(p => p[0]), ys = clip.map(p => p[1]);
      const inP = (x, y) => {
        let c = false;
        for (let i = 0, j = clip.length - 1; i < clip.length; j = i++) {
          const [xi, yi] = clip[i], [xj, yj] = clip[j];
          if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) c = !c;
        }
        return c;
      };
      const gx = g ? g.x1 - g.x0 : 1, gy = g ? g.y1 - g.y0 : 1, den = (gx * gx + gy * gy) || 1;
      for (let y = Math.max(0, Math.floor(Math.min(...ys))); y <= Math.min(H - 1, Math.ceil(Math.max(...ys))); y++)
        for (let x = Math.max(0, Math.floor(Math.min(...xs))); x <= Math.min(W - 1, Math.ceil(Math.max(...xs))); x++) {
          if (!inP(x + 0.5, y + 0.5)) continue;
          let t = g ? ((x - g.x0) * gx + (y - g.y0) * gy) / den : 0;
          t = Math.max(0, Math.min(1, t));
          const i = (y * W + x) * 3;
          for (let k = 0; k < 3; k++) buf[i + k] = a[k] + (b[k] - a[k]) * t;
        }
    },
    stroke() {},
    ellipse(x, y, rx, ry) {
      for (let py = Math.max(0, Math.floor(y - ry)); py <= Math.min(H - 1, Math.ceil(y + ry)); py++)
        for (let px = Math.max(0, Math.floor(x - rx)); px <= Math.min(W - 1, Math.ceil(x + rx)); px++) {
          const dx = (px - x) / rx, dy = (py - y) / ry;
          if (dx * dx + dy * dy <= 1) { const i = (py * W + px) * 3; for (let k = 0; k < 3; k++) buf[i + k] *= 0.94; }
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
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

const S = 260, N = 6, tok = process.argv[2] || 'R';
const W = S * N, H = S;
const sheet = new Float32Array(W * H * 3).fill(0.97);
for (let i = 0; i < N; i++) {
  const { api, buf } = raster(S, S, 0.98);
  const canvas = {
    width: S, height: S, style: {}, getContext: () => api,
    getBoundingClientRect: () => ({ width: S, height: S }),
    addEventListener() {}, setPointerCapture() {}, clientWidth: S,
  };
  const v = new CubeView(canvas, { view: 'default', interactive: false });
  v.resize();
  const p = i / (N - 1);
  if (p > 0) v.anim = { spec: Cube.spec(tok), start: 0, dur: 100, p: Math.min(0.999, p) };
  v.draw();
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const a = (y * S + x) * 3, b = (y * W + i * S + x) * 3;
    for (let k = 0; k < 3; k++) sheet[b + k] = buf[a + k];
  }
}
fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
fs.writeFileSync(path.join(__dirname, 'out', 'strip-' + tok.replace("'", 'p') + '.png'), png(W, H, sheet));
console.log('wrote out/strip-' + tok + '.png');
