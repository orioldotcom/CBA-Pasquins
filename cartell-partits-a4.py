#!/usr/bin/env python3
"""
Cartell "Partits a Artés" — A4 300 ppp, amb l'estil de cbartes.net/partits.

  python3 cartell.py partits.json sortida.png sortida.pdf

El JSON té aquesta forma (vegeu exemple-setmana.json):
  {"temporada": "...", "peu_esq": "...", "peu_dre": "...",
   "dies": [{"titol": "Dissabte 3 d'octubre",
             "partits": [{"hora":"09.30h","nostre":"...","rival":"...","lliga":"(CT)"}]}]}

La mida de lletra NO és fixa: es calcula la més gran que hi cap en alçada i
després es tria el tall més ampli de Sofia Sans que encara hi cap en amplada.
Les fonts i l'escut es descarreguen sols el primer cop.
"""
from PIL import Image, ImageDraw, ImageFont
import sys, json, math, os, urllib.request

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets-cartell")

GF = "https://raw.githubusercontent.com/google/fonts/main/ofl"
ASSETS = {
    "sofia.ttf":        f"{GF}/sofiasansextracondensed/SofiaSansExtraCondensed%5Bwght%5D.ttf",
    "sofia-cond.ttf":   f"{GF}/sofiasanscondensed/SofiaSansCondensed%5Bwght%5D.ttf",
    "sofia-semi.ttf":   f"{GF}/sofiasanssemicondensed/SofiaSansSemiCondensed%5Bwght%5D.ttf",
    "leaguegothic.ttf": f"{GF}/leaguegothic/LeagueGothic%5Bwdth%5D.ttf",
    "robotocond.ttf":   f"{GF}/robotocondensed/RobotoCondensed%5Bwght%5D.ttf",
    "crest.png":        "https://cbartes.net/wp-content/uploads/2024/06/Logo-CBA.png",
}

def ensure_assets():
    os.makedirs(BASE, exist_ok=True)
    for name, url in ASSETS.items():
        path = os.path.join(BASE, name)
        if not os.path.exists(path):
            print("descarregant", name)
            urllib.request.urlretrieve(url, path)

W, H = 2480, 3508                 # A4 @300dpi
RED, DARK, THEM = (184, 25, 29), (20, 17, 17), (58, 52, 52)
GREY, LINE, WHITE = (138, 133, 133), (226, 220, 220), (255, 255, 255)
FOOT_PINK, STAR = (248, 217, 217), (138, 20, 23)

LX, RXM = 115, 115                # marges laterals
BAND_Y0, BAND_Y1 = 125, 548
FOOT_Y0 = H - 168

_cache = {}
SOFIA = "sofia.ttf"          # es tria automàticament segons l'amplada disponible
def sofia(size, weight):
    key = ("s", SOFIA, size, weight)
    if key not in _cache:
        f = ImageFont.truetype(f"{BASE}/{SOFIA}", size); f.set_variation_by_axes([weight])
        _cache[key] = f
    return _cache[key]

def league(size):
    key = ("l", size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(f"{BASE}/leaguegothic.ttf", size)
    return _cache[key]

def roboto(size, weight=500):
    key = ("r", size, weight)
    if key not in _cache:
        f = ImageFont.truetype(f"{BASE}/robotocond.ttf", size); f.set_variation_by_axes([weight])
        _cache[key] = f
    return _cache[key]

def tw(d, txt, font, ls=0):
    if ls == 0:
        return d.textlength(txt, font=font)
    return sum(d.textlength(c, font=font) for c in txt) + ls * (len(txt) - 1)

def draw_ls(d, xy, txt, font, fill, ls=0):
    if ls == 0:
        d.text(xy, txt, font=font, fill=fill); return
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=font, fill=fill)
        x += d.textlength(c, font=font) + ls

def star_poly(cx, cy, r):
    p = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        p.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return p

# ---------- mètriques dependents de la mida base F ----------
def metrics(F):
    return dict(
        f_match=int(F), f_info=max(18, int(F * 0.42)), f_day=int(F * 1.65),
        row_info_dy=int(F * 1.00), row_h=int(F * 1.46), row_gap=int(F * 0.30),
        day_h=int(F * 2.45), day_gap=int(F * 0.55), season_h=int(F * 1.85),
        f_season=int(F * 1.30), gap_tcol=int(F * 0.42),
    )

def vfits(data, F, avail_top, avail_bot):
    m = metrics(F)
    n_rows = sum(len(x["partits"]) for x in data["dies"])
    n_days = len(data["dies"])
    total = (m["season_h"] + n_days * m["day_h"] + (n_days - 1) * m["day_gap"]
             + n_rows * (m["row_h"] + m["row_gap"]))
    return (total <= avail_bot - avail_top), total

def fits(d, data, F, avail_top, avail_bot):
    m = metrics(F)
    f_t = sofia(m["f_match"], 800); f_s = sofia(m["f_match"], 500)
    time_w = max(tw(d, p["hora"], f_t) for day in data["dies"] for p in day["partits"])
    team_x = LX + time_w + m["gap_tcol"]
    right = W - RXM
    for day in data["dies"]:
        for p in day["partits"]:
            wln = (tw(d, p["nostre"], f_t) + tw(d, "–", f_s)
                   + tw(d, p["rival"], f_s) + m["f_match"] * 0.7)
            if team_x + wln > right:
                return False, None
    n_rows = sum(len(x["partits"]) for x in data["dies"])
    n_days = len(data["dies"])
    total = (m["season_h"] + n_days * m["day_h"] + (n_days - 1) * m["day_gap"]
             + n_rows * (m["row_h"] + m["row_gap"]))
    return (total <= avail_bot - avail_top), total

def build(data, out_png, out_pdf):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    avail_top, avail_bot = BAND_Y1 + 40, FOOT_Y0 - 40

    global SOFIA
    # 1) mida màxima que hi cap verticalment (no depèn de la família)
    Fv = next(c for c in range(160, 40, -1)
              if vfits(data, c, avail_top, avail_bot)[0])
    # 2) la família més ampla que encara hi cap horitzontalment sense perdre mida
    for fam in ("sofia-semi.ttf", "sofia-cond.ttf", "sofia.ttf"):
        SOFIA = fam
        cand = next((c for c in range(Fv, 40, -1)
                     if fits(d, data, c, avail_top, avail_bot)[0]), 0)
        if cand >= Fv * 0.90:
            F = cand
            break
    used = vfits(data, F, avail_top, avail_bot)[1]
    print("família:", SOFIA, " Fv:", Fv)
    m = metrics(F)
    slack = (avail_bot - avail_top) - used
    n_rows = sum(len(x["partits"]) for x in data["dies"])
    extra = slack / (n_rows + len(data["dies"]) + 1)   # repartim l'espai sobrant
    print(f"F={F}px  ocupat={used}  sobrant={slack:.0f}  extra/fila={extra:.1f}")

    # ---------- marca d'aigua ----------
    crest = Image.open(f"{BASE}/crest.png").convert("RGBA")
    wms = 1250
    wm = crest.resize((wms, wms), Image.LANCZOS)
    wm = Image.merge("RGBA", (*wm.convert("RGB").convert("L").convert("RGB").split(), wm.getchannel("A")))
    wm.putalpha(wm.getchannel("A").point(lambda v: int(v * 0.05)))
    img.paste(wm, (W - wms + 330, H - wms + 40), wm)

    # ---------- banda ----------
    d.rectangle([0, BAND_Y0, W, BAND_Y1], fill=RED)
    f_small, f_big = league(112), league(232)
    cx = 1300
    y1 = BAND_Y0 + 42
    d.text((cx - tw(d, "PARTITS A", f_small) / 2, y1), "PARTITS A", font=f_small, fill=WHITE)
    d.text((cx - tw(d, "ARTÉS", f_big) / 2, y1 + 108), "ARTÉS", font=f_big, fill=WHITE)
    for i in range(3):
        d.polygon(star_poly(2290, BAND_Y0 + 90 + i * 122, 54), fill=STAR)
    cs = 600
    cr = crest.resize((cs, cs), Image.LANCZOS)
    img.paste(cr, (75, BAND_Y0 - 62), cr)

    # ---------- temporada ----------
    y = avail_top
    f_season = league(m["f_season"])
    s = data["temporada"]
    draw_ls(d, (W / 2 - tw(d, s, f_season, 2) / 2, y), s, f_season, RED, 2)
    y += m["season_h"] + extra

    # ---------- partits ----------
    f_t   = sofia(m["f_match"], 800)
    f_s   = sofia(m["f_match"], 500)
    f_day = league(m["f_day"])
    f_i   = roboto(m["f_info"], 500)
    time_w = max(tw(d, p["hora"], f_t) for day in data["dies"] for p in day["partits"])
    TEAM_X = LX + time_w + m["gap_tcol"]

    for dn, day in enumerate(data["dies"]):
        d.text((W / 2 - tw(d, day["titol"], f_day) / 2, y), day["titol"], font=f_day, fill=GREY)
        y += m["day_h"] + extra
        for i, p in enumerate(day["partits"]):
            d.text((LX, y), p["hora"], font=f_t, fill=RED)
            x = TEAM_X
            d.text((x, y), p["nostre"], font=f_t, fill=DARK)
            x += tw(d, p["nostre"], f_t) + m["f_match"] * 0.26
            d.text((x, y), "–", font=f_s, fill=GREY)
            x += tw(d, "–", f_s) + m["f_match"] * 0.26
            d.text((x, y), p["rival"], font=f_s, fill=THEM)
            draw_ls(d, (TEAM_X + 4, y + m["row_info_dy"]), p["lliga"], f_i, GREY, m["f_info"] * 0.07)
            rb = y + m["row_h"]
            if i < len(day["partits"]) - 1:
                d.rectangle([LX, rb, W - RXM, rb + 2], fill=LINE)
            y = rb + m["row_gap"] + extra
        if dn < len(data["dies"]) - 1:
            y += m["day_gap"]

    # ---------- peu ----------
    d.rectangle([0, FOOT_Y0, W, H], fill=RED)
    f_foot = league(78)
    fy = FOOT_Y0 + 34
    d.text((LX + 40, fy), data["peu_esq"], font=f_foot, fill=FOOT_PINK)
    d.text((W - RXM - 40 - tw(d, data["peu_dre"], f_foot), fy), data["peu_dre"], font=f_foot, fill=FOOT_PINK)

    print("final y:", int(y), "/ peu", FOOT_Y0)
    img.save(out_png, dpi=(300, 300))
    # PDF sense pèrdua i lleuger: paleta de 64 colors + PNG dins del PDF (img2pdf).
    # Amb JPEG el text es desfibra i el fitxer pesa el triple.
    try:
        import img2pdf, io
        buf = io.BytesIO()
        img.quantize(colors=64, dither=Image.FLOYDSTEINBERG).save(buf, "PNG", optimize=True)
        with open(out_pdf, "wb") as fh:
            fh.write(img2pdf.convert(buf.getvalue(),
                                     layout_fun=img2pdf.get_fixed_dpi_layout_fun((300, 300))))
    except ImportError:
        img.save(out_pdf, "PDF", resolution=300.0)

if __name__ == "__main__":
    ensure_assets()
    data = json.load(open(sys.argv[1]))
    build(data, sys.argv[2], sys.argv[3])
