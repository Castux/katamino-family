# 3D-printable set

One set of pieces and two boards for three games:

| Game | Pieces | Board |
|---|---|---|
| **Katamino** | the 12 pentominoes 1–12 | long board, a separator closes 5×3 … 5×12; the whole board for 5×13 |
| **Katamino Family**, one or two players | 2–8, A–E, X, Y, 2× W, 2× V | long board: one separator in the middle row gives each player 5×6 |
| **Pentomino puzzle** | the 12 pentominoes | 6×10 tray (or 5×12 on the long board) |

Each piece is a row of cubes with chamfered edges, so you can still see every cube.
Shapes and labels come from `analysis/pieces.py`.

## Build

```sh
pip install numpy manifold3d
python print3d/make_stl.py            # writes print3d/stl/
python print3d/make_stl.py --cell 15  # bigger set for beds of 210 mm or more
```

`python print3d/make_stl.py --help` lists every setting (gap, chamfer, clearance, wall,
well depth, slot size).

## What to print (default 12.5 mm cubes, fits a 180 mm bed such as the Bambu A1 mini)

| File | Count | Size (mm) |
|---|---|---|
| `pieces/1_i_pentomino.stl` … `pieces/12_w_pentomino.stl` | 1 each | 12.2 high |
| `pieces/A_…` to `pieces/E_…`, `X_l_tromino`, `Y_i_tromino` | 1 each | |
| `pieces/W_domino_x2.stl`, `pieces/V_monomino_x2.stl` | **2 each** | |
| `board_5x13.stl` | 1 | 177 × 77 × 11 |
| `separator_x2.stl` | **2** | 67.5 × 12.2 × 12.2, print flat like a piece |
| `tray_6x10.stl` | 1 | 140 × 90 × 11 |

Print the pieces as they come out (flat on the bed). No supports are needed. The 45° chamfers
print cleanly. 0.2 mm layers and 15% infill are plenty. Give each piece its own colour.
`analysis/pieces.py` has the box colours if you want to copy them.

## The long board

A continuous 5×13 grid, like the Katamino Family board. A **separator** is a 1×5 bar the
size of one full row. Each end has a key that drops into a slot centred on that row in
the wall, so the separator takes the place of any row and doesn't slide:

- **Katamino / one player:** put the separator in row k + 1 for a 5×k rectangle
  (3 to 12). Leave it out for a 5×13 challenge.
- **Two players:** one separator in the middle row (the dot on the far rim) gives each
  player 5×6 from their own end. With both separators, each player closes their own
  rectangle (sizes adding up to 11 at most).

The groove along the top of the separator tells it apart from the I pentomino. Printing it
in a neutral colour helps too.

The 6×10 tray is the classic pentomino puzzle. It also stores the 12 pentominoes when
they're packed in a solution. The Family's small pieces fit in the long board.

## Fit

- Every cube is `cell − 2·gap` wide (gap 0.15 mm), so a full rectangle has 0.3 mm of
  play per cell, plus `clearance` (0.3 mm) at each wall.
- If pieces are tight in the board (over-extrusion, elephant's foot), raise `--clearance`
  or `--gap` a little rather than scaling in the slicer. Scaling also shrinks the slots.
- The separator keys are 0.4 mm narrower than their slots (`--slot`, default 6 mm).
