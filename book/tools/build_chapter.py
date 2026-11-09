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
            if kind == "table":
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

    # -- page furniture
    def _paper(self):
        self.c.setFillColorRGB(*PAPER)
        self.c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    def new_page(self, furniture: bool = True):
        if self.page:
            self.c.showPage()
        self.page += 1
        self._paper()
        self.y = PAGE_H - M_TOP
        self.floats = []
        if furniture:
            self._footer()

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
        if self.y - needed < M_BOT:
            self.new_page()

    # -- text primitives
    def draw_line(self, text: str, font: str, size: float, color, justify=False,
                  right=None, left=None, leading=None):
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
        if justify and spaces and natural < avail:
            t.setWordSpace((avail - natural) / spaces)
            t.textOut(displayed)
        else:
            # right aligned
            t.setTextOrigin(right - natural, self.y)
            t.textOut(displayed)
        c.drawText(t)
        self.y -= leading if leading else size * 1.5

    FLOAT_GAP = 4.5 * mm

    def line_bounds(self, size: float, indent: float = 0.0) -> tuple[float, float]:
        """Usable horizontal span of the next line, minus any live float."""
        left = M_SIDE + indent
        right = M_SIDE + TEXT_W - indent
        top, bot = self.y + size * 0.82, self.y - size * 0.30
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
        if self.y - h < M_BOT:
            self.new_page()
        top = self.y + BODY_SIZE * 0.82
        x = M_SIDE if side == "left" else M_SIDE + TEXT_W - w
        self.c.drawImage(ImageReader(str(path)), x, top - h, w, h,
                         preserveAspectRatio=True, mask="auto")
        self.c.setStrokeColorRGB(0.78, 0.74, 0.66)
        self.c.setLineWidth(0.5)
        self.c.rect(x, top - h, w, h, stroke=1, fill=0)
        self.floats.append({"side": side, "x0": x, "x1": x + w,
                            "top": top, "bot": top - h})

    def paragraph(self, text: str, *, size=BODY_SIZE, leading=BODY_LEAD,
                  font="Vazir", color=INK, justify=True, gap=7.0,
                  indent=0.0, first_indent=0.0):
        words = [w for w in text.split(" ") if w]
        i = 0
        first = True
        guard = 0
        while i < len(words):
            guard += 1
            if guard > 4000:
                raise RuntimeError("wrap loop")
            self.ensure(leading)
            left, right = self.line_bounds(size, indent)
            if first:
                left += first_indent
            if right - left < 32 * mm:
                # too narrow beside a float: drop below it and retry
                self.clear_floats()
                continue
            avail = right - left
            line: list[str] = []
            while i < len(words):
                trial = " ".join(line + [words[i]])
                if width(trial, font, size) <= avail or not line:
                    line.append(words[i])
                    i += 1
                else:
                    break
            last = i >= len(words)
            self.draw_line(" ".join(line), font, size, color,
                           justify=justify and not last, right=right, left=left,
                           leading=leading)
            first = False
        self.y -= gap

    def heading(self, text: str):
        self.clear_floats()
        self.ensure(BODY_LEAD * 2.4)
        self.y -= 8
        key = f"sec-{self.outline_idx}"
        self.outline_idx += 1
        self.c.bookmarkPage(key)
        self.c.addOutlineEntry(text, key, level=0, closed=False)
        self.c.setFillColorRGB(*GOLD)
        self.c.rect(M_SIDE + TEXT_W - 2.2 * mm, self.y - 1.0 * mm, 2.2 * mm, 6.2 * mm,
                    stroke=0, fill=1)
        self.draw_line(text, "Vazir-Bold", 14.2, INK, justify=False,
                       right=M_SIDE + TEXT_W - 5 * mm, leading=BODY_LEAD * 1.25)
        self.y -= 3

    def quote(self, text: str):
        self.ensure(BODY_LEAD * 2)
        self.y -= 2
        self.paragraph(text, font="Vazir-Med", color=(0.24, 0.22, 0.30),
                       justify=False, indent=10 * mm, gap=8)

    def ornament(self):
        self.clear_floats()
        self.ensure(16 * mm)
        self.y -= 4 * mm
        cy = self.y + 2 * mm
        cx = PAGE_W / 2
        self.c.setStrokeColorRGB(*GOLD)
        self.c.setLineWidth(0.6)
        self.c.line(cx - 22 * mm, cy, cx - 5 * mm, cy)
        self.c.line(cx + 5 * mm, cy, cx + 22 * mm, cy)
        self.c.setFillColorRGB(*GOLD)
        self.c.circle(cx, cy, 1.1 * mm, stroke=0, fill=1)
        self.y -= 6 * mm

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

    def figure(self, image_id: str, caption: str):
        path = self.images[image_id]
        with Image.open(path) as im:
            iw, ih = im.size
        max_w = TEXT_W
        max_h = 105 * mm
        scale = min(max_w / iw, max_h / ih)
        w, h = iw * scale, ih * scale
        cap_lines = wrap(caption, "Vazir-Light", 9.4, TEXT_W - 4 * mm)
        cap_h = len(cap_lines) * 5.4 * mm + 4 * mm
        self.ensure(h + cap_h + 8 * mm)
        top = self.y + 2 * mm
        x = M_SIDE + (TEXT_W - w) / 2
        self.c.drawImage(ImageReader(str(path)), x, top - h, w, h,
                         preserveAspectRatio=True, mask="auto")
        self.c.setStrokeColorRGB(0.78, 0.74, 0.66)
        self.c.setLineWidth(0.6)
        self.c.rect(x, top - h, w, h, stroke=1, fill=0)
        self.y = top - h - 5.5 * mm
        badge = f"{image_id} — "
        first = True
        for line in cap_lines:
            text = (badge + line) if first else line
            self.draw_line(text, "Vazir-Light", 9.4, MUTED, justify=False,
                           left=M_SIDE + 2 * mm, right=M_SIDE + TEXT_W - 2 * mm,
                           leading=5.4 * mm)
            first = False
        self.y -= 5 * mm

    def table(self, rows: list[list[str]]):
        self.clear_floats()
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

        self.ensure(row_h * 3)
        draw_header()
        for r_idx, row in enumerate(body):
            if self.y - row_h < M_BOT:
                self.new_page()
                draw_header()
            if r_idx % 2 == 0:
                self.c.setFillColorRGB(0.945, 0.935, 0.91)
                self.c.rect(M_SIDE, self.y - row_h + 3.2 * mm, TEXT_W, row_h,
                            stroke=0, fill=1)
            x_right = M_SIDE + TEXT_W
            for idx, cell in enumerate(row):
                font = "Vazir-Med" if idx in (0, 2) else "Vazir"
                self.c.setFont(font, 9.6)
                self.c.setFillColorRGB(*(GOLD if idx == 2 else INK))
                self.c.drawRightString(x_right - 2.5 * mm, self.y - 2.2 * mm, shape(cell))
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
        c.setFont("Vazir-Light", 8)
        c.setFillColorRGB(0.80, 0.78, 0.74)
        c.drawCentredString(PAGE_W / 2, 12 * mm,
                            shape("تصویر آغاز فصل: تصویرسازی اختصاصی — سند تاریخی نیست"))

    def save(self):
        self.c.save()


def build_pdf(chapter_dir: Path, title: str, blocks: list[Block], images: dict[str, Path]):
    out = chapter_dir / "build" / "chapter-01-fa.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = ChapterPDF(out, title, images)
    _, _, subtitle = title.partition("|")
    pdf.opener(images["A02"], title, subtitle.strip())
    pdf.new_page()
    for block in blocks:
        if block.kind == "figure":
            placement = block.attrs.get("placement", "")
            if placement.startswith("float-"):
                side = placement.split("-", 1)[1]
                w = float(block.attrs.get("width", "60mm").replace("mm", "")) * mm
                pdf.float_figure(block.attrs["id"], side, w)
            elif placement == "inline":
                pdf.figure(block.attrs["id"], "")
            continue
        if block.kind == "heading":
            pdf.heading(block.text)
        elif block.kind == "quote":
            pdf.quote(block.text)
        elif block.kind == "hr":
            pdf.ornament()
        elif block.kind == "table":
            pdf.table(block.rows)
        elif block.kind in ("meta", "note", "credits", "internal"):
            # editorial furniture: never printed inside the narrative
            continue
        else:
            pdf.paragraph(block.text)
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


# ---------------------------------------------------------------- DOCX
def build_docx(chapter_dir: Path, title: str, blocks: list[Block], images: dict[str, Path]):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Mm, Pt, RGBColor

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
            color=None, space_after=6, line=1.6):
        par.alignment = align
        ppr = par._p.get_or_add_pPr()
        b = OxmlElement("w:bidi")
        b.set(qn("w:val"), "1")
        ppr.append(b)
        par.paragraph_format.space_after = Pt(space_after)
        par.paragraph_format.line_spacing = line
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

    for block in blocks:
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
                width_mm = 120
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
        elif block.kind == "heading":
            p = doc.add_paragraph()
            p.add_run(block.text)
            rtl(p, WD_ALIGN_PARAGRAPH.RIGHT, size=14, bold=True,
                color=(0x2A, 0x2C, 0x33), space_after=6)
            p.paragraph_format.space_before = Pt(12)
        elif block.kind == "quote":
            p = doc.add_paragraph()
            p.add_run(block.text)
            rtl(p, WD_ALIGN_PARAGRAPH.RIGHT, size=12, bold=True,
                color=(0x3D, 0x39, 0x4C))
            p.paragraph_format.right_indent = Mm(10)
        elif block.kind == "hr":
            p = doc.add_paragraph()
            p.add_run("\u2042")
            rtl(p, WD_ALIGN_PARAGRAPH.CENTER, size=12, color=(0x8C, 0x6B, 0x2E))
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
                c.text = cell
                rtl(c.paragraphs[0], WD_ALIGN_PARAGRAPH.RIGHT, size=10, bold=True)
            for row in body:
                cells = table.add_row().cells
                for idx, cell in enumerate(row):
                    cells[idx].text = cell
                    rtl(cells[idx].paragraphs[0], WD_ALIGN_PARAGRAPH.RIGHT,
                        size=10, space_after=2, line=1.3)
            doc.add_paragraph()
        elif block.kind in ("meta", "note", "credits", "internal"):
            continue
        else:
            p = doc.add_paragraph()
            p.add_run(block.text)
            rtl(p)

    footer = section.footer.paragraphs[0]
    footer.add_run(BOOK_TITLE)
    rtl(footer, WD_ALIGN_PARAGRAPH.CENTER, size=9, color=(0x6B, 0x6E, 0x78))

    out = chapter_dir / "build" / "chapter-01-fa.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
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
