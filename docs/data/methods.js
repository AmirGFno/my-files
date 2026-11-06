/* ==========================================================================
   methods.js — the content model of the platform.
   هر پازل → چند روش → هر روش چند گام → هر گام شش بخش ثابت.
   Adding a puzzle or a method is a data edit, not a code edit.
   ========================================================================== */

const CONTENT = {
  version: 1,
  puzzles: [
    /* ------------------------------------------------------------------ 3x3 */
    {
      id: '3x3',
      name: 'مکعب ۳×۳',
      en: '3×3×3',
      status: 'ready',
      intro: 'پایه‌ی همه‌ی روبیک‌ها. اگر این را یاد بگیری، بقیه نسخه‌های ساده‌ترند.',
      methods: [
        /* ---------------------------------------------------------- LBL */
        {
          id: 'lbl',
          name: 'لایه‌به‌لایه',
          en: 'Layer by Layer',
          level: 'beginner',
          status: 'ready',
          algorithms: 6,
          summary: 'اولین روشی که باید یاد بگیری. فقط ۶ الگوریتم و مسیر خطی.',
          why: 'این روش مکعب را از پایین به بالا می‌سازد و در هر گام فقط یک چیز را تغییر می‌دهد. ' +
               'برای کسی که تازه شروع کرده، مهم‌ترین ویژگی‌اش این است که هیچ‌وقت نمی‌گوید «حالا چه کار کنم؟»',
          steps: [
            {
              id: 'cross',
              title: 'صلیب سفید',
              goal: 'چهار لبه‌ی سفید در لایه‌ی پایین، هر کدام بالای مرکز هم‌رنگ خودش.',
              why: 'لبه‌ی سفید یک قطعه با دو رنگ است. تا وقتی رنگ دوم با مرکز هم‌رنگش یکی نشود، ' +
                   'لبه در جای درست نیست — حتی اگر سفیدش رو به پایین باشد.',
              states: [
                { label: 'شروع: مکعب به‌هم‌ریخته', alg: 'R U F\' L2 D B\' R2 U\' F2 D2 L B2 U2 R\' F D\' L2 B U2', next: null, view: 'default' },
                { label: 'دیزی: چهار سفید دور مرکز زرد', alg: 'R2 L2 F2 B2', next: 'R2 F2 B2 L2', view: 'top' },
                { label: 'صلیب سفید: هر لبه بالای مرکز هم‌رنگش', alg: 'R2 L2 F2 B2 R2 F2 B2 L2', next: null, view: 'bottom' },
              ],
              steps: [
                { t: 'لبه‌های سفید را بالا بیاور', d: 'سفیدها را دور مرکز زرد جمع کن، رو به بالا.' },
                { t: 'رنگ کنار لبه را بسنج', d: 'سبز روی مرکز سبز، قرمز روی قرمز.' },
                { t: 'لبه را پایین بیاور', d: 'همان وجه را دو حرکت بچرخان.' },
                { t: 'هر چهار لبه را تکرار کن', d: 'ترتیب مهم نیست؛ هر لبه مستقل است.' },
              ],
              algorithms: [
                { alg: 'R2 L2 F2 B2', label: 'تمرین: ساخت دیزی از مکعب حل‌شده' },
                { alg: 'R2 F2 B2 L2', label: 'تمرین: چهار جفت لبه را پایین بیاور (دیزی → صلیب)' },
              ],
              mistakes: [
                'لبه‌ی سفید رو به بالا مانده: یک حرکت پایینش بیاور و از نو تطبیق بده.',
                'دیزی کامل است ولی صلیب کج است: هر لبه را جداگانه پایین بیاور، نه همه را با هم.',
              ],
              alternatives: [
                { name: 'دیزی', why: 'بدون نیاز به دیدن لبه‌های پایین', moves: '۱۲–۱۶',
                  difficulty: 1, ref: 'cross', recommended: true },
                { name: 'صلیب مستقیم', why: 'حرکت کمتر، نیاز به دید فضایی', moves: '۶–۱۰',
                  difficulty: 3, ref: 'cross-direct' },
                { name: 'صلیب کور', why: 'پایه‌ی سرعت در CFOP', moves: '۸',
                  difficulty: 5, ref: 'cross-blind' },
              ],
            },
            {
              id: 'corners1',
              title: 'گوشه‌های لایه اول',
              goal: 'چهار گوشه‌ی سفید در جای خود، با رنگ‌های کناری هم‌رنگ مرکزها.',
              why: 'گوشه سه رنگ دارد، پس سه شرط باید همزمان برقرار شود. به همین دلیل «تکرار یک الگوریتم کوتاه» ' +
                   'از «الگوریتم مخصوص هر حالت» امن‌تر است: فقط باید بدانی گوشه بالای خانه‌ی درست است یا نه.',
              states: [
                { label: 'قبل از این گام: سه گوشه جاشده، یکی مانده', alg: 'M2 U\' M U2 M\' U\' M2 R2 B2 R F R\' B2 R F\' R2 U2 R\' U\' R U\' R\' F U R U\' R\' F2 U\' F U R U R\' U\' R U\' R\'', next: 'R U R\'', view: 'bottom' },
              ],
              steps: [
                { t: 'گوشه را بالای خانه‌اش بگیر', d: 'رنگ‌های کنارش را با دو مرکز کنار هم تطبیق بده.' },
                { t: 'R U R\' U\' را تکرار کن', d: 'تا وقتی گوشه در جای خودش بنشیند.' },
                { t: 'سه گوشه‌ی دیگر را تکرار کن', d: 'هر بار فقط یک گوشه را جابه‌جا کن.' },
              ],
              algorithms: [
                { alg: 'R U R\' U\'', label: 'تکرار تا جا افتادن' },
                { alg: 'R\' D\' R D', label: 'روش جایگزین' },
              ],
              mistakes: [
                'اگر گوشه‌ای بعد از ۶ تکرار جا نیفتاد، رنگ‌های کنارش با مرکزها نمی‌خوانند؛ آن را یک دور بچرخان.',
              ],
              alternatives: [
                { name: 'تکرار سکسی', why: 'حفظ کردن صفر، فقط تکرار', moves: '۳ تا ۱۸',
                  difficulty: 1, ref: 'corners1', recommended: true },
                { name: 'الگوریتم مستقیم', why: 'حرکت کمتر، تشخیص سخت‌تر', moves: '۳',
                  difficulty: 3, ref: 'corners1-direct' },
                { name: 'Keyhole', why: 'اگر یک گوشه را عمداً باز بگذاری', moves: '۴',
                  difficulty: 4, ref: 'corners1-keyhole' },
              ],
            },
            {
              id: 'layer2',
              title: 'لبه‌های لایه دوم',
              goal: 'چهار لبه‌ی میانی در جای خود؛ دو لایه‌ی پایین کامل.',
              why: 'این گام اولین جایی است که یک الگوریتم واقعی حفظ می‌کنی. الگوریتم دو بخش دارد: ' +
                   'لبه را از بالا جدا می‌کند، و بعد در شکاف کنار می‌نشاند.',
              states: [
                { label: 'قبل از این گام: یک لبه‌ی میانی مانده', alg: 'M2 U\' M U2 M\' U\' M2 R2 B2 R F R\' B2 R F\' R2 U2 R\' U\' R U\' R\' F U R U\' R\' F2 U\' F U R U R\' U\'', next: 'U R U\' R\' U\' F\' U F', view: 'default' },
              ],
              steps: [
                { t: 'لبه‌ی درست را در بالا پیدا کن', d: 'دو رنگش باید با دو مرکز همسایه یکی باشد.' },
                { t: 'بالای خانه‌ی مقصد بگیر', d: 'اگر باید به راست برود: U R U\' R\' U\' F\' U F' },
                { t: 'اگر باید به چپ برود', d: 'همان الگوریتم آینه‌ای: U\' L\' U L U F U\' F\'' },
              ],
              algorithms: [
                { alg: 'U R U\' R\' U\' F\' U F', label: 'درج از راست' },
                { alg: 'U\' L\' U L U F U\' F\'', label: 'درج آینه‌ای از چپ' },
              ],
              mistakes: [
                'اگر لبه‌ای در لایه‌ی دوم است ولی برعکس، اول با یک الگوریتم بیرونش بیاور، بعد دوباره جا بنداز.',
              ],
              alternatives: [
                { name: 'درج از راست', why: 'الگوریتم کوتاه و قابل تکرار', moves: '۸',
                  difficulty: 2, ref: 'layer2', recommended: true },
                { name: 'درج آینه‌ای از چپ', why: 'بدون چرخش مکعب', moves: '۸',
                  difficulty: 2, ref: 'layer2-left' },
                { name: 'Keyhole', why: 'سریع‌تر برای چند لبه پشت سر هم', moves: '۴–۶',
                  difficulty: 4, ref: 'layer2-keyhole' },
              ],
            },
            {
              id: 'yellow-cross',
              title: 'صلیب زرد',
              goal: 'چهار لبه‌ی زرد رو به بالا؛ شکل صلیب روی وجه زرد.',
              why: 'در این گام مهم نیست لبه‌ها کجا هستند، فقط جهتشان مهم است. برای همین یک الگوریتم ' +
                   'کوچک کافی است: از «نقطه» به «ال»، از «ال» به «خط»، از «خط» به صلیب.',
              states: [
                { label: 'خط زرد — نه صلیب', alg: 'M2 U\' M U2 M\' U\' M2 R2 B2 R F R\' B2 R F\' R2 U2 R\' U\' R U\' R\' F U R U\' R\' F\'', next: 'F R U R\' U\' F\'', view: 'top' },
              ],
              steps: [
                { t: 'شکل را تشخیص بده', d: 'نقطه، ال، یا خط.' },
                { t: 'مکعب را درست بگیر', d: 'ال را طوری بگیر که گوشه‌اش بالا-چپ باشد.' },
                { t: 'F R U R\' U\' F\' را بزن', d: 'هر بار یک پله به صلیب نزدیک‌تر می‌شوی.' },
              ],
              algorithms: [
                { alg: 'F R U R\' U\' F\'', label: 'الگوریتم اصلی' },
                { alg: 'Fw R U R\' U\' Fw\'', label: 'نسخه‌ی عریض' },
              ],
              mistakes: [
                'اگر بعد از دو بار هنوز صلیب نشد، جهت گرفتن مکعب اشتباه است؛ ال را دوباره تنظیم کن.',
              ],
              alternatives: [
                { name: 'F R U R\' U\' F\'', why: 'کوتاه‌ترین و امن‌ترین', moves: '۶',
                  difficulty: 1, ref: 'yellow-cross', recommended: true },
                { name: 'نسخه‌ی عریض', why: 'زاویه‌ی دست بهتر برای حالت نقطه', moves: '۶',
                  difficulty: 2, ref: 'yellow-cross-wide' },
                { name: '۲-Look OLL', why: 'صلیب و گوشه‌ها را با هم', moves: '۹',
                  difficulty: 3, ref: 'two-look-oll' },
              ],
            },
            {
              id: 'yellow-corners-orient',
              title: 'جهت گوشه‌های زرد',
              goal: 'تمام وجه زرد یک‌رنگ؛ گوشه‌ها لازم نیست در جای خودشان باشند.',
              why: 'الگوریتم سون سه گوشه را می‌چرخاند و یکی را دست نمی‌زند. با تکرار آن و چرخاندن وجه پایین، ' +
                   'همه‌ی گوشه‌ها بالا می‌آیند بدون اینکه چیزی خراب شود.',
              states: [
                { label: 'صلیب زرد آماده، گوشه‌ها برگشته', alg: 'M2 U\' M U2 M\' U\' M2 R2 B2 R F R\' B2 R F\' R2 U2 R\' U\' R U\' R\'', next: 'R U R\' U R U2 R\'', view: 'top' },
              ],
              steps: [
                { t: 'سون یا آنتی‌سون را تشخیص بده', d: 'دو گوشه بالا، دو گوشه پایین.' },
                { t: 'R U R\' U R U2 R\' را بزن', d: 'یا معکوسش، بسته به جهت.' },
              ],
              algorithms: [
                { alg: 'R U R\' U R U2 R\'', label: 'سون' },
                { alg: 'R U2 R\' U\' R U\' R\'', label: 'آنتی‌سون' },
              ],
              mistakes: ['سون را روی حالت اشتباه بزنی، وضعیت را عوض می‌کند ولی حل نمی‌کند؛ از نو تشخیص بده.'],
              alternatives: [
                { name: 'سون', why: 'دو الگوریتم ساده برای همه‌ی حالت‌ها', moves: '۷',
                  difficulty: 1, ref: 'yellow-corners-orient', recommended: true },
                { name: 'تکرار سکسی', why: 'بدون حفظ کردن، ولی کند', moves: '۶ تا ۱۲',
                  difficulty: 1, ref: 'sune-repeat' },
                { name: 'OCLL کامل', why: '۷ حالت، یک‌ضربه‌ای', moves: '۷–۹',
                  difficulty: 3, ref: 'ocll' },
              ],
            },
            {
              id: 'yellow-corners-permute',
              title: 'جای گوشه‌های زرد',
              goal: 'چهار گوشه در جای خودشان؛ ممکن است نیاز به چرخش نهایی داشته باشند.',
              why: 'نیکلاس سه گوشه را در یک چرخه جابه‌جا می‌کند و گوشه‌ی چهارم را نگه می‌دارد. ' +
                   'چون گوشه‌ی چهارم ثابت است، همیشه می‌شود با حداکثر دو اجرا کار را تمام کرد.',
              states: [
                { label: 'وجه زرد کامل، گوشه‌ها جابه‌جا', alg: 'M2 U\' M U2 M\' U\' M2 R2 B2 R F R\' B2 R F\' R', next: 'R\' F R\' B2 R F\' R\' B2 R2', view: 'top' },
              ],
              steps: [
                { t: 'یک گوشه‌ی درست پیدا کن', d: 'اگر هیچ‌کدام درست نیست، یک بار الگوریتم را بزن.' },
                { t: 'آن گوشه را در جای خودش نگه دار', d: 'و الگوریتم را روی سه گوشه‌ی دیگر بزن.' },
              ],
              algorithms: [
                { alg: 'U R U\' L\' U R\' U\' L', label: 'نیکلاس' },
                { alg: 'R\' F R\' B2 R F\' R\' B2 R2', label: 'A-Perm' },
              ],
              mistakes: ['اگر هیچ گوشه‌ای سرجایش نیست، یک گوشه را بالای جای درستش بگیر، الگوریتم را یک بار بزن، بعد دوباره نگاه کن.'],
              alternatives: [
                { name: 'نیکلاس', why: 'کوتاه و برای مبتدی کافی', moves: '۸',
                  difficulty: 2, ref: 'yellow-corners-permute', recommended: true },
                { name: 'A-Perm', why: 'استاندارد و سریع‌تر', moves: '۹',
                  difficulty: 3, ref: 'a-perm' },
              ],
            },
            {
              id: 'yellow-edges-permute',
              title: 'جای لبه‌های زرد',
              goal: 'مکعب حل‌شده. آخرین گام!',
              why: 'یک الگوریتم، سه لبه را در یک دایره جابه‌جا می‌کند. اگر چهار لبه جابه‌جا باشند، ' +
                   'دو بار اجرا لازم است — و همین تنها چیزی است که باید یاد بگیری.',
              states: [
                { label: 'فقط جای سه لبه مانده', alg: 'M2 U\' M U2 M\' U\' M2', next: 'M2 U M U2 M\' U M2', view: 'top' },
              ],
              steps: [
                { t: 'لبه‌ها را نگاه کن', d: 'سه‌تایی جابه‌جا یا دوتایی.' },
                { t: 'U-Perm را بزن', d: 'تا همه سر جایشان بروند.' },
              ],
              algorithms: [
                { alg: 'M2 U M U2 M\' U M2', label: 'U-Perm (ام‌محور)' },
                { alg: 'R U\' R U R U R U\' R\' U\' R2', label: 'U-Perm استاندارد' },
              ],
              mistakes: ['اگر مکعب حل شد ولی یک لبه برعکس است، مکعب فیزیکی‌ات خراب شده، نه الگوریتم.'],
              alternatives: [
                { name: 'U-Perm', why: 'الگوریتم پایه، همیشه کار می‌کند', moves: '۹',
                  difficulty: 2, ref: 'yellow-edges-permute', recommended: true },
                { name: 'نسخه‌ی ام‌محور', why: 'دست راحت‌تر، سرعت بیشتر', moves: '۹',
                  difficulty: 3, ref: 'u-perm-m' },
                { name: 'EPLL کامل', why: 'چهار حالت، یک‌ضربه‌ای', moves: '۴–۹',
                  difficulty: 4, ref: 'epll' },
              ],
            },
          ],
        },
        /* ------------------------------------------------------- Petrus */
        {
          id: 'petrus',
          name: 'پتروس',
          en: 'Petrus',
          level: 'mid',
          status: 'outline',
          algorithms: 40,
          summary: 'بلوک‌سازی شهودی؛ فکر کردن به‌جای حفظ کردن.',
          why: 'اگر از تکرار الگوریتم خسته شده‌ای، این روش جای خوبی برای شروع است: بیشتر کار با فهم است.',
          steps: [
            { id: 'block222', title: 'بلوک ۲×۲×۲', goal: 'یک گوشه‌ی مکعب را کامل کن.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'block223', title: 'گسترش به ۲×۲×۳', goal: 'یک لایه‌ی کامل به بلوک اضافه کن.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'eo', title: 'جهت‌گیری لبه‌ها', goal: 'همه‌ی لبه‌های باقی‌مانده جهت‌دار شوند.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'f2l', title: 'دو لایه‌ی آخر', goal: 'دو لایه‌ی باقی‌مانده را کامل کن.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'll', title: 'لایه آخر', goal: 'COLL و EPLL.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
          ],
        },
        /* ------------------------------------------------------------ ZZ */
        {
          id: 'zz',
          name: 'زد-زد',
          en: 'ZZ',
          level: 'mid',
          status: 'outline',
          algorithms: 50,
          summary: 'بدون چرخش مکعب؛ همه‌ی لبه‌ها از اول جهت‌دار می‌شوند.',
          why: 'زیباترین روش از نظر منطقی: با جهت‌گیری لبه‌ها در همان ابتدا، تمام F2L بدون چرخش انجام می‌شود.',
          steps: [
            { id: 'eoline', title: 'EOLine', goal: 'همه‌ی لبه‌ها جهت‌دار + خط پایین.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'f2l', title: 'F2L بدون چرخش', goal: 'دو بلوک پایین.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'ocll', title: 'جهت گوشه‌های بالا', goal: 'وجه بالا یک‌رنگ.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'pll', title: 'جای لایه آخر', goal: 'PLL.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
          ],
        },
        /* ---------------------------------------------------------- CFOP */
        {
          id: 'cfop',
          name: 'سی‌اف‌اوپی',
          en: 'CFOP',
          level: 'pro',
          status: 'outline',
          algorithms: 119,
          summary: 'محبوب‌ترین روش سرعتی دنیا؛ سقف سرعت.',
          why: 'اگر هدف زمان است، اینجا تمام می‌شود: ۱۱۹ الگوریتم، تقسیم‌بندی چهار مرحله‌ای، و بیشترین منابع تمرینی.',
          steps: [
            { id: 'cross', title: 'کراس', goal: 'صلیب در لایه‌ی پایین.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'f2l', title: 'F2L', goal: 'دو لایه‌ی اول با جفت‌سازی.', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'oll', title: 'OLL', goal: 'جهت‌گیری کل لایه آخر (۵۷ حالت).', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
            { id: 'pll', title: 'PLL', goal: 'جای‌گذاری لایه آخر (۲۱ حالت).', why: '', steps: [], algorithms: [], mistakes: [], alternatives: [] },
          ],
        },
      ],
    },

    /* ------------------------------------------------------------------ 2x2 */
    {
      id: '2x2',
      name: 'مکعب ۲×۲',
      en: '2×2×2',
      status: 'planned',
      intro: 'بدون مرکز و بدون لبه؛ فقط گوشه. بعد از ۳×۳ تقریباً یک تمرین است.',
      methods: [
        {
          id: 'lbl2',
          name: 'لایه‌به‌لایه',
          en: 'Layer by Layer',
          level: 'beginner',
          status: 'planned',
          algorithms: 3,
          summary: 'همان منطق ۳×۳ با دو گام کمتر.',
          why: '',
          steps: [],
        },
        {
          id: 'ortega',
          name: 'اورتگا',
          en: 'Ortega',
          level: 'mid',
          status: 'planned',
          algorithms: 12,
          summary: 'محبوب‌ترین روش ۲×۲؛ یک وجه + OLL + PBL.',
          why: '',
          steps: [],
        },
        {
          id: 'cll',
          name: 'CLL',
          en: 'CLL',
          level: 'pro',
          status: 'planned',
          algorithms: 42,
          summary: 'یک گام برای کل لایه آخر.',
          why: '',
          steps: [],
        },
      ],
    },

    /* ------------------------------------------------------------- others */
    { id: '4x4', name: 'مکعب ۴×۴', en: '4×4×4', status: 'planned', intro: 'روش Reduction و Yau.', methods: [] },
    { id: '5x5', name: 'مکعب ۵×۵', en: '5×5×5', status: 'planned', intro: 'Reduction، Yau5 و Hoya.', methods: [] },
    { id: 'pyraminx', name: 'هرمینکس', en: 'Pyraminx', status: 'planned', intro: 'ساده‌ترین پازل برای شروع بعد از ۲×۲.', methods: [] },
    { id: 'megaminx', name: 'مگامینکس', en: 'Megaminx', status: 'planned', intro: 'دوازده وجه، همان منطق لایه‌به‌لایه.', methods: [] },
    { id: 'skewb', name: 'اسکیوب', en: 'Skewb', status: 'planned', intro: 'چهار محور چرخش، روش Sarah.', methods: [] },
    { id: 'square1', name: 'اسکوئر-۱', en: 'Square-1', status: 'planned', intro: 'تنها پازل «شکل‌عوض‌کن» فهرست.', methods: [] },
  ],
};

if (typeof window !== 'undefined') window.CONTENT = CONTENT;
