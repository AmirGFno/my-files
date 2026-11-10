#!/usr/bin/env python3
"""Build a Persian RTL chapter (PDF + DOCX) from the chapter Markdown source.

Usage:
    .venv/bin/python book/tools/build_chapter.py book/chapters/ch01

Requires: reportlab, arabic-reshaper, python-bidi, Pillow, python-docx
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
FONT_DIR = ROOT / "book" / "assets" / "fonts"
BOOK_TITLE = "چرخه اسرارآمیز اعصار و تاریخ معنوی بشر"

FA_DIGITS = {ord(str(i)): chr(0x06F0 + i) for i in range(10)}


def fa(value) -> str:
    return str(value).translate(FA_DIGITS)


# ---------------------------------------------------------------- parsing
@dataclass
class Block:
    kind: str
    text: str = ""
    attrs: dict = field(default_factory=dict)
    rows: list = field(default_factory=list)


def parse_markdown(path: Path) -> tuple[str, list[Block]]:
    raw = path.read_text(encoding="utf-8").replace("CC BY-SA 4.0", "CC\u00a0BY-SA\u00a04.0").replace("CC BY-SA", "CC\u00a0BY-SA")
    lines = raw.splitlines()
    blocks: list[Block] = []
    title = ""
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            i += 1
            continue
        if line.startswith(":::"):
            head = line[3:].strip()
            kind, *rest = head.split()
            attrs = dict(tok.split("=", 1) for tok in rest if "=" in tok)
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith(":::"):
                body.append(lines[i].rstrip())
                i += 1
            i += 1
            if kind == "footnotes":
                notes = {}
                for r in body:
                    if r.strip():
                        num, _, val = r.partition("|")
                        notes[num.strip()] = val.strip()
                blocks.append(Block("footnotes", attrs=notes))
            elif kind == "table":
                rows = [[c.strip() for c in r.split("|")] for r in body if r.strip()]
                blocks.append(Block("table", attrs=attrs, rows=rows))
            elif kind == "figure":
                blocks.append(Block("figure", "\n".join(body).strip(), attrs))
            elif kind == "meta":
                blocks.append(Block("meta", "\n".join(body).strip(), attrs))
            else:
                blocks.append(Block(kind, "\n".join(body).strip(), attrs))
            continue
        if line.startswith("## "):
            blocks.append(Block("heading", line[3:].strip()))
            i += 1
            continue
        if line.startswith("> "):
            blocks.append(Block("quote", line[2:].strip()))
            i += 1
            continue
        if line.strip() == "---":
            blocks.append(Block("hr"))
            i += 1
            continue
        blocks.append(Block("para", line.strip()))
        i += 1
    return title, blocks


# ---------------------------------------------------------------- images
IMAGE_SOURCES = {
    "A02": ROOT / "book/images/originals/A02_ch01_opener.jpg",
    "A17": ROOT / "book/images/originals/A17_ch01_inner.jpg",
    "H01": ROOT / "book/images/historical/H01_CH01_antikythera-mechanism.jpg",
    "H46": ROOT / "book/images/historical/H46_CH01_prague-orloj-dial.jpg",
    "H45": ROOT / "book/chapters/ch01/images/historical/H45_CH01_dunhuang-star-chart.png",
}


def prepare_images(chapter_dir: Path, ids: list[str]) -> dict[str, Path]:
    out_dir = chapter_dir / "images" / "print"
    out_dir.mkdir(parents=True, exist_ok=True)
    prepared = {}
    # smooth top-to-bottom scrim used behind the chapter title
    scrim_path = out_dir / "_opener_scrim.png"
    sw, sh = 600, 900
    scrim = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    px = scrim.load()
    for yy in range(sh):
        frac = yy / (sh - 1)
        alpha = int(round(215 * max(0.0, 1.0 - frac) ** 1.25))
        for xx in range(sw):
            px[xx, yy] = (10, 12, 17, alpha)
    scrim.save(scrim_path)
    prepared["_scrim"] = scrim_path
    for image_id in ids:
        src = IMAGE_SOURCES[image_id]
        if not src.exists():
            raise FileNotFoundError(src)
        dst = out_dir / f"{image_id}_print.jpg"
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((2200, 2200), Image.LANCZOS)
            im.save(dst, "JPEG", quality=90, optimize=True)
        prepared[image_id] = dst
    return prepared


# ---------------------------------------------------------------- shaping
_reshaper = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": True,
        "RIAL SIGN": True,
    }
)


def shape(text: str) -> str:
    # base_dir='R' keeps Persian base direction even when a line starts with
    # a Latin token (figure ids, licences, photographer names).
    return get_display(_reshaper.reshape(text), base_dir="R")


def width(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(shape(text), font, size)


def wrap(text: str, font: str, size: float, max_w: float) -> list[str]:
    words = [w for w in text.split(" ") if w]
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if width(trial, font, size) <= max_w or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


# ---------------------------------------------------------------- PDF
PAGE_W, PAGE_H = 210 * mm, 297 * mm
M_SIDE, M_TOP, M_BOT = 22 * mm, 20 * mm, 20 * mm
TEXT_W = PAGE_W - 2 * M_SIDE
BODY_SIZE = 12.2
BODY_LEAD = 21.5
INK = (0.13, 0.14, 0.17)
MUTED = (0.42, 0.44, 0.49)
GOLD = (0.55, 0.42, 0.18)
PAPER = (0.985, 0.98, 0.965)
DARK = (0.07, 0.08, 0.11)


class ChapterPDF:
    def __init__(self, out_path: Path, title: str, images: dict[str, Path]):
        for name, file in [
            ("Vazir", "Vazirmatn-Regular.ttf"),
            ("Vazir-Med", "Vazirmatn-Medium.ttf"),
            ("Vazir-Bold", "Vazirmatn-Bold.ttf"),
            ("Vazir-Light", "Vazirmatn-Light.ttf"),
        ]:
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / file)))
        self.c = canvas.Canvas(str(out_path), pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle(title)
        self.c.setAuthor(BOOK_TITLE)
        self.c.setSubject("فصل یکم — نسخه صفحه‌آرایی‌شده")
        self.title = title
        self.images = images
        self.y = PAGE_H - M_TOP
        self.page = 0
        self.outline_idx = 0
        self.floats: list[dict] = []
        self._last_divider = True   # nothing printed yet
        self.footnote_defs: dict[str, str] = {}
        self.page_notes: list[tuple[str, str]] = []
        self.bottom_limit = M_BOT

    # -- page furniture
    def _paper(self):
        self.c.setFillColorRGB(*PAPER)
        self.c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    def new_page(self, furniture: bool = True):
        if self.page:
            self._flush_notes()
            self.c.showPage()
        self.page += 1
        self._paper()
        self.y = PAGE_H - M_TOP
        self.floats = []
        self.page_notes = []
        self.bottom_limit = M_BOT
        if furniture:
            self._footer()

    NOTE_SIZE = 6.6
    NOTE_LEAD = 3.5 * mm
    NOTE_COLS = 4

    def note_band_height(self, count: int) -> float:
        rows = (count + self.NOTE_COLS - 1) // self.NOTE_COLS
        return 3.0 * mm + rows * self.NOTE_LEAD + 1.5 * mm

    def reserve_notes(self, numbers: list[str]):
        """Hold a strip at the foot of the current page for these footnotes."""
        pending = [n for n in numbers if n not in {x[0] for x in self.page_notes}]
        if not pending:
            return
        h = self.note_band_height(len(self.page_notes) + len(pending))
        self.bottom_limit = M_BOT + h
        self.page_notes.extend((n, self.footnote_defs.get(n, "")) for n in pending)

    def _flush_notes(self):
        if not self.page_notes:
            return
        top = self.bottom_limit - 1.0 * mm
        self.c.setStrokeColorRGB(0.80, 0.77, 0.70)
        self.c.setLineWidth(0.4)
        self.c.line(M_SIDE + TEXT_W * 0.62, top, M_SIDE + TEXT_W, top)
        col_w = TEXT_W / self.NOTE_COLS
        y = top - 3.4 * mm
        for idx, (num, val) in enumerate(self.page_notes):
            row, col = divmod(idx, self.NOTE_COLS)
            x_right = M_SIDE + TEXT_W - col * col_w - 1.5 * mm
            self.c.setFont("Vazir-Light", self.NOTE_SIZE)
            self.c.setFillColorRGB(*MUTED)
            # Latin term + Persian numeral: draw in logical order, no bidi pass
            self.c.drawRightString(x_right, y - row * self.NOTE_LEAD,
                                   f"{fa(num)}. {val}")

    def _footer(self):
        c = self.c
        c.setStrokeColorRGB(0.82, 0.79, 0.72)
        c.setLineWidth(0.5)
        c.line(M_SIDE, M_BOT - 6 * mm, PAGE_W - M_SIDE, M_BOT - 6 * mm)
        c.setFont("Vazir-Light", 8.5)
        c.setFillColorRGB(*MUTED)
        c.drawRightString(PAGE_W - M_SIDE, M_BOT - 12 * mm, shape(BOOK_TITLE))
        c.setFont("Vazir-Med", 9.5)
        c.drawString(M_SIDE, M_BOT - 12 * mm, shape(fa(self.page)))

    def ensure(self, needed: float):
        if self.y - needed < self.bottom_limit:
            self.new_page()

    # -- text primitives
    def draw_line(self, text: str, font: str, size: float, color, justify=False,
                  right=None, left=None, leading=None):
        self._last_divider = False
        right = M_SIDE + TEXT_W if right is None else right
        left = M_SIDE if left is None else left
        avail = right - left
        displayed = shape(text)
        natural = pdfmetrics.stringWidth(displayed, font, size)
        c = self.c
        c.setFillColorRGB(*color)
        t = c.beginText()
        t.setTextOrigin(left, self.y)
        t.setFont(font, size)
        spaces = text.count(" ")
        # PDF word spacing (Tw) lives in the text state and survives BT/ET, so it
        # must be reset explicitly on every line or justified spacing leaks into
        # the following right-aligned lines and pushes them past the margin.
        if justify and spaces and natural < avail:
            t.setWordSpace((avail - natural) / spaces)
            t.textOut(displayed)
        else:
            t.setWordSpace(0)
            t.setTextOrigin(right - natural, self.y)
            t.textOut(displayed)
        c.drawText(t)
        self.y -= leading if leading else size * 1.5

    FLOAT_GAP = 4.5 * mm

    def line_bounds(self, size: float, indent: float = 0.0) -> tuple[float, float]:
        """Usable horizontal span of the next line, minus any live float."""
        left = M_SIDE + indent
        right = M_SIDE + TEXT_W - indent
        top, bot = self.y + size * 1.05 + 1.0, self.y - size * 0.35 - 1.0
        for f in self.floats:
            if top > f["bot"] and bot < f["top"]:
                if f["side"] == "left":
                    left = max(left, f["x1"] + self.FLOAT_GAP)
                else:
                    right = min(right, f["x0"] - self.FLOAT_GAP)
        return left, right

    def clear_floats(self):
        if self.floats:
            self.y = min(self.y, min(f["bot"] for f in self.floats) - 3 * mm)
            self.floats = []

    def float_figure(self, image_id: str, side: str, width_mm: float):
        """Place a small image flush to one margin; following text wraps around it."""
        path = self.images[image_id]
        with Image.open(path) as im:
            iw, ih = im.size
        w = min(width_mm, TEXT_W * 0.52)
        h = w * ih / iw
        if self.y - h < self.bottom_limit:
            self.new_page()
        top = self.y + BODY_SIZE * 0.82
        x = M_SIDE if side == "left" else M_SIDE + TEXT_W - w
        self.c.drawImage(ImageReader(str(path)), x, top - h, w, h,
                         preserveAspectRatio=True, mask="auto")
        self.c.setStrokeColorRGB(0.78, 0.74, 0.66)
        self.c.setLineWidth(0.5)
        self.c.rect(x, top - h, w, h, stroke=1, fill=0)
        # 4pt keep-out margin below the plate so no glyph box can clip its corner
        self.floats.append({"side": side, "x0": x, "x1": x + w,
                            "top": top, "bot": top - h - 4.0})

    # A block of up to this many lines is never split across a page boundary.
    KEEP_WHOLE_LINES = 8
    MIN_SIDE_LINES = 2

    def _measure_paragraph(self, text, *, size, leading, font, indent,
                           first_indent, gap, tail_fit=False):
        """Dry-run the wrap so we know where the block would break, before inking.

        With tail_fit, a final line only reserves its ink descent instead of a
        full leading below the baseline. This lets a chapter's closing sentence
        sit at the foot of the page without stranding it on a near-blank page.
        """
        words = [w for w in text.split(" ") if w]
        y = self.y
        floats = [dict(f) for f in self.floats]
        lines: list[dict] = []
        page = 0
        i = 0
        first = True
        guard = 0
        while i < len(words):
            guard += 1
            if guard > 4000:
                raise RuntimeError("wrap loop")
            if not tail_fit and y - leading < self.bottom_limit:
                page += 1
                y = PAGE_H - M_TOP
                floats = []
                continue
            left, right = M_SIDE + indent, M_SIDE + TEXT_W - indent
            top, bot = y + size * 1.05 + 1.0, y - size * 0.35 - 1.0
            for f in floats:
                if top > f["bot"] and bot < f["top"]:
                    if f["side"] == "left":
                        left = max(left, f["x1"] + self.FLOAT_GAP)
                    else:
                        right = min(right, f["x0"] - self.FLOAT_GAP)
            if first:
                left += first_indent
            if right - left < 32 * mm:
                if floats:
                    y = min(y, min(f["bot"] for f in floats) - 3 * mm)
                    floats = []
                    continue
                right = left + 32 * mm
            avail = right - left
            line: list[str] = []
            j = i
            while j < len(words):
                trial = " ".join(line + [words[j]])
                if width(trial, font, size) <= avail or not line:
                    line.append(words[j])
                    j += 1
                else:
                    break
            needed = leading
            if tail_fit and j == len(words):
                needed = size * 0.35 + 1.0
            if y - needed < self.bottom_limit:
                page += 1
                y = PAGE_H - M_TOP
                floats = []
                continue
            lines.append({"text": " ".join(line), "left": left,
                          "right": right, "y": y, "page": page})
            i = j
            y -= leading
            first = False
        return lines, y - gap, page

    def paragraph(self, text: str, *, size=BODY_SIZE, leading=BODY_LEAD,
                  font="Vazir", color=INK, justify=True, gap=7.0,
                  indent=0.0, first_indent=0.0, keep_next_lines=0,
                  tail_fit=False):
        kw = dict(size=size, leading=leading, font=font, indent=indent,
                  first_indent=first_indent, gap=gap, tail_fit=tail_fit)
        if keep_next_lines:
            probe, _, _ = self._measure_paragraph(text, **kw)
            self.ensure(len(probe) * leading + gap + keep_next_lines * BODY_LEAD)
        lines, end_y, last_page = self._measure_paragraph(text, **kw)
        if not lines:
            return
        if last_page > 0:
            head = sum(1 for l in lines if l["page"] == 0)
            tail = sum(1 for l in lines if l["page"] == last_page)
            # keep short blocks intact; never strand 1 line on either side
            if (len(lines) <= self.KEEP_WHOLE_LINES
                    or head < self.MIN_SIDE_LINES or tail < self.MIN_SIDE_LINES):
                self.new_page()
                lines, end_y, last_page = self._measure_paragraph(text, **kw)
        cursor = 0
        for idx, l in enumerate(lines):
            while cursor < l["page"]:
                self.new_page()
                cursor += 1
            self.y = l["y"]
            self.draw_line(l["text"], font, size, color,
                           justify=justify and idx < len(lines) - 1,
                           right=l["right"], left=l["left"], leading=leading)
        self.y = end_y

    def divider(self):
        """The only section separator printed in the chapter: rule - dot - rule."""
        if self._last_divider:
            return
        self.clear_floats()
        self.ensure(20 * mm + 2 * BODY_LEAD)
        self.y -= 7 * mm
        cy = self.y + 2 * mm
        cx = PAGE_W / 2
        self.c.setStrokeColorRGB(*GOLD)
        self.c.setLineWidth(0.6)
        self.c.line(cx - 20 * mm, cy, cx - 4.5 * mm, cy)
        self.c.line(cx + 4.5 * mm, cy, cx + 20 * mm, cy)
        self.c.setFillColorRGB(*GOLD)
        self.c.circle(cx, cy, 0.9 * mm, stroke=0, fill=1)
        self.y -= 9 * mm
        self._last_divider = True

    def quote(self, text: str):
        self.ensure(BODY_LEAD * 2)
        self.y -= 2
        self.paragraph(text, font="Vazir-Med", color=(0.24, 0.22, 0.30),
                       justify=False, indent=10 * mm, gap=8)

    def ornament(self):
        self.divider()

    def meta_card(self, text: str):
        rows = [r for r in text.splitlines() if r.strip()]
        pad = 6 * mm
        line_h = 7.4 * mm
        h = pad * 2 + line_h * len(rows)
        self.ensure(h + 6 * mm)
        top = self.y + 2 * mm
        self.c.setFillColorRGB(0.955, 0.945, 0.92)
        self.c.setStrokeColorRGB(0.80, 0.74, 0.60)
        self.c.setLineWidth(0.7)
        self.c.roundRect(M_SIDE, top - h, TEXT_W, h, 3 * mm, stroke=1, fill=1)
        y = top - pad - 3.4 * mm
        for row in rows:
            label, _, value = row.partition(":")
            self.c.setFont("Vazir-Bold", 10.4)
            self.c.setFillColorRGB(*GOLD)
            lbl = shape(label.strip() + ":")
            self.c.drawRightString(M_SIDE + TEXT_W - pad, y, lbl)
            lw = pdfmetrics.stringWidth(lbl, "Vazir-Bold", 10.4)
            self.c.setFont("Vazir", 10.4)
            self.c.setFillColorRGB(*INK)
            val_lines = wrap(value.strip(), "Vazir", 10.4, TEXT_W - 2 * pad - lw - 4 * mm)
            self.c.drawString(M_SIDE + TEXT_W - pad - lw - 3 * mm -
                              pdfmetrics.stringWidth(shape(val_lines[0]), "Vazir", 10.4),
                              y, shape(val_lines[0]))
            y -= line_h
        self.y = top - h - 8 * mm

    def figure(self, image_id: str):
        """Full-width plate. Shrinks to fit the space left on this page instead of
        jumping to the next one; only moves if even the minimum size cannot fit."""
        self.clear_floats()
        self._last_divider = False
        path = self.images[image_id]
        with Image.open(path) as im:
            iw, ih = im.size
        room = self.y - self.bottom_limit - 9 * mm
        full_w = TEXT_W
        full_h = full_w * ih / iw
        min_w = TEXT_W * 0.45
        w = full_w
        h = full_h
        if h > room:
            if room >= min_w * ih / iw:
                h = room
                w = h * iw / ih
            else:
                self.new_page()
                room = self.y - self.bottom_limit - 9 * mm
                h = min(full_h, room)
                w = h * iw / ih
        self.ensure(h + 9 * mm)
        top = self.y + 1 * mm
        x = M_SIDE + (TEXT_W - w) / 2
        self.c.drawImage(ImageReader(str(path)), x, top - h, w, h,
                         preserveAspectRatio=True, mask="auto")
        self.c.setStrokeColorRGB(0.78, 0.74, 0.66)
        self.c.setLineWidth(0.6)
        self.c.rect(x, top - h, w, h, stroke=1, fill=0)
        self.y = top - h - 8 * mm

    def table(self, rows: list[list[str]]):
        self.clear_floats()
        self._last_divider = False
        header, *body = rows
        cols = len(header)
        weights = [0.13, 0.20, 0.26, 0.41] if cols == 4 else [1 / cols] * cols
        widths = [TEXT_W * w for w in weights]
        row_h = 8.2 * mm

        def draw_header():
            self.c.setFillColorRGB(0.16, 0.17, 0.22)
            self.c.rect(M_SIDE, self.y - row_h + 3 * mm, TEXT_W, row_h, stroke=0, fill=1)
            x_right = M_SIDE + TEXT_W
            for idx, cell in enumerate(header):
                self.c.setFont("Vazir-Med", 9.8)
                self.c.setFillColorRGB(0.97, 0.95, 0.90)
                self.c.drawRightString(x_right - 2.5 * mm, self.y - 2.4 * mm, shape(cell))
                x_right -= widths[idx]
            self.y -= row_h + 1.5 * mm

        markers = [m for r in body for m in re.findall(r"\[(\d+)\]", " ".join(r))]
        if markers:
            self.ensure(row_h * (len(body) + 1) + 14 * mm
                        + self.note_band_height(len(markers)))
            self.reserve_notes(markers)
        self.ensure(row_h * (len(body) + 1) + 14 * mm)
        draw_header()
        for r_idx, row in enumerate(body):
            if self.y - row_h < self.bottom_limit:
                self.new_page()
                draw_header()
            if r_idx % 2 == 0:
                self.c.setFillColorRGB(0.945, 0.935, 0.91)
                self.c.rect(M_SIDE, self.y - row_h + 3.2 * mm, TEXT_W, row_h,
                            stroke=0, fill=1)
            x_right = M_SIDE + TEXT_W
            for idx, cell in enumerate(row):
                font = "Vazir-Med" if idx in (0, 2) else "Vazir"
                mark = re.search(r"\[(\d+)\]", cell)
                label = re.sub(r"\[\d+\]", "", cell)
                self.c.setFont(font, 9.6)
                self.c.setFillColorRGB(*(GOLD if idx == 2 else INK))
                shown = shape(label)
                self.c.drawRightString(x_right - 2.5 * mm, self.y - 2.2 * mm, shown)
                if mark:
                    wlab = pdfmetrics.stringWidth(shown, font, 9.6)
                    self.c.setFont("Vazir-Light", 5.6)
                    self.c.setFillColorRGB(*MUTED)
                    self.c.drawRightString(x_right - 2.5 * mm - wlab - 0.5 * mm,
                                           self.y - 0.5 * mm, fa(mark.group(1)))
                x_right -= widths[idx]
            self.c.setStrokeColorRGB(0.86, 0.83, 0.77)
            self.c.setLineWidth(0.4)
            self.c.line(M_SIDE, self.y - row_h + 3.4 * mm,
                        M_SIDE + TEXT_W, self.y - row_h + 3.4 * mm)
            self.y -= row_h
        self.y -= 6 * mm

    def credits(self, text: str):
        self.new_page()
        self.heading("زیرنویس‌ها و اعتبارات تصاویر این فصل")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                self.y -= 3 * mm
                continue
            self.paragraph(line, size=10.2, leading=17.5, font="Vazir",
                           color=INK, justify=True, gap=6)

    def opener(self, image_path: Path, title: str, subtitle: str):
        self.new_page(furniture=False)
        c = self.c
        with Image.open(image_path) as im:
            iw, ih = im.size
        scale = max(PAGE_W / iw, PAGE_H / ih)
        w, h = iw * scale, ih * scale
        c.drawImage(ImageReader(str(image_path)), (PAGE_W - w) / 2, (PAGE_H - h) / 2,
                    w, h, preserveAspectRatio=True, mask="auto")
        # gradient scrim at top for legible title (pre-rendered, smooth alpha)
        scrim = self.images["_scrim"]
        c.drawImage(ImageReader(str(scrim)), 0, PAGE_H * 0.30, PAGE_W, PAGE_H * 0.70,
                    preserveAspectRatio=False, mask="auto")
        c.setFillColorRGB(0, 0, 0, alpha=1)
        c.setFillColorRGB(0.86, 0.74, 0.44)
        c.setFont("Vazir-Med", 13)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 32 * mm, shape("فصل اول"))
        c.setFillColorRGB(0.98, 0.96, 0.92)
        c.setFont("Vazir-Bold", 25)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 47 * mm, shape(subtitle))
        c.setStrokeColorRGB(0.72, 0.60, 0.33)
        c.setLineWidth(0.8)
        c.line(PAGE_W / 2 - 26 * mm, PAGE_H - 55 * mm, PAGE_W / 2 + 26 * mm, PAGE_H - 55 * mm)
        c.setFont("Vazir-Light", 10.5)
        c.setFillColorRGB(0.88, 0.86, 0.82)
        c.drawCentredString(PAGE_W / 2, PAGE_H - 63 * mm, shape(BOOK_TITLE))

    def save(self):
        self._flush_notes()
        self.c.save()


def build_pdf(chapter_dir: Path, title: str, blocks: list[Block], images: dict[str, Path]):
    out = chapter_dir / "build" / "chapter-01-fa.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = ChapterPDF(out, title, images)
    for b in blocks:
        if b.kind == "footnotes":
            pdf.footnote_defs.update(b.attrs)
    _, _, subtitle = title.partition("|")
    pdf.opener(images["A02"], title, subtitle.strip())
    pdf.c.bookmarkPage("chapter-01")
    pdf.c.addOutlineEntry(title, "chapter-01", level=0, closed=False)
    pdf.new_page()
    last_text_idx = max(
        (i for i, b in enumerate(blocks) if b.kind in ("para", "quote")),
        default=-1,
    )
    for block_idx, block in enumerate(blocks):
        if block.kind == "figure":
            placement = block.attrs.get("placement", "")
            if placement.startswith("float-"):
                side = placement.split("-", 1)[1]
                w = float(block.attrs.get("width", "60mm").replace("mm", "")) * mm
                pdf.float_figure(block.attrs["id"], side, w)
            elif placement == "inline":
                pdf.figure(block.attrs["id"])
            continue
        if block.kind == "heading":
            # section titles are never printed; they only mark a break
            pdf.divider()
        elif block.kind == "quote":
            pdf.quote(block.text)
        elif block.kind == "hr":
            pdf.ornament()
        elif block.kind == "table":
            pdf.table(block.rows)
        elif block.kind in ("meta", "note", "credits", "internal", "footnotes"):
            # editorial furniture / definitions: not printed as a block
            continue
        else:
            lead_in = block.text.rstrip().endswith(":")
            pdf.paragraph(
                block.text,
                keep_next_lines=2 if lead_in else 0,
                tail_fit=block_idx == last_text_idx,
            )
    pdf.clear_floats()
    pdf.save()
    return out, pdf.page


def docx_tight_wrap(paragraph, side: str = "left", dist_mm: float = 4.0):
    """Convert the inline picture in `paragraph` into a floating, tight-wrapped one."""
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls, qn

    inline = paragraph._p.find(".//" + qn("wp:inline"))
    if inline is None:
        return
    extent = inline.find(qn("wp:extent"))
    cx, cy = extent.get("cx"), extent.get("cy")
    dist = str(int(dist_mm * 36000))
    anchor = parse_xml(
        f'<wp:anchor {nsdecls("wp", "a", "pic", "r")} distT="0" distB="0" '
        f'distL="{dist}" distR="{dist}" simplePos="0" relativeHeight="251658240" '
        'behindDoc="0" locked="0" layoutInCell="1" allowOverlap="0">'
        '<wp:simplePos x="0" y="0"/>'
        f'<wp:positionH relativeFrom="column"><wp:align>{side}</wp:align></wp:positionH>'
        '<wp:positionV relativeFrom="paragraph"><wp:posOffset>0</wp:posOffset></wp:positionV>'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        '<wp:wrapTight wrapText="bothSides">'
        '<wp:wrapPolygon edited="0">'
        '<wp:start x="0" y="0"/><wp:lineTo x="0" y="21600"/>'
        '<wp:lineTo x="21600" y="21600"/><wp:lineTo x="21600" y="0"/>'
        '<wp:lineTo x="0" y="0"/>'
        '</wp:wrapPolygon></wp:wrapTight>'
        '</wp:anchor>'
    )
    for tag in ("wp:docPr", "wp:cNvGraphicFramePr", "a:graphic"):
        el = inline.find(qn(tag))
        if el is not None:
            anchor.append(el)
    inline.getparent().replace(inline, anchor)


def docx_add_footnotes(path: Path, notes: dict[str, str]):
    """Inject a real Word footnotes part so the terms sit at the foot of the page."""
    import shutil
    import zipfile
    from xml.sax.saxutils import escape

    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    CT = "http://schemas.openxmlformats.org/package/2006/content-types"
    sep = ('<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr>'
           '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
           '<w:r><w:separator/></w:r></w:p></w:footnote>'
           '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr>'
           '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
           '<w:r><w:continuationSeparator/></w:r></w:p></w:footnote>')
    body = []
    for num, val in sorted(notes.items(), key=lambda kv: int(kv[0])):
        body.append(
            f'<w:footnote w:id="{int(num)}"><w:p><w:pPr>'
            '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
            '<w:jc w:val="left"/></w:pPr>'
            '<w:r><w:rPr><w:vertAlign w:val="superscript"/><w:sz w:val="14"/>'
            '</w:rPr><w:footnoteRef/></w:r>'
            '<w:r><w:rPr><w:rFonts w:ascii="Vazirmatn" w:hAnsi="Vazirmatn" '
            'w:cs="Vazirmatn"/><w:sz w:val="14"/><w:szCs w:val="14"/></w:rPr>'
            f'<w:t xml:space="preserve"> {escape(val)}</w:t></w:r>'
            '</w:p></w:footnote>')
    footnotes = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 f'<w:footnotes xmlns:w="{W}">{sep}{"".join(body)}</w:footnotes>')

    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                txt = data.decode("utf-8")
                override = ('<Override PartName="/word/footnotes.xml" '
                            'ContentType="application/vnd.openxmlformats-officedocument'
                            '.wordprocessingml.footnotes+xml"/>')
                txt = txt.replace("</Types>", override + "</Types>")
                data = txt.encode("utf-8")
            elif item.filename == "word/_rels/document.xml.rels":
                txt = data.decode("utf-8")
                ids = {int(m) for m in re.findall(r'Id="rId(\d+)"', txt)}
                new_id = f"rId{max(ids) + 1 if ids else 1}"
                rel = (f'<Relationship Id="{new_id}" Type="{R}/footnotes" '
                       'Target="footnotes.xml"/>')
                txt = txt.replace("</Relationships>", rel + "</Relationships>")
                data = txt.encode("utf-8")
            elif item.filename == "word/settings.xml":
                txt = data.decode("utf-8")
                if "<w:footnotePr" not in txt:
                    pr = ('<w:footnotePr><w:numFmt w:val="hindiArabic"/>'
                          '<w:restartEachPage w:val="false"/></w:footnotePr>')
                    if "<w:compat>" in txt:
                        txt = txt.replace("<w:compat>", pr + "<w:compat>", 1)
                    else:
                        txt = txt.replace("</w:settings>", pr + "</w:settings>")
                data = txt.encode("utf-8")
            zout.writestr(item, data)
        zout.writestr("word/footnotes.xml", footnotes.encode("utf-8"))
    shutil.move(str(tmp), str(path))


# ---------------------------------------------------------------- DOCX
def build_docx(chapter_dir: Path, title: str, blocks: list[Block], images: dict[str, Path]):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor

    note_defs: dict[str, str] = {}
    for b in blocks:
        if b.kind == "footnotes":
            note_defs.update(b.attrs)
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = Mm(22)
    section.top_margin = section.bottom_margin = Mm(20)
    bidi_sec = OxmlElement("w:bidi")
    section._sectPr.append(bidi_sec)

    normal = doc.styles["Normal"]
    normal.font.name = "Vazirmatn"
    normal.font.size = Pt(12)
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), "Vazirmatn")
    szcs = OxmlElement("w:szCs")
    szcs.set(qn("w:val"), "24")
    rpr.append(szcs)

    def rtl(par, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, bold=False,
            color=None, space_after=6, line=1.6, keep_together=True,
            keep_next=False):
        par.alignment = align
        ppr = par._p.get_or_add_pPr()
        b = OxmlElement("w:bidi")
        b.set(qn("w:val"), "1")
        ppr.append(b)
        par.paragraph_format.space_after = Pt(space_after)
        par.paragraph_format.line_spacing = line
        par.paragraph_format.widow_control = True
        par.paragraph_format.keep_together = keep_together
        par.paragraph_format.keep_with_next = keep_next
        for run in par.runs:
            run.font.name = "Vazirmatn"
            r = run._element.get_or_add_rPr()
            rtl_run = OxmlElement("w:rtl")
            rtl_run.set(qn("w:val"), "1")
            r.append(rtl_run)
            cs = OxmlElement("w:szCs")
            cs.set(qn("w:val"), str(int((size or 12) * 2)))
            r.append(cs)
            if bold:
                run.bold = True
                bcs = OxmlElement("w:bCs")
                r.append(bcs)
            if size:
                run.font.size = Pt(size)
            if color:
                run.font.color.rgb = RGBColor(*color)
        return par

    _, _, subtitle = title.partition("|")
    p = doc.add_paragraph()
    p.add_run("فصل اول")
    rtl(p, WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, color=(0x8C, 0x6B, 0x2E))
    p = doc.add_paragraph()
    p.add_run(subtitle.strip())
    rtl(p, WD_ALIGN_PARAGRAPH.CENTER, size=22, bold=True, space_after=14)

    last_divider = True
    for block in blocks:
        if block.kind in ("meta", "note", "credits", "internal", "footnotes"):
            continue
        if block.kind == "figure" and block.attrs.get("placement") == "opener":
            pass
        elif block.kind not in ("heading", "hr"):
            last_divider = False
        if block.kind == "figure":
            image_id = block.attrs["id"]
            placement = block.attrs.get("placement", "")
            p = doc.add_paragraph()
            rtl(p, WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
            run = p.add_run()
            with Image.open(images[image_id]) as im:
                iw, ih = im.size
            if placement.startswith("float-"):
                width_mm = min(float(block.attrs.get("width", "60mm").replace("mm", "")), 82)
            elif placement == "opener":
                width_mm = 150
            else:
                width_mm = 166
            height_mm = width_mm * ih / iw
            if height_mm > 150:
                height_mm = 150
                width_mm = height_mm * iw / ih
            run.add_picture(str(images[image_id]), width=Mm(width_mm))
            if placement.startswith("float-"):
                docx_tight_wrap(p, placement.split("-", 1)[1])
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.line_spacing = Pt(1)
        elif block.kind in ("heading", "hr"):
            if last_divider:
                continue
            p = doc.add_paragraph()
            p.add_run("\u2014  \u066d  \u2014")
            rtl(p, WD_ALIGN_PARAGRAPH.CENTER, size=12, color=(0x8C, 0x6B, 0x2E),
                space_after=10, line=1.2, keep_next=True)
            p.paragraph_format.space_before = Pt(10)
            last_divider = True
        elif block.kind == "quote":
            p = doc.add_paragraph()
            p.add_run(block.text)
            rtl(p, WD_ALIGN_PARAGRAPH.RIGHT, size=12, bold=True,
                color=(0x3D, 0x39, 0x4C))
            p.paragraph_format.right_indent = Mm(10)
        elif block.kind == "table":
            header, *body = block.rows
            table = doc.add_table(rows=1, cols=len(header))
            table.style = "Light Grid Accent 1"
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            tblpr = table._tbl.tblPr
            bidi_vis = OxmlElement("w:bidiVisual")
            tblpr.append(bidi_vis)
            for idx, cell in enumerate(header):
                c = table.rows[0].cells[idx]
                c.paragraphs[0].add_run(cell)
                rtl(c.paragraphs[0], WD_ALIGN_PARAGRAPH.RIGHT, size=10, bold=True,
                    keep_next=True)
            for r_idx, row in enumerate(body):
                cells = table.add_row().cells
                for idx, cell in enumerate(row):
                    para = cells[idx].paragraphs[0]
                    mark = re.search(r"\[(\d+)\]", cell)
                    para.add_run(re.sub(r"\[\d+\]", "", cell))
                    if mark:
                        run = para.add_run()
                        run.font.superscript = True
                        ref = OxmlElement("w:footnoteReference")
                        ref.set(qn("w:id"), mark.group(1))
                        run._r.append(ref)
                    rtl(para, WD_ALIGN_PARAGRAPH.RIGHT, size=10, space_after=2,
                        line=1.3, keep_next=r_idx < len(body) - 1)
            for row in table.rows:
                cant = OxmlElement("w:cantSplit")
                row._tr.get_or_add_trPr().append(cant)
            doc.add_paragraph()
        else:
            p = doc.add_paragraph()
            p.add_run(block.text)
            rtl(p, keep_next=block.text.rstrip().endswith(":"))

    footer = section.footer.paragraphs[0]
    footer.add_run(BOOK_TITLE)
    rtl(footer, WD_ALIGN_PARAGRAPH.CENTER, size=9, color=(0x6B, 0x6E, 0x78))

    out = chapter_dir / "build" / "chapter-01-fa.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    used = {m for b in blocks if b.kind == "table"
            for r in b.rows for m in re.findall(r"\[(\d+)\]", " ".join(r))}
    if used:
        docx_add_footnotes(out, {k: v for k, v in note_defs.items() if k in used})
    return out


def main():
    chapter_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "book/chapters/ch01")
    chapter_dir = chapter_dir.resolve()
    src = chapter_dir / "chapter-01.md"
    title, blocks = parse_markdown(src)
    ids = [b.attrs["id"] for b in blocks if b.kind == "figure"]
    images = prepare_images(chapter_dir, ids)
    pdf_path, pages = build_pdf(chapter_dir, title, blocks, images)
    docx_path = build_docx(chapter_dir, title, blocks, images)
    credits = [b.text for b in blocks if b.kind == "credits"]
    if credits:
        cpath = chapter_dir / "build" / "image-credits.md"
        cpath.write_text("# اعتبارات تصاویر فصل یکم\n\n"
                         "این فهرست داخل روایت چاپ نمی‌شود؛ در پایان‌نامهٔ منابعِ کتاب ادغام خواهد شد.\n\n"
                         + "\n\n".join(credits) + "\n", encoding="utf-8")
    words = len(re.findall(r"\S+", " ".join(b.text for b in blocks if b.kind in
                                          ("para", "quote", "heading"))))
    print(f"PDF : {pdf_path.relative_to(ROOT)}  ({fa(pages)} pages)")
    print(f"DOCX: {docx_path.relative_to(ROOT)}")
    print(f"Narrative words: {fa(words)} | figures: {', '.join(ids)}")
    print("Credits: build/image-credits.md (not printed inside the chapter)")


if __name__ == "__main__":
    main()
