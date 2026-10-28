"""Whiten black scan-edge bands / slivers on the cleaned (no-watermark) PDF.

Strategy
  * paper-like pages (whiteness >= 0.5): detect the true paper edge on all four
    sides with a bright-run scan, fit a robust straight line, fill everything
    outside with the page's paper colour, then iteratively clean thin residual
    slivers that hug the edge, and finally remove dark neutral blobs that touch
    the page border (connected components).
  * colourful pages (the two covers): no paper edge exists, so we strip the
    black scan band that hugs the border with a per-row / per-column run scan,
    followed by a small connected-component pass.
All work happens on the embedded scan images, so nothing is re-rendered or
re-compressed: quality is preserved 1:1.

Usage:
    python repair_edges.py [SRC.pdf] [OUT.pdf]
Defaults are the stage-2 / stage-3 file names used by this repo.
"""
import sys
import time

import numpy as np
import pymupdf
from scipy import ndimage as ndi

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    "KECHAP_BOOK_بیست‌ینو قریشی 1406 (بدون واترمارک).pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else \
    "KECHAP_BOOK_بیست‌ینو قریشی 1406 (ترمیم‌شده).pdf"

BRIGHT, RUN, MAXOFF, TOL, INSIDE = 215, 20, 150, 3.0, 2
SLIVBAND, MAXSLIV = 30, 22
DARKMAX, SATMAX, NEARB, FRACPIX = 140, 50, 90, 0.04


def gray(a):
    return a.astype(np.float32).mean(axis=2)


def sat(a):
    return a.max(axis=2).astype(np.int16) - a.min(axis=2).astype(np.int16)


def first_run(mask, n, axis):
    """first index (along axis) where n consecutive True start; NaN if none."""
    m = mask if axis == 1 else mask.T
    m = m.astype(np.int32)
    c = np.cumsum(m, axis=1)
    c = np.concatenate([np.zeros((c.shape[0], 1), np.int32), c], axis=1)
    win = c[:, n:] - c[:, :-n]
    hit = win == n
    any_hit = hit.any(axis=1)
    idx = np.argmax(hit, axis=1).astype(np.float32)
    idx[~any_hit] = np.nan
    return idx


def edge_pos(g, side):
    H, W = g.shape
    if side == "L":
        v = first_run(g > BRIGHT, RUN, 1); v[v > MAXOFF] = np.nan; return v
    if side == "R":
        v = first_run(g[:, ::-1] > BRIGHT, RUN, 1); v = W - 1 - v; v[v > W - 1 - 0] = np.nan
        v[v < W - 1 - MAXOFF] = np.nan; return v
    if side == "T":
        v = first_run(g > BRIGHT, RUN, 0); v[v > MAXOFF] = np.nan; return v
    v = first_run(g[::-1, :] > BRIGHT, RUN, 0); v = H - 1 - v
    v[v < H - 1 - MAXOFF] = np.nan; return v


def robust_line(t, v, seed=7):
    m = ~np.isnan(v)
    if m.sum() < 25:
        return None
    t, v = t[m].astype(np.float64), v[m].astype(np.float64)
    n = len(t)
    rng = np.random.default_rng(seed)
    i = rng.integers(0, n, 600); j = rng.integers(0, n, 600)
    ok = np.abs(t[i] - t[j]) >= 40
    i, j = i[ok], j[ok]
    if len(i) == 0:
        return None
    a = (v[j] - v[i]) / (t[j] - t[i])
    b = v[i] - a * t[i]
    keep = np.abs(a) <= 0.12
    a, b = a[keep], b[keep]
    if len(a) == 0:
        return None
    inl = (np.abs(v[None, :] - (a[:, None] * t[None, :] + b[:, None])) < TOL).sum(axis=1)
    k = int(np.argmax(inl))
    if inl[k] < 0.45 * n:
        return None
    A, B = a[k], b[k]
    for _ in range(3):
        m2 = np.abs(v - (A * t + B)) < TOL * 1.6
        if m2.sum() < 25:
            break
        A, B = np.polyfit(t[m2], v[m2], 1)
    return float(A), float(B)


def paper_color(arr, g):
    """dominant bright colour of the page; never returns an empty/NaN fill"""
    b = g > 205
    if b.sum() < 2000:
        b = g > np.percentile(g, 85)
    if not b.any():
        b = g >= g.max()
    if not b.any():
        return np.full(3, 255, np.uint8)
    return np.round(np.median(arr[b], axis=0)).astype(np.uint8)


def edge_fill(arr, fill):
    """whiten everything outside the fitted paper edge"""
    H, W, _ = arr.shape
    g = gray(arr)
    out = arr.copy()
    for side in ("L", "R", "T", "B"):
        t = np.arange(H) if side in ("L", "R") else np.arange(W)
        f = robust_line(t, edge_pos(g, side))
        if f is None:
            continue
        lim = np.clip(f[0] * t + f[1], 0, (W - 1) if side in ("L", "R") else (H - 1))
        inside = lim - INSIDE if side in ("L", "T") else lim + INSIDE
        xs = np.arange(W)[None, :]
        ys = np.arange(H)[:, None]
        if side == "L":
            out[xs < inside[:, None]] = fill
        elif side == "R":
            out[xs > inside[:, None]] = fill
        elif side == "T":
            out[ys < inside[None, :]] = fill
        else:
            out[ys > inside[None, :]] = fill
    return out


def sliver_clean(arr, fill, passes=(25, 15, 8)):
    out = arr.copy()
    for drop in passes:
        g = gray(out)
        pos_l = np.clip(robust_line(np.arange(g.shape[0]), edge_pos(g, "L")) or (0, 0), 0, g.shape[1] - 1)
        lim_l = np.clip(pos_l[0] * np.arange(g.shape[0]) + pos_l[1], 0, g.shape[1] - 1)
        pos_r = robust_line(np.arange(g.shape[0]), edge_pos(g, "R"))
        lim_r = None if pos_r is None else np.clip(pos_r[0] * np.arange(g.shape[0]) + pos_r[1], 0, g.shape[1] - 1)
        pos_t = robust_line(np.arange(g.shape[1]), edge_pos(g, "T"))
        lim_t = None if pos_t is None else np.clip(pos_t[0] * np.arange(g.shape[1]) + pos_t[1], 0, g.shape[0] - 1)
        pos_b = robust_line(np.arange(g.shape[1]), edge_pos(g, "B"))
        lim_b = None if pos_b is None else np.clip(pos_b[0] * np.arange(g.shape[1]) + pos_b[1], 0, g.shape[0] - 1)

        pm = float(np.median(g[g > 150])) if (g > 150).any() else 245.0
        np_mask = g < (pm - drop)
        H, W = g.shape
        for y in range(H):
            s = max(0, int(lim_l[y]) - INSIDE + 1)
            x, e = s, min(W, s + SLIVBAND)
            while x < e and np_mask[y, x]:
                x += 1
            if x < e and 0 < x - s <= MAXSLIV and not np_mask[y, x]:
                out[y, s:x] = fill
            if lim_r is not None:
                s = min(W - 1, int(lim_r[y]) + INSIDE - 1)
                x, e = s, max(-1, s - SLIVBAND)
                while x > e and np_mask[y, x]:
                    x -= 1
                if x > e and 0 < s - x <= MAXSLIV and x >= 0 and not np_mask[y, x]:
                    out[y, x + 1:s + 1] = fill
        np_mask = gray(out) < (pm - drop)
        for x in range(W):
            s = max(0, int(lim_t[x]) - INSIDE + 1) if lim_t is not None else 0
            if lim_t is not None:
                y, e = s, min(H, s + SLIVBAND)
                while y < e and np_mask[y, x]:
                    y += 1
                if y < e and 0 < y - s <= MAXSLIV and not np_mask[y, x]:
                    out[s:y, x] = fill
            if lim_b is not None:
                s = min(H - 1, int(lim_b[x]) + INSIDE - 1)
                y, e = s, max(-1, s - SLIVBAND)
                while y > e and np_mask[y, x]:
                    y -= 1
                if y > e and 0 < s - y <= MAXSLIV and y >= 0 and not np_mask[y, x]:
                    out[y + 1:s + 1, x] = fill
    return out


def border_blocks(arr, fill, near=NEARB, frac=FRACPIX, darkmax=DARKMAX, satmax=SATMAX):
    H, W, _ = arr.shape
    cand = (gray(arr) < darkmax) & (sat(arr) < satmax)
    if not cand.any():
        return arr, 0
    lab, n = ndi.label(cand, structure=np.ones((3, 3), np.int16))
    if n == 0:
        return arr, 0
    ids = np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
    ids = ids[ids > 0]
    if ids.size == 0:
        return arr, 0
    objs = ndi.find_objects(lab)
    out = arr.copy()
    total = 0
    for cid in ids:
        sl = objs[cid - 1]
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        area = int((lab[sl] == cid).sum())
        if area > frac * H * W:
            continue
        if not (x0 <= near or (W - 1 - x1) <= near or y0 <= near or (H - 1 - y1) <= near):
            continue
        if min(y1 - y0, x1 - x0) > near:
            continue
        out[sl][lab[sl] == cid] = fill
        total += area
    return out, total


def prefix_len(mask):
    """length of the leading run of True along axis=1 for every row"""
    m = mask.astype(np.int8)
    W = m.shape[1]
    ff = (m == 0).argmax(axis=1).astype(np.int32)
    alltrue = mask.all(axis=1)
    ff[alltrue] = W
    ff[~mask.any(axis=1)] = 0
    return ff


def _strip_uniform(view, mask, fill, tol, maxT):
    """On a (lines, thickness, 3) view, strip the leading dark run of every line
    whose run length agrees with the edge-wide consensus."""
    L = prefix_len(mask)
    nz = L > 0
    if nz.sum() < 0.5 * len(L):
        return 0
    T = int(np.median(L[nz]))
    if T < 2 or T > maxT:
        return 0
    keep = nz & (np.abs(L - T) <= tol)
    if not keep.any():
        return 0
    lim = int(min(T + tol, L[keep].max()))
    cut = np.where(keep, np.minimum(L, lim), 0)
    total = 0
    for i in np.nonzero(cut)[0]:
        c = int(cut[i])
        view[i, :c] = fill
        total += c
    return total


def band_consensus(arr, fill, darkmax=140, satmax=60, tol=14, maxT=120):
    """Strip the border band only where its thickness agrees with the edge-wide
    consensus, so cover artwork that merely touches the border stays intact.

    A scan band is a *uniform* strip along the whole edge; artwork (a figure, a
    dark colour block) produces lines with a very different run length and is
    therefore skipped instead of eaten.
    """
    out = arr.copy()
    band = (gray(out) < darkmax) & (sat(out) < satmax)
    total = 0
    # left / right: rows are lines, thickness runs along x
    total += _strip_uniform(out, band, fill, tol, maxT)
    total += _strip_uniform(out[:, ::-1], band[:, ::-1], fill, tol, maxT)
    # top / bottom: transpose so columns become lines
    tv = out.transpose(1, 0, 2)
    total += _strip_uniform(tv, band.T, fill, tol, maxT)
    total += _strip_uniform(tv[:, ::-1], band[::-1, :].T, fill, tol, maxT)
    return out, total


def frame_clean(arr, fill, band=6, darkmax=140, satmax=60):
    """Whiten dark neutral pixels in the outermost `band` pixels (scan frame)."""
    out = arr.copy()
    H, W = out.shape[:2]
    dark = (gray(out) < darkmax) & (sat(out) < satmax)
    total = 0
    for sl in (np.s_[0:band, :], np.s_[H - band:H, :],
               np.s_[:, 0:band], np.s_[:, W - band:W]):
        m = dark[sl]
        total += int(m.sum())
        out[sl][m] = fill
    return out, total


def speck_clean(arr, fill, near=45, maxarea=700):
    """remove small dark specks that sit just inside the paper edge."""
    H, W, _ = arr.shape
    g = gray(arr)
    lines = {}
    for side in ("L", "R", "T", "B"):
        t = np.arange(H) if side in ("L", "R") else np.arange(W)
        f = robust_line(t, edge_pos(g, side))
        if f is not None:
            lines[side] = np.clip(f[0] * t + f[1], 0, (W - 1) if side in ("L", "R") else (H - 1))
    if not lines:
        return arr
    xs = np.arange(W)[None, :]
    ys = np.arange(H)[:, None]
    zone = np.zeros((H, W), bool)
    if "L" in lines:
        zone |= (xs >= lines["L"][:, None] - 3) & (xs <= lines["L"][:, None] + near)
    if "R" in lines:
        zone |= (xs <= lines["R"][:, None] + 3) & (xs >= lines["R"][:, None] - near)
    if "T" in lines:
        zone |= (ys >= lines["T"][None, :] - 3) & (ys <= lines["T"][None, :] + near)
    if "B" in lines:
        zone |= (ys <= lines["B"][None, :] + 3) & (ys >= lines["B"][None, :] - near)
    cand = (g < 150) & (sat(arr) < 70) & zone
    if not cand.any():
        return arr
    lab, n = ndi.label(cand, structure=np.ones((3, 3), np.int16))
    if n == 0:
        return arr
    objs = ndi.find_objects(lab)
    sizes = ndi.sum(cand, lab, range(1, n + 1))
    out = arr.copy()
    for k in range(1, n + 1):
        if sizes[k - 1] > maxarea:
            continue
        sl = objs[k - 1]
        if not zone[sl][lab[sl] == k].all():
            continue
        out[sl][lab[sl] == k] = fill
    return out


def fix_page(arr):
    fill = paper_color(arr, gray(arr))
    whiteshare = float((gray(arr) > 215).mean())
    if whiteshare >= 0.5:
        out = edge_fill(arr, fill)
        out, _ = border_blocks(out, fill)
        out = sliver_clean(out, fill)
        out = speck_clean(out, fill)
        out, _ = border_blocks(out, fill)
        out, _ = frame_clean(out, fill)
        kind = "text"
    else:
        out, _ = band_consensus(arr, fill)
        out, _ = border_blocks(out, fill, near=80, frac=0.03)
        out, _ = band_consensus(out, fill)
        out, _ = frame_clean(out, fill)
        kind = "art"
    return out, kind


def main():
    doc = pymupdf.open(SRC)
    t0 = time.time()
    for page in doc:
        xrefs = [i for i in page.get_images(full=True) if i[7] == "I0"]
        if not xrefs:
            print(f"page {page.number + 1}: no /I0 image, skipped", flush=True)
            continue
        xref = xrefs[0][0]
        w = int(doc.xref_get_key(xref, "Width")[1])
        h = int(doc.xref_get_key(xref, "Height")[1])
        arr = np.frombuffer(doc.xref_stream(xref), np.uint8).reshape(h, w, 3).copy()
        out, kind = fix_page(arr)
        doc.update_stream(xref, out.tobytes(), compress=True)
        print(f"page {page.number + 1}/{doc.page_count} {kind} {w}x{h} {time.time()-t0:.0f}s", flush=True)
    doc.save(OUT, garbage=3, deflate=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
