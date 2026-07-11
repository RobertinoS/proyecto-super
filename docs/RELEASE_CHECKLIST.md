# Release checklist MVP v1.0

Checklist para validar una entrega local estable.

## 1. Rama y estado Git

- [ ] Estar en rama de release.
- [ ] Ejecutar `git status`.
- [ ] Confirmar que no hay cambios inesperados.
- [ ] Revisar `git log --oneline --decorate -5`.

## 2. Archivos ignorados

- [ ] Confirmar que `data/raw/` no versiona datos crudos reales.
- [ ] Confirmar que `data/processed/` no versiona outputs generados.
- [ ] Confirmar que ZIPs, logs, caches y archivos temporales no se versionan.
- [ ] Confirmar que los samples demo de `data/sample/` si quedan versionados.

## 3. Compilacion Python

Comando:

```bash
python -m compileall scripts
```

Resultado esperado:

- [ ] Todos los scripts compilan sin errores en Windows/PowerShell.

## 4. Flujo demo completo

Comando:

```bash
python scripts/08_generar_mvp_demo.py
```

Resultado esperado:

- [ ] `data/processed/precios_normalizados.csv`
- [ ] `data/processed/precios_san_juan_sepa.csv`
- [ ] `data/processed/precios_matcheados.csv`
- [ ] `data/processed/precios_con_promociones.csv`
- [ ] `data/processed/comparacion_lista_compra.csv`
- [ ] `data/processed/mejor_compra_por_producto.csv`
- [ ] `data/processed/recomendacion_ruta.csv`
- [ ] `data/processed/ruta_compra_dividida.csv`

## 5. Pruebas automatizadas

Comando:

```bash
python -m pytest
```

Resultado esperado:

- [ ] Toda la suite pasa.

## 6. Dashboard

Servir:

```bash
python -m http.server 8026 --bind 127.0.0.1
```

Abrir:

```text
http://127.0.0.1:8026/dashboard/
```

Validar:

- [ ] Cargar `data/processed/precios_con_promociones.csv`.
- [ ] Cargar `data/sample/lista_compra_demo.csv`.
- [ ] Cargar `data/sample/sucursales_demo.csv`.
- [ ] Cargar `data/sample/ubicacion_usuario_demo.csv`.
- [ ] Buscar productos.
- [ ] Agregar producto a lista desde UI.
- [ ] Editar cantidad.
- [ ] Eliminar item.
- [ ] Guardar lista en `localStorage`.
- [ ] Recuperar lista.
- [ ] Exportar CSV.
- [ ] Calcular ranking por comercio.
- [ ] Ver ahorro, faltantes y mejor compra dividida.
- [ ] Calcular cercania/ruta.
- [ ] Confirmar que el dashboard aclara distancia aproximada.

## 7. Documentacion

- [ ] README actualizado.
- [ ] `docs/GUIA_USO_MVP.md` actualizado.
- [ ] `docs/DATA_CONTRACT.md` actualizado.
- [ ] `docs/TEST_PLAN.md` actualizado.
- [ ] `docs/PROJECT_STATUS.md` actualizado.
- [ ] `docs/CHANGELOG.md` actualizado.
- [ ] `docs/DATA_RETENTION_POLICY.md` actualizado.

## 8. Cierre

- [ ] No se versionan datos crudos reales.
- [ ] No se versionan outputs de `data/processed/`.
- [ ] El proyecto puede ejecutarse localmente con un unico flujo demo.
- [ ] El dashboard puede usarse sin instrucciones externas.
