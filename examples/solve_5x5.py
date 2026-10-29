"""
Exhaustive tree search: fit 6 wooden polyominoes into a 5x5 square.
Pieces may be rotated and flipped (they're flat blocks you can turn over).

Search strategy: always fill the first empty cell (row-major order).
Every piece/orientation that could cover that cell is tried. Because every
solution must cover that cell with *something*, this enumerates every
solution exactly once (no duplicates, nothing missed).
"""

N = 5

# Piece definitions as (row, col) cells
PIECES = {
    "U": [(0,0),(0,1),(0,2),(1,0),(1,2)],          # yellow U-pentomino
    "S": [(0,0),(0,1),(1,1),(1,2)],                # yellow S/Z-tetromino
    "L": [(0,0),(1,0),(1,1),(1,2)],                # teal L-tetromino
    "I": [(0,0),(1,0),(2,0),(3,0)],                # pink 1x4 bar
    "B": [(0,0),(0,1),(1,0)],                      # brown L-tromino
    "V": [(0,0),(1,0),(2,0),(2,1),(2,2)],          # blue V-pentomino
}
NAMES = {"U": "yellow U", "S": "yellow S", "L": "teal L",
         "I": "pink I", "B": "brown corner", "V": "blue V"}

def normalize(cells):
    r0 = min(r for r, c in cells); c0 = min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))

def orientations(cells):
    """All distinct rotations + reflections."""
    out, cur = set(), cells
    for _ in range(4):
        cur = [(c, -r) for r, c in cur]              # rotate 90
        out.add(normalize(cur))
        out.add(normalize([(r, -c) for r, c in cur]))  # mirror
    return list(out)

# For each orientation, store it "anchored" at its first cell in row-major
# order, so placing it on the first empty cell is a simple offset.
ORIENTS = {}
for name, cells in PIECES.items():
    lst = []
    for o in orientations(cells):
        ar, ac = o[0]  # sorted -> first cell is topmost-leftmost
        lst.append([(r - ar, c - ac) for r, c in o])
    ORIENTS[name] = lst

board = [[None] * N for _ in range(N)]
solutions = []
nodes = 0

def first_empty():
    for r in range(N):
        for c in range(N):
            if board[r][c] is None:
                return r, c
    return None

def search(remaining):
    global nodes
    nodes += 1
    cell = first_empty()
    if cell is None:
        solutions.append([row[:] for row in board])
        return
    r0, c0 = cell
    for name in list(remaining):
        for o in ORIENTS[name]:
            placed = [(r0 + dr, c0 + dc) for dr, dc in o]
            if all(0 <= r < N and 0 <= c < N and board[r][c] is None
                   for r, c in placed):
                for r, c in placed: board[r][c] = name
                remaining.remove(name)
                search(remaining)
                remaining.add(name)
                for r, c in placed: board[r][c] = None

# ---- symmetry handling: group solutions under the 8 symmetries of the square
def transforms(g):
    out, cur = [], g
    for _ in range(4):
        cur = [list(row) for row in zip(*cur[::-1])]   # rotate
        out.append(cur)
        out.append([row[::-1] for row in cur])          # mirror
    return out

def key(g): return "".join("".join(row) for row in g)

if __name__ == "__main__":
    search(set(PIECES))
    for name in PIECES:
        print(f"{NAMES[name]:13s}: {len(ORIENTS[name])} orientations")
    print(f"\nSearch tree nodes visited: {nodes}")
    print(f"Total solutions (rotations/reflections counted separately): {len(solutions)}")

    seen, unique = set(), []
    for s in solutions:
        if key(s) in seen: continue
        unique.append(s)
        for t in transforms(s): seen.add(key(t))
    print(f"Distinct solutions up to rotation/reflection of the square: {len(unique)}\n")

    for i, s in enumerate(unique, 1):
        print(f"Solution {i}:")
        for row in s: print("   " + " ".join(row))
        print()
    print("Legend: " + ", ".join(f"{k}={v}" for k, v in NAMES.items()))
