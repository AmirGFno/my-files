"""Build the sample pages (کتاب نمونه) - four pages that define the book's look.

Run:  python3 tools/sample.py
Out:  book/out/sample-pages.pdf
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


# ------------------------------------------------------------------ primitives
def d_left(i, n, width, gap, cell) -> float:
    """x of the i-th column, counted from the RIGHT (RTL) inside a width."""
    return MARGIN_IN + (n - 1 - i) * (cell + gap)


def sec(d, x, y, num, title, width=None, sub=""):
    width = width or CONTENT_W
    c = d.c
    if num:
        typo.draw_paragraph(c, x, y, num, width, 9.2, weight="semibold", align="right",
                            color=ACCENT)
        y -= 17
    y = typo.draw_paragraph(c, x, y, title, width, 14.5, weight="bold", leading=1.5, color=INK)
    if sub:
        y = typo.draw_paragraph(c, x, y + 3, sub, width, 9.4, weight="regular",
                                leading=1.85, color=INK_FAINT)
    return y - 6


def pill(c, x_right: float, y_baseline: float, text: str, fg, bg, size=7.0, weight="medium"):
    """Small rounded tag, right-aligned at x_right."""
    w = typo.text_width(typo.visual(text), typo.font(weight), size) + 13
    h = size + 7
    c.setFillColorRGB(*bg)
    c.roundRect(x_right - w, y_baseline - 2.5, w, h, h / 2, stroke=0, fill=1)
    typo.draw_paragraph(c, x_right - w, y_baseline + 1.2, text, w, size, weight=weight,
                        align="center", color=fg)
    return w


def algorithm_row(d, x, y, width, alg, title, height=38, color=None):
    """One algorithm inside a tidy row: Persian title on the right, LTR alg on the left."""
    c = d.c
    c.setFillColorRGB(0.966, 0.969, 0.976)
    c.roundRect(x, y - height, width, height, 5, stroke=0, fill=1)
    c.setFillColorRGB(*(color or NAVY))
    c.roundRect(x + width - 3.2, y - height, 3.2, height, 1.5, stroke=0, fill=1)
    aw = typo.latin_width(alg, 10.4)
    label_x = x + 12 + aw + 10
    label_w = x + width - 12 - label_x
    if label_w > 30:
        typo.draw_paragraph(c, label_x, y - height + 14, title, label_w, 8.2,
                            weight="regular", align="right", color=INK_SOFT)
    d.alg(x + 12, y - height + 14.5, alg, size=10.4, color=color or NAVY)
    return y - height - 5


def move_arrow(c, x, y, label, r=9.5):
    c.saveState()
    c.setStrokeColorRGB(*INK_SOFT)
    c.setLineWidth(1.15)
    p = c.beginPath()
    p.arc(x - r, y - r, x + r, y + r, 35, 250)
    c.drawPath(p, stroke=1, fill=0)
    ax = x + r * math.cos(math.radians(35))
    ay = y + r * math.sin(math.radians(35))
    c.setFillColorRGB(*INK_SOFT)
    n = c.beginPath()
    n.moveTo(ax + 2.6, ay + 2.2)
    n.lineTo(ax - 1.8, ay + 4.6)
    n.lineTo(ax - 1.2, ay - 1.8)
    n.close()
    c.drawPath(n, stroke=0, fill=1)
    c.setFont(typo.font("bold"), 8)
    c.setFillColorRGB(*INK)
    c.drawCentredString(x, y - 3, label)
    c.restoreState()


def notation_strip(d, x, y, width):
    c = d.c
    items = [("R", "راست"), ("L", "چپ"), ("U", "بالا"), ("D", "پایین"), ("F", "جلو"), ("B", "عقب")]
    gap = 8
    n = len(items)
    cell = (width - gap * (n - 1)) / n
    for i, (letter, fa) in enumerate(items):
        cx = d_left(i, n, width, gap, cell)
        c.setFillColorRGB(0.97, 0.975, 0.985)
        c.roundRect(cx, y - 50, cell, 50, 6, stroke=0, fill=1)
        move_arrow(c, cx + cell / 2, y - 17, letter)
        typo.draw_paragraph(c, cx, y - 39, fa, cell, 7.5, align="center", color=INK_FAINT)
    return y - 50 - 10


def hero_cube_with_shadow(c, x, y, size, cube=None, view="default"):
    c.saveState()
    c.setFillColorRGB(0.04, 0.08, 0.16)
    c.ellipse(x + size * 0.04, y - size * 0.02, x + size * 0.96, y + size * 0.10,
              stroke=0, fill=1)
    c.restoreState()
    render.draw_cube(c, x, y + size * 0.02, size, cube, view=view, shadow=False)


def data_table(d, x, y, width, rows, colw, size=8.2, rh=19, accent_col=None):
    """Header row in navy, zebra body. colw are fractions that sum to 1."""
    c = d.c
    for ri, row in enumerate(rows):
        ry = y - ri * rh
        if ri == 0:
            c.setFillColorRGB(*NAVY)
            c.roundRect(x, ry - 5, width, rh, 3, stroke=0, fill=1)
            colr, wt = (1, 1, 1), "medium"
        else:
            if ri % 2 == 0:
                c.setFillColorRGB(0.973, 0.975, 0.981)
                c.rect(x, ry - 5, width, rh, stroke=0, fill=1)
            colr, wt = (INK if ri == 1 else INK_SOFT), "regular"
        cx = x + width
        for ci, txt in enumerate(row):
            w = width * colw[ci]
            typo.draw_paragraph(c, cx - w, ry + 1, txt, w - 5, size, weight=wt,
                                align="right" if ci == 0 else "center", color=colr)
            cx -= w
    return y - len(rows) * rh - 6


# ------------------------------------------------------------------ page 1
def page_intro(d: Doc):
    c = d.new_page(running="نقشه راه", chapter="جلد اول · مکعب ۳×۳")
    y = PAGE[1] - MARGIN_TOP - 26

    panel_h = 232
    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y - panel_h, CONTENT_W, panel_h, 10, stroke=0, fill=1)

    text_w = CONTENT_W * 0.53
    text_right = MARGIN_IN + CONTENT_W - 26
    tx = text_right - text_w

    typo.draw_paragraph(c, tx, y - 32, "فصل ۱", text_w, 9, weight="medium",
                        align="right", color=(0.55, 0.66, 0.84))
    yy = typo.draw_paragraph(c, tx, y - 52, "چهار مسیر، یک مکعب", text_w, 24, weight="bold",
                             align="right", leading=1.35, color=(1, 1, 1))
    typo.draw_paragraph(
        c, tx, yy - 2,
        "هیچ‌کس با حفظ کردن ۱۱۹ الگوریتم شروع نمی‌کند. این کتاب یک مسیر مبتدی، دو مسیر میانی و یک مسیر "
        "حرفه‌ای دارد. هر چهار مسیر تا آخر کار می‌کنند و هر وقت خواستی می‌توانی مسیرت را عوض کنی.",
        text_w, 9.4, weight="regular", leading=1.95, color=(0.80, 0.85, 0.92))

    hero_cube_with_shadow(c, MARGIN_IN + 24, y - panel_h + 28, 165, Cube(), view="default")

    # ---------------- four methods
    y2 = y - panel_h - 30
    typo.draw_paragraph(c, MARGIN_IN, y2, "چهار روش، به ترتیب سختی", CONTENT_W, 12.5,
                        weight="bold", align="right", color=INK)
    typo.draw_paragraph(c, MARGIN_IN, y2 - 15, "از راست به چپ: مسیر یادگیری پیشنهادی",
                        CONTENT_W, 8.5, align="right", color=INK_FAINT)
    y2 -= 32

    methods = [
        ("لایه‌به‌لایه", "LBL", "beginner", "۶ الگوریتم", "اولین حل کامل"),
        ("پتروس", "Petrus", "mid", "۴۰ الگوریتم", "فکر کردن، نه حفظ کردن"),
        ("زد-زد", "ZZ", "mid", "۵۰ الگوریتم", "بدون چرخش مکعب"),
        ("سی‌اف‌اوپی", "CFOP", "pro", "۱۱۹ الگوریتم", "سقف سرعت"),
    ]
    gap = 10
    n = 4
    cell = (CONTENT_W - gap * (n - 1)) / n
    card_h = 104
    for i, (fa, en, lvl, algs, hook) in enumerate(methods):
        cx = d_left(i, n, CONTENT_W, gap, cell)
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(cx, y2 - card_h, cell, card_h, 7, stroke=0, fill=1)
        c.setFillColorRGB(*LEVEL[lvl])
        c.roundRect(cx + cell - 4, y2 - card_h, 4, card_h, 2, stroke=0, fill=1)
        typo.draw_paragraph(c, cx + 10, y2 - 20, fa, cell - 28, 11, weight="bold",
                            align="right", color=INK)
        d.alg(cx + 10, y2 - 36, en, size=7.6, color=INK_FAINT, tracking=0.3)
        typo.draw_paragraph(c, cx + 10, y2 - 56, hook, cell - 22, 7.9, align="right",
                            color=INK_SOFT, leading=1.8)
        typo.draw_paragraph(c, cx + 10, y2 - 82, algs, cell - 22, 8.2, align="right",
                            color=LEVEL[lvl])
        typo.draw_paragraph(c, cx + 10, y2 - 95, LEVEL_FA[lvl], cell - 22, 7.4,
                            align="right", color=INK_FAINT)

    # ---------------- notation
    y3 = y2 - card_h - 34
    y3 = sec(d, MARGIN_IN, y3, "۱.۱", "نت‌نویسی: زبان مشترک همه‌ی روش‌ها",
             sub="شش وجه، شش حرف. پریم یعنی خلاف جهت عقربه‌های ساعت، ۲ یعنی نیم‌دور.")
    y3 = notation_strip(d, MARGIN_IN, y3 - 2, CONTENT_W)
    d.body(MARGIN_IN, y3 - 2,
           "الگوریتم زنجیره‌ای از حرکت‌هاست که پشت سر هم اجرا می‌شوند: (R U R' U'). فاصله‌ها فقط برای "
           "خوانایی‌اند و ترتیب از چپ به راست خوانده می‌شود. اگر جایی اشتباه شد، همان الگوریتم را برعکس "
           "و از آخر اجرا کن تا مکعب به حالت قبلی برگردد؛ به این «اینورس» می‌گوییم.",
           CONTENT_W, 10)
    return d


# ------------------------------------------------------------------ page 2
def columns(widths: Sequence[float], gap: float, total: float = None):
    """RTL column frame: returns [(x_right, width), ...] starting from the right margin."""
    total = total or CONTENT_W
    out = []
    x = MARGIN_IN + total
    for w in widths:
        out.append((x, w))
        x -= w + gap
    return out


def page_step(d: Doc):
    c = d.new_page(running="مبتدی · لایه‌به‌لایه", chapter="فصل ۲ · صلیب سفید")

    y = PAGE[1] - MARGIN_TOP - 26
    d.step_badge(MARGIN_IN + CONTENT_W - 28, y + 4, "۳", color=LEVEL["beginner"], d=28)
    typo.draw_paragraph(c, MARGIN_IN, y + 14, "گام سوم · لایه‌به‌لایه", 220, 9.5,
                        weight="medium", align="right", color=LEVEL["beginner"])
    title_w = CONTENT_W - 46
    y = typo.draw_paragraph(c, MARGIN_IN, y - 10, "صلیب سفید را از «دیزی» بساز", title_w,
                            20, weight="bold", leading=1.4, color=INK)
    y = typo.draw_paragraph(
        c, MARGIN_IN, y - 3,
        "هدف این گام: چهار لبه‌ی سفید، هر کدام بالای مرکز هم‌رنگ خودش. فن این گام «تطبیق رنگ کنار لبه» "
        "است، نه چرخاندن بی‌هدف.", title_w, 9.6, leading=1.9, color=INK_SOFT) - 18

    # ---------------- figure strip: start -> after -> flat daisy map
    fig_h = 128
    gap = 14
    cols = columns([(CONTENT_W - 2 * gap) / 3] * 3, gap)
    fig_top = y
    figs = [
        ("حالت شروع", scene(""), "قبل", "cube-default"),
        ("پس از دیزی", scene("R2 L2 F2 B2"), "بعد", "cube-top"),
        ("نمای بالا: دیزی", scene("R2 L2 F2 B2"), "", "map"),
    ]
    for (xr, w), (cap, cube, tag, kind) in zip(cols, figs):
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(xr - w, fig_top - fig_h - 10, w, fig_h + 14, 8, stroke=0, fill=1)
        if kind == "map":
            render.draw_face_map(c, xr - w + 14, fig_top - fig_h + 2, w - 28, cube, "U",
                                 gap=3, radius=3.5)
        else:
            render.draw_cube(c, xr - w + 6, fig_top - fig_h - 2, w - 12, cube,
                             view="default" if kind.endswith("default") else "top",
                             shadow=False)
        if tag:
            c.setFillColorRGB(1, 1, 1)
            c.roundRect(xr - w + 6, fig_top - 6, 26, 14, 4, stroke=0, fill=1)
            typo.draw_paragraph(c, xr - w + 6, fig_top - 2.5, tag, 26, 7.2, weight="medium",
                                align="center", color=INK_SOFT)
        typo.draw_paragraph(c, xr - w, fig_top - fig_h - 30, cap, w, 7.8, align="center",
                            color=INK_FAINT)

    # ---------------- comparison table
    ty = fig_top - fig_h - 52
    typo.draw_paragraph(c, MARGIN_IN, ty, "کدام تکنیک برای صلیب؟", CONTENT_W, 10, weight="bold",
                        align="right", color=INK)
    ty -= 20
    ty = data_table(d, MARGIN_IN, ty, CONTENT_W,
                    [("تکنیک", "تعداد حرکت", "لایه‌های حل‌شده", "مناسب برای", "توضیح کامل"),
                     ("دیزی (پیشنهادی)", "۱۲–۱۶", "دست‌نخورده", "مبتدی مطلق", "ص ۳۶"),
                     ("صلیب مستقیم", "۶–۱۰", "دست‌نخورده", "با دید فضایی", "ص ۴۴"),
                     ("صلیب کور", "۸", "دست‌نخورده", "زیر ۳۰ ثانیه", "ص ۵۲")],
                    colw=[0.30, 0.16, 0.22, 0.20, 0.12])

    # ---------------- two columns: method (right) | algorithms + why (left)
    body_top = ty - 16
    right_w = CONTENT_W * 0.47
    left_w = CONTENT_W - right_w - 24
    rx = MARGIN_IN + CONTENT_W - right_w
    lx = MARGIN_IN

    cy = body_top
    typo.draw_paragraph(c, rx, cy, "روش پیشنهادی: دیزی", right_w, 11.5, weight="bold",
                        align="right", color=INK)
    cy -= 19
    steps = [
        ("هر لبه‌ی سفید را بالا بیاور",
         "لبه‌های سفید را دور مرکز زرد جمع کن، طوری که سفید رو به بالا باشد."),
        ("رنگ کنار لبه را با مرکز بسنج",
         "اگر سبز است، باید بالای مرکز سبز بایستد؛ نه بالای مرکز قرمز."),
        ("لبه را پایین بیاور",
         "آن وجه را دو حرکت بچرخان تا لبه در لایه‌ی پایین، در جای خودش بنشیند."),
    ]
    for i, (t, s_) in enumerate(steps, 1):
        c.setFillColorRGB(*LEVEL["beginner"])
        c.circle(rx + right_w - 7, cy + 2.5, 6.2, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(typo.font("bold"), 7.6)
        c.drawCentredString(rx + right_w - 7, cy + 0.2, _fa_digits(str(i)))
        typo.draw_paragraph(c, rx, cy, t, right_w - 20, 9.4, weight="medium", align="right",
                            color=INK)
        cy = typo.draw_paragraph(c, rx, cy - 13, s_, right_w - 20, 8.4, align="right",
                                 color=INK_SOFT, leading=1.85) - 9

    # left column
    ly = body_top
    typo.draw_paragraph(c, lx, ly, "الگوریتم‌های این گام", left_w, 10, weight="bold",
                        align="right", color=INK)
    ly -= 10
    for alg, title in (("F R U R' U' F'", "صلیب زرد"),
                       ("F2 R2", "دیزی دو حرکتی"),
                       ("R U R' U'", "چرخش لبه")):
        ly = algorithm_row(d, lx, ly, left_w, alg, title)
    ly -= 6
    ly = d.callout(lx, ly, left_w, "چرا دیزی کار می‌کند",
                   "لبه‌ی سفید یک قطعه با دو رنگ است. تا وقتی رنگ دوم با مرکز هم‌رنگش یکی نشود، "
                   "لبه در جای درست نیست. دیزی این تطبیق را در لایه‌ی بالا و در دید کامل انجام "
                   "می‌دهد.")
    d.callout(lx, ly, left_w, "اشتباه رایج",
              "اگر لبه درست پایین نیامد، به لایه‌ی بالا برگردانش و تطبیق را از نو بگیر. "
              "صلیب ناقص، گام بعدی را غیرممکن می‌کند.", kind="warn")

    return d


# ------------------------------------------------------------------ page 3
def page_alternatives(d: Doc):
    c = d.new_page(running="کارگاه روش‌های جایگزین", chapter="فصل ۲")

    y = PAGE[1] - MARGIN_TOP - 26
    typo.draw_paragraph(c, MARGIN_IN, y, "بخش ۲.۹ · کارگاه", CONTENT_W, 9.2, weight="medium",
                        align="right", color=ACCENT)
    y = typo.draw_paragraph(c, MARGIN_IN, y - 17, "هر گام، چند راه", CONTENT_W, 21,
                            weight="bold", leading=1.4, color=INK)
    y = typo.draw_paragraph(
        c, MARGIN_IN, y - 1,
        "در فصل ۲ یک روش برای هر گام یاد گرفتی. این کارگاه جایگزین‌های همان گام‌ها را کنار هم می‌گذارد "
        "تا انتخاب کنی. عدد کنار هر تکنیک، صفحه‌ی توضیح کامل آن است.", CONTENT_W, 9.6,
        leading=1.95, color=INK_SOFT) - 20

    blocks = [
        ("گام ۳ · صلیب سفید", "beginner", [
            ("دیزی", "لبه‌ها را دور مرکز زرد جمع می‌کنی و یکی‌یکی پایین می‌آوری.",
             "بدون نیاز به دیدن لبه‌های پایین", "۱۲–۱۶", "۳۶", "پیشنهادی"),
            ("صلیب مستقیم", "هر لبه را مستقیم از هر جای مکعب به جای خودش می‌بری.",
             "حرکت کمتر، نیاز به دید فضایی", "۶–۱۰", "۴۴", ""),
            ("صلیب کور", "کل صلیب را در ۱۵ ثانیه‌ی بازرسی برنامه‌ریزی می‌کنی.",
             "پایه‌ی سرعت در CFOP", "۸", "۵۲", "حرفه‌ای"),
        ]),
        ("گام ۵ · لبه‌های لایه دوم", "mid", [
            ("درج از راست", "لبه را از بالا می‌آوری و به شکاف راست می‌فرستی.",
             "الگوریتم کوتاه و قابل تکرار", "۸", "۶۸", "پیشنهادی"),
            ("درج آینه‌ای از چپ", "همان الگوریتم با دست چپ؛ برای شکاف سمت چپ.",
             "بدون چرخش مکعب", "۸", "۷۰", ""),
            ("Keyhole", "یک گوشه را باز می‌گذاری و لبه را از سوراخ عبور می‌دهی.",
             "سریع‌تر برای چند لبه پشت سر هم", "۴–۶", "۷۴", ""),
        ]),
        ("گام ۷ · جای لبه‌های زرد", "pro", [
            ("U-Perm", "سه لبه را در یک چرخه جابه‌جا می‌کند.", "الگوریتم پایه، همیشه کار می‌کند",
             "۹", "۱۰۲", "پیشنهادی"),
            ("U-Perm ام‌محور", "همان کار با حرکت‌های M؛ دست راحت‌تر، سرعت بیشتر.",
             "برای زیر ۴۰ ثانیه", "۹", "۱۰۶", ""),
            ("EPLL کامل", "چهار حالت لبه‌ها را یک‌ضربه‌ای می‌زند.", "بدون تکرار، تشخیص سخت‌تر",
             "۴", "۱۴۰", ""),
        ]),
    ]

    gap = 14
    n = 3
    bw = (CONTENT_W - gap * (n - 1)) / n
    top = y
    lowest = top
    for bi, (title, lvl, items) in enumerate(blocks):
        bx = d_left(bi, n, CONTENT_W, gap, bw)
        by = top
        c.setFillColorRGB(*LEVEL_SOFT[lvl])
        c.roundRect(bx, by - 24, bw, 24, 5, stroke=0, fill=1)
        typo.draw_paragraph(c, bx, by - 16, title, bw - 12, 9.2, weight="bold", align="right",
                            color=LEVEL[lvl])
        by -= 36
        for (name, what, why, moves, page, badge) in items:
            typo.draw_paragraph(c, bx + 12, by, name, bw - 46, 9.6, weight="bold",
                                align="right", color=INK)
            pg = "ص " + page
            typo.draw_latin(c, bx + 2, by, pg, 7.6, weight="medium", align="left", color=ACCENT,
                            tracking=0.3)
            by -= 15
            by = typo.draw_paragraph(c, bx, by, what, bw - 2, 8.1, align="right",
                                     color=INK_SOFT, leading=1.8) - 3
            by = typo.draw_paragraph(c, bx, by, why, bw - 2, 7.6, align="right",
                                     color=INK_FAINT, leading=1.75) - 5
            # last line: moves + optional badge
            if badge:
                pill(c, bx + bw, by + 1.5, badge, ACCENT, ACCENT_SOFT, size=6.6)
            typo.draw_paragraph(c, bx, by, moves + " حرکت", bw - 54, 7.5, align="right",
                                color=INK_FAINT)
            by -= 22
        lowest = min(lowest, by)
        if bi < n - 1:
            c.setStrokeColorRGB(*RULE)
            c.setLineWidth(0.6)
            c.line(bx - gap / 2, top + 4, bx - gap / 2, by + 10)

    # ---------------- how the cross-reference works
    fy = lowest - 10
    typo.draw_paragraph(c, MARGIN_IN, fy, "ارجاع‌ها چطور کار می‌کنند", CONTENT_W, 10.5,
                        weight="bold", align="right", color=INK)
    fy -= 14
    typo.draw_paragraph(c, MARGIN_IN, fy,
                        "هر تکنیک یک صفحه‌ی توضیح کامل دارد. با شماره‌ی صفحه مستقیم برو سراغش:",
                        CONTENT_W, 8.8, align="right", color=INK_SOFT)
    fy -= 16

    chain = [("ص ۳۶", "تکنیک پایه", LEVEL["beginner"]),
             ("ص ۴۴", "جایگزین میانی", LEVEL["mid"]),
             ("ص ۵۲", "نسخه‌ی حرفه‌ای", LEVEL["pro"])]
    arw = 26
    cw = (CONTENT_W - 2 * arw) / 3
    for i, (pg, label, col) in enumerate(chain):
        cxr = MARGIN_IN + CONTENT_W - i * (cw + arw)
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(cxr - cw, fy - 34, cw, 34, 5, stroke=0, fill=1)
        c.setFillColorRGB(*col)
        c.roundRect(cxr - 3.4, fy - 34, 3.4, 34, 1.5, stroke=0, fill=1)
        typo.draw_latin(c, cxr - 12, fy - 14, pg, 9.2, weight="semibold", align="right",
                        color=col, tracking=0.4)
        typo.draw_paragraph(c, cxr - cw + 10, fy - 24, label, cw - 24, 7.4, align="right",
                            color=INK_FAINT)
        if i < 2:
            ax = cxr - cw - arw / 2
            c.setStrokeColorRGB(*INK_FAINT)
            c.setLineWidth(1.0)
            c.line(ax + 6, fy - 17, ax - 6, fy - 17)
            c.setFillColorRGB(*INK_FAINT)
            pp = c.beginPath()
            pp.moveTo(ax - 9, fy - 17)
            pp.lineTo(ax - 3.4, fy - 14.6)
            pp.lineTo(ax - 3.4, fy - 19.4)
            pp.close()
            c.drawPath(pp, stroke=0, fill=1)

    fy -= 46
    c.setFillColorRGB(0.972, 0.974, 0.98)
    c.roundRect(MARGIN_IN, fy - 56, CONTENT_W, 56, 7, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 16, fy - 20,
                        "قاعده‌ی انتخاب: تا وقتی زیر ۶۰ ثانیه نمی‌زنی، جایگزین را عوض نکن.",
                        CONTENT_W - 32, 9.6, weight="medium", align="right", color=INK)
    typo.draw_paragraph(c, MARGIN_IN + 16, fy - 40,
                        "اول یک تکنیک را تا حد رفلکس تمرین کن، بعد سراغ بعدی برو. تعویض زودهنگام "
                        "بزرگ‌ترین دلیل گیر کردن در ۴۰ ثانیه است.", CONTENT_W - 32, 8.6,
                        align="right", color=INK_SOFT)
    return d


def build(path: str):
    d = Doc(path)
    page_intro(d)
    page_step(d)
    page_alternatives(d)
    d.save()
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("wrote", build(os.path.join(OUT, "sample-pages.pdf")))
