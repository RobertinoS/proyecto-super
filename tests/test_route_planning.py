import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "07_planificar_ruta.py"

COMPARISON_COLUMNS = [
    "comercio",
    "productos_encontrados",
    "productos_faltantes",
    "cobertura_lista_pct",
    "costo_total_estimado",
    "diferencia_vs_mas_barato",
    "ahorro_vs_mas_caro",
    "ranking_precio",
]

BEST_COLUMNS = [
    "item_lista",
    "grupo_comparacion",
    "comercio_recomendado",
    "producto_encontrado",
    "precio_final",
    "precio_unitario_comparable",
    "ahorro_vs_promedio",
    "confianza_matching",
]

BRANCH_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "direccion",
    "latitud",
    "longitud",
    "zona",
    "horario_referencia",
]

USER_COLUMNS = ["nombre_ubicacion", "latitud", "longitud", "localidad", "descripcion"]

ROUTE_COLUMNS = [
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


def load_module():
    spec = importlib.util.spec_from_file_location("planificar_ruta", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def comparison_row(comercio, cost, coverage="100.00", savings="500.00"):
    return {
        "comercio": comercio,
        "productos_encontrados": "2",
        "productos_faltantes": "0",
        "cobertura_lista_pct": coverage,
        "costo_total_estimado": str(cost),
        "diferencia_vs_mas_barato": "0.00",
        "ahorro_vs_mas_caro": savings,
        "ranking_precio": "1",
    }


def best_row(item, comercio, price, saving="100"):
    return {
        "item_lista": item,
        "grupo_comparacion": item.lower().replace(" ", "_"),
        "comercio_recomendado": comercio,
        "producto_encontrado": item,
        "precio_final": str(price),
        "precio_unitario_comparable": str(price),
        "ahorro_vs_promedio": saving,
        "confianza_matching": "0.95",
    }


def branch_row(comercio, sucursal, lat, lon, localidad="Capital"):
    return {
        "comercio": comercio,
        "sucursal": sucursal,
        "localidad": localidad,
        "direccion": f"{sucursal} 123",
        "latitud": str(lat),
        "longitud": str(lon),
        "zona": "Demo",
        "horario_referencia": "Lun a sab 09:00-21:00",
    }


def user_row(lat=-31.5375, lon=-68.5364):
    return {
        "nombre_ubicacion": "Casa demo",
        "latitud": str(lat),
        "longitud": str(lon),
        "localidad": "Capital",
        "descripcion": "Demo",
    }


def test_load_branches_user_location_and_haversine(tmp_path):
    module = load_module()
    branches_path = tmp_path / "sucursales.csv"
    user_path = tmp_path / "usuario.csv"
    write_csv(branches_path, [branch_row("Comercio A", "Centro", -31.5375, -68.5364)], BRANCH_COLUMNS)
    write_csv(user_path, [user_row()], USER_COLUMNS)

    branches = module.load_branches(branches_path)
    origin = module.load_user_location(user_path)

    assert branches[0].comercio == "Comercio A"
    assert origin.nombre_ubicacion == "Casa demo"
    assert module.haversine_km(origin.latitud, origin.longitud, branches[0].latitud, branches[0].longitud) == 0
    assert 1.0 < module.haversine_km(-31.5375, -68.5364, -31.5328, -68.5489) < 2.0


def test_route_recommendation_sorts_by_score_conveniencia(tmp_path):
    module = load_module()
    comparison_path = tmp_path / "comparacion.csv"
    best_path = tmp_path / "best.csv"
    branches_path = tmp_path / "sucursales.csv"
    user_path = tmp_path / "usuario.csv"
    recommendation_path = tmp_path / "recomendacion_ruta.csv"
    split_path = tmp_path / "ruta_compra_dividida.csv"

    write_csv(
        comparison_path,
        [
            comparison_row("Cerca", 1050),
            comparison_row("Lejos", 1000),
        ],
        COMPARISON_COLUMNS,
    )
    write_csv(best_path, [best_row("Yerba", "Cerca", 1050), best_row("Leche", "Lejos", 1000)], BEST_COLUMNS)
    write_csv(
        branches_path,
        [
            branch_row("Cerca", "Centro", -31.5375, -68.5364),
            branch_row("Lejos", "Oeste", -31.5279, -68.6051, "Rivadavia"),
        ],
        BRANCH_COLUMNS,
    )
    write_csv(user_path, [user_row()], USER_COLUMNS)

    report = module.plan_route(
        comparison_path,
        best_path,
        branches_path,
        user_path,
        recommendation_path,
        split_path,
        costo_km_estimado=180,
    )

    recommendations = read_csv(recommendation_path)
    split = read_csv(split_path)
    assert report["recommendation_rows"] == 2
    assert recommendations[0]["comercio"] == "Cerca"
    assert float(recommendations[0]["score_conveniencia"]) < float(recommendations[1]["score_conveniencia"])
    assert all(column in recommendations[0] for column in ROUTE_COLUMNS)
    assert all(column in split[0] for column in SPLIT_ROUTE_COLUMNS)
    assert recommendation_path.exists()
    assert split_path.exists()


def test_script_generates_route_outputs_from_sprint_6_flow():
    commands = [
        [sys.executable, "scripts/03_filtrar_san_juan.py", "--input", "data/sample/sepa/sepa_precios_simulado.csv"],
        [sys.executable, "scripts/04_matching_productos.py"],
        [sys.executable, "scripts/06_aplicar_promociones.py", "--date", "2026-07-11"],
        [sys.executable, "scripts/05_calcular_lista_compra.py", "--prices", "data/processed/precios_con_promociones.csv"],
        [sys.executable, "scripts/07_planificar_ruta.py"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr or result.stdout

    recommendation = ROOT / "data" / "processed" / "recomendacion_ruta.csv"
    split_route = ROOT / "data" / "processed" / "ruta_compra_dividida.csv"
    assert recommendation.exists()
    assert split_route.exists()
    recommendation_rows = read_csv(recommendation)
    split_rows = read_csv(split_route)
    assert all(column in recommendation_rows[0] for column in ROUTE_COLUMNS)
    assert all(column in split_rows[0] for column in SPLIT_ROUTE_COLUMNS)
    assert recommendation_rows[0]["recomendacion"] == "Recomendado: mejor balance precio/distancia"
    assert float(recommendation_rows[0]["score_conveniencia"]) >= float(recommendation_rows[0]["costo_total_estimado"])
