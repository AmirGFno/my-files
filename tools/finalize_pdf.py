#!/usr/bin/env python3
"""Stage 4 — final build.

  1. white bar over the right margin strip that carries the vertical
     @KECHAP_BOOK watermark band (from page BAR_FROM on). The bar never covers
     printed ink: if a page has text in the strip, the bar starts after it.
  2. bolder print: black/white level stretch + gamma so letters read darker
     while paper stays paper.
  3. PDF below the 100 MB GitHub limit: every scan is re-encoded as JPEG (colour
     kept when it fits the budget) and the quality is lowered until the whole
     file fits.

Geometry and resolution never change: pixels stay 1:1, only codec + tone
curve. Nothing is re-rendered by a PDF rasteriser.

Usage: finalize_pdf.py SRC.pdf OUT.pdf [report.txt]
Env:   BAR_FROM=4  BAR_START_PT=558  BUDGET_MB=96  Q_TOP=86  Q_BOTTOM=64
"""
import hashlib
import os
import re
import sys

import numpy as np
import pymupdf

SRC = sys.argv[1]
OUT = sys.argv[2]
REPORT = sys.argv[3] if len(sys.argv) > 3 else "final_report.txt"

BAR_FROM = int(os.environ.get("BAR_FROM", 4))
BAR_START_PT = float(os.environ.get("BAR_START_PT", 560.0))
BUDGET = float(os.environ.get("BUDGET_MB", 96)) * 1048576
Q_TOP = int(os.environ.get("Q_TOP", 86))
Q_BOTTOM = int(os.environ.get("Q_BOTTOM", 64))
Q_STEP = int(os.environ.get("Q_STEP", 4))
OVERHEAD = 1 * 1048576

BP, WP, GAMMA = 26.0, 238.0, 1.28          # bold curve for paper pages
BP_C, WP_C, GAMMA_C = 10.0, 246.0, 1.06    # gentle curve for colour pages
INK = 120
COLOUR_SAT = 40
COLOUR_SHARE = 0.002
LINE_FRACTION = 0.80        # a column this "inked" over the full height = line
LINE_MAX_WIDTH = 8
RENDER_PAGES = (4, 151, 283)


# ------------------------------------------------------------------ pdf utils
def image_xref(doc, page):
    imgs = [i for i in page.get_images(full=True) if i[7] == "I0"]
    imgs = imgs or page.get_images(full=True)
    return imgs[0][0] if imgs else None


def unshare(doc):
    """give every page its own copy of a shared scan object"""
    seen, cloned = set(), 0
    for page in doc:
        xref = image_xref(doc, page)
        if xref is None:
            continue
        if xref in seen:
            new = doc.get_new_xref()
            doc.update_object(new, doc.xref_object(xref))
            doc.update_stream(new, doc.xref_stream(xref), compress=False)
            doc.xref_set_key(page.xref, "Resources",
                             "<< /XObject << /I0 %d 0 R >> >>" % new)
            cloned += 1
        else:
            seen.add(xref)
    return cloned


def decode(doc, xref):
    pm = pymupdf.Pixmap(doc, xref)
    if pm.colorspace is None or pm.colorspace.n != 3:
        pm = pymupdf.Pixmap(pymupdf.csRGB, pm)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 3)


def page_width_pt(page):
    s = page.read_contents()
    m = re.search(rb"q\s+([-\d\.]+)\s+[-\d\.]+\s+[-\d\.]+\s+[-\d\.]+\s+"
                  rb"[-\d\.]+\s+[-\d\.]+\s+cm", s)
    return abs(float(m.group(1))) if m else page.rect.width


def jpeg(plane, quality):
    if plane.ndim == 2:
        pm = pymupdf.Pixmap(pymupdf.csGRAY, plane.shape[1], plane.shape[0],
                            np.ascontiguousarray(plane).tobytes(), 0)
    else:
        pm = pymupdf.Pixmap(pymupdf.csRGB, plane.shape[1], plane.shape[0],
                            np.ascontiguousarray(plane).tobytes(), 0)
    return pm.tobytes("jpeg", jpg_quality=quality)


def write_image(doc, xref, data, grey, w, h):
    doc.update_stream(xref, data, compress=False)
    doc.xref_set_key(xref, "Filter", "/DCTDecode")
    doc.xref_set_key(xref, "ColorSpace", "/DeviceGray" if grey else "/DeviceRGB")
    doc.xref_set_key(xref, "BitsPerComponent", "8")
    doc.xref_set_key(xref, "Width", str(w))
    doc.xref_set_key(xref, "Height", str(h))
    for key in ("DecodeParms", "SMask", "Mask", "Decode"):
        doc.xref_set_key(xref, key, "null")


# --------------------------------------------------------------- image logic
def bolden(arr, colour_page):
    a = arr.astype(np.float32)
    if colour_page:
        x = np.clip((a - BP_C) / (WP_C - BP_C), 0, 1) ** GAMMA_C
        return (x * 255.0 + 0.5).astype(np.uint8)
    g = a.mean(axis=2)
    x = np.clip((g - BP) / (WP - BP), 0, 1) ** GAMMA
    return (x * 255.0 + 0.5).astype(np.uint8)


SCAN_BORDER = int(os.environ.get("SCAN_BORDER", 14))


def bar_start_px(plane_gray, cand):
    """x where the white bar may start without eating printed ink

    The scanner leaves a thin dark border on the outer few pixels; that is not
    content, so it is ignored when looking for printed ink.
    """
    W = plane_gray.shape[1]
    stop = max(cand + 4, W - SCAN_BORDER)
    if cand >= stop - 1:
        return cand if cand < W - 3 else 0
    ink = plane_gray[:, cand:stop] < 140
    if not ink.any():
        return cand
    col_frac = ink.mean(axis=0)
    solid = col_frac > LINE_FRACTION
    # grow the solid line runs and mask them out
    real = ~solid
    i = 0
    n = len(solid)
    while i < n:
        if solid[i]:
            j = i
            while j < n and solid[j]:
                j += 1
            if j - i <= LINE_MAX_WIDTH:
                real[i:j] = False        # thin vertical line: safe to whiten
            i = j
        else:
            i += 1
    if not real.any():
        return cand
    return min(W - 4, cand + int(np.nonzero(real)[0].max()) + 3)


def build_plane(arr, x0, colour_page, keep_colour):
    out = bolden(arr, colour_page)
    if x0:
        out[:, x0:] = 255
    if keep_colour:
        return out
    return out.mean(axis=2).astype(np.uint8) if out.ndim == 3 else out


def main():
    doc = pymupdf.open(SRC)
    total = doc.page_count
    cloned = unshare(doc)
    if cloned:
        print(f"unshared {cloned} shared scan objects", flush=True)

    pages = []
    for page in doc:
        xref = image_xref(doc, page)
        if xref is None:
            continue
        w = int(doc.xref_get_key(xref, "Width")[1])
        h = int(doc.xref_get_key(xref, "Height")[1])
        arr = decode(doc, xref)
        g = arr.astype(np.float32).mean(axis=2)
        colour_page = float((g > 215).mean()) < 0.5
        sat = arr.max(axis=2).astype(np.int16) - arr.min(axis=2).astype(np.int16)
        has_colour = float(((sat > COLOUR_SAT) & (g < 245)).mean()) > COLOUR_SHARE
        x0 = 0
        if page.number + 1 >= BAR_FROM and not colour_page:
            cand = int(round(BAR_START_PT / page_width_pt(page) * w))
            x0 = bar_start_px(g, min(max(cand, 0), w - 3))
        pages.append({"no": page.number + 1, "xref": xref, "w": w, "h": h,
                      "colour_page": colour_page, "has_colour": has_colour,
                      "x0": x0})
        if len(pages) % 60 == 0:
            print(f"  prepared {len(pages)} pages", flush=True)

    n_bar = sum(1 for p in pages if p["x0"])
    n_col = sum(1 for p in pages if p["has_colour"])
    print(f"pages={total} with_image={len(pages)} bar_pages={n_bar} "
          f"colour_pages={n_col}", flush=True)

    # ---- choose quality: one pass, all candidates at once ------------------
    candidates = [(True, q) for q in range(Q_TOP, Q_BOTTOM - 1, -Q_STEP)]
    candidates += [(False, q) for q in range(Q_TOP, Q_BOTTOM - 4, -Q_STEP)]
    totals = {c: 0 for c in candidates}
    for i, p in enumerate(pages):
        arr = decode(doc, p["xref"])          # decoded once, then discarded
        for keep_colour, q in candidates:
            plane = build_plane(arr, p["x0"], p["colour_page"],
                                keep_colour and p["has_colour"])
            totals[(keep_colour, q)] += len(jpeg(plane, q))
        del arr
        if i % 40 == 0:
            print(f"  measuring {i + 1}/{len(pages)}", flush=True)

    chosen = None
    for c in candidates:
        est = totals[c] + OVERHEAD
        print(f"  colour={c[0]} q={c[1]}: {est / 1048576:.1f} MiB", flush=True)
        if est <= BUDGET:
            chosen = c
            break
    if chosen is None:
        chosen = candidates[-1]
        print("  WARNING: budget not reached", flush=True)
    keep_colour, quality = chosen
    print(f"chosen: colour={keep_colour} q={quality}", flush=True)

    # ---- write ------------------------------------------------------------
    for i, p in enumerate(pages):
        arr = decode(doc, p["xref"])
        plane = build_plane(arr, p["x0"], p["colour_page"],
                            keep_colour and p["has_colour"])
        write_image(doc, p["xref"], jpeg(plane, quality), plane.ndim == 2,
                    p["w"], p["h"])
        del arr, plane
        if p["no"] % 50 == 0:
            print(f"  wrote page {p['no']}", flush=True)

    doc.save(OUT, garbage=4, deflate=True)
    doc.close()

    # ---- validate ---------------------------------------------------------
    chk = pymupdf.open(OUT)
    src = pymupdf.open(SRC)
    size = os.path.getsize(OUT)

    def img(d, pno):
        page = d[pno - 1]
        return decode(d, image_xref(d, page))

    bar_rows, bar_bad = [], []
    for p in pages:
        if not p["x0"]:
            continue
        g = img(chk, p["no"]).astype(np.float32).mean(axis=2)
        seg = g[:, p["x0"]:]
        dark = float((seg < 200).mean())
        bar_rows.append((p["no"], p["x0"], float(seg.min()), dark))
        if dark > 0.002 or seg.min() < 170:
            bar_bad.append((p["no"], round(dark, 5), float(seg.min())))

    samples = [p for p in (1, 61, 151, 250, 283) if p <= total]
    ink_rows = []
    for pno in samples:
        for label, d in (("before", src), ("after", chk)):
            g = img(d, pno).astype(np.float32).mean(axis=2)
            ink = g < INK
            ink_rows.append((pno, label,
                             float(ink.mean()),
                             float((g < 190).mean()),
                             float(g[ink].mean()) if ink.any() else 255.0))

    for pno in RENDER_PAGES:
        if pno <= chk.page_count:
            chk[pno - 1].get_pixmap(dpi=90).save(f"final_p{pno}.png")

    pages_after = chk.page_count
    chk.close()
    src.close()

    sha = hashlib.sha256()
    with open(OUT, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    digest = sha.hexdigest()

    ok = size < 100 * 1048576 and pages_after == total and not bar_bad
    lines = [
        "FINAL REPORT (stage 4)",
        "======================",
        f"source          : {os.path.basename(SRC)}",
        f"output          : {os.path.basename(OUT)}",
        f"size            : {size:,} bytes ({size / 1048576:.2f} MiB)",
        f"under 100 MiB   : {'YES' if size < 100 * 1048576 else 'NO'}",
        f"pages           : {pages_after}",
        f"codec           : JPEG, colour_kept={keep_colour}, q={quality}",
        f"sha256          : {digest}",
        "",
        f"white bar       : {len(bar_rows)} paper pages from page {BAR_FROM} "
        f"(start {BAR_START_PT} pt); colour pages skipped (artwork would be cut)",
        f"bar fully white : {'YES' if not bar_bad else 'NO'}",
    ]
    for pno, x0, mn, dark in bar_rows[:5]:
        lines.append(f"  page {pno:>3} x0={x0:>4} min_gray={mn:5.0f} "
                     f"dark_frac={dark:.5f}")
    if bar_bad:
        lines.append(f"  pages with ink in the bar: {bar_bad[:8]}")
    lines += ["",
              "ink metrics on the embedded scan (bolder => cov grows, "
              "mean_ink falls):",
              f"  {'page':>4} {'when':>6} {'cov<120':>9} {'cov<190':>9} "
              f"{'mean_ink':>9}"]
    for pno, label, cov, cov190, mean_ink in ink_rows:
        lines.append(f"  {pno:>4} {label:>6} {cov * 100:8.2f}% "
                     f"{cov190 * 100:8.2f}% {mean_ink:9.1f}")
    lines += ["", "RESULT: " + ("PASS" if ok else "REVIEW NEEDED")]

    txt = "\n".join(lines)
    print(txt)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    if not ok:
        sys.exit(3)


if __name__ == "__main__":
    main()
