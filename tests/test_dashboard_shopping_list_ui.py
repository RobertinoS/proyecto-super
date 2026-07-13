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
        "Precio efectivo",
        "Sucursales CSV",
        "Ranking por conveniencia",
        "Ruta dividida sugerida",
        "Calidad de datos",
        "Semaforo operativo",
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
const promoCsv = [
  "comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente,cantidad_base,unidad_base,precio_unitario_comparable,grupo_comparacion,confianza_matching,precio_original,precio_efectivo,ahorro_promocion,promo_aplicada,precio_unitario_efectivo",
  "Comercio A,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,1000,2026-07-10,test,1,kg,1000,yerba_mate_playadito_1kg,0.95,1000,1000,0,,1000",
  "Comercio B,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,1200,2026-07-10,test,1,kg,1200,yerba_mate_playadito_1kg,0.95,1200,800,400,20% promo,800"
].join("\n");
const promoRows = api.toObjects(promoCsv);
const promoList = [api.createShoppingItemFromCatalog(api.buildCatalog(promoRows)[0], 1, "kg", "alta")];
const promoComparison = api.buildShoppingComparison(promoRows, promoList);
const qualityReportCsv = [
  "archivo_origen,comercio,sucursal,localidad,total_filas,filas_validas,filas_invalidas,incidencias,duplicados,precios_sospechosos,fecha_min,fecha_max,antiguedad_dias,estado_calidad",
  "precios_reales_validados.csv,Comercio A,Centro,Capital,2,2,0,0,0,0,2026-07-10,2026-07-10,2,OK",
  "precios_reales_validados.csv,Comercio B,Oeste,Rivadavia,2,1,1,2,1,1,2026-07-09,2026-07-09,3,REVISAR"
].join("\n");
const qualitySummaryCsv = [
  "comercio,sucursal,localidad,productos_validos,categorias_cubiertas,ultima_fecha_relevamiento,antiguedad_dias,score_calidad,estado_operativo",
  "Comercio A,Centro,Capital,2,1,2026-07-10,2,100,OK",
  "Comercio B,Oeste,Rivadavia,1,1,2026-07-09,3,75,REVISAR"
].join("\n");
const qualityReport = api.parseQualityReport(qualityReportCsv);
const qualitySummary = api.parseQualitySummary(qualitySummaryCsv);
const rawQualityCsv = [
  "comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente",
  "Comercio A,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,1000,2026-07-10,test",
  "Comercio A,Centro,Capital,Manteca,Marca,Lacteos,200 g,abc,2026-07-10,test",
  "Comercio A,Centro,Capital,Queso,Marca,Lacteos,1 kg,7800,31/02/2026,test",
  "Comercio A,Centro,Mendoza,Arroz,Marca,Almacen,1 kg,2000,2026-07-10,test",
  "Comercio A,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,1000,2026-07-10,test"
].join("\n");
const rawQualityRows = api.toObjects(rawQualityCsv);
const branchCsv = [
  "comercio,sucursal,localidad,direccion,latitud,longitud,zona,horario_referencia",
  "Comercio A,Centro,Capital,Centro 1,-31.5375,-68.5364,Centro,Demo",
  "Comercio B,Oeste,Rivadavia,Oeste 1,-31.5279,-68.6051,Oeste,Demo"
].join("\n");
const userCsv = [
  "nombre_ubicacion,latitud,longitud,localidad,descripcion",
  "Casa demo,-31.5375,-68.5364,Capital,Demo"
].join("\n");
const branches = api.parseBranches(branchCsv);
const origin = api.parseUserLocation(userCsv);
const routeRecommendations = api.buildRouteRecommendations(comparison, branches, origin, 180);
const splitRoute = api.buildSplitRoute(split, branches, origin);
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
  promoHasPromotions: api.hasPromotions(promoRows),
  promoEffectivePrice: api.rowBasePrice(promoRows[1]),
  promoBestCommerce: promoComparison[0].comercio,
  qualityReportRows: qualityReport.length,
  qualitySummaryRows: qualitySummary.length,
  qualityBadgeOk: api.qualityBadgeClass(qualitySummary[0].estado_operativo),
  qualityBadgeReview: api.qualityBadgeClass(qualitySummary[1].estado_operativo),
  qualityBadgeStale: api.qualityBadgeClass("DESACTUALIZADO"),
  qualityWarnings: rawQualityRows.validationWarnings.join(" | "),
  routeBestCommerce: routeRecommendations[0].comercio,
  routeBestScore: routeRecommendations[0].score,
  splitRouteStops: splitRoute.length,
  haversineZero: api.haversineKm(-31.5375, -68.5364, -31.5375, -68.5364),
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
    assert data["promoHasPromotions"] is True
    assert data["promoEffectivePrice"] == 800
    assert data["promoBestCommerce"] == "Comercio B"
    assert data["qualityReportRows"] == 2
    assert data["qualitySummaryRows"] == 2
    assert "quality-ok" in data["qualityBadgeOk"]
    assert "quality-review" in data["qualityBadgeReview"]
    assert "quality-stale" in data["qualityBadgeStale"]
    assert "omitida" in data["qualityWarnings"]
    assert "fecha invalida" in data["qualityWarnings"]
    assert "localidad fuera" in data["qualityWarnings"]
    assert "duplicado" in data["qualityWarnings"]
    assert data["routeBestCommerce"] == "Comercio A"
    assert data["routeBestScore"] >= 2200
    assert data["splitRouteStops"] == 2
    assert data["haversineZero"] == 0
