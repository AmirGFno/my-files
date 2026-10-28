#!/usr/bin/env python3
"""Build README.md from the real numbers in validation_report.txt."""
import json
import os
import re

rep = open("validation_report.txt", encoding="utf-8").read()


def grab(pattern, default="—"):
    m = re.search(pattern, rep)
    return m.group(1).strip() if m else default


out_name = grab(r"output file\s+:\s+(.+)")
size_bytes = int(grab(r"output size \(bytes\)\s+:\s+(\d+)"))
size_mib = grab(r"output size \(bytes\).*?\(([\d\.]+) MiB\)")
sha = grab(r"sha256\s+:\s+([0-9a-f]{64})")
pages = grab(r"pages\s+:\s+(\d+)")
artifacts = grab(r"artifact blocks in src:\s+(\d+)")

rel = {}
if os.path.exists("ci/release.json"):
    rel = json.load(open("ci/release.json", encoding="utf-8"))

download_url = rel.get("browser_download_url",
                       "https://github.com/AmirGFno/my-files/releases/download/v1/")
release_url = rel.get("release_url",
                      "https://github.com/AmirGFno/my-files/releases/tag/v1")

readme = f"""# کچاپ بوک — بیست‌ینو قریشی ۱۴۰۶ (بدون واترمارک)

| مشخصه | مقدار |
|---|---|
| نام فایل | `{out_name}` |
| نام asset در Releases | `{rel.get('asset_name', 'KECHAP_BOOK_BISTINO_1406_watermark-free.pdf')}` |
| تعداد صفحات | {pages} |
| حجم | {size_bytes:,} بایت ({size_mib} مگابایت) |
| SHA256 | `{sha}` |
| فرمت | PDF 1.7 اسکن‌شده (NAPS2 / PDFsharp) |

## دانلود

فایل بزرگ‌تر از سقف ۱۰۰ مگابایتی گیت‌هاب است، بنابراین به‌صورت asset ریلیز منتشر شده:

**{download_url}**

صفحه ریلیز: {release_url}

> فایل در یک ریپوی Private است؛ برای دانلود باید با حساب GitHub خود وارد شده باشید.

نام asset در گیت‌هاب ASCII است (گیت‌هاب نام‌های غیرانگلیسی را حذف می‌کند). بعد از دانلود،
برای برگرداندن نام اصلی:

```bash
mv "{rel.get('asset_name', 'KECHAP_BOOK_BISTINO_1406_watermark-free.pdf')}" "{out_name}"
```

## چه کاری انجام شد

واترمارک‌ها روی هر صفحه به‌صورت Artifact تزریق شده بودند ({artifacts} بلوک در کل فایل).
استریم محتوای هر صفحه بازنویسی شد تا فقط قرارگیری تصویر اسکن پایه (`/I0`) باقی بماند:

- تمام بلوک‌های `/Artifact <</Subtype/Watermark/Type/Pagination>> BDC ... EMC` حذف شدند
- XObjectهای واترمارک `/FXX1 ../ FXX6` و گرافیک‌استیت `/FXE1 gs` حذف شدند
- عملیات متن و منابع فونت (واترمارک چرخیده Helvetica) حذف شدند
- در Catalog: `OCProperties`، `AcroForm` و `Names` صفر (null) شدند
- آبجکت‌های تصویری واقعی واترمارک با `garbage=4` از فایل پاک شدند، نه پنهان

کیفیت اسکن هیچ صفحه‌ای تغییر نکرده: بایت‌های تصویر پایه هر ۲۸۳ صفحه با فایل مبدأ
مو‌به‌مو یکسان است (بدون رندر یا فشرده‌سازی مجدد).

## اعتبارسنجی

{rep.strip()}

## بازسازی روی فایل مبدأ

```bash
pip install pymupdf
python tools/strip_watermarks.py original.pdf "out.pdf"
```

## اسکریپت‌ها

- `tools/strip_watermarks.py` — حذف واترمارک + اعتبارسنجی کامل
- `tools/publish_release.py` — انتشار asset ریلیز و تطبیق SHA256 بعد از آپلود
- `.github/workflows/build.yml` — اجرای خودکار کل زنجیره (دانلود → پردازش → انتشار)
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
print(readme)
