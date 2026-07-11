from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


COMPARISON_REQUIRED_COLUMNS = [
    "comercio",
    "productos_encontrados",
    "productos_faltantes",
    "cobertura_lista_pct",
    "costo_total_estimado",
    "ahorro_vs_mas_caro",
]

BEST_SPLIT_REQUIRED_COLUMNS = [
    "item_lista",
    "grupo_comparacion",
    "comercio_recomendado",
    "producto_encontrado",
    "precio_final",
    "ahorro_vs_promedio",
]

BRANCH_REQUIRED_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "direccion",
    "latitud",
    "longitud",
    "zona",
    "horario_referencia",
]

USER_LOCATION_REQUIRED_COLUMNS = [
    "nombre_ubicacion",
    "latitud",
    "longitud",
    "localidad",
    "descripcion",
]

ROUTE_RECOMMENDATION_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "costo_total_estimado",
    "ahorro_vs_mas_caro",
    "cobertura_lista_pct",
    "distancia_km",
    "penalizacion_distancia",
    "score_conveniencia",
    "recomendacion",
]

SPLIT_ROUTE_COLUMNS = [
    "orden_sugerido",
    "comercio",
    "sucursal",
    "localidad",
    "productos_a_comprar",
    "costo_estimado",
    "distancia_desde_origen_km",
    "distancia_acumulada_km",
    "ahorro_estimado",
]


@dataclass(frozen=True)
class Branch:
    comercio: str
    sucursal: str
    localidad: str
    direccion: str
    latitud: float
    longitud: float
    zona: str
    horario_referencia: str


@dataclass(frozen=True)
class UserLocation:
    nombre_ubicacion: str
    latitud: float
    longitud: float
    localidad: str
    descripcion: str


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{key: str(value or "").strip() for key, value in row.items()} for row in reader]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_columns(rows: list[dict[str, str]], required: list[str], name: str) -> None:
    if not rows:
        raise ValueError(f"El archivo {name} esta vacio.")
    columns = set(rows[0].keys())
    missing = [column for column in required if column not in columns]
    if missing:
        raise ValueError(f"Faltan columnas en {name}: {', '.join(missing)}")


def parse_number(value: Any) -> float | None:
    text = str(value or "").strip().replace("$", "").replace(" ", "")
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return None
    return number


def format_number(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_branches(path: Path) -> list[Branch]:
    rows = read_csv(path)
    validate_columns(rows, BRANCH_REQUIRED_COLUMNS, "sucursales")
    branches: list[Branch] = []
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        lat = parse_number(row.get("latitud"))
        lon = parse_number(row.get("longitud"))
        if lat is None or lon is None:
            errors.append(f"Fila {index}: latitud/longitud invalida.")
            continue
        branches.append(
            Branch(
                comercio=row.get("comercio", ""),
                sucursal=row.get("sucursal", ""),
                localidad=row.get("localidad", ""),
                direccion=row.get("direccion", ""),
                latitud=lat,
                longitud=lon,
                zona=row.get("zona", ""),
                horario_referencia=row.get("horario_referencia", ""),
            )
        )
    if errors:
        raise ValueError("Errores en sucursales: " + " | ".join(errors))
    return branches


def load_user_location(path: Path) -> UserLocation:
    rows = read_csv(path)
    validate_columns(rows, USER_LOCATION_REQUIRED_COLUMNS, "ubicacion_usuario")
    row = rows[0]
    lat = parse_number(row.get("latitud"))
    lon = parse_number(row.get("longitud"))
    if lat is None or lon is None:
        raise ValueError("La ubicacion de usuario tiene latitud/longitud invalida.")
    return UserLocation(
        nombre_ubicacion=row.get("nombre_ubicacion", ""),
        latitud=lat,
        longitud=lon,
        localidad=row.get("localidad", ""),
        descripcion=row.get("descripcion", ""),
    )


def load_user_location_from_args(path: Path, latitud: float | None, longitud: float | None) -> UserLocation:
    if latitud is not None and longitud is not None:
        return UserLocation(
            nombre_ubicacion="Ubicacion manual",
            latitud=latitud,
            longitud=longitud,
            localidad="",
            descripcion="Coordenadas ingresadas por parametro",
        )
    return load_user_location(path)


def branches_for_commerce(branches: list[Branch], commerce: str) -> list[Branch]:
    matches = [branch for branch in branches if branch.comercio == commerce]
    return matches


def nearest_branch(branches: list[Branch], commerce: str, lat: float, lon: float) -> tuple[Branch | None, float]:
    candidates = branches_for_commerce(branches, commerce)
    if not candidates:
        return None, 0.0
    branch = min(candidates, key=lambda item: haversine_km(lat, lon, item.latitud, item.longitud))
    return branch, haversine_km(lat, lon, branch.latitud, branch.longitud)


def build_route_recommendations(
    comparison_rows: list[dict[str, str]],
    branches: list[Branch],
    origin: UserLocation,
    costo_km_estimado: float,
) -> list[dict[str, str]]:
    raw_rows: list[dict[str, Any]] = []
    for row in comparison_rows:
        commerce = row.get("comercio", "")
        cost = parse_number(row.get("costo_total_estimado")) or 0.0
        coverage = parse_number(row.get("cobertura_lista_pct")) or 0.0
        ahorro = parse_number(row.get("ahorro_vs_mas_caro"))
        commerce_branches = branches_for_commerce(branches, commerce)
        if not commerce_branches:
            commerce_branches = [
                Branch(commerce, "Sin sucursal mapeada", "", "", origin.latitud, origin.longitud, "", "")
            ]
        for branch in commerce_branches:
            distance = haversine_km(origin.latitud, origin.longitud, branch.latitud, branch.longitud)
            penalty = distance * costo_km_estimado
            raw_rows.append(
                {
                    "comercio": commerce,
                    "sucursal": branch.sucursal,
                    "localidad": branch.localidad,
                    "costo_total_estimado": cost,
                    "ahorro_vs_mas_caro": ahorro,
                    "cobertura_lista_pct": coverage,
                    "distancia_km": distance,
                    "penalizacion_distancia": penalty,
                    "score_conveniencia": cost + penalty,
                }
            )

    raw_rows.sort(key=lambda item: (-item["cobertura_lista_pct"], item["score_conveniencia"], item["distancia_km"], item["comercio"]))
    best_full_score = next((item["score_conveniencia"] for item in raw_rows if item["cobertura_lista_pct"] >= 99.99), None)
    for index, item in enumerate(raw_rows):
        if best_full_score is not None and item["cobertura_lista_pct"] >= 99.99 and item["score_conveniencia"] == best_full_score:
            item["recomendacion"] = "Recomendado: mejor balance precio/distancia"
        elif item["cobertura_lista_pct"] < 99.99:
            item["recomendacion"] = "Cobertura parcial: revisar faltantes"
        else:
            item["recomendacion"] = "Alternativa completa"

    return [
        {
            "comercio": item["comercio"],
            "sucursal": item["sucursal"],
            "localidad": item["localidad"],
            "costo_total_estimado": format_number(item["costo_total_estimado"]),
            "ahorro_vs_mas_caro": format_number(item["ahorro_vs_mas_caro"]) if item["ahorro_vs_mas_caro"] is not None else "",
            "cobertura_lista_pct": format_number(item["cobertura_lista_pct"]),
            "distancia_km": format_number(item["distancia_km"]),
            "penalizacion_distancia": format_number(item["penalizacion_distancia"]),
            "score_conveniencia": format_number(item["score_conveniencia"]),
            "recomendacion": item["recomendacion"],
        }
        for item in raw_rows
    ]


def group_best_split(best_split_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in best_split_rows:
        commerce = row.get("comercio_recomendado", "").strip()
        if not commerce:
            continue
        grouped.setdefault(commerce, []).append(row)
    return grouped


def build_split_route(
    best_split_rows: list[dict[str, str]],
    branches: list[Branch],
    origin: UserLocation,
) -> list[dict[str, str]]:
    grouped = group_best_split(best_split_rows)
    remaining = set(grouped.keys())
    current_lat = origin.latitud
    current_lon = origin.longitud
    accumulated = 0.0
    rows: list[dict[str, str]] = []
    order = 1

    while remaining:
        options: list[tuple[float, str, Branch | None]] = []
        for commerce in sorted(remaining):
            branch, distance = nearest_branch(branches, commerce, current_lat, current_lon)
            options.append((distance, commerce, branch))
        distance, commerce, branch = min(options, key=lambda item: (item[0], item[1]))
        items = grouped[commerce]
        accumulated += distance
        direct_distance = (
            haversine_km(origin.latitud, origin.longitud, branch.latitud, branch.longitud)
            if branch is not None
            else 0.0
        )
        cost = sum(parse_number(item.get("precio_final")) or 0.0 for item in items)
        saving = sum(parse_number(item.get("ahorro_vs_promedio")) or 0.0 for item in items)
        products = "; ".join(item.get("item_lista", "") for item in items)
        rows.append(
            {
                "orden_sugerido": str(order),
                "comercio": commerce,
                "sucursal": branch.sucursal if branch else "Sin sucursal mapeada",
                "localidad": branch.localidad if branch else "",
                "productos_a_comprar": products,
                "costo_estimado": format_number(cost),
                "distancia_desde_origen_km": format_number(direct_distance),
                "distancia_acumulada_km": format_number(accumulated),
                "ahorro_estimado": format_number(saving),
            }
        )
        if branch is not None:
            current_lat = branch.latitud
            current_lon = branch.longitud
        remaining.remove(commerce)
        order += 1
    return rows


def plan_route(
    comparison_path: Path,
    best_split_path: Path,
    branches_path: Path,
    user_location_path: Path,
    recommendation_output: Path,
    split_route_output: Path,
    report_path: Path | None = None,
    costo_km_estimado: float = 180.0,
    latitud: float | None = None,
    longitud: float | None = None,
) -> dict[str, Any]:
    comparison_rows = read_csv(comparison_path)
    validate_columns(comparison_rows, COMPARISON_REQUIRED_COLUMNS, "comparacion_lista_compra")
    best_split_rows = read_csv(best_split_path)
    validate_columns(best_split_rows, BEST_SPLIT_REQUIRED_COLUMNS, "mejor_compra_por_producto")
    branches = load_branches(branches_path)
    origin = load_user_location_from_args(user_location_path, latitud, longitud)

    recommendations = build_route_recommendations(comparison_rows, branches, origin, costo_km_estimado)
    split_route = build_split_route(best_split_rows, branches, origin)
    write_csv(recommendation_output, recommendations, ROUTE_RECOMMENDATION_COLUMNS)
    write_csv(split_route_output, split_route, SPLIT_ROUTE_COLUMNS)

    best = recommendations[0] if recommendations else None
    report = {
        "comparison": str(comparison_path),
        "best_split": str(best_split_path),
        "branches": str(branches_path),
        "origin": origin.nombre_ubicacion,
        "costo_km_estimado": costo_km_estimado,
        "recommendation_output": str(recommendation_output),
        "split_route_output": str(split_route_output),
        "recommendation_rows": len(recommendations),
        "split_stops": len(split_route),
        "best_recommendation": best or {},
        "distance_note": "Distancia Haversine aproximada en linea recta; no reemplaza navegacion real.",
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Planifica ruta simple por precio efectivo, cobertura y distancia aproximada.")
    parser.add_argument("--comparison", default=str(root / "data" / "processed" / "comparacion_lista_compra.csv"))
    parser.add_argument("--best-split", default=str(root / "data" / "processed" / "mejor_compra_por_producto.csv"))
    parser.add_argument("--branches", default=str(root / "data" / "sample" / "sucursales_demo.csv"))
    parser.add_argument("--user-location", default=str(root / "data" / "sample" / "ubicacion_usuario_demo.csv"))
    parser.add_argument("--recommendation-output", default=str(root / "data" / "processed" / "recomendacion_ruta.csv"))
    parser.add_argument("--split-route-output", default=str(root / "data" / "processed" / "ruta_compra_dividida.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "ruta_reporte.json"))
    parser.add_argument("--costo-km-estimado", type=float, default=180.0)
    parser.add_argument("--latitud", type=float, default=None)
    parser.add_argument("--longitud", type=float, default=None)
    args = parser.parse_args()

    try:
        report = plan_route(
            Path(args.comparison),
            Path(args.best_split),
            Path(args.branches),
            Path(args.user_location),
            Path(args.recommendation_output),
            Path(args.split_route_output),
            Path(args.report),
            args.costo_km_estimado,
            args.latitud,
            args.longitud,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
