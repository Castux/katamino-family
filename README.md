# Katamino Family, solved · Gagne ton papa !, résolu

An exhaustive analysis of Gigamic's **Katamino Family** (French title *Gagne ton papa !*,
by André and John Perriolat), plus a website to explore the results and deal random
starting sets for one or two players. The website is bilingual (English / French): every
view exists in both languages and the EN / FR switch in the top bar remembers the choice.

## The game, as analysed

- Pieces (as read from the box): pentominoes **2–8** (L, Y, N, V, P, U, Z), tetrominoes
  **A–E** (I, L, T, S, O), trominoes **Y** (I) and **X** (L), two dominoes **W** and two
  monominoes **V**. The doubles exist so that two players can play at the same time.
- A **starting set** is 5 or 6 *different* pieces filling a 3×5 or 4×5 rectangle.
- After solving it, the player adds an unused pentomino and the rectangle grows by one
  row (width stays 5), up to three times.
- Pieces may be rotated and turned over. Solutions are counted modulo the symmetries of
  the rectangle.

## Main results

| | Box as sold | + printed 1, 9, 10, 12 | + all five missing pentominoes |
|---|---|---|---|
| Solvable starting sets | 1,008 | 2,142 | 2,229 |
| Never lock, whatever is added | 903 | 1,362 | 573 |

- With the box as sold, dead ends only ever happen at the **first** addition. All 105
  lockable starts are 4×5 starts with 5 pieces.
- Pentomino **8 (Z)** is the hardest to add: about half the solutions of a typical pick.
  **6 (P)** is the most forgiving.
- Of the missing pentominoes, **11 (X)** is a lock-maker (a dead end 65% of the time as
  the first addition) and is best left out of this game. **1 (I)** never locks anything.
- The piece labels follow one generation order (longest straight line first, extra
  cubes moving from the end of the line toward its middle). See the Naming page.

## Layout

```
solver/solver.cpp          exhaustive tiling counter (C++, reads jobs on stdin)
solver/solver.go           Go port of the solver, same output, jobs in parallel (-forgiveness mode too)
solver/compare.py          checks a solver against the published data/results_*.json
analysis/pieces.py         piece shapes, box contents, printed extras
analysis/play.py           playable sets, the five difficulty bands, two-player rounds
analysis/forgiveness.py    how forgiving each set is (drives difficulty) -> data/forgiveness.json
analysis/katamino.py       enumerates starting sets and game paths, calls the solver
analysis/kata_common.py    shared loading, SVG drawing and en/fr formatting helpers
analysis/gen_sets_locks.py "Safe sets" and "Locks" views
analysis/gen_growth.py     "Difficulty" view (effect of each added pentomino)
analysis/gen_full12.py     "Full set" view (the five missing pentominoes)
analysis/pure_pentominoes.py  difficulty of all 12 pentominoes in pure 5×n rectangles
site/template.html         website shell: Home, Play, Explorer, Naming, Method
site/build_site.py         assembles everything into build/index.html
data/results_box.json      solved data for the box as sold
data/results_full.json     solved data with all 12 pentominoes
data/forgiveness.json      forgiveness of every starting set
examples/solve_5x5.py      the first small puzzle: six pieces into a 5×5 square
print3d/make_stl.py        3D-printable pieces and boards (see print3d/README.md)
cards/make_cards.py        printable two-player card deck (cards/cards_en.pdf, cards_fr.pdf)
```

## Usage

Requirements: Python 3.8+ (standard library only) and a C++17 compiler.

```sh
make site      # build/index.html from the shipped data (seconds)
make solver    # compile the solver
make solver-go # Go port, same results on all cores (check: python solver/compare.py box build/solver-go)
make cards     # two-player card deck as PDF (needs Chrome or Edge)
make data      # recompute both results files (resumable: progress is cached in build/)
```

`build/index.html` is a single self-contained file. Open it locally or put it on any static
host (GitHub Pages works: publish the file as `index.html`). Views are selected by the
URL hash: `#play`, `#sets`, `#explore`, `#locks`, `#growth`, `#full`, `#naming`, `#method`.

## Play page

- **One player:** choose the pieces (box as sold, or with printed 1, 9, 10, 12), the
  starting rectangle and a difficulty. You get a starting set that never locks, the pool
  of pentominoes to add, and a hidden solution.
- **Two players:** choose a difficulty for each player; the number of rounds follows from
  the starting rectangle (see below). The two sets share no piece except the doubled W and V, and the
  leftover pentominoes form a shared pool that is safe for both.
- Difficulty is how forgiving a set is: the chance that placing its big pieces (4-5
  squares) at random, largest first, leaves gaps its small pieces (1-3 squares) can fill.
  Small pieces patch gaps, so few solutions alone don't make a set hard. Bands are fifths
  per rectangle size, ties broken by solution count.
- Two players on the 5×13 board grow their rectangles to 6 rows each: 3 rounds from a
  3×5 start, 2 from a 4×5 start. Each player uses a separator until 6 + 6, when one
  separator in the middle row serves both.

## Caveats

- Piece shapes were read from a photo of the box; check `analysis/pieces.py` against yours.
- The naming-convention explanation is a reconstruction, not publisher documentation.
