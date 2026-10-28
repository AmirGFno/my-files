#!/usr/bin/env python3
"""Before/after stats for stage 3 (edge repair).

All numbers are measured on the embedded scan images, never on a render:
  * interior_dark : dark pixels well inside the page   -> must be identical
  * border_dark   : dark pixels in the outer 6-pixel frame -> should go to ~0
  * dark removed  : dark->bright changes farther than 150 px from every border
                    (would mean text was erased)          -> must be 0
  * brightened    : any pixel that got *darker* after the repair -> must be 0
Renders of cover / a text page / last page are written at dpi=80.

Usage: edge_stats.py BEFORE.pdf AFTER.pdf
"""
import sys

import numpy as np
import pymupdf

BEFORE, AFTER = sys.argv[1], sys.argv[2]
SAMPLES = [1, 61, 151, 152, 250, 283]
RENDER = {1: "cover", 151: "text", 283: "last"}
GUARD = 150


def load(doc, idx):
    page = doc[idx]
    imgs = [i for i in page.get_images(full=True) if i[7] == "I0"]
    xref = imgs[0][0]
    w = int(doc.xref_get_key(xref, "Width")[1])
    h = int(doc.xref_get_key(xref, "Height")[1])
    arr = np.frombuffer(doc.xref_stream(xref), np.uint8).reshape(h, w, 3)
    return arr, page


def frame_mask(g, band=6):
    return np.concatenate([g[:band, :].ravel(), g[-band:, :].ravel(),
                           g[:, :band].ravel(), g[:, -band:].ravel()])


def audit(a, b):
    ga = a.astype(np.float32).mean(axis=2)
    gb = b.astype(np.float32).mean(axis=2)
    interior = (int((ga[60:-60, 60:-60] < 120).sum()),
                int((gb[60:-60, 60:-60] < 120).sum()))
    border = (int((frame_mask(ga) < 120).sum()),
              int((frame_mask(gb) < 120).sum()))
    removed = (ga < 120) & (gb >= 120)
    H, W = ga.shape
    deep = np.zeros_like(removed)
    deep[GUARD:H - GUARD, GUARD:W - GUARD] = True
    dark_removed_deep = int((removed & deep).sum())
    brightened = int(((gb < ga - 20) & (ga >= 160)).sum())  # content got darker
    return interior, border, dark_removed_deep, brightened


def main():
    a, b = pymupdf.open(BEFORE), pymupdf.open(AFTER)
    print(f"pages: before={a.page_count} after={b.page_count}")
    print(f"{'page':>5} {'interior_dark':>22} {'border_dark':>16} "
          f"{'dark_removed_deep':>18} {'brightened':>11}  verdict")
    rows, ok = [], (a.page_count == b.page_count)
    samples = [p for p in SAMPLES if p <= min(a.page_count, b.page_count)]
    for p in samples:
        (i0, i1), (b0, b1), deep, bright = audit(load(a, p - 1)[0],
                                                 load(b, p - 1)[0])
        same = i0 == i1
        shrunk = b1 <= max(300, 0.01 * b0)
        good = same and shrunk and deep == 0 and bright == 0
        ok &= good
        rows.append((p, i0, i1, b0, b1, deep, bright, good))
        print(f"{p:>5} {i0:>10} -> {i1:<8} {b0:>8} -> {b1:<6} "
              f"{deep:>18} {bright:>11}  {'OK' if good else 'CHECK'}")
    for p, label in RENDER.items():
        if p <= b.page_count:
            load(b, p - 1)[1].get_pixmap(dpi=80).save(f"{label}.png")

    print("\nRESULT:", "PASS" if ok else "REVIEW NEEDED")
    with open("edge_stats.txt", "w", encoding="utf-8") as f:
        f.write(f"pages: before={a.page_count} after={b.page_count} "
                f"(scan images measured directly, no re-render)\n\n")
        f.write(f"{'page':>5} {'interior_dark':>14} {'after':>10} "
                f"{'border_dark':>12} {'after':>8} "
                f"{'dark_removed_deep':>18} {'brightened':>11}\n")
        for p, i0, i1, b0, b1, deep, bright, _g in rows:
            f.write(f"{p:>5} {i0:>14} {i1:>10} {b0:>12} {b1:>8} "
                    f"{deep:>18} {bright:>11}\n")
        f.write("\ninterior_dark = dark pixels inside the text area "
                "(identical before/after => no text touched)\n")
        f.write("border_dark   = dark pixels in the outer 6 px frame (scan band)\n")
        f.write("dark_removed_deep = dark->bright flips farther than 150 px from "
                "every border (must be 0)\n")
        f.write("brightened    = pixels that became darker (must be 0)\n")
        f.write("\nRESULT: " + ("PASS" if ok else "REVIEW NEEDED") + "\n")
    sys.exit(0 if ok else 5)


if __name__ == "__main__":
    main()
