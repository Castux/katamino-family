"""
Fragment for the "Full set" view (English and French): what happens if the five missing pentominoes
(1 = I, 9 = T, 10 = F, 11 = X, 12 = W) are added to the box.
Reads data/results_full.json (from katamino.py --set full).
"""
import kata_common as kc
from kata_common import fmt, FRAGMENTS
import json, os, itertools, collections, math

R = json.load(open(os.path.join(kc.DATA, "results_full.json")))
_saved = kc.P, kc.DISPLAY          # restored at the end: other generators share kata_common
kc.P = {p["name"]: p for p in R["pieces"]}
kc.DISPLAY = R["display"]
P, DISP = kc.P, kc.DISPLAY
ORDER = [p["name"] for p in R["pieces"]]
PENT = [n for n in ORDER if len(P[n]["cells"]) == 5]
NEW = ["1", "9", "F", "K", "M"]
SETS = R["sets"]
lab = lambda n: DISP.get(n, n)
tag = lambda n: kc.piece_tag(n)
key = lambda s: "".join(sorted(s, key=ORDER.index))
u = lambda k: SETS[k][1]
area = lambda k: sum(len(P[c]["cells"]) for c in k)
NAME = {"1": "I", "2": "L", "3": "Y", "4": "N", "5": "V", "6": "P", "7": "U", "8": "Z",
        "9": "T", "F": "F", "K": "X", "M": "W"}

starts = [{"k": k, "unused": un, "fails": [set(f) for f in fs]} for k, un, fs in R["starts"]]

def safe(s, pool):
    """No combination of 1-3 pool pentominoes (not in the start) gives an unsolvable rectangle."""
    return not any(all(c in pool for c in q) for f in s["fails"] for q in f)

# ---------------------------------------------------------- 1. which extras to add
rows = []
for r in range(6):
    for E in itertools.combinations(NEW, r):
        pool = set(p for p in PENT if p not in NEW or p in E)
        st = [s for s in starts if all(c not in NEW or c in E for c in s["k"])]
        orig = [s for s in st if not any(c in NEW for c in s["k"])]
        rows.append({"E": E, "starts": len(st), "safe": sum(safe(s, pool) for s in st),
                     "orig": sum(safe(s, pool) for s in orig), "norig": len(orig)})
base = rows[0]
REC = ("1", "9", "F", "M")
rec = next(r for r in rows if r["E"] == REC)
full = rows[-1]
# ---------------------------------------------------------- 2. per pentomino: dead ends and growth
dead, tri, rel = collections.Counter(), collections.Counter(), collections.defaultdict(list)
for s in starts:
    k, un = s["k"], s["unused"]
    for d in range(3):
        for Q in itertools.combinations(un, d):
            T = key(k + "".join(Q))
            if u(T) == 0: continue
            ok = {}
            for p in un:
                if p in Q: continue
                tri[p, d + 1] += 1
                v = u(key(T + p))
                if v == 0: dead[p, d + 1] += 1
                else: ok[p] = math.log(v / u(T))
            if len(ok) > 1:
                m = sum(ok.values()) / len(ok)
                for p, v in ok.items(): rel[p].append(v - m)
grow = {p: math.exp(sum(rel[p]) / len(rel[p])) for p in PENT}
rate1 = {p: dead[p, 1] / tri[p, 1] for p in PENT}
mx = max(rate1.values())
# ---------------------------------------------------------- 3. locks at later additions
minimal = collections.Counter(); minimal_x = collections.Counter()
for s in starts:
    k, un = s["k"], s["unused"]
    for d in (1, 2, 3):
        for Q in itertools.combinations(un, d):
            if u(key(k + "".join(Q))) == 0 and all(
                    u(key(k + "".join(Rr))) > 0 for r in range(1, d) for Rr in itertools.combinations(Q, r)):
                minimal[d] += 1; minimal_x[d] += "K" in Q

# ---------------------------------------------------------- 4. original starts: who breaks them
orig = [s for s in starts if not any(c in NEW for c in s["k"])]
orig_safe_before = [s for s in orig if safe(s, set(p for p in PENT if p not in NEW))]
culprit = collections.Counter()
for s in orig_safe_before:
    for e in NEW:
        pool = set(p for p in PENT if p not in NEW) | {e}
        if not safe(s, pool): culprit[e] += 1
# ---------------------------------------------------------- 5. examples: X locks
xs = [s for s in orig_safe_before if any(q == "K" for q in s["fails"][0])]
xs = sorted(xs, key=lambda s: -u(s["k"]))[:8]
from kata_common import num, pct, fx, both, bilingual
def pic(k, cell=20): return kc.grid_svg(SETS[k][2], 5, area(k) // 5, cell, labels=True, title=k)
xpics = [(s, pic(s["k"])) for s in xs]
PKIND = {"en": "pentomino", "fr": "pentamino"}

def ename(E, l):
    if not E: return "none (the box as sold)" if l == "en" else "aucun (la boîte d’origine)"
    return ", ".join(f"{lab(e)} ({NAME[e]})" for e in E)

def t_sub(l):
    of = "of" if l == "en" else "sur"
    return "".join(
        f'<tr{" class=sel" if r["E"] == REC else ""}><td>{ename(r["E"], l)}</td><td class="n">{num(r["starts"], l)}</td>'
        f'<td class="n"><b>{num(r["safe"], l)}</b></td><td class="n">{pct(r["safe"]/r["starts"], l)}</td>'
        f'<td class="n">{num(r["orig"], l)} <span class="muted">{of} {num(r["norig"], l)}</span></td></tr>'
        for r in sorted(rows, key=lambda r: (("K" in r["E"]), len(r["E"]), r["E"])))

def t_pent(l):
    new = " · new" if l == "en" else " · nouveau"
    return "".join(
        f'<tr{" class=new" if p in NEW else ""}><td>{tag(p)} <span class="muted">{NAME[p]}{new if p in NEW else ""}</span></td>'
        + "".join(f'<td class="n">{pct(dead[p,d]/tri[p,d], l, 1)}</td>' for d in (1, 2, 3))
        + f'<td class="barcell"><span class="bar" style="width:{100*rate1[p]/mx:.0f}%"></span></td>'
        f'<td class="n">{fx(grow[p], l)}</td></tr>'
        for p in sorted(PENT, key=lambda p: -rate1[p]))

def t_cul(l):
    m = max(1, max(culprit.values()))
    return "".join(
        f'<tr><td>{tag(e)} <span class="muted">{NAME[e]}</span></td><td class="n"><b>{culprit[e]}</b></td>'
        f'<td class="n">{pct(culprit[e]/len(orig_safe_before), l)}</td>'
        f'<td class="barcell"><span class="bar" style="width:{100*culprit[e]/m:.0f}%"></span></td></tr>'
        for e in sorted(NEW, key=lambda e: -culprit[e]))

def t_x(l):
    w = ("solutions in", "no solution") if l == "en" else ("solutions en", "aucune solution")
    return "".join(
        f'<figure class="tile">{svg}<figcaption><b>{num(u(s["k"]), l)}</b> {w[0]} {area(s["k"])//5}×5'
        f'<span class="muted">{" ".join(lab(c) for c in s["k"])} + 11 → {w[1]}</span></figcaption></figure>'
        for s, svg in xpics)

def legend(l):
    return "".join(f'<div class="lg">{kc.shape_svg(n, 14)}<span><b>{lab(n)}</b> '
                   f'{NAME[n] + " pentomino" if l == "en" else "pentamino " + NAME[n]}</span></div>' for n in NEW)

EXTRA = """
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:22px 18px;margin-top:18px}
.tile{margin:0}.tile svg{display:block;max-width:100%;height:auto}
.tile figcaption{margin-top:6px;font-size:.92rem;line-height:1.35}.tile figcaption .muted{display:block;font-size:.84rem}
tr.sel td{background:color-mix(in srgb,var(--box) 22%,transparent);font-weight:600}
td:first-child{white-space:nowrap}
tr.new td:first-child b{text-decoration:underline;text-underline-offset:3px}
.legend{display:flex;flex-wrap:wrap;gap:14px 28px;margin:18px 0 0}
.lg{display:flex;gap:10px;align-items:center;font-size:.95rem}
"""
x_first = rate1["K"]
x_only = rows[[r["E"] for r in rows].index(("K",))]["orig"]
m2 = minimal_x[2] / max(1, minimal[2]); m3 = minimal_x[3] / max(1, minimal[3]); m1 = minimal_x[1] / minimal[1]

def text(l):
    if l == "en":
        return f"""
<h1>Printing the five missing pentominoes</h1>
<p class="lede">The box has 7 of the 12 pentominoes. Adding the other five makes the set complete for classic Katamino. This page checks what they do to this game: same rules, every starting set of 5 or 6 different pieces, up to three pentomino additions in any order.</p>
<div class="legend">{legend(l)}</div>
<p class="caption">Numbered by the generation order described on the <a href="#naming">Naming</a> page: I first, then T, F, X, W after the seven in the box.</p>
<div class="keyfacts">
 <div><b>{num(full["starts"], l)}</b><span>starting sets with all 12 pentominoes available, up from {num(base["starts"], l)}</span></div>
 <div><b>{num(full["safe"], l)}</b><span>of them never lock, fewer than the {num(base["safe"], l)} safe starts in the box as sold</span></div>
 <div><b>{pct(x_first, l)}</b><span>of first additions where 11 (X) is chosen end in a rectangle with no solution</span></div>
</div>
<h2>The short answer</h2>
<p>Print all five for Katamino, but leave 11 (X) out of this game’s pentomino pool, or keep it as a deliberate hard mode. X alone is responsible for most of the damage: with it in the pool, only {num(x_only, l)} of the box’s {num(base["norig"], l)} original starting sets stay safe. Without it, adding 1, 9, 10 and 12 gives <b>{num(rec["safe"], l)}</b> starting sets that never lock, against {num(base["safe"], l)} today. T, F and W each break a few original starts, but far fewer than X does.</p>
<h2>Which extras to add</h2>
<p>Every choice of extra pentominoes. “Starting sets” counts the solvable 3×5 and 4×5 starts that use only the pieces available; “never lock” means every sequence of up to three additions from the pool stays solvable. The last column follows the {num(base["norig"], l)} starting sets that use only the original pieces. Choices that include 11 (X) are listed last. The highlighted row is the suggested set.</p>
<div class="scroll"><table><thead><tr><th>Extra pentominoes printed</th><th class="n">Starting sets</th><th class="n">Never lock</th><th class="n">Share</th><th class="n">Original starts still safe</th></tr></thead><tbody>{t_sub(l)}</tbody></table></div>
<h2>Each pentomino as an addition</h2>
<p>With all 12 in the pool: how often adding each pentomino at the 1st, 2nd or 3rd addition turns a solvable rectangle into one with no solution. The last column is the solution-count factor (compared with the other options at the same moment, among additions that stay solvable). The I bar never locks anything, since on a 5-wide board it can always lie as a full extra row. X is in a different league from every other piece.</p>
<div class="scroll"><table><thead><tr><th>Pentomino</th><th class="n">1st addition</th><th class="n">2nd</th><th class="n">3rd</th><th class="barcell"></th><th class="n">Solutions vs. typical pick</th></tr></thead><tbody>{t_pent(l)}</tbody></table></div>
<h2>Locks can now happen later in the game</h2>
<p>With the box as sold, every dead end was at the first addition. With all 12 pentominoes, {num(minimal[2], l)} combinations of two additions fail even though each addition works on its own, and {num(minimal[3], l)} combinations of three fail even though every smaller step works. X is part of {pct(m2, l)} of the second-stage failures and {pct(m3, l)} of the third-stage ones (first stage: {num(minimal[1], l)} failing additions, {pct(m1, l)} of them X).</p>
<h2>What each new piece does to the original starts</h2>
<p>Of the {num(len(orig_safe_before), l)} original starting sets that never lock today, how many gain a dead end if only that one new pentomino is added to the pool.</p>
<div class="scroll"><table><thead><tr><th>New pentomino in the pool</th><th class="n">Starts that start locking</th><th class="n">Share</th><th></th></tr></thead><tbody>{t_cul(l)}</tbody></table></div>
<h2>X breaking well-behaved starts</h2>
<p>Some of the original starting sets with the most solutions, each shown as one solution, where adding 11 (X) next leaves no solution at all. X’s centre needs a free cell on all four sides, so in a 5-wide board it can only sit in the three middle columns, and the cells it walls off in the corners are hard to fill.</p>
<div class="tiles">{t_x(l)}</div>"""
    return f"""
<h1>Imprimer les cinq pentaminos manquants</h1>
<p class="lede">La boîte contient 7 des 12 pentaminos. Ajouter les cinq autres complète le jeu pour le Katamino classique. Cette page vérifie leur effet sur ce jeu-ci : mêmes règles, toutes les combinaisons de départ de 5 ou 6 pièces différentes, jusqu’à trois ajouts de pentaminos dans n’importe quel ordre.</p>
<div class="legend">{legend(l)}</div>
<p class="caption">Numérotés selon l’ordre de génération décrit à la page <a href="#naming">Noms</a> : le I d’abord, puis T, F, X, W après les sept de la boîte.</p>
<div class="keyfacts">
 <div><b>{num(full["starts"], l)}</b><span>combinaisons de départ avec les 12 pentaminos, contre {num(base["starts"], l)}</span></div>
 <div><b>{num(full["safe"], l)}</b><span>ne se bloquent jamais, moins que les {num(base["safe"], l)} départs sûrs de la boîte d’origine</span></div>
 <div><b>{pct(x_first, l)}</b><span>des premiers ajouts du 11 (X) donnent un rectangle sans solution</span></div>
</div>
<h2>En bref</h2>
<p>Imprimez les cinq pour le Katamino, mais retirez le 11 (X) de la réserve de pentaminos de ce jeu, ou gardez-le comme mode difficile assumé. Le X est responsable de l’essentiel des dégâts : avec lui dans la réserve, seuls {num(x_only, l)} des {num(base["norig"], l)} départs d’origine restent sûrs. Sans lui, ajouter les 1, 9, 10 et 12 donne <b>{num(rec["safe"], l)}</b> combinaisons qui ne se bloquent jamais, contre {num(base["safe"], l)} aujourd’hui. Le T, le F et le W bloquent chacun quelques départs d’origine, mais bien moins que le X.</p>
<h2>Quels pentaminos ajouter</h2>
<p>Tous les choix possibles de pentaminos supplémentaires. « Combinaisons de départ » compte les départs 3×5 et 4×5 solubles avec les seules pièces disponibles ; « ne se bloquent jamais » signifie que toute suite de trois ajouts au plus depuis la réserve reste soluble. La dernière colonne suit les {num(base["norig"], l)} combinaisons qui n’utilisent que les pièces d’origine. Les choix qui incluent le 11 (X) sont en fin de liste. La ligne surlignée est la sélection conseillée.</p>
<div class="scroll"><table><thead><tr><th>Pentaminos imprimés en plus</th><th class="n">Combinaisons de départ</th><th class="n">Ne se bloquent jamais</th><th class="n">Part</th><th class="n">Départs d’origine encore sûrs</th></tr></thead><tbody>{t_sub(l)}</tbody></table></div>
<h2>Chaque pentamino comme ajout</h2>
<p>Avec les 12 dans la réserve : la fréquence à laquelle l’ajout de chaque pentamino, au 1er, 2e ou 3e ajout, transforme un rectangle soluble en rectangle sans solution. La dernière colonne donne le facteur sur le nombre de solutions (par rapport aux autres options au même moment, parmi les ajouts qui restent solubles). La barre I ne bloque jamais rien : sur un plateau de 5 de large, elle peut toujours se poser comme une rangée complète de plus. Le X est dans une catégorie à part.</p>
<div class="scroll"><table><thead><tr><th>Pentamino</th><th class="n">1er ajout</th><th class="n">2e</th><th class="n">3e</th><th class="barcell"></th><th class="n">Solutions par rapport à un choix typique</th></tr></thead><tbody>{t_pent(l)}</tbody></table></div>
<h2>Les blocages peuvent maintenant arriver plus tard</h2>
<p>Avec la boîte d’origine, toutes les impasses arrivaient au premier ajout. Avec les 12 pentaminos, {num(minimal[2], l)} combinaisons de deux ajouts échouent alors que chaque ajout seul fonctionne, et {num(minimal[3], l)} combinaisons de trois échouent alors que chaque étape plus courte fonctionne. Le X est en cause dans {pct(m2, l)} des échecs au deuxième ajout et {pct(m3, l)} au troisième (au premier : {num(minimal[1], l)} ajouts en échec, dont {pct(m1, l)} avec le X).</p>
<h2>L’effet de chaque nouvelle pièce sur les départs d’origine</h2>
<p>Sur les {num(len(orig_safe_before), l)} combinaisons d’origine qui ne se bloquent jamais aujourd’hui, combien deviennent bloquables si l’on ajoute seulement ce nouveau pentamino à la réserve.</p>
<div class="scroll"><table><thead><tr><th>Nouveau pentamino dans la réserve</th><th class="n">Départs qui deviennent bloquables</th><th class="n">Part</th><th></th></tr></thead><tbody>{t_cul(l)}</tbody></table></div>
<h2>Le X casse des départs sans histoire</h2>
<p>Quelques-unes des combinaisons d’origine qui ont le plus de solutions, chacune montrée par une solution, pour lesquelles ajouter ensuite le 11 (X) ne laisse aucune solution. Le centre du X doit avoir une case libre de chaque côté : sur un plateau de 5 de large, il ne peut se placer que dans les trois colonnes du milieu, et les cases qu’il isole dans les coins sont difficiles à remplir.</p>
<div class="tiles">{t_x(l)}</div>"""

FRAGMENTS["full"] = (("Printing the five missing pentominoes", "Imprimer les pentaminos manquants"), bilingual(text), EXTRA)
kc.P, kc.DISPLAY = _saved
