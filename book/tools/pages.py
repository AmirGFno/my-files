"""The sample pages, rebuilt around a single educational pattern.

The reading experience we are designing for:

    هر فصل یک روش است  →  هر روش چند «گام» دارد  →  هر گام همین یک قالب را دارد:
    ۱ هدف  ۲ چرا این‌جوری  ۳ قدم‌ها  ۴ الگوریتم  ۵ خطا  ۶ جایگزین‌ها

The reader must always be able to answer three questions without thinking:
    کجای کتابم؟ چه کاری باید بکنم؟ اگر گیر کردم کجا بروم؟
"""
from __future__ import annotations

import math
import os
from typing import List, Sequence, Tuple

from cube3d import Cube
from design import (ACCENT, ACCENT_SOFT, CONTENT_W, INK, INK_FAINT, INK_SOFT, LEVEL, LEVEL_FA,
                    LEVEL_SOFT, MARGIN_BOT, MARGIN_IN, MARGIN_OUT, MARGIN_TOP, NAVY, PAGE, RULE,
                    TEAL, Doc, _fa_digits)
import render
import typo
from scenes import cross_ok, daisy_ok, scene

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
TOP = PAGE[1] - MARGIN_TOP - 30


# ==================================================================== primitives
def frame(widths: Sequence[float], gap: float = 24) -> List[Tuple[float, float]]:
    """RTL columns: [(left_x, width), ...] — first entry is the RIGHT-hand column."""
    out, right = [], MARGIN_IN + CONTENT_W
    for w in widths:
        out.append((right - w, w))
        right -= w + gap
    return out


def pill(c, x_right, y, text, fg, bg, size=7.0, weight="medium"):
    w = typo.text_width(typo.visual(text), typo.font(weight), size) + 13
    h = size + 7
    c.setFillColorRGB(*bg)
    c.roundRect(x_right - w, y - 2.5, w, h, h / 2, stroke=0, fill=1)
    typo.draw_paragraph(c, x_right - w, y + 1.2, text, w, size, weight=weight,
                        align="center", color=fg)
    return w


def eyebrow(d, x, y, text, width=None, color=None):
    return typo.draw_paragraph(d.c, x, y, text, width or CONTENT_W, 8.6, weight="semibold",
                               align="right", color=color or ACCENT)


def h2(d, x, y, text, width=None, size=15):
    return typo.draw_paragraph(d.c, x, y, text, width or CONTENT_W, size, weight="bold",
                               leading=1.5, color=INK)


def lead(d, x, y, text, width=None, size=10):
    return typo.draw_paragraph(d.c, x, y, text, width or CONTENT_W, size, weight="regular",
                               leading=2.0, color=INK_SOFT)


def rule(c, x, y, width, color=None):
    c.setStrokeColorRGB(*(color or RULE))
    c.setLineWidth(0.6)
    c.line(x, y, x + width, y)


def section_label(c, x_right, y, n, text, width, color=None):
    """Section heading: accent tick + number at the RIGHT edge, title flowing left."""
    col = color or ACCENT
    c.setFillColorRGB(*col)
    c.rect(x_right - 3, y - 1.5, 3, 12, stroke=0, fill=1)
    label = text
    if n:
        label = "بخش " + n + " · " + text
    typo.draw_paragraph(c, x_right - width + 10, y, label, width - 14, 8.6,
                        weight="semibold", align="right", color=col)
    return y - 16


def algorithm_row(d, x, y, width, alg, title, height=36, color=None):
    c = d.c
    c.setFillColorRGB(0.966, 0.969, 0.976)
    c.roundRect(x, y - height, width, height, 5, stroke=0, fill=1)
    c.setFillColorRGB(*(color or NAVY))
    c.roundRect(x + width - 3.2, y - height, 3.2, height, 1.5, stroke=0, fill=1)
    aw = typo.latin_width(alg, 10.2)
    label_x = x + 12 + aw + 10
    label_w = x + width - 12 - label_x
    if label_w > 28:
        typo.draw_paragraph(c, label_x, y - height + 13.5, title, label_w, 8.0,
                            weight="regular", align="right", color=INK_SOFT)
    d.alg(x + 12, y - height + 14, alg, size=10.2, color=color or NAVY)
    return y - height - 5


def callout(d, x, y, width, title, text, kind="why", size=9.2):
    c = d.c
    palette = {
        "why": ((0.93, 0.96, 0.99), (0.13, 0.36, 0.66), "چرا این‌جوری؟"),
        "warn": ((0.99, 0.94, 0.92), (0.74, 0.24, 0.15), "اگر گیر کردی"),
        "note": ((0.94, 0.97, 0.94), (0.10, 0.45, 0.30), "نکته"),
    }
    bg, fg, default_title = palette.get(kind, palette["why"])
    inner = width - 26
    lines = typo.wrap_paragraph(text, inner, size)
    height = 18 + 15 + len(lines) * size * 1.85 + 10
    c.setFillColorRGB(*bg)
    c.roundRect(x, y - height, width, height, 6, stroke=0, fill=1)
    c.setFillColorRGB(*fg)
    c.roundRect(x + width - 3, y - height, 3, height, 1.5, stroke=0, fill=1)
    typo.draw_paragraph(c, x + 12, y - 19, title or default_title, inner, size,
                        weight="bold", align="right", color=fg)
    typo.draw_paragraph(c, x + 12, y - 19 - 15, text, inner, size, weight="regular",
                        align="right", color=(0.22, 0.24, 0.28), leading=1.85)
    return y - height - 10


def data_table(d, x, y, width, rows, colw, size=8.2, rh=20, highlight_row=None):
    c = d.c
    for ri, row in enumerate(rows):
        ry = y - ri * rh
        if ri == 0:
            c.setFillColorRGB(*NAVY)
            c.roundRect(x, ry - 6, width, rh, 4, stroke=0, fill=1)
            colr, wt = (1, 1, 1), "medium"
        else:
            c.setFillColorRGB(*((0.99, 0.96, 0.90) if ri == highlight_row else
                                ((0.973, 0.975, 0.981) if ri % 2 == 0 else (1, 1, 1))))
            c.rect(x, ry - 6, width, rh, stroke=0, fill=1)
            colr, wt = (INK if ri == highlight_row else INK_SOFT), (
                "medium" if ri == highlight_row else "regular")
        cx = x + width
        for ci, txt in enumerate(row):
            w = width * colw[ci]
            if ci == 0:
                typo.draw_paragraph(c, cx - w, ry, txt, w - 6, size, weight=wt,
                                    align="right", color=colr)
            elif typo.numerals(txt) == txt or all(ch in "0123456789۰۱۲۳۴۵۶۷۸۹٪%.,–- " for ch in txt):
                typo.draw_numerals(c, cx - 3, ry, txt, size, weight=wt, align="right",
                                   color=colr)
            else:
                typo.draw_paragraph(c, cx - w, ry, txt, w - 6, size, weight=wt,
                                    align="center", color=colr)
            cx -= w
    return y - len(rows) * rh - 6


# ------------------------------------------------------------------ navigation
def step_progress(d, x_right, y, total, current, width=None, color=None):
    """The 'where am I' widget: numbered dots, current one filled."""
    c = d.c
    col = color or LEVEL["beginner"]
    width = width or CONTENT_W
    gap = width / total
    for i in range(total):
        n = i + 1
        cx = x_right - gap * i - gap / 2
        done = n < current
        cur = n == current
        if cur:
            c.setFillColorRGB(*col)
            c.circle(cx, y, 9.5, stroke=0, fill=1)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(typo.font("bold"), 8.6)
            c.drawCentredString(cx, y - 3, _fa_digits(str(n)))
        elif done:
            c.setFillColorRGB(*LEVEL_SOFT.get("beginner", ACCENT_SOFT))
            c.circle(cx, y, 8.5, stroke=0, fill=1)
            c.setFillColorRGB(*col)
            c.setFont(typo.font("medium"), 8)
            c.drawCentredString(cx, y - 2.8, _fa_digits(str(n)))
        else:
            c.setStrokeColorRGB(*RULE)
            c.setLineWidth(0.9)
            c.circle(cx, y, 8.5, stroke=1, fill=0)
            c.setFillColorRGB(*INK_FAINT)
            c.setFont(typo.font("regular"), 8)
            c.drawCentredString(cx, y - 2.8, _fa_digits(str(n)))
        if i < total - 1:
            c.setStrokeColorRGB(*(col if done else RULE))
            c.setLineWidth(1.2 if done else 0.7)
            c.line(cx - 12, y, cx - gap + 12, y)
    return y - 26


# ==================================================================== page 1
def page_map(d: Doc):
    """«از کجا شروع کنم؟» - the one page a confused beginner needs."""
    c = d.new_page(running="نقشه کتاب", chapter="جلد اول · مکعب ۳×۳")

    y = TOP
    eyebrow(d, MARGIN_IN, y, "راهنمای خواندن · یک صفحه")
    y = h2(d, MARGIN_IN, y - 24, "از کجا شروع کنم؟", size=26)
    y = lead(d, MARGIN_IN, y - 4,
             "این کتاب چهار مسیر دارد. مسیرها را قاطی نکن: اول تازه‌کار شو، بعد مسیر خودت را انتخاب کن. "
             "برای مسیر سبز فقط سه فصل لازم است.", CONTENT_W * 0.72) - 22

    # ---------------- the three-track ladder
    tracks = [
        ("مسیر سبز", "تازه‌کار", "beginner", "فصل ۲", "لایه‌به‌لایه",
         "تنها مسیری که بدون هیچ پیش‌زمینه‌ای تا حل کامل می‌برد.", "۶ الگوریتم", "۸۰ صفحه"),
        ("مسیر آبی", "میانی", "mid", "فصل ۳ و ۴", "پتروس یا ZZ",
         "وقتی زیر ۹۰ ثانیه می‌زنی، یکی از این دو را انتخاب کن.", "۴۰ تا ۵۰ الگوریتم", "۱۲۰ صفحه"),
        ("مسیر بنفش", "حرفه‌ای", "pro", "فصل ۵", "CFOP",
         "بدون حد وسط: ۱۱۹ الگوریتم، سقف سرعت.", "۱۱۹ الگوریتم", "۱۴۰ صفحه"),
    ]
    gap = 12
    n = 3
    cw = (CONTENT_W - gap * (n - 1)) / n
    card_h = 184
    for i, (name, level, lvl, chap, method, desc, algs, pages) in enumerate(tracks):
        xr = MARGIN_IN + CONTENT_W - i * (cw + gap)
        x = xr - cw
        c.setFillColorRGB(*LEVEL_SOFT[lvl])
        c.roundRect(x, y - card_h, cw, card_h, 8, stroke=0, fill=1)
        # header strip
        c.setFillColorRGB(*LEVEL[lvl])
        c.roundRect(x, y - 26, cw, 26, 8, stroke=0, fill=1)
        c.rect(x, y - 26, cw, 12, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 10, y - 17, name, cw - 20, 9.6, weight="bold",
                            align="right", color=(1, 1, 1))
        typo.draw_paragraph(c, x + 10, y - 17, level, cw - 20, 8.2, weight="regular",
                            align="left", color=(1, 1, 1))
        yy = y - 44
        typo.draw_paragraph(c, x + 10, yy, "از " + chap, cw - 20, 8.2, align="right",
                            color=INK_FAINT)
        yy = typo.draw_paragraph(c, x + 10, yy - 15, method, cw - 20, 14, weight="bold",
                                 align="right", color=INK)
        yy = typo.draw_paragraph(c, x + 10, yy - 2, desc, cw - 20, 8.4, align="right",
                                 color=INK_SOFT, leading=1.9)
        # footer: algorithms on one line, page count on the next
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(x + 8, y - card_h + 8, cw - 16, 40, 5, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 14, y - card_h + 32, algs, cw - 28, 8.2, weight="medium",
                            align="right", color=LEVEL[lvl])
        typo.draw_paragraph(c, x + 14, y - card_h + 18, pages, cw - 28, 7.8, align="right",
                            color=INK_FAINT)

    y -= card_h + 26

    # ---------------- «this is how every step page looks»
    right, left = frame([CONTENT_W * 0.60 - 24, CONTENT_W * 0.40])
    rx, rw = right
    y0 = y
    y = section_label(c, rx + rw, y, "۱.۲", "هر صفحه‌ی گام، همین شش بخش را دارد", rw)
    blocks = [
        ("هدف گام", "یک جمله: در پایان این صفحه چه چیزی حل شده است."),
        ("چرا این‌جوری", "منطق پشت روش، بدون فرمول."),
        ("قدم‌ها", "شماره‌دار، هر قدم یک کار."),
        ("الگوریتم", "حرکت‌ها به‌صورت لاتین و جدا از متن."),
        ("اگر گیر کردی", "خطاهای رایج و راه خروج."),
        ("جایگزین‌ها", "تکنیک‌های دیگر همین گام + شماره صفحه."),
    ]
    for i, (t, s) in enumerate(blocks, 1):
        c.setFillColorRGB(*ACCENT_SOFT)
        c.circle(rx + rw - 6, y + 2, 5.5, stroke=0, fill=1)
        c.setFillColorRGB(*ACCENT)
        c.setFont(typo.font("bold"), 7)
        c.drawCentredString(rx + rw - 6, y - 0.4, _fa_digits(str(i)))
        typo.draw_paragraph(c, rx, y, t, rw - 18, 9.2, weight="bold", align="right", color=INK)
        y = typo.draw_paragraph(c, rx, y - 12, s, rw - 18, 8.2, align="right",
                                color=INK_FAINT, leading=1.75) - 7

    # left visual: the reading path, as a vertical spine
    lx, lw = left
    my = y0 - 4
    card_h = 196
    c.setFillColorRGB(0.975, 0.977, 0.982)
    c.roundRect(lx, my - card_h, lw, card_h, 8, stroke=0, fill=1)
    typo.draw_paragraph(c, lx + 12, my - 22, "مسیر خواندن", lw - 24, 9.4, weight="bold",
                        align="right", color=INK)
    path = [
        ("مکعب را بشناس", "قطعه‌ها، نت‌نویسی", "ص ۸", LEVEL["beginner"]),
        ("یک روش را کامل کن", "لایه‌به‌لایه، بدون پرش", "فصل ۲", LEVEL["beginner"]),
        ("جایگزین‌ها را مقایسه کن", "کارگاه پایان فصل", "ص ۸۰", LEVEL["mid"]),
        ("سرعت را بالا ببر", "روش دوم یا CFOP", "فصل ۳–۵", LEVEL["pro"]),
    ]
    step_y = my - 44
    spine_x = lx + lw - 20
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(1.2)
    c.line(spine_x, step_y + 6, spine_x, step_y - 3 * 38 - 4)
    for i, (t, s_, pg, col) in enumerate(path):
        yy = step_y - i * 38
        c.setFillColorRGB(*col)
        c.circle(spine_x, yy, 8, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(typo.font("bold"), 7.6)
        c.drawCentredString(spine_x, yy - 2.8, _fa_digits(str(i + 1)))
        typo.draw_paragraph(c, lx + 74, yy + 3, t, lw - 122, 8.8, weight="medium",
                            align="right", color=INK)
        typo.draw_paragraph(c, lx + 74, yy - 9, s_, lw - 122, 7.6, align="right",
                            color=INK_FAINT)
        typo.draw_numerals(c, lx + 14, yy - 2, pg, 7.6, weight="medium", align="left",
                           color=col)

    y2 = min(y, my - card_h) - 22

    # ---------------- the reading rule
    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y2 - 46, CONTENT_W, 46, 7, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 18, y2 - 19,
                        "قانون طلایی: تا وقتی یک روش را کامل یاد نگرفته‌ای، سراغ روش بعدی نرو.",
                        CONTENT_W - 36, 10, weight="medium", align="right", color=(1, 1, 1))
    typo.draw_paragraph(c, MARGIN_IN + 18, y2 - 35,
                        "بخش «جایگزین‌ها» برای بعد است؛ اول مسیر اصلی را تا پایان برو.",
                        CONTENT_W - 36, 8.6, align="right", color=(0.72, 0.78, 0.88))
    return d


# ==================================================================== page 2
def page_step(d: Doc):
    """One step page, with a fixed six-part pattern and a clear 'you are here'."""
    c = d.new_page(running="فصل ۲ · گام ۳ از ۷", chapter="لایه‌به‌لایه")

    y = TOP - 4
    # ---------------- header: where you are in the method (7 steps)
    typo.draw_paragraph(c, MARGIN_IN, y, "کجای روش هستی؟ گام ۳ از ۷", CONTENT_W, 8.4,
                        weight="medium", align="right", color=LEVEL["beginner"])
    y -= 22
    step_progress(d, MARGIN_IN + CONTENT_W, y, 7, 3)
    y -= 26

    # ---------------- 1. goal
    y = section_label(c, MARGIN_IN + CONTENT_W, y, "۱", "هدف این گام", CONTENT_W,
                      color=LEVEL["beginner"])
    y = h2(d, MARGIN_IN, y, "صلیب سفید را از «دیزی» بساز", size=20)
    y = lead(d, MARGIN_IN, y - 2,
             "در پایان این صفحه: چهار لبه‌ی سفید در لایه‌ی پایین، هر کدام بالای مرکز هم‌رنگ خودش.",
             CONTENT_W * 0.78) - 4

    # three states in one row: هدف | شروع | پایان
    y -= 14
    fig_h = 104
    gap = 12
    cw = (CONTENT_W - gap * 2) / 3
    figs = [("۱. شروع", scene(""), "default", "۱"),
            ("۲. دیزی", scene("R2 L2 F2 B2"), "top", "۲"),
            ("۳. صلیب کامل", scene("F2 L2 B2 R2"), "bottom", "۳")]
    for i, (cap, cube, view, tag) in enumerate(figs):
        xr = MARGIN_IN + CONTENT_W - i * (cw + gap)
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(xr - cw, y - fig_h - 8, cw, fig_h + 14, 7, stroke=0, fill=1)
        render.draw_cube(c, xr - cw + 6, y - fig_h, cw - 12, cube, view=view, shadow=False)
        typo.draw_paragraph(c, xr - cw, y - fig_h - 22, cap, cw, 7.8, align="center",
                            color=INK_FAINT)
        if i < 2:
            axx = xr - cw - gap / 2
            c.setStrokeColorRGB(*INK_FAINT)
            c.setLineWidth(0.9)
            c.line(axx + 4, y - fig_h / 2 - 4, axx - 4, y - fig_h / 2 - 4)
            c.setFillColorRGB(*INK_FAINT)
            pp = c.beginPath()
            pp.moveTo(axx - 7, y - fig_h / 2 - 4)
            pp.lineTo(axx - 1.5, y - fig_h / 2 - 1.6)
            pp.lineTo(axx - 1.5, y - fig_h / 2 - 6.4)
            pp.close()
            c.drawPath(pp, stroke=0, fill=1)

    # one quiet caption line instead of a noisy legend
    typo.draw_paragraph(c, MARGIN_IN, y - fig_h - 34,
                        "سه لحظه از همین گام؛ هر سه از یک مکعب شبیه‌سازی‌شده ساخته شده‌اند.",
                        CONTENT_W, 7.6, align="right", color=INK_FAINT)

    y -= fig_h + 50

    # ---------------- 2 + 3: why, then the steps
    right, left = frame([CONTENT_W * 0.56 - 24, CONTENT_W * 0.44])
    rx, rw = right
    lx, lw = left

    yright = y
    yright = section_label(c, rx + rw, yright, "۲", "چرا این‌جوری؟", rw)
    yright = typo.draw_paragraph(
        c, rx, yright + 4,
        "لبه‌ی سفید یک قطعه با دو رنگ است. تا وقتی رنگ دوم با مرکز هم‌رنگش یکی نشود، لبه در جای "
        "درست نیست — حتی اگر سفیدش رو به پایین باشد. دیزی این تطبیق را در لایه‌ی بالا و در دید "
        "کامل انجام می‌دهد؛ برای همین برای مبتدی از صلیب مستقیم امن‌تر است.",
        rw, 9.2, align="right", color=INK_SOFT, leading=1.95) - 14
    yright = section_label(c, rx + rw, yright, "۳", "قدم‌ها", rw)
    steps = [
        ("چهار لبه‌ی سفید را بالا بیاور", "سفیدها دور مرکز زرد، رو به بالا."),
        ("رنگ کنار لبه را با مرکز بسنج", "سبز روی مرکز سبز، قرمز روی قرمز."),
        ("لبه را پایین بیاور", "همان وجه را دو حرکت بچرخان."),
        ("هر چهار لبه را تکرار کن", "ترتیب مهم نیست؛ هر لبه مستقل است."),
    ]
    for i, (t, s) in enumerate(steps, 1):
        c.setFillColorRGB(*LEVEL["beginner"])
        c.circle(rx + rw - 6.5, yright + 2, 6, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(typo.font("bold"), 7.4)
        c.drawCentredString(rx + rw - 6.5, yright - 0.2, _fa_digits(str(i)))
        typo.draw_paragraph(c, rx, yright, t, rw - 20, 9.2, weight="medium", align="right",
                            color=INK)
        yright = typo.draw_paragraph(c, rx, yright - 12.5, s, rw - 20, 8.2, align="right",
                                     color=INK_FAINT, leading=1.7) - 7

    # left column: algorithms + mistakes
    yleft = y - 2
    yleft = section_label(c, lx + lw, yleft, "۴", "الگوریتم‌های این گام", lw)
    for alg, title in (("F R U R' U' F'", "صلیب زرد"),
                       ("F2 R2", "دیزی در دو حرکت"),
                       ("D2", "برگرداندن دیزی")):
        yleft = algorithm_row(d, lx, yleft, lw, alg, title)
    yleft -= 6
    yleft = section_label(c, lx + lw, yleft, "۵", "اگر گیر کردی", lw, color=(0.74, 0.24, 0.15))
    d.callout(lx, yleft + 4, lw, "دو خطای رایج",
              "۱) لبه‌ی سفید رو به بالا مانده: آن را با یک حرکت پایین بیاور و از نو تطبیق بده.  "
              "۲) دیزی کامل است ولی صلیب کج است: مکعب را با لایه‌ی زرد به بالا بچرخان و هر لبه را "
              "جداگانه پایین بیاور.", kind="warn")

    # ---------------- 6. alternatives (the cross-reference block)
    ya = min(yright, yleft - 86) - 8
    ya = section_label(c, MARGIN_IN + CONTENT_W, ya, "۶", "جایگزین‌های همین گام", CONTENT_W,
                       color=ACCENT)
    ya = typo.draw_paragraph(c, MARGIN_IN, ya - 2,
                             "همین گام را سه تکنیک دیگر هم می‌شود زد؛ توضیح کامل هر کدام در صفحه‌ی "
                             "مشخص‌شده است.", CONTENT_W * 0.8, 8.4, align="right",
                             color=INK_FAINT) - 12
    ya = data_table(d, MARGIN_IN, ya, CONTENT_W,
               [("تکنیک", "حرکت", "سختی", "مناسب برای", "توضیح کامل"),
                ("دیزی (همین فصل)", "۱۲–۱۶", "۱ از ۵", "مبتدی مطلق", "همین صفحه"),
                ("صلیب مستقیم", "۶–۱۰", "۳ از ۵", "با دید فضایی", "ص ۴۴"),
                ("صلیب کور", "۸", "۵ از ۵", "زیر ۳۰ ثانیه", "ص ۵۲")],
               colw=[0.30, 0.14, 0.14, 0.24, 0.18], highlight_row=1, rh=19)

    # ---------------- next-step chip: never leave the reader without a next move
    ny = ya - 14
    c.setFillColorRGB(0.972, 0.974, 0.98)
    c.roundRect(MARGIN_IN, ny - 34, CONTENT_W, 34, 6, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 14, ny - 21,
                        "تمام شد؟ گام بعدی: چهار گوشه‌ی سفید را جا بینداز", CONTENT_W - 120,
                        9.2, weight="medium", align="right", color=INK)
    typo.draw_latin(c, MARGIN_IN + CONTENT_W - 16, ny - 21, "ص ۳۸", 8.6, weight="semibold",
                    align="right", color=ACCENT, tracking=0.4)
    return d


# ==================================================================== page 3
def page_workshop(d: Doc):
    """The alternatives workshop: one row per step, self-explaining columns."""
    c = d.new_page(running="کارگاه جایگزین‌ها", chapter="لایه‌به‌لایه · پایان فصل ۲")

    y = TOP
    y = section_label(c, MARGIN_IN + CONTENT_W, y, "۲.۹", "پایان فصل ۲", CONTENT_W)
    y = h2(d, MARGIN_IN, y - 2, "کارگاه روش‌های جایگزین", size=22)
    y = lead(d, MARGIN_IN, y - 2,
             "در فصل ۲ برای هر گام یک روش یاد گرفتی. اینجا همان گام‌ها را با تکنیک‌های دیگر مقایسه "
             "می‌کنی. هر ردیف یک گام است؛ از راست به چپ بخوان.", CONTENT_W * 0.82) - 16

    rows = [
        ("گام ۳ · صلیب سفید", "beginner", [
            ("دیزی", "بدون نیاز به دیدن لبه‌های پایین", "۱۲–۱۶", "۳۶", True),
            ("صلیب مستقیم", "حرکت کمتر، نیاز به دید فضایی", "۶–۱۰", "۴۴", False),
            ("صلیب کور", "پایه‌ی سرعت در CFOP", "۸", "۵۲", False),
        ]),
        ("گام ۵ · لبه‌های لایه دوم", "mid", [
            ("درج از راست", "الگوریتم کوتاه و قابل تکرار", "۸", "۶۸", True),
            ("درج آینه‌ای از چپ", "بدون چرخش مکعب", "۸", "۷۰", False),
            ("Keyhole", "سریع‌تر برای چند لبه پشت سر هم", "۴–۶", "۷۴", False),
        ]),
        ("گام ۷ · جای لبه‌های زرد", "pro", [
            ("U-Perm", "الگوریتم پایه، همیشه کار می‌کند", "۹", "۱۰۲", True),
            ("U-Perm ام‌محور", "برای زیر ۴۰ ثانیه", "۹", "۱۰۶", False),
            ("EPLL کامل", "بدون تکرار، تشخیص سخت‌تر", "۴", "۱۴۰", False),
        ]),
    ]

    # column geometry, right to left: [badge][technique][why][moves][page]
    badge_w, tech_w, why_w, move_w, page_w = 52, 108, 168, 56, 56
    x_right = MARGIN_IN + CONTENT_W

    def col_positions():
        x = x_right
        pos = []
        for w in (badge_w, tech_w, why_w, move_w, page_w):
            pos.append((x - w, w))
            x -= w
        return pos

    # ---------------- column header
    hdr = ["", "تکنیک", "چرا بهتر است", "حرکت", "توضیح کامل"]
    xs = col_positions()
    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y - 20, CONTENT_W, 20, 4, stroke=0, fill=1)
    for (cx, w), label in zip(xs, hdr):
        if label:
            typo.draw_paragraph(c, cx, y - 14, label, w - 4, 7.8, weight="medium",
                                align="right" if w > 60 else "center", color=(1, 1, 1))
    y -= 30

    for title, lvl, items in rows:
        c.setFillColorRGB(*LEVEL_SOFT[lvl])
        c.roundRect(MARGIN_IN, y - 22, CONTENT_W, 22, 5, stroke=0, fill=1)
        c.setFillColorRGB(*LEVEL[lvl])
        c.roundRect(MARGIN_IN + CONTENT_W - 3.2, y - 22, 3.2, 22, 1.5, stroke=0, fill=1)
        typo.draw_paragraph(c, MARGIN_IN + 12, y - 15.5, title, CONTENT_W - 24, 9.2,
                            weight="bold", align="right", color=LEVEL[lvl])
        y -= 30
        for name, why, moves, page, recommended in items:
            bx, bw = xs[0]
            tx, tw = xs[1]
            wx, ww = xs[2]
            mx, mw = xs[3]
            px, pw = xs[4]
            if recommended:
                pill(c, bx + bw, y + 1, "پیشنهادی", ACCENT, ACCENT_SOFT, size=6.4)
            typo.draw_paragraph(c, tx, y, name, tw - 6, 9.0,
                                weight="bold" if recommended else "medium",
                                align="right", color=INK)
            typo.draw_paragraph(c, wx, y + 0.6, why, ww - 10, 7.8, align="right",
                                color=INK_FAINT)
            typo.draw_numerals(c, mx + mw - 6, y + 0.6, moves, 8.0, weight="regular",
                               align="right", color=INK_SOFT)
            typo.draw_numerals(c, px + pw - 6, y + 0.6, "ص " + page, 8.2, weight="medium",
                               align="right", color=ACCENT)
            y -= 22
            rule(c, MARGIN_IN, y + 6, CONTENT_W)
        y -= 12

    # ---------------- how cross-references behave
    y = section_label(c, MARGIN_IN + CONTENT_W, y - 2, "", "این شماره‌ها چه کاری می‌کنند",
                      CONTENT_W, color=NAVY)
    y = typo.draw_paragraph(
        c, MARGIN_IN, y + 2,
        "هر شماره، صفحه‌ای است که آن تکنیک در آن کامل توضیح داده شده: از چیستی، تا قدم‌ها، "
        "الگوریتم‌ها و خطاهایش. در نسخه‌ی وب، همین شماره یک لینک می‌شود.", CONTENT_W * 0.8,
        8.6, align="right", color=INK_SOFT, leading=1.9) - 12

    chain = [("ص ۳۶", "تکنیک پایه", LEVEL["beginner"]),
             ("ص ۴۴", "جایگزین میانی", LEVEL["mid"]),
             ("ص ۵۲", "نسخه‌ی حرفه‌ای", LEVEL["pro"])]
    arw = 26
    ccw = (CONTENT_W - 2 * arw) / 3
    for i, (pg, label, col) in enumerate(chain):
        cxr = MARGIN_IN + CONTENT_W - i * (ccw + arw)
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(cxr - ccw, y - 32, ccw, 32, 5, stroke=0, fill=1)
        c.setFillColorRGB(*col)
        c.roundRect(cxr - 3.4, y - 32, 3.4, 32, 1.5, stroke=0, fill=1)
        typo.draw_latin(c, cxr - 12, y - 14, pg, 9.0, weight="semibold", align="right",
                        color=col, tracking=0.4)
        typo.draw_paragraph(c, cxr - ccw + 10, y - 24, label, ccw - 22, 7.2, align="right",
                            color=INK_FAINT)
        if i < 2:
            ax = cxr - ccw - arw / 2
            c.setStrokeColorRGB(*INK_FAINT)
            c.setLineWidth(1.0)
            c.line(ax + 5, y - 16, ax - 5, y - 16)
            c.setFillColorRGB(*INK_FAINT)
            pp = c.beginPath()
            pp.moveTo(ax - 8, y - 16)
            pp.lineTo(ax - 2.6, y - 13.6)
            pp.lineTo(ax - 2.6, y - 18.4)
            pp.close()
            c.drawPath(pp, stroke=0, fill=1)

    y -= 46

    # ---------------- how to choose (fills the page with something useful)
    y = section_label(c, MARGIN_IN + CONTENT_W, y, "", "چطور انتخاب کنم؟", CONTENT_W,
                      color=NAVY)
    criteria = [
        ("اگر تازه‌کاری", "همان ستون «پیشنهادی» را بردار و بقیه را نخوان.", LEVEL["beginner"]),
        ("اگر سرعت می‌خواهی", "تکنیکی را بردار که حرکت کمتری دارد، حتی اگر سخت‌تر است.", LEVEL["mid"]),
        ("اگر گیر می‌کنی", "تکنیکی را بردار که خطای کمتر دارد، نه حرکت کمتر.", LEVEL["pro"]),
    ]
    gap = 10
    cwn = (CONTENT_W - gap * 2) / 3
    for i, (t, s, col) in enumerate(criteria):
        xr = MARGIN_IN + CONTENT_W - i * (cwn + gap)
        x = xr - cwn
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(x, y - 54, cwn, 54, 6, stroke=0, fill=1)
        c.setFillColorRGB(*col)
        c.roundRect(x + cwn - 3.2, y - 54, 3.2, 54, 1.5, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 10, y - 16, t, cwn - 22, 9.0, weight="bold", align="right",
                            color=INK)
        typo.draw_paragraph(c, x + 10, y - 31, s, cwn - 22, 7.8, align="right",
                            color=INK_SOFT, leading=1.8)
    y -= 68

    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y - 46, CONTENT_W, 46, 7, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 18, y - 19,
                        "قاعده: تا وقتی زیر ۶۰ ثانیه نمی‌زنی، جایگزین را عوض نکن.",
                        CONTENT_W - 36, 10, weight="medium", align="right", color=(1, 1, 1))
    typo.draw_paragraph(c, MARGIN_IN + 18, y - 35,
                        "اول یک تکنیک را تا حد رفلکس تمرین کن، بعد سراغ بعدی برو.",
                        CONTENT_W - 36, 8.6, align="right", color=(0.72, 0.78, 0.88))
    return d


def build(path: str):
    d = Doc(path)
    page_map(d)
    page_step(d)
    page_workshop(d)
    d.save()
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("wrote", build(os.path.join(OUT, "sample-pages.pdf")))
