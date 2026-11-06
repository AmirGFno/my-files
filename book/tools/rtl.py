"""Bidi (token-level subset of UBA) + Arabic shaping, so Persian text renders correctly.

ReportLab draws glyphs in the order given, with no shaping and no bidi. So we:
  1. shape Arabic runs with arabic_reshaper (logical order preserved),
  2. tokenise: a whole LTR chunk (Latin letters, digits, (), ', -, spaces between)
     becomes ONE atomic token of class L -> keeps algorithms like (R U R' U') intact,
  3. run bidi levels over tokens,
  4. reorder tokens into visual order.
"""
from __future__ import annotations

import re
import unicodedata

import arabic_reshaper

_ARABIC = set(range(0x0600, 0x0700)) | set(range(0xFB50, 0xFDFF)) | set(range(0xFE70, 0xFEFF))

_LTR_CHUNK = re.compile(r"[A-Za-z0-9'’()\[\]+\-=×/.%:]+(?: [A-Za-z0-9'’()\[\]+\-=×/.%:]+)*")


def _cls(ch: str) -> str:
    o = ord(ch)
    if 0x0660 <= o <= 0x0669 or 0x06F0 <= o <= 0x06F9:
        return "AN"
    if o in _ARABIC:
        if ch in "،؛؟":
            return "ON"
        return "R"
    b = unicodedata.bidirectional(ch)
    if b in ("L", "R", "AL", "EN", "AN"):
        return "R" if b in ("R", "AL") else ("L" if b == "L" else "EN")
    if b in ("ON", "B", "S", "ES", "ET", "CS", "BN", "NSM"):
        return "ON"
    if b == "WS":
        return "WS"
    return "ON"


def _tokenize(text: str) -> list[str]:
    """Split into bidi tokens; LTR chunks (algorithms, English words) stay whole."""
    tokens: list[str] = []
    pos = 0
    for m in _LTR_CHUNK.finditer(text):
        if m.start() > pos:
            tokens.extend(list(text[pos : m.start()]))
        tokens.append(m.group(0))
        pos = m.end()
    if pos < len(text):
        tokens.extend(list(text[pos:]))
    return [t for t in tokens if t]


def _shape_runs(text: str) -> str:
    out, buf = [], []
    for ch in text:
        if ord(ch) in _ARABIC:
            buf.append(ch)
        else:
            if buf:
                out.append(arabic_reshaper.reshape("".join(buf)))
                buf = []
            out.append(ch)
    if buf:
        out.append(arabic_reshaper.reshape("".join(buf)))
    return "".join(out)


def _levels(tokens: list[str], base: int = 1) -> list[int]:
    n = len(tokens)
    if not n:
        return []
    types = []
    for t in tokens:
        if len(t) > 1 and _LTR_CHUNK.fullmatch(t):
            types.append("L")
        else:
            ch = t[0]
            kind = _cls(ch)
            types.append(kind)

    # W2: EN after R -> AN
    last = None
    for i in range(n):
        if types[i] in ("R", "L"):
            last = types[i]
        elif types[i] == "EN" and last == "R":
            types[i] = "AN"

    # N1/N2
    neutrals = {"ON", "WS"}
    for i in range(n):
        if types[i] not in neutrals:
            continue
        j = i
        while j < n and types[j] in neutrals:
            j += 1
        before = types[i - 1] if i else ("R" if base else "L")
        after = types[j] if j < n else ("R" if base else "L")
        if before == after and before in ("R", "L"):
            resolved = before
        elif before in ("EN", "AN") and after in ("EN", "AN"):
            resolved = "R"
        else:
            resolved = "R" if base else "L"
        for k in range(i, j):
            types[k] = resolved

    levels = []
    for t in types:
        if base % 2 == 0:
            extra = {"R": 1, "AN": 2, "EN": 2}.get(t, 0)
        else:
            extra = {"L": 1, "EN": 1, "AN": 1}.get(t, 0)
        levels.append(base + extra)
    return levels


def visual(text: str) -> str:
    if not text:
        return ""
    tokens = _tokenize(_shape_runs(text))
    levels = _levels(tokens)
    highest = max(levels) if levels else 1
    lowest_odd = min([l for l in levels if l % 2 == 1], default=1)
    for lvl in range(highest, lowest_odd - 1, -1):
        i = 0
        while i < len(tokens):
            if levels[i] >= lvl:
                j = i
                while j < len(tokens) and levels[j] >= lvl:
                    j += 1
                tokens[i:j] = tokens[i:j][::-1]
                levels[i:j] = levels[i:j][::-1]
                i = j
            else:
                i += 1
    return "".join(tokens).replace("\u2066", "").replace("\u2069", "")


def isolate(latin: str) -> str:
    """Wrap an LTR fragment so it keeps its internal order (RLM acts as a neutral)."""
    return "\u200f" + latin + "\u200f"


if __name__ == "__main__":
    tests = [
        "حرکت R U R' U' را انجام بده.",
        "صفحه ۲۲ — مرحله ۳",
        "الگوریتم (F R U R' U' F') برای صلیب زرد",
        "۴ روش، ۱ مبتدی و ۱ حرفه‌ای (CFOP).",
    ]
    for s in tests:
        print(s, "\n   ->", visual(s), "\n")
