"""
Piece definitions for Gigamic's Katamino Family ("Gagne ton papa !"), read from the box.

Each entry: (id, label, colour, cells as (row, col), copies in the box).
The id is the single character printed on the piece, except for the 10-12
pentominoes (not in the box) which use one-character internal ids; DISPLAY maps
those back to their printed number.
"""
BOX = [
    ("2", "L pentomino", "#f2a65a", [(0,0),(1,0),(1,1),(1,2),(1,3)], 1),
    ("3", "Y pentomino", "#6b3a1f", [(0,0),(1,0),(2,0),(3,0),(1,1)], 1),
    ("4", "N pentomino", "#8e5aa6", [(0,0),(1,0),(1,1),(2,1),(3,1)], 1),
    ("5", "V pentomino", "#2b4fa3", [(0,0),(1,0),(2,0),(2,1),(2,2)], 1),
    ("6", "P pentomino", "#ec7aa0", [(0,1),(1,0),(1,1),(2,0),(2,1)], 1),
    ("7", "U pentomino", "#eee35a", [(0,0),(0,1),(0,2),(1,0),(1,2)], 1),
    ("8", "Z pentomino", "#55b4e3", [(0,0),(0,1),(1,0),(2,0),(2,-1)], 1),
    ("A", "I tetromino", "#ec7aa0", [(0,0),(0,1),(0,2),(0,3)], 1),
    ("B", "L tetromino", "#5fb37a", [(0,0),(0,1),(0,2),(1,2)], 1),
    ("C", "T tetromino", "#55b4e3", [(0,0),(1,0),(2,0),(1,1)], 1),
    ("D", "S tetromino", "#eee35a", [(0,0),(0,1),(1,1),(1,2)], 1),
    ("E", "O tetromino", "#8e5aa6", [(0,0),(0,1),(1,0),(1,1)], 1),
    ("X", "L tromino",   "#6b3a1f", [(0,0),(0,1),(1,1)], 1),
    ("Y", "I tromino",   "#f08a2c", [(0,0),(0,1),(0,2)], 1),
    ("W", "domino",      "#e9b98c", [(0,0),(0,1)], 2),
    ("V", "monomino",    "#e0362c", [(0,0)], 2),
]
# The five pentominoes missing from the box (for 3D printing), numbered by the
# generation order described in the README: I = 1, then T, F, X, W = 9-12.
EXTRA = [
    ("1", "I pentomino", "#c9b28f", [(0,0),(0,1),(0,2),(0,3),(0,4)], 1),
    ("9", "T pentomino", "#2fa39a", [(0,0),(0,1),(0,2),(1,1),(2,1)], 1),
    ("F", "F pentomino", "#a6c64a", [(0,1),(0,2),(1,0),(1,1),(2,1)], 1),
    ("K", "X pentomino", "#b0305c", [(0,1),(1,0),(1,1),(1,2),(2,1)], 1),
    ("M", "W pentomino", "#7083b0", [(0,0),(1,0),(1,1),(2,1),(2,2)], 1),
]
DISPLAY = {"F": "10", "K": "11", "M": "12"}

def piece_set(name):
    """'box' = the box as sold; 'full' = box + the five printed pentominoes.
    Order matters only for canonical keys: box pieces keep their relative order."""
    if name == "box":
        return BOX
    if name == "full":
        return [EXTRA[0]] + BOX[:7] + EXTRA[1:] + BOX[7:]
    raise ValueError(name)
