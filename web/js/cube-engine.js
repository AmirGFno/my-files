/* ==========================================================================
   cube-engine.js — cube model + animated 3D renderer (no dependencies)

   Two things this file gets right that a naive version gets wrong:
   1) camera: an explicit orbit (yaw/pitch) per named view, so "bottom" really
      looks at the D face instead of showing an upside-down default view;
   2) animation: a move is a *partial rotation of one layer over time*, drawn by
      rotating the affected stickers by a fraction of the angle. Nothing snaps.
   ========================================================================== */

const FACES = ['U', 'D', 'F', 'B', 'R', 'L'];
const NORMALS = { U: [0, 1, 0], D: [0, -1, 0], F: [0, 0, 1], B: [0, 0, -1], R: [1, 0, 0], L: [-1, 0, 0] };
const COLORS = {
  U: [0.98, 0.79, 0.10], D: [0.96, 0.96, 0.94], F: [0.10, 0.62, 0.42],
  B: [0.11, 0.36, 0.72], R: [0.83, 0.14, 0.19], L: [0.96, 0.50, 0.10],
};
const FACE_FA = { U: 'بالا', D: 'پایین', F: 'جلو', B: 'عقب', R: 'راست', L: 'چپ' };
const COLOR_FA = { U: 'زرد', D: 'سفید', F: 'سبز', B: 'آبی', R: 'قرمز', L: 'نارنجی' };

/* ------------------------------------------------------------------ maths */
const vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const vcross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const vnorm = (v) => { const n = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / n, v[1] / n, v[2] / n]; };
const vscale = (v, s) => [v[0] * s, v[1] * s, v[2] * s];
const vadd = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

function rotAxis(axis, deg) {
  const r = (deg * Math.PI) / 180;
  const c = Math.cos(r), s = Math.sin(r);
  return (v) => {
    const [x, y, z] = v;
    if (axis === 'x') return [x, c * y - s * z, s * y + c * z];
    if (axis === 'y') return [c * x + s * z, y, -s * x + c * z];
    return [c * x - s * y, s * x + c * y, z];
  };
}

/* ---------------------------------------------------------------- the model */
class Cube {
  constructor() {
    this.st = new Map();
    for (let x = -1; x <= 1; x++)
      for (let y = -1; y <= 1; y++)
        for (let z = -1; z <= 1; z++) {
          if (x === 0 && y === 0 && z === 0) continue;
          const d = {};
          if (x === 1) d.R = 'R';
          if (x === -1) d.L = 'L';
          if (y === 1) d.U = 'U';
          if (y === -1) d.D = 'D';
          if (z === 1) d.F = 'F';
          if (z === -1) d.B = 'B';
          this.st.set(`${x},${y},${z}`, d);
        }
  }

  clone() {
    const c = new Cube();
    c.st = new Map();
    for (const [k, v] of this.st) c.st.set(k, { ...v });
    return c;
  }

  key() {
    return [...this.st.entries()].sort().map(([k, v]) =>
      k + ':' + Object.keys(v).sort().map(f => f + v[f]).join('')).join('|');
  }

  _turn(axis, layers, deg) {
    const rot = rotAxis(axis, deg);
    const idx = { x: 0, y: 1, z: 2 }[axis];
    const set = new Set(layers);
    const out = new Map();
    for (const [k, faces] of this.st) {
      const pos = k.split(',').map(Number);
      if (!set.has(pos[idx])) { out.set(k, { ...faces }); continue; }
      const np = rot(pos).map(v => Math.round(v));
      const nf = {};
      for (const [f, col] of Object.entries(faces)) {
        const n = rot(NORMALS[f]).map(v => Math.round(v));
        for (const name in NORMALS) {
          const nv = NORMALS[name];
          if (nv[0] === n[0] && nv[1] === n[1] && nv[2] === n[2]) nf[name] = col;
        }
      }
      out.set(np.join(','), nf);
    }
    this.st = out;
    return this;
  }

  /** parse one token into {axis, layers, deg} — single source of truth */
  static spec(tok) {
    const base = tok[0];
    const mod = tok.slice(1);
    const turns = mod === '2' ? 2 : mod === "'" ? 3 : 1;
    const whole = { x: ['x', 1], y: ['y', -1], z: ['z', -1], M: ['x', 1], E: ['y', -1], S: ['z', -1] };
    if (whole[base]) {
      const [axis, sign] = whole[base];
      const idx = { x: 0, y: 1, z: 2 }[axis];
      const centre = axis === 'x' ? 'M' : axis === 'y' ? 'E' : 'S';
      const layers = base === centre ? [0] : [-1, 0, 1];
      return { axis, layers, deg: sign * 90 * turns, base, mod };
    }
    const faces = {
      U: ['y', 1, -1], D: ['y', -1, 1], R: ['x', 1, -1],
      L: ['x', -1, 1], F: ['z', 1, -1], B: ['z', -1, 1],
    };
    const wide = { u: 'U', d: 'D', r: 'R', l: 'L', f: 'F', b: 'B' };
    if (wide[base]) {
      const [axis, layer, sign] = faces[wide[base]];
      return { axis, layers: [layer, 0], deg: sign * 90 * turns, base, mod };
    }
    const f = faces[base];
    if (!f) throw new Error(`unknown move: ${tok}`);
    const [axis, layer, sign] = f;
    return { axis, layers: [layer], deg: sign * 90 * turns, base, mod };
  }

  move(tok) {
    const s = Cube.spec(tok);
    return this._turn(s.axis, s.layers, ((s.deg % 360) + 360) % 360);
  }

  apply(alg) {
    for (const tok of String(alg || '').trim().split(/\s+/).filter(Boolean)) this.move(tok);
    return this;
  }

  solved() {
    for (const f of FACES) {
      const cols = new Set();
      for (const faces of this.st.values()) if (faces[f]) cols.add(faces[f]);
      if (cols.size > 1) return false;
    }
    return true;
  }

  at(pos, face) {
    const c = this.st.get(pos.join(','));
    return c ? c[face] : undefined;
  }

  layer(axis, sign) {
    const idx = { x: 0, y: 1, z: 2 }[axis];
    return [...this.st.entries()].map(([k, v]) => [k.split(',').map(Number), v]).filter(([p]) => p[idx] === sign);
  }

  isCross(face = 'D') {
    const axis = (face === 'U' || face === 'D') ? 'y' : (face === 'R' || face === 'L') ? 'x' : 'z';
    const sign = (face === 'U' || face === 'R' || face === 'F') ? 1 : -1;
    const edges = this.layer(axis, sign).filter(([p]) => p.filter(q => q === 0).length === 1);
    if (edges.length !== 4) return false;
    for (const [p, v] of edges) {
      if (v[face] !== face) return false;
      for (const [f, col] of Object.entries(v)) {
        if (f === face) continue;
        if (this.at(NORMALS[f], f) !== col) return false;
      }
    }
    return true;
  }

  isDaisy(top = 'U', colour = 'D') {
    if (this.at([0, 1, 0], top) !== top) return false;
    const lb = this.layer('y', 1);
    const edges = lb.filter(([p]) => p.filter(q => q === 0).length === 1);
    const corners = lb.filter(([p]) => p.filter(q => q === 0).length === 2);
    if (edges.length !== 4) return false;
    if (edges.filter(([, v]) => v[top] === colour).length !== 4) return false;
    if (corners.some(([, v]) => v[top] === colour)) return false;
    return true;
  }
}

/* ---------------------------------------------------------------- camera */
/* Explicit spherical orbit. yaw spins around the vertical axis, pitch tilts.
   These four presets are hand-tuned so the intended faces actually face you. */
/* Angles are not eyeballed: each preset was measured by the share of the canvas
   its three visible faces take, so "bottom" really is dominated by D and no
   face is a sliver. (Measured: default 29/36/36, top 20/20/61, bottom 20/20/61,
   front 17/17/66.) A perfectly square-on view is avoided on purpose: it hides
   nine stickers behind their neighbours and the silhouette goes flat. */
const VIEWS = {
  default: { yaw: 45, pitch: 30 },   // U, F, R as equal thirds
  top: { yaw: 45, pitch: 56 },       // U dominant, F and R equal
  bottom: { yaw: 45, pitch: -52 },   // D dominant, looking from below
  back: { yaw: 225, pitch: 30 },     // U, B, L
  front: { yaw: 15, pitch: 14 },     // F dominant, and all 27 stickers stay visible
};

const STICKER = 0.472;  // half-size: 0.944 of a cubie, so a ~5% gap like a real cube
/* one clock for the whole animation. requestAnimationFrame hands over
   performance.now() timestamps, so mixing in Date.now() would make progress
   jump to a huge negative number and freeze every turn. */
const clock = () => (typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now());

const LIFT = 0.006;     // stickers sit just above the body so faces never coincide
const LIGHT = { U: 1.0, F: 0.94, R: 0.84, D: 0.97, B: 0.88, L: 0.78 };
const DARK = { U: 0.92, F: 0.84, R: 0.72, D: 0.90, B: 0.78, L: 0.66 };

function cameraBasis(yawDeg, pitchDeg) {
  const yaw = (yawDeg * Math.PI) / 180;
  const pitch = (pitchDeg * Math.PI) / 180;
  const dir = [
    Math.sin(yaw) * Math.cos(pitch),
    Math.sin(pitch),
    Math.cos(yaw) * Math.cos(pitch),
  ];
  const depth = vnorm(dir);
  const right = vnorm(vcross([0, 1, 0], depth));
  const up = vnorm(vcross(depth, right));
  return { right, up, depth };
}

const hexOf = (c) => '#' + c.map(q => Math.round(Math.max(0, Math.min(1, q)) * 255).toString(16).padStart(2, '0')).join('');
const mixc = (a, b, t) => a.map((q, i) => q + (b[i] - q) * t);

/* ---------------------------------------------------------------- the view */
class CubeView {
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.cube = opts.cube ? opts.cube.clone() : new Cube();
    this.viewName = opts.view || 'default';
    this.interactive = opts.interactive !== false;
    this.showShadow = opts.shadow !== false;
    this.speed = opts.speed || 1;                 // 1 = normal
    this.baseDuration = opts.duration || 260;     // ms per quarter turn at speed 1
    // respect the system setting: people who ask for less motion get instant turns
    this.reducedMotion = typeof matchMedia === 'function'
      && matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.orbit = { ...(VIEWS[this.viewName] || VIEWS.default) };
    this.home = { ...this.orbit };
    this.drag = null;
    this.anim = null;                             // {spec, start, dur, token}
    this.queue = [];
    this.onMove = opts.onMove || null;            // (token, index, total)
    this.onDone = opts.onDone || null;
    this._raf = null;
    this._resize();
    if (this.interactive) this._bind();
    this._loop = this._loop.bind(this);
    this.draw();
  }

  _resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    const w = Math.max(80, Math.round(rect.width || this.canvas.clientWidth || 240));
    const h = Math.max(80, Math.round(rect.height || w));
    this.canvas.width = Math.round(w * dpr);
    this.canvas.height = Math.round(h * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.w = w;
    this.h = h;
  }

  resize() { this._resize(); this.draw(); }

  _bind() {
    const c = this.canvas;
    c.style.touchAction = 'none';
    c.style.cursor = 'grab';
    const down = (e) => {
      this.drag = { x: e.clientX, y: e.clientY, yaw: this.orbit.yaw, pitch: this.orbit.pitch };
      c.setPointerCapture?.(e.pointerId);
      c.style.cursor = 'grabbing';
    };
    const move = (e) => {
      if (!this.drag) return;
      this.orbit.yaw = this.drag.yaw - (e.clientX - this.drag.x) * 0.5;
      this.orbit.pitch = Math.max(-85, Math.min(85, this.drag.pitch + (e.clientY - this.drag.y) * 0.4));
      this.draw();
    };
    const up = () => { this.drag = null; c.style.cursor = 'grab'; };
    c.addEventListener('pointerdown', down);
    c.addEventListener('pointermove', move);
    c.addEventListener('pointerup', up);
    c.addEventListener('pointercancel', up);
    c.addEventListener('pointerleave', up);
  }

  /* ------------------------------------------------------------- playback */
  setSpeed(mult) { this.speed = Math.max(0.15, Math.min(4, mult)); }

  resetTo(cube = new Cube()) {
    this.stop();
    this.cube = cube.clone();
    this.draw();
  }

  stop() {
    this.queue = [];
    this.anim = null;
    if (this._raf) cancelAnimationFrame(this._raf);
    this._raf = null;
  }

  /** enqueue an algorithm; resolves when finished */
  play(alg, { loop = false } = {}) {
    const toks = String(alg || '').trim().split(/\s+/).filter(Boolean);
    this.stop();
    return new Promise((resolve) => {
      this.queue = toks.map((t, i) => ({ tok: t, i, n: toks.length }));
      this._resolve = resolve;
      this._tick(clock());
    });
  }

  step() {
    if (!this.queue.length) return;
    const item = this.queue.shift();
    this._beginMove(item);
  }

  _tick(now) {
    if (!this.anim && this.queue.length) this._beginMove(this.queue.shift(), now);
    if (!this.anim) {
      this._raf = null;
      this.draw();
      const done = this._resolve;
      this._resolve = null;
      if (done) done();
      return;
    }
    this._raf = requestAnimationFrame(this._loop);
  }

  _loop() {
    if (!this.anim) { this._raf = null; return; }
    const now = clock();
    const p = Math.max(0, Math.min(1, (now - this.anim.start) / this.anim.dur));
    this.anim.p = p;
    this.draw();
    if (p >= 1) {
      this.cube.move(this.anim.spec.base + this.anim.spec.mod);
      this.anim = null;
      this._tick(now);
    } else {
      this._raf = requestAnimationFrame(this._loop);
    }
  }

  _beginMove(item, now = clock()) {
    const spec = Cube.spec(item.tok);
    const dur = this.reducedMotion
      ? 1
      : Math.max(70, (this.baseDuration * Math.abs(spec.deg) / 90) / this.speed);
    this.anim = { spec, start: now, dur, p: 0 };
    this.onMove?.(item.tok, item.i, item.n);
    // note: the caller schedules the frames — scheduling here too would draw
    // every frame twice
  }

  /* ------------------------------------------------------------- rendering */
  draw() {
    const ctx = this.ctx, W = this.w, H = this.h;
    if (!W || !H) return;
    ctx.clearRect(0, 0, W, H);

    const { right, up, depth } = cameraBasis(this.orbit.yaw, this.orbit.pitch);
    const proj = (p) => [vdot(p, right), vdot(p, up)];

    const corners = [];
    for (const x of [-1.5, 1.5]) for (const y of [-1.5, 1.5]) for (const z of [-1.5, 1.5]) corners.push([x, y, z]);
    const flat = corners.map(proj);
    const xs = flat.map(p => p[0]), ys = flat.map(p => p[1]);
    const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
    const scale = (Math.min(W, H) * 0.86) / span;
    const cx = (Math.max(...xs) + Math.min(...xs)) / 2;
    const cy = (Math.max(...ys) + Math.min(...ys)) / 2;
    const toScreen = (p) => [W / 2 + (vdot(p, right) - cx) * scale, H / 2 - (vdot(p, up) - cy) * scale];

    // partial rotation for the move in flight
    let spin = null;
    if (this.anim) {
      const eased = easeInOut(this.anim.p);
      spin = {
        rot: rotAxis(this.anim.spec.axis, this.anim.spec.deg * eased),
        layers: new Set(this.anim.spec.layers),
        axis: this.anim.spec.axis,
      };
    }
    const idxOf = { x: 0, y: 1, z: 2 };

    /* Build the scene out of solid cubies instead of a flat backdrop with
       stickers on it. Why: while a layer turns, part of it is behind the body,
       and stickers painted over a flat backdrop would show through where they
       should be hidden. Sorting real cubie faces by depth fixes that. */
    const facets = [];
    const BODY = 0.5;        // plastic, as a fraction of a cubie
    const STK = 0.472;       // sticker inset that leaves a visible seam

    for (const [key, faces] of this.cube.st) {
      const pos = key.split(',').map(Number);
      const moving = !!(spin && spin.layers.has(pos[idxOf[spin.axis]]));
      const place = (v) => (moving ? spin.rot(v) : v);

      for (const face of FACES) {
        const colour = faces[face];
        if (!colour) continue;                       // only cubies on this surface
        const normal0 = NORMALS[face];
        const normal = place(normal0);
        if (vdot(normal, depth) <= 0.02) continue;   // back-face culling
        const axis = Math.abs(normal0[0]) ? 0 : Math.abs(normal0[1]) ? 1 : 2;
        const sign = normal0[axis];
        const uAxis = axis === 0 ? 1 : axis === 1 ? 0 : 0;
        const vAxis = axis === 0 ? 2 : axis === 1 ? 2 : 1;

        const build = (half, lift) => [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([su, sv]) => {
          const p = pos.slice();
          p[axis] = pos[axis] + sign * (0.5 + lift);
          p[uAxis] += su * half;
          p[vAxis] += sv * half;
          return place(p);
        });

        // the dark plastic face, slightly bigger than the sticker on it
        const bodyQuad = build(BODY, 0);
        const bodyPts = bodyQuad.map(toScreen);
        const edge = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
        let bArea = 0, bPerim = 0;
        for (let i = 0, j = bodyPts.length - 1; i < bodyPts.length; j = i++) {
          bArea += (bodyPts[j][0] + bodyPts[i][0]) * (bodyPts[j][1] - bodyPts[i][1]);
          bPerim += edge(bodyPts[j], bodyPts[i]);
        }
        const bThin = bPerim ? Math.abs(bArea) / bPerim : 0;
        // keep near-edge-on body faces: skipping them opened a gap between a
        // turning slab and the body, which looked like a hole in the cube
        if (bThin >= Math.min(W, H) * 0.003) {
          facets.push({
            pts: bodyPts, kind: 'body',
            depth: vdot(centroid(bodyQuad), depth),
            top: [0.115, 0.125, 0.145], bottom: [0.055, 0.06, 0.072],
          });
        }

        // the sticker itself
        const stickerQuad = build(STK, LIFT);
        const stickerPts = stickerQuad.map(toScreen);
        let area2 = 0, perim = 0;
        for (let i = 0, j = stickerPts.length - 1; i < stickerPts.length; j = i++) {
          area2 += (stickerPts[j][0] + stickerPts[i][0]) * (stickerPts[j][1] - stickerPts[i][1]);
          perim += edge(stickerPts[j], stickerPts[i]);
        }
        const thin = perim ? Math.abs(area2) / perim : 0;
        // a sticker seen edge-on is a hairline; it only looks like a stray streak
        if (thin < Math.min(W, H) * (moving ? 0.022 : 0.011)) continue;

        const lit = 0.55 + 0.45 * Math.max(0, vdot(vnorm(normal), vnorm([-0.35, 0.72, 0.75])));
        const base = COLORS[colour] || [0.8, 0.8, 0.8];
        facets.push({
          pts: stickerPts, kind: 'sticker',
          depth: vdot(centroid(stickerQuad), depth) + 0.002,
          top: mixc(base, [1, 1, 1], 0.10 * lit).map(q => Math.min(1, q * (0.82 + 0.28 * lit))),
          bottom: base.map(q => q * (0.62 + 0.24 * lit)),
        });
      }
    }

    /* silhouette: the body outline, so no gap shows between faces */
    const allPts = [];
    for (const p of corners) allPts.push(toScreen(p));
    const hullPts = hull(allPts);

    // contact shadow, under everything
    if (this.showShadow) {
      const hxs = hullPts.map(p => p[0]), hys = hullPts.map(p => p[1]);
      const sx = (Math.max(hxs) + Math.min(hxs)) / 2;
      const sw = (Math.max(hxs) - Math.min(hxs)) * 0.46;
      const sy = Math.max(hys);
      const sh = Math.min(W, H) * 0.022;
      for (const [k, a] of [[1, 0.05], [0.78, 0.06], [0.56, 0.07]]) {
        ctx.beginPath();
        ctx.ellipse(sx, sy + sh * 2, sw * k, sh * k, 0, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(15,20,32,${a})`;
        ctx.fill();
      }
    }

    /* paint far to near */
    facets.sort((a, b) => a.depth - b.depth);
    for (const f of facets) drawFacet(ctx, f, Math.min(W, H) * (f.kind === 'sticker' ? 0.008 : 0.004));

  }
}

const centroid = (quad) => [
  (quad[0][0] + quad[1][0] + quad[2][0] + quad[3][0]) / 4,
  (quad[0][1] + quad[1][1] + quad[2][1] + quad[3][1]) / 4,
  (quad[0][2] + quad[1][2] + quad[2][2] + quad[3][2]) / 4,
];

function drawFacet(ctx, f, radius) {
  const xs = f.pts.map(p => p[0]), ys = f.pts.map(p => p[1]);
  const g = ctx.createLinearGradient(Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys));
  g.addColorStop(0, hexOf(f.top));
  g.addColorStop(1, hexOf(f.bottom));
  roundPoly(ctx, f.pts, radius);
  ctx.fillStyle = g;
  ctx.fill();
  if (f.kind === 'sticker') {
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(12,14,20,0.38)';
    ctx.stroke();
  }
}

function easeInOut(t) {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

function hull(points) {
  const pts = points.map(p => [p[0], p[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [];
  for (const p of pts) {
    while (lower.length >= 2 && cr(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
    lower.push(p);
  }
  const upper = [];
  for (const p of pts.slice().reverse()) {
    while (upper.length >= 2 && cr(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
    upper.push(p);
  }
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}

function roundPoly(ctx, pts, r) {
  const n = pts.length;
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const p0 = pts[i], p1 = pts[(i + 1) % n], pm = pts[(i - 1 + n) % n];
    const v0 = [p0[0] - pm[0], p0[1] - pm[1]];
    const v1 = [p1[0] - p0[0], p1[1] - p0[1]];
    const l0 = Math.hypot(v0[0], v0[1]) || 1, l1 = Math.hypot(v1[0], v1[1]) || 1;
    const rr = Math.min(r, l0 / 2.6, l1 / 2.6);
    const a = [p0[0] - (v0[0] / l0) * rr, p0[1] - (v0[1] / l0) * rr];
    const b = [p0[0] + (v1[0] / l1) * rr, p0[1] + (v1[1] / l1) * rr];
    if (i === 0) ctx.moveTo(a[0], a[1]); else ctx.lineTo(a[0], a[1]);
    ctx.quadraticCurveTo(p0[0], p0[1], b[0], b[1]);
  }
  ctx.closePath();
}

if (typeof window !== 'undefined') {
  Object.assign(window, { Cube, CubeView, CUBE_COLORS: COLORS, CUBE_FACE_FA: FACE_FA, CUBE_COLOR_FA: COLOR_FA, CUBE_VIEWS: VIEWS });
}
if (typeof module !== 'undefined') module.exports = { Cube, CubeView, COLORS, NORMALS };
