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


CENTRE = {"U": (0, 1, 0), "D": (0, -1, 0), "R": (1, 0, 0),
          "L": (-1, 0, 0), "F": (0, 0, 1), "B": (0, 0, -1)}
AXIS = {"U": 1, "D": 1, "R": 0, "L": 0, "F": 2, "B": 2}
SIGN = {"U": 1, "D": -1, "R": 1, "L": -1, "F": 1, "B": -1}


def layer_cubies(c: Cube, face: str):
    ax, sg = AXIS[face], SIGN[face]
    return [p for p in c.st if p[ax] == sg]


def kind(pos) -> str:
    """'centre' | 'edge' | 'corner' — by how many coordinates are zero."""
    zeros = sum(1 for q in pos if q == 0)
    return {1: "edge", 2: "corner", 3: "centre"}.get(zeros, "?")


def is_cross(c: Cube, face: str = "D", colour: str = None) -> bool:
    """Strict cross test.

    Exactly the four edge cubies of the layer carry `colour` on `face`, no corner
    does, and every edge side-sticker matches its own centre colour.
    """
    colour = colour or face
    edges = [p for p in layer_cubies(c, face) if kind(p) == "edge"]
    if len(edges) != 4:
        return False
    for p in edges:
        if c.st[p].get(face) != colour:
            return False
        for f, col in c.st[p].items():
            if f == face:
                continue
            if c.st[CENTRE[f]].get(f) != col:      # side must match its centre
                return False
    return True


def is_daisy(c: Cube, top: str = "U", colour: str = "D") -> bool:
    """Strict daisy test: centre is the top colour, four edges show `colour` up."""
    if c.st[CENTRE[top]].get(top) != top:
        return False
    edges = [p for p in layer_cubies(c, top) if kind(p) == "edge"]
    corners = [p for p in layer_cubies(c, top) if kind(p) == "corner"]
    if len(edges) != 4:
        return False
    if sum(1 for p in edges if c.st[p].get(top) == colour) != 4:
        return False
    if sum(1 for p in corners if c.st[p].get(top) == colour):
        return False
    return True


# keep the old names working
def cross_ok(c: Cube, face: str = "D") -> bool:
    return is_cross(c, face)


def daisy_ok(c: Cube) -> bool:
    return is_daisy(c)


if __name__ == "__main__":
    cands_daisy = ["F2 R2 B2 L2", "F2 R2 B2 L2 U", "x2 F2 R2 B2 L2"]
    for a in cands_daisy:
        print("daisy", a, daisy_ok(scene(a)))
    for a in ["F2 L2 B2 R2", "F2 R2 B2 L2", "F2 B2 L2 R2", "F2 L2 R2 B2"]:
        print("cross", a, cross_ok(scene(a)))
