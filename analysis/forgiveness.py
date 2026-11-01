"""
Forgiveness of every playable starting set -> data/forgiveness.json.

Forgiveness is the chance that placing the big pieces (4 or 5 squares) one by one,
largest first, each at random wherever it fits, leaves gaps the small pieces
(1 to 3 squares) can fill exactly. Small pieces patch gaps, so sets with several of
them are forgiving even when they have few solutions. See solver/solver.go.

  make solver-go && python3 analysis/forgiveness.py
"""
import json, os, subprocess, sys, time
from pieces import piece_set

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLVER = os.path.join(ROOT, "build", "solver-go")
OUT = os.path.join(ROOT, "data", "forgiveness.json")

def playable_keys():
    """Starting sets of every pool (box sets are a subset of the full results)."""
    full = json.load(open(os.path.join(ROOT, "data", "results_full.json"), encoding="utf-8"))
    box = json.load(open(os.path.join(ROOT, "data", "results_box.json"), encoding="utf-8"))
    return sorted({k for k, _, _ in full["starts"]} | {k for k, _, _ in box["starts"]})

def main():
    if not any(os.path.exists(SOLVER + ext) for ext in ("", ".exe")):
        sys.exit("build/solver-go not found: run `make solver-go` first")
    pieces = piece_set("full")
    index = {p[0]: i for i, p in enumerate(pieces)}
    size = {p[0]: len(p[3]) for p in pieces}
    keys = playable_keys()
    lines = [str(len(pieces))] + [f"{n} {len(cl)} " + " ".join(f"{r} {c}" for r, c in cl) for n, _, _, cl, _ in pieces]
    lines.append(str(len(keys)))
    for k in keys:
        lines.append(f"{sum(size[c] for c in k) // 5} {len(k)} " + " ".join(f"{index[c]} 1" for c in k))
    t0 = time.time()
    out = subprocess.run([os.path.abspath(SOLVER), "-forgiveness"], input="\n".join(lines) + "\n",
                         capture_output=True, text=True, check=True).stdout.split()
    result = {k: round(float(v), 6) for k, v in zip(keys, out)}
    json.dump(result, open(OUT, "w", encoding="utf-8"), separators=(",", ":"), sort_keys=True)
    print(f"{len(result)} sets in {time.time() - t0:.0f}s -> {os.path.relpath(OUT, ROOT)}", file=sys.stderr)

if __name__ == "__main__":
    main()
