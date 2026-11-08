/* solve.js — build ONE real solve of ONE scrambled cube, stage by stage.

   Why this file exists: the figures used to be independent snapshots, each
   invented backwards from a solved cube. Each one was a legal cube state, but
   they were not a lesson: the state before step 5 had nothing to do with the
   state after step 4, and several steps showed a cube that was already almost
   solved. A learner following the page could not copy anything.

   Here every figure is a stage of the same solve:

     scrambled → daisy → white cross → first-layer corners → middle layer
               → yellow cross → yellow face → yellow corners → solved

   The rules this file enforces (see check()):
     · each stage starts exactly where the previous stage ended;
     · each stage's printed lesson, replayed from its own figure, really does
       produce the next figure;
     · no stage disturbs a piece that an earlier stage finished;
     · a stage that the scramble happened to leave already finished is first
       broken with the same algorithm it teaches, and then solved — so no step
       is ever skipped and no shortcut appears out of luck.

   Camera convention (this file records it, the site applies it):
   the white layer is held UP while it is being built, then the cube is turned
   so the yellow layer faces up for the last layer.

   Run: node tools/cube/solve.js            (verbose)
        node tools/cube/solve.js --json     (machine readable, for the site)
*/
const path = require('path');
const { Cube } = require(path.join(__dirname, '../../web/js/cube-engine.js'));

/* ------------------------------------------------------------------ pieces */
const NORM = { U: [0, 1, 0], D: [0, -1, 0], F: [0, 0, 1], B: [0, 0, -1], R: [1, 0, 0], L: [-1, 0, 0] };
const ALL = ['U', 'D', 'F', 'B', 'R', 'L'];
const SIDES = ['F', 'R', 'B', 'L'];
const OPP = { U: 'D', D: 'U', F: 'B', B: 'F', R: 'L', L: 'R' };

/* centres never move here: every search only uses face turns */
const centre = (c, f) => c.at(NORM[f], f);
const placed = (c, p) => {
  const v = c.st.get(p.join(','));
  return !!v && Object.entries(v).every(([f, col]) => centre(c, f) === col);
};
const facesUp = (c, p) => c.at(p, 'U');
const cnt = (c, list) => list.filter(p => placed(c, p)).length;

const D_EDGES = [[0, -1, 1], [1, -1, 0], [0, -1, -1], [-1, -1, 0]];
const D_CORNERS = [[1, -1, 1], [1, -1, -1], [-1, -1, -1], [-1, -1, 1]];
const MID_EDGES = [[1, 0, 1], [1, 0, -1], [-1, 0, -1], [-1, 0, 1]];
const U_EDGES = [[0, 1, 1], [1, 1, 0], [0, 1, -1], [-1, 1, 0]];
const U_CORNERS = [[1, 1, 1], [1, 1, -1], [-1, 1, -1], [-1, 1, 1]];
const FIRST_TWO = [...D_EDGES, ...D_CORNERS, ...MID_EDGES];

/* which two side faces belong to a slot, and where its U-layer twin sits */
const CORNER_SLOTS = [
  { pos: [1, -1, 1], faces: ['R', 'F'] },
  { pos: [1, -1, -1], faces: ['R', 'B'] },
  { pos: [-1, -1, -1], faces: ['L', 'B'] },
  { pos: [-1, -1, 1], faces: ['L', 'F'] },
];
const EDGE_SLOTS = [
  { pos: [1, 0, 1], faces: ['R', 'F'] },
  { pos: [1, 0, -1], faces: ['R', 'B'] },
  { pos: [-1, 0, -1], faces: ['L', 'B'] },
  { pos: [-1, 0, 1], faces: ['L', 'F'] },
];
const slotAt = (list, pos) => list.find(s => s.pos.join(',') === pos.join(',')) || null;

const STAGE = {
  cross:          { goal: D_EDGES,   keep: [] },
  corners1:       { goal: D_CORNERS, keep: D_EDGES },
  layer2:         { goal: MID_EDGES, keep: [...D_EDGES, ...D_CORNERS] },
  yellowCross:    { goal: U_EDGES,   keep: FIRST_TWO, up: true },
  yellowOrient:   { goal: U_CORNERS, keep: FIRST_TWO, up: true },
  yellowCorners:  { goal: U_CORNERS, keep: FIRST_TWO, up: true },
  yellowEdges:    { goal: U_EDGES,   keep: [...FIRST_TWO, ...U_CORNERS] },
};
const ORDER = ['cross', 'corners1', 'layer2', 'yellowCross', 'yellowOrient', 'yellowCorners', 'yellowEdges'];
/* the camera each stage is filmed from — the site reads this, nothing else */
const VIEW = { cross: 'bottom', corners1: 'bottom', layer2: 'bottom', yellowCross: 'top',
  yellowOrient: 'top', yellowCorners: 'top', yellowEdges: 'top' };

const keeps = (c, stage) => STAGE[stage].keep.every(p => placed(c, p));
const upDone = (c, stage) => STAGE[stage].goal.every(p => facesUp(c, p) === 'U');
/* the last-layer goals are about orientation only: the U colour on the U face */
const done = (c, stage) => {
  switch (stage) {
    case 'cross': return c.isCross();
    case 'corners1': return cnt(c, D_CORNERS) === 4 && keeps(c, stage);
    case 'layer2': return cnt(c, MID_EDGES) === 4 && keeps(c, stage);
    case 'yellowCross': return upDone(c, 'yellowCross') && keeps(c, stage);
    case 'yellowOrient': return upDone(c, 'yellowOrient') && keeps(c, stage);
    case 'yellowCorners': return cnt(c, U_CORNERS) === 4 && keeps(c, stage);
    case 'yellowEdges': return c.solved();
    default: return false;
  }
};

/* ---------------------------------------------------------------- notation */
const invert = (alg) => String(alg).trim().split(/\s+/).filter(Boolean).reverse()
  .map(t => (t.endsWith("'") ? t.slice(0, -1) : t.endsWith('2') ? t : t + "'")).join(' ');
function simplify(alg) {
  const toks = String(alg || '').trim().split(/\s+/).filter(Boolean);
  const out = [];
  const amount = (t) => (t.endsWith("'") ? 3 : t.endsWith('2') ? 2 : 1);
  const fmt = (f, q) => (q % 4 === 1 ? f : q % 4 === 2 ? f + '2' : f + "'");
  for (const t of toks) {
    const face = t[0];
    if (out.length && out[out.length - 1][0] === face) {
      const prev = out.pop();
      const q = (amount(prev) + amount(t)) % 4;
      if (q) out.push(fmt(face, q));
    } else out.push(t);
  }
  return out.join(' ');
}
const applyTo = (cube, alg) => { const c = cube.clone(); if (alg) c.apply(alg); return c; };
const ALIGN = ['', 'U', 'U2', "U'"];

/* Displaying a figure from "the other side" is a whole-cube turn. A turn applied
   to the cube and to all the moves keeps everything true:
       x2 · (A B C)  =  (x2 A x2) (x2 B x2) (x2 C x2) · x2
   so the same lesson can be filmed with the white layer up (while the first
   layer is being built) and with it down later, without telling a different
   story. FACE_MAP is what x2 does to face names. */
/* the mapping itself is measured, not remembered: turning the cube and every
   move the same way is a conjugation, so each move becomes exactly one move */
function measureFlip() {
  const toks = [];
  for (const f of ['U', 'D', 'F', 'B', 'R', 'L', 'M', 'E', 'S']) for (const m of ['', '2', "'"]) toks.push(f + m);
  const singles = toks.map(t => { const c = new Cube(); c.apply(t); return [t, c.key()]; });
  const map = {};
  for (const t of toks) {
    const c = new Cube(); c.apply('x2'); c.apply(t); c.apply('x2');
    const k = c.key();
    map[t] = (singles.find(([, kk]) => kk === k) || [t])[0];
  }
  return map;
}
const FLIP = measureFlip();
const flipAlg = (alg) => String(alg || '').trim().split(/\s+/).filter(Boolean)
  .map(t => FLIP[t] || t).join(' ');

/* ------------------------------------------------------ one-piece searching */
/** shortest sequence that makes `goal` true. `keep`, when given, is required on
 *  the *final* state only — mid-algorithm the cube is allowed to look messy
 *  (that is what an algorithm is). `everyMove`, when given, must hold after
 *  every single turn; it is used while collecting the daisy, where the whole
 *  point is to never lose an edge that is already up. */
function search(start, { goal, faces = ALL, maxDepth = 6, keep = null, everyMove = null }) {
  const moves = [];
  for (const f of faces) moves.push(f, f + '2', f + "'");
  const accept = (c) => goal(c) && (!keep || keep(c));
  let found = null;
  const path = [];
  const dfs = (c, depth, prev) => {
    if (depth === 0) return false;
    for (const mv of moves) {
      if (prev && mv[0] === prev) continue;
      /* opposite faces commute: only try one of the two orders */
      if (prev && OPP[mv[0]] === prev && ALL.indexOf(mv[0]) < ALL.indexOf(prev)) continue;
      const n = c.clone(); n.move(mv);
      if (everyMove && !everyMove(n)) continue;
      path.push(mv);
      if (accept(n)) { found = path.join(' '); return true; }
      if (dfs(n, depth - 1, mv[0])) return true;
      path.pop();
    }
    return false;
  };
  for (let d = 1; d <= maxDepth && !found; d++) { path.length = 0; dfs(start.clone(), d, null); }
  return found;
}

/** the cubie whose colour set is exactly `colors`, as a position */
function findPiece(cube, colors) {
  const want = colors.slice().sort().join();
  for (const [k, v] of cube.st) {
    const vals = Object.values(v);
    if (vals.length !== colors.length) continue;
    if (vals.slice().sort().join() === want) return k.split(',').map(Number);
  }
  return null;
}

/* --------------------------------------------------------- stage 1: cross */
/** the daisy: four white edges standing up around the yellow centre */
const upWhite = (c, p) => c.at(p, 'U') === 'D';
const daisyCount = (c) => U_EDGES.filter(p => upWhite(c, p)).length;

function buildDaisy(start) {
  let cur = start.clone();
  const steps = [];
  for (let guard = 0; guard < 8 && daisyCount(cur) < 4; guard++) {
    const before = daisyCount(cur);
    const alg = search(cur, {
      goal: (c) => daisyCount(c) > before,
      faces: ALL,
      maxDepth: 6,
      everyMove: (c) => daisyCount(c) >= before,
    });
    if (!alg) return null;
    cur = applyTo(cur, alg);
    steps.push(alg);
  }
  if (daisyCount(cur) !== 4 || cur.at([0, 1, 0], 'U') !== 'U') return null;
  return { cube: cur, lesson: simplify(steps.join(' ')) };
}

/** drop the daisy: line each edge up over its centre, then a half turn */
const U_EDGE_SLOT = { F: [0, 1, 1], R: [1, 1, 0], B: [0, 1, -1], L: [-1, 1, 0] };

function dropDaisy(daisy) {
  let cur = daisy.clone();
  const steps = [];
  for (let guard = 0; guard < 20 && !cur.isCross(); guard++) {
    let did = false;
    for (const f of SIDES) {
      const slot = U_EDGE_SLOT[f];
      if (cur.at(slot, 'U') === 'D' && cur.at(slot, f) === centre(cur, f)) {
        cur = applyTo(cur, f + '2');
        steps.push(f + '2');
        did = true;
        break;
      }
    }
    if (did) continue;
    cur = applyTo(cur, 'U');
    steps.push('U');
  }
  if (!cur.isCross()) return null;
  return { cube: cur, lesson: simplify(steps.join(' ')) };
}

/* --------------------------------------------- stage 2/3: corners and edges */
/* Only the instruments the page teaches are used in these two stages: lift a
   piece out with a three-move trigger, line it up with U, drop it back in. That
   keeps every printed lesson a sequence a learner can copy instead of an
   optimal-but-unreadable computer solution. */
const cornerTriggers = (faces) => {
  const out = [];
  for (const a of faces) {
    out.push(`${a} U ${a}'`, `${a} U2 ${a}'`, `${a} U' ${a}'`,
      `${a}' U' ${a}`, `${a}' U ${a}`, `${a}' U2 ${a}`);
  }
  out.push(`${faces[0]} U ${faces[0]}' U'`, `${faces[0]} U' ${faces[0]}' U`);
  return out;
};

/** find the shortest {alignment + trigger} (or two of them) that reaches `goal`
 *  while keeping every finished piece finished */
function triggerStep(cur, triggers, goal, keep, maxDepth = 2) {
  const aligns = ALIGN;
  const cands = [];
  for (const u of aligns) for (const t of triggers) cands.push((u ? u + ' ' : '') + t);
  if (maxDepth >= 1) {
    for (const c of cands) {
      const n = applyTo(cur, c);
      if (keep(n) && goal(n)) return c;
    }
  }
  if (maxDepth >= 2) {
    for (const c of cands) {
      const n = applyTo(cur, c);
      if (!keep(n)) continue;
      for (const d of cands) {
        const m = applyTo(n, d);
        if (keep(m) && goal(m)) return c + ' ' + d;
      }
    }
  }
  return null;
}

function placeSlot(start, { colors, slot, slots, stage }) {
  let cur = start.clone();
  const steps = [];
  const already = slots.filter(o => o.pos.join() !== slot.pos.join() && placed(start, o.pos)).map(o => o.pos);
  const keep = (c) => keeps(c, stage) && already.every(p => placed(c, p));
  for (let guard = 0; guard < 6; guard++) {
    if (placed(cur, slot.pos)) return { cube: cur, lessons: steps };
    const pos = findPiece(cur, colors);
    if (!pos) return null;
    const holder = slotAt(slots, pos) || slot;
    const triggers = [...new Set([...cornerTriggers(slot.faces), ...cornerTriggers(holder.faces)])];
    const goal = pos[1] === 1 ? (c) => placed(c, slot.pos) : (c) => findPiece(c, colors)[1] === 1;
    const alg = triggerStep(cur, triggers, goal, keep, 2);
    if (!alg) return null;
    cur = applyTo(cur, alg);
    steps.push(alg);
  }
  return placed(cur, slot.pos) ? { cube: cur, lessons: steps } : null;
}

/* ----------------------------------- stage 3, the way the page teaches it */
/* one "insert" takes an edge that is standing in the U layer and drops it into
   the slot in front of you. Both hands are the same algorithm mirrored:
       right hand:  U R U' R' U' F' U F
       left  hand:  U' L' U L U F U' F'
   Written with the slot's own two faces, because the solver turns the cube. */
/* which of the slot's two faces is A and which is B: the algorithm's first face
   is the one that comes *next* going round the cube (F → R → B → L → F). For the
   front-right slot that is R, for the left-front slot it is F. Swap them and the
   algorithm shoves the edge into the neighbouring slot instead. */
const SIDE_ORDER = ['F', 'R', 'B', 'L'];
const handOrder = ([f1, f2]) => {
  const i1 = SIDE_ORDER.indexOf(f1), i2 = SIDE_ORDER.indexOf(f2);
  return (i1 + 1) % 4 === i2 ? [f2, f1] : [f1, f2];
};
const insertAlgs = ([f1, f2]) => {
  const [A, B] = handOrder([f1, f2]);
  return [
    `U ${A} U' ${A}' U' ${B}' U ${B}`,
    `U' ${B}' U ${B} U ${A} U' ${A}'`,
  ];
};
/* every taught form of the algorithm, once per U alignment */
const withAUF = (algs) => [].concat(algs).flatMap(alg => ALIGN.map(u => (u ? u + ' ' : '') + alg));

function placeMiddleEdge(start, { colors, slot, stage }) {
  let cur = start.clone();
  const steps = [];
  const keep = (c) => keeps(c, stage);
  for (let guard = 0; guard < 6; guard++) {
    if (placed(cur, slot.pos)) return { cube: cur, lessons: steps };
    const pos = findPiece(cur, colors);
    if (!pos) return null;
    const inU = pos[1] === 1;
    /* the slot the edge is sitting in decides which hand pops it out */
    const holder = inU ? slot : (slotAt(EDGE_SLOTS, pos) || slot);
    const cands = withAUF(insertAlgs(holder.faces));
    let moved = null;
    for (const alg of cands) {
      const c = applyTo(cur, alg);
      if (!keep(c)) continue;
      if (inU && placed(c, slot.pos)) { moved = { alg, cube: c }; break; }
      if (!inU && findPiece(c, colors)[1] === 1) { moved = { alg, cube: c }; break; }
    }
    if (!moved) {
      /* the edge is in the U layer but upside down, or the alignment is odd:
         use the generic search before giving up */
      const goal = inU ? (c) => placed(c, slot.pos) : (c) => findPiece(c, colors)[1] === 1;
      const alg = search(cur, { goal, faces: ['U', ...holder.faces, ...slot.faces], maxDepth: 7, keep });
      if (!alg) return null;
      moved = { alg, cube: applyTo(cur, alg) };
    }
    cur = moved.cube;
    steps.push(moved.alg);
  }
  return placed(cur, slot.pos) ? { cube: cur, lessons: steps } : null;
}

/* ------------------------------------------------- stage 4-7: last layer */
/* the algorithms the page teaches, and only those */
const LESSONS = {
  yellowCross: ["F R U R' U' F'"],
  yellowOrient: ["R U R' U R U2 R'", "R U2 R' U' R U' R'"],
  yellowCorners: ["R U' L' U R' U' L", "U R U' L' U R' U' L",
    "R' F R' B2 R F' R' B2 R2", "R2 B2 R F R' B2 R F' R"],
  yellowEdges: ["M2 U M U2 M' U M2", "M2 U' M U2 M' U' M2", "R U' R U R U R U' R' U' R2"],
};

/** every way of spending one lesson: an alignment, then the algorithm */
function lessonSteps(stage) {
  const out = [];
  for (const alg of LESSONS[stage]) for (const auf of ALIGN) out.push((auf ? auf + ' ' : '') + alg);
  return out;
}

/** breadth-first over lessons: the shortest chain of taught algorithms that
 *  finishes the stage. Depth 3 is enough for every last-layer case. */
function lessonSolve(start, stage, maxSteps = 3) {
  const steps = lessonSteps(stage);
  const goal = (c) => done(c, stage) && keeps(c, stage);
  if (goal(start)) return { cube: start.clone(), lesson: '' };
  const seen = new Set([start.key()]);
  let frontier = [{ cube: start.clone(), lesson: '' }];
  for (let d = 0; d < maxSteps; d++) {
    const next = [];
    for (const node of frontier) {
      for (const s of steps) {
        const c = applyTo(node.cube, s);
        if (!keeps(c, stage)) continue;
        const lesson = node.lesson ? node.lesson + ' ' + s : s;
        if (goal(c)) return { cube: c, lesson };
        const k = c.key();
        if (seen.has(k)) continue;
        seen.add(k);
        next.push({ cube: c, lesson });
      }
    }
    frontier = next;
    if (!frontier.length) break;
  }
  return null;
}

/** one last-layer stage, done only with the algorithms the page teaches.
 *  Returned with the shortest lesson that actually shows something: a break
 *  whose repair is its exact inverse would cancel out and show the reader
 *  nothing, so those candidates are thrown away. */
function runLessonStage(start, stage, allowBreak = false) {
  const own = LESSONS[stage];
  const picks = [];

  /* the common case: the stage is there to be done, use the short chain */
  if (!done(start, stage)) {
    const plain = lessonSolve(start, stage);
    if (plain) return plain;
  }
  if (!allowBreak) return null;

  /* the stage arrived finished: perform one of its own algorithms first, then
     undo the mess with the stage's algorithms. A single break is often repaired
     by its own inverse — a lesson of two cancelling algorithms shows nothing —
     so two-algorithm breaks are tried as well. */
  const firsts = own.flatMap(a => ALIGN.map(u => (u ? u + ' ' : '') + a));
  const prefixes = [...firsts];
  for (const f of firsts) for (const a of own) for (const u of ALIGN) prefixes.push(f + ' ' + (u ? u + ' ' : '') + a);
  for (const prefix of prefixes) {
    const broken = applyTo(start, prefix);
    if (!keeps(broken, stage)) continue;
    const rest = lessonSolve(broken, stage, 4);
    if (!rest || !rest.lesson) continue;
    const lesson = simplify(prefix + ' ' + rest.lesson);
    /* the reader must actually see the taught algorithm, not a couple of U turns */
    if (!own.some(a => lesson.includes(a))) continue;
    if (lesson.split(/\s+/).length < 2) continue;
    picks.push({ cube: rest.cube, lesson });
  }

  if (!picks.length) return null;
  picks.sort((a, b) => a.lesson.split(' ').length - b.lesson.split(' ').length);
  return picks[0];
}

/** The rule the site taught us: a step is never skipped. If the cube happens to
 *  arrive with a stage already finished, the solver first breaks that stage with
 *  one of the algorithms the same stage teaches — and then does the stage for
 *  real. The reader sees the step performed; nothing is quietly skipped. */
function ensureWork(cur, stage, repertoire) {
  if (!done(cur, stage)) return { cube: cur, prefix: '' };
  for (const alg of repertoire) for (const u of ALIGN) {
    const prefix = (u ? u + ' ' : '') + alg;
    const c = applyTo(cur, prefix);
    if (keeps(c, stage) && !done(c, stage)) return { cube: c, prefix };
  }
  return null;
}

/* ---------------------------------------------------------------- the solve *//* ---------------------------------------------------------------- the solve */
function attempt(scramble, allowBreak) {
  const figs = {};
  /* a scramble that already happens to contain a white cross would turn the
     first lesson into a no-op, so the scramble is extended a few turns until it
     does not — the reader still starts from a genuinely scrambled cube */
  let effective = String(scramble || '').trim();
  const extra = ['R', "U", "F'", 'L2', "B", "D'"];
  for (let i = 0; i < extra.length && new Cube().apply(effective).isCross(); i++) {
    effective = (effective + ' ' + extra[i]).trim();
  }
  let start = new Cube().apply(effective);
  const preBreak = '';
  /* every stage's start state, described as the moves from the scramble */
  const stageStarts = { yellowCross: '', yellowOrient: '', yellowCorners: '', yellowEdges: '' };
  const soFar = [];

  /* --- stage 1: daisy, then the white cross --- */
  let cur = start.clone();
  let daisy = buildDaisy(cur);
  if (!daisy) return { ok: false, at: 'daisy' };
  const drop = dropDaisy(daisy.cube);
  if (!drop) return { ok: false, at: 'cross' };
  figs.cross = {
    before: start,
    daisy: daisy.cube,
    after: drop.cube,
    daisyLesson: simplify(preBreak + ' ' + daisy.lesson),
    dropLesson: drop.lesson,
    lesson: simplify(preBreak + ' ' + daisy.lesson + ' ' + drop.lesson),
  };
  cur = drop.cube;
  soFar.push(figs.cross.lesson);

  /* --- stage 2: first-layer corners --- */
  const cornerSteps = [];
  if (done(cur, 'corners1') && !allowBreak) return { skipped: 'corners1' };
  const c1work = ensureWork(cur, 'corners1', ["R U R'", "R U' R'", "F' U' F"]);
  if (!c1work) return { ok: false, at: 'corners1' };
  const c1break = c1work.prefix;
  if (c1break) cur = c1work.cube;
  for (const slot of CORNER_SLOTS) {
    const colors = ['D', centre(start, slot.faces[0]), centre(start, slot.faces[1])];
    const r = placeSlot(cur, { colors, slot, slots: CORNER_SLOTS, stage: 'corners1' });
    if (!r) return { ok: false, at: 'corners1' };
    cur = r.cube;
    cornerSteps.push(...r.lessons);
  }
  if (cnt(cur, D_CORNERS) !== 4 || !keeps(cur, 'corners1')) return { ok: false, at: 'corners1' };
  soFar.push(simplify([c1break, ...cornerSteps].join(' ')));
  figs.corners1 = { before: figs.cross.after, after: cur,
    lessons: [...(c1break ? [c1break] : []), ...cornerSteps],
    lesson: simplify([c1break, ...cornerSteps].join(' ')) };

  /* --- stage 3: middle layer --- */
  const midSteps = [];
  if (done(cur, 'layer2') && !allowBreak) return { skipped: 'layer2' };
  const l2work = ensureWork(cur, 'layer2', ["R U R' U'", "R U' R'", "F' U' F"]);
  if (!l2work) return { ok: false, at: 'layer2' };
  const l2break = l2work.prefix;
  if (l2break) cur = l2work.cube;
  for (const slot of EDGE_SLOTS) {
    const colors = [centre(start, slot.faces[0]), centre(start, slot.faces[1])];
    const r = placeMiddleEdge(cur, { colors, slot, stage: 'layer2' });
    if (!r) return { ok: false, at: 'layer2' };
    cur = r.cube;
    midSteps.push(...r.lessons);
  }
  if (cnt(cur, MID_EDGES) !== 4 || !keeps(cur, 'layer2')) return { ok: false, at: 'layer2' };
  soFar.push(simplify([l2break, ...midSteps].join(' ')));
  stageStarts.yellowCross = simplify(effective + ' ' + soFar.join(' '));
  figs.layer2 = { before: figs.corners1.after, after: cur,
    lessons: [...(l2break ? [l2break] : []), ...midSteps],
    lesson: simplify([l2break, ...midSteps].join(' ')) };

  /* --- stage 4: yellow cross --- */
  if (done(cur, 'yellowCross') && !allowBreak) return { skipped: 'yellowCross' };
  let r = runLessonStage(cur, 'yellowCross', allowBreak);
  if (!r) return { ok: false, at: 'yellowCross' };
  figs.yellowCross = { before: figs.layer2.after, after: r.cube, lesson: simplify(r.lesson) };
  cur = r.cube;
  soFar.push(simplify(r.lesson));
  stageStarts.yellowOrient = simplify(effective + ' ' + soFar.join(' '));

  /* --- stage 5: whole yellow face --- */
  if (done(cur, 'yellowOrient') && !allowBreak) return { skipped: 'yellowOrient' };
  r = runLessonStage(cur, 'yellowOrient', allowBreak);
  if (!r) return { ok: false, at: 'yellowOrient' };
  figs.yellowOrient = { before: figs.yellowCross.after, after: r.cube, lesson: simplify(r.lesson) };
  cur = r.cube;
  soFar.push(simplify(r.lesson));
  stageStarts.yellowCorners = simplify(effective + ' ' + soFar.join(' '));

  /* --- stage 6: yellow corners in place --- */
  if (done(cur, 'yellowCorners') && !allowBreak) return { skipped: 'yellowCorners' };
  r = runLessonStage(cur, 'yellowCorners', allowBreak);
  if (!r) return { ok: false, at: 'yellowCorners' };
  figs.yellowCorners = { before: figs.yellowOrient.after, after: r.cube, lesson: simplify(r.lesson) };
  cur = r.cube;
  soFar.push(simplify(r.lesson));
  stageStarts.yellowEdges = simplify(effective + ' ' + soFar.join(' '));

  /* --- stage 7: yellow edges in place --- */
  if (done(cur, 'yellowEdges') && !allowBreak) return { skipped: 'yellowEdges' };
  r = runLessonStage(cur, 'yellowEdges', allowBreak);
  if (!r) return { ok: false, at: 'yellowEdges' };
  figs.yellowEdges = { before: figs.yellowCorners.after, after: r.cube, lesson: simplify(r.lesson) };
  if (!r.cube.solved()) return { ok: false, at: 'yellowEdges' };

  for (const stage of ORDER) figs[stage].view = VIEW[stage];
  return { ok: true, scramble: effective, figs, stageStarts, solved: r.cube };
}

/* ---------------------------------------------------------------- the entry */
/* A scramble is picked, not invented after the fact: if a stage happens to be
   finished already (the luckiest 1-in-200 case), the scramble is extended by a
   few more turns of the same cube and tried again. That keeps every lesson as
   short and as natural as what a real scramble produces. */
const TAILS = [
  '', " R U' F2", " F' L D2", " U2 B R'", " L2 F U", " B2 R2 D", " U R2 B'",
  " D' L2 F", " R' B2 U", " F2 U' R", " L U2 B", " B' D2 L",
];
function solveFrom(scramble) {
  const base = String(scramble || '').trim();
  let last = null;
  for (const tail of TAILS) {
    const r = attempt((base + tail).trim(), false);
    if (r.ok) return r;
    last = r;
  }
  /* extremely unlikely: accept a solve that has to break a lucky stage first */
  for (const tail of TAILS.slice(0, 4)) {
    const r = attempt((base + tail).trim(), true);
    if (r.ok) return r;
  }
  return { ok: false, at: (last && (last.skipped || last.at)) || 'unknown' };
}

/* --------------------------------------------------------------- validation */
function check(result) {
  const problems = [];
  if (!result.ok) return [`solve stopped at ${result.at}`];
  const f = result.figs;
  const say = (label, ok) => { if (!ok) problems.push(label); };

  const stageCheck = (name, lesson) => {
    const { before, after } = f[name];
    say(`${name}: the printed lesson does not reach the next figure`,
      applyTo(before, lesson).key() === after.key());
    say(`${name}: finished pieces from earlier stages were disturbed`, keeps(after, name));
    say(`${name}: the goal of the stage is not reached`, done(after, name));
    say(`${name}: the figure does not start where the previous one ended`, !!before);
  };

  say('cross: the daisy figure is not a daisy',
    daisyCount(f.cross.daisy) === 4 && f.cross.daisy.at([0, 1, 0], 'U') === 'U');
  say('cross: the daisy does not come out of the scrambled cube',
    applyTo(f.cross.before, f.cross.daisyLesson).key() === f.cross.daisy.key());
  say('cross: dropping the daisy does not give a white cross',
    applyTo(f.cross.daisy, f.cross.dropLesson).key() === f.cross.after.key() && f.cross.after.isCross());

  stageCheck('corners1', f.corners1.lesson);
  stageCheck('layer2', f.layer2.lesson);
  stageCheck('yellowCross', f.yellowCross.lesson);
  stageCheck('yellowOrient', f.yellowOrient.lesson);
  stageCheck('yellowCorners', f.yellowCorners.lesson);
  stageCheck('yellowEdges', f.yellowEdges.lesson);

  /* one continuous solve: no gap anywhere */
  const chain = [
    ['corners1', 'cross'], ['layer2', 'corners1'], ['yellowCross', 'layer2'],
    ['yellowOrient', 'yellowCross'], ['yellowCorners', 'yellowOrient'],
    ['yellowEdges', 'yellowCorners'],
  ];
  for (const [next, prev] of chain) {
    say(`chain broken between ${prev} and ${next}`,
      f[next].before.key() === f[prev].after.key());
  }
  say('the scrambled figure is not the scramble', f.cross.before.key() === new Cube().apply(result.scramble).key());
  say('the last figure is not a solved cube', f.yellowEdges.after.solved());

  /* nothing is skipped: every stage performs at least one of its algorithms,
     even in the lucky case where the cube arrives with that stage finished */
  const lessons = {
    cross: [f.cross.daisyLesson, f.cross.dropLesson],
    corners1: [f.corners1.lesson],
    layer2: [f.layer2.lesson],
    yellowCross: [f.yellowCross.lesson],
    yellowOrient: [f.yellowOrient.lesson],
    yellowCorners: [f.yellowCorners.lesson],
    yellowEdges: [f.yellowEdges.lesson],
  };
  for (const stage of ORDER) {
    const own = lessons[stage].join(' ').trim();
    say(`${stage}: the step is empty — nothing is shown`, own.split(/\s+/).filter(Boolean).length > 0);
  }
  /* a one-turn alignment is legitimate for a case the scramble solved by luck,
     but it must not be the whole of two last-layer stages in the same solve */
  const oneMove = ['yellowCross', 'yellowOrient', 'yellowCorners', 'yellowEdges']
    .filter(stage => f[stage].lesson.trim().split(/\s+/).length <= 1);
  say('the whole last layer is skipped with alignments', oneMove.length <= 1);
  return problems;
}

/** the whole solve in the shape the site stores: eight figures, each one a
 *  window on the same cube, each with the moves that take it to the next one */
const STAGE_FA = {
  cross: 'صلیب سفید',
  corners1: 'گوشه‌های لایه اول',
  layer2: 'لبه‌های لایه دوم',
  yellowCross: 'صلیب زرد',
  yellowOrient: 'وجه زرد کامل',
  yellowCorners: 'جای گوشه‌های زرد',
  yellowEdges: 'جای لبه‌های زرد',
};

function toData(result) {
  const f = result.figs;
  const S = result.stageStarts;
  const SCR = result.scramble;
  /* Every `alg` below is the whole story from the scrambled cube: the site makes
     a figure with `new Cube().apply(alg)`. A lesson that forgot the scramble
     would paint a different cube — the exact bug this file exists to prevent —
     so the moves are composed here, once, in one place. */
  const all = (...algs) => [SCR, ...algs.filter(Boolean)].join(' ').trim();

  /* The white layer is the working layer while it is built, so those figures
     look at the white face (camera "bottom" in model space, where white is D).
     The last layer is then the yellow one, and those figures look from the top
     with the finished white side down and out of sight. */
  /* White up: the first three stages are shown on a cube that has been turned
     over, so the white face really is at the top of the picture the way the
     reader holds it. Turning the whole cube over first means every following
     move still means what the page says — the moves do not change, only the
     side of the cube we are looking at. */
  const TURN = '';
  /* nothing is turned over any more: each figure is the real state of the solve,
     and the camera is picked per figure — see VIEW_BY_STATE below */
  const up = (alg) => alg;
  /* The white layer is the one being worked on, so the camera always looks at
     the white face: from above while the daisy is being made (its petals point
     up), from below once the cross is down. The last layer is looked at from
     above, with the finished white side facing away from the reader. */
  const viewWhite = 'bottom';
  const viewYellow = 'top';

  const crossDone = all(f.cross.lesson);
  const c1Done = all(f.cross.lesson, f.corners1.lesson);
  const l2Done = all(f.cross.lesson, f.corners1.lesson, f.layer2.lesson);

  const states = {
    cross: [
      { label: 'شروع: مکعب به‌هم‌ریخته', alg: up(all()), next: f.cross.daisyLesson, view: 'default' },
      { label: 'دیزی: چهار سفید دور مرکز زرد', alg: up(all(f.cross.daisyLesson)), next: f.cross.dropLesson, view: 'top' },
      { label: 'صلیب سفید: هر لبه بالای مرکز هم‌رنگش', alg: up(crossDone), next: null, view: viewWhite },
    ],
    corners1: [
      { label: 'قبل از این گام: صلیب آماده است', alg: up(crossDone), next: TURN + ' ' + f.corners1.lesson, view: viewWhite },
      { label: 'بعد از این گام: لایه اول کامل', alg: up(c1Done), next: null, view: viewWhite },
    ],
    layer2: [
      { label: 'قبل از این گام: لایه اول کامل است', alg: up(c1Done), next: f.layer2.lesson, view: viewWhite },
      { label: 'بعد از این گام: دو لایه پایین کامل', alg: up(l2Done), next: null, view: viewWhite },
    ],
    yellowCross: [
      { label: 'قبل از این گام: روی زرد بی‌شکل', alg: S.yellowCross, next: f.yellowCross.lesson, view: viewYellow },
      { label: 'بعد از این گام: صلیب زرد', alg: S.yellowOrient, next: null, view: viewYellow },
    ],
    yellowOrient: [
      { label: 'قبل از این گام: صلیب زرد، گوشه‌ها برگشته', alg: S.yellowOrient, next: f.yellowOrient.lesson, view: viewYellow },
      { label: 'بعد از این گام: تمام وجه زرد یک‌رنگ', alg: S.yellowCorners, next: null, view: viewYellow },
    ],
    yellowCorners: [
      { label: 'قبل از این گام: وجه زرد کامل، گوشه‌ها جابه‌جا', alg: S.yellowCorners, next: f.yellowCorners.lesson, view: viewYellow },
      { label: 'بعد از این گام: گوشه‌ها سر جای خودشان', alg: S.yellowEdges, next: null, view: viewYellow },
    ],
    yellowEdges: [
      { label: 'قبل از این گام: فقط جای سه لبه مانده', alg: S.yellowEdges, next: f.yellowEdges.lesson, view: viewYellow },
      { label: 'بعد از این گام: مکعب حل شد', alg: all(f.cross.lesson, f.corners1.lesson, f.layer2.lesson,
        f.yellowCross.lesson, f.yellowOrient.lesson, f.yellowCorners.lesson, f.yellowEdges.lesson),
        next: null, view: viewYellow, solved: true },
    ],
  };
  /* the stages filmed white-up are the same solve seen from the other side */
  const turned = ['cross', 'corners1', 'layer2'];
  return { scramble: SCR, states, order: ORDER, labels: STAGE_FA, turned, turn: TURN };
}

/** the figure data must agree with the solve it came from — checked here so a
 *  wrong prefix can never reach the page */
function checkData(data, result) {
  const problems = [];
  const say = (label, ok) => { if (!ok) problems.push('data: ' + label); };
  const cube = (alg) => new Cube().apply(alg || '');
  const f = result.figs;
  /* the figures before the flip must be the states of the solve, seen flipped */
  const TURN = data.turn || '';
  /* the white-layer figures are the same states, seen after a whole-cube turn */
  const same = (alg, ref) => cube(alg).key() === cube(ref.key ? ref.key() : ref).key()
    || cube(alg).key() === cube((result.scramble + ' ' + '') + '').key() && false;
  const seenAs = (alg, refCube) => {
    const a = cube(alg);
    const b = refCube.clone(); if (TURN) b.apply(TURN);
    return a.key() === b.key();
  };
  say('cross: the first figure is not the scramble', seenAs(data.states.cross[0].alg, new Cube().apply(result.scramble)));
  /* the daisy figure is shown turned over, so its white petals face D in model
     space: turn it back before asking whether it is a daisy */
  const daisyFig = cube(data.states.cross[1].alg);
  const daisyBack = daisyFig.clone(); if (TURN) daisyBack.apply(TURN);
  say('cross: the daisy figure is not a daisy', daisyBack.isDaisy());
  say('cross: the third figure is not a white cross', seenAs(data.states.cross[2].alg, f.cross.after));
  say('corners1: the figure is not the state after the corners', seenAs(data.states.corners1[1].alg, f.corners1.after));
  say('layer2: the figure is not the state after the middle layer', seenAs(data.states.layer2[1].alg, f.layer2.after));
  void same;
  say('yellowCross: the figure is not the state before the yellow cross', cube(data.states.yellowCross[0].alg).key() === f.yellowCross.before.key());
  say('yellowCross: the figure is not the yellow cross', cube(data.states.yellowCross[1].alg).key() === f.yellowCross.after.key());
  say('yellowOrient: wrong figure', cube(data.states.yellowOrient[0].alg).key() === f.yellowOrient.before.key());
  say('yellowCorners: wrong figure', cube(data.states.yellowCorners[0].alg).key() === f.yellowCorners.before.key());
  say('yellowEdges: wrong figure', cube(data.states.yellowEdges[0].alg).key() === f.yellowEdges.before.key());
  say('yellowEdges: the last figure is not a solved cube', cube(data.states.yellowEdges[1].alg).solved());
  /* the moves of each figure must really lead to the next figure */
  const leads = (st, next) => cube(st.alg).apply(st.next).key() === cube(next.alg).key();
  for (const list of Object.values(data.states)) {
    for (let i = 0; i + 1 < list.length; i++) {
      if (!list[i].next || !list[i + 1].alg) continue;
      say(`a lesson does not lead to the next figure: ${list[i].label}`, leads(list[i], list[i + 1]));
    }
  }
  /* and each stage must start where the previous one ended */
  say('corners1 does not start where cross ended', cube(data.states.corners1[0].alg).key() === cube(data.states.cross[2].alg).key());
  say('layer2 does not start where corners1 ended', cube(data.states.layer2[0].alg).key() === cube(data.states.corners1[1].alg).key());
  say('yellowCross does not start where layer2 ended', cube(data.states.yellowCross[0].alg).key() === cube(data.states.layer2[1].alg).key());
  say('yellowOrient does not start where yellowCross ended', cube(data.states.yellowOrient[0].alg).key() === cube(data.states.yellowCross[1].alg).key());
  say('yellowCorners does not start where yellowOrient ended', cube(data.states.yellowCorners[0].alg).key() === cube(data.states.yellowOrient[1].alg).key());
  say('yellowEdges does not start where yellowCorners ended', cube(data.states.yellowEdges[0].alg).key() === cube(data.states.yellowCorners[1].alg).key());
  return problems;
}

/** the step ids of the LBL method, in the order of the solve */
const STEP_IDS = {
  cross: 'cross',
  corners1: 'corners1',
  layer2: 'layer2',
  yellowCross: 'yellow-cross',
  yellowOrient: 'yellow-corners-orient',
  yellowCorners: 'yellow-corners-permute',
  yellowEdges: 'yellow-edges-permute',
};

/** rewrite the `states: [...]` array of one step in methods.js, leaving every
 *  other character of the file alone (it is hand-written content, not a data
 *  dump, so a full re-emit would destroy the prose) */
function patchStates(src, stepId, states) {
  const at = src.indexOf(`id: '${stepId}',`);
  if (at < 0) throw new Error(`step ${stepId} not found`);
  const open = src.indexOf('states: [', at);
  if (open < 0) throw new Error(`step ${stepId} has no states`);
  /* walk the brackets to find the end of the array */
  let i = src.indexOf('[', open), depth = 0;
  for (; i < src.length; i++) {
    if (src[i] === '[') depth++;
    else if (src[i] === ']') { depth--; if (!depth) break; }
  }
  const q = (v) => (v === null || v === undefined ? 'null' : "'" + String(v).replace(/\\/g, '\\\\').replace(/'/g, "\\'") + "'");
  const rows = states.map(st => '                { label: ' + q(st.label) +
    ', alg: ' + q(st.alg) + ', next: ' + q(st.next) + ', view: ' + q(st.view) + ' },');
  const literal = 'states: [\n' + rows.join('\n') + '\n              ]';
  return src.slice(0, open) + literal + src.slice(i + 1);
}

/** plug the generated figures into the hand-written step pages */
function patchMethods(result, file) {
  const data = toData(result);
  let src = require('fs').readFileSync(file, 'utf8');
  for (const stage of ORDER) {
    src = patchStates(src, STEP_IDS[stage], data.states[stage]);
  }
  require('fs').writeFileSync(file, src);
  return file;
}

/** write the data file the site loads (web/data/solve-lbl.js) */
const DATA_HEADER = `/* solve-lbl.js — GENERATED, do not edit by hand.
   Produced by: node tools/cube/solve.js --write
   One continuous solve of one scrambled cube: every figure below is a stage of
   the same solve, and the moves of a stage take its figure to the next one.
   The camera of each figure looks at the face the step is about. */
`;
function writeData(result, file) {
  const data = toData(result);
  const body = `const SOLVE_LBL = ${JSON.stringify(data, null, 2)};\n`;
  require('fs').writeFileSync(file, DATA_HEADER + body);
  return file;
}

module.exports = {
  solveFrom, check, toData, checkData, writeData, patchMethods, STAGE, ORDER, VIEW, LESSONS, invert, simplify, applyTo, placed, cnt, done, keeps,
  D_EDGES, D_CORNERS, MID_EDGES, U_EDGES, U_CORNERS,
};

if (require.main === module) {
  if (process.argv.includes('--write')) {
    const out = path.join(__dirname, '../../web/data/solve-lbl.js');
    const scramble = "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2";
    const r = solveFrom(scramble);
    const problems = check(r);
    if (problems.length) { for (const p of problems) console.log('! ' + p); process.exit(1); }
    writeData(r, out);
    console.log('wrote ' + path.relative(process.cwd(), out));
    const methods = path.join(__dirname, '../../web/data/methods.js');
    patchMethods(r, methods);
    console.log('patched ' + path.relative(process.cwd(), methods));
    console.log('scramble:', r.scramble);
    process.exit(0);
  }
  const scrambles = [
    "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2",
    "L2 F' U2 R B2 D' F2 L' U' R2 B D2 F U' L U2 B' R'",
    "D2 L2 B R' U F2 D' B2 R2 U' L F' D2 B U2 R' F2 L'",
    "F R U' R' U' R U R' F' R U R' U' R' F R F'",
  ];
  let bad = 0;
  for (const s of scrambles) {
    const t = Date.now();
    const r = solveFrom(s);
    const problems = check(r);
    if (problems.length) bad++;
    console.log(`${problems.length ? 'FAIL' : 'OK  '}  ${s}  (${Date.now() - t}ms)`);
    for (const p of problems) console.log('      ! ' + p);
    if (!problems.length) {
      console.log('      daisy   :', r.figs.cross.daisyLesson);
      console.log('      drop    :', r.figs.cross.dropLesson);
      console.log('      corners1:', r.figs.corners1.lesson);
      console.log('      layer2  :', r.figs.layer2.lesson);
      console.log('      y-cross :', r.figs.yellowCross.lesson);
      console.log('      y-face  :', r.figs.yellowOrient.lesson);
      console.log('      y-corner:', r.figs.yellowCorners.lesson);
      console.log('      y-edge  :', r.figs.yellowEdges.lesson);
    }
  }
  process.exitCode = bad ? 1 : 0;
}
