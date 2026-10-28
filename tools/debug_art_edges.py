#!/usr/bin/env python3
"""Diagnostics for the two colour-cover pages: measure the dark border band."""
import numpy as np
import pymupdf

PDF = "KECHAP_BOOK_بیست‌ینو قریشی 1406 (بدون واترمارک).pdf"


def gray(a):
    return a.astype(np.float32).mean(axis=2)


def sat(a):
    return a.max(axis=2).astype(np.int16) - a.min(axis=2).astype(np.int16)


def runs(mask):
    """leading run length along axis=1"""
    m = mask.astype(np.int8)
    W = m.shape[1]
    ff = (m == 0).argmax(axis=1).astype(np.int32)
    ff[mask.all(axis=1)] = W
    ff[~mask.any(axis=1)] = 0
    return ff


doc = pymupdf.open(PDF)
for pno in (1, 283):
    page = doc[pno - 1]
    xref = [i for i in page.get_images(full=True) if i[7] == "I0"][0][0]
    w = int(doc.xref_get_key(xref, "Width")[1])
    h = int(doc.xref_get_key(xref, "Height")[1])
    a = np.frombuffer(doc.xref_stream(xref), np.uint8).reshape(h, w, 3)
    g, s = gray(a), sat(a)
    print(f"\n=== page {pno} {w}x{h} whiteshare={float((g>215).mean()):.3f}")
    for name, mask in (("L", (g < 140) & (s < 60)),
                       ("R", ((g < 140) & (s < 60))[:, ::-1]),
                       ("T", ((g < 140) & (s < 60)).T),
                       ("B", ((g < 140) & (s < 60))[::-1, :].T)):
        L = runs(mask)
        nz = L[L > 0]
        if nz.size == 0:
            print(f"  {name}: no dark at border")
            continue
        q = np.percentile(nz, [10, 25, 50, 75, 90, 99]).round(0).astype(int)
        print(f"  {name}: lines_with_dark={nz.size}/{len(L)} "
              f"p10/25/50/75/90/99={q.tolist()} max={int(nz.max())}")
    # component view of everything dark & neutral that touches the frame
    from scipy import ndimage as ndi
    cand = (g < 140) & (s < 60)
    lab, n = ndi.label(cand, structure=np.ones((3, 3), np.int16))
    border_ids = set(np.unique(np.concatenate(
        [lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])).tolist()) - {0}
    objs = ndi.find_objects(lab)
    print(f"  components={n} touching_border={len(border_ids)}")
    rows = []
    for cid in border_ids:
        sl = objs[cid - 1]
        area = int((lab[sl] == cid).sum())
        th = min(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start)
        rows.append((area, th, sl[0].start, sl[1].start,
                     sl[0].stop, sl[1].stop))
    for area, th, y0, x0, y1, x1 in sorted(rows, reverse=True)[:10]:
        print(f"    area={area:7d} thickness={th:4d} bbox=({y0},{x0})-({y1},{x1})")
