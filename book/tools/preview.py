"""Rasterise figures with PIL for quick visual QA (no PDF engine needed)."""
from PIL import Image, ImageDraw
from cube3d import Cube, COLORS, GREY, PLASTIC
import render

def png(cube, path, size=460, view="default", highlight=(), highlight_by="face", bg="white"):
    basis = render.VIEWS[view]
    project = render._fit(basis, size)
    im = Image.new("RGB", (size, size), bg)
    d = ImageDraw.Draw(im)
    hull = render._hull([project(p) for p in [(a,b,c) for a in (-1,1) for b in (-1,1) for c in (-1,1)]])
    d.polygon(hull, fill=tuple(int(v*255) for v in PLASTIC))
    for pts, colour, face in render._visible_stickers(cube, basis):
        base = COLORS.get(colour, GREY)
        if highlight:
            keep = (face in highlight) if highlight_by == "face" else (colour in highlight)
            base = base if keep else GREY
        col = render._shade(base, render.LIGHT[face])
        d.polygon([project(p) for p in pts], fill=tuple(int(v*255) for v in col))
    im.save(path)

if __name__ == "__main__":
    png(Cube(), "/home/user/my-files/book/_qa_solved.png")
    c = Cube(); c.apply("R U R' U'"); png(c, "/home/user/my-files/book/_qa_scrambled.png")
    print("ok")
