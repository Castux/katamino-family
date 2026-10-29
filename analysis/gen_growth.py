"""
Fragment for the "Difficulty" view (static, English and French): in the 903 starting sets that never lock,
how does each added pentomino change the number of solutions?

Method. A game state is a starting set plus the pentominoes added so far. At each
state the player has several pentominoes to choose from. For each option p,
growth(p) = solutions after adding p / solutions before. Different states have very
different sizes, so each option is compared with the other options available at the
same moment: relative(p) = growth(p) / geometric mean of growth over all options.
Averaging log(relative) over every state gives a per-pentomino factor that is not
distorted by the starting set, the board size or the stage.
"""
from kata_common import *
import itertools, math

SAFE = [s for s in STARTS if not s["locked"]]
u = lambda k: SETS[k][1]
GM = lambda xs: math.exp(sum(xs) / len(xs)) if xs else float("nan")

rel = {d: collections.defaultdict(list) for d in (1, 2, 3)}
worst = {d: collections.Counter() for d in (1, 2, 3)}
fair = {d: collections.Counter() for d in (1, 2, 3)}
n_opt = {d: collections.Counter() for d in (1, 2, 3)}
drops, tries = collections.Counter(), collections.Counter()
moves = []          # (ratio, before key, pentomino, after key)
inter = collections.defaultdict(list)   # (piece in start, pentomino) -> step-1 relative logs
cats = collections.defaultdict(lambda: collections.defaultdict(list))  # start rect -> p -> logs

for s in SAFE:
    k, un = s["k"], s["unused"]
    for d in range(3):
        for Q in itertools.combinations(un, d):
            T = key(k + "".join(Q))
            opts = [p for p in un if p not in Q]
            lg = {p: math.log(u(key(T + p)) / u(T)) for p in opts}
            m = sum(lg.values()) / len(lg)
            lo = min(lg.values()); ws = [p for p in opts if lg[p] == lo]
            for p in opts:
                r = lg[p] - m
                rel[d + 1][p].append(r); cats[s["h"]][p].append(r)
                n_opt[d + 1][p] += 1; fair[d + 1][p] += 1 / len(opts)
                if p in ws: worst[d + 1][p] += 1 / len(ws)
                tries[p] += 1
                after = key(T + p)
                if u(after) < u(T): drops[p] += 1
                moves.append((u(after) / u(T), T, p, after))
                if d == 0:
                    for q in k: inter[q, p].append(r)

# Does a pentomino already on the board slow the *next* additions? (paired within start)
carry = collections.defaultdict(list)
for s in SAFE:
    k, un = s["k"], s["unused"]
    for d in (1, 2):
        steps = []
        for Q in itertools.combinations(un, d):
            T = key(k + "".join(Q))
            steps += [(Q, q, math.log(u(key(T + q)) / u(T))) for q in un if q not in Q]
        for p in un:
            a = [g for Q, q, g in steps if p in Q]
            b = [g for Q, q, g in steps if p not in Q and q != p]
            if a and b: carry[p].append(sum(a) / len(a) - sum(b) / len(b))

# End of the game: sets with all three additions, with vs without p (same start)
final = collections.defaultdict(list)
for s in SAFE:
    k, un = s["k"], s["unused"]
    fin = {Q: math.log(u(key(k + "".join(Q)))) for Q in itertools.combinations(un, 3)}
    for p in un:
        a = [v for Q, v in fin.items() if p in Q]; b = [v for Q, v in fin.items() if p not in Q]
        if a and b: final[p].append(sum(a) / len(a) - sum(b) / len(b))

eff = {p: GM(sum((rel[d][p] for d in (1, 2, 3)), [])) for p in PENT}
order = sorted(PENT, key=lambda p: eff[p])
hardest, easiest = order[0], order[-1]

# ------------------------------------------------------------ pieces of HTML
def diverge(x, span=math.log(3)):
    """Bar centred on ×1, log scale, clipped at ×1/3 and ×3."""
    v = max(-1, min(1, math.log(x) / span)); w = abs(v) * 50
    side = f'class="neg" style="width:{w:.1f}%;right:50%"' if v < 0 else f'class="pos" style="width:{w:.1f}%;left:50%"'
    return f'<span class="dv"><span {side}></span><span class="mid"></span></span>'

def t_main(l):
    return "".join(
        f'<tr><td>{piece_tag(p)} <span class="muted">{plabel(p, l)}</span></td>'
        + "".join(f'<td class="n">{fx(GM(rel[d][p]), l)}</td>' for d in (1, 2, 3))
        + f'<td class="n"><b>{fx(eff[p], l)}</b></td><td class="barcell">{diverge(eff[p])}</td></tr>'
        for p in order)

def t_worst(l):
    return "".join(
        f'<tr><td>{piece_tag(p)}</td>'
        + "".join(f'<td class="n">{pct(worst[d][p]/n_opt[d][p], l)} <span class="muted">({pct(fair[d][p]/n_opt[d][p], l)})</span></td>' for d in (1, 2, 3))
        + "</tr>" for p in order)

def t_drop(l):
    return "".join(
        f'<tr><td>{piece_tag(p)}</td><td class="n"><b>{num(drops[p], l)}</b></td><td class="n">{num(tries[p], l)}</td>'
        f'<td class="n">{pct(drops[p]/tries[p], l, 1)}</td>'
        f'<td class="barcell"><span class="bar" style="width:{100*drops[p]/max(drops.values()):.0f}%"></span></td></tr>'
        for p in order)

def t_cat(l):
    return "".join(f'<tr><td>{piece_tag(p)}</td><td class="n">{fx(GM(cats[3][p]), l)}</td><td class="n">{fx(GM(cats[4][p]), l)}</td></tr>' for p in order)

def t_late(l):
    return "".join(f'<tr><td>{piece_tag(p)}</td><td class="n">{fx(GM(carry[p]), l)}</td><td class="n"><b>{fx(GM(final[p]), l)}</b></td></tr>' for p in order)

def t_int(l):
    def heat(x):
        v = max(-1, min(1, math.log(x) / math.log(4))); a = abs(v)
        bg = f"rgba(var(--heat),{a:.2f})" if v < 0 else f"rgba(var(--good),{a:.2f})"
        return f'<td style="background:{bg};color:{"#fff" if a > .6 else "inherit"}">{num(x, l, 2)}</td>'
    head = "In the start set ↓ / added first →" if l == "en" else "Dans le départ ↓ / ajouté en premier →"
    return (f"<thead><tr><th>{head}</th>" + "".join(f"<th>{p}</th>" for p in order) + "</tr></thead><tbody>"
            + "".join(f"<tr><td>{piece_tag(q)}</td>" + "".join(
                heat(GM(inter[q, p])) if inter[q, p] else '<td class="muted">–</td>' for p in order) + "</tr>"
                for q in ORDER) + "</tbody>")

seen, ex = set(), []
for ratio, T, p, after in sorted(moves):
    if (T, p) in seen: continue
    seen.add((T, p)); ex.append((ratio, T, p, after))
    if len(ex) == 12: break
def pic(k, cell=20):
    return grid_svg(SETS[k][2], 5, area(k) // 5, cell, labels=True, title=k)
pairs = "".join(
    f'<figure class="pair"><div class="pp">{pic(T)}<span class="arrow">+ {p}</span>{pic(after)}</div>'
    f'<figcaption><b>{both(lambda l: num(u(T), l))} → {both(lambda l: num(u(after), l))}</b> solutions'
    f'<span class="muted">{area(T)//5}×5 {" ".join(T)}, {both(lambda l: "then" if l == "en" else "puis")} {area(after)//5}×5 '
    f'{both(lambda l: "with" if l == "en" else "avec")} {p}</span></figcaption></figure>'
    for ratio, T, p, after in ex)
n_moves = len(moves)

EXTRA_CSS = """
.dv{position:relative;display:block;height:12px}
.dv .neg,.dv .pos{position:absolute;top:1px;height:10px;border-radius:5px}
.dv .neg{background:var(--bad)} .dv .pos{background:var(--good-solid)}
.dv .mid{position:absolute;left:50%;top:-3px;bottom:-3px;width:1.5px;background:var(--ink)}
.pairs{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:26px 22px;margin-top:18px}
.pair{margin:0}
.pp{display:flex;align-items:center;gap:10px}
.pp svg{flex:none}
.arrow{font-weight:700;white-space:nowrap}
.pair figcaption{margin-top:6px;font-size:.92rem;line-height:1.35}
.pair figcaption .muted{display:block;font-size:.84rem}
"""
w1 = worst[1][hardest] / n_opt[1][hardest]
H, E = hardest, easiest

def text(l):
    if l == "en":
        return f"""
<h1>Which pentomino makes the next stage harder</h1>
<p class="lede">In the {num(len(SAFE), l)} starting sets that never lock, every rectangle stays solvable. But some pentominoes leave far fewer solutions than others when they are added. This page measures that across all {num(n_moves, l)} possible pentomino additions in those games.</p>
<div class="keyfacts">
 <div><b>{fx(eff[H], l)}</b><span>solutions after adding {H} ({plabel(H, l)}), compared with the average option at the same moment</span></div>
 <div><b>{pct(w1, l)}</b><span>of first additions where {H} is available, it leaves the fewest solutions of all the options</span></div>
 <div><b>{fx(eff[E], l)}</b><span>for {E} ({plabel(E, l)}), the most forgiving pentomino to add</span></div>
</div>
<h2>How the comparison works</h2>
<p>At any moment in a game, the player has a few unused pentominoes to choose from. For each one, the growth is the number of solutions after adding it divided by the number before. Bigger rectangles usually have more solutions, so growth depends heavily on where you are in the game. To remove that, each option is compared with the other options available at the same moment: a factor of ×0.50 means adding that pentomino leaves half as many solutions as a typical alternative would. Factors are geometric means over every starting set and every order of play. Solution counts are modulo turning and mirroring the whole rectangle.</p>
<h2>Effect of each pentomino, by stage</h2>
<p>{H} is the hard one at every stage, followed by 7 (U) and 4 (N). {E} (P) gives more than twice the solutions of a typical pick, and 2 (L) about 60% more. The effect barely changes from the first addition to the third.</p>
<div class="scroll"><table><thead><tr><th>Pentomino added</th><th class="n">1st addition</th><th class="n">2nd</th><th class="n">3rd</th><th class="n">All stages</th><th class="barcell"><span class="muted">fewer ← ×1 → more</span></th></tr></thead><tbody>{t_main(l)}</tbody></table></div>
<h2>How often it’s the worst option</h2>
<p>The share of decisions in which that pentomino leaves the fewest solutions among the options available. The figure in brackets is what it would be if every option were equally likely to be worst. By the third addition, {H} is the worst option almost every time it’s on the table; {E} essentially never is.</p>
<div class="scroll"><table><thead><tr><th>Pentomino</th><th class="n">1st addition</th><th class="n">2nd</th><th class="n">3rd</th></tr></thead><tbody>{t_worst(l)}</tbody></table></div>
<h2>When adding a piece leaves fewer solutions than before</h2>
<p>The rectangle grows by a row with each pentomino, so the count usually goes up. These are the additions where it went down instead: the bigger puzzle has fewer solutions than the smaller one.</p>
<div class="scroll"><table><thead><tr><th>Pentomino added</th><th class="n">Count went down</th><th class="n">Additions</th><th class="n">Rate</th><th></th></tr></thead><tbody>{t_drop(l)}</tbody></table></div>
<h2>Does the damage carry over?</h2>
<p>It would be natural to expect some pieces to make the following stages harder. The data says the cost is paid once, when the piece goes in. The first column compares the growth of the next additions when the pentomino is already on the board with when it isn’t, within the same starting set. Every factor is close to ×1, so later stages grow at their usual rate. The second column is the net result at the end of the game: the final rectangles (all three additions) that include the pentomino against those that don’t, from the same start. Because the lower count persists, ending with {H} in the set means about a third as many solutions.</p>
<div class="scroll"><table><thead><tr><th>Pentomino</th><th class="n">Next additions, if already placed</th><th class="n">Final rectangle, with vs. without</th></tr></thead><tbody>{t_late(l)}</tbody></table></div>
<h2>By starting rectangle</h2>
<p>The same ranking holds whether the game starts in 3×5 or 4×5.</p>
<div class="scroll"><table><thead><tr><th>Pentomino</th><th class="n">Games starting 3×5</th><th class="n">Games starting 4×5</th></tr></thead><tbody>{t_cat(l)}</tbody></table></div>
<h2>Start piece and first pentomino together</h2>
<p>The factor for the first addition, split by which pieces are in the starting set. Red is fewer solutions than a typical pick, green more. {H}’s penalty appears whatever the start contains (between ×0.34 and ×0.52); it is steepest when the start holds C (T) or X (the L tromino).</p>
<div class="scroll"><table class="heat">{t_int(l)}</table></div>
<h2>The steepest drops</h2>
<p>The twelve additions that cut the solution count the most, each shown as one solution before and after.</p>"""
    return f"""
<h1>Quel pentamino complique l’étape suivante</h1>
<p class="lede">Dans les {num(len(SAFE), l)} combinaisons de départ qui ne se bloquent jamais, tous les rectangles restent solubles. Mais certains pentaminos laissent beaucoup moins de solutions que d’autres quand on les ajoute. Cette page le mesure sur les {num(n_moves, l)} ajouts de pentamino possibles dans ces parties.</p>
<div class="keyfacts">
 <div><b>{fx(eff[H], l)}</b><span>de solutions après l’ajout du {H} ({plabel(H, l)}), par rapport à l’option moyenne au même moment</span></div>
 <div><b>{pct(w1, l)}</b><span>des premiers ajouts où le {H} est disponible, c’est lui qui laisse le moins de solutions</span></div>
 <div><b>{fx(eff[E], l)}</b><span>pour le {E} ({plabel(E, l)}), le pentamino le plus facile à ajouter</span></div>
</div>
<h2>Comment se fait la comparaison</h2>
<p>À chaque moment de la partie, le joueur a le choix entre quelques pentaminos inutilisés. Pour chacun, la croissance est le nombre de solutions après l’ajout divisé par le nombre avant. Les grands rectangles ont en général plus de solutions, donc la croissance dépend beaucoup de l’avancement de la partie. Pour neutraliser cet effet, chaque option est comparée aux autres options disponibles au même moment : un facteur de ×0,50 signifie que ce pentamino laisse deux fois moins de solutions qu’une option typique. Les facteurs sont des moyennes géométriques sur toutes les combinaisons de départ et tous les ordres de jeu. Les solutions sont comptées sans les rotations ni les symétries du rectangle entier.</p>
<h2>Effet de chaque pentamino, par étape</h2>
<p>Le {H} est le plus difficile à chaque étape, suivi du 7 (U) et du 4 (N). Le {E} (P) donne plus de deux fois plus de solutions qu’un choix typique, et le 2 (L) environ 60 % de plus. L’effet change à peine entre le premier et le troisième ajout.</p>
<div class="scroll"><table><thead><tr><th>Pentamino ajouté</th><th class="n">1er ajout</th><th class="n">2e</th><th class="n">3e</th><th class="n">Toutes étapes</th><th class="barcell"><span class="muted">moins ← ×1 → plus</span></th></tr></thead><tbody>{t_main(l)}</tbody></table></div>
<h2>À quelle fréquence c’est la pire option</h2>
<p>La part des décisions où ce pentamino laisse le moins de solutions parmi les options disponibles. Entre parenthèses : ce que ce serait si toutes les options avaient la même chance d’être la pire. Au troisième ajout, le {H} est presque toujours la pire option quand il est disponible ; le {E} ne l’est pratiquement jamais.</p>
<div class="scroll"><table><thead><tr><th>Pentamino</th><th class="n">1er ajout</th><th class="n">2e</th><th class="n">3e</th></tr></thead><tbody>{t_worst(l)}</tbody></table></div>
<h2>Quand un ajout laisse moins de solutions qu’avant</h2>
<p>Le rectangle grandit d’une rangée à chaque pentamino, donc le nombre de solutions augmente en général. Voici les ajouts où il a diminué : le plus grand casse-tête a moins de solutions que le plus petit.</p>
<div class="scroll"><table><thead><tr><th>Pentamino ajouté</th><th class="n">Nombre en baisse</th><th class="n">Ajouts</th><th class="n">Taux</th><th></th></tr></thead><tbody>{t_drop(l)}</tbody></table></div>
<h2>L’effet se prolonge-t-il ?</h2>
<p>On pourrait s’attendre à ce que certaines pièces compliquent les étapes suivantes. Les données montrent que le coût se paie une seule fois, au moment où la pièce entre. La première colonne compare la croissance des ajouts suivants selon que le pentamino est déjà en jeu ou non, pour une même combinaison de départ. Tous les facteurs sont proches de ×1 : les étapes suivantes progressent au rythme habituel. La seconde colonne donne le bilan en fin de partie : les rectangles finaux (après trois ajouts) qui contiennent le pentamino, comparés à ceux qui ne le contiennent pas, depuis le même départ. Comme la baisse persiste, finir avec le {H} donne environ trois fois moins de solutions.</p>
<div class="scroll"><table><thead><tr><th>Pentamino</th><th class="n">Ajouts suivants, s’il est déjà placé</th><th class="n">Rectangle final, avec ou sans</th></tr></thead><tbody>{t_late(l)}</tbody></table></div>
<h2>Selon le rectangle de départ</h2>
<p>Le classement est le même que la partie commence en 3×5 ou en 4×5.</p>
<div class="scroll"><table><thead><tr><th>Pentamino</th><th class="n">Parties en 3×5</th><th class="n">Parties en 4×5</th></tr></thead><tbody>{t_cat(l)}</tbody></table></div>
<h2>Pièce du départ et premier pentamino ensemble</h2>
<p>Le facteur du premier ajout, selon les pièces présentes au départ. Rouge : moins de solutions qu’un choix typique ; vert : plus. La pénalité du {H} apparaît quel que soit le départ (entre ×0,34 et ×0,52) ; elle est la plus forte quand le départ contient le C (T) ou le X (le triomino L).</p>
<div class="scroll"><table class="heat">{t_int(l)}</table></div>
<h2>Les plus fortes baisses</h2>
<p>Les douze ajouts qui réduisent le plus le nombre de solutions, chacun montré par une solution avant et après.</p>"""

body = bilingual(text) + f'<div class="pairs">{pairs}</div>'
FRAGMENTS["growth"] = (("Which pentomino makes the next stage harder", "Quel pentamino complique la suite"), body, EXTRA_CSS)
