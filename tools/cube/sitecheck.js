/* sitecheck.js — the published site lives at the repo root (GitHub Pages serves
   the branch root), while the source of truth is web/. This copies nothing: it
   FAILS if the two drift apart, which is exactly how a "it's updated" mistake
   happens.

   Run: node tools/cube/sitecheck.js          check
        node tools/cube/sitecheck.js --sync    copy web/ → root */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '../..');
const WEB = path.join(ROOT, 'web');
const FILES = [
  'index.html',
  'css/app.css',
  'js/app.js',
  'js/cube-engine.js',
  'data/methods.js',
  'fonts/Vazirmatn-Regular.woff2',
  'fonts/Vazirmatn-Medium.woff2',
  'fonts/Vazirmatn-SemiBold.woff2',
  'fonts/Vazirmatn-Bold.woff2',
];
const DIRS = ['css', 'js', 'data', 'fonts'];

const sync = process.argv.includes('--sync');
let bad = 0;

if (sync) {
  for (const d of DIRS) fs.cpSync(path.join(WEB, d), path.join(ROOT, d), { recursive: true });
  fs.copyFileSync(path.join(WEB, 'index.html'), path.join(ROOT, 'index.html'));
  console.log('synced web/ → repo root');
}

for (const rel of FILES) {
  const a = path.join(WEB, rel), b = path.join(ROOT, rel);
  const hasA = fs.existsSync(a), hasB = fs.existsSync(b);
  if (!hasA) { console.log(`FAIL  source missing: web/${rel}`); bad++; continue; }
  if (!hasB) { console.log(`FAIL  published copy missing: /${rel}  → run with --sync`); bad++; continue; }
  const same = fs.readFileSync(a).equals(fs.readFileSync(b));
  if (!same) { console.log(`FAIL  drift: web/${rel} ≠ /${rel}  → run with --sync`); bad++; }
}

/* the published entry point must be the app, not a directory listing or a readme */
const index = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const checks = [
  ['root index.html is the app shell', /<main id="main">/.test(index) && /js\/app\.js/.test(index)],
  ['root index.html points at relative assets only', !/src="\/|href="\/(?!\/)/.test(index)],
  ['CNAME is the custom domain', fs.existsSync(path.join(ROOT, 'CNAME')) && fs.readFileSync(path.join(ROOT, 'CNAME'), 'utf8').trim() === 'robikplatform.com'],
  ['no __pycache__ or build junk committed', !fs.readdirSync(path.join(ROOT, 'book/tools')).some(f => f === '__pycache__')],
];
for (const [label, ok] of checks) {
  if (ok) console.log('ok    ' + label);
  else { console.log('FAIL  ' + label); bad++; }
}

console.log(bad ? `\n${bad} problem(s)` : '\npublished copy matches the source');
process.exit(bad ? 1 : 0);
