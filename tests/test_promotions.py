import csv
import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMO_SCRIPT = ROOT / "scripts" / "06_aplicar_promociones.py"
SHOPPING_SCRIPT = ROOT / "scripts" / "05_calcular_lista_compra.py"

PRICE_COLUMNS = [
    "comercio",
    "sucursal",
    "localidad",
    "producto",
    "marca",
    "categoria",
    "presentacion",
    "precio",
    "fecha_relevamiento",
    "fuente",
    "cantidad_base",
    "unidad_base",
    "precio_unitario_comparable",
    "grupo_comparacion",
    "confianza_matching",
]

PROMOTION_COLUMNS = [
    "promo_id",
    "comercio",
    "grupo_comparacion",
    "tipo_promocion",
    "descripcion",
    "descuento_pct",
    "descuento_monto",
    "tope_descuento",
    "medio_pago",
    "dia_semana",
    "fecha_inicio",
    "fecha_fin",
    "acumulable",
    "prioridad",
]

LIST_COLUMNS = ["item_lista", "grupo_comparacion", "cantidad", "unidad", "prioridad"]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
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


def price_row(comercio="Comercio A", precio=1000, group="yerba_mate_playadito_1kg", **extra):
    row = {
        "comercio": comercio,
        "sucursal": f"{comercio} Centro",
        "localidad": "Capital",
        "producto": "Yerba Playadito 1kg",
        "marca": "Playadito",
        "categoria": "Almacen",
        "presentacion": "1 kg",
        "precio": str(precio),
        "fecha_relevamiento": "2026-07-10",
        "fuente": "test",
        "cantidad_base": "1",
        "unidad_base": "kg",
        "precio_unitario_comparable": str(precio),
        "grupo_comparacion": group,
        "confianza_matching": "0.95",
    }
    row.update(extra)
    return row


def promo_row(promo_id, tipo, **extra):
    row = {
        "promo_id": promo_id,
        "comercio": "Comercio A",
        "grupo_comparacion": "yerba_mate_playadito_1kg",
        "tipo_promocion": tipo,
        "descripcion": promo_id,
        "descuento_pct": "",
        "descuento_monto": "",
        "tope_descuento": "",
        "medio_pago": "",
        "dia_semana": "todos",
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-12-31",
        "acumulable": "no",
        "prioridad": "10",
    }
    row.update(extra)
    return row


def promotion(module, promo_id, tipo, **extra):
    return module.Promotion(
        promo_id=promo_id,
        comercio=extra.get("comercio", "Comercio A"),
        grupo_comparacion=extra.get("grupo_comparacion", "yerba_mate_playadito_1kg"),
        tipo_promocion=tipo,
        descripcion=extra.get("descripcion", promo_id),
        descuento_pct=extra.get("descuento_pct", 0.0),
        descuento_monto=extra.get("descuento_monto", 0.0),
        tope_descuento=extra.get("tope_descuento", 0.0),
        medio_pago=extra.get("medio_pago", ""),
        dia_semana=extra.get("dia_semana", "todos"),
        fecha_inicio=extra.get("fecha_inicio", date(2026, 1, 1)),
        fecha_fin=extra.get("fecha_fin", date(2026, 12, 31)),
        acumulable=extra.get("acumulable", False),
        prioridad=extra.get("prioridad", 10),
    )


def test_load_promotions_and_vigencia(tmp_path):
    module = load_module(PROMO_SCRIPT, "aplicar_promociones_vigencia")
    path = tmp_path / "promos.csv"
    write_csv(
        path,
        [
            promo_row("VIERNES", "descuento_porcentaje", descuento_pct="10", dia_semana="viernes"),
            promo_row("LUNES", "descuento_porcentaje", descuento_pct="10", dia_semana="lunes"),
        ],
        PROMOTION_COLUMNS,
    )

    promos = module.load_promotions(path)
    row = price_row()
    applicable = module.applicable_promotions(row, promos, date(2026, 7, 10))

    assert len(promos) == 2
    assert [promo.promo_id for promo in applicable] == ["VIERNES"]


def test_expired_and_future_promotions_do_not_apply():
    module = load_module(PROMO_SCRIPT, "aplicar_promociones_expired_future")
    row = price_row(precio=1000)
    promos = [
        promotion(
            module,
            "VENCIDA",
            "descuento_porcentaje",
            descuento_pct=50,
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 6, 30),
        ),
        promotion(
            module,
            "FUTURA",
            "descuento_porcentaje",
            descuento_pct=50,
            fecha_inicio=date(2026, 8, 1),
            fecha_fin=date(2026, 12, 31),
        ),
        promotion(
            module,
            "VIGENTE",
            "descuento_porcentaje",
            descuento_pct=10,
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 31),
        ),
    ]

    result = module.apply_promotions_to_row(row, promos, date(2026, 7, 11))

    assert result["precio_efectivo"] == "900.00"
    assert result["promo_id_aplicada"] == "VIGENTE"


def test_discount_percentage_fixed_amount_cap_and_special_price():
    module = load_module(PROMO_SCRIPT, "aplicar_promociones_discounts")

    pct = promotion(module, "PCT", "descuento_porcentaje", descuento_pct=10)
    fixed = promotion(module, "FIX", "descuento_monto_fijo", descuento_monto=120)
    capped = promotion(module, "CAP", "descuento_porcentaje", descuento_pct=50, tope_descuento=100)
    special = promotion(module, "SPECIAL", "precio_especial", descuento_monto=850)
    second = promotion(module, "SECOND", "segunda_unidad", descuento_pct=50)

    assert module.calculate_discount(pct, 1000, 1000) == 100
    assert module.calculate_discount(fixed, 1000, 1000) == 120
    assert module.calculate_discount(capped, 1000, 1000) == 100
    assert module.calculate_discount(special, 1000, 1000) == 150
    assert module.calculate_discount(second, 1000, 1000) == 250


def test_non_accumulable_promotion_keeps_highest_saving():
    module = load_module(PROMO_SCRIPT, "aplicar_promociones_non_accum")
    row = price_row(precio=1000)
    promos = [
        promotion(module, "PCT", "descuento_porcentaje", descuento_pct=10, prioridad=1),
        promotion(module, "FIX", "descuento_monto_fijo", descuento_monto=150, prioridad=99),
    ]

    result = module.apply_promotions_to_row(row, promos, date(2026, 7, 10))

    assert result["precio_efectivo"] == "850.00"
    assert result["ahorro_promocion"] == "150.00"
    assert result["promo_id_aplicada"] == "FIX"


def test_accumulable_promotions_follow_priority_order():
    module = load_module(PROMO_SCRIPT, "aplicar_promociones_accum")
    row = price_row(precio=1000)
    promos = [
        promotion(module, "PCT", "descuento_porcentaje", descuento_pct=10, acumulable=True, prioridad=2),
        promotion(module, "FIX", "descuento_monto_fijo", descuento_monto=100, acumulable=True, prioridad=1),
    ]

    result = module.apply_promotions_to_row(row, promos, date(2026, 7, 10))

    assert result["precio_efectivo"] == "810.00"
    assert result["ahorro_promocion"] == "190.00"
    assert result["promo_id_aplicada"] == "FIX+PCT"


def test_payment_method_filter():
    module = load_module(PROMO_SCRIPT, "aplicar_promociones_payment")
    row = price_row(precio=1000)
    promo = promotion(
        module,
        "VISA",
        "descuento_medio_pago",
        descuento_pct=20,
        medio_pago="Visa",
        acumulable=True,
    )

    assert module.apply_promotions_to_row(row, [promo], date(2026, 7, 10), "Visa")["precio_efectivo"] == "800.00"
    assert module.apply_promotions_to_row(row, [promo], date(2026, 7, 10), "Master")["precio_efectivo"] == "1000.00"


def test_script_generates_prices_with_promotions():
    subprocess.run(
        [sys.executable, "scripts/03_filtrar_san_juan.py", "--input", "data/sample/sepa/sepa_precios_simulado.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, "scripts/04_matching_productos.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [sys.executable, "scripts/06_aplicar_promociones.py", "--date", "2026-07-10"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    output = ROOT / "data" / "processed" / "precios_con_promociones.csv"
    rows = read_csv(output)
    assert output.exists()
    assert all(column in rows[0] for column in ["precio_original", "precio_efectivo", "ahorro_promocion", "promo_aplicada"])
    assert any(float(row["ahorro_promocion"]) > 0 for row in rows)


def test_shopping_list_ranking_uses_effective_price(tmp_path):
    module = load_module(SHOPPING_SCRIPT, "calcular_lista_compra_promos")
    prices_path = tmp_path / "precios_con_promociones.csv"
    list_path = tmp_path / "lista.csv"
    comparison_path = tmp_path / "comparacion.csv"
    best_path = tmp_path / "best.csv"
    report_path = tmp_path / "report.json"

    price_columns = PRICE_COLUMNS + [
        "precio_original",
        "precio_efectivo",
        "ahorro_promocion",
        "promo_id_aplicada",
        "promo_aplicada",
        "medio_pago_promocion",
        "precio_unitario_efectivo",
    ]
    write_csv(
        prices_path,
        [
            price_row("Comercio A", 1000, precio_original="1000.00", precio_efectivo="1000.00", precio_unitario_efectivo="1000.00"),
            price_row("Comercio B", 1200, precio_original="1200.00", precio_efectivo="800.00", precio_unitario_efectivo="800.00"),
        ],
        price_columns,
    )
    write_csv(
        list_path,
        [{"item_lista": "Yerba Playadito 1kg", "grupo_comparacion": "yerba_mate_playadito_1kg", "cantidad": "1", "unidad": "kg", "prioridad": "alta"}],
        LIST_COLUMNS,
    )

    report = module.calculate_shopping_list(prices_path, list_path, comparison_path, best_path, report_path)
    comparison = read_csv(comparison_path)
    best = read_csv(best_path)

    assert report["price_mode"] == "precio_efectivo"
    assert comparison[0]["comercio"] == "Comercio B"
    assert comparison[0]["costo_total_estimado"] == "800.00"
    assert best[0]["comercio_recomendado"] == "Comercio B"
    assert best[0]["precio_final"] == "800.00"
