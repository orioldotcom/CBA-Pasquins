#!/usr/bin/env python3
"""
Tot en un: llegeix els partits a Artés de la setmana i genera el cartell A4.

  python3 cartell_setmanal.py [offset_setmanes]

offset 0 = setmana en curs (per defecte), 1 = la següent.
Escriu cartell-partits-<dilluns>.png i .pdf al directori actual i imprimeix
un resum + les rutes.
"""
import sys, json, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))

def load(name, fitxer):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fitxer))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

dades = load("partits_setmana", "partits_setmana.py")
cartell = load("cartell", "cartell-partits-a4.py")

off = int(sys.argv[1]) if len(sys.argv) > 1 else 0
data = dades.setmana(off)

n = sum(len(d["partits"]) for d in data["dies"])
if n == 0:
    print("CAP PARTIT a Artés aquesta setmana:", data["setmana"])
    sys.exit(2)

dilluns = data["setmana"].split("/")[0]
png = os.path.join(HERE, f"cartell-partits-{dilluns}.png")
pdf = os.path.join(HERE, f"cartell-partits-{dilluns}.pdf")

cartell.ensure_assets()
cartell.build(data, png, pdf)

print(f"\nSetmana {data['setmana']} — {n} partits a Artés")
for d in data["dies"]:
    print(" ", d["titol"] + ":", len(d["partits"]))
print("PNG:", png)
print("PDF:", pdf, f"({os.path.getsize(pdf)/1024:.0f} KB)")
