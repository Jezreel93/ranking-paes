# Ranking PAES Justo

Ranking propio de colegios según la PAES que **ajusta el promedio por la cantidad de estudiantes** que rindieron, para que no sea lo mismo que 30 alumnos saquen 900 a que 3.000 sostengan 800.

## ¿Por qué un ranking distinto?

El ranking tradicional (The Clinic) ordena por **promedio simple**. Eso premia a colegios chicos: con pocos alumnos es fácil tener un promedio alto (más varianza y más capacidad de seleccionar a quién rinde).

Acá usamos un **estimador bayesiano de encogimiento** (_shrinkage_), el mismo principio detrás del ranking de IMDb:

```
score_ajustado = (n / (n + m)) · promedio_colegio + (m / (n + m)) · promedio_nacional
```

- `n` = estudiantes que rindieron en el colegio
- `promedio_nacional` = media nacional **ponderada por alumnos**
- `m` = peso de credibilidad (cuántos alumnos hacen falta para "creerle" al promedio)

Colegios con pocos alumnos son jalados hacia el promedio nacional; los grandes con buen puntaje se mantienen arriba. En el HTML, `m` es un **slider en vivo**: con `m = 0` recuperás el ranking tradicional.

## Costo-beneficio (arancel)

Además del puntaje ajustado, el ranking incluye una columna de **arancel mensual** y una de **costo-beneficio**:

- Colegios de **financiamiento público = gratis** → mejor costo-beneficio por definición (★).
- Colegios **pagados**: `costo-beneficio = puntaje ajustado por cada $100.000/mes`. Más alto = más puntos por tu plata.

En Chile **no hay listado oficial de aranceles** de colegios particulares pagados, así que se investigaron a mano los ~50 mejor rankeados desde sitios oficiales y prensa. Los datos viven en `data/aranceles.json` (clave `NOMBRE||COMUNA`), con fuente y nivel de confianza por colegio. Los que no publican precio quedan como `s/i`. Para agregar/corregir un arancel, editá ese archivo y volvé a correr el parser. Montos referenciales (varían por nivel), UF ≈ $39.000.

## Cómo usarlo

`index.html` es **autocontenido**: los datos viven embebidos dentro del propio archivo. Solo abrilo con doble clic en cualquier navegador (no necesita servidor) y podés pasárselo a quien quieras como un único archivo.

## Estructura

```
paes-ranking/
├── index.html            # La app del ranking, autocontenida (doble clic)
├── data/
│   ├── manifest.json      # Lista de años disponibles (auto-generado)
│   └── 2025.json          # Datos limpios de un año (fuente de la verdad)
├── source/
│   └── raw-2025.md        # Tabla cruda extraída de la fuente
└── scripts/
    └── build_data.py      # Convierte source/*.md -> data/*.json
```

## Agregar un nuevo año (año tras año)

1. Guardá la tabla cruda del nuevo año en `source/raw-<año>.md` (mismo formato de tabla markdown: `| lugar | nombre | comuna | tipo | alumnos | promedio |`).
2. Corré el parser:

```bash
cd scripts
python3 build_data.py 2026 ../source/raw-2026.md
```

Esto genera `data/2026.json`, actualiza `data/manifest.json` y **re-inyecta todos los años dentro de `index.html`** (entre los marcadores `/*__PAES_DATA_START__*/` y `/*__PAES_DATA_END__*/`). El selector de año en el HTML lo detecta automáticamente. El `index.html` sigue siendo un único archivo autocontenido y compartible.

## Formato del JSON

```json
{
  "anio": "2025",
  "fuente": "The Clinic - Ranking PAES",
  "meta": {
    "total_colegios": 3287,
    "total_alumnos": 179604,
    "promedio_nacional_ponderado": 611.467
  },
  "colegios": [
    {
      "lugar_original": 1,
      "nombre": "COLEGIO CAMBRIDGE COLLEGE",
      "comuna": "PROVIDENCIA",
      "tipo": "Particular pagado",
      "estudiantes": 30,
      "promedio": 893.417
    }
  ]
}
```
