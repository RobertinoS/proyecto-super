import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "dashboard" / "index.html"
REFERENCE = ROOT / "design_reference" / "site_model"


def html_ids(path: Path) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', path.read_text(encoding="utf-8")))


def test_site_reference_and_integration_documents_exist():
    assert (REFERENCE / "html.txt").exists()
    assert len(list(REFERENCE.glob("*.jpg"))) >= 2
    assert (ROOT / "docs" / "UI_INTEGRATION_PLAN.md").exists()
    assert (ROOT / "docs" / "UI_COMPONENT_MAPPING.md").exists()


def test_official_dashboard_preserves_contract_and_adds_site_ui():
    dashboard_ids = html_ids(DASHBOARD)
    html = DASHBOARD.read_text(encoding="utf-8")
    protected_ids = {
        "fileInput", "listInput", "branchInput", "userLocationInput",
        "qualitySummaryInput", "qualityReportInput", "searchInput", "commerceFilter",
        "builderSearchInput", "productCandidates", "shoppingListRows", "calculateListButton",
        "saveListButton", "restoreListButton", "exportListButton", "clearStoredListButton",
        "clearListButton", "listRankingRows", "splitRows", "missingRows", "qualityRows",
        "manualLatInput", "manualLonInput", "costKmInput", "calculateRouteButton",
        "routeRows", "splitRouteRows", "recalculateAllButton", "clearSessionButton",
        "processingBar", "execBestCommerce", "execBestCost", "execSavings", "execCoverage",
        "execQualityIssues", "execRouteRecommendation",
        "cloudSummaryInput", "cloudSourcesInput", "cloudAlertsInput", "cloudReviewsInput",
        "cloudSourcesRows", "cloudAlertsRows", "reviewRows", "reviewerInput",
        "exportReviewDecisionsButton",
    }

    assert protected_ids.issubset(dashboard_ids)
    assert 'data-ui-version="site-v2"' in html
    assert "Super<em>Precios</em>" in html
    assert "Panel de compra inteligente" in html
    assert "sidebar-foot" in html
    assert "@media (max-width: 600px)" in html
    assert "aria-live=\"polite\"" in html
    assert "setProcessing" in html
    assert "updateActionStates" in html
    assert "typeof confirm" in html
    assert "parseCloudJson" in html
    assert "local_export_pending_authenticated_api" in html
    assert "fetch(" not in html

    for text in [
        "Precios cargados",
        "Armar lista",
        "Ranking por comercio",
        "Mejor compra dividida",
        "Faltantes",
        "Calidad de datos",
        "Ranking por conveniencia",
        "Ruta dividida sugerida",
        "Operacion cloud",
        "Bandeja de revision",
    ]:
        assert text in html


def test_official_dashboard_javascript_keeps_business_capabilities():
    if shutil.which("node") is None:
        pytest.skip("Node.js no esta disponible para validar el JavaScript del dashboard.")

    script = r"""
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
      hidden: false,
      disabled: false,
      addEventListener() {},
    });
  }
  return elements.get(id);
}

const storage = new Map();
const context = {
  console, Intl, Number, Math, String, Array, Set, Map, JSON, Error,
  confirm: () => true,
  document: {
    body: { classList: { toggle() {} } },
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
  "comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente,cantidad_base,unidad_base,precio_unitario_comparable,grupo_comparacion,confianza_matching,precio_original,precio_efectivo,ahorro_promocion,promo_aplicada,precio_unitario_efectivo",
  "Vea,Centro,Capital,Yerba Playadito,Playadito,Almacen,1 kg,1100,2026-07-12,test,1,kg,1100,yerba_playadito_1kg,0.95,1100,1000,100,Promo Vea,1000",
  "Carrefour,Rawson,Rawson,Yerba Playadito,Playadito,Almacen,1 kg,1050,2026-07-12,test,1,kg,1050,yerba_playadito_1kg,0.95,1050,1050,0,,1050",
  "Vea,Centro,Capital,Leche entera,Marca,Lacteos,1 l,1300,2026-07-12,test,1,l,1300,leche_entera_1l,0.90,1300,1300,0,,1300"
].join("\n");
const listCsv = [
  "item_lista,grupo_comparacion,cantidad,unidad,prioridad",
  "Yerba Playadito 1kg,yerba_playadito_1kg,1,kg,alta",
  "Leche entera 1L,leche_entera_1l,1,l,media"
].join("\n");
const branchCsv = [
  "comercio,sucursal,localidad,direccion,latitud,longitud,zona,horario_referencia",
  "Vea,Centro,Capital,Centro 1,-31.5375,-68.5364,Centro,Demo",
  "Carrefour,Rawson,Rawson,Rawson 1,-31.5480,-68.5200,Sur,Demo"
].join("\n");
const originCsv = [
  "nombre_ubicacion,latitud,longitud,localidad,descripcion",
  "Casa demo,-31.5375,-68.5364,Capital,Demo"
].join("\n");
const qualityCsv = [
  "comercio,sucursal,localidad,productos_validos,categorias_cubiertas,ultima_fecha_relevamiento,antiguedad_dias,score_calidad,estado_operativo",
  "Vea,Centro,Capital,2,2,2026-07-12,0,100,OK",
  "Carrefour,Rawson,Rawson,1,1,2026-07-12,0,78,REVISAR"
].join("\n");

const rows = api.toObjects(priceCsv);
const list = api.parseList(listCsv);
const comparison = api.buildShoppingComparison(rows, list);
const split = api.buildBestSplit(rows, list);
const branches = api.parseBranches(branchCsv);
const origin = api.parseUserLocation(originCsv);
const routes = api.buildRouteRecommendations(comparison, branches, origin, 180);
const quality = api.parseQualitySummary(qualityCsv);
const cloudSummary = api.parseCloudJson(JSON.stringify({ executions_last_24h: 1, pending_reviews: 2 }), "operacion", false);
const cloudSources = api.parseCloudJson(JSON.stringify([{ source: "vea", operational_status: "HEALTHY" }]), "fuentes", true);
let sensitiveCloudMessage = "";
try { api.parseCloudJson(JSON.stringify({ api_key: "not-allowed" }), "operacion", false); } catch (error) { sensitiveCloudMessage = error.message; }
api.persistList(list);
const restored = api.readStoredList();
const exported = api.serializeListToCsv(restored);
let invalidMessage = "";
try { api.toObjects("comercio,producto\nVea,Yerba"); } catch (error) { invalidMessage = error.message; }
const privateDatasetCsv = [
  "comercio,sucursal,localidad,producto,marca,categoria,presentacion,precio,fecha_relevamiento,fuente,precio_efectivo",
  "Vea,Online nacional,San Juan,Yerba Mate Playadito 1 Kg,Playadito,Almacen,1 Kg,4250,2026-07-21,oficial:vea,4250",
  "Vea,Online nacional,San Juan,Aceite Girasol Natura 900 Ml,Natura,Almacen,900 Ml,2390,2026-07-21,oficial:vea,2390"
].join("\n");
const privateRows = api.toObjects(privateDatasetCsv);
const privateCatalog = api.buildCatalog(privateRows);
const privateList = [api.createShoppingItemFromCatalog(privateCatalog[0], 1, "un", "media")];
const privateComparison = api.buildShoppingComparison(privateRows, privateList);

console.log(JSON.stringify({
  rows: rows.length,
  list: list.length,
  catalog: api.buildCatalog(rows).length,
  comparison: comparison.length,
  bestCommerce: comparison[0].comercio,
  split: split.length,
  routes: routes.length,
  quality: quality.length,
  cloudExecutions: cloudSummary.executions_last_24h,
  cloudSources: cloudSources.length,
  cloudBadge: api.cloudBadgeClass(cloudSources[0].operational_status),
  sensitiveCloudMessage,
  promotion: api.hasPromotions(rows),
  effectivePrice: api.rowBasePrice(rows[0]),
  restored: restored.length,
  exportHeader: exported.split("\n")[0],
  invalidMessage,
  privateCatalog: privateCatalog.length,
  privateGroups: privateCatalog.map(entry => entry.grupo_comparacion).sort(),
  privateComparison: privateComparison.length,
}));
"""

    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    data = json.loads(result.stdout)
    assert data["rows"] == 3
    assert data["list"] == 2
    assert data["catalog"] == 2
    assert data["comparison"] == 2
    assert data["bestCommerce"] == "Vea"
    assert data["split"] == 2
    assert data["routes"] == 2
    assert data["quality"] == 2
    assert data["cloudExecutions"] == 1
    assert data["cloudSources"] == 1
    assert "cloud-healthy" in data["cloudBadge"]
    assert "campos sensibles" in data["sensitiveCloudMessage"]
    assert data["promotion"] is True
    assert data["effectivePrice"] == 1000
    assert data["restored"] == 2
    assert data["exportHeader"] == "item_lista,grupo_comparacion,cantidad,unidad,prioridad"
    assert "Faltan columnas en precios" in data["invalidMessage"]
    assert data["privateCatalog"] == 2
    assert data["privateGroups"] == ["Aceite Girasol Natura 900 Ml", "Yerba Mate Playadito 1 Kg"]
    assert data["privateComparison"] == 1
