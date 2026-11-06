"""A real 3x3x3 cube engine + a vector renderer for book diagrams.

No external deps: geometry is done by hand so every figure is generated from a
simulated cube state (so a typo in an algorithm is caught, not published).
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple, Sequence

Vec = Tuple[float, float, float]

# ---------------------------------------------------------------- colours
# Book palette: one colour per face, tuned for print (not neon).
COLORS = {
    "U": (0.98, 0.79, 0.10),   # yellow
    "D": (0.95, 0.95, 0.93),   # white
    "F": (0.10, 0.62, 0.42),   # green
    "B": (0.11, 0.36, 0.72),   # blue
    "R": (0.83, 0.14, 0.19),   # red
    "L": (0.96, 0.50, 0.10),   # orange
}
PLASTIC = (0.10, 0.10, 0.12)
GREY = (0.78, 0.78, 0.80)

FACE_NORMALS = {
    "U": (0, 1, 0), "D": (0, -1, 0),
    "R": (1, 0, 0), "L": (-1, 0, 0),
    "F": (0, 0, 1), "B": (0, 0, -1),
}

# camera basis: screen right = (1,0,-1), up = ..., so we see U, F(left), R(right)
ISO_RIGHT = (0.70710678, 0.0, -0.70710678)
ISO_UP = (0.40824829, 0.81649658, 0.40824829)   # cross(d, right)
ISO_DEPTH = (0.57735027, 0.57735027, 0.57735027)  # toward viewer


def _rot(axis: str, deg: int):
    """Integer rotation matrix about a coordinate axis (right-hand rule)."""
    c = {0: 1, 90: 0, 180: -1, 270: 0}[deg % 360]
    s = {0: 0, 90: 1, 180: 0, 270: -1}[deg % 360]
    if axis == "x":
        return lambda v: (v[0], c * v[1] - s * v[2], s * v[1] + c * v[2])
    if axis == "y":
        return lambda v: (c * v[0] + s * v[2], v[1], -s * v[0] + c * v[2])
    return lambda v: (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2])


class Cube:
    """State = mapping sticker-slot -> colour letter.

    A sticker slot is (position, face) where position is the integer cubie
    coordinate in {-1,0,1}^3 and face is the outward normal letter.
    """

    def __init__(self) -> None:
        self.st: Dict[Tuple[int, int, int], Dict[str, str]] = {}
        for x in (-1, 0, 1):
            for y in (-1, 0, 1):
                for z in (-1, 0, 1):
                    if (x, y, z) == (0, 0, 0):
                        continue
                    d = {}
                    if x == 1: d["R"] = "R"
                    if x == -1: d["L"] = "L"
                    if y == 1: d["U"] = "U"
                    if y == -1: d["D"] = "D"
                    if z == 1: d["F"] = "F"
                    if z == -1: d["B"] = "B"
                    self.st[(x, y, z)] = d

    def copy(self) -> "Cube":
        c = Cube.__new__(Cube)
        c.st = {k: dict(v) for k, v in self.st.items()}
        return c

    # -- moves -------------------------------------------------------
    def turn(self, axis: str, layer: int, deg: int, wide: bool = False) -> "Cube":
        """Rotate stickers on the given layer(s)."""
        R = _rot(axis, deg)
        new: Dict[Tuple[int, int, int], Dict[str, str]] = {}
        layer_idx = {"x": 0, "y": 1, "z": 2}[axis]
        for pos, faces in self.st.items():
            keep = pos[layer_idx] == layer or (wide and pos[layer_idx] == 0)
            if not keep:
                new[pos] = dict(faces)
                continue
            npos = tuple(int(round(v)) for v in R(pos))
            nf = {}
            for f, col in faces.items():
                n = R(FACE_NORMALS[f])
                n = tuple(int(round(v)) for v in n)
                for name, nv in FACE_NORMALS.items():
                    if nv == n:
                        nf[name] = col
                        break
            new[npos] = nf          # type: ignore[assignment]
        self.st = new
        return self

    # -- notation ----------------------------------------------------
    def apply(self, alg: str) -> "Cube":
        for tok in alg.split():
            self.move(tok)
        return self

    def move(self, tok: str) -> "Cube":
        base = tok[0]
        mod = tok[1:]
        deg = 1
        if mod == "2":
            deg = 2
        elif mod == "'":
            deg = 3
        # letter -> (axis, layer, sign, wide)
        table = {
            "U": ("y",  1, -1, False), "D": ("y", -1,  1, False),
            "R": ("x",  1, -1, False), "L": ("x", -1,  1, False),
            "F": ("z",  1, -1, False), "B": ("z", -1,  1, False),
            "r": ("x",  1, -1, True),  "l": ("x", -1,  1, True),
            "u": ("y",  1, -1, True),  "d": ("y", -1,  1, True),
            "f": ("z",  1, -1, True),  "b": ("z", -1,  1, True),
            "M": ("x",  0,  1, False), "E": ("y", 0, -1, False), "S": ("z", 0, -1, False),
            "x": ("x",  0,  1, True),  "y": ("y", 0, -1, True),  "z": ("z", 0, -1, True),
        }
        if base not in table:
            raise ValueError(f"unknown move {tok!r}")
        axis, layer, sign, wide = table[base]
        if base in "xyz":
            # whole-cube rotation: every layer, same direction
            R = _rot(axis, (sign * 90 * deg) % 360)
            new = {}
            for pos, faces in self.st.items():
                npos = tuple(int(round(v)) for v in R(pos))
                nf = {}
                for f, col in faces.items():
                    n = tuple(int(round(v)) for v in R(FACE_NORMALS[f]))
                    for name, nv in FACE_NORMALS.items():
                        if nv == n:
                            nf[name] = col
                            break
                new[npos] = nf
            self.st = new
            return self
        return self.turn(axis, layer, (sign * 90 * deg) % 360, wide)

    # -- queries -----------------------------------------------------
    def solved(self) -> bool:
        return self._faces_uniform()

    def _faces_uniform(self) -> bool:
        for face in FACE_NORMALS:
            cols = {v[face] for v in self.st.values() if face in v}
            if len(cols) > 1:
                return False
        return True

    def face_complete(self, face: str) -> bool:
        cols = {v[face] for v in self.st.values() if face in v}
        return len(cols) == 1

    def layer_complete(self, face: str) -> bool:
        """Whole layer solved (face + its sides aligned)."""
        axis = {"U": "y", "D": "y", "R": "x", "L": "x", "F": "z", "B": "z"}[face]
        idx = {"x": 0, "y": 1, "z": 2}[axis]
        want = 1 if face in "URF" else -1
        cubies = [p for p in self.st if p[idx] == want]
        # every sticker on the layer must match the colour of its own face once solved
        cols = {}
        for p in cubies:
            for f, c in self.st[p].items():
                cols.setdefault(f, set()).add(c)
        return all(len(v) == 1 for v in cols.values()) and len(cols) >= 1
