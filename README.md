# CBA-Pasquins

Pasquins setmanals dels partits que el CB Artés juga a casa, generats automàticament
cada dilluns a les 10:00 i enviats per correu amb l'enllaç a aquest repositori.

Els fitxers són a `pasquins/`, un PNG i un PDF per setmana, anomenats amb el dilluns
de la setmana corresponent.

## Com funciona

| Fitxer | Què fa |
|---|---|
| `partits_setmana.py` | Llegeix els partits a Artés de la setmana del Google Apps Script del club i de l'API de partits extra del WordPress. Reprodueix la mateixa lògica de noms d'equip i de lliga que cbartes.net/partits |
| `cartell-partits-a4.py` | Dibuixa el pasquí A4 a 300 ppp (PNG + PDF). Es descarrega sol les tipografies i l'escut |
| `publica.py` | Ho encadena tot, fa el commit i el push, i imprimeix les URL públiques |

Manualment:

```
python3 publica.py      # setmana en curs
python3 publica.py 1    # la setmana vinent
```

Si aquella setmana no es juga a Artés, surt amb codi 2 i no publica res.

## El disseny

Replica el cartell de cbartes.net/partits: banda vermella amb l'escut, capçalera per
dia, hora en vermell, equip del club en negreta, rival en gris i la lliga a sota.

La mida de lletra no és fixa: es calcula la més gran que hi cap en alçada i després
es tria el tall més ample de Sofia Sans (Semi Condensed, Condensed o Extra Condensed)
que encara hi càpiga d'ample. Així el pasquí sempre omple la pàgina, tant si hi ha
sis partits com catorze.
