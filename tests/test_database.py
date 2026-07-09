import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database import create_schema, insert_price_rows


def test_database_insert_price_row():
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    saved = insert_price_rows(
        conn,
        [
            {
                "capture_date": "2026-07-07",
                "source_id": "test",
                "chain": "Demo",
                "branch_name": "Centro",
                "province": "San Juan",
                "city": "Capital",
                "product_name_raw": "Arroz Demo 1 Kg",
                "brand": "Demo",
                "category": "Almacen",
                "price_list": "$ 1.000",
                "confidence_score": 90,
            }
        ],
    )
    assert saved >= 1
    assert conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0] == 1
    assert conn.execute("SELECT reference_unit FROM prices").fetchone()[0] == "kg"
    conn.close()
