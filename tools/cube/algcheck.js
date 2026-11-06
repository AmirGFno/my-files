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

for (const p of CONTENT.puzzles) for (const m of p.methods || []) for (const s of m.steps || []) {
  const figs = (s.states || []).filter(f => f.next);
  if (!figs.length) continue;
  const where = `${p.id}/${m.id}/${s.id}`;
  const lessons = (s.algorithms || []).map(a => a.alg.replace(/\s+/g, ' ').trim());
  for (const fig of figs) {
    const start = new Cube().apply(fig.alg || '');
    const expected = start.clone().apply(fig.next).key();
    const hit = lessons.some(alg => ALIGN.some(u => {
      const c = start.clone(); c.apply(alg); if (u) c.apply(u);
      return c.key() === expected;
    }));
    report(`${where}: a published algorithm reproduces the animated move`, hit);
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
