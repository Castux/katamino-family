"""
3D-printable Katamino set: one set of pieces and two boards that cover

  - Katamino            12 pentominoes, 5×3 .. 5×12 rectangles closed by a separator
  - Katamino Family     the box pieces (pentominoes 2-8, tetrominoes A-E, trominoes X Y,
                        two dominoes W, two monominoes V), one or two players
  - Pentomino puzzle    the 12 pentominoes in 6×10 (or 5×12 on the long board)

Every piece is a union of cubes with chamfered edges, so each cube stays visible.

Outputs (default print3d/stl/):
  pieces/<label>_<name>.stl   one file per piece (print each in its own colour)
  board_5x13.stl              long board, continuous 5×13 grid, key slots at every row
  separator_x2.stl            1×5 bar that blocks one row; print two
  tray_6x10.stl               pentomino puzzle board, also stores the 12 pentominoes

Long board: a plain 5×13 grid. A separator fills a whole row and is held by keys
in slots centred on that row. Katamino: a separator in row k + 1 closes a 5×k
rectangle (k = 3..12); without it the whole board is a 5×13 challenge. Two
players: one separator in the middle row gives each player 5×6; with two
separators each player closes their own rectangle (a + b ≤ 11).

Requires: numpy, manifold3d (pip install manifold3d).
"""
import argparse, os, sys
import numpy as np
from manifold3d import Manifold, OpType

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis"))
from pieces import BOX, EXTRA, DISPLAY

# The 12 pentominoes, in printed-label order, plus the Family's smaller pieces.
PENTOMINOES = sorted([p for p in BOX + EXTRA if len(p[3]) == 5], key=lambda p: int(DISPLAY.get(p[0], p[0])))
SMALL = [p for p in BOX if len(p[3]) < 5]

# ---------------------------------------------------------------- primitives
def box(x0, y0, z0, x1, y1, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def chamfered_box(x0, y0, z0, x1, y1, z1, c):
    """Box with every edge chamfered at 45° by c: hull of three inset boxes."""
    return Manifold.batch_hull([
        box(x0 + c, y0 + c, z0, x1 - c, y1 - c, z1),
        box(x0 + c, y0, z0 + c, x1 - c, y1, z1 - c),
        box(x0, y0 + c, z0 + c, x1, y1 - c, z1 - c),
    ])

def union(parts):
    return Manifold.batch_boolean(parts, OpType.Add) if len(parts) > 1 else parts[0]

# ---------------------------------------------------------------- pieces
def piece(cells, a):
    """cells: (row, col) list. Each cube is pitch - 2*gap wide, so neighbouring pieces
    in a full rectangle have 2*gap of play. Cubes of the same piece are joined by
    bridges just inside the chamfers, so the seams read as V grooves."""
    p, g, c = a.cell, a.gap, a.chamfer
    s = p - 2 * g
    parts = []
    cs = set(cells)
    for r, col in cs:
        x, y = col * p + g, -r * p + g
        parts.append(chamfered_box(x, y, 0, x + s, y + s, s, c))
    for r, col in cs:
        x, y = col * p + g, -r * p + g
        if (r, col + 1) in cs:   # bridge to the right
            parts.append(box(x + s / 2, y + c, c, x + p + s / 2, y + s - c, s - c))
        if (r - 1, col) in cs:   # bridge upward (row - 1 is +y)
            parts.append(box(x + c, y + s / 2, c, x + s - c, y + p + s / 2, s - c))
        if {(r, col + 1), (r - 1, col), (r - 1, col + 1)} <= cs:   # fill the 2×2 centre hole
            parts.append(box(x + s / 2, y + s / 2, c, x + p + s / 2, y + p + s / 2, s - c))
    m = union(parts)
    lo = m.bounding_box()[:3]
    return m.translate([-lo[0], -lo[1], 0])

# ---------------------------------------------------------------- boards
def well_board(inner_x, inner_y, a, extra=lambda b, F, H: b):
    """Chamfered slab with a rectangular well [0,inner_x]×[0,inner_y], floor at F."""
    w, F, H, c = a.wall, a.floor, a.floor + a.depth, 1.5
    b = chamfered_box(-w, -w, 0, inner_x + w, inner_y + w, H, c)
    b = b - box(0, 0, F, inner_x, inner_y, H + 1)
    # chamfer the well's top edge
    lip = Manifold.batch_hull([box(0, 0, H - a.lip, inner_x, inner_y, H - a.lip + 0.01),
                               box(-a.lip, -a.lip, H, inner_x + a.lip, inner_y + a.lip, H + 0.01)])
    b = b - lip
    return extra(b, F, H)

def floor_lines(xs, ys, inner_x, inner_y, F, a):
    """Shallow engraved lines on the well floor."""
    lw, ld = 1.0, 0.5
    cuts = [box(x - lw / 2, 0, F - ld, x + lw / 2, inner_y, F + 0.01) for x in xs]
    cuts += [box(0, y - lw / 2, F - ld, inner_x, y + lw / 2, F + 0.01) for y in ys]
    return cuts

def long_board(a, rows=13):
    """5×13 board with one continuous grid. Each long wall has a key slot centred on
    every row, so a separator can take the place of any row."""
    p, cl = a.cell, a.clearance
    inner_x = 2 * cl + rows * p
    inner_y = 2 * cl + 5 * p
    def extra(b, F, H):
        cuts = []
        for j in range(rows):
            xc = cl + (j + 0.5) * p
            cuts.append(box(xc - a.slot / 2, -a.slot_depth, F, xc + a.slot / 2, inner_y + a.slot_depth, H + 1))
        cuts += floor_lines([cl + j * p for j in range(1, rows)], [cl + i * p for i in range(1, 5)],
                            inner_x, inner_y, F, a)
        # dot on the far rim at the middle row (two players, 6 + 6)
        x = cl + (rows // 2 + 0.5) * p
        cuts.append(Manifold.cylinder(1.0, 1.0, 1.0, 24).translate([x, inner_y + a.wall / 2, H - 0.8]))
        return b - union(cuts)
    return well_board(inner_x, inner_y, a, extra)

def separator(a):
    """A 1×5 bar that fills one row, with a key at each end that drops into the wall
    slots. Printed flat, like a piece. A groove along the top marks it as the separator."""
    p, g, cl = a.cell, a.gap, a.clearance
    s = p - 2 * g
    bar = piece([(0, i) for i in range(5)], a)
    length = 5 * p - 2 * g
    reach = cl + g + a.slot_depth - 0.3   # from the bar's end into the slot
    kw = a.slot - 0.4
    keys = [box(-reach, s / 2 - kw / 2, 0, 0.5, s / 2 + kw / 2, a.depth - 0.5),
            box(length - 0.5, s / 2 - kw / 2, 0, length + reach, s / 2 + kw / 2, a.depth - 0.5)]
    stripe = box(a.chamfer + 1, s / 2 - 1, s - 0.8, length - a.chamfer - 1, s / 2 + 1, s + 1)
    m = union([bar] + keys) - stripe
    lo = m.bounding_box()[:3]
    return m.translate([-lo[0], -lo[1], 0])

def tray(a, cols=10, rows=6):
    p, cl = a.cell, a.clearance
    inner_x, inner_y = 2 * cl + cols * p, 2 * cl + rows * p
    def extra(b, F, H):
        cuts = floor_lines([cl + i * p for i in range(1, cols)], [cl + i * p for i in range(1, rows)],
                           inner_x, inner_y, F, a)
        return b - union(cuts)
    return well_board(inner_x, inner_y, a, extra)

# ---------------------------------------------------------------- output
def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, tri
    with open(path, "wb") as f:
        f.write(b"katamino".ljust(80, b" "))
        f.write(np.uint32(len(t)).tobytes())
        f.write(rec.tobytes())

def slug(name):
    return name.lower().replace(" ", "_")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cell", type=float, default=12.5, help="grid pitch in mm (cube size); 12.5 fits a 180 mm bed")
    ap.add_argument("--gap", type=float, default=0.15, help="each cube is cell - 2*gap wide")
    ap.add_argument("--chamfer", type=float, default=1.0, help="cube edge chamfer in mm")
    ap.add_argument("--clearance", type=float, default=0.3, help="extra room at each well wall")
    ap.add_argument("--wall", type=float, default=7.0)
    ap.add_argument("--floor", type=float, default=3.0)
    ap.add_argument("--depth", type=float, default=8.0, help="well depth")
    ap.add_argument("--lip", type=float, default=1.0, help="chamfer on the well's top edge")
    ap.add_argument("--slot", type=float, default=6.0, help="width of the separator key slots")
    ap.add_argument("--slot-depth", type=float, default=2.5, help="how far slots cut into the walls")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl"))
    a = ap.parse_args()

    os.makedirs(os.path.join(a.out, "pieces"), exist_ok=True)
    for pid, name, colour, cells, copies in PENTOMINOES + SMALL:
        label = DISPLAY.get(pid, pid)
        suffix = f"_x{copies}" if copies > 1 else ""
        fn = os.path.join(a.out, "pieces", f"{label}_{slug(name)}{suffix}.stl")
        write_stl(piece(cells, a), fn)
        print("wrote", os.path.relpath(fn))
    for fn, m in [("board_5x13.stl", long_board(a)), ("separator_x2.stl", separator(a)), ("tray_6x10.stl", tray(a))]:
        path = os.path.join(a.out, fn)
        write_stl(m, path)
        x0, y0, z0, x1, y1, z1 = m.bounding_box()
        print(f"wrote {os.path.relpath(path)}  {x1-x0:.1f} x {y1-y0:.1f} x {z1-z0:.1f} mm")

if __name__ == "__main__":
    main()
