"""Design system for the book: page geometry, colours, and reusable components."""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdfcanvas

import render
import typo
from cube3d import Cube

# ------------------------------------------------------------------ page
PAGE = A4
MARGIN_OUT = 46          # outer (left in a RTL book)
MARGIN_IN = 62           # gutter
MARGIN_TOP = 54
MARGIN_BOT = 56
CONTENT_W = PAGE[0] - MARGIN_OUT - MARGIN_IN

# ------------------------------------------------------------------ palette
INK = (0.11, 0.12, 0.16)
INK_SOFT = (0.36, 0.38, 0.43)
INK_FAINT = (0.62, 0.64, 0.68)
PAPER = (1.0, 1.0, 1.0)
RULE = (0.86, 0.87, 0.89)

NAVY = (0.07, 0.13, 0.24)          # premium dark
ACCENT = (0.90, 0.42, 0.13)        # signature orange
ACCENT_SOFT = (0.98, 0.93, 0.88)
TEAL = (0.06, 0.47, 0.45)

LEVEL = {                          # beginner / intermediate / advanced
    "beginner": (0.10, 0.53, 0.32),
    "mid": (0.13, 0.36, 0.66),
    "pro": (0.36, 0.16, 0.55),
}
LEVEL_SOFT = {
    "beginner": (0.90, 0.96, 0.92),
    "mid": (0.89, 0.93, 0.97),
    "pro": (0.94, 0.91, 0.97),
}
LEVEL_FA = {"beginner": "مبتدی", "mid": "متوسط", "pro": "حرفه‌ای"}


class Doc:
    def __init__(self, path: str, title: str = "آموزش حل مکعب روبیک"):
        self.c = pdfcanvas.Canvas(path, pagesize=PAGE)
        self.c.setTitle(title)
        self.page = 0
        typo.register_fonts()

    # -------------------------------------------------- page shell
    def new_page(self, running: str = "", chapter: str = "", folio: bool = True):
        if self.page:
            self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColorRGB(*PAPER)
        c.rect(0, 0, PAGE[0], PAGE[1], stroke=0, fill=1)
        if running or chapter:
            self._running_head(running, chapter)
        if folio:
            self._folio()
        return c

    def _running_head(self, running: str, chapter: str):
        """Single centred running head: 'chapter · running' in the outer margin area."""
        c = self.c
        y = PAGE[1] - MARGIN_TOP + 26
        c.setStrokeColorRGB(*RULE)
        c.setLineWidth(0.6)
        c.line(MARGIN_IN, y - 10, PAGE[0] - MARGIN_OUT, y - 10)
        parts = [p for p in (chapter, running) if p]
        if parts:
            label = " · ".join(parts)
            typo.draw_paragraph(c, MARGIN_IN, y, label, CONTENT_W, 7.8, weight="regular",
                                align="center", color=INK_FAINT)

    def _folio(self):
        c = self.c
        x = MARGIN_OUT / 2           # outer (left) margin in a right-to-left book
        c.setStrokeColorRGB(*RULE)
        c.setLineWidth(0.6)
        c.line(x - 8, MARGIN_BOT - 30, x + 8, MARGIN_BOT - 30)
        c.setFont(typo.font("semibold"), 9.5)
        c.setFillColorRGB(*INK_SOFT)
        c.drawCentredString(x, MARGIN_BOT - 42, _fa_digits(str(self.page)))

    def save(self):
        self.c.showPage()
        self.c.save()

    # -------------------------------------------------- components
    def h1_chapter(self, number: str, kicker: str, title: str, level: str = "beginner",
                   lead: str = ""):
        """Chapter opener: big number, kicker, title, lead paragraph."""
        c = self.c
        top = PAGE[1] - MARGIN_TOP - 40
        col = LEVEL.get(level, ACCENT)
        # level chip
        chip_w, chip_h = 96, 22
        c.setFillColorRGB(*LEVEL_SOFT.get(level, ACCENT_SOFT))
        c.roundRect(PAGE[0] - MARGIN_OUT - chip_w, top + 6, chip_w, chip_h, 11, stroke=0, fill=1)
        typo.draw_paragraph(c, PAGE[0] - MARGIN_OUT - chip_w, top + 14, LEVEL_FA.get(level, ""),
                            chip_w, 9, weight="medium", align="center", color=col)

        typo.draw_paragraph(c, MARGIN_IN, top - 2, kicker, CONTENT_W, 10.5,
                            weight="medium", color=col)
        # title: a large Persian line
        c.setFillColorRGB(*INK)
        y = top - 46
        y = typo.draw_paragraph(c, MARGIN_IN, y, title, CONTENT_W, 30, weight="bold",
                                leading=1.35, color=INK)
        c.setStrokeColorRGB(*col)
        c.setLineWidth(3)
        c.line(PAGE[0] - MARGIN_OUT - 54, y + 8, PAGE[0] - MARGIN_OUT, y + 8)
        if lead:
            y -= 14
            y = typo.draw_paragraph(c, MARGIN_IN, y, lead, CONTENT_W, 11.5, weight="regular",
                                    leading=1.85, color=INK_SOFT)
        return y - 22

    def h2(self, x: float, y: float, text: str, width: float = None, size: float = 15,
           color=None) -> float:
        c = self.c
        width = width or CONTENT_W
        c.setFillColorRGB(*(color or INK))
        y = typo.draw_paragraph(c, x, y, text, width, size, weight="bold", leading=1.5,
                               color=color or INK)
        return y - 2

    def body(self, x: float, y: float, text: str, width: float = None, size: float = 10.5,
             color=None, leading: float = 1.9) -> float:
        width = width or CONTENT_W
        return typo.draw_paragraph(self.c, x, y, text, width, size, leading=leading,
                                   color=color or INK_SOFT)

    def alg(self, x: float, y: float, s: str, size: float = 11.5, align: str = "left",
            color=None, weight: str = "medium", tracking: float = 0.6) -> None:
        typo.draw_latin(self.c, x, y, s, size, weight=weight, align=align,
                        color=color or INK, tracking=tracking)

    def alg_band(self, x: float, y: float, width: float, alg: str, label: str = "",
                 color=None, h: float = 30):
        """A tinted band holding an algorithm, LTR, with an optional Persian label."""
        c = self.c
        col = color or NAVY
        c.setFillColorRGB(*(0.96, 0.965, 0.98))
        c.roundRect(x, y - h + 8, width, h, 5, stroke=0, fill=1)
        c.setFillColorRGB(*col)
        c.roundRect(x + width - 3.5, y - h + 8, 3.5, h, 1.5, stroke=0, fill=1)
        self.alg(x + 12, y - h + 18, alg, size=11.5, color=col)
        if label:
            typo.draw_paragraph(c, x, y - h + 18, label, width - 12, 8.5,
                                weight="regular", align="right", color=INK_FAINT)
        return y - h - 10

    def callout(self, x: float, y: float, width: float, title: str, text: str,
                kind: str = "why", min_h: float = 0) -> float:
        """Tinted box: why it works / common mistake / note."""
        c = self.c
        palette = {
            "why": ((0.93, 0.96, 0.99), (0.13, 0.36, 0.66), "چرا کار می‌کند"),
            "warn": ((0.99, 0.94, 0.92), (0.74, 0.24, 0.15), "اشتباه رایج"),
            "note": ((0.94, 0.97, 0.94), (0.10, 0.45, 0.30), "نکته"),
        }
        bg, fg, default_title = palette.get(kind, palette["why"])
        inner = width - 26
        # measure
        head_w = typo.text_width(typo.visual(title or default_title), typo.font("bold"), 9.5)
        lines = typo.wrap_paragraph(text, inner, 9.5)
        height = 16 + 16 + len(lines) * 9.5 * 1.85 + 8
        height = max(height, min_h)
        c.setFillColorRGB(*bg)
        c.roundRect(x, y - height, width, height, 6, stroke=0, fill=1)
        c.setFillColorRGB(*fg)
        c.roundRect(x + width - 3, y - height, 3, height, 1.5, stroke=0, fill=1)
        typo.draw_paragraph(c, x + 12, y - 20, title or default_title, inner, 9.5,
                            weight="bold", align="right", color=fg)
        cy = y - 20 - 15
        self.body(x + 12, cy, text, inner, 9.5, color=(0.22, 0.24, 0.28), leading=1.85)
        return y - height - 12

    def figure(self, x: float, y_bottom: float, size: float, cube: Optional[Cube] = None,
               caption: str = "", view: str = "default", highlight=(),
               highlight_by: str = "face", shadow: bool = True) -> None:
        render.draw_cube(self.c, x, y_bottom, size, cube, view=view,
                         highlight=highlight, highlight_by=highlight_by, shadow=shadow)
        if caption:
            typo.draw_paragraph(self.c, x - 6, y_bottom - 12, caption, size + 12, 8,
                                align="center", color=INK_FAINT)

    def rule(self, y: float, x: float = None, width: float = None, color=None):
        c = self.c
        c.setStrokeColorRGB(*(color or RULE))
        c.setLineWidth(0.6)
        c.line(x if x is not None else MARGIN_IN, y,
               (x if x is not None else MARGIN_IN) + (width if width else CONTENT_W), y)

    def step_badge(self, x: float, y: float, n: str, color=None, d: float = 26):
        c = self.c
        c.setFillColorRGB(*(color or ACCENT))
        c.circle(x + d / 2, y, d / 2, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1)
        c.setFont(typo.font("bold"), 13)
        c.drawCentredString(x + d / 2, y - 4.5, _fa_digits(str(n)))


def _fa_digits(s: str) -> str:
    return s.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
