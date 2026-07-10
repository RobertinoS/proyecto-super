import json
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_shopping_list_ui_sections_exist():
    html = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")

    for text in [
        "Precios cargados",
        "Armar lista",
        "Lista actual",
        "Ranking por comercio",
        "Mejor compra dividida",
        "Faltantes",
        "Exportar CSV",
    ]:
        assert text in html


def test_dashboard_builder_storage_export_and_ranking():
    if shutil.which("node") is None:
        pytest.skip("Node.js no esta disponible para validar el JS embebido del dashboard.")

    js = r"""
const fs = require("fs");
const vm = require("vm");
const html = fs.readFileSync("dashboard/index.html", "utf8");
const match = html.match(/<script>([\s\S]*)<\/script>/);
if (!match) throw new Error("script not found");

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id,
      value: id === "defaultQuantityInput" ? "1" : "",
      textContent: "",
      innerHTML: "",
      className: "",
      addEventListener() {},
    });
  }
  return elements.get(id);
}

const storage = new Map();
const context = {
  console,
  Intl,
  Number,
  Math,
  String,
  Array,
  Set,
  Map,
  JSON,
  Error,
  document: {
    getElementById: element,
    createElement: () => ({ click() {} }),
  },
  FileReader: function () {},
  Blob: function () {},
  URL: { createObjectURL: () => "blob:test", revokeObjectURL() {} },
  localStorage: {
    setItem: (key, value) => storage.set(key, value),
    getItem: key => storage.get(key) || null,
    removeItem: key => storage.delete(key),
  },
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(match[1], context, { filename: "dashboard/index.html" });

const api = context.__proyectoSuperDashboard;
const priceCsv = [
  "comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente,cantidad_base,unidad_base,precio_unitario_comparable,grupo_comparacion,confianza_matching",
  "Comercio A,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,1000,2026-07-10,test,1,kg,1000,yerba_mate_playadito_1kg,0.95",
  "Comercio B,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,900,2026-07-10,test,1,kg,900,yerba_mate_playadito_1kg,0.95",
  "Comercio A,Centro,Capital,Leche entera,La Serenisima,Lacteos,1 l,1200,2026-07-10,test,1,l,1200,leche_entera_la_serenisima_1l,0.95"
].join("\n");

const rows = api.toObjects(priceCsv);
const catalog = api.buildCatalog(rows);
const yerba = catalog.find(item => item.grupo_comparacion === "yerba_mate_playadito_1kg");
const leche = catalog.find(item => item.grupo_comparacion === "leche_entera_la_serenisima_1l");

let list = [];
list = api.upsertListItem(list, api.createShoppingItemFromCatalog(yerba, 1, "kg", "alta"));
list = api.upsertListItem(list, api.createShoppingItemFromCatalog(yerba, 1, "kg", "alta"));
list = api.updateListItem(list, 0, { cantidad: "1", unidad: "kg" });
list = api.upsertListItem(list, api.createShoppingItemFromCatalog(leche, 1, "l", "media"));
const afterRemove = api.removeListItemAt(list, 1);
list = api.upsertListItem(afterRemove, api.createShoppingItemFromCatalog(leche, 1, "l", "media"));

const saved = api.persistList(list);
const restored = api.readStoredList();
const exported = api.serializeListToCsv(restored);
const comparison = api.buildShoppingComparison(rows, restored);
const split = api.buildBestSplit(rows, restored);
api.clearStoredList();
const cleared = api.readStoredList();

const result = {
  rows: rows.length,
  catalog: catalog.length,
  saved,
  restored: restored.length,
  cleared: cleared.length,
  exportHeader: exported.split("\n")[0],
  exportHasYerba: exported.includes("yerba_mate_playadito_1kg"),
  bestCommerce: comparison[0].comercio,
  bestCoverage: comparison[0].cobertura,
  missingCommerceCount: comparison.filter(row => row.faltantes.length > 0).length,
  splitCount: split.length,
  splitBestYerba: split.find(row => row.item.grupo_comparacion === "yerba_mate_playadito_1kg").best.row.comercio,
};

console.log(JSON.stringify(result));
"""

    result = subprocess.run(
        ["node", "-e", js],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["rows"] == 3
    assert data["catalog"] == 2
    assert data["saved"] is True
    assert data["restored"] == 2
    assert data["cleared"] == 0
    assert data["exportHeader"] == "item_lista,grupo_comparacion,cantidad,unidad,prioridad"
    assert data["exportHasYerba"] is True
    assert data["bestCommerce"] == "Comercio A"
    assert data["bestCoverage"] == 100
    assert data["missingCommerceCount"] == 1
    assert data["splitCount"] == 2
    assert data["splitBestYerba"] == "Comercio B"
