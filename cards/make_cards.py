"""
Printable two-player card deck for Katamino Family, with the printed extra
pentominoes (1, 9, 10, 12; 11 is left out because it locks most sets).

Each A6 card is one game. It lies between the two players: the top half faces one
player, the bottom half the other, and the shared pentominoes are in the middle.
Pieces are drawn in the printed set's colours (pentominoes blue, tetrominoes pink,
smaller pieces violet), without labels, and each half of the card has a thick border
in its difficulty colour.
Every starting set on a card never locks, whichever pentominoes from the shared
pool are added. Both players start on the same rectangle size and grow it to 6
rows (3 rounds from 3×5, 2 from 4×5), so both fit the 5×13 board.

Card categories (difficulty bands from analysis/play.py, 1 = very easy, 5 = expert):
  equal       1-1, 2-2, 3-3, 4-4, 5-5
  one apart   1-2, 2-3, 3-4, 4-5      (two players of different ages)
  extremes    1-5

  python cards/make_cards.py                   # cards/cards_en.pdf and cards_fr.pdf
  python cards/make_cards.py --per-size 2      # 2 cards per category and start size

PDF output uses headless Chrome or Edge; without one, print build/cards_<lang>.html
from a browser (A4, no margins, background graphics on).
"""
import argparse, html, math, os, random, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "analysis"))
import play

POOL = play.pools()["extras"]
FULL = play._load("full")
PIECES = {p["name"]: p for p in FULL["pieces"]}

CATEGORIES = [(t, t) for t in range(play.BANDS)] + [(t, t + 1) for t in range(play.BANDS - 1)] + [(0, play.BANDS - 1)]
BAND_COLORS = ["#2e9e5b", "#8bbf3f", "#e8b931", "#e8792c", "#c8372d"]
INK = "#1b1208"
SIZE_COLORS = {5: "#a8d3ec", 4: "#f3a7b0"}   # printed set: pastel blue, pastel pink
SMALL_COLOR = "#7a5fbf"                      # and the board's violet for the rest
piece_color = lambda name: SIZE_COLORS.get(len(PIECES[name]["cells"]), SMALL_COLOR)

TEXT = {
    "en": {
        "title": "Katamino Family",
        "subtitle": "Two-player cards",
        "pool": "Shared pentominoes",
        "rounds": lambda n: f"then {n} rounds",
        "start": "Start",
        "rules_title": "How to play",
        "rules": [
            "Lay the card between you. Each player takes the pieces from their half.",
            "Each player fills the board from their own end. Put a separator just after your rectangle.",
            "Rectangle full? Take any pentomino from the middle of the card, move your separator one row further and fill again.",
            "Stop at 6 rows. At 6 + 6 you meet in the middle: one separator is enough.",
            "First to finish wins. Every pentomino in the middle works: no dead ends.",
        ],
        "legend_title": "Difficulty",
        "legend_note": "The percentage is the chance that putting the big pieces down at random still leaves gaps the small ones can fill. Fewer small pieces means harder. Two players of different ages: use the cards with two different colours.",
    },
    "fr": {
        "title": "Katamino Family",
        "subtitle": "Cartes à deux joueurs",
        "pool": "Pentaminos communs",
        "rounds": lambda n: f"puis {n} manches",
        "start": "Départ",
        "rules_title": "Comment jouer",
        "rules": [
            "Posez la carte entre vous. Chaque joueur prend les pièces de sa moitié.",
            "Chacun remplit le plateau depuis son bout. Placez un séparateur juste après votre rectangle.",
            "Rectangle rempli ? Prenez un pentamino au milieu de la carte, reculez votre séparateur d’une rangée et remplissez à nouveau.",
            "On s’arrête à 6 rangées. À 6 + 6 on se rejoint au milieu : un seul séparateur suffit.",
            "Le premier qui finit a gagné. Tous les pentaminos du milieu marchent : jamais d’impasse.",
        ],
        "legend_title": "Difficulté",
        "legend_note": "Le pourcentage est la chance qu’en posant les grandes pièces au hasard, les petites puissent encore combler les trous. Moins de petites pièces, plus c’est dur. Deux joueurs d’âges différents : prenez les cartes à deux couleurs.",
    },
}

# ---------------------------------------------------------------- choosing pairs
def choose_pairs(per_size, seed):
    """per_size cards for each category and start size. Each set is used at most once
    when possible; equal-band cards pair sets with the closest solution counts."""
    rng = random.Random(seed)
    used, cards = set(), []
    for low, high in CATEGORIES:
        for h in (3, 4):
            band = lambda t: [s for s in POOL["sets"] if s["h"] == h and s["band"] == t]
            firsts, seconds = band(low), band(high)
            rng.shuffle(firsts)
            chosen = []
            for allow_reuse in (False, True):
                for a in firsts:
                    if len(chosen) == per_size:
                        break
                    if not allow_reuse and a["k"] in used:
                        continue
                    options = [b for b in seconds if play.playable_pair(a, b, POOL)
                               and (allow_reuse or b["k"] not in used) and {a["k"], b["k"]} not in chosen]
                    if not options:
                        continue
                    if low == high:
                        best = min(abs(math.log(a["u"] / b["u"])) for b in options)
                        options = [b for b in options if abs(math.log(a["u"] / b["u"])) == best]
                    b = rng.choice(options)
                    used |= {a["k"], b["k"]}
                    chosen.append({a["k"], b["k"]})
                    cards.append({"a": a, "b": b, "h": h, "pool": play.shared_pool(a, b, POOL["pentominoes"])})
    for i, card in enumerate(cards, 1):
        card["number"] = i
    return cards

# ---------------------------------------------------------------- drawing (mm units)
def oriented(cells):
    """Lay the piece wide rather than tall."""
    rows = max(r for r, _ in cells) - min(r for r, _ in cells)
    cols = max(c for _, c in cells) - min(c for _, c in cells)
    if rows > cols:
        cells = [(c, -r) for r, c in cells]
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return [(r - r0, c - c0) for r, c in cells]

def piece_svg(name, cell):
    p = PIECES[name]
    cells = oriented([tuple(x) for x in p["cells"]])
    rows, cols = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
    s = set(cells)
    w, h = cols * cell, rows * cell
    sw = cell * 0.08
    out = [f'<svg width="{w + sw:.2f}mm" height="{h + sw:.2f}mm" viewBox="{-sw/2:.3f} {-sw/2:.3f} {w + sw:.3f} {h + sw:.3f}">']
    for r, c in cells:
        out.append(f'<rect x="{c*cell}" y="{r*cell}" width="{cell}" height="{cell}" fill="{piece_color(name)}" '
                   f'stroke="#ffffff" stroke-opacity=".45" stroke-width="{sw*0.6:.3f}"/>')
    edges = []
    for r, c in cells:
        x, y = c * cell, r * cell
        if (r - 1, c) not in s: edges.append(f"M{x} {y}h{cell}")
        if (r + 1, c) not in s: edges.append(f"M{x} {y+cell}h{cell}")
        if (r, c - 1) not in s: edges.append(f"M{x} {y}v{cell}")
        if (r, c + 1) not in s: edges.append(f"M{x+cell} {y}v{cell}")
    out.append(f'<path d="{"".join(edges)}" stroke="{INK}" stroke-width="{sw:.3f}" fill="none" stroke-linecap="square"/>')
    out.append("</svg>")
    return "".join(out)

def dots(band, size=3.2):
    gap = size * 0.45
    w = 5 * size + 4 * gap
    out = [f'<svg width="{w:.2f}mm" height="{size:.2f}mm" viewBox="0 0 {w} {size}">']
    for i in range(play.BANDS):
        x = i * (size + gap) + size / 2
        filled = i <= band
        out.append(f'<circle cx="{x}" cy="{size/2}" r="{size/2 - 0.2}" fill="{BAND_COLORS[band] if filled else "none"}" '
                   f'stroke="{BAND_COLORS[band]}" stroke-width="0.35"/>')
    out.append("</svg>")
    return "".join(out)

# ---------------------------------------------------------------- pages
def half_html(s, h, lang, flipped):
    t = TEXT[lang]
    pieces = sorted(s["k"], key=lambda c: (-len(PIECES[c]["cells"]), s["k"].index(c)))
    cell = 7.6 if len(pieces) <= 5 else 7.0
    return f'''<div class="half{' flipped' if flipped else ''}">
  <div class="head">{dots(s["band"])}<span class="band">{html.escape(play.BAND_NAMES[lang][s["band"]])}</span>
    <span class="size">{t["start"]} {h}×5 · {t["rounds"](play.rounds(h))}</span></div>
  <div class="body"><div class="pieces">{"".join(f'<div class="pc">{piece_svg(c, cell)}</div>' for c in pieces)}</div></div>
</div>'''

def card_html(card, lang):
    t = TEXT[lang]
    pool = "".join(f'<div class="pc">{piece_svg(c, 2.9)}</div>' for c in card["pool"])
    frame = lambda where, band: f'<div class="frame {where}" style="border-color:{BAND_COLORS[band]}"></div>'
    return f'''<div class="card">{frame("top", card["b"]["band"])}{frame("bottom", card["a"]["band"])}
  {half_html(card["b"], card["h"], lang, True)}
  <div class="mid"><div class="num">{card["number"]}</div>
    <div class="pool"><div class="pl">{t["pool"]}</div><div class="pps">{pool}</div></div></div>
  {half_html(card["a"], card["h"], lang, False)}
</div>'''

def rules_card(lang):
    t = TEXT[lang]
    steps = "".join(f"<li>{html.escape(x)}</li>" for x in t["rules"])
    sample = "".join(f'<div class="pc">{piece_svg(c, 3.2)}</div>' for c in POOL["pentominoes"])
    return f'''<div class="card text"><h1>{t["title"]}</h1><h2>{t["subtitle"]}</h2>
  <h3>{t["rules_title"]}</h3><ol>{steps}</ol><div class="pps wide">{sample}</div></div>'''

def legend_card(lang, cards):
    t = TEXT[lang]
    rows = []
    for band in range(play.BANDS):
        rng3 = [s["f"] for s in POOL["sets"] if s["h"] == 3 and s["band"] == band]
        rng4 = [s["f"] for s in POOL["sets"] if s["h"] == 4 and s["band"] == band]
        pct = lambda f: f"{f * 100:.1f}".rstrip("0").rstrip(".") if f < 0.1 else f"{f * 100:.0f}"
        span = lambda fs: f"{pct(min(fs))}–{pct(max(fs))} %"
        rows.append(f'<tr><td>{dots(band)}</td><td><b>{html.escape(play.BAND_NAMES[lang][band])}</b></td>'
                    f'<td>3×5: {span(rng3)}</td><td>4×5: {span(rng4)}</td></tr>')
    index = []
    for low, high in CATEGORIES:
        nums = [c["number"] for c in cards if (c["a"]["band"], c["b"]["band"]) == (low, high)]
        if nums:
            index.append(f'<tr><td>{dots(low, 2.4)}</td><td>{dots(high, 2.4)}</td><td>{nums[0]}–{nums[-1]}</td></tr>')
    return f'''<div class="card text"><h3>{t["legend_title"]}</h3>
  <table class="legend">{"".join(rows)}</table><p class="note">{html.escape(t["legend_note"])}</p>
  <table class="index">{"".join(index)}</table></div>'''

CSS = f"""
@page {{ size: A4; margin: 0 }}
* {{ box-sizing: border-box }}
body {{ margin: 0; font-family: "Segoe UI", system-ui, sans-serif; color: {INK}; -webkit-print-color-adjust: exact; print-color-adjust: exact }}
.page {{ width: 210mm; height: 297mm; page-break-after: always; position: relative; overflow: hidden }}
.sheet {{ display: grid; grid-template-columns: 105mm 105mm; grid-template-rows: 148.5mm 148.5mm }}
.sheet::before, .sheet::after {{ content: ""; position: absolute; background: none; border: 0 dashed #c8c0b4 }}
.sheet::before {{ left: 105mm; top: 0; height: 297mm; border-left-width: 0.2mm }}
.sheet::after {{ top: 148.5mm; left: 0; width: 210mm; border-top-width: 0.2mm }}
.card {{ width: 105mm; height: 148.5mm; padding: 9mm; display: flex; flex-direction: column; position: relative }}
.frame {{ position: absolute; left: 0; right: 0; border: 4mm solid }}
.frame.top {{ top: 0; height: 50%; border-bottom: 0 }}
.frame.bottom {{ bottom: 0; height: 50%; border-top: 0 }}
.half {{ flex: 1; display: flex; flex-direction: column; gap: 2mm }}
.half.flipped {{ transform: rotate(180deg) }}
.head {{ display: flex; align-items: center; gap: 2mm; font-size: 3.2mm }}
.band {{ font-weight: 700 }}
.size {{ margin-left: auto; color: #6b5e4e }}
.body {{ flex: 1; display: flex; gap: 4mm; align-items: center }}
.pieces {{ flex: 1; display: flex; flex-wrap: wrap; gap: 3mm 3.5mm; align-items: center; justify-content: center }}
.pc svg {{ display: block }}
.mid {{ flex: none; height: 25mm; margin: 2mm -5mm; padding: 0 5mm; background: #f4eee4; border-top: 0.3mm solid #e2d8c8; border-bottom: 0.3mm solid #e2d8c8;
        display: flex; align-items: center; gap: 4mm }}
.num {{ font-size: 7mm; font-weight: 800; min-width: 10mm; text-align: center; color: #8a7a64 }}
.pool {{ flex: 1 }}
.pl {{ font-size: 2.8mm; color: #6b5e4e; margin-bottom: 1.2mm }}
.pps {{ display: flex; flex-wrap: wrap; gap: 1.6mm 2.2mm; align-items: center }}
.pps.wide {{ justify-content: center; margin-top: auto; gap: 2mm 3mm }}
.text {{ font-size: 3.3mm; line-height: 1.35 }}
.text h1 {{ font-size: 8mm; margin: 2mm 0 0 }}
.text h2 {{ font-size: 4.2mm; margin: 0 0 4mm; font-weight: 500; color: #6b5e4e }}
.text h3 {{ font-size: 4.6mm; margin: 0 0 2mm }}
.text ol {{ padding-left: 5mm; margin: 0 0 4mm }}
.text li {{ margin-bottom: 1.6mm }}
.legend, .index {{ border-collapse: collapse; margin-bottom: 3mm }}
.legend td, .index td {{ padding: 1mm 2mm 1mm 0; vertical-align: middle; font-size: 3.1mm }}
.note {{ color: #6b5e4e; font-size: 2.9mm }}
"""

def build(lang, cards):
    front = [rules_card(lang), legend_card(lang, cards)]
    all_cards = front + [card_html(c, lang) for c in cards]
    sheets = [f'<section class="page sheet">{"".join(all_cards[i:i+4])}</section>' for i in range(0, len(all_cards), 4)]
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{TEXT[lang]["title"]} · {TEXT[lang]["subtitle"]}</title>'
            f'<style>{CSS}</style></head><body>{"".join(sheets)}</body></html>')

def find_browser():
    for path in [os.environ.get("CHROME", ""),
                 r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                 "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if path and os.path.exists(path):
            return path
    return next((shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge") if shutil.which(n)), None)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-size", type=int, default=3, help="cards per category for each start size (3×5 and 4×5)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--lang", choices=["en", "fr", "both"], default="both")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    cards = choose_pairs(a.per_size, a.seed)
    browser = find_browser()
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    for lang in (["en", "fr"] if a.lang == "both" else [a.lang]):
        page = os.path.join(ROOT, "build", f"cards_{lang}.html")
        open(page, "w", encoding="utf-8").write(build(lang, cards))
        if not browser:
            print(f"wrote {os.path.relpath(page, ROOT)} (no Chrome/Edge found: print it to PDF from a browser)")
            continue
        pdf = os.path.join(a.out, f"cards_{lang}.pdf")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", "file:///" + page.replace(os.sep, "/")],
                       check=True, capture_output=True)
        print(f"wrote {os.path.relpath(pdf, ROOT)}")
    print(f"{len(cards)} game cards + rules and difficulty cards")

if __name__ == "__main__":
    main()
