"""Cube states used by the sample pages, each verified by a property check."""
from __future__ import annotations

from cube3d import Cube

WHITE, YELLOW = "D", "U"


def inv(alg: str) -> str:
    out = []
    for tok in reversed(alg.split()):
        if tok.endswith("2"):
            out.append(tok)
        elif tok.endswith("'"):
            out.append(tok[:-1])
        else:
            out.append(tok + "'")
    return " ".join(out)


def scene(alg: str = "") -> Cube:
    c = Cube()
    if alg:
        c.apply(alg)
    return c


# ---------------------------------------------------------------- checks
def face_colors(c: Cube, face: str) -> set:
    return {v[face] for v in c.st.values() if face in v}


def daisy_ok(c: Cube) -> bool:
    """Four white edges standing around the yellow centre on top."""
    u = [v for p, v in c.st.items() if p[1] == 1 and "U" in v]
    whites = sum(1 for v in u if v["U"] == WHITE)
    centre_yellow = c.st[(0, 1, 0)]["U"] == YELLOW
    return whites == 4 and centre_yellow


def cross_ok(c: Cube, face: str = "D") -> bool:
    axis = {"U": 1, "D": 1, "R": 0, "L": 0, "F": 2, "B": 2}[face]
    layer = 1 if face in "URF" else -1
    edges = [(0, 1, 0)] if False else None
    ok = True
    for p, v in c.st.items():
        if p[axis] != layer:
            continue
        if sum(1 for q in p if q != 0) != 1:       # edges only
            continue
        if v.get(face) != face:
            ok = False
    # side stickers of those edges must match their centres
    for p, v in c.st.items():
        if p[axis] != layer or sum(1 for q in p if q != 0) != 1:
            continue
        for f, col in v.items():
            if f == face:
                continue
            centre = [0, 0, 0]
            centre[{"x": 0, "y": 1, "z": 2}[f.lower()]] = 0
            cpos = {"U": (0, 1, 0), "D": (0, -1, 0), "R": (1, 0, 0),
                    "L": (-1, 0, 0), "F": (0, 0, 1), "B": (0, 0, -1)}[f]
            if c.st[cpos][f] != col:
                ok = False
    return ok


if __name__ == "__main__":
    cands_daisy = ["F2 R2 B2 L2", "F2 R2 B2 L2 U", "x2 F2 R2 B2 L2"]
    for a in cands_daisy:
        print("daisy", a, daisy_ok(scene(a)))
    for a in ["F2 L2 B2 R2", "F2 R2 B2 L2", "F2 B2 L2 R2", "F2 L2 R2 B2"]:
        print("cross", a, cross_ok(scene(a)))
