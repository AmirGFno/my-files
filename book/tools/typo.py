"""Typography layer: Persian typesetting for ReportLab.

* registers the Persian family
* paragraph = logical Persian text + inline Latin runs (algorithms) -> wrapped
  lines in VISUAL order, ready for canvas.drawString
* latin() helper for algorithm strings (always LTR, mono-ish, never reordered)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from rtl import visual

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")

FAMILY = {"regular": "Vazir", "medium": "Vazir-Med", "semibold": "Vazir-Semi", "bold": "Vazir-Bold"}
FILES = {"Vazir": "Vazirmatn-Regular.ttf", "Vazir-Med": "Vazirmatn-Medium.ttf",
         "Vazir-Semi": "Vazirmatn-SemiBold.ttf", "Vazir-Bold": "Vazirmatn-Bold.ttf"}

_registered = False


def register_fonts() -> None:
    global _registered
    if _registered:
        return
    for name, fn in FILES.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, fn)))
    _registered = True


def font(weight: str = "regular") -> str:
    register_fonts()
    return FAMILY[weight]


def text_width(s: str, fname: str, size: float) -> float:
    return pdfmetrics.stringWidth(s, fname, size)


def _is_latin(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch in "'()-+=×/.,%:[]")


def tokens(text: str) -> List[Tuple[str, bool]]:
    """Split into (chunk, is_latin) preserving spaces."""
    out: List[Tuple[str, bool]] = []
    buf, mode = "", None
    for ch in text:
        m = _is_latin(ch) or (ch == " " and mode is True)
        if m != mode and buf:
            out.append((buf, bool(mode)))
            buf = ""
        mode = m
        buf += ch
    if buf:
        out.append((buf, bool(mode)))
    return out


@dataclass
class Line:
    text: str          # visual (draw-ready) string
    width: float


def wrap_paragraph(text: str, width: float, size: float, weight: str = "regular",
                   line_gap: float = 1.75) -> List[Line]:
    """Wrap a Persian paragraph to `width` points and return visual-order lines.

    Wrapping is done in logical order (so it can break on spaces) and each line is
    then converted to visual order independently.
    """
    fname = font(weight)
    space = text_width(" ", fname, size)
    words = text.split(" ")
    lines: List[Line] = []
    current: List[str] = []
    for w in words:
        trial = " ".join(current + [w])
        if text_width(visual(trial), fname, size) <= width or not current:
            current.append(w)
        else:
            lines.append(Line(visual(" ".join(current)), text_width(visual(" ".join(current)), fname, size)))
            current = [w]
    if current:
        s = " ".join(current)
        lines.append(Line(visual(s), text_width(visual(s), fname, size)))
    return lines


def draw_paragraph(c, x: float, y: float, text: str, width: float, size: float,
                   weight: str = "regular", align: str = "right",
                   leading: float = 1.75, color=(0.12, 0.12, 0.14)) -> float:
    """Draw a right-aligned Persian paragraph with the top line's baseline at y.

    Returns the y of the next baseline.
    """
    fname = font(weight)
    c.setFont(fname, size)
    c.setFillColorRGB(*color)
    lines = wrap_paragraph(text, width, size, weight)
    cy = y
    for ln in lines:
        if align == "right":
            c.drawRightString(x + width, cy, ln.text)
            _record(x + width - ln.width, x + width, cy, cy - size * (leading - 1), text)
        elif align == "center":
            c.drawCentredString(x + width / 2, cy, ln.text)
            _record(x + width / 2 - ln.width / 2, x + width / 2 + ln.width / 2, cy,
                    cy - size * (leading - 1), text)
        else:
            c.drawString(x, cy, ln.text)
            _record(x, x + ln.width, cy, cy - size * (leading - 1), text)
        cy -= size * leading
    return cy


def draw_latin(c, x: float, y: float, s: str, size: float, weight: str = "medium",
               align: str = "left", color=(0.12, 0.12, 0.14), tracking: float = 0.6):
    """Draw an algorithm / Latin fragment left-to-right (never reordered)."""
    fname = font(weight)
    c.setFont(fname, size)
    c.setFillColorRGB(*color)
    if tracking:
        total = sum(text_width(ch, fname, size) + tracking for ch in s) - tracking
        if align == "center":
            cx = x - total / 2
        elif align == "right":
            cx = x - total
        else:
            cx = x
        for ch in s:
            c.drawString(cx, y, ch)
            cx += text_width(ch, fname, size) + tracking
        return
    if align == "center":
        c.drawCentredString(x, y, s)
    elif align == "right":
        c.drawRightString(x, y, s)
    else:
        c.drawString(x, y, s)


def latin_width(s: str, size: float, weight: str = "medium", tracking: float = 0.6) -> float:
    fname = font(weight)
    return sum(text_width(ch, fname, size) + tracking for ch in s) - tracking


def para_height(text: str, width: float, size: float, weight: str = "regular",
                leading: float = 1.9) -> float:
    """Height in points that draw_paragraph will consume for this text."""
    return len(wrap_paragraph(text, width, size, weight)) * size * leading


# ------------------------------------------------------------------ numerals
_DIGITS = set("0123456789۰۱۲۳۴۵۶۷۸۹٪%.,")


def numerals(text: str) -> str:
    """Draw-ready string for text that is mostly digits/punctuation.

    In a right-to-left paragraph a number like Page 36 must be mirrored by bidi;
    standalone numbers (table cells, ranges, counters) keep their logical order,
    otherwise "۱۲–۱۶" would print as "۱۶–۱۲".
    """
    import arabic_reshaper as _ar
    return _ar.reshape(text)


_FA_DIGITS = set("۰۱۲۳۴۵۶۷۸۹٪،؛؟")


def _has_letters(s: str) -> bool:
    """True only for real Persian letters — digits and punctuation don't count."""
    return any("\u0600" <= ch <= "\u06ff" and ch not in _FA_DIGITS for ch in s)


def smart(s: str) -> str:
    """Right string for mixed content.

    * contains Persian letters  -> full bidi (so "ص ۳۶" prints as «ص ۳۶»)
    * pure digits/punctuation   -> keep logical order (so "۱۲–۱۶" is not mirrored)
    """
    return visual(s) if _has_letters(s) else numerals(s)


def draw_smart(c, x: float, y: float, s: str, size: float, weight: str = "regular",
               align: str = "right", color=(0.36, 0.38, 0.43)) -> float:
    """Draw mixed Persian/number text correctly aligned. Returns its width."""
    fname = font(weight)
    c.setFont(fname, size)
    c.setFillColorRGB(*color)
    out = smart(s)
    w = pdfmetrics.stringWidth(out, fname, size)
    if align == "right":
        c.drawRightString(x, y, out)
    elif align == "center":
        c.drawCentredString(x, y, out)
    else:
        c.drawString(x, y, out)
    _record(x - w if align == "right" else (x - w / 2 if align == "center" else x),
            x if align == "right" else (x + w / 2 if align == "center" else x + w),
            y, y - size * 0.75, s)
    return w


def draw_numerals(c, x: float, y: float, s: str, size: float, weight: str = "regular",
                  align: str = "right", color=(0.36, 0.38, 0.43)) -> None:
    fname = font(weight)
    c.setFont(fname, size)
    c.setFillColorRGB(*color)
    out = numerals(s)
    if align == "right":
        c.drawRightString(x, y, out)
    elif align == "center":
        c.drawCentredString(x, y, out)
    else:
        c.drawString(x, y, out)


# ------------------------------------------------------------------ measuring
def text_height(text: str, width: float, size: float, weight: str = "regular",
                leading: float = 1.9) -> float:
    if not text:
        return 0.0
    return len(wrap_paragraph(text, width, size, weight)) * size * leading


def fit_size(text: str, width: float, weight: str = "bold", start: float = 28,
             minimum: float = 14, leading: float = 1.4) -> float:
    """Largest font size at which `text` wraps into at most two lines."""
    s = start
    while s > minimum:
        if len(wrap_paragraph(text, width, s, weight)) <= 2:
            return s
        s -= 1
    return minimum


def one_line_width(text: str, width: float, size: float, weight="regular") -> float:
    """Shrink `size` until `text` fits on one line."""
    s = size
    while s > 5:
        if len(wrap_paragraph(text, width, s, weight)) == 1:
            return s
        s -= 0.5
    return 5


# ------------------------------------------------------------------ layout lint
TRACE: list = []          # (page, x_left, x_right, y_baseline, bottom_y, text)
_PAGE = [0]


def set_page(n: int) -> None:
    _PAGE[0] = n
    TRACE.clear()


def _record(x0, x1, y, bottom, text):
    TRACE.append((_PAGE[0], x0, x1, y, bottom, text))


def report(bounds) -> list:
    """Return human-readable layout violations for the current page."""
    x_min, x_max, y_min, y_max = bounds
    out = []
    for page, x0, x1, y, bottom, text in TRACE:
        if bottom < y_min - 0.5:
            out.append(f"page {page}: text below the bottom margin ({bottom:.0f} < {y_min:.0f}): {text[:40]}")
        if y > y_max + 0.5:
            out.append(f"page {page}: text above the top margin ({y:.0f} > {y_max:.0f}): {text[:40]}")
        if x1 > x_max + 0.5:
            out.append(f"page {page}: text past the right margin ({x1:.0f} > {x_max:.0f}): {text[:40]}")
        if x0 < x_min - 0.5:
            out.append(f"page {page}: text past the left margin ({x0:.0f} < {x_min:.0f}): {text[:40]}")
    return out
