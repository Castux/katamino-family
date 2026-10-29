"""
Builds the website as one self-contained file: build/index.html.

Views are switched by the URL hash (#play, #sets, #explore, #locks, #growth,
#full, #naming, #method), so the site works from a single file, on any static host
or straight from disk.

The analysis views come from the generators in analysis/, which register their
HTML in kata_common.FRAGMENTS. The Play and Explorer views are rendered in the
browser from the JSON embedded here.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
import kata_common as kc
import gen_sets_locks, gen_growth   # noqa: F401  (register fragments)
import gen_full12                   # noqa: F401  (must come last: temporarily swaps kc.P)

BOX = json.load(open(os.path.join(ROOT, "data", "results_box.json")))
FULL = json.load(open(os.path.join(ROOT, "data", "results_full.json")))
OUT = os.path.join(ROOT, "build", "index.html")

# ------------------------------------------------------------------ CSS scoping
def scope(css, sel):
    """Prefix every selector of a flat stylesheet with `sel` (fragment CSS only)."""
    out = []
    for rule in css.split("}"):
        if "{" not in rule:
            continue
        sels, body = rule.split("{", 1)
        sels = ",".join(f"{sel} {s.strip()}" for s in sels.split(",") if s.strip())
        out.append(f"{sels}{{{body}}}")
    return "\n".join(out)

# ------------------------------------------------------------------ data for the browser
def safe_without(fails, banned):
    return not any(not any(c in banned for c in q) for f in fails for q in f)

size_box = {p["name"]: len(p["cells"]) for p in BOX["pieces"]}
box_play = [[k, sum(size_box[c] for c in k) // 5, BOX["sets"][k][1], BOX["sets"][k][2]]
            for k, un, fails in BOX["starts"] if not any(fails)]
EXTRAS = {"1", "9", "F", "M"}               # 11 (X) is left out on purpose
size_full = {p["name"]: len(p["cells"]) for p in FULL["pieces"]}
ext_play = [[k, sum(size_full[c] for c in k) // 5, FULL["sets"][k][1], FULL["sets"][k][2]]
            for k, un, fails in FULL["starts"] if "K" not in k and safe_without(fails, {"K"})]
inv_box = {p["name"]: p["copies"] for p in BOX["pieces"]}
inv_ext = dict(inv_box, **{e: 1 for e in EXTRAS})
order_full = [p["name"] for p in FULL["pieces"]]
pent_box = [p["name"] for p in BOX["pieces"] if len(p["cells"]) == 5]
pent_ext = [n for n in order_full if size_full[n] == 5 and n != "K"]

n_box_safe = len(box_play)
site_data = {
    "pieces": FULL["pieces"], "display": FULL["display"],
    "play": {
        "box": {"sets": box_play, "pentominoes": pent_box, "inventory": inv_box},
        "extras": {"sets": ext_play, "pentominoes": pent_ext, "inventory": inv_ext},
    },
    "explore": {"starts": BOX["starts"], "sets": BOX["sets"], "candidates": BOX["candidates"],
                "maxAdd": BOX["maxAdd"], "order": [p["name"] for p in BOX["pieces"]]},
    "homeFacts": [
        [kc.num(len(BOX["starts"]), "en"), kc.num(len(BOX["starts"]), "fr"),
         f"starting sets fill their 3×5 or 4×5 rectangle, out of {kc.num(len(BOX['candidates']), 'en')} groups with the right area",
         f"combinaisons de départ remplissent leur rectangle 3×5 ou 4×5, sur {kc.num(len(BOX['candidates']), 'fr')} groupes de la bonne aire"],
        [kc.num(n_box_safe, "en"), kc.num(n_box_safe, "fr"),
         "never lock, whichever pentominoes are added and in whatever order",
         "ne se bloquent jamais, quels que soient les pentaminos ajoutés et leur ordre"],
        ["1st", "1er", "addition is the only place a dead end can happen with the box as sold",
         "ajout : le seul moment où une impasse est possible avec la boîte d’origine"],
        [kc.num(len(ext_play), "en"), kc.num(len(ext_play), "fr"),
         "never-locking starts if pentominoes 1, 9, 10 and 12 are 3D-printed and added",
         "départs qui ne se bloquent jamais si l’on imprime en 3D et ajoute les pentaminos 1, 9, 10 et 12"],
    ],
}

# ------------------------------------------------------------------ naming diagram
def pent_order_svg(l):
    C = 14
    W = {"en": ("Line of 5", "Line of 4", "cube walks inward", "Line of 3", "extras at an end", "middle used", "No line of 3",
                "longest straight line", "extra cubes", "faded: not in the box"),
         "fr": ("Ligne de 5", "Ligne de 4", "un cube avance", "Ligne de 3", "ajouts à un bout", "milieu utilisé", "Pas de ligne de 3",
                "plus longue ligne droite", "cubes ajoutés", "en pâle : absent de la boîte")}[l]
    groups = [
        (W[0], "", [("1", [(0, c) for c in range(5)], [])]),
        (W[1], W[2], [("2", [(1, c) for c in range(4)], [(0, 0)]), ("3", [(1, c) for c in range(4)], [(0, 1)])]),
        (W[3], W[4], [("4", [(1, c) for c in range(3)], [(0, 2), (0, 3)]), ("5", [(2, c) for c in range(3)], [(1, 2), (0, 2)]),
                                           ("6", [(1, c) for c in range(3)], [(0, 1), (0, 2)]), ("7", [(1, c) for c in range(3)], [(0, 0), (0, 2)]),
                                           ("8", [(1, c) for c in range(3)], [(0, 0), (2, 2)])]),
        (W[3], W[5], [("9", [(0, c) for c in range(3)], [(1, 1), (2, 1)]), ("10", [(1, c) for c in range(3)], [(0, 1), (2, 2)]),
                                      ("11", [(1, c) for c in range(3)], [(0, 1), (2, 1)])]),
        (W[6], "", [("12", [], [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)])]),
    ]
    letters = dict(zip("1 2 3 4 5 6 7 8 9 10 11 12".split(), "I L Y N V P U Z T F X W".split()))
    kept = set("2345678")
    out, y = [], 24
    for name, sub, ps in groups:
        out.append(f'<text class="gl" x="10" y="{y+16}">{name}</text>')
        if sub: out.append(f'<text class="gs" x="10" y="{y+34}">{sub}</text>')
        for i, (num, spine, extra) in enumerate(ps):
            x0 = 180 + i * 98
            out.append(f'<g{"" if num in kept else " opacity=\"0.3\""}>')
            out += [f'<rect class="sp" x="{x0+c*C}" y="{y+r*C}" width="{C}" height="{C}" stroke="var(--bg)" stroke-width="1"/>' for r, c in spine]
            out += [f'<rect class="ex" x="{x0+c*C}" y="{y+r*C}" width="{C}" height="{C}" stroke="var(--bg)" stroke-width="1"/>' for r, c in extra]
            out.append(f'<text x="{x0}" y="{y+3*C+18}"{" font-weight=\"700\"" if num in kept else ""}>{num} · {letters[num]}</text></g>')
        y += 3 * C + 48
    out.append(f'<rect class="sp" x="10" y="{y}" width="{C}" height="{C}"/><text class="gs" x="30" y="{y+11}">{W[7]}</text>'
               f'<rect class="ex" x="190" y="{y}" width="{C}" height="{C}"/><text class="gs" x="210" y="{y+11}">{W[8]}</text>'
               f'<text class="gs" x="320" y="{y+11}">{W[9]}</text>')
    return (f'<svg viewBox="0 0 680 {y+30}" role="img" aria-label="The 12 pentominoes in generation order; the box keeps 2 to 8">'
            + "".join(out) + "</svg>")

# ------------------------------------------------------------------ assemble
tpl = open(os.path.join(ROOT, "site", "template.html"), encoding="utf-8").read()
base_css = kc.CSS
views, view_css = [], []
for vid in ["sets", "locks", "growth", "full"]:
    title, body, css = kc.FRAGMENTS[vid]
    body = re.sub(r"<nav>.*?</nav>", "", body, flags=re.S)
    views.append(f'<section class="view" id="v-{vid}"><div class="wrap">{body}</div></section>')
    if css:
        view_css.append(scope(css, f"#v-{vid}"))
data = json.dumps(site_data, separators=(",", ":")).replace("</", "<\\/")
html = (tpl.replace("/*BASE_CSS*/", base_css)
           .replace("/*VIEW_CSS*/", "\n".join(view_css))
           .replace("<!--VIEWS-->", "\n".join(views))
           .replace("<!--PENTORDER_EN-->", pent_order_svg("en"))
           .replace("<!--PENTORDER_FR-->", pent_order_svg("fr"))
           .replace("/*DATA*/null", data))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(html)
print(f"{os.path.relpath(OUT, ROOT)}: {len(html)/1e6:.1f} MB, "
      f"{len(box_play)} box and {len(ext_play)} extras starting sets for Play")
