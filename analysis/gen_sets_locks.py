"""
Fragments for the "Safe sets" and "Locks" views (static HTML, no JavaScript), in
English and French.
"""
from kata_common import *

# ---------------------------------------------------------------- safe sets
valid = sorted((s for s in STARTS if not s["locked"]), key=lambda s: (s["u"], s["h"], s["k"]))
cnt = collections.Counter((s["h"], s["n"]) for s in valid)
tiles = "".join(
    f'<figure class="tile">{grid_svg(s["g"], 5, s["h"], 24, labels=True, title=s["k"])}'
    f'<figcaption><span class="rank">#{i}</span> <b>{both(lambda l: num(s["u"], l))}</b> '
    f'{plural(s["u"], "solution", "solutions")}'
    f'<span class="muted">{s["h"]}×5 · {" ".join(s["k"])}</span></figcaption></figure>'
    for i, s in enumerate(valid, 1))

def sets_text(l):
    if l == "en":
        return f"""
<h1>{num(len(valid), l)} starting sets that never lock</h1>
<p class="lede">Every starting set below fills its rectangle, and stays solvable whichever unused pentominoes are added, in any order, through three additions (3×5 up to 6×5, 4×5 up to 7×5).</p>
<p>Each set is shown as one of its solutions, so the picture is both the piece list and a worked answer. Sets are sorted by their number of solutions, fewest first, so the top of the list is the hardest place to start. Solutions are counted once per shape: turning or mirroring the whole rectangle doesn’t make a new one.</p>
<p class="caption">{num(cnt[3,5], l)} start in 3×5 with 5 pieces, {num(cnt[4,5], l)} in 4×5 with 5 pieces, and {num(cnt[4,6], l)} in 4×5 with 6 pieces. No set uses the same piece twice.</p>"""
    return f"""
<h1>{num(len(valid), l)} combinaisons de départ qui ne se bloquent jamais</h1>
<p class="lede">Chaque combinaison ci-dessous remplit son rectangle et reste soluble quels que soient les pentaminos ajoutés ensuite, dans n’importe quel ordre, sur trois ajouts (de 3×5 à 6×5, de 4×5 à 7×5).</p>
<p>Chaque combinaison est représentée par l’une de ses solutions : l’image donne à la fois la liste des pièces et une réponse. Elles sont triées par nombre de solutions, du plus petit au plus grand : le haut de la liste correspond aux départs les plus difficiles. Les solutions sont comptées une fois par forme : tourner ou retourner tout le rectangle ne crée pas de nouvelle solution.</p>
<p class="caption">{num(cnt[3,5], l)} commencent en 3×5 avec 5 pièces, {num(cnt[4,5], l)} en 4×5 avec 5 pièces et {num(cnt[4,6], l)} en 4×5 avec 6 pièces. Aucune combinaison n’utilise deux fois la même pièce.</p>"""

body1 = bilingual(sets_text) + f'<div class="tiles">{tiles}</div>'
FRAGMENTS["sets"] = (("Starting sets that never lock", "Combinaisons qui ne se bloquent jamais"), body1, "")

# ---------------------------------------------------------------- locks
locked = [s for s in STARTS if s["locked"]]
cat_all = [s for s in STARTS if s["h"] == 4 and s["n"] == 5]   # every lock is in this group
assert all(s["h"] == 4 and s["n"] == 5 for s in locked)
assert all(not any(s["fails"][1:]) for s in STARTS)             # locks only at the first addition
base = len(locked) / len(cat_all)

tried45 = collections.Counter(p for s in cat_all for p in s["unused"])
failed = collections.Counter(p for s in STARTS for p in s["fails"][0])
add_rows = sorted(PENT, key=lambda p: -failed[p] / tried45[p])
mx = max(failed[p] / tried45[p] for p in PENT)
inset = {q: [s for s in cat_all if q in s["k"]] for q in ORDER}
rate = {q: (sum(s["locked"] for s in v) / len(v) if v else 0) for q, v in inset.items()}
mx2 = max(rate.values())
picks = collections.Counter(len(s["fails"][0]) for s in locked)
npent = lambda s: sum(c in PENT for c in s["k"])
ntet = lambda s: sum(len(P[c]["cells"]) == 4 for c in s["k"])
lock_rows = "".join(
    f'<tr><td>{grid_svg(s["g"], 5, 4, 24, labels=True, title=s["k"])}</td>'
    f'<td>{" ".join(s["k"])}</td><td class="n">{both(lambda l: num(s["u"], l))}</td>'
    f'<td><div class="pcs">{"".join(piece_tag(p) for p in s["fails"][0])}</div></td></tr>'
    for s in sorted(locked, key=lambda s: (-len(s["fails"][0]), s["k"])))
top_add = add_rows[0]

def t_add(l):
    return "".join(
        f'<tr><td>{piece_tag(p)} <span class="muted">{plabel(p, l)}</span></td>'
        f'<td class="n"><b>{failed[p]}</b></td><td class="n">{num(tried45[p], l)}</td>'
        f'<td class="n">{pct(failed[p]/tried45[p], l, 1)}</td>'
        f'<td class="barcell"><span class="bar" style="width:{100*failed[p]/tried45[p]/mx:.0f}%"></span></td></tr>'
        for p in add_rows)

def t_in(l):
    return "".join(
        f'<tr><td>{piece_tag(q)} <span class="muted">{plabel(q, l)}</span></td>'
        f'<td class="n"><b>{sum(s["locked"] for s in inset[q])}</b></td><td class="n">{len(inset[q])}</td>'
        f'<td class="n">{pct(rate[q], l)}</td><td class="n">{num(rate[q]/base, l, 2)}×</td>'
        f'<td class="barcell"><span class="bar" style="width:{100*rate[q]/mx2:.0f}%"></span></td></tr>'
        for q in sorted(ORDER, key=lambda q: -rate[q]))

def t_mat(l):
    def cell(q, p):
        att = [s for s in cat_all if q in s["k"] and p in s["unused"]]
        if not att: return '<td class="muted">–</td>'
        f = sum(p in s["fails"][0] for s in att); r = f / len(att)
        alpha = min(1, r / 0.35)
        col = "#fff" if alpha > .6 else "inherit"
        tip = f"{f} of {len(att)}" if l == "en" else f"{f} sur {len(att)}"
        return f'<td style="background:rgba(var(--heat),{alpha:.2f});color:{col}" title="{tip}">{pct(r, l)}</td>'
    head = "In the start set ↓ / added first →" if l == "en" else "Dans le départ ↓ / ajouté en premier →"
    return (f"<thead><tr><th>{head}</th>" + "".join(f"<th>{p}</th>" for p in PENT) + "</tr></thead><tbody>"
            + "".join(f"<tr><td>{piece_tag(q)}</td>" + "".join(cell(q, p) for p in PENT) + "</tr>" for q in ORDER)
            + "</tbody>")

def comp_table(fn, label, l):
    g = collections.defaultdict(lambda: [0, 0])
    for s in cat_all:
        g[fn(s)][0] += 1; g[fn(s)][1] += s["locked"]
    return "".join(f'<tr><td>{k} {label(k)}</td><td class="n"><b>{v[1]}</b></td><td class="n">{v[0]}</td>'
                   f'<td class="n">{pct(v[1]/v[0], l)}</td></tr>' for k, v in sorted(g.items()))

def locks_text(l):
    if l == "en":
        pent_lab = lambda k: plural(k, "pentomino", "pentominoes")
        tet_lab = lambda k: plural(k, "tetromino", "tetrominoes")
        return f"""
<h1>What locks a starting set</h1>
<p class="lede">A starting set is locked when some pentomino, added next, gives a rectangle with no solution. Of {num(len(STARTS), l)} solvable starting sets, {len(locked)} can lock this way.</p>
<div class="keyfacts">
 <div><b>{len(locked)}</b><span>locked starting sets, all of them 4×5 starts with 5 pieces ({pct(base, l)} of that group)</span></div>
 <div><b>0</b><span>locks after the first addition: if the first pentomino fits, every later one does too</span></div>
 <div><b>{sum(failed.values())}</b><span>bad first picks across those sets; {picks[1]} sets have exactly one</span></div>
</div>
<h2>The pentomino added first</h2>
<p>How often each pentomino is a dead end when it is the first one added to a 4×5 five-piece start. Pentomino {top_add} ({plabel(top_add, l)}) is the worst by a wide margin; 2 (the L) almost never locks anything.</p>
<div class="scroll"><table><thead><tr><th>Pentomino added</th><th class="n">Dead ends</th><th class="n">Times possible</th><th class="n">Rate</th><th></th></tr></thead><tbody>{t_add(l)}</tbody></table></div>
<h2>Pieces in the starting set</h2>
<p>Among the {len(cat_all)} solvable 4×5 starts with 5 pieces, the share of those containing each piece that can lock. The last column compares it with the average of {pct(base, l)}. Tetrominoes C (T), D (S) and E (O) are the strongest warning signs.</p>
<div class="scroll"><table><thead><tr><th>Piece in the start set</th><th class="n">Locked</th><th class="n">Sets with it</th><th class="n">Rate</th><th class="n">vs. average</th><th></th></tr></thead><tbody>{t_in(l)}</tbody></table></div>
<h2>Start piece and first pentomino together</h2>
<p>Each cell is the share of 4×5 five-piece starts containing the row’s piece where adding the column’s pentomino first is a dead end. Hover a cell for the raw counts.</p>
<div class="scroll"><table class="heat">{t_mat(l)}</table></div>
<h2>Set composition</h2>
<p>Starts with fewer pentominoes, and so more small pieces, lock far more often.</p>
<div class="scroll"><table><thead><tr><th>4×5 five-piece starts with</th><th class="n">Locked</th><th class="n">Sets</th><th class="n">Rate</th></tr></thead>
<tbody>{comp_table(npent, pent_lab, l)}<tr class="sec"><td colspan="4">By number of tetrominoes</td></tr>{comp_table(ntet, tet_lab, l)}</tbody></table></div>
<h2>Every locked starting set</h2>
<p>Sorted by how many first picks are dead ends ({", ".join(f"{picks[k]} with {k}" for k in sorted(picks, reverse=True))}).</p>
<div class="scroll"><table><thead><tr><th>Starting set, shown as one solution</th><th>Pieces</th><th class="n">Solutions</th><th>Dead end if added first</th></tr></thead><tbody>{lock_rows}</tbody></table></div>"""
    pent_lab = lambda k: plural(k, "pentamino", "pentaminos")
    tet_lab = lambda k: plural(k, "tétramino", "tétraminos")
    return f"""
<h1>Ce qui bloque une combinaison de départ</h1>
<p class="lede">Une combinaison de départ se bloque quand un pentamino, ajouté ensuite, donne un rectangle sans solution. Sur {num(len(STARTS), l)} combinaisons de départ solubles, {len(locked)} peuvent se bloquer ainsi.</p>
<div class="keyfacts">
 <div><b>{len(locked)}</b><span>combinaisons qui peuvent se bloquer, toutes des départs 4×5 à 5 pièces ({pct(base, l)} de ce groupe)</span></div>
 <div><b>0</b><span>blocage après le premier ajout : si le premier pentamino passe, tous les suivants passent aussi</span></div>
 <div><b>{sum(failed.values())}</b><span>mauvais premiers choix dans ces combinaisons ; {picks[1]} n’en ont qu’un seul</span></div>
</div>
<h2>Le pentamino ajouté en premier</h2>
<p>La fréquence à laquelle chaque pentamino mène à une impasse quand il est le premier ajouté à un départ 4×5 à cinq pièces. Le pentamino {top_add} ({plabel(top_add, l)}) est de loin le pire ; le 2 (le L) ne bloque presque jamais rien.</p>
<div class="scroll"><table><thead><tr><th>Pentamino ajouté</th><th class="n">Impasses</th><th class="n">Occasions</th><th class="n">Taux</th><th></th></tr></thead><tbody>{t_add(l)}</tbody></table></div>
<h2>Les pièces du départ</h2>
<p>Parmi les {len(cat_all)} départs 4×5 à 5 pièces solubles, la part de ceux qui contiennent chaque pièce et peuvent se bloquer. La dernière colonne la compare à la moyenne de {pct(base, l)}. Les tétraminos C (T), D (S) et E (O) sont les signaux d’alerte les plus nets.</p>
<div class="scroll"><table><thead><tr><th>Pièce du départ</th><th class="n">Bloquées</th><th class="n">Combinaisons</th><th class="n">Taux</th><th class="n">par rapport à la moyenne</th><th></th></tr></thead><tbody>{t_in(l)}</tbody></table></div>
<h2>Pièce du départ et premier pentamino ensemble</h2>
<p>Chaque case donne la part des départs 4×5 à cinq pièces contenant la pièce de la ligne pour lesquels ajouter d’abord le pentamino de la colonne mène à une impasse. Survolez une case pour voir les effectifs.</p>
<div class="scroll"><table class="heat">{t_mat(l)}</table></div>
<h2>Composition des combinaisons</h2>
<p>Les départs avec moins de pentaminos, donc plus de petites pièces, se bloquent bien plus souvent.</p>
<div class="scroll"><table><thead><tr><th>Départs 4×5 à cinq pièces avec</th><th class="n">Bloquées</th><th class="n">Combinaisons</th><th class="n">Taux</th></tr></thead>
<tbody>{comp_table(npent, pent_lab, l)}<tr class="sec"><td colspan="4">Par nombre de tétraminos</td></tr>{comp_table(ntet, tet_lab, l)}</tbody></table></div>
<h2>Toutes les combinaisons qui peuvent se bloquer</h2>
<p>Triées par nombre de premiers choix menant à une impasse ({", ".join(f"{picks[k]} avec {k}" for k in sorted(picks, reverse=True))}).</p>
<div class="scroll"><table><thead><tr><th>Combinaison de départ, montrée par une solution</th><th>Pièces</th><th class="n">Solutions</th><th>Impasse si ajouté en premier</th></tr></thead><tbody>{lock_rows}</tbody></table></div>"""

FRAGMENTS["locks"] = (("What locks a starting set", "Ce qui bloque une combinaison"), bilingual(locks_text), "")
