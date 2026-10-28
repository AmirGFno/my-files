#!/usr/bin/env python3
"""Before/after edge stats for stage 3 (edge repair).

For the sample pages it reports, on the embedded scan images directly:
  * interior_dark : dark pixels well inside the page (text integrity)
  * border_dark   : dark pixels inside the outer 6-pixel frame (scan band)
and writes dpi=80 renders of cover / a text page / last page.

Usage: edge_stats.py BEFORE.pdf AFTER.pdf
"""
import sys

import numpy as np
import pymupdf

BEFORE, AFTER = sys.argv[1], sys.argv[2]
SAMPLES = [1, 61, 151, 152, 250, 283]
RENDER = {1: "cover", 151: "text", 283: "last"}


def page_array(doc, idx):
    page = doc[idx]
    imgs = [i for i in page.get_images(full=True) if i[7] == "I0"]
    xref = imgs[0][0]
    w = int(doc.xref_get_key(xref, "Width")[1])
    h = int(doc.xref_get_key(xref, "Height")[1])
    arr = np.frombuffer(doc.xref_stream(xref), np.uint8).reshape(h, w, 3)
    return arr, page


def stats(arr):
    g = arr.astype(np.float32).mean(axis=2)
    interior = int((g[60:-60, 60:-60] < 120).sum())
    frame = np.concatenate([g[:6, :].ravel(), g[-6:, :].ravel(),
                            g[:, :6].ravel(), g[:, -6:].ravel()])
    border = int((frame < 120).sum())
    return interior, border


def main():
    a, b = pymupdf.open(BEFORE), pymupdf.open(AFTER)
    print(f"pages: before={a.page_count} after={b.page_count}")
    print(f"{'page':>5} {'interior_dark before':>20} {'after':>10} "
          f"{'delta':>6} | {'border_dark before':>18} {'after':>8}")
    rows = []
    ok = True
    for p in SAMPLES:
        ai, ab = stats(page_array(a, p - 1)[0])
        bi, bb = stats(page_array(b, p - 1)[0])
        same = ai == bi
        ok &= same
        rows.append((p, ai, bi, ab, bb, same))
        print(f"{p:>5} {ai:>20} {bi:>10} {bi - ai:>6} | {ab:>18} {bb:>8}"
              f"   {'text intact' if same else 'TEXT CHANGED'}")
    for p, label in RENDER.items():
        page_array(b, p - 1)[1].get_pixmap(dpi=80).save(f"{label}.png")
    print("\nRESULT:", "PASS" if ok else "REVIEW NEEDED")
    with open("edge_stats.txt", "w", encoding="utf-8") as f:
        f.write(f"pages: before={a.page_count} after={b.page_count}\n")
        f.write(f"{'page':>5} {'interior_before':>15} {'interior_after':>14} "
                f"{'border_before':>13} {'border_after':>12}\n")
        for p, ai, bi, ab, bb, same in rows:
            f.write(f"{p:>5} {ai:>15} {bi:>14} {ab:>13} {bb:>12}\n")
        f.write("\nRESULT: " + ("PASS" if ok else "REVIEW NEEDED") + "\n")
    sys.exit(0 if ok else 5)


if __name__ == "__main__":
    main()
