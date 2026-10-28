#!/usr/bin/env python3
"""Stage 4 — final polish.

  1. white bar over the right-hand margin strip where the @KECHAP_BOOK
     watermark band used to sit (from page BAR_FROM on).
  2. bolder print: black/white level stretch + gamma, so letters read darker
     while the paper stays paper.
  3. PDF below the 100 MB GitHub limit: pages are stored as JPEG (grey for
     paper pages, RGB where colour matters) and the quality is lowered
     automatically until the whole file fits the budget.

Resolution and geometry never change (no re-render, no resampling); only the
codec and the tone curve.

Usage: finalize_pdf.py SRC.pdf OUT.pdf [report.txt]
Env:   BAR_FROM=4 BAR_START_PT=555 BUDGET_MB=95 Q_TOP=86 Q_BOTTOM=62
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
BAR_START_PT = float(os.environ.get("BAR_START_PT", 555.0))
BUDGET = float(os.environ.get("BUDGET_MB", 95)) * 1048576
Q_TOP = int(os.environ.get("Q_TOP", 86))
Q_BOTTOM = int(os.environ.get("Q_BOTTOM", 62))
OVERHEAD = 1 * 1048576          # xref table, content streams, fonts: none left

BP, WP, GAMMA = 26.0, 238.0, 1.28         # bold-print curve (paper pages)
BP_C, WP_C, GAMMA_C = 10.0, 246.0, 1.06   # gentle curve for colour pages
INK = 120
COLOR_SAT = 45                            # saturation that counts as "colour"
COLOR_SHARE = 0.004                       # share of pixels that keeps RGB
RENDER_PAGES = (4, 151, 283)


def image_xref(doc, page):
    imgs = [i for i in page.get_images(full=True) if i[7] == "I0"]
    imgs = imgs or page.get_images(full=True)
    return imgs[0][0] if imgs else None


def decode(doc, xref):
    pm = pymupdf.Pixmap(doc, xref)
    if pm.colorspace is None or pm.colorspace.n != 3:
        pm = pymupdf.Pixmap(pymupdf.csRGB, pm)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 3)


def page_width_pt(doc, page):
    s = page.read_contents()
    m = re.search(rb"q\s+([-\d\.]+)\s+[-\d\.]+\s+[-\d\.]+\s+[-\d\.]+\s+"
                  rb"[-\d\.]+\s+[-\d\.]+\s+cm", s)
    return abs(float(m.group(1))) if m else page.rect.width


def analyse(arr):
    """(is_colour_page, has_colour_ink, bar_x0_px) for one scan"""
    g = arr.astype(np.float32).mean(axis=2)
    art = float((g > 215).mean()) < 0.5
    sat = arr.max(axis=2).astype(np.int16) - arr.min(axis=2).astype(np.int16)
    colorful = float(((sat > COLOR_SAT) & (g < 245)).mean()) > COLOR_SHARE
    return art, colorful


def bolden(arr, art):
    a = arr.astype(np.float32)
    if art:
        x = np.clip((a - BP_C) / (WP_C - BP_C), 0, 1) ** GAMMA_C
        return (x * 255.0 + 0.5).astype(np.uint8)
    g = a.mean(axis=2)
    x = np.clip((g - BP) / (WP - BP), 0, 1) ** GAMMA
    return (x * 255.0 + 0.5).astype(np.uint8)


def jpeg(plane, quality):
    if plane.ndim == 2:
        pm = pymupdf.Pixmap(pymupdf.csGRAY, plane.shape[1], plane.shape[0],
                            np.ascontiguousarray(plane).tobytes(), 0)
    else:
        pm = pymupdf.Pixmap(pymupdf.csRGB, plane.shape[1], plane.shape[0],
                            np.ascontiguousarray(plane).tobytes(), 0)
    return pm.tobytes("jpeg", jpg_quality=quality)


def build_plane(arr, bar_x0, art, keep_colour):
    out = bolden(arr, art)
    if bar_x0:
        out[:, bar_x0:] = 255
    if not keep_colour:
        return out if out.ndim == 2 else out.mean(axis=2).astype(np.uint8)
    return out


def write_image(doc, xref, data, grey, w, h):
    doc.update_stream(xref, data, compress=False)
    doc.xref_set_key(xref, "Filter", "/DCTDecode")
    doc.xref_set_key(xref, "ColorSpace", "/DeviceGray" if grey else "/DeviceRGB")
    doc.xref_set_key(xref, "BitsPerComponent", "8")
    doc.xref_set_key(xref, "Width", str(w))
    doc.xref_set_key(xref, "Height", str(h))
    for key in ("DecodeParms", "SMask", "Mask", "Decode"):
        doc.xref_set_key(xref, key, "null")


def unshare(doc):
    """give every page its own copy of its scan image

    Some PDFs point several pages at one image object (blank or identical
    scans). Rewriting such a shared stream once per page would leave only the
    last edit visible, so duplicate objects are cloned and the page resources
    are repointed.
    """
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


def plan(doc):
    """collect per-page metadata once"""
    meta = []
    for page in doc:
        xref = image_xref(doc, page)
        if xref is None:
            continue
        w = int(doc.xref_get_key(xref, "Width")[1])
        h = int(doc.xref_get_key(xref, "Height")[1])
        arr = decode(doc, xref)
        art, colourful = analyse(arr)
        x0 = 0
        if page.number + 1 >= BAR_FROM:
            dw = page_width_pt(doc, page)
            cand = int(round(BAR_START_PT / dw * w))
            cand = max(0, min(w - 2, cand))
            g = arr.astype(np.float32).mean(axis=2)
            sat = arr.max(axis=2).astype(np.int16) - arr.min(axis=2).astype(np.int16)
            if art:
                # a cover: only strip the margin when no artwork lives there
                neutral_dark = ((g[:, cand:] < 150) & (sat[:, cand:] < 60))
                if float(neutral_dark.mean()) < 0.02:
                    x0 = cand
            else:
                # paper page: keep any printed ink that reaches into the strip
                ink = (g[:, cand:] < INK)
                if ink.any():
                    cols = np.nonzero(ink.any(axis=0))[0]
                    right = cand + int(cols.min())
                    x0 = max(cand, right - 2)
                else:
                    x0 = cand
        meta.append({"page": page.number + 1, "xref": xref, "w": w, "h": h,
                     "art": art, "colour": colourful, "x0": x0})
    return meta


def measure(doc, meta, q, preserve_colour):
    total = 0
    for m in meta:
        arr = decode(doc, m["xref"])
        keep = preserve_colour and m["colour"]
        plane = build_plane(arr, m["x0"], m["art"], keep)
        total += len(jpeg(plane, q))
    return total


def main():
    doc = pymupdf.open(SRC)
    total_pages = doc.page_count
    cloned = unshare(doc)
    if cloned:
        print(f"unshared {cloned} shared scan objects", flush=True)
    meta = plan(doc)
    print(f"pages={total_pages} images={len(meta)}", flush=True)
    print("bar pages:", sum(1 for m in meta if m["x0"]), "| colour pages:",
          sum(1 for m in meta if m["colour"]), flush=True)

    # ---- pick a codec plan that fits the budget ---------------------------
    plans = [(True, q) for q in range(Q_TOP, Q_BOTTOM - 1, -4)]
    plans += [(False, q) for q in range(Q_TOP, Q_BOTTOM - 5, -4)]
    chosen = None
    for preserve, q in plans:
        est = measure(doc, meta, q, preserve) + OVERHEAD
        print(f"  plan colour={preserve} q={q}: {est / 1048576:.1f} MiB",
              flush=True)
        if est <= BUDGET:
            chosen = (preserve, q, est)
            break
    if chosen is None:
        preserve, q = False, Q_BOTTOM - 4
        chosen = (preserve, q, measure(doc, meta, q, preserve) + OVERHEAD)
        print("  WARNING: budget not reached", flush=True)
    preserve, q, est = chosen
    print(f"chosen: colour={preserve} q={q} est={est / 1048576:.1f} MiB",
          flush=True)

    # ---- write ------------------------------------------------------------
    for m in meta:
        arr = decode(doc, m["xref"])
        keep = preserve and m["colour"]
        plane = build_plane(arr, m["x0"], m["art"], keep)
        write_image(doc, m["xref"], jpeg(plane, q), not keep, m["w"], m["h"])
        if m["page"] % 50 == 0:
            print(f"  wrote page {m['page']}", flush=True)

    doc.save(OUT, garbage=4, deflate=True)
    doc.close()

    # ---- validate ---------------------------------------------------------
    chk = pymupdf.open(OUT)
    src = pymupdf.open(SRC)
    size = os.path.getsize(OUT)

    def image_of(d, pno):
        page = d[pno - 1]
        return decode(d, image_xref(d, page))

    bar_rows, bar_bad = [], []
    for m in meta:
        if not m["x0"]:
            continue
        g = image_of(chk, m["page"]).astype(np.float32).mean(axis=2)
        seg = g[:, m["x0"]:]
        dark = float((seg < 200).mean())
        bar_rows.append((m["page"], m["x0"], float(seg.min()), dark))
        if dark > 0.001 or seg.min() < 180:
            bar_bad.append((m["page"], round(dark, 5), float(seg.min())))

    samples = [p for p in (1, 61, 151, 250, 283) if p <= total_pages]
    ink_rows = []
    for pno in samples:
        for label, d in (("before", src), ("after", chk)):
            g = image_of(d, pno).astype(np.float32).mean(axis=2)
            ink = g < INK
            mean_ink = float(g[ink].mean()) if ink.any() else 255.0
            ink_rows.append((pno, label, float(ink.mean()),
                             float((g < 190).mean()), mean_ink))

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

    ok = size < 100 * 1048576 and pages_after == total_pages and not bar_bad
    lines = [
        "FINAL REPORT (stage 4)",
        "======================",
        f"source          : {os.path.basename(SRC)}",
        f"output          : {os.path.basename(OUT)}",
        f"size            : {size:,} bytes ({size / 1048576:.2f} MiB)",
        f"under 100 MiB   : {'YES' if size < 100 * 1048576 else 'NO'}",
        f"pages           : {pages_after}",
        f"codec           : JPEG, colour={preserve}, q={q}",
        f"sha256          : {digest}",
        "",
        f"white bar pages : {len(bar_rows)} (from page {BAR_FROM}, "
        f"start {BAR_START_PT} pt)",
        f"bar fully white : {'YES' if not bar_bad else 'NO'}",
    ]
    for pno, x0, mn, dark in bar_rows[:5]:
        lines.append(f"  page {pno:>3} x0={x0:>4} min_gray={mn:5.0f} "
                     f"dark_frac={dark:.5f}")
    if bar_bad:
        lines.append(f"  pages with ink in the strip: {bar_bad[:8]}")
    lines += ["",
              "ink metrics — coverage_120 grows and mean_ink falls when the",
              "print gets bolder (measurement on the embedded scan):",
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
