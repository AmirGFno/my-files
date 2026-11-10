# تصویرهای تاریخی فصل ۱ — وضعیتِ نهایی

هر سه تصویر تاریخی فصل موجود و در متن جای‌گذاری شده‌اند:

| شناسه | فایل | جای واقعیِ فایل |
| --- | --- | --- |
| H01 | `H01_CH01_antikythera-mechanism.jpg` | `book/images/historical/` (روی `origin/main`) |
| H46 | `H46_CH01_prague-orloj-dial.jpg` | `book/images/historical/` (روی `origin/main`) |
| H45 | `H45_CH01_dunhuang-star-chart.png` | همین پوشه — **ارسالیِ کاربر** |

## دربارهٔ H45

پنلِ قطبِ شمالیِ **اطلسِ ستارگانِ دونهوانگ**؛ طومارِ کاغذِ توت از سدهٔ هفتمِ میلادی، بازیافته از غارِ کتابخانه (غارِ ۱۷) در موگائو، اکنون در کتابخانهٔ بریتانیا با شمارهٔ `Or.8210/S.3326`. رقومی‌سازیِ کتابخانهٔ بریتانیا با نشانِ Public Domain معرفی شده است.

**ابعاد فایلِ ارسالی ۲۲۴×۲۲۵ پیکسل است.** در اندازهٔ شناورِ ۴۸ میلی‌متری که در فصل استفاده شده قابل قبول است، اما برای چاپِ نهایی باید نسخهٔ پرجزئیات از کتابخانهٔ بریتانیا / پروژهٔ بین‌المللی دونهوانگ جایگزین شود. فایل دست‌نخورده نگه داشته شده و بزرگ‌نمایی نشده است.

## نکته

H01 و H46 روی شاخهٔ `main` هستند و عمداً روی این شاخه دوباره کامیت نشده‌اند. برای ساختِ خروجی، اگر روی دیسک نبودند:

```bash
git fetch origin main
git show origin/main:book/images/historical/H01_CH01_antikythera-mechanism.jpg > book/images/historical/H01_CH01_antikythera-mechanism.jpg
git show origin/main:book/images/historical/H46_CH01_prague-orloj-dial.jpg  > book/images/historical/H46_CH01_prague-orloj-dial.jpg
```

در نسخهٔ فعلیِ فصل، **هیچ زیرنویسی زیر این تصویرها چاپ نمی‌شود**؛ اطلاعات ضروری داخل دیالوگِ راهنما آمده و اعتبارات در `../../build/image-credits.md` است.
