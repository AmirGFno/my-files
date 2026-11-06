/* algcheck.js — verify that the algorithm printed on a page is the one its own
   figure uses. This catches "the text says R U R' but the picture plays
   something else", which is the easiest mistake to ship and the hardest to see.

   Run: node tools/cube/algcheck.js */
const fs = require('fs');
const path = require('path');
const enginePath = path.join(__dirname, '../../web/js/cube-engine.js');
const src = fs.readFileSync(enginePath, 'utf8');
const win = {};
new Function('window', 'module', 'exports', 'requestAnimationFrame', 'cancelAnimationFrame', 'devicePixelRatio',
  src + '\nwindow.__x = { Cube };')(win, {}, {}, () => {}, () => {}, 1);
const { Cube } = win.__x;

const mod = { exports: {} };
new Function('module', 'exports', 'window',
  fs.readFileSync(path.join(__dirname, '../../web/data/methods.js'), 'utf8') + '\nmodule.exports = CONTENT;')(mod, mod.exports, undefined);
const CONTENT = mod.exports;

let bad = 0, good = 0;
const report = (label, pass) => {
  if (pass) { good++; console.log('PASS  ' + label); }
  else { bad++; console.log('FAIL  ' + label); }
};
const ALIGN = ['', 'U', 'U2', "U'"];
/* a lesson printed on the page and the same lesson played by the figure are
   compared after the obvious simplifications (F' F cancels, R R2 = R') */
const { simplify } = require('./solve.js');

/* A figure's `next` is what the button actually plays. Since a step can need the
   same instrument more than once, `next` may be a chain of the step's published
   algorithms, optionally separated by U alignments — but it must be nothing else.
   This is the check that "the picture only ever does what the page teaches". */
const tokens = (alg) => String(alg || '').trim().split(/\s+/).filter(Boolean);

/* The curriculum, written down as patterns. A figure may only play moves that
   fit one of these — that is what "the picture teaches what the page teaches"
   means in practice. A pattern is a list of steps; each step is either a literal
   move, `*` (any single face turn, incl. double and prime) or one of the named
   shapes below. */
const SIDE = 'FRBLUD';
const ANY = /^[FRBLUDMES](2|')?$/;   /* any turn, slice moves included */
/* `X U X'`: turn a face, turn the top, turn the face back — half a trigger */
const HALF = (t, i) => {
  const a = t[i], u = t[i + 1], b = t[i + 2];
  if (!a || !u || !b) return 0;
  if (!ANY.test(a) || !/^U(2|')?$/.test(u)) return 0;
  const inv = (m) => (m.length === 1 ? m + "'" : m.endsWith("'") ? m[0] : m[0] + '2');
  return inv(a) === b ? 3 : 0;
};
/* the middle-layer insert, 8 moves: U A U' A' U' B' U B */
const INSERTS = [];
for (const A of SIDE) for (const B of SIDE) {
  if (A === B) continue;
  INSERTS.push([`U`, `${A}`, `U'`, `${A}'`, `U'`, `${B}'`, `U`, `${B}`]);
  INSERTS.push([`U'`, `${B}'`, `U`, `${B}`, `U`, `${A}`, `U'`, `${A}'`]);
}

/** can `alg` be read as a sequence of the step's allowed shapes? */
function fitsCurriculum(alg, step) {
  const t = tokens(simplify(alg));
  const patterns = step.patterns || [];
  /* a step may need its own algorithm twice in a row (or after an alignment),
     so pairs of published algorithms are phrases too, written the way the two
     fuse together (F' F cancels) */
  const single = (step.algorithms || []).map(a => tokens(simplify(a.alg)));
  const literals = [...single];
  for (const a of single) for (const b of single) literals.push(tokens(simplify(a.join(' ') + ' ' + b.join(' '))));
  let i = 0;
  while (i < t.length) {
    if (step.anyTurn && ANY.test(t[i])) { i += 1; continue; }
    if (/^U(2|')?$/.test(t[i])) { i += 1; continue; }               /* aligning the top */
    const hit = patterns.find(p => p.every((x, k) => t[i + k] === x)) ||
      literals.find(p => p.every((x, k) => t[i + k] === x));
    if (hit) { i += hit.length; continue; }
    const half = HALF(t, i);                                        /* X U X' */
    if (half && step.trigger) { i += half; continue; }
    if (step.inserts && INSERTS.some(p => p.every((x, k) => x === t[i + k]))) {
      i += 8; continue;
    }
    return false;
  }
  return true;
}

/* what each step is allowed to show */
const CURRICULUM = {
  cross: { anyTurn: true },                       /* turning faces is the lesson */
  corners1: { trigger: true },                    /* lift a corner, align, drop it */
  layer2: { trigger: true, inserts: true },       /* the two inserts, and ejecting */
  'yellow-cross': {},
  'yellow-corners-orient': {},
  'yellow-corners-permute': {},
  'yellow-edges-permute': { triggers: true },
};

for (const p of CONTENT.puzzles) for (const m of p.methods || []) for (const s of m.steps || []) {
  const figs = (s.states || []).filter(f => f.next);
  if (!figs.length) continue;
  const where = `${p.id}/${m.id}/${s.id}`;
  const lessons = (s.algorithms || []).map(a => a.alg.replace(/\s+/g, ' ').trim());
  const plan = CURRICULUM[s.id] || {};
  for (const fig of figs) {
    report(`${where}: the animation only uses the algorithms this page teaches`,
      fitsCurriculum(fig.next, { ...plan, algorithms: s.algorithms || [] }));
    /* and the animation must actually change the cube */
    const start = new Cube().apply(fig.alg || '');
    const after = start.clone().apply(fig.next);
    report(`${where}: the animation does not change the cube`,
      after.key() !== start.key());
  }
}

/* the figures of a step are windows on one solve: the end of one figure is the
   start of the next, and the printed algorithm really produces it */
for (const p of CONTENT.puzzles) for (const m of p.methods || []) for (const s of m.steps || []) {
  const list = s.states || [];
  const where = `${p.id}/${m.id}/${s.id}`;
  for (let i = 0; i + 1 < list.length; i++) {
    const a = new Cube().apply(list[i].alg || '');
    const moved = a.clone().apply(list[i].next || '');
    report(`${where}: figure ${i + 1} of ${list.length} does not lead to the next figure`,
      moved.key() === new Cube().apply(list[i + 1].alg || '').key());
  }
}

/* every published algorithm must at least be legal notation */
for (const p of CONTENT.puzzles) for (const m of p.methods || []) for (const s of m.steps || []) {
  for (const a of s.algorithms || []) {
    let okAlg = true;
    try { new Cube().apply(a.alg); } catch (e) { okAlg = false; }
    if (!okAlg) report(`${p.id}/${m.id}/${s.id}: illegal notation "${a.alg}"`, false);
  }
}

console.log(`\n${good} passed, ${bad} failed`);
process.exit(bad ? 1 : 0);
