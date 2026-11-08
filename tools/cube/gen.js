/* gen.js — emit the seven scenes of the beginner method, straight from the one
   real solve in solve.js.

   It used to build each scene backwards from the solved cube, which produced
   seven true but unrelated pictures: step 5 did not start from step 4's cube.
   Now the scenes are stages of a single solve, and everything the site shows is
   checked here before it is published.

   Run: node gen.js > scenes.txt   (also writes scenes.json)
*/
const fs = require('fs');
const path = require('path');
const { Cube } = require(path.join(__dirname, '../../web/js/cube-engine.js'));
const S = require('./solve.js');

const { solveFrom, check, toData, checkData, STAGE, ORDER, placed, cnt, done } = S;
const D_EDGES = S.D_EDGES, D_CORNERS = S.D_CORNERS, MID_EDGES = S.MID_EDGES;
const U_EDGES = S.U_EDGES, U_CORNERS = S.U_CORNERS;
const FIRST_TWO = [...D_EDGES, ...D_CORNERS, ...MID_EDGES];

const SCRAMBLE = "R U F' L2 D B' R2 U' F2 D2 L B2 U2 R' F D' L2 B U2";
const result = solveFrom(SCRAMBLE);
if (!result.ok) {
  console.error(`the solve stopped at ${result.at}`);
  process.exit(1);
}
const data = toData(result);
const F = result.figs;

const ok = (label, cond) => { console.log((cond ? 'PASS  ' : 'FAIL  ') + label); return cond; };
let allOk = true;
allOk &= ok('the solve is one continuous chain (see solve.js)', check(result).length === 0);
allOk &= ok('the figures agree with the solve they came from', checkData(data, result).length === 0);

/* ---- the scenes, as the site stores them ---- */
const SCENES = { scramble: SCRAMBLE, states: data.states, moves: F, data };

/* ------------------------------------------------------------------- verify */
console.log('\nstep             figure   lesson→   earlier work   camera');
for (const name of ORDER) {
  const list = data.states[name];
  const last = list[list.length - 1];
  const fig = new Cube().apply(list[0].alg || '');
  const after = fig.clone().apply(list[0].next || '');
  const st = STAGE[name];
  const keepList = st.keep && st.keep.length ? st.keep : null;
  const kept = keepList ? cnt(after, keepList) + '/' + keepList.length : '—';
  /* the step's first figure must lead to the step's second figure; the cross is
     the one step with three figures (scrambled → daisy → cross) */
  const target = name === 'cross' ? list[1].alg : last.alg;
  allOk &= ok(`${name}: figure → lesson → next figure`, after.key() === new Cube().apply(target || '').key());
  console.log('   ', name.padEnd(13), list[0].view.padEnd(8), kept, '  ', (list[0].next || '—').slice(0, 46));
}

/* the facts each step is supposed to show */
const cube = (alg) => new Cube().apply(alg || '');
allOk &= ok('the first figure is the scrambled cube', !cube(data.states.cross[0].alg).isCross());
allOk &= ok('the daisy figure is a real daisy', cube(data.states.cross[1].alg).isDaisy());
allOk &= ok('the cross figure is a real white cross', cube(data.states.cross[2].alg).isCross());
allOk &= ok('the cross figure has no corner finished yet (that is step 2)',
  D_CORNERS.every(p => !placed(cube(data.states.cross[2].alg), p)));
allOk &= ok('the corners figure has the whole first layer',
  cnt(cube(data.states.corners1[1].alg), D_CORNERS) === 4 && cnt(cube(data.states.corners1[1].alg), D_EDGES) === 4);
allOk &= ok('the layer-2 figure has two complete layers',
  cnt(cube(data.states.layer2[1].alg), FIRST_TWO) === 12);
allOk &= ok('the yellow-cross figure has two layers and four yellow edges up',
  cnt(cube(data.states.yellowCross[1].alg), FIRST_TWO) === 12 &&
  U_EDGES.every(p => cube(data.states.yellowCross[1].alg).at(p, 'U') === 'U'));
allOk &= ok('the yellow-face figure has the whole yellow face',
  U_CORNERS.every(p => cube(data.states.yellowOrient[1].alg).at(p, 'U') === 'U'));
allOk &= ok('the last figure is a solved cube', cube(data.states.yellowEdges[1].alg).solved());

/* every stage really starts where the previous one ended */
for (let i = 1; i < ORDER.length; i++) {
  const prev = data.states[ORDER[i - 1]];
  const cur = data.states[ORDER[i]];
  allOk &= ok(`${ORDER[i]} starts where ${ORDER[i - 1]} ended`,
    cube(prev[prev.length - 1].alg).key() === cube(cur[0].alg).key());
}

/* a step must show something: no figure pair may have an empty `next` */
for (const name of ORDER) {
  const list = data.states[name];
  allOk &= ok(`${name}: the step has moves to show`, list[0].next && list[0].next.trim().length > 0);
}

console.log('\n' + (allOk ? 'ALL CHECKS PASS' : 'SOME CHECKS FAILED'));

if (require.main === module) {
  const payload = {
    scramble: result.scramble,
    states: data.states,
    moves: {
      cross: { daisy: F.cross.daisyLesson, drop: F.cross.dropLesson, all: F.cross.lesson },
      corners1: F.corners1.lesson,
      layer2: F.layer2.lesson,
      yellowCross: F.yellowCross.lesson,
      yellowOrient: F.yellowOrient.lesson,
      yellowCorners: F.yellowCorners.lesson,
      yellowEdges: F.yellowEdges.lesson,
    },
    views: { cross: 'bottom', corners1: 'bottom', layer2: 'bottom', yellowCross: 'top', yellowOrient: 'top', yellowCorners: 'top', yellowEdges: 'top' },
  };
  fs.writeFileSync(path.join(__dirname, 'scenes.json'), JSON.stringify(payload, null, 2));
}

module.exports = { SCENES, OK: allOk, ORDER, data, result, SCRAMBLE, placed, cnt };
