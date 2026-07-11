from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


OUTPUTS = [
    "data/processed/precios_normalizados.csv",
    "data/raw/sepa/manual/sepa_precios_simulado.csv",
    "data/processed/precios_san_juan_sepa.csv",
    "data/processed/precios_matcheados.csv",
    "data/processed/precios_con_promociones.csv",
    "data/processed/comparacion_lista_compra.csv",
    "data/processed/mejor_compra_por_producto.csv",
    "data/processed/recomendacion_ruta.csv",
    "data/processed/ruta_compra_dividida.csv",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(root: Path, label: str, command: list[str]) -> None:
    print(f"\n== {label} ==", flush=True)
    print(" ".join(command), flush=True)
    result = subprocess.run(command, cwd=root, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Fallo el paso '{label}' con codigo {result.returncode}.")


def validate_outputs(root: Path) -> list[dict[str, str | int | bool]]:
    report = []
    for relative in OUTPUTS:
        path = root / relative
        report.append(
            {
                "path": relative,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    missing = [item["path"] for item in report if not item["exists"]]
    if missing:
        raise FileNotFoundError("Faltan outputs del MVP demo: " + ", ".join(missing))
    return report


def build_demo(date: str, costo_km_estimado: float) -> dict:
    root = project_root()
    python = sys.executable
    steps = [
        (
            "Normalizar CSV demo local",
            [python, "scripts/02_normalizar_precios.py"],
        ),
        (
            "Importar SEPA sample en modo manual",
            [
                python,
                "scripts/01_descargar_o_importar_sepa.py",
                "--mode",
                "manual",
                "--input",
                "data/sample/sepa/sepa_precios_simulado.csv",
            ],
        ),
        (
            "Filtrar precios San Juan",
            [
                python,
                "scripts/03_filtrar_san_juan.py",
                "--input",
                "data/raw/sepa/manual/sepa_precios_simulado.csv",
            ],
        ),
        (
            "Matchear productos",
            [python, "scripts/04_matching_productos.py"],
        ),
        (
            "Aplicar promociones demo",
            [python, "scripts/06_aplicar_promociones.py", "--date", date],
        ),
        (
            "Calcular lista con precio efectivo",
            [
                python,
                "scripts/05_calcular_lista_compra.py",
                "--prices",
                "data/processed/precios_con_promociones.csv",
            ],
        ),
        (
            "Planificar ruta demo",
            [
                python,
                "scripts/07_planificar_ruta.py",
                "--costo-km-estimado",
                str(costo_km_estimado),
            ],
        ),
    ]

    for label, command in steps:
        run_step(root, label, command)

    outputs = validate_outputs(root)
    return {
        "ok": True,
        "release": "MVP v1.0 demo",
        "date": date,
        "costo_km_estimado": costo_km_estimado,
        "outputs": outputs,
        "dashboard": "dashboard/index.html",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera todos los outputs demo del MVP v1.0.")
    parser.add_argument(
        "--date",
        default="2026-07-11",
        help="Fecha de calculo para promociones demo. Por defecto usa 2026-07-11 para reproducibilidad.",
    )
    parser.add_argument("--costo-km-estimado", type=float, default=180.0)
    args = parser.parse_args()

    try:
        report = build_demo(args.date, args.costo_km_estimado)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("\n== Resumen MVP demo ==", flush=True)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    print("\nAbrir el dashboard con: python -m http.server 8026 --bind 127.0.0.1", flush=True)
    print("Luego entrar a: http://127.0.0.1:8026/dashboard/", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
