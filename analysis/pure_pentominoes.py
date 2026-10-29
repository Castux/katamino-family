"""Run after `make solver`. Difficulty of all 12 pentominoes in 5-wide rectangles (pentominoes only, Katamino-style:
n pieces fill 5 x n). For every subset of n pentominoes, n = 2..7, count tilings."""
import itertools, subprocess, math, collections, os
SOLVER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "solver")
PIECES = {
 "F": [(0,1),(0,2),(1,0),(1,1),(2,1)], "I": [(0,0),(0,1),(0,2),(0,3),(0,4)],
 "L": [(0,0),(1,0),(1,1),(1,2),(1,3)], "N": [(0,0),(1,0),(1,1),(2,1),(3,1)],
 "P": [(0,1),(1,0),(1,1),(2,0),(2,1)], "T": [(0,0),(0,1),(0,2),(1,1),(2,1)],
 "U": [(0,0),(0,1),(0,2),(1,0),(1,2)], "V": [(0,0),(1,0),(2,0),(2,1),(2,2)],
 "W": [(0,0),(1,0),(1,1),(2,1),(2,2)], "X": [(0,1),(1,0),(1,1),(1,2),(2,1)],
 "Y": [(0,0),(1,0),(2,0),(3,0),(1,1)], "Z": [(0,0),(0,1),(1,1),(2,1),(2,2)],
}
N = list(PIECES); idx = {n: i for i, n in enumerate(N)}
jobs = [c for n in range(2, 8) for c in itertools.combinations(N, n)]
lines = [str(len(N))] + [f"{n} 5 " + " ".join(f"{r} {c}" for r, c in PIECES[n]) for n in N]
lines += [str(len(jobs))] + [f"{len(c)} {len(c)} " + " ".join(f"{idx[p]} 1" for p in c) for c in jobs]
out = subprocess.run([SOLVER], input="\n".join(lines) + "\n", capture_output=True, text=True).stdout.split("\n")
U = {"".join(c): int(l.split()[1]) for c, l in zip(jobs, out)}
key = lambda s: "".join(sorted(s, key=N.index))

# (a) share of n-piece sets containing p that tile 5 x n
print("tile rate by set size (sets containing the piece)")
for n in range(2, 8):
    row = {p: sum(U[k] > 0 for k in U if len(k) == n and p in k) / sum(1 for k in U if len(k) == n and p in k) for p in N}
    print(n, " ".join(f"{p}:{row[p]:.2f}" for p in sorted(N, key=lambda p: -row[p])))
# (b) Katamino-style growth: from a tileable set S, add p; compare options (log(u+1) relative to mean)
rel = collections.defaultdict(list); dead = collections.Counter(); tries = collections.Counter()
for k, v in U.items():
    if v == 0 or len(k) == 7: continue
    opts = [p for p in N if p not in k]
    lg = {p: math.log(U[key(k + p)] + 1) for p in opts}; m = sum(lg.values()) / len(lg)
    for p in opts:
        rel[p].append(lg[p] - m); tries[p] += 1; dead[p] += U[key(k + p)] == 0
print("\nadding p to a solvable set: relative factor, dead-end rate")
for p in sorted(N, key=lambda p: -sum(rel[p]) / len(rel[p])):
    print(p, f"x{math.exp(sum(rel[p])/len(rel[p])):.2f}", f"{100*dead[p]/tries[p]:.0f}%")
