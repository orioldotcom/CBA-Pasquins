#!/usr/bin/env python3
"""
Llegeix els partits de la setmana directament de les fonts de cbartes.net
(Google Apps Script + API de partits extra) i escriu el JSON que menja
cartell-partits-a4.py. No cal navegador: funciona des del núvol.

  python3 partits_setmana.py [offset_setmanes] > partits.json

offset 0 = setmana en curs (dilluns a diumenge), 1 = la següent.
La lògica de noms d'equip i de lliga és la mateixa que la de la pàgina web.
"""
import json, re, sys, unicodedata, urllib.request
from datetime import date, timedelta

GAS_URL = ("https://script.google.com/macros/s/"
           "AKfycbwb9drm2SQQdZxpmOXvQaXctEkg5QjWb8MUD6IjvA8OY0dabdZXv0M4FbJtKYSHlWin/exec")
EXTRA_URL = "https://cbartes.net/wp-json/cba/v1/partits-extra"

TEAM_NAMES = {
    'SÈNIOR A (M)': 'Sènior Masculí A', 'SÈNIOR B (M)': 'Sènior Masculí B',
    'SÈNIOR (F)': 'Sènior Femení A', 'SÈNIOR B (F)': 'Sènior Femení B',
    'JÚNIOR VERMELL (M)': 'Júnior Masculí Vermell', 'JÚNIOR NEGRE (M)': 'Júnior Masculí Negre',
    'JÚNIOR (F)': 'Júnior Femení', 'CADET 1R ANY (M)': 'Cadet Masculí 1r any',
    'CADET VERMELL (M)': 'Cadet Masculí Vermell', 'CADET NEGRE (M)': 'Cadet Masculí Negre',
    'CADET (F)': 'Cadet Femení', 'CADET 1R ANY (F)': 'Cadet Femení 1r any',
    'INFANTIL 1R ANY (M)': 'Infantil Masculí 1r any', 'INFANTIL (M)': 'Infantil Masculí Vermell',
    'INFANTIL VERMELL (F)': 'Infantil Femení Vermell', 'INFANTIL NEGRE (F)': 'Infantil Femení Negre',
    'MINI (M)': 'Mini Masculí', 'MINI 1R ANY (M)': 'Mini Masculí 1r any',
    'MINI NEGRE (M)': 'Mini Masculí Negre', 'MINI VERMELL (F)': 'Mini Femení Vermell',
    'MINI NEGRE (F)': 'Mini Femení Negre', 'PRE-MINI VERMELL (M)': 'Pre-Mini Masculí Vermell',
    'PRE-MINI NEGRE (M)': 'Pre-Mini Masculí Negre', 'PRE-MINI VERMELL (F)': 'Pre-Mini Femení Vermell',
}
NAMES = {k.upper().strip(): v for k, v in TEAM_NAMES.items()}

CAT_RULES = [(r'ESCOBOL', 'Escobol'), (r'PRE-?\s?MINI', 'Pre-Mini'), (r'MINI', 'Mini'),
             (r'INFANTIL', 'Infantil'), (r'CADET', 'Cadet'), (r'J[UÚ]NIOR', 'Júnior'),
             (r'S[EÈ]NIOR|TERRITORIAL|CATALANA|CATALUNYA|\bFEB\b|\bEBA\b|COPA|LLIGA', 'Sènior')]
COMP_NOMS = [(r'TERCERA\s+FEB', 'Sènior A (M)', 'Tercera FEB')]

DAYS = ['Dilluns', 'Dimarts', 'Dimecres', 'Dijous', 'Divendres', 'Dissabte', 'Diumenge']
MESOS = [('gener', 'de'), ('febrer', 'de'), ('març', 'de'), ('abril', "d'"), ('maig', 'de'),
         ('juny', 'de'), ('juliol', 'de'), ('agost', "d'"), ('setembre', 'de'),
         ('octubre', "d'"), ('novembre', 'de'), ('desembre', 'de')]


def up(s):
    s = str(s).upper()
    return re.sub(r'(^|[\s(])(\d{1,2})(R|N|T|A)(?=[\s.)]|$)',
                  lambda m: m.group(1) + m.group(2) + m.group(3).lower(), s)


def is_artes(n):
    return bool(re.search(r'ART[EÉ]S', str(n or ''), re.I))


def derived_name(g):
    c = str(g[7] or '').upper()
    for rx, nom, _ in COMP_NOMS:
        if re.search(rx, c):
            return nom
    cat = ''
    for rx, val in CAT_RULES:
        if re.search(rx, c):
            cat = val
            break
    if re.search(r'FEMEN|\bFEM\b|\bFEM\.', c):
        gen = 'F'
    elif re.search(r'MASCUL|\bMASC\b|\bMASC\.', c):
        gen = 'M'
    else:
        gen = 'M' if (cat and cat != 'Escobol') else ''
    nm = g[2] if is_artes(g[2]) else g[3]
    suf = re.sub(r'.*ART[EÉ]S', '', str(nm).upper())
    suf = re.sub(r'[^A-ZÀ-Ú0-9 ]', '', suf).strip()
    if len(suf) > 1:
        suf = suf[0] + suf[1:].lower()
    first = '1r any' if re.search(r'1R\.?\s?ANY', c) else ''
    parts = [p for p in [cat or 'CB Artés', first, suf] if p]
    return ' '.join(parts) + (f' ({gen})' if gen else '')


def team_name(g):
    if len(g) > 9 and g[9]:
        return str(g[9])
    d = derived_name(g)
    return NAMES.get(d.upper(), d)


def level_label(g):
    c = str(g[7] or '').upper()
    for rx, _, titol in COMP_NOMS:
        if re.search(rx, c):
            return titol
    pre = 'CC ' if c.startswith('C.C.') else ('CT ' if c.startswith('C.T.') else '')
    c = re.sub(r'^C\.[CT]\.\s*', '', c)
    c = re.sub(r'^BCN\s+U\d+\s*-\s*', '', c)
    c = re.sub(r'PRE-?\s?MINI|MINI|INFANTIL|CADET|J[UÚ]NIOR|S[EÈ]NIOR|ESCOBOL', '', c)
    c = re.sub(r'MASCUL[IÍ]|FEMEN[IÍ]|\bFEM\.?|\bMASC\.?', '', c)
    c = re.sub(r'1R\.?\s?ANY', '', c)
    c = re.sub(r'(\d[AR])\.', r'\1', c)
    c = re.sub(r'\s+', ' ', c).strip()
    return (pre + c).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'cba-cartell/1.0'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def setmana(offset=0):
    avui = date.today()
    dl = avui - timedelta(days=avui.weekday()) + timedelta(weeks=offset)
    dg = dl + timedelta(days=6)

    games = fetch(GAS_URL).get('games', [])
    try:
        games += fetch(EXTRA_URL).get('games', [])
    except Exception as e:
        print('avís: partits extra no disponibles:', e, file=sys.stderr)

    casa = []
    for g in games:
        try:
            d = date.fromisoformat(g[0])
        except Exception:
            continue
        if dl <= d <= dg and is_artes(g[2]):
            casa.append((d, g))
    casa.sort(key=lambda x: (x[0], x[1][1]))

    dies, actual = [], None
    for d, g in casa:
        mes, prep = MESOS[d.month - 1]
        titol = f"{DAYS[d.weekday()]} {d.day} {prep}{'' if prep.endswith(chr(39)) else ' '}{mes}"
        if actual is None or actual['titol'] != titol:
            actual = {'titol': titol, 'partits': []}
            dies.append(actual)
        etiqueta = g[8] if len(g) > 8 and g[8] else level_label(g)
        estat = {2: 'AJORNAT', 3: 'SUSPÈS'}.get(int(g[6] or 0), '')
        lliga = f'({up(etiqueta)})' if etiqueta else ''
        if estat:
            lliga = (lliga + ' · ' if lliga else '') + estat
        actual['partits'].append({
            'hora': str(g[1]).replace(':', '.') + 'h',
            'nostre': up(team_name(g)),
            'rival': up(g[3]),
            'lliga': lliga,
        })

    return {
        'temporada': 'TEMPORADA 2026/2027',
        'peu_esq': 'cbartes.net/partits',
        'peu_dre': '@clubbasquetartes',
        'setmana': f'{dl.isoformat()}/{dg.isoformat()}',
        'dies': dies,
    }


if __name__ == '__main__':
    off = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(json.dumps(setmana(off), ensure_ascii=False, indent=2))
