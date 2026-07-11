from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


PRICE_REQUIRED_COLUMNS = [
    "comercio",
    "producto",
    "precio",
    "grupo_comparacion",
    "cantidad_base",
    "unidad_base",
]

PROMOTION_REQUIRED_COLUMNS = [
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

PROMOTION_TYPES = {
    "descuento_porcentaje",
    "descuento_monto_fijo",
    "segunda_unidad",
    "precio_especial",
    "descuento_medio_pago",
}

OUTPUT_COLUMNS = [
    "precio_original",
    "precio_efectivo",
    "ahorro_promocion",
    "promo_id_aplicada",
    "promo_aplicada",
    "medio_pago_promocion",
    "precio_unitario_efectivo",
]

WEEKDAYS = {
    "lunes": 0,
    "monday": 0,
    "martes": 1,
    "tuesday": 1,
    "miercoles": 2,
    "miércoles": 2,
    "wednesday": 2,
    "jueves": 3,
    "thursday": 3,
    "viernes": 4,
    "friday": 4,
    "sabado": 5,
    "sábado": 5,
    "saturday": 5,
    "domingo": 6,
    "sunday": 6,
}

ALL_DAYS = {"", "todos", "todo", "diario", "all", "todos los dias", "todos los días"}


@dataclass(frozen=True)
class Promotion:
    promo_id: str
    comercio: str
    grupo_comparacion: str
    tipo_promocion: str
    descripcion: str
    descuento_pct: float
    descuento_monto: float
    tope_descuento: float
    medio_pago: str
    dia_semana: str
    fecha_inicio: date | None
    fecha_fin: date | None
    acumulable: bool
    prioridad: int


@dataclass(frozen=True)
class PromotionApplication:
    promotion: Promotion
    ahorro: float
    precio_despues: float


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
    return number if number >= 0 else None


def parse_int(value: Any, default: int = 1000) -> int:
    number = parse_number(value)
    return int(number) if number is not None else default


def format_money(value: float | None) -> str:
    return "" if value is None else f"{max(value, 0):.2f}"


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y%m%d"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Fecha invalida: {text}")


def parse_bool(value: Any) -> bool:
    return normalize_text(value) in {"si", "s", "yes", "true", "1", "y"}


def weekday_matches(value: Any, calculation_date: date) -> bool:
    text = normalize_text(value)
    if text in ALL_DAYS:
        return True
    values = [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
    if not values:
        return True
    return any(WEEKDAYS.get(day) == calculation_date.weekday() for day in values)


def payment_matches(promo_payment: str, selected_payment: str | None) -> bool:
    if not promo_payment:
        return True
    if not selected_payment:
        return True
    return normalize_text(promo_payment) == normalize_text(selected_payment)


def load_promotions(path: Path) -> list[Promotion]:
    rows = read_csv(path)
    validate_columns(rows, PROMOTION_REQUIRED_COLUMNS, "promociones")
    promotions: list[Promotion] = []
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        promo_type = normalize_text(row.get("tipo_promocion"))
        if promo_type not in PROMOTION_TYPES:
            errors.append(f"Fila {index}: tipo_promocion invalido: {row.get('tipo_promocion', '')}")
            continue
        try:
            start = parse_date(row.get("fecha_inicio"))
            end = parse_date(row.get("fecha_fin"))
        except ValueError as exc:
            errors.append(f"Fila {index}: {exc}")
            continue
        if start and end and start > end:
            errors.append(f"Fila {index}: fecha_inicio posterior a fecha_fin.")
            continue
        promotions.append(
            Promotion(
                promo_id=row.get("promo_id", "").strip() or f"promo_{index}",
                comercio=row.get("comercio", "").strip(),
                grupo_comparacion=row.get("grupo_comparacion", "").strip(),
                tipo_promocion=promo_type,
                descripcion=row.get("descripcion", "").strip(),
                descuento_pct=parse_number(row.get("descuento_pct")) or 0.0,
                descuento_monto=parse_number(row.get("descuento_monto")) or 0.0,
                tope_descuento=parse_number(row.get("tope_descuento")) or 0.0,
                medio_pago=row.get("medio_pago", "").strip(),
                dia_semana=row.get("dia_semana", "").strip(),
                fecha_inicio=start,
                fecha_fin=end,
                acumulable=parse_bool(row.get("acumulable")),
                prioridad=parse_int(row.get("prioridad")),
            )
        )
    if errors:
        raise ValueError("Errores en promociones: " + " | ".join(errors))
    return promotions


def promotion_is_active(promotion: Promotion, calculation_date: date) -> bool:
    if promotion.fecha_inicio and calculation_date < promotion.fecha_inicio:
        return False
    if promotion.fecha_fin and calculation_date > promotion.fecha_fin:
        return False
    return weekday_matches(promotion.dia_semana, calculation_date)


def promotion_matches_row(
    promotion: Promotion,
    row: dict[str, str],
    calculation_date: date,
    medio_pago: str | None = None,
) -> bool:
    if not promotion_is_active(promotion, calculation_date):
        return False
    if promotion.comercio and normalize_text(promotion.comercio) != normalize_text(row.get("comercio")):
        return False
    if promotion.grupo_comparacion and promotion.grupo_comparacion != row.get("grupo_comparacion", "").strip():
        return False
    return payment_matches(promotion.medio_pago, medio_pago)


def applicable_promotions(
    row: dict[str, str],
    promotions: list[Promotion],
    calculation_date: date,
    medio_pago: str | None = None,
) -> list[Promotion]:
    return [
        promotion
        for promotion in promotions
        if promotion_matches_row(promotion, row, calculation_date, medio_pago)
    ]


def calculate_discount(promotion: Promotion, original_price: float, current_price: float) -> float:
    discount = 0.0
    if promotion.tipo_promocion == "descuento_porcentaje":
        discount = current_price * promotion.descuento_pct / 100
    elif promotion.tipo_promocion == "descuento_monto_fijo":
        discount = promotion.descuento_monto
    elif promotion.tipo_promocion == "segunda_unidad":
        # A 50% discount on the second unit is equivalent to 25% off per unit.
        discount = current_price * (promotion.descuento_pct / 100) / 2
    elif promotion.tipo_promocion == "precio_especial":
        discount = current_price - promotion.descuento_monto
    elif promotion.tipo_promocion == "descuento_medio_pago":
        discount = current_price * promotion.descuento_pct / 100 if promotion.descuento_pct else promotion.descuento_monto

    discount = max(discount, 0.0)
    if promotion.tope_descuento > 0:
        discount = min(discount, promotion.tope_descuento)
    return min(discount, current_price)


def apply_accumulable_promotions(original_price: float, promotions: list[Promotion]) -> tuple[float, list[PromotionApplication]]:
    current_price = original_price
    applications: list[PromotionApplication] = []
    for promotion in sorted(promotions, key=lambda promo: (promo.prioridad, promo.promo_id)):
        discount = calculate_discount(promotion, original_price, current_price)
        if discount <= 0:
            continue
        current_price = max(current_price - discount, 0.0)
        applications.append(PromotionApplication(promotion, discount, current_price))
    return original_price - current_price, applications


def best_non_accumulable_application(
    original_price: float,
    promotions: list[Promotion],
) -> tuple[float, list[PromotionApplication]]:
    best: PromotionApplication | None = None
    for promotion in promotions:
        discount = calculate_discount(promotion, original_price, original_price)
        if discount <= 0:
            continue
        application = PromotionApplication(promotion, discount, original_price - discount)
        if best is None or application.ahorro > best.ahorro or (
            application.ahorro == best.ahorro and promotion.prioridad < best.promotion.prioridad
        ):
            best = application
    return (best.ahorro, [best]) if best else (0.0, [])


def apply_promotions_to_row(
    row: dict[str, str],
    promotions: list[Promotion],
    calculation_date: date,
    medio_pago: str | None = None,
) -> dict[str, str]:
    original_price = parse_number(row.get("precio"))
    if original_price is None or original_price <= 0:
        raise ValueError(f"Precio invalido para producto {row.get('producto', '')}")

    candidates = applicable_promotions(row, promotions, calculation_date, medio_pago)
    accumulable = [promotion for promotion in candidates if promotion.acumulable]
    non_accumulable = [promotion for promotion in candidates if not promotion.acumulable]

    accum_saving, accum_apps = apply_accumulable_promotions(original_price, accumulable)
    non_accum_saving, non_accum_apps = best_non_accumulable_application(original_price, non_accumulable)

    if non_accum_saving >= accum_saving:
        total_saving = non_accum_saving
        applications = non_accum_apps
    else:
        total_saving = accum_saving
        applications = accum_apps

    effective_price = max(original_price - total_saving, 0.0)
    quantity = parse_number(row.get("cantidad_base"))
    effective_unit_price = effective_price / quantity if quantity and quantity > 0 else effective_price

    out = dict(row)
    out["precio_original"] = format_money(original_price)
    out["precio_efectivo"] = format_money(effective_price)
    out["ahorro_promocion"] = format_money(total_saving)
    out["promo_id_aplicada"] = "+".join(application.promotion.promo_id for application in applications)
    out["promo_aplicada"] = " | ".join(application.promotion.descripcion for application in applications)
    out["medio_pago_promocion"] = " | ".join(
        dict.fromkeys(application.promotion.medio_pago for application in applications if application.promotion.medio_pago)
    )
    out["precio_unitario_efectivo"] = format_money(effective_unit_price)
    return out


def apply_promotions(
    prices_path: Path,
    promotions_path: Path,
    output_path: Path,
    report_path: Path | None = None,
    calculation_date: date | None = None,
    medio_pago: str | None = None,
) -> dict[str, Any]:
    rows = read_csv(prices_path)
    validate_columns(rows, PRICE_REQUIRED_COLUMNS, "precios")
    promotions = load_promotions(promotions_path)
    calculation_date = calculation_date or date.today()

    processed: list[dict[str, str]] = []
    invalid_rows: list[str] = []
    applied_count = 0
    total_saving = 0.0
    for index, row in enumerate(rows, start=2):
        try:
            out = apply_promotions_to_row(row, promotions, calculation_date, medio_pago)
        except ValueError as exc:
            invalid_rows.append(f"Fila {index}: {exc}")
            continue
        if (parse_number(out.get("ahorro_promocion")) or 0.0) > 0:
            applied_count += 1
        total_saving += parse_number(out.get("ahorro_promocion")) or 0.0
        processed.append(out)

    if not processed:
        raise ValueError("No se generaron filas validas con promociones.")

    fieldnames = list(rows[0].keys())
    for column in OUTPUT_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)
    write_csv(output_path, processed, fieldnames)

    report = {
        "prices": str(prices_path),
        "promotions": str(promotions_path),
        "output": str(output_path),
        "calculation_date": calculation_date.isoformat(),
        "medio_pago": medio_pago or "",
        "rows_in": len(rows),
        "rows_out": len(processed),
        "promotions_loaded": len(promotions),
        "rows_with_promotion": applied_count,
        "total_saving": format_money(total_saving),
        "invalid_rows": invalid_rows,
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Aplica promociones y calcula precio efectivo.")
    parser.add_argument("--prices", default=str(root / "data" / "processed" / "precios_matcheados.csv"))
    parser.add_argument("--promotions", default=str(root / "data" / "sample" / "promociones_demo.csv"))
    parser.add_argument("--output", default=str(root / "data" / "processed" / "precios_con_promociones.csv"))
    parser.add_argument("--report", default=str(root / "data" / "processed" / "precios_con_promociones_reporte.json"))
    parser.add_argument("--date", default="", help="Fecha de calculo YYYY-MM-DD. Por defecto usa hoy.")
    parser.add_argument("--medio-pago", default="", help="Medio de pago elegido. Si se omite, muestra promos disponibles.")
    args = parser.parse_args()

    try:
        calculation_date = parse_date(args.date) if args.date else date.today()
        report = apply_promotions(
            Path(args.prices),
            Path(args.promotions),
            Path(args.output),
            Path(args.report),
            calculation_date,
            args.medio_pago,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
