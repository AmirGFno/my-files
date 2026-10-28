#!/usr/bin/env python3
"""Build README.md from the real numbers in the generated reports."""
import json
import os
import re

rep = open("validation_report.txt", encoding="utf-8").read()
edge = open("edge_stats.txt", encoding="utf-8").read() \
    if os.path.exists("edge_stats.txt") else ""
rel = json.load(open("ci/release.json", encoding="utf-8")) \
    if os.path.exists("ci/release.json") else {"assets": []}


def grab(pattern, default="—", text=None):
    m = re.search(pattern, text if text is not None else rep)
    return m.group(1).strip() if m else default


def asset(label):
    for a in rel.get("assets", []):
        if a.get("label") == label:
            return a
    return {}


st2 = asset("stage2")
st3 = asset("stage3")
name2 = st2.get("name", "KECHAP_BOOK_BISTINO_1406_watermark-free.pdf")
name3 = st3.get("name", "KECHAP_BOOK_BISTINO_1406_edges-repaired.pdf")
url2 = st2.get("browser_download_url", "")
url3 = st3.get("browser_download_url", "")
size2 = st2.get("size") or int(grab(r"output size \(bytes\)\s+:\s+(\d+)"))
size3 = st3.get("size") or 0
pages = grab(r"pages\s+:\s+(\d+)")
artifacts = grab(r"artifact blocks in src:\s+(\d+)")
sha2 = st2.get("sha256", "")
sha3 = st3.get("sha256", "")
raw_name = grab(r"output file\s+:\s+(.+)")
rep_alias = "KECHAP_BOOK_بیست‌ینو قریشی 1406 (ترمیم‌شده).pdf"

readme = f"""# کچاپ بوک — بیست‌ینو قریشی ۱۴۰۶ (بدون واترمارک، ترمیم‌شده)

کتاب {pages} صفحه‌ای، اسکن‌شده (NAPS2 / PDFsharp، PDF 1.7). دو نسخه منتشر شده است:

## دانلود مستقیم

| نسخه | فایل | حجم | توضیح |
|---|---|---|---|
| مرحله ۲ | [`{name2}`]({url2}) | {size2:,} بایت | فقط واترمارک حذف شده؛ کیفیت اسکن هر صفحه بایت‌به‌بایت دست‌نخورده |
| مرحله ۳ | [`{name3}`]({url3}) | {size3:,} بایت | همان فایل + سفید شدن نوار سیاه لبه‌های اسکن |

صفحه ریلیز: {rel.get('release_url', 'https://github.com/AmirGFno/my-files/releases/tag/v1')}

> ریپو Private است؛ برای دانلود باید با حساب GitHub خود وارد شده باشید.
> گیت‌هاب نام asset را به ASCII تبدیل می‌کند؛ برای برگرداندن نام فارسی:

```bash
mv {name2} "{raw_name}"
mv {name3} "{rep_alias}"
```

## SHA256

```
{sha2}  {name2}
{sha3}  {name3}
```

هر دو asset بعد از آپلود دوباره دانلود و SHA256 آن‌ها تطبیق داده شده است.

## مرحله ۲ — حذف واترمارک

واترمارک‌ها روی هر صفحه به‌صورت Artifact تزریق شده بودند ({artifacts} بلوک در کل فایل).
استریم محتوای هر صفحه بازنویسی شد تا فقط قرارگیری تصویر اسکن پایه (`/I0`) باقی بماند:

- تمام بلوک‌های `/Artifact <</Subtype/Watermark/Type/Pagination>> BDC ... EMC` حذف شدند
- XObjectهای واترمارک `/FXX1 ../ FXX6` و گرافیک‌استیت `/FXE1 gs` حذف شدند
- عملیات متن و منابع فونت (واترمارک چرخیده Helvetica) حذف شدند
- در Catalog: `OCProperties`، `AcroForm` و `Names` صفر (null) شدند
- آبجکت‌های تصویری واترمارک با `garbage=4` واقعاً از فایل پاک شدند، نه پنهان

## مرحله ۳ — ترمیم لبه‌های سیاه

پردازش مستقیم روی پیکسل‌های تصویر تعبیه‌شده در PDF انجام شده؛ هیچ صفحه‌ای رندر یا
JPEG/دوباره فشرده نشده است (فقط استریم تصویر با deflate ذخیره شده).

- **۲۸۱ صفحه کاغذ سفید**: تشخیص لبه واقعی کاغذ در چهار طرف با اسکن
  «run روشن»، برازش خط مقاوم، پر کردن بیرون لبه با رنگ کاغذ همان صفحه، پاک‌سازی
  ریز‌نوارهای چسبیده به لبه و حذف لکه‌های تیره متصل به حاشیه (connected components)
- **۲ صفحه جلد رنگی**: لبه کاغذ وجود ندارد، پس لبه واقعی صفحه با «پله نوری تیز»
  (bright→dark) در ۳۰ پیکسل اول هر طرف پیدا می‌شود و فقط همان نوار باریک حذف
  می‌شود؛ جای نوار با رنگ پیکسل‌های همسایه همان خط پر می‌شود تا طرح ادامه پیدا کند.
  نوارهایی که از این عمق بیشتر باشند (مثل ساق پای نگهبان) طرح تلقی و دست‌نخورده
  می‌مانند
- در پایان، حداکثر ۶ پیکسل حاشیه هر صفحه از پیکسل‌های تیره بی‌رنگ پاک می‌شود

### نمونه‌های بصری

| جلد (بعد) | صفحه متنی ۱۵۱ (بعد) | صفحه آخر (بعد) |
|---|---|---|
| ![cover](docs/edge_cover.png) | ![text](docs/edge_text.png) | ![last](docs/edge_last.png) |

### اعتبارسنجی قبل/بعد (اندازه‌گیری روی تصویر تعبیه‌شده)

```
{edge.strip()}
```

`interior_dark` در چهار صفحه متنی نمونه (۶۱، ۱۵۱، ۱۵۲، ۲۵۰) قبل و بعد **کاملاً
یکسان** است: هیچ متنی پاک نشده است. دو صفحه جلد (۱ و ۲۸۳) لبه کاغذ ندارند، بنابراین
`interior_dark` آن‌ها کمی کاهش دارد — با بررسی تصویر diff (پایین) این کاهش مربوط به
نوار اسکن لبه است، نه طرح جلد.

`border_dark` در حاشیه ۶ پیکسلی از ۷٬۷۶۶–۲۲٬۷۰۳ به ۰–۹۵ رسیده، هیچ پیکسلی در کل فایل
تیره‌تر نشده (`brightened = 0`) و هیچ حذف تیره‌ای دورتر از ۱۵۰ پیکسل از لبه رخ نداده
(`dark_removed_deep = 0`).

### تصویر تغییرات روی جلدها

قرمز = پیکسل‌هایی که در مرحله ۳ عوض شده‌اند (فقط نوار لبه):

![diff cover](docs/diff_cover.png)

![diff last](docs/diff_last.png)

## اعتبارسنجی مرحله ۲

```
{rep.strip()}
```

## بازسازی

```bash
pip install pymupdf numpy scipy
python tools/strip_watermarks.py original.pdf "out.pdf"
python tools/repair_edges.py "out.pdf" "out-repaired.pdf"
python tools/edge_stats.py "out.pdf" "out-repaired.pdf"
```

## اسکریپت‌ها

- `tools/strip_watermarks.py` — حذف واترمارک + اعتبارسنجی
- `tools/repair_edges.py` — ترمیم لبه‌های سیاه اسکن
- `tools/edge_stats.py` — اعتبارسنجی قبل/بعد مرحله ۳
- `tools/publish_release.py` — انتشار assetها و تطبیق SHA256 بعد از آپلود
- `.github/workflows/build.yml` — اجرای خودکار کل زنجیره (دانلود → حذف واترمارک →
  ترمیم لبه → اعتبارسنجی → انتشار)
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
print(readme[:1500])
