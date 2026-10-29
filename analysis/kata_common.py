"""
Shared data loading and SVG drawing helpers for the report generators.
Reads data/results_box.json (the box as sold). Generators register their
page fragments in FRAGMENTS; site/build_site.py assembles them into the website.
"""
import json, os, collections, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
D = json.load(open(os.path.join(DATA, "results_box.json")))
FRAGMENTS = {}   # view id -> (title, body html, extra css)
P = {p["name"]: p for p in D["pieces"]}
ORDER = [p["name"] for p in D["pieces"]]
PENT = [n for n in ORDER if len(P[n]["cells"]) == 5]
SETS = D["sets"]
area = lambda k: sum(len(P[c]["cells"]) for c in k)
key = lambda s: "".join(sorted(s, key=ORDER.index))
fmt = lambda n: f"{n:,}"
INK = "#1b1208"
DISPLAY = {}  # internal one-character id -> printed label (e.g. "F" -> "10")
DARK_TEXT = {"3", "X", "5"}

STARTS = [{"k": k, "unused": u, "fails": f, "h": area(k) // 5, "n": len(k),
           "u": SETS[k][1], "fx": SETS[k][0], "g": SETS[k][2], "locked": any(f)}
          for k, u, f in D["starts"]]

# ---------------------------------------------------------------- drawing
def grid_svg(g, w, h, cell, labels=False, transpose=False, fluid=False, title="solution"):
    at = lambda r, c: g[r * w + c]
    R, C, get = h, w, at
    if transpose:
        R, C, get = w, h, (lambda r, c: at(c, r))
    W, H, sw = C * cell, R * cell, max(1.2, cell / 14)
    size = 'width="100%"' if fluid else f'width="{W}" height="{H}"'
    s = [f'<svg {size} viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(title)}">']
    for r in range(R):
        for c in range(C):
            s.append(f'<rect x="{c*cell}" y="{r*cell}" width="{cell+.5}" height="{cell+.5}" fill="{P[get(r,c)]["color"]}"/>')
    diff = lambda a, b: a != b or a == "V"
    d = []
    for r in range(R):
        for c in range(C):
            if c + 1 < C and diff(get(r, c), get(r, c + 1)): d.append(f"M{(c+1)*cell} {r*cell}v{cell}")
            if r + 1 < R and diff(get(r, c), get(r + 1, c)): d.append(f"M{c*cell} {(r+1)*cell}h{cell}")
    s.append(f'<path d="{"".join(d)}" stroke="{INK}" stroke-width="{sw}" fill="none" stroke-linecap="square"/>')
    s.append(f'<rect x="{sw/2}" y="{sw/2}" width="{W-sw}" height="{H-sw}" fill="none" stroke="{INK}" stroke-width="{sw}"/>')
    if labels:
        seen = set()
        for r in range(R):
            for c in range(C):
                ch = get(r, c); ident = f"V{r},{c}" if ch == "V" else ch
                if ident in seen: continue
                seen.add(ident)
                s.append(f'<text x="{c*cell+cell/2}" y="{r*cell+cell/2}" dy=".35em" text-anchor="middle" '
                         f'font-size="{cell*(.42 if len(DISPLAY.get(ch, ch)) == 1 else .36):.1f}" font-weight="700" font-family="Bricolage Grotesque,system-ui,sans-serif" fill="{"#fff" if ch in DARK_TEXT else INK}">{DISPLAY.get(ch, ch)}</text>')
    s.append("</svg>")
    return "".join(s)

def shape_svg(name, cell=13):
    cs = P[name]["cells"]
    mr, mc = min(r for r, _ in cs), min(c for _, c in cs)
    h = max(r for r, _ in cs) - mr + 1; w = max(c for _, c in cs) - mc + 1
    s = [f'<svg width="{w*cell}" height="{h*cell}" viewBox="0 0 {w*cell} {h*cell}" aria-hidden="true">']
    for r, c in cs:
        s.append(f'<rect x="{(c-mc)*cell}" y="{(r-mr)*cell}" width="{cell}" height="{cell}" fill="{P[name]["color"]}" stroke="{INK}" stroke-width="1.2"/>')
    return "".join(s) + "</svg>"

def piece_tag(n):
    return f'<span class="pc">{shape_svg(n, 9)}<b>{DISPLAY.get(n, n)}</b></span>'

# ---------------------------------------------------------------- page shell
CSS = """
:root{--bg:#f5ead6;--panel:#ecdcc0;--ink:#2e1e10;--muted:#6e5638;--line:#cdb48d;--box:#f29e2e;--bad:#c9302a;--heat:201,48,42;
 color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#1d150e;--panel:#2a1f15;--ink:#f3e6d0;--muted:#bfa685;--line:#4a3826;--box:#f2a640;--bad:#ff6b5e;--heat:255,107,94;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#1d150e;--panel:#2a1f15;--ink:#f3e6d0;--muted:#bfa685;--line:#4a3826;--box:#f2a640;--bad:#ff6b5e;--heat:255,107,94;color-scheme:dark}
*,*::before,*::after{box-sizing:inherit}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Bricolage Grotesque",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:17px;line-height:1.5;font-variant-numeric:tabular-nums}
.wrap{max-width:1000px;margin:0 auto;padding:44px 20px 80px}
h1{font-size:clamp(2rem,5.5vw,3.2rem);line-height:1.04;font-weight:800;letter-spacing:-.02em;margin:0 0 16px;max-width:16ch}
h2{font-size:1.45rem;font-weight:800;margin:52px 0 10px}
p{max-width:68ch;margin:0 0 12px}
.lede{font-size:1.12rem;color:var(--muted)}
.caption,.muted{color:var(--muted);font-size:.9rem}
nav{font-size:.95rem;margin:0 0 26px}
nav a{color:var(--ink);text-underline-offset:3px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
th{font-weight:600;font-size:.9rem;color:var(--muted)}
td.n,th.n{text-align:right;white-space:nowrap}
td.n b{font-size:1.1rem}
.pcs{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}
.pc{display:inline-flex;align-items:center;gap:4px}
.pc b{font-weight:700;font-size:.92rem}
.rank{color:var(--muted);font-size:.85rem;width:3em}
.sec{background:var(--panel)} .sec td{font-weight:700;padding:10px}
.bar{display:block;height:10px;border-radius:5px;background:var(--bad);min-width:2px}
.barcell{width:40%}
.heat td{text-align:center;font-size:.85rem;padding:6px 4px;min-width:3.2em}
.heat th{text-align:center}
.heat th:first-child,.heat td:first-child{text-align:left}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:22px 18px;margin-top:22px}
.tile{margin:0}
.tile svg{display:block;max-width:100%;height:auto}
.tile figcaption{margin-top:6px;font-size:.92rem;line-height:1.35}
.tile figcaption .muted{display:block;font-size:.84rem}
.keyfacts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:26px;margin:28px 0 0}
.keyfacts b{display:block;font-size:2.2rem;font-weight:800;line-height:1}
.keyfacts span{color:var(--muted);font-size:.95rem}
"""
FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&display=swap" rel="stylesheet">')

def page(title, body):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'<title>{html.escape(title)}</title>{FONT}<style>{CSS}</style></head>'
            f'<body><div class="wrap">{body}</div></body></html>')


# ---------------------------------------------------------------- bilingual output (en / fr)
# Every view is written twice, once per language, inside <div lang="en"> / <div lang="fr">;
# the site shows one of them. Large shared blocks (the tiles of solutions) are written
# once with bilingual captions via both().
LANGS = ("en", "fr")
NNBSP = "\u202f"   # French thousands separator and space before %

def num(x, l, d=0):
    s = f"{x:,.{d}f}"
    return s if l == "en" else s.replace(",", NNBSP).replace(".", ",")

def pct(x, l, d=0):
    """x is a fraction (0.25 -> 25%)."""
    return num(100 * x, l, d) + ("%" if l == "en" else NNBSP + "%")

def fx(x, l, d=2):
    return "×" + num(x, l, d)

def both(f):
    """Inline text in both languages; f(lang) -> str."""
    a, b = f("en"), f("fr")
    return a if a == b else f'<span lang="en">{a}</span><span lang="fr">{b}</span>'

def bilingual(f):
    """Block in both languages; f(lang) -> html."""
    return f'<div lang="en">{f("en")}</div><div lang="fr">{f("fr")}</div>'

KIND_FR = {"pentomino": "pentamino", "tetromino": "tétramino", "tromino": "triomino",
           "domino": "domino", "monomino": "monomino"}

def plabel(name, l):
    """'L pentomino' in English, 'pentamino L' in French."""
    label = P[name]["label"]
    if l == "en":
        return label
    parts = label.split(" ")
    return KIND_FR[parts[-1]] + (" " + parts[0] if len(parts) == 2 else "")

def plural(n, one, many):
    return one if n == 1 else many
