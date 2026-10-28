# کچاپ بوک — بیست‌ینو قریشی ۱۴۰۶ (بدون واترمارک)

| مشخصه | مقدار |
|---|---|
| نام فایل | `KECHAP_BOOK_بیست‌ینو قریشی 1406 (بدون واترمارک).pdf` |
| نام asset در Releases | `KECHAP_BOOK_BISTINO_1406_watermark-free.pdf` |
| تعداد صفحات | 283 |
| حجم | 152,515,517 بایت (145.45 مگابایت) |
| SHA256 | `c8417d612a1d473d2f3bdcdcff6a54370084987b4eb94ef122367389139a1445` |
| فرمت | PDF 1.7 اسکن‌شده (NAPS2 / PDFsharp) |

## دانلود

فایل بزرگ‌تر از سقف ۱۰۰ مگابایتی گیت‌هاب است، بنابراین به‌صورت asset ریلیز منتشر شده:

**https://github.com/AmirGFno/my-files/releases/download/v1/**

صفحه ریلیز: https://github.com/AmirGFno/my-files/releases/tag/v1

> فایل در یک ریپوی Private است؛ برای دانلود باید با حساب GitHub خود وارد شده باشید.

نام asset در گیت‌هاب ASCII است (گیت‌هاب نام‌های غیرانگلیسی را حذف می‌کند). بعد از دانلود،
برای برگرداندن نام اصلی:

```bash
mv "KECHAP_BOOK_BISTINO_1406_watermark-free.pdf" "KECHAP_BOOK_بیست‌ینو قریشی 1406 (بدون واترمارک).pdf"
```

## چه کاری انجام شد

واترمارک‌ها روی هر صفحه به‌صورت Artifact تزریق شده بودند (1698 بلوک در کل فایل).
استریم محتوای هر صفحه بازنویسی شد تا فقط قرارگیری تصویر اسکن پایه (`/I0`) باقی بماند:

- تمام بلوک‌های `/Artifact <</Subtype/Watermark/Type/Pagination>> BDC ... EMC` حذف شدند
- XObjectهای واترمارک `/FXX1 ../ FXX6` و گرافیک‌استیت `/FXE1 gs` حذف شدند
- عملیات متن و منابع فونت (واترمارک چرخیده Helvetica) حذف شدند
- در Catalog: `OCProperties`، `AcroForm` و `Names` صفر (null) شدند
- آبجکت‌های تصویری واقعی واترمارک با `garbage=4` از فایل پاک شدند، نه پنهان

کیفیت اسکن هیچ صفحه‌ای تغییر نکرده: بایت‌های تصویر پایه هر ۲۸۳ صفحه با فایل مبدأ
مو‌به‌مو یکسان است (بدون رندر یا فشرده‌سازی مجدد).

## اعتبارسنجی

VALIDATION REPORT
=================
source file           : original.pdf
output file           : KECHAP_BOOK_بیست‌ینو قریشی 1406 (بدون واترمارک).pdf
source size (bytes)   : 152718885
output size (bytes)   : 152515517  (145.45 MiB)
sha256                : c8417d612a1d473d2f3bdcdcff6a54370084987b4eb94ef122367389139a1445

pages                 : 283 (expected 283)
artifact blocks in src: 1698
BDC blocks left       : 0   (must be 0)
/FXX|/FXE refs left   : 0   (must be 0)
text operators left   : 0   (must be 0)
/Font refs in content : 0   (must be 0)
font objects in file  : 0   (must be 0)
watermark xobj names  : 0   (must be 0)
image objects in file : 283   (expected 283)
pages w/ pure content : 283/283
scan pixels identical : 283/283

catalog keys after cleanup:
  OCProperties -> ('null', 'null')
  AcroForm     -> ('null', 'null')
  Names        -> ('null', 'null')

RESULT: PASS

## بازسازی روی فایل مبدأ

```bash
pip install pymupdf
python tools/strip_watermarks.py original.pdf "out.pdf"
```

## اسکریپت‌ها

- `tools/strip_watermarks.py` — حذف واترمارک + اعتبارسنجی کامل
- `tools/publish_release.py` — انتشار asset ریلیز و تطبیق SHA256 بعد از آپلود
- `.github/workflows/build.yml` — اجرای خودکار کل زنجیره (دانلود → پردازش → انتشار)
