"""The sample pages.

Every block is measured before it is drawn: column widths are computed from the
content, headings shrink to fit, table columns get an explicit x each. This is
what keeps Persian text from colliding — the previous version guessed offsets.
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
from scenes import is_cross, is_daisy, scene

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
TOP = PAGE[1] - MARGIN_TOP - 30
BOTTOM = MARGIN_BOT + 18

# ------------------------------------------------------------------ states
START = ""
DAISY = "R2 L2 F2 B2"                 # verified: four white edges up, yellow centre
CROSS = "R2 L2 F2 B2 F2 R2 B2 L2"     # verified: white cross on the bottom


# ==================================================================== helpers
def cols(widths: Sequence[float], gap: float = 22, right: float = None) -> List[Tuple[float, float]]:
    """Right-to-left columns: [(left_x, width)] — index 0 is the RIGHT-hand one."""
    out, xr = [], right if right is not None else MARGIN_IN + CONTENT_W
    for w in widths:
        out.append((xr - w, w))
        xr -= w + gap
    return out


def tick(c, xr, y, color):
    c.setFillColorRGB(*color)
    c.rect(xr - 3, y - 1.5, 3, 11.5, stroke=0, fill=1)


def kicker(c, xr, y, text, width=None, color=None, size=8.4):
    """Small label, tick at the right edge, text flowing left from it."""
    width = width or CONTENT_W
    tick(c, xr, y, color or ACCENT)
    typo.draw_paragraph(c, xr - width + 9, y, text, width - 12, size, weight="semibold",
                        align="right", color=color or ACCENT)
    return y - 19


def heading(d, x, y, text, width=None, size=24, max_lines=2):
    width = width or CONTENT_W
    size = typo.fit_size(text, width, "bold", start=size, minimum=13)
    return typo.draw_paragraph(d.c, x, y, text, width, size, weight="bold", leading=1.42,
                               align="right", color=INK)


def lead(d, x, y, text, width=None, size=10.2, color=None):
    return typo.draw_paragraph(d.c, x, y, text, width or CONTENT_W, size, weight="regular",
                               leading=2.0, align="right", color=color or INK_SOFT)


def para(d, x, y, text, width, size=9.2, color=None, weight="regular", leading=1.95):
    return typo.draw_paragraph(d.c, x, y, text, width, size, weight=weight, align="right",
                               leading=leading, color=color or INK_SOFT)


def rule(c, x, y, w, color=None):
    c.setStrokeColorRGB(*(color or RULE))
    c.setLineWidth(0.6)
    c.line(x, y, x + w, y)


def pill(c, x_right, y, text, fg, bg, size=6.8):
    w = typo.text_width(typo.visual(text), typo.font("medium"), size) + 12
    h = size + 6.5
    c.setFillColorRGB(*bg)
    c.roundRect(x_right - w, y - 2, w, h, h / 2, stroke=0, fill=1)
    typo.draw_paragraph(c, x_right - w, y + 1.4, text, w, size, weight="medium",
                        align="center", color=fg)
    return w


def progress(c, x_right, y, total, current, width, color):
    gap = width / total
    for i in range(total):
        n = i + 1
        cx = x_right - gap * i - gap / 2
        if n == current:
            c.setFillColorRGB(*color)
            c.circle(cx, y, 9, stroke=0, fill=1)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(typo.font("bold"), 8.2)
            c.drawCentredString(cx, y - 3, _fa_digits(str(n)))
        elif n < current:
            c.setFillColorRGB(*LEVEL_SOFT["beginner"])
            c.circle(cx, y, 8, stroke=0, fill=1)
            c.setFillColorRGB(*color)
            c.setFont(typo.font("medium"), 7.6)
            c.drawCentredString(cx, y - 2.7, _fa_digits(str(n)))
        else:
            c.setStrokeColorRGB(*RULE)
            c.setLineWidth(0.9)
            c.circle(cx, y, 8, stroke=1, fill=0)
            c.setFillColorRGB(*INK_FAINT)
            c.setFont(typo.font("regular"), 7.6)
            c.drawCentredString(cx, y - 2.7, _fa_digits(str(n)))
        if i < total - 1:
            c.setStrokeColorRGB(*(color if n < current else RULE))
            c.setLineWidth(1.3 if n < current else 0.7)
            c.line(cx - 11, y, cx - gap + 11, y)
    return y - 28


def algs_block(d, x, y, width, items, color=None):
    """Algorithms, each in its own row: LTR algorithm on the left, label on the right."""
    c = d.c
    for alg, label in items:
        h = 34
        c.setFillColorRGB(0.966, 0.969, 0.976)
        c.roundRect(x, y - h, width, h, 5, stroke=0, fill=1)
        c.setFillColorRGB(*(color or NAVY))
        c.roundRect(x + width - 3.2, y - h, 3.2, h, 1.5, stroke=0, fill=1)
        aw = typo.latin_width(alg, 10.0)
        d.alg(x + 10, y - h + 13.5, alg, size=10.0, color=color or NAVY)
        lx = x + 10 + aw + 12
        lw = (x + width - 10) - lx
        if lw > 26:
            typo.draw_paragraph(c, lx, y - h + 13.5, label, lw, 7.8,
                                align="right", color=INK_FAINT)
        y -= h + 4
    return y


def callout(d, x, y, width, title, text, kind="why", size=9.0):
    c = d.c
    bg, fg = {
        "why": ((0.93, 0.96, 0.99), (0.13, 0.36, 0.66)),
        "warn": ((0.99, 0.94, 0.92), (0.74, 0.24, 0.15)),
        "note": ((0.94, 0.97, 0.94), (0.10, 0.45, 0.30)),
    }[kind]
    inner = width - 24
    th = typo.text_height(text, inner, size)
    h = 17 + 14 + th + 8
    c.setFillColorRGB(*bg)
    c.roundRect(x, y - h, width, h, 6, stroke=0, fill=1)
    c.setFillColorRGB(*fg)
    c.roundRect(x + width - 3, y - h, 3, h, 1.5, stroke=0, fill=1)
    typo.draw_paragraph(c, x + 11, y - 18, title, inner, size, weight="bold",
                        align="right", color=fg)
    typo.draw_paragraph(c, x + 11, y - 18 - 13.5, text, inner, size,
                        align="right", leading=1.85, color=(0.22, 0.24, 0.28))
    return y - h - 9


def table(d, x, y, width, header, rows, weights, align=None, size=8.4, rh=21,
          accent_col=None):
    """A table with explicit column x positions — nothing can collide."""
    c = d.c
    total = sum(weights)
    ws = [width * w / total for w in weights]
    rights, xr = [], x + width
    for w in ws:
        rights.append(xr)
        xr -= w
    align = align or (["right"] + ["center"] * (len(header) - 1))

    c.setFillColorRGB(*NAVY)
    c.roundRect(x, y - rh + 6, width, rh, 4, stroke=0, fill=1)
    for i, cell in enumerate(header):
        typo.draw_paragraph(c, rights[i] - ws[i] + 6, y - rh + 13.5, cell, ws[i] - 12,
                            size - 0.4, weight="medium", align=align[i], color=(1, 1, 1))
    y -= rh
    for ri, row in enumerate(rows):
        if ri % 2 == 1:
            c.setFillColorRGB(0.973, 0.975, 0.981)
            c.rect(x, y - rh + 6, width, rh, stroke=0, fill=1)
        for ci, cell in enumerate(row):
            numeric = all(ch in "0123456789۰۱۲۳۴۵۶۷۸۹٪%.,–- " for ch in cell)
            if numeric:
                typo.draw_numerals(c, rights[ci] - 6, y - rh + 13.5, cell, size,
                                   align=align[ci] if align[ci] != "center" else "center",
                                   color=ACCENT if ci == accent_col else INK_SOFT)
            else:
                typo.draw_paragraph(c, rights[ci] - ws[ci] + 6, y - rh + 13.5, cell,
                                    ws[ci] - 12, size, align=align[ci],
                                    color=ACCENT if ci == accent_col else
                                    (INK if ci == 0 else INK_SOFT))
        y -= rh
    rule(c, x, y + 6, width)
    return y


def figure_row(d, y, fig_h, items, gap=12):
    """items: [(caption, cube, view)] laid out right to left, with arrows between."""
    c = d.c
    n = len(items)
    cw = (CONTENT_W - gap * (n - 1)) / n
    for i, (cap, cube, view) in enumerate(items):
        xr = MARGIN_IN + CONTENT_W - i * (cw + gap)
        c.setFillColorRGB(0.972, 0.974, 0.980)
        c.roundRect(xr - cw, y - fig_h, cw, fig_h, 7, stroke=0, fill=1)
        box = min(cw - 8, fig_h - 8)
        render.draw_cube(c, xr - cw + (cw - box) / 2, y - fig_h + (fig_h - box) / 2,
                         box, cube, view=view, shadow=True)
        typo.draw_paragraph(c, xr - cw, y - fig_h - 12, cap, cw, 7.6,
                            align="center", color=INK_FAINT)
        if i < n - 1:
            ax = xr - cw - gap / 2
            c.setStrokeColorRGB(*INK_FAINT)
            c.setLineWidth(0.9)
            c.line(ax + 4, y - fig_h / 2, ax - 4, y - fig_h / 2)
            c.setFillColorRGB(*INK_FAINT)
            p = c.beginPath()
            p.moveTo(ax - 7, y - fig_h / 2)
            p.lineTo(ax - 1.5, y - fig_h / 2 + 2.4)
            p.lineTo(ax - 1.5, y - fig_h / 2 - 2.4)
            p.close()
            c.drawPath(p, stroke=0, fill=1)
    return y - fig_h - 22


# ==================================================================== page 1
def page_map(d: Doc):
    c = d.new_page(running="نقشه کتاب", chapter="جلد اول · مکعب ۳×۳")
    y = TOP

    kicker(c, MARGIN_IN + CONTENT_W, y, "راهنمای خواندن · یک صفحه")
    y = heading(d, MARGIN_IN, y - 26, "از کجا شروع کنم؟", size=27)
    y = lead(d, MARGIN_IN, y - 4,
             "این کتاب چند مسیر دارد و مسیرها را نباید قاطی کرد: اول تازه‌کار شو، بعد مسیر خودت را "
             "انتخاب کن. مسیر سبز فقط سه فصل لازم دارد.", CONTENT_W * 0.70) - 20

    tracks = [
        ("مسیر سبز", "تازه‌کار", "beginner", "از فصل ۲", "لایه‌به‌لایه",
         "تنها مسیری که بدون پیش‌زمینه تا حل کامل می‌برد.", "۶ الگوریتم", "۸۰ صفحه"),
        ("مسیر آبی", "میانی", "mid", "از فصل ۳ و ۴", "پتروس یا ZZ",
         "وقتی زیر ۹۰ ثانیه می‌زنی، یکی از این دو را انتخاب کن.", "۴۰ تا ۵۰ الگوریتم", "۱۲۰ صفحه"),
        ("مسیر بنفش", "حرفه‌ای", "pro", "از فصل ۵", "CFOP",
         "بدون حد وسط: ۱۱۹ الگوریتم، سقف سرعت.", "۱۱۹ الگوریتم", "۱۴۰ صفحه"),
    ]
    gap, n = 12, 3
    cw = (CONTENT_W - gap * (n - 1)) / n
    card_h = 172
    for i, (name, level, lvl, chap, method, desc, algs, pages) in enumerate(tracks):
        xr = MARGIN_IN + CONTENT_W - i * (cw + gap)
        x = xr - cw
        c.setFillColorRGB(*LEVEL_SOFT[lvl])
        c.roundRect(x, y - card_h, cw, card_h, 8, stroke=0, fill=1)
        c.setFillColorRGB(*LEVEL[lvl])
        c.roundRect(x, y - 25, cw, 25, 8, stroke=0, fill=1)
        c.rect(x, y - 25, cw, 10, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 10, y - 16.5, name, cw - 20, 9.4, weight="bold",
                            align="right", color=(1, 1, 1))
        typo.draw_paragraph(c, x + 10, y - 16.5, level, cw - 20, 8.0, align="left",
                            color=(1, 1, 1))
        yy = y - 42
        typo.draw_paragraph(c, x + 10, yy, chap, cw - 20, 7.8, align="right", color=INK_FAINT)
        yy = typo.draw_paragraph(c, x + 10, yy - 14, method, cw - 20, 13, weight="bold",
                                 align="right", color=INK)
        yy = typo.draw_paragraph(c, x + 10, yy - 2, desc, cw - 20, 8.2, align="right",
                                 color=INK_SOFT, leading=1.9)
        c.setFillColorRGB(1, 1, 1)
        c.roundRect(x + 9, y - card_h + 9, cw - 18, 38, 5, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 15, y - card_h + 31, algs, cw - 30, 8.0, weight="medium",
                            align="right", color=LEVEL[lvl])
        typo.draw_paragraph(c, x + 15, y - card_h + 17, pages, cw - 30, 7.6, align="right",
                            color=INK_FAINT)

    y -= card_h + 24

    right, left = cols([CONTENT_W * 0.60 - 24, CONTENT_W * 0.40])
    rx, rw = right
    lx, lw = left

    yr = kicker(c, rx + rw, y, "ساختار هر صفحه‌ی گام · شش بخش ثابت", rw)
    blocks = [
        ("هدف گام", "یک جمله: در پایان این صفحه چه چیزی حل شده است."),
        ("چرا این‌جوری", "منطق پشت روش، بدون فرمول."),
        ("قدم‌ها", "شماره‌دار، هر قدم یک کار."),
        ("الگوریتم", "حرکت‌ها لاتین و جدا از متن."),
        ("اگر گیر کردی", "خطاهای رایج و راه خروج."),
        ("جایگزین‌ها", "تکنیک‌های دیگر همین گام + صفحه."),
    ]
    for i, (t, s_) in enumerate(blocks, 1):
        c.setFillColorRGB(*ACCENT_SOFT)
        c.circle(rx + rw - 5.5, yr + 2.5, 5.5, stroke=0, fill=1)
        c.setFillColorRGB(*ACCENT)
        c.setFont(typo.font("bold"), 7)
        c.drawCentredString(rx + rw - 5.5, yr + 0.2, _fa_digits(str(i)))
        typo.draw_paragraph(c, rx, yr, t, rw - 17, 8.8, weight="bold", align="right",
                            color=INK)
        yr = typo.draw_paragraph(c, rx, yr - 11.5, s_, rw - 17, 7.9, align="right",
                                 color=INK_FAINT, leading=1.75) - 6.5

    # reading path (left)
    card2 = 190
    c.setFillColorRGB(0.975, 0.977, 0.982)
    c.roundRect(lx, y - card2, lw, card2, 8, stroke=0, fill=1)
    typo.draw_paragraph(c, lx + 12, y - 21, "مسیر خواندن", lw - 24, 9.2, weight="bold",
                        align="right", color=INK)
    path = [
        ("مکعب را بشناس", "قطعه‌ها و نت‌نویسی", "ص ۸", LEVEL["beginner"]),
        ("یک روش را کامل کن", "لایه‌به‌لایه، بدون پرش", "فصل ۲", LEVEL["beginner"]),
        ("جایگزین‌ها را بسنج", "کارگاه پایان فصل", "ص ۸۰", LEVEL["mid"]),
        ("سرعت را بالا ببر", "روش دوم یا CFOP", "فصل ۳ تا ۵", LEVEL["pro"]),
    ]
    sy = y - 42
    spine = lx + lw - 21
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(1.2)
    c.line(spine, sy + 8, spine, sy - 3 * 38 - 2)
    for i, (t, s_, pg, col) in enumerate(path):
        yy = sy - i * 38
        c.setFillColorRGB(*col)
        c.circle(spine, yy, 8.5, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(typo.font("bold"), 7.4)
        c.drawCentredString(spine, yy - 2.8, _fa_digits(str(i + 1)))
        tx = lx + 12
        tw = (spine - 14) - tx
        typo.draw_paragraph(c, tx, yy + 6, t, tw, 8.6, weight="medium", align="right",
                            color=INK)
        typo.draw_paragraph(c, tx, yy - 5, s_, tw, 7.4, align="right", color=INK_FAINT)
        typo.draw_numerals(c, tx, yy - 17, pg, 7.2, align="left", color=col)

    y = min(yr, y - card2) - 20
    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y - 44, CONTENT_W, 44, 7, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 18, y - 19,
                        "قانون طلایی: تا وقتی یک روش را کامل یاد نگرفته‌ای، سراغ روش بعدی نرو.",
                        CONTENT_W - 36, 9.8, weight="medium", align="right", color=(1, 1, 1))
    typo.draw_paragraph(c, MARGIN_IN + 18, y - 34,
                        "بخش «جایگزین‌ها» برای بعد است؛ اول مسیر اصلی را تا پایان برو.",
                        CONTENT_W - 36, 8.4, align="right", color=(0.72, 0.78, 0.88))
    return d


# ==================================================================== page 2
def page_step(d: Doc):
    c = d.new_page(running="فصل ۲ · گام ۳ از ۷", chapter="لایه‌به‌لایه")

    y = TOP
    typo.draw_paragraph(c, MARGIN_IN, y, "کجای روش هستی؟ گام ۳ از ۷", CONTENT_W, 8.4,
                        weight="medium", align="right", color=LEVEL["beginner"])
    y -= 22
    y = progress(c, MARGIN_IN + CONTENT_W, y, 7, 3, CONTENT_W, LEVEL["beginner"]) - 6

    y = kicker(c, MARGIN_IN + CONTENT_W, y, "بخش ۱ · هدف این گام", CONTENT_W,
               color=LEVEL["beginner"])
    y = heading(d, MARGIN_IN, y - 6, "صلیب سفید را از «دیزی» بساز", size=22)
    y = lead(d, MARGIN_IN, y - 3,
             "در پایان این صفحه: چهار لبه‌ی سفید در لایه‌ی پایین، هر کدام بالای مرکز هم‌رنگ خودش.",
             CONTENT_W * 0.78) - 14

    y = figure_row(d, y, 96, [
        ("۱. شروع", scene(START), "default"),
        ("۲. دیزی", scene(DAISY), "top"),
        ("۳. صلیب کامل", scene(CROSS), "bottom"),
    ])
    y -= 4

    right, left = cols([CONTENT_W * 0.56 - 22, CONTENT_W * 0.44])
    rx, rw = right
    lx, lw = left

    yr = kicker(c, rx + rw, y, "بخش ۲ · چرا این‌جوری؟", rw)
    yr = para(d, rx, yr + 4,
              "لبه‌ی سفید یک قطعه با دو رنگ است. تا وقتی رنگ دوم با مرکز هم‌رنگش یکی نشود، "
              "لبه در جای درست نیست — حتی اگر سفیدش رو به پایین باشد. دیزی این تطبیق را در "
              "لایه‌ی بالا و در دید کامل انجام می‌دهد.", rw, 9.0) - 12

    yr = kicker(c, rx + rw, yr, "بخش ۳ · قدم‌ها", rw)
    steps = [
        ("چهار لبه‌ی سفید را بالا بیاور", "سفیدها دور مرکز زرد، رو به بالا."),
        ("رنگ کنار لبه را بسنج", "سبز روی مرکز سبز، قرمز روی قرمز."),
        ("لبه را پایین بیاور", "همان وجه را دو حرکت بچرخان."),
        ("هر چهار لبه را تکرار کن", "ترتیب مهم نیست؛ هر لبه مستقل است."),
    ]
    for i, (t, s_) in enumerate(steps, 1):
        c.setFillColorRGB(*LEVEL["beginner"])
        c.circle(rx + rw - 6, yr + 2.5, 5.8, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(typo.font("bold"), 7.2)
        c.drawCentredString(rx + rw - 6, yr + 0.2, _fa_digits(str(i)))
        typo.draw_paragraph(c, rx, yr, t, rw - 18, 8.9, weight="medium", align="right",
                            color=INK)
        yr = typo.draw_paragraph(c, rx, yr - 11.5, s_, rw - 18, 7.9, align="right",
                                 color=INK_FAINT, leading=1.7) - 6

    yl = kicker(c, lx + lw, y, "بخش ۴ · الگوریتم‌های این گام", lw)
    yl = algs_block(d, lx, yl + 2, lw, [
        ("F R U R' U' F'", "صلیب زرد"),
        ("F2 R2", "دیزی دو حرکتی"),
        ("D2", "برگرداندن دیزی"),
    ]) - 4
    yl = kicker(c, lx + lw, yl, "بخش ۵ · اگر گیر کردی", lw, color=(0.74, 0.24, 0.15))
    yl = callout(d, lx, yl + 2, lw, "دو خطای رایج",
                 "۱) لبه‌ی سفید رو به بالا مانده: یک حرکت پایینش بیاور و از نو تطبیق بده.  "
                 "۲) دیزی کامل است ولی صلیب کج است: هر لبه را جداگانه پایین بیاور.",
                 kind="warn")

    y = min(yr, yl) - 8
    y = kicker(c, MARGIN_IN + CONTENT_W, y, "بخش ۶ · جایگزین‌های همین گام", CONTENT_W)
    y = para(d, MARGIN_IN, y + 2,
             "همین گام را سه تکنیک دیگر هم می‌شود زد؛ توضیح کامل هر کدام در صفحه‌ی مشخص‌شده است.",
             CONTENT_W * 0.78, 8.4, color=INK_FAINT) - 8
    y = table(d, MARGIN_IN, y, CONTENT_W,
              ["تکنیک", "حرکت", "سختی", "مناسب برای", "توضیح کامل"],
              [["دیزی (همین فصل)", "۱۲–۱۶", "۱ از ۵", "مبتدی مطلق", "همین صفحه"],
               ["صلیب مستقیم", "۶–۱۰", "۳ از ۵", "با دید فضایی", "ص ۴۴"],
               ["صلیب کور", "۸", "۵ از ۵", "زیر ۳۰ ثانیه", "ص ۵۲"]],
              weights=[30, 14, 14, 24, 18], accent_col=4, rh=20)

    y -= 12
    c.setFillColorRGB(0.972, 0.974, 0.98)
    c.roundRect(MARGIN_IN, y - 32, CONTENT_W, 32, 6, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 14, y - 20,
                        "تمام شد؟ گام بعدی: چهار گوشه‌ی سفید را جا بینداز", CONTENT_W - 110,
                        9.0, weight="medium", align="right", color=INK)
    typo.draw_numerals(c, MARGIN_IN + CONTENT_W - 16, y - 20, "ص ۳۸", 8.6,
                       weight="semibold", align="right", color=ACCENT)
    return d


# ==================================================================== page 3
def page_workshop(d: Doc):
    c = d.new_page(running="کارگاه جایگزین‌ها", chapter="لایه‌به‌لایه · پایان فصل ۲")

    y = TOP
    y = kicker(c, MARGIN_IN + CONTENT_W, y, "پایان فصل ۲ · بخش ۲.۹", CONTENT_W)
    y = heading(d, MARGIN_IN, y - 4, "کارگاه روش‌های جایگزین", size=23)
    y = lead(d, MARGIN_IN, y - 3,
             "در فصل ۲ برای هر گام یک روش یاد گرفتی. اینجا همان گام‌ها را با تکنیک‌های دیگر "
             "مقایسه می‌کنی. هر ردیف یک گام است؛ از راست به چپ بخوان.", CONTENT_W * 0.80) - 16

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

    weights = [52, 104, 158, 50, 54]
    total = sum(weights)
    ws = [CONTENT_W * w / total for w in weights]
    rights, xr = [], MARGIN_IN + CONTENT_W
    for w in ws:
        rights.append(xr)
        xr -= w

    # header
    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y - 20, CONTENT_W, 20, 4, stroke=0, fill=1)
    for i, label in enumerate(["", "تکنیک", "چرا بهتر است", "حرکت", "توضیح کامل"]):
        if not label:
            continue
        typo.draw_paragraph(c, rights[i] - ws[i] + 4, y - 14, label, ws[i] - 8, 7.6,
                            weight="medium", align="right" if i <= 2 else "center",
                            color=(1, 1, 1))
    y -= 30

    for title, lvl, items in rows:
        c.setFillColorRGB(*LEVEL_SOFT[lvl])
        c.roundRect(MARGIN_IN, y - 21, CONTENT_W, 21, 5, stroke=0, fill=1)
        c.setFillColorRGB(*LEVEL[lvl])
        c.roundRect(MARGIN_IN + CONTENT_W - 3.2, y - 21, 3.2, 21, 1.5, stroke=0, fill=1)
        typo.draw_paragraph(c, MARGIN_IN + 12, y - 15, title, CONTENT_W - 24, 9.0,
                            weight="bold", align="right", color=LEVEL[lvl])
        y -= 27
        for name, why, moves, page, recommended in items:
            if recommended:
                pill(c, rights[0] - 6, y + 1, "پیشنهادی", ACCENT, ACCENT_SOFT, 6.2)
            typo.draw_paragraph(c, rights[1] - ws[1] + 4, y, name, ws[1] - 8, 8.8,
                                weight="bold" if recommended else "medium",
                                align="right", color=INK)
            typo.draw_paragraph(c, rights[2] - ws[2] + 4, y + 0.5, why, ws[2] - 8, 7.6,
                                align="right", color=INK_FAINT)
            typo.draw_numerals(c, rights[3] - 4, y + 0.5, moves, 7.8, align="right",
                               color=INK_SOFT)
            typo.draw_numerals(c, rights[4] - 4, y + 0.5, "ص " + page, 8.0,
                               weight="medium", align="right", color=ACCENT)
            y -= 20
            rule(c, MARGIN_IN, y + 5, CONTENT_W)
        y -= 10

    y = kicker(c, MARGIN_IN + CONTENT_W, y, "این شماره‌ها چه کاری می‌کنند", CONTENT_W,
               color=NAVY)
    y = para(d, MARGIN_IN, y + 3,
             "هر شماره، صفحه‌ای است که آن تکنیک در آن کامل توضیح داده شده: چیستی، قدم‌ها، "
             "الگوریتم‌ها و خطاها. در نسخه‌ی وب همین شماره یک لینک می‌شود.",
             CONTENT_W * 0.78, 8.4) - 12

    chain = [("ص ۳۶", "تکنیک پایه", LEVEL["beginner"]),
             ("ص ۴۴", "جایگزین میانی", LEVEL["mid"]),
             ("ص ۵۲", "نسخه‌ی حرفه‌ای", LEVEL["pro"])]
    arw = 24
    ccw = (CONTENT_W - 2 * arw) / 3
    for i, (pg, label, col) in enumerate(chain):
        cxr = MARGIN_IN + CONTENT_W - i * (ccw + arw)
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(cxr - ccw, y - 30, ccw, 30, 5, stroke=0, fill=1)
        c.setFillColorRGB(*col)
        c.roundRect(cxr - 3.4, y - 30, 3.4, 30, 1.5, stroke=0, fill=1)
        typo.draw_numerals(c, cxr - 12, y - 13, pg, 8.8, weight="semibold", align="right",
                           color=col)
        typo.draw_paragraph(c, cxr - ccw + 10, y - 23, label, ccw - 22, 7.0,
                            align="right", color=INK_FAINT)
        if i < 2:
            ax = cxr - ccw - arw / 2
            c.setStrokeColorRGB(*INK_FAINT)
            c.setLineWidth(1.0)
            c.line(ax + 5, y - 15, ax - 5, y - 15)
            c.setFillColorRGB(*INK_FAINT)
            p = c.beginPath()
            p.moveTo(ax - 8, y - 15)
            p.lineTo(ax - 2.6, y - 12.6)
            p.lineTo(ax - 2.6, y - 17.4)
            p.close()
            c.drawPath(p, stroke=0, fill=1)

    y -= 42
    y = kicker(c, MARGIN_IN + CONTENT_W, y, "چطور انتخاب کنم؟", CONTENT_W, color=NAVY)
    criteria = [
        ("اگر تازه‌کاری", "همان ستون «پیشنهادی» را بردار و بقیه را نخوان.", LEVEL["beginner"]),
        ("اگر سرعت می‌خواهی", "تکنیکی با حرکت کمتر، حتی اگر سخت‌تر است.", LEVEL["mid"]),
        ("اگر گیر می‌کنی", "تکنیکی با خطای کمتر، نه حرکت کمتر.", LEVEL["pro"]),
    ]
    cw3 = (CONTENT_W - 20) / 3
    for i, (t, s_, col) in enumerate(criteria):
        x = MARGIN_IN + i * (cw3 + 10)
        c.setFillColorRGB(0.975, 0.977, 0.982)
        c.roundRect(x, y - 50, cw3, 50, 6, stroke=0, fill=1)
        c.setFillColorRGB(*col)
        c.roundRect(x + cw3 - 3.2, y - 50, 3.2, 50, 1.5, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 10, y - 16, t, cw3 - 22, 8.6, weight="bold",
                            align="right", color=INK)
        typo.draw_paragraph(c, x + 10, y - 30, s_, cw3 - 22, 7.6, align="right",
                            color=INK_SOFT, leading=1.8)
    y -= 62

    c.setFillColorRGB(*NAVY)
    c.roundRect(MARGIN_IN, y - 44, CONTENT_W, 44, 7, stroke=0, fill=1)
    typo.draw_paragraph(c, MARGIN_IN + 18, y - 19,
                        "قاعده: تا وقتی زیر ۶۰ ثانیه نمی‌زنی، جایگزین را عوض نکن.",
                        CONTENT_W - 36, 9.8, weight="medium", align="right", color=(1, 1, 1))
    typo.draw_paragraph(c, MARGIN_IN + 18, y - 34,
                        "اول یک تکنیک را تا حد رفلکس تمرین کن، بعد سراغ بعدی برو.",
                        CONTENT_W - 36, 8.4, align="right", color=(0.72, 0.78, 0.88))
    return d


def build(path: str):
    d = Doc(path)
    page_map(d)
    page_step(d)
    page_workshop(d)
    problems = d.check()
    d.save()
    for p in problems:
        print("LAYOUT:", p)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("wrote", build(os.path.join(OUT, "sample-pages.pdf")))
