#!/usr/bin/env python3
"""
Remove Pagination/Watermark artifacts from a NAPS2-scanned PDF.

Strategy: every page's content stream is rebuilt so it contains ONLY the base
scan placement (q <ctm> cm /I0 Do Q). All /Artifact ... EMC blocks, the
watermark XObjects (/FXX1../FXX6), text/font resources and the page's
/OCProperties, /AcroForm and /Names entries are dropped. The base scan image
XObjects themselves are never touched, re-encoded or re-compressed.

Usage: strip_watermarks.py <src.pdf> <out.pdf> [report.txt]
"""
import hashlib
import os
import re
import sys

import pymupdf

SRC = sys.argv[1]
OUT = sys.argv[2]
REPORT = sys.argv[3] if len(sys.argv) > 3 else "validation_report.txt"

base_re = re.compile(rb"q\s*([-\d\.\s]+?)\s*cm\s*/I0\s*Do\s*Q")
clean_re = re.compile(rb"^\s*q\s*[-\d\.\s]+cm\s*/I0\s+Do\s*Q\s*$")
text_op_re = re.compile(rb"(?:\bTj\b|\bTJ\b|\bTf\b|\bTd\b|\bTd\s|\bBT\b)")


def new_stream(doc, data):
    xref = doc.get_new_xref()
    doc.update_object(xref, "<< /Length %d >>" % len(data))
    doc.update_stream(xref, data)
    return xref


def page_object_count(doc, kind_key, kind_val):
    n = 0
    for x in range(1, doc.xref_length()):
        try:
            k, v = doc.xref_get_key(x, kind_key)
        except Exception:
            continue
        if k == "name" and v == kind_val:
            n += 1
        elif k == "xref" and v.split()[0] == kind_val:
            n += 1
    return n


def main():
    if not os.path.exists(SRC):
        sys.exit(f"source not found: {SRC}")

    doc = pymupdf.open(SRC)
    src_pages = doc.page_count

    removed_blocks = 0
    pages_done = 0
    for page in doc:
        s = page.read_contents()
        m = base_re.search(s)
        if not m:
            sys.exit(f"base image block missing on page {page.number + 1}")
        ctm = b" ".join(m.group(1).split())
        base = [i for i in page.get_images(full=True) if i[7] == "I0"]
        if not base:
            sys.exit(f"no I0 image on page {page.number + 1}")
        xref = new_stream(doc, b"q\n" + ctm + b" cm\n/I0 Do\nQ\n")
        page.set_contents(xref)
        doc.xref_set_key(page.xref, "Resources",
                         "<< /XObject << /I0 %d 0 R >> >>" % base[0][0])
        removed_blocks += s.count(b"BDC")
        pages_done += 1

    cat = doc.pdf_catalog()
    dropped_keys = {}
    for k in ("OCProperties", "AcroForm", "Names"):
        before = doc.xref_get_key(cat, k)
        doc.xref_set_key(cat, k, "null")
        after = doc.xref_get_key(cat, k)
        dropped_keys[k] = (str(before), str(after))

    doc.save(OUT, garbage=4, deflate=True, clean=True)
    doc.close()

    # ---------------------------------------------------------------- verify
    chk = pymupdf.open(OUT)
    out_pages = chk.page_count

    bdc = fxx = text_ops = font_refs = 0
    content_ok = 0
    for page in chk:
        s = page.read_contents()
        bdc += s.count(b"BDC")
        fxx += len(re.findall(rb"/FX[EF]?\d", s)) + s.count(b"/FXX")
        text_ops += len(text_op_re.findall(s))
        font_refs += s.count(b"/Font")
        if clean_re.match(s):
            content_ok += 1

    def count_objs(key, val):
        n = 0
        for x in range(1, chk.xref_length()):
            try:
                k, v = chk.xref_get_key(x, key)
            except Exception:
                continue
            if k in ("name", "xref") and v.split()[0].strip("/") == val.strip("/"):
                n += 1
        return n

    image_objs = count_objs("Subtype", "/Image")
    font_objs = count_objs("Type", "/Font")
    xobj_fxx = 0
    for x in range(1, chk.xref_length()):
        try:
            k, v = chk.xref_get_key(x, "Name")
        except Exception:
            continue
        if k == "name" and v.startswith(("/FXX", "/FXE")):
            xobj_fxx += 1

    cat_out = chk.pdf_catalog()
    cat_state = {k: chk.xref_get_key(cat_out, k) for k in
                 ("OCProperties", "AcroForm", "Names")}
    chk.close()

    size = os.path.getsize(OUT)
    sha = hashlib.sha256()
    with open(OUT, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    digest = sha.hexdigest()

    lines = [
        "VALIDATION REPORT",
        "=================",
        f"source file           : {os.path.basename(SRC)}",
        f"output file           : {os.path.basename(OUT)}",
        f"source size (bytes)   : {os.path.getsize(SRC)}",
        f"output size (bytes)   : {size}  ({size / 1048576:.2f} MiB)",
        f"sha256                : {digest}",
        "",
        f"pages                 : {out_pages} (expected {src_pages})",
        f"artifact blocks in src: {removed_blocks}",
        f"BDC blocks left       : {bdc}   (must be 0)",
        f"/FXX|/FXE refs left   : {fxx}   (must be 0)",
        f"text operators left   : {text_ops}   (must be 0)",
        f"/Font refs in content : {font_refs}   (must be 0)",
        f"font objects in file  : {font_objs}   (must be 0)",
        f"watermark xobj names  : {xobj_fxx}   (must be 0)",
        f"image objects in file : {image_objs}   (expected {out_pages})",
        f"pages w/ pure content : {content_ok}/{out_pages}",
        "",
        "catalog keys after cleanup:",
    ]
    for k, v in cat_state.items():
        lines.append(f"  {k:12s} -> {v}")

    ok = (out_pages == src_pages == 283 and bdc == 0 and fxx == 0
          and text_ops == 0 and font_refs == 0 and font_objs == 0
          and xobj_fxx == 0 and image_objs == out_pages and content_ok == out_pages)

    lines.append("")
    lines.append("RESULT: " + ("PASS" if ok else "REVIEW NEEDED"))

    txt = "\n".join(lines)
    print(txt)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(txt + "\n")

    # renders for eyeball check (rendering does not modify the document)
    for idx, label in ((0, "cover"), (150, "p151"), (out_pages - 1, "last")):
        d = pymupdf.open(OUT)
        pix = d[idx].get_pixmap(dpi=110)
        pix.save(f"{label}.png")
        d.close()

    if not ok:
        sys.exit(3)


if __name__ == "__main__":
    main()
