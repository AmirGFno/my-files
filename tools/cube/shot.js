/* screenshot.js — render a CubeView through a tiny software rasterizer and write
   a PNG, so the cube can actually be looked at without a browser. */
const fs = require('fs');
const zlib = require('zlib');
const src = fs.readFileSync(require('path').join(__dirname, '../../web/js/cube-engine.js'), 'utf8');
const win = {};
new Function('window', 'module', 'exports', 'requestAnimationFrame', 'cancelAnimationFrame', 'devicePixelRatio',
  src + '\nwindow.__x = { Cube, CubeView };')(win, {}, {}, () => {}, () => {}, 1);
const { Cube, CubeView } = win.__x;

function raster(W, H) {
  const buf = new Float32Array(W * H * 3).fill(0.97);   // light backdrop
  const strokes = [];
  let clip = null;
  const parse = (c) => [parseInt(c.slice(1,3),16)/255, parseInt(c.slice(3,5),16)/255, parseInt(c.slice(5,7),16)/255];
  const api = {
    _g: null, _cur: [], _strokes: strokes,
    setTransform() {}, clearRect() {}, beginPath() { api._cur = []; },
    moveTo(x, y) { api._cur.push([x, y]); }, lineTo(x, y) { api._cur.push([x, y]); },
    quadraticCurveTo(x1, y1, x, y) { api._cur.push([x, y]); },
    closePath() { clip = api._cur.slice(); },
    createLinearGradient(x0, y0, x1, y1) {
      const g = { c0: '#000', c1: '#000', x0, y0, x1, y1, addColorStop(t, c) { if (t === 0) g.c0 = c; else g.c1 = c; } };
      api._g = g; return g;
    },
    fill() {
      if (!clip || clip.length < 3) return;
      const g = api._g;
      const a = g ? parse(g.c0) : [0.5, 0.5, 0.5];
      const b = g ? parse(g.c1) : a;
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
      const gx = (g ? g.x1 - g.x0 : 1) || 1, gy = (g ? g.y1 - g.y0 : 1) || 1;
      for (let y = minY; y <= maxY; y++) for (let x = minX; x <= maxX; x++) {
        if (!inside(x + 0.5, y + 0.5)) continue;
        let t = g ? ((x - g.x0) * gx + (y - g.y0) * gy) / (gx * gx + gy * gy) : 0;
        t = Math.max(0, Math.min(1, t));
        const i = (y * W + x) * 3;
        for (let k = 0; k < 3; k++) buf[i + k] = a[k] + (b[k] - a[k]) * t;
      }
    },
    stroke() { if (clip && clip.length >= 3) api._strokes.push(clip.slice()); },
    ellipse() {},
    set fillStyle(v) {}, set strokeStyle(v) {}, set lineWidth(v) {},
  };
  return { api, buf, strokes };
}

function png(W, H, buf) {
  const raw = Buffer.alloc((W * 3 + 1) * H);
  for (let y = 0; y < H; y++) {
    raw[y * (W * 3 + 1)] = 0;
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 3, o = y * (W * 3 + 1) + 1 + x * 3;
      raw[o] = Math.round(Math.max(0, Math.min(1, buf[i])) * 255);
      raw[o + 1] = Math.round(Math.max(0, Math.min(1, buf[i + 1])) * 255);
      raw[o + 2] = Math.round(Math.max(0, Math.min(1, buf[i + 2])) * 255);
    }
  }
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const t = Buffer.from(type);
    const body = Buffer.concat([t, data]);
    const crcTable = png.table || (png.table = (() => {
      const t2 = []; for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t2[n] = c >>> 0; } return t2;
    })());
    let crc = 0xffffffff;
    for (const b of body) crc = crcTable[(crc ^ b) & 0xff] ^ (crc >>> 8);
    const c = Buffer.alloc(4); c.writeUInt32BE((crc ^ 0xffffffff) >>> 0);
    return Buffer.concat([len, body, c]);
  };
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4);
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0)),
  ]);
}

function render({ view = 'default', alg = '', yaw, pitch, W = 300, mid = null, name }) {
  const { api, buf } = raster(W, W);
  const canvas = {
    width: W, height: W, style: {},
    getContext: () => api,
    getBoundingClientRect: () => ({ width: W, height: W }),
    addEventListener() {}, setPointerCapture() {}, clientWidth: W,
  };
  const v = new CubeView(canvas, { view, interactive: false, shadow: true });
  if (yaw != null) v.orbit = { yaw, pitch };
  v.resize();
  v.cube.apply(alg);
  if (mid) {  // freeze a move part-way through, to see real rotation
    v.anim = { spec: Cube.spec(mid.tok), start: 0, dur: 100, p: mid.p };
  }
  v.draw();
  fs.writeFileSync(require('path').join(__dirname, 'out', name + '.png'), png(W, W, buf));
  console.log('wrote', name + '.png');
}

render({ name: 'shot-default', view: 'default', W: 420 });
render({ name: 'shot-top', view: 'top', W: 440 });
render({ name: 'shot-bottom', view: 'bottom', W: 320 });
render({ name: 'shot-mid', view: 'default', mid: { tok: 'R', p: 0.45 }, W: 320 });
