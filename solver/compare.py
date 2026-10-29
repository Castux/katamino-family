"""Feed every set in data/results_<set>.json to a solver and compare with the stored results.
usage: python solver/compare.py <box|full> <solver exe> [extra solver args] [--limit N]"""
import json, os, subprocess, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "analysis"))
from pieces import piece_set

name, exe, *rest = sys.argv[1:]
limit = None
if "--limit" in rest:
    i = rest.index("--limit"); limit = int(rest[i + 1]); rest = rest[:i] + rest[i + 2:]
PIECES = piece_set(name)
NAME = [p[0] for p in PIECES]; SIZE = {p[0]: len(p[3]) for p in PIECES}; IDX = {n: i for i, n in enumerate(NAME)}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sets = json.load(open(os.path.join(ROOT, "data", f"results_{name}.json")))["sets"]
keys = sorted(sets, key=lambda k: (sum(SIZE[c] for c in k), k))[:limit]
lines = [str(len(PIECES))] + [f"{n} {len(cl)} " + " ".join(f"{r} {c}" for r, c in cl) for n, _, _, cl, _ in PIECES]
lines.append(str(len(keys)))
for k in keys:
    counts = {c: k.count(c) for c in dict.fromkeys(k)}
    lines.append(f"{sum(SIZE[c] for c in k)//5} {len(counts)} " + " ".join(f"{IDX[c]} {n}" for c, n in counts.items()))
t0 = time.time()
out = subprocess.run([os.path.abspath(exe), *rest], input="\n".join(lines) + "\n", capture_output=True, text=True, check=True).stdout.split("\n")
dt = time.time() - t0
bad = 0
for k, line in zip(keys, out):
    f, u, s = line.split()
    got = [int(f), int(u), None if s == "-" else s]
    if got != sets[k]:
        bad += 1
        if bad <= 5: print("MISMATCH", k, got, sets[k])
print(f"{name} {os.path.basename(exe)} {' '.join(rest)}: {len(keys)} sets, {bad} mismatches, {dt:.1f}s", flush=True)

