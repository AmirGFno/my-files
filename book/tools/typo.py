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
        elif align == "center":
            c.drawCentredString(x + width / 2, cy, ln.text)
        else:
            c.drawString(x, cy, ln.text)
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
