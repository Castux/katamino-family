"""
Exhaustive analysis of Katamino Family starting sets (5-wide rectangles).

  python3 analysis/katamino.py --set box    -> data/results_box.json
  python3 analysis/katamino.py --set full   -> data/results_full.json

1. Starting sets: every group of 5 or 6 *different* pieces whose area is 15 (3x5)
   or 20 (4x5) is tested for tilability. (The box holds two W and two V so that two
   players can play at once; a single starting set never uses a piece twice.)
2. Game paths: the player then adds pentominoes not already used, one row per
   pentomino, up to MAX_ADD times. Solvability depends only on the final set of
   pieces, so each start S is checked against every S + Q, Q a subset of its unused
   pentominoes with 1 <= |Q| <= MAX_ADD. Each distinct set is solved once.

Solutions are counted modulo the symmetries of the rectangle. Results are cached
in build/cache_<set>.json after every batch, so an interrupted run resumes.
"""
import argparse, itertools, json, os, subprocess, sys, time
from pieces import piece_set, DISPLAY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLVER = os.path.join(ROOT, "build", "solver")
MAX_ADD = 3
BATCH = 2000

ap = argparse.ArgumentParser()
ap.add_argument("--set", choices=["box", "full"], default="box")
args = ap.parse_args()

PIECES = piece_set(args.set)
NAME = [p[0] for p in PIECES]
SIZE = {p[0]: len(p[3]) for p in PIECES}
IDX = {p[0]: i for i, p in enumerate(PIECES)}
PENTOS = [n for n in NAME if SIZE[n] == 5]
CACHE = os.path.join(ROOT, "build", f"cache_{args.set}.json")
RESULTS = os.path.join(ROOT, "data", f"results_{args.set}.json")

key = lambda ms: "".join(sorted(ms, key=NAME.index))
area = lambda k: sum(SIZE[c] for c in k)

def load_cache():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    if os.path.exists(RESULTS):               # seed from published results
        return {k: {"fixed": f, "unique": u, "sample": s}
                for k, (f, u, s) in json.load(open(RESULTS))["sets"].items()}
    return {}

def run_solver(keys):
    lines = [str(len(PIECES))]
    for n, _, _, cells, _ in PIECES:
        lines.append(f"{n} {len(cells)} " + " ".join(f"{r} {c}" for r, c in cells))
    lines.append(str(len(keys)))
    for k in keys:
        counts = {c: k.count(c) for c in dict.fromkeys(k)}
        lines.append(f"{area(k)//5} {len(counts)} " + " ".join(f"{IDX[c]} {n}" for c, n in counts.items()))
    out = subprocess.run([SOLVER], input="\n".join(lines) + "\n", capture_output=True,
                         text=True, check=True).stdout.split("\n")
    res = {}
    for k, line in zip(keys, out):
        f, u, s = line.split()
        res[k] = {"fixed": int(f), "unique": int(u), "sample": None if s == "-" else s}
    return res

def solve_all(keys, cache):
    todo = sorted((k for k in set(keys) if k not in cache), key=lambda k: (area(k), k))
    t0 = time.time()
    for i in range(0, len(todo), BATCH):
        cache.update(run_solver(todo[i:i + BATCH]))
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        json.dump(cache, open(CACHE, "w"))
        print(f"  solved {min(i + BATCH, len(todo))}/{len(todo)} ({time.time()-t0:.0f}s)", file=sys.stderr)
    return {k: cache[k] for k in keys}

def main():
    if not os.path.exists(SOLVER):
        sys.exit("build/solver not found: run `make solver` first")
    cache = load_cache()
    cands = sorted(key(c) for n in (5, 6) for c in itertools.combinations(NAME, n)
                   if area(c) in (15, 20))
    res = solve_all(cands, cache)
    starts = [k for k in cands if res[k]["unique"] > 0]
    print(f"{len(cands)} candidate starting sets, {len(starts)} tile", file=sys.stderr)
    ext = {}
    for s in starts:
        unused = [p for p in PENTOS if p not in s]
        for d in range(1, MAX_ADD + 1):
            for q in itertools.combinations(unused, d):
                ext[s, q] = key(s + "".join(q))
    res.update(solve_all(list(set(ext.values())), cache))

    report = []
    for s in starts:
        unused = [p for p in PENTOS if p not in s]
        fails = [["".join(q) for q in itertools.combinations(unused, d) if res[ext[s, q]]["unique"] == 0]
                 for d in range(1, MAX_ADD + 1)]
        report.append([s, "".join(unused), fails])
    out = {"display": DISPLAY if args.set == "full" else {},
           "pieces": [{"name": n, "label": l, "color": c, "cells": cl, "copies": cp}
                      for n, l, c, cl, cp in PIECES],
           "maxAdd": MAX_ADD, "candidates": cands, "starts": report,
           "sets": {k: [v["fixed"], v["unique"], v["sample"]] for k, v in res.items()}}
    json.dump(out, open(RESULTS, "w"), separators=(",", ":"))
    print(f"{len(starts)} starting sets, {sum(1 for r in report if any(r[2]))} with a dead end"
          f" -> {os.path.relpath(RESULTS, ROOT)}", file=sys.stderr)

if __name__ == "__main__":
    main()
