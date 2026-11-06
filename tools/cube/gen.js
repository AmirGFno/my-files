/* gen.js — emit the 7 verified scenes of the beginner method for the site.

   Each scene is "the picture where this lesson applies": every earlier step is
   already finished, this step's pieces are not. The next scene is produced by
   actually applying the lesson, so the page can animate figure → next and the
   claim is checkable, not decorative.

   Build order is backwards from the solved cube with backtracking, because a
   lesson for the last layer must not disturb the first two layers.

   Run: node gen.js > scenes.txt   (also writes scenes.json)
*/
const fs = require('fs');
const { Cube } = require(require('path').join(__dirname, '../../web/js/cube-engine.js'));

const NORM = { U: [0, 1, 0], D: [0, -1, 0], F: [0, 0, 1], B: [0, 0, -1], R: [1, 0, 0], L: [-1, 0, 0] };
const centre = (c, f) => c.at(NORM[f], f);
const placed = (c, p) => {
  const v = c.st.get(p.join(','));
  if (!v) return false;
  return Object.entries(v).every(([f, col]) => centre(c, f) === col);
};
const upFacing = (c, p) => c.at(p, 'U') === 'U';
const cnt = (c, list, fn = placed) => list.filter(p => fn(c, p)).length;

const D_EDGES = [[0, -1, 1], [1, -1, 0], [0, -1, -1], [-1, -1, 0]];
const D_CORNERS = [[1, -1, 1], [1, -1, -1], [-1, -1, -1], [-1, -1, 1]];
const MID_EDGES = [[1, 0, 1], [1, 0, -1], [-1, 0, -1], [-1, 0, 1]];
const U_EDGES = [[0, 1, 1], [1, 1, 0], [0, 1, -1], [-1, 1, 0]];
const U_CORNERS = [[1, 1, 1], [1, 1, -1], [-1, 1, -1], [-1, 1, 1]];
const FIRST_TWO = [...D_EDGES, ...D_CORNERS, ...MID_EDGES];

const STAGE = {
  corners1:      { goal: D_CORNERS, fn: placed,   keep: D_EDGES },
  layer2:        { goal: MID_EDGES, fn: placed,   keep: [...D_EDGES, ...D_CORNERS] },
  yellowCross:   { goal: U_EDGES,   fn: upFacing, keep: FIRST_TWO },
  yellowOrient:  { goal: U_CORNERS, fn: upFacing, keep: FIRST_TWO, keepUp: U_EDGES },
  yellowCorners: { goal: U_CORNERS, fn: placed,   keep: FIRST_TWO, keepUp: U_EDGES },
  yellowEdges:   { goal: U_EDGES,   fn: placed,   keep: [...FIRST_TWO, ...U_CORNERS], keepUp: U_EDGES },
};

const ALIGN = ['', 'U', 'U2', "U'"];

/* collapse "R R", "U U'" … so a scene algorithm reads like something a human wrote */
function simplify(alg) {
  const toks = String(alg).trim().split(/\s+/).filter(Boolean);
  const out = [];
  const amount = (t) => (t.endsWith("'") ? 3 : t.endsWith('2') ? 2 : 1);
  const fmt = (face, q) => (q % 4 === 1 ? face : q % 4 === 2 ? face + '2' : face + "'");
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
const invert = (alg) => String(alg).trim().split(/\s+/).filter(Boolean).reverse()
  .map(t => (t.endsWith("'") ? t.slice(0, -1) : t.endsWith('2') ? t : t + "'")).join(' ');
function rotationTo(a, b) {
  for (const u of ALIGN) {
    const c = a.clone(); if (u) c.apply(u);
    if (c.key() === b.key()) return u;
  }
  return null;
}
function sound(c, stage) {
  const st = STAGE[stage];
  if (cnt(c, st.keep) !== st.keep.length) return false;
  if (st.keepUp && cnt(c, st.keepUp, upFacing) !== st.keepUp.length) return false;
  return cnt(c, st.goal, st.fn) < st.goal.length;
}

/* The instruments the site teaches. Nothing else is allowed into a figure. */
const TAUGHT = {
  corners1: [["R U R'", 'درج گوشه، یک تکرار'], ["R U R' U'", 'سکسی، سه تکرار']],
  layer2: [["U R U' R' U' F' U F", 'درج از راست'], ["U' L' U L U F U' F'", 'درج آینه از چپ']],
  yellowCross: [["F R U R' U' F'", 'صلیب زرد']],
  yellowOrient: [["R U R' U R U2 R'", 'سون'], ["R U2 R' U' R U' R'", 'آنتی‌سون']],
  yellowCorners: [["U R U' L' U R' U' L", 'جابه‌جایی سه گوشه'], ["R' F R' B2 R F' R' B2 R2", 'A-Perm']],
  yellowEdges: [["M2 U M U2 M' U M2", 'جابه‌جایی لبه‌ها'], ["R U' R U R U R U' R' U' R2", 'U-Perm']],
};

function candidates(stage, reps = [1, 2, 3]) {
  const out = [];
  for (const [alg, name] of TAUGHT[stage]) {
    for (const k of reps) {
      for (const lead of ALIGN) {
        for (const gap of (k > 1 ? ALIGN : [''])) {
          const parts = [];
          if (lead) parts.push(lead);
          for (let i = 0; i < k; i++) { if (i && gap) parts.push(gap); parts.push(alg); }
          const algStr = parts.join(' ');
          out.push({ alg: algStr, name: k > 1 ? `${name} ×${k}` : name });
        }
      }
    }
  }
  return [...new Map(out.map(o => [o.alg, o])).values()]
    .sort((a, b) => a.alg.split(' ').length - b.alg.split(' ').length);
}

/* ---------------------------------------------------- last layer, backwards */
const LAST = ['yellowEdges', 'yellowCorners', 'yellowOrient', 'yellowCross'];
function lastLayerChain() {
  const picked = {};
  let after = new Cube();                       // solved cube
  let afterAlg = '';                            // algorithm from solved to `after`
  const go = (i) => {
    if (i >= LAST.length) return true;
    const stage = LAST[i];
    for (const cand of candidates(stage)) {
      const fig = after.clone(); fig.apply(invert(cand.alg));
      if (!sound(fig, stage)) continue;
      const chk = fig.clone(); chk.apply(cand.alg);
      if (cnt(chk, STAGE[stage].goal, STAGE[stage].fn) !== STAGE[stage].goal.length) continue;
      const align = rotationTo(chk, after);
      if (align === null) continue;
      const figAlg = simplify((afterAlg + ' ' + invert(cand.alg)).trim());
      picked[stage] = {
        figure: fig, next: after.clone(), name: cand.name,
        figureAlg: figAlg, nextAlg: (figAlg + ' ' + cand.alg + (align ? ' ' + align : '')).trim(),
        lesson: (cand.alg + (align ? ' ' + align : '')).trim(),
      };
      const prev = after, prevAlg = afterAlg;
      after = fig; afterAlg = (afterAlg + ' ' + invert(cand.alg)).trim();
      if (go(i + 1)) return true;
      after = prev; afterAlg = prevAlg; delete picked[stage];
    }
    return false;
  };
  if (!go(0)) throw new Error('no consistent last-layer chain');
  return picked;
}

/* ------------------------------------------- first two layers, also backwards */
function figureBefore(name, afterState, afterAlg = '') {
  for (const cand of candidates(name, [1, 2, 3, 4, 5, 6])) {
    const fig = afterState.clone(); fig.apply(invert(cand.alg));
    if (!sound(fig, name)) continue;
    const chk = fig.clone(); chk.apply(cand.alg);
    if (cnt(chk, STAGE[name].goal, STAGE[name].fn) !== STAGE[name].goal.length) continue;
    const align = rotationTo(chk, afterState);
    if (align === null) continue;
    const figAlg = simplify((afterAlg + ' ' + invert(cand.alg)).trim());
    return {
      figure: fig, next: afterState.clone(), name: cand.name, figureAlg: figAlg,
      nextAlg: (figAlg + ' ' + cand.alg + (align ? ' ' + align : '')).trim(),
      lesson: (cand.alg + (align ? ' ' + align : '')).trim(),
    };
  }
  return null;
}

/* ------------------------------------------------------------ step 1: cross */
const SCRAMBLE = "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2";
const DAISY_ALG = 'R2 L2 F2 B2';
const DAISY_TO_CROSS = 'R2 F2 B2 L2';   // the part of CROSS_ALG after the daisy
/* the cross figure must be a *cross and nothing else*: four white edges with
   their side colours matched, and no corner accidentally in place (an earlier
   candidate quietly solved one corner, which is not what step 1 shows) */
const CROSS_ALG = 'R2 L2 F2 B2 R2 F2 B2 L2';
const scrambleCube = new Cube().apply(SCRAMBLE);
const daisyCube = new Cube().apply(DAISY_ALG);
const crossCube = new Cube().apply(CROSS_ALG);

const ll = lastLayerChain();
const l2 = figureBefore('layer2', ll.yellowCross.figure, ll.yellowCross.figureAlg);
if (!l2) throw new Error('no layer-2 figure');
/* The chain that follows is derived backwards from the solved cube; the white
   cross page keeps its own (separately verified) cross illustration. Both are
   true states, they are simply different examples. */
const c1 = figureBefore('corners1', l2.figure, l2.figureAlg);
if (!c1) throw new Error('no corner figure');
const l2Final = l2;
const crossCubeAligned = crossCube;
/* ------------------------------------------------------------------ assembly */
const SCENES = {
  cross: {
    scramble: scrambleCube, scrambleAlg: SCRAMBLE,
    daisy: daisyCube, daisyAlg: DAISY_ALG,
    cross: crossCubeAligned, crossAlg: CROSS_ALG, daisyCube, daisyToCross: DAISY_TO_CROSS,
    next: c1.figure,
  },
  corners1: { ...c1, figureAlg: c1.figureAlg },
  layer2: l2Final,
  yellowCross: ll.yellowCross,
  yellowOrient: ll.yellowOrient,
  yellowCorners: ll.yellowCorners,
  yellowEdges: ll.yellowEdges,
};

/* ------------------------------------------------------------------- verify */
const ORDER = ['cross', 'corners1', 'layer2', 'yellowCross', 'yellowOrient', 'yellowCorners', 'yellowEdges'];
const ok = (label, cond) => { console.log((cond ? 'PASS  ' : 'FAIL  ') + label); return cond; };
let allOk = true;

allOk &= ok('scramble: cross not built yet', cnt(scrambleCube, D_EDGES) === 0);
allOk &= ok('daisy figure is a real daisy', daisyCube.isDaisy());
allOk &= ok('cross figure is a real white cross with matching sides',
  crossCube.isCross() && D_EDGES.every(p => placed(crossCube, p)));
allOk &= ok('cross figure has no finished corner yet (that is step 2)',
  D_CORNERS.every(p => !placed(crossCube, p)));
allOk &= ok('daisy → cross uses four double turns of side faces',
  SCENES.cross.daisyCube.clone().apply(SCENES.cross.daisyToCross).key() === crossCube.key());
allOk &= ok('the daisy figure does not already have a cross', !daisyCube.isCross());

console.log('\nstep            figure  lesson→  earlier work   instrument');
for (const name of ORDER.slice(1)) {
  const st = STAGE[name];
  const sc = SCENES[name];
  const applied = sc.figure.clone(); applied.apply(sc.lesson);
  const lands = rotationTo(applied, sc.next) !== null;
  allOk &= ok(`${name}: ${cnt(sc.figure, st.goal, st.fn)}/${st.goal.length} → ${
    cnt(applied, st.goal, st.fn)}/${st.goal.length}, earlier work ${cnt(sc.figure, st.keep)}/${st.keep.length}`,
    lands && cnt(applied, st.goal, st.fn) === st.goal.length);
  console.log('   ', sc.lesson.padEnd(46), sc.name);
}

/* every figure must keep the previous figures' achievements */
allOk &= ok('corners1 figure still has the white cross', cnt(SCENES.corners1.figure, D_EDGES) === 4);
allOk &= ok('layer2 figure still has the first layer', cnt(SCENES.layer2.figure, [...D_EDGES, ...D_CORNERS]) === 8);
allOk &= ok('yellowCross figure still has two layers', cnt(SCENES.yellowCross.figure, FIRST_TWO) === 12);
allOk &= ok('final lesson solves the cube', SCENES.yellowEdges.next.solved());

/* the stored algorithms must reproduce the stored states exactly */
for (const name of ORDER.slice(1)) {
  const sc = SCENES[name];
  const replayed = new Cube().apply(sc.figureAlg);
  allOk &= ok(`${name}: stored figure algorithm reproduces the figure`, replayed.key() === sc.figure.key());
  const replayed2 = new Cube().apply(sc.nextAlg);
  allOk &= ok(`${name}: stored next algorithm reproduces the next state`, replayed2.key() === sc.next.key());
}

console.log('\n' + (allOk ? 'ALL CHECKS PASS' : 'SOME CHECKS FAILED'));

if (require.main === module) {
  const payload = {
    scramble: SCRAMBLE,
    daisyAlg: DAISY_ALG,
    daisyToCross: DAISY_TO_CROSS,
    crossAlg: CROSS_ALG,
    steps: {},
  };
  for (const name of ORDER.slice(1)) {
    payload.steps[name] = {
      figureAlg: SCENES[name].figureAlg, lesson: SCENES[name].lesson, instrument: SCENES[name].name,
    };
  }
  fs.writeFileSync(__dirname + '/scenes.json', JSON.stringify(payload, null, 2));
}
module.exports = { SCENES, OK: allOk, ORDER, cnt, STAGE, D_EDGES, D_CORNERS, MID_EDGES, U_EDGES, U_CORNERS, placed, upFacing, invert, DAISY_ALG, CROSS_ALG, SCRAMBLE };
