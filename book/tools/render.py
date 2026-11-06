"""Vector renderer for cube figures.

One geometry source, three outputs:
  * draw_cube(canvas, ...) -> crisp vector art inside the PDF
  * svg(cube, ...)         -> the same figure as SVG, reused later on the web
Every figure is derived from a simulated cube state, never from clip-art.

Geometry convention: a cubie centre lives at a coordinate in {-1,0,1} on each
axis; each cubie is 1.0 wide, so the whole cube spans [-1.5, 1.5].
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

from cube3d import COLORS, FACE_NORMALS, GREY, PLASTIC, Cube

Vec = Tuple[float, float, float]

CUBIE = 1.0              # cubie edge
HALF = 1.5               # half of the whole cube
STICKER = 0.415          # half-size of a sticker (leaves the plastic border)
LIGHT = {"U": 1.00, "F": 0.93, "R": 0.82, "D": 0.96, "B": 0.88, "L": 0.78}

AXES = ("x", "y", "z")

# The world axes are a right-handed frame (Y up, Z toward the viewer). Rubik's
# standard colour scheme is right-handed too: white D, yellow U, green F, blue B,
# red R, orange L. Red/green/yellow then share a corner the way a real cube does.
COLOUR_NAMES_FA = {
    "U": "زرد", "D": "سفید", "F": "سبز", "B": "آبی", "R": "قرمز", "L": "نارنجی",
}


# ------------------------------------------------------------------ camera
def look_at_from(direction: Vec) -> Tuple[Vec, Vec, Vec]:
    """Orthographic camera looking along -direction. Returns (right, up, depth)."""
    n = math.sqrt(sum(c * c for c in direction))
    d = tuple(c / n for c in direction)
    ry0, rz0 = (0.0, 1.0, 0.0)[0], (0.0, 1.0, 0.0)[2]
    wu = (0.0, 1.0, 0.0)
    right = (wu[1] * d[2] - wu[2] * d[1], wu[2] * d[0] - wu[0] * d[2], wu[0] * d[1] - wu[1] * d[0])
    rn = math.sqrt(sum(c * c for c in right))
    right = tuple(c / rn for c in right)
    up = (d[1] * right[2] - d[2] * right[1], d[2] * right[0] - d[0] * right[2], d[0] * right[1] - d[1] * right[0])
    un = math.sqrt(sum(c * c for c in up))
    return right, tuple(c / un for c in up), d


VIEWS = {
    "default": look_at_from((0.60, 0.74, 0.94)),   # U, F, R
    "top": look_at_from((0.55, 1.05, 0.30)),
    "back": look_at_from((-0.60, 0.74, -0.94)),    # U, B, L
    "front": look_at_from((0.05, 0.28, 1.0)),      # F dominant
    "bottom": look_at_from((0.52, -0.70, 0.92)),   # D, F, R - for cross figures
    "low": look_at_from((0.60, 0.42, 0.98)),
}


def _dot(a: Vec, b: Vec) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _proj(v: Vec, basis) -> Tuple[float, float, float]:
    right, up, depth = basis
    return _dot(v, right), _dot(v, up), _dot(v, depth)


def _shade(color, f: float):
    return tuple(min(1.0, max(0.0, c * f)) for c in color)


def _mix(a, b, t: float):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _lighten(color, amount: float):
    """Soft highlight: lift toward white without washing the colour out."""
    return _mix(color, (1.0, 1.0, 1.0), amount)


def _darken(color, amount: float):
    return _mix(color, (0.06, 0.06, 0.08), amount)


# ------------------------------------------------------------------ geometry
def _corners() -> List[Vec]:
    return [(x, y, z) for x in (-HALF, HALF) for y in (-HALF, HALF) for z in (-HALF, HALF)]


def _visible_stickers(cube: Cube, basis):
    """(polygon3d, colour_letter, face_letter) for every sticker facing the camera."""
    depth = basis[2]
    out = []
    for face, normal in FACE_NORMALS.items():
        if _dot(normal, depth) <= 0.02:          # back-face culling
            continue
        ci = AXES.index("xyz"[[abs(v) for v in normal].index(1)])
        sign = normal[ci]
        u_axis, v_axis = ("x", "y", "z")[ci], None
        u_axis = {"x": "y", "y": "x", "z": "x"}[AXES[ci]]
        v_axis = {"x": "z", "y": "z", "z": "y"}[AXES[ci]]
        ui, vi = AXES.index(u_axis), AXES.index(v_axis)
        for pos, faces in cube.st.items():
            if face not in faces or abs(pos[ci] - sign) > 0.5:
                continue
            plane = pos[ci] + sign * CUBIE / 2
            pts = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = list(pos)
                p[ci] = plane
                p[ui] += su * STICKER
                p[vi] += sv * STICKER
                pts.append(tuple(p))
            out.append((pts, faces[face], face))
    return out


def _hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: List[Tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _fit(basis, size: float):
    """Projector: world -> (px, py) inside a size x size box, cube centred."""
    proj = [_proj(c, basis) for c in _corners()]
    xs = [p[0] for p in proj]
    ys = [p[1] for p in proj]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    s = size / (span * 1.06)
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2

    def project(p: Vec) -> Tuple[float, float]:
        x, y, _ = _proj(p, basis)
        return size / 2 + (x - cx) * s, size / 2 - (y - cy) * s

    return project


def _keep(face: str, colour: str, highlight, highlight_by: str) -> bool:
    if not highlight:
        return True
    if highlight_by == "face":
        return face in highlight
    return colour in highlight


# ------------------------------------------------------------------ shading
def _light_dir(basis) -> Tuple[float, float]:
    """2D direction (screen space) that light appears to come from."""
    return (-0.42, 0.91)


def _gradient_colors(base, face: str):
    """Sticker gradient: lit corner -> shadowed corner, per face orientation."""
    lit = _lighten(base, 0.16)
    shaded = _darken(base, 0.10 if face in "UF" else 0.17)
    return lit, shaded


def _rounded_poly_path(c, pts, radius: float = 2.2):
    """Build a ReportLab path for a convex quad with slightly rounded corners."""
    n = len(pts)
    path = c.beginPath()
    for i in range(n):
        p0 = pts[i]
        p1 = pts[(i + 1) % n]
        p_1 = pts[(i - 1) % n]
        v0 = (p0[0] - p_1[0], p0[1] - p_1[1])
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        l0 = max(1e-6, (v0[0] ** 2 + v0[1] ** 2) ** 0.5)
        l1 = max(1e-6, (v1[0] ** 2 + v1[1] ** 2) ** 0.5)
        r = min(radius, l0 / 2.2, l1 / 2.2)
        start = (p0[0] - v0[0] / l0 * r, p0[1] - v0[1] / l0 * r)
        end = (p0[0] + v1[0] / l1 * r, p0[1] + v1[1] / l1 * r)
        if i == 0:
            path.moveTo(*start)
        else:
            path.lineTo(*start)
        path.curveTo(p0[0] - v0[0] / l0 * r * 0.45, p0[1] - v0[1] / l0 * r * 0.45,
                     p0[0] + v1[0] / l1 * r * 0.45, p0[1] + v1[1] / l1 * r * 0.45,
                     *end)
    path.close()
    return path


# ------------------------------------------------------------------ PDF
def draw_cube(c, x: float, y: float, size: float, cube: Optional[Cube] = None,
              view: str = "default", highlight_by: str = "face",
              highlight: Sequence[str] = (), body: bool = True,
              shadow: bool = True, alpha: float = 1.0) -> None:
    """Draw a cube in a `size` x `size` box whose bottom-left corner is (x, y).

    highlight: sticker colours (or faces) kept in colour; everything else greys out.
    """
    cube = cube or Cube()
    basis = VIEWS[view]
    project = _fit(basis, size)

    def at(px: float, py: float) -> Tuple[float, float]:
        return x + px, y + (size - py + size) - size  # project() already flips y

    def at2(px: float, py: float) -> Tuple[float, float]:
        return x + px, y + (size - py)

    hull_pts = [project(p) for p in _corners()]
    hull = _hull(hull_pts)

    if shadow:
        # soft contact shadow under the cube: stacked, faint ellipses
        hx = [p[0] for p in hull_pts]
        hy = [p[1] for p in hull_pts]
        cx = (min(hx) + max(hx)) / 2
        w = (max(hx) - min(hx)) * 0.54
        h = size * 0.032
        cy = min(hy) - size * 0.020
        for k, a in ((1.0, 0.05), (0.78, 0.06), (0.55, 0.07)):
            c.saveState()
            c.setFillColorRGB(0.14, 0.16, 0.20, alpha=a)
            c.ellipse(x + cx - w * k, y + cy - h * k, x + cx + w * k, y + cy + h * k,
                      stroke=0, fill=1)
            c.restoreState()

    if body:
        c.saveState()
        c.setFillColorRGB(*PLASTIC)
        p = c.beginPath()
        p.moveTo(*at2(*hull[0]))
        for q in hull[1:]:
            p.lineTo(*at2(*q))
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.restoreState()

    ldx, ldy = _light_dir(basis)
    for pts, colour, face in _visible_stickers(cube, basis):
        base = COLORS.get(colour, GREY)
        if not _keep(face, colour, highlight, highlight_by):
            base = GREY
        base = _shade(base, LIGHT[face])
        screen = [at2(*project(p)) for p in pts]
        xs = [q[0] for q in screen]
        ys = [q[1] for q in screen]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        lit, dark = _gradient_colors(base, face)
        radius = max(1.0, size * 0.020)

        # sticker = rounded quad, filled with a gradient clipped to the shape
        c.saveState()
        path = _rounded_poly_path(c, screen, radius=radius)
        c.clipPath(path, stroke=0, fill=0)
        if ldx >= 0:
            gx0, gy0, gx1, gy1 = x0, y0, x1, y1
        else:
            gx0, gy0, gx1, gy1 = x1, y0, x0, y1
        try:
            c.linearGradient(gx0, gy0, gx1, gy1, (lit, dark), (0, 1))
        except Exception:
            c.setFillColorRGB(*base)
            c.rect(x0 - 2, y0 - 2, x1 - x0 + 4, y1 - y0 + 4, stroke=0, fill=1)
        c.restoreState()

        # thin darker edge so neighbouring stickers of the same colour stay apart
        c.saveState()
        c.setStrokeColorRGB(*_darken(base, 0.45))
        c.setLineWidth(max(0.35, size * 0.004))
        c.drawPath(_rounded_poly_path(c, screen, radius=radius), stroke=1, fill=0)
        c.restoreState()


# ------------------------------------------------------------------ SVG
def _hx(col) -> str:
    return "#%02x%02x%02x" % tuple(int(round(max(0, min(1, v)) * 255)) for v in col)


def svg(cube: Optional[Cube] = None, size: int = 320, view: str = "default",
        highlight_by: str = "face", highlight: Sequence[str] = (), bg: str = "") -> str:
    cube = cube or Cube()
    basis = VIEWS[view]
    project = _fit(basis, size)
    hull = _hull([project(p) for p in _corners()])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
             f'viewBox="0 0 {size} {size}" role="img">']
    if bg:
        parts.append(f'<rect width="{size}" height="{size}" fill="{bg}"/>')
    d = "M " + " L ".join(f"{px:.2f},{py:.2f}" for px, py in hull) + " Z"
    parts.append(f'<path d="{d}" fill="{_hx(PLASTIC)}"/>')
    for pts, colour, face in _visible_stickers(cube, basis):
        base = COLORS.get(colour, GREY)
        if not _keep(face, colour, highlight, highlight_by):
            base = GREY
        d = "M " + " L ".join(f"{project(p)[0]:.2f},{project(p)[1]:.2f}" for p in pts) + " Z"
        parts.append(f'<path d="{d}" fill="{_hx(_shade(base, LIGHT[face]))}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


# ------------------------------------------------------------------ 2D face maps
FACE_GRID = {
    # face -> 3x3 list of cubie positions, listed visually (top row first, left->right)
    "U": [(-1, 1, 1), (0, 1, 1), (1, 1, 1),
          (-1, 1, 0), (0, 1, 0), (1, 1, 0),
          (-1, 1, -1), (0, 1, -1), (1, 1, -1)],
    "D": [(-1, -1, -1), (0, -1, -1), (1, -1, -1),
          (-1, -1, 0), (0, -1, 0), (1, -1, 0),
          (-1, -1, 1), (0, -1, 1), (1, -1, 1)],
    "F": [(-1, 1, 1), (0, 1, 1), (1, 1, 1),
          (-1, 0, 1), (0, 0, 1), (1, 0, 1),
          (-1, -1, 1), (0, -1, 1), (1, -1, 1)],
}


def draw_face_map(c, x, y, size: float, cube: Cube, face: str = "U",
                  highlight: Sequence[str] = (), highlight_by: str = "face",
                  gap: float = 2.0, pad: float = 0.0, radius: float = 2.5) -> None:
    """A flat 3x3 face diagram (what the reader sees when looking straight at a face)."""
    cells = FACE_GRID[face]
    cell = (size - 2 * pad) / 3
    for i, pos in enumerate(cells):
        col_letter = cube.st[pos].get(face)
        base = COLORS.get(col_letter, GREY)
        if highlight and not _keep(face, col_letter, highlight, highlight_by):
            base = GREY
        col = _shade(base, 1.0 if face in "UF" else 0.95)
        cx = x + pad + (i % 3) * cell
        cy = y + pad + (2 - i // 3) * cell
        c.setFillColorRGB(*col)
        c.roundRect(cx + gap, cy + gap, cell - 2 * gap, cell - 2 * gap,
                    radius, stroke=0, fill=1)
