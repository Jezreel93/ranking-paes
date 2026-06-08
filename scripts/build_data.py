#!/usr/bin/env python3
"""
Convierte la tabla de ranking PAES (en formato markdown, tal como se extrae de
la página de The Clinic) a un JSON limpio listo para el ranking propio.

Uso:
    python3 build_data.py <anio> <archivo_fuente.md>

Ejemplo:
    python3 build_data.py 2025 ../source/raw-2025.md

Genera:
    ../data/<anio>.json        -> lista de colegios de ese anio
    ../data/manifest.json      -> lista de anios disponibles (auto-actualizado)
"""
import json
import re
import sys
from pathlib import Path


def parse_markdown_table(text: str):
    """Extrae filas de datos de una tabla markdown.

    Una fila de datos valida tiene 6 celdas y la primera es el numero de lugar.
    """
    colegios = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        # separa por pipe y descarta los extremos vacios
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        if not cells[0].isdigit():
            continue  # salta encabezado / separadores

        lugar = int(cells[0])
        nombre = cells[1]
        comuna = cells[2]
        tipo = normaliza_tipo(cells[3])
        estudiantes = to_int(cells[4])
        promedio = to_float(cells[5])

        if estudiantes is None or promedio is None:
            continue

        colegios.append(
            {
                "lugar_original": lugar,
                "nombre": nombre,
                "comuna": comuna,
                "tipo": tipo,
                "estudiantes": estudiantes,
                "promedio": promedio,
            }
        )
    return colegios


def normaliza_tipo(tipo: str) -> str:
    """Corrige typos comunes de la fuente (ej. 'Fianciamiento')."""
    t = tipo.strip()
    t = t.replace("Fianciamiento", "Financiamiento")
    return t


def to_int(value: str):
    value = re.sub(r"[^\d-]", "", value)
    try:
        return int(value)
    except ValueError:
        return None


def to_float(value: str):
    value = value.replace(",", "").strip()
    try:
        return float(value)
    except ValueError:
        return None


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    anio = sys.argv[1]
    fuente = Path(sys.argv[2]).resolve()
    if not fuente.exists():
        print(f"No existe el archivo fuente: {fuente}")
        sys.exit(1)

    data_dir = (Path(__file__).parent / ".." / "data").resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    text = fuente.read_text(encoding="utf-8")
    colegios = parse_markdown_table(text)

    if not colegios:
        print("No se encontraron filas de datos. Revisa el formato de la fuente.")
        sys.exit(1)

    total_alumnos = sum(c["estudiantes"] for c in colegios)
    promedio_nacional_ponderado = round(
        sum(c["promedio"] * c["estudiantes"] for c in colegios) / total_alumnos, 3
    )

    salida = {
        "anio": anio,
        "fuente": "The Clinic - Ranking PAES",
        "meta": {
            "total_colegios": len(colegios),
            "total_alumnos": total_alumnos,
            "promedio_nacional_ponderado": promedio_nacional_ponderado,
        },
        "colegios": colegios,
    }

    out_file = data_dir / f"{anio}.json"
    out_file.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Actualiza el manifest con los anios disponibles
    manifest_file = data_dir / "manifest.json"
    anios = set()
    for f in data_dir.glob("*.json"):
        if f.name == "manifest.json":
            continue
        anios.add(f.stem)
    manifest = {"anios": sorted(anios, reverse=True)}
    manifest_file.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Inyecta TODOS los anios dentro del index.html para que sea autocontenido
    embedded = embed_into_html(data_dir, manifest["anios"])

    print(f"OK -> {out_file}")
    print(f"   colegios: {len(colegios)}")
    print(f"   alumnos totales: {total_alumnos}")
    print(f"   promedio nacional ponderado: {promedio_nacional_ponderado}")
    print(f"   anios en manifest: {manifest['anios']}")
    if embedded:
        print(f"   datos embebidos en: {embedded}")


def embed_into_html(data_dir: Path, anios):
    """Inyecta la data de todos los anios dentro de index.html (autocontenido)."""
    html_file = (data_dir / ".." / "index.html").resolve()
    if not html_file.exists():
        return None

    db = {"manifest": {"anios": anios}, "years": {}}
    for anio in anios:
        db["years"][anio] = json.loads(
            (data_dir / f"{anio}.json").read_text(encoding="utf-8")
        )

    payload = json.dumps(db, ensure_ascii=False, separators=(",", ":"))

    html = html_file.read_text(encoding="utf-8")
    start = "/*__PAES_DATA_START__*/"
    end = "/*__PAES_DATA_END__*/"
    i = html.find(start)
    j = html.find(end)
    if i == -1 or j == -1:
        print("   AVISO: no se encontraron los marcadores en index.html, no se embebio.")
        return None
    new_html = html[: i + len(start)] + payload + html[j:]
    html_file.write_text(new_html, encoding="utf-8")
    return html_file


if __name__ == "__main__":
    main()
