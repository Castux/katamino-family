"""
Playable starting sets and difficulty bands, shared by the website (Play page) and
the printed card deck.

A playable set never locks: whichever pentominoes from its pool are added, in any
order, the rectangle stays solvable. Difficulty is the set's forgiveness
(data/forgiveness.json): the chance that placing the big pieces at random leaves
gaps the small pieces (1 to 3 squares) can fill. Small pieces patch gaps, so a set
with few solutions but several small pieces is still easy. Ties are broken by the
solution count. Sets are split per rectangle size into BANDS bands of about equal
size (sets with the same score always share a band); band 0 is the most forgiving.

Two players on the 5×13 board each grow their rectangle to FINAL_ROWS rows: a
3×5 start adds 3 pentominoes, a 4×5 start adds 2. Until both reach 6 rows each
player closes their rectangle with their own separator (a + b + 2 <= 13); at
6 + 6 a single separator in the middle row serves both.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANDS = 5
FINAL_ROWS = 6
BAND_NAMES = {"en": ["Very easy", "Easy", "Medium", "Hard", "Expert"],
              "fr": ["Très facile", "Facile", "Moyen", "Difficile", "Expert"]}
EXTRAS = {"1", "9", "F", "M"}               # 11 (X) is left out on purpose

def _load(name):
    return json.load(open(os.path.join(ROOT, "data", f"results_{name}.json"), encoding="utf-8"))

def _safe_without(fails, banned):
    return not any(not any(c in banned for c in q) for f in fails for q in f)

def assign_bands(sets):
    """Add 'band' to each set dict, per rectangle height: most forgiving first, then
    most solutions."""
    for h in {s["h"] for s in sets}:
        hs = sorted((s for s in sets if s["h"] == h), key=lambda s: (-s["f"], -s["u"], s["k"]))
        first = {}
        for i, s in enumerate(hs):
            first.setdefault((s["f"], s["u"]), i)
            s["band"] = min(BANDS - 1, BANDS * first[s["f"], s["u"]] // len(hs))
    return sets

def pools():
    """{'box': ..., 'extras': ...}, each with sets (k, h, u, g, band), pentominoes
    and inventory (copies of each piece)."""
    box, full = _load("box"), _load("full")
    forgiveness = json.load(open(os.path.join(ROOT, "data", "forgiveness.json"), encoding="utf-8"))
    size_box = {p["name"]: len(p["cells"]) for p in box["pieces"]}
    size_full = {p["name"]: len(p["cells"]) for p in full["pieces"]}
    as_set = lambda data, size, k: {"k": k, "h": sum(size[c] for c in k) // 5,
                                    "u": data["sets"][k][1], "g": data["sets"][k][2], "f": forgiveness[k]}
    box_sets = [as_set(box, size_box, k) for k, _, fails in box["starts"] if not any(fails)]
    ext_sets = [as_set(full, size_full, k) for k, _, fails in full["starts"]
                if "K" not in k and _safe_without(fails, {"K"})]
    inv_box = {p["name"]: p["copies"] for p in box["pieces"]}
    order_full = [p["name"] for p in full["pieces"]]
    return {
        "box": {"sets": assign_bands(box_sets), "inventory": inv_box,
                "pentominoes": [p["name"] for p in box["pieces"] if len(p["cells"]) == 5]},
        "extras": {"sets": assign_bands(ext_sets), "inventory": dict(inv_box, **{e: 1 for e in EXTRAS}),
                   "pentominoes": [n for n in order_full if size_full[n] == 5 and n != "K"]},
    }

def fits(a, b, inventory):
    """Can sets a and b be laid out at the same time with this many copies of each piece?"""
    return all((a + b).count(c) <= inventory.get(c, 0) for c in set(a + b))

def rounds(h):
    return FINAL_ROWS - h

def shared_pool(a, b, pentominoes):
    return [p for p in pentominoes if p not in a["k"] and p not in b["k"]]

def playable_pair(a, b, pool):
    """Both sets fit together and the pool leaves enough pentominoes for every round."""
    return (a["k"] != b["k"] and fits(a["k"], b["k"], pool["inventory"])
            and len(shared_pool(a, b, pool["pentominoes"])) >= rounds(a["h"]) + rounds(b["h"]))
