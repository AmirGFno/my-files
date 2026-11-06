/* sitecheck.js — the source of truth is web/; GitHub Pages publishes docs/.
   This copies nothing by itself: it FAILS when the two drift apart, which is
   exactly how an "is it updated?" mistake happens.

   Run: node tools/cube/sitecheck.js          check
        node tools/cube/sitecheck.js --sync    copy web/ → docs/ */
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '../..');
const WEB = path.join(ROOT, 'web');
const OUT = path.join(ROOT, 'docs');   // what GitHub Pages serves
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
  fs.mkdirSync(OUT, { recursive: true });
  for (const d of DIRS) fs.cpSync(path.join(WEB, d), path.join(OUT, d), { recursive: true });
  fs.copyFileSync(path.join(WEB, 'index.html'), path.join(OUT, 'index.html'));
  console.log('synced web/ → docs/');
}

for (const rel of FILES) {
  const a = path.join(WEB, rel), b = path.join(OUT, rel);
  const hasA = fs.existsSync(a), hasB = fs.existsSync(b);
  if (!hasA) { console.log(`FAIL  source missing: web/${rel}`); bad++; continue; }
  if (!hasB) { console.log(`FAIL  published copy missing: docs/${rel}  → run with --sync`); bad++; continue; }
  const same = fs.readFileSync(a).equals(fs.readFileSync(b));
  if (!same) { console.log(`FAIL  drift: web/${rel} ≠ docs/${rel}  → run with --sync`); bad++; }
}

/* the published entry point must be the app, not a directory listing or a readme */
const index = fs.readFileSync(path.join(OUT, 'index.html'), 'utf8');
const checks = [
  ['docs/index.html is the app shell', /<main id="main">/.test(index) && /js\/app\.js/.test(index)],
  ['docs/index.html uses relative asset paths only', !/src="\/|href="\/(?!\/)/.test(index)],
  ['no CNAME (the site is served from the github.io address)', !fs.existsSync(path.join(ROOT, 'CNAME'))],
  ['no __pycache__ or build junk committed', !fs.readdirSync(path.join(ROOT, 'book/tools')).some(f => f === '__pycache__')],
];
for (const [label, ok] of checks) {
  if (ok) console.log('ok    ' + label);
  else { console.log('FAIL  ' + label); bad++; }
}

console.log(bad ? `\n${bad} problem(s)` : '\npublished copy matches the source');
process.exit(bad ? 1 : 0);
