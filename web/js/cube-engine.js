/* ==========================================================================
   cube-engine.js — a 3x3x3 cube model + interactive 3D renderer.
   No dependencies. Same geometry rules as the print engine (book/tools),
   so diagrams and the web app can never disagree.
   ========================================================================== */

const FACES = ['U', 'D', 'F', 'B', 'R', 'L'];
const NORMALS = {
  U: [0, 1, 0], D: [0, -1, 0], F: [0, 0, 1],
  B: [0, 0, -1], R: [1, 0, 0], L: [-1, 0, 0],
};
const COLORS = {
  U: [0.98, 0.79, 0.10],   // yellow
  D: [0.95, 0.95, 0.93],   // white
  F: [0.10, 0.62, 0.42],   // green
  B: [0.11, 0.36, 0.72],   // blue
  R: [0.83, 0.14, 0.19],   // red
  L: [0.96, 0.50, 0.10],   // orange
};
const FACE_FA = { U: 'بالا', D: 'پایین', F: 'جلو', B: 'عقب', R: 'راست', L: 'چپ' };
const COLOR_FA = { U: 'زرد', D: 'سفید', F: 'سبز', B: 'آبی', R: 'قرمز', L: 'نارنجی' };

/* ---------------------------------------------------------------- the model */
class Cube {
  constructor() {
    this.st = new Map();               // "x,y,z" -> {face: colour}
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
      k + ':' + Object.entries(v).sort().map(([f, c]) => f + c).join('')).join('|');
  }

  /** rotate one layer (or two, when wide) */
  _turn(axis, layer, deg, wide) {
    const rad = (deg * Math.PI) / 180;
    const c = Math.round(Math.cos(rad)), s = Math.round(Math.sin(rad));
    const rot = (v) => {
      const [x, y, z] = v;
      if (axis === 'x') return [x, c * y - s * z, s * y + c * z];
      if (axis === 'y') return [c * x + s * z, y, -s * x + c * z];
      return [c * x - s * y, s * x + c * y, z];
    };
    const idx = { x: 0, y: 1, z: 2 }[axis];
    const out = new Map();
    for (const [k, faces] of this.st) {
      const pos = k.split(',').map(Number);
      const keep = pos[idx] === layer || (wide && pos[idx] === 0);
      if (!keep) { out.set(k, { ...faces }); continue; }
      const np = rot(pos).map(Math.round);
      const nf = {};
      for (const [f, col] of Object.entries(faces)) {
        const n = rot(NORMALS[f]).map(Math.round);
        for (const [name, nv] of Object.entries(NORMALS))
          if (nv[0] === n[0] && nv[1] === n[1] && nv[2] === n[2]) nf[name] = col;
      }
      out.set(np.join(','), nf);
    }
    this.st = out;
    return this;
  }

  move(tok) {
    const base = tok[0];
    const mod = tok.slice(1);
    const deg = mod === '2' ? 2 : mod === "'" ? 3 : 1;
    const table = {
      U: ['y', 1, -1, false], D: ['y', -1, 1, false],
      R: ['x', 1, -1, false], L: ['x', -1, 1, false],
      F: ['z', 1, -1, false], B: ['z', -1, 1, false],
      u: ['y', 1, -1, true], d: ['y', -1, 1, true],
      r: ['x', 1, -1, true], l: ['x', -1, 1, true],
      f: ['z', 1, -1, true], b: ['z', -1, 1, true],
      M: ['x', 0, 1, false], E: ['y', 0, -1, false], S: ['z', 0, -1, false],
      x: ['x', 0, 1, true], y: ['y', 0, -1, true], z: ['z', 0, -1, true],
    };
    const t = table[base];
    if (!t) throw new Error(`unknown move: ${tok}`);
    const [axis, layer, sign, wide] = t;
    if ('xyz'.includes(base)) {
      this._turn(axis, 0, (sign * 90 * deg + 360) % 360, true);
      for (const l of [-1, 1]) this._turn(axis, l, (sign * 90 * deg + 360) % 360, false);
      // simplify: rotate everything at once
      const rad = (sign * 90 * deg * Math.PI) / 180;
      const c = Math.round(Math.cos(rad)), s = Math.round(Math.sin(rad));
      const rot = (v) => {
        const [x, y, z] = v;
        if (axis === 'x') return [x, c * y - s * z, s * y + c * z];
        if (axis === 'y') return [c * x + s * z, y, -s * x + c * z];
        return [c * x - s * y, s * x + c * y, z];
      };
      const out = new Map();
      for (const [k, faces] of this.st) {
        const np = rot(k.split(',').map(Number)).map(Math.round);
        const nf = {};
        for (const [f, col] of Object.entries(faces)) {
          const n = rot(NORMALS[f]).map(Math.round);
          for (const [name, nv] of Object.entries(NORMALS))
            if (nv[0] === n[0] && nv[1] === n[1] && nv[2] === n[2]) nf[name] = col;
        }
        out.set(np.join(','), nf);
      }
      this.st = out;
      return this;
    }
    return this._turn(axis, layer, (sign * 90 * deg + 360) % 360, wide);
  }

  apply(alg) {
    for (const tok of alg.trim().split(/\s+/).filter(Boolean)) this.move(tok);
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

  /** sticker colour of a cubie on a face */
  at(pos, face) {
    const c = this.st.get(pos.join(','));
    return c ? c[face] : undefined;
  }

  /** strict cross check, same rule as the book */
  isCross(face = 'D') {
    const idx = { x: 0, y: 1, z: 2 }[face === 'U' || face === 'D' ? 'y' : face === 'R' || face === 'L' ? 'x' : 'z'];
    const sign = face === 'U' || face === 'R' || face === 'F' ? 1 : -1;
    const edges = [...this.st.entries()].map(([k, v]) => [k.split(',').map(Number), v])
      .filter(([p]) => p[idx] === sign && p.filter(q => q === 0).length === 1);
    if (edges.length !== 4) return false;
    for (const [p, v] of edges) {
      if (v[face] !== face) return false;
      for (const [f, col] of Object.entries(v)) {
        if (f === face) continue;
        const centre = NORMALS[f].map(q => q);
        if (this.at(centre, f) !== col) return false;
      }
    }
    return true;
  }

  isDaisy(top = 'U', colour = 'D') {
    if (this.at([0, 1, 0], top) !== top) return false;
    const layer = [...this.st.entries()].map(([k, v]) => [k.split(',').map(Number), v])
      .filter(([p]) => p[1] === 1);
    const edges = layer.filter(([p]) => p.filter(q => q === 0).length === 1);
    const corners = layer.filter(([p]) => p.filter(q => q === 0).length === 2);
    if (edges.length !== 4) return false;
    if (edges.filter(([, v]) => v[top] === colour).length !== 4) return false;
    if (corners.filter(([, v]) => v[top] === colour).length > 0) return false;
    return true;
  }
}

/* ---------------------------------------------------------------- the view */
const VIEWS = {
  default: [0.60, 0.74, 0.94],
  top: [0.55, 1.05, 0.30],
  back: [-0.60, 0.74, -0.94],
  bottom: [0.52, -0.70, 0.92],
};
const LIGHT = { U: 1.00, F: 0.93, R: 0.82, D: 0.96, B: 0.88, L: 0.78 };

function norm(v) {
  const n = Math.hypot(...v);
  return v.map(q => q / n);
}
function cross3(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}
function dot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
function basis(dir) {
  const d = norm(dir);
  const worldUp = [0, 1, 0];
  const right = norm(cross3(worldUp, d));
  const up = norm(cross3(d, right));
  return { right, up, d };
}
function shade(c, f) {
  return c.map(q => Math.min(1, Math.max(0, q * f)));
}
function hex(c) {
  return '#' + c.map(q => Math.round(q * 255).toString(16).padStart(2, '0')).join('');
}

class CubeView {
  /** Interactive isometric cube.
   * @param {HTMLCanvasElement} canvas
   * @param {{size?:number, view?:string, interactive?:boolean}} opts
   */
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.cube = new Cube();
    this.viewName = opts.view || 'default';
    this.interactive = opts.interactive !== false;
    this.spin = { yaw: 0, pitch: 0, dragging: false, lx: 0, ly: 0 };
    this.highlight = null;
    this.queue = [];
    this.animating = false;
    this.resize();
    if (this.interactive) this._bind();
    this.draw();
  }

  resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    const size = Math.max(90, Math.round(rect.width || this.canvas.clientWidth || 240));
    this.canvas.width = size * dpr;
    this.canvas.height = size * dpr;
    this.canvas.style.height = size + 'px';
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.size = size;
  }

  _bind() {
    const c = this.canvas;
    c.style.cursor = 'grab';
    c.addEventListener('pointerdown', (e) => {
      this.spin.dragging = true;
      this.spin.lx = e.clientX;
      this.spin.ly = e.clientY;
      c.setPointerCapture(e.pointerId);
      c.style.cursor = 'grabbing';
    });
    c.addEventListener('pointermove', (e) => {
      if (!this.spin.dragging) return;
      this.spin.yaw += (e.clientX - this.spin.lx) * 0.01;
      this.spin.pitch = Math.max(-1.2, Math.min(1.2, this.spin.pitch + (e.clientY - this.spin.ly) * 0.008));
      this.spin.lx = e.clientX;
      this.spin.ly = e.clientY;
      this.draw();
    });
    const stop = () => { this.spin.dragging = false; c.style.cursor = 'grab'; };
    c.addEventListener('pointerup', stop);
    c.addEventListener('pointercancel', stop);
  }

  setState(cube) {
    this.cube = cube;
    this.draw();
  }

  setHighlight(stickers) {
    this.highlight = stickers && stickers.length ? new Set(stickers) : null;
    this.draw();
  }

  /** apply moves with a short animation */
  async apply(alg, speed = 170) {
    const moves = alg.trim().split(/\s+/).filter(Boolean);
    for (const m of moves) {
      this.cube.move(m);
      this.draw();
      await new Promise(r => setTimeout(r, speed));
    }
  }

  _projector() {
    const b = basis(VIEWS[this.viewName] || VIEWS.default);
    const cosY = Math.cos(this.spin.yaw), sinY = Math.sin(this.spin.yaw);
    const cosP = Math.cos(this.spin.pitch), sinP = Math.sin(this.spin.pitch);
    const right = [b.right[0] * cosY + b.d[0] * sinY, b.right[1] * cosY + b.d[1] * sinY, b.right[2] * cosY + b.d[2] * sinY];
    const depth = norm([b.d[0] * cosY - b.right[0] * sinY, b.d[1] * cosY - b.right[1] * sinY, b.d[2] * cosY - b.right[2] * sinY]);
    const upBase = norm(cross3(depth, right));
    const up = [upBase[0] * cosP + depth[0] * sinP, upBase[1] * cosP + depth[1] * sinP, upBase[2] * cosP + depth[2] * sinP];
    const dep = norm(cross3(right, up));
    const corners = [];
    for (const x of [-1.5, 1.5]) for (const y of [-1.5, 1.5]) for (const z of [-1.5, 1.5])
      corners.push([x, y, z]);
    const proj = corners.map(p => [dot(p, right), dot(p, up)]);
    const xs = proj.map(p => p[0]), ys = proj.map(p => p[1]);
    const span = Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
    const s = (this.size * 0.88) / span;
    const cx = (Math.max(...xs) + Math.min(...xs)) / 2;
    const cy = (Math.max(...ys) + Math.min(...ys)) / 2;
    return (p) => {
      const x = dot(p, right), y = dot(p, up);
      return [this.size / 2 + (x - cx) * s, this.size / 2 - (y - cy) * s];
    };
  }

  draw() {
    const ctx = this.ctx;
    const S = this.size;
    ctx.clearRect(0, 0, S, S);
    const project = this._projector();
    const b = basis(VIEWS[this.viewName] || VIEWS.default);

    // body silhouette
    const bodyPts = [];
    for (const x of [-1.5, 1.5]) for (const y of [-1.5, 1.5]) for (const z of [-1.5, 1.5])
      bodyPts.push(project([x, y, z]));
    ctx.beginPath();
    hull(bodyPts).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
    ctx.closePath();
    ctx.fillStyle = '#15161b';
    ctx.fill();

    // visible stickers
    const quads = [];
    for (const face of FACES) {
      const n = NORMALS[face];
      if (dot(n, b.d) <= 0.02) continue;          // back-face culling
      const axis = Math.abs(n[0]) ? 0 : Math.abs(n[1]) ? 1 : 2;
      const sign = n[axis];
      const uAxis = axis === 0 ? 1 : axis === 1 ? 0 : 0;
      const vAxis = axis === 0 ? 2 : axis === 1 ? 2 : 1;
      for (const [key, faces] of this.cube.st) {
        if (!faces[face]) continue;
        const pos = key.split(',').map(Number);
        if (Math.abs(pos[axis] - sign) > 0.5) continue;
        const plane = pos[axis] + sign * 0.5;
        const pts = [];
        for (const [su, sv] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
          const p = pos.slice();
          p[axis] = plane;
          p[uAxis] += su * 0.41;
          p[vAxis] += sv * 0.41;
          pts.push(p);
        }
        quads.push([pts, faces[face], face]);
      }
    }
    for (const [pts, colour, face] of quads) {
      const sp = pts.map(project);
      const kept = !this.highlight || this.highlight.has(colour) || this.highlight.has(face);
      const base = kept ? COLORS[colour] : [0.78, 0.78, 0.80];
      const col = shade(base, LIGHT[face]);
      const xs = sp.map(p => p[0]), ys = sp.map(p => p[1]);
      const g = ctx.createLinearGradient(Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys));
      g.addColorStop(0, hex(col.map(q => Math.min(1, q + 0.14))));
      g.addColorStop(1, hex(col.map(q => Math.max(0, q - 0.10))));
      roundPoly(ctx, sp, 3.2);
      ctx.fillStyle = g;
      ctx.fill();
      ctx.strokeStyle = 'rgba(10,10,14,0.55)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }
  }
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
    const l0 = Math.hypot(...v0) || 1, l1 = Math.hypot(...v1) || 1;
    const rr = Math.min(r, l0 / 2.4, l1 / 2.4);
    const a = [p0[0] - (v0[0] / l0) * rr, p0[1] - (v0[1] / l0) * rr];
    const b = [p0[0] + (v1[0] / l1) * rr, p0[1] + (v1[1] / l1) * rr];
    if (i === 0) ctx.moveTo(a[0], a[1]); else ctx.lineTo(a[0], a[1]);
    ctx.quadraticCurveTo(p0[0], p0[1], b[0], b[1]);
  }
  ctx.closePath();
}

if (typeof window !== 'undefined') {
  window.Cube = Cube;
  window.CubeView = CubeView;
  window.CUBE_COLORS = COLORS;
  window.CUBE_FACE_FA = FACE_FA;
  window.CUBE_COLOR_FA = COLOR_FA;
}
