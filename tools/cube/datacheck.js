/* datacheck.js — content lint: no dead links, no empty steps, no duplicate ids.
   Run: node tools/cube/datacheck.js */
const fs = require('fs');
const path = require('path');
const mod = { exports: {} };
new Function('module', 'exports', 'window',
  fs.readFileSync(path.join(__dirname, '../../web/data/methods.js'), 'utf8') + '\nmodule.exports = CONTENT;')(mod, mod.exports, undefined);
const C = mod.exports;

let bad = 0;
const fail = (m) => { bad++; console.log('FAIL  ' + m); };
const ok = (m) => console.log('ok    ' + m);

const puzIds = new Set();
for (const p of C.puzzles) {
  if (puzIds.has(p.id)) fail(`duplicate puzzle id ${p.id}`);
  puzIds.add(p.id);
  const mIds = new Set();
  for (const m of p.methods || []) {
    if (mIds.has(m.id)) fail(`duplicate method id ${p.id}/${m.id}`);
    mIds.add(m.id);
    if (!m.summary) fail(`method without summary: ${p.id}/${m.id}`);
    const sIds = new Set((m.steps || []).map(s => s.id));
    for (const s of m.steps || []) {
      const where = `${p.id}/${m.id}/${s.id}`;
      if (!s.title) fail(`step without title: ${where}`);
      if (m.status === 'ready') {
        if (!s.goal) fail(`ready step without goal: ${where}`);
        if (!(s.steps || []).length) fail(`ready step without a numbered walkthrough: ${where}`);
      }
      for (const st of s.states || []) {
        if (!st.label) fail(`figure without label: ${where}`);
        if (st.next && !st.alg) fail(`figure has next but no start alg: ${where}`);
      }
      for (const a of s.alternatives || []) {
        if (a.ref && a.ref !== s.id && !sIds.has(a.ref)) {
          console.log(`warn  alternative "${a.name}" in ${where} points at missing step ${a.ref} (rendered as "به‌زودی")`);
        }
      }
      for (const a of s.algorithms || []) if (!a.alg) fail(`algorithm row without alg: ${where}`);
    }
  }
}
console.log(bad ? `\n${bad} problem(s)` : '\ncontent is clean');
process.exit(bad ? 1 : 0);
