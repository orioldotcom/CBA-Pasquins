#!/usr/bin/env python3
"""
Genera el pasquí de la setmana i el publica en aquest repositori.

  python3 publica.py [offset_setmanes]

offset 0 = setmana en curs (per defecte), 1 = la següent.

Surt amb codi 2 i sense publicar res si aquella setmana no es juga a Artés.
En acabar imprimeix les URL públiques, que són el que va al correu.
"""
import json, os, sys, subprocess, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = "https://raw.githubusercontent.com/orioldotcom/CBA-Pasquins/main/pasquins/"


def load(nom, fitxer):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(HERE, fitxer))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(*args):
    return subprocess.run(["git", "-C", HERE, *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def hora_min(h):
    """'19.00h' -> minuts, per inserir en ordre cronologic."""
    t = str(h).replace("h", "").replace(":", ".").strip()
    try:
        hh, _, mm = t.partition(".")
        return int(hh) * 60 + int(mm or 0)
    except ValueError:
        return 0


def aplica_excepcions(data):
    """Afegeix les files destacades d'excepcions.json, si n'hi ha per a aquesta setmana."""
    fitxer = os.path.join(HERE, "excepcions.json")
    if not os.path.exists(fitxer):
        return
    with open(fitxer, encoding="utf-8") as fh:
        totes = json.load(fh)
    clau = data["setmana"].split("/")[0]
    for exc in totes.get(clau, []):
        dia = next((x for x in data["dies"] if x.get("data") == exc.get("data")), None)
        if dia is None:
            print("AVIS excepcio sense dia:", exc.get("data"))
            continue
        pos = len(dia["partits"])
        for i, p in enumerate(dia["partits"]):
            if hora_min(p["hora"]) > hora_min(exc["hora"]):
                pos = i
                break
        dia["partits"].insert(pos, {k: v for k, v in exc.items() if k != "data"})
        print("EXCEPCIO", exc.get("titol"), "->", dia["titol"])


def main():
    off = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    dades = load("partits_setmana", "partits_setmana.py")
    cartell = load("cartell", "cartell-partits-a4.py")

    data = dades.setmana(off)
    aplica_excepcions(data)
    n = sum(len(d["partits"]) for d in data["dies"])
    if n == 0:
        print("CAP_PARTIT", data["setmana"])
        return 2

    dilluns = data["setmana"].split("/")[0]
    carpeta = os.path.join(HERE, "pasquins")
    os.makedirs(carpeta, exist_ok=True)
    base = f"cartell-partits-{dilluns}"
    png, pdf = os.path.join(carpeta, base + ".png"), os.path.join(carpeta, base + ".pdf")

    cartell.ensure_assets()
    cartell.build(data, png, pdf)

    git("add", "pasquins")
    if git("status", "--porcelain", "pasquins"):
        git("commit", "-m", f"Pasqui dels partits a Artes de la setmana del {dilluns}")
        git("push", "origin", "main")

    print()
    print("SETMANA", data["setmana"])
    print("PARTITS", n)
    for d in data["dies"]:
        print("DIA", d["titol"], "-", len(d["partits"]), "partits")
    print("URL_PDF", RAW + base + ".pdf")
    print("URL_PNG", RAW + base + ".png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
