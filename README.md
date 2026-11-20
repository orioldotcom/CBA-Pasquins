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
| `excepcions.json` | Files destacades puntuals (presentacions, actes del club) per a una setmana concreta |

## Excepcions puntuals

Per destacar un acte del club dins el pasquí d'una setmana, s'afegeix una entrada a
`excepcions.json` amb el dilluns d'aquella setmana com a clau:

```json
{
  "2026-11-23": [
    {"data": "2026-11-28", "tipus": "event", "hora": "19.00h",
     "titol": "PRESENTACIÓ D'EQUIPS", "subtitol": "TEMPORADA 2026-2027"}
  ]
}
```

Surt com una franja vermella plena, amb el títol en blanc i el subtítol a continuació,
i s'insereix al dia indicat en ordre cronològic segons l'hora: si la federació canvia
l'horari d'un partit, l'acte continua caient al lloc que li toca. Les setmanes que no
surten al fitxer es generen amb el format normal, o sigui que una excepció caduca sola.

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
