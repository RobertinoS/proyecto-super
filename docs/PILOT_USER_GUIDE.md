# Guia de uso del piloto interno

## Alcance y seguridad

Este piloto es privado, manual y supervisado. Use solo el entorno staging
aislado de Proyecto Super y la clave de servicio recibida por un canal seguro.
No copie la clave, una URL temporal ni valores de configuracion en el
dashboard, capturas, archivos o chat.

Al terminar, todos los flags deben volver a:

```text
PROJECT_SUPER_AUTOMATION_ENABLED=false
SOURCE_MODE=fixture
ENABLE_PUBLICATION=false
ENABLE_CLOUD_PUBLICATION=false
ENABLE_PRIVATE_PUBLICATION=false
ENABLE_INTERNAL_DATASET_ACCESS=false
```

## Flujo fixture reproducible

1. Confirme que FastAPI staging responde `GET /health` y que el modo indicado
   es `fixture`. Si no responde, siga la recuperacion de
   `docs/STAGING_INCIDENT_RUNBOOK.md` y no continue.
2. Abra Swagger de FastAPI desde el enlace interno autorizado. En
   `POST /jobs/scrape`, use una ejecucion manual con `source=vea`,
   `dry_run=true`, una pagina y hasta tres productos. Guarde solo el `run_id`
   y el `execution_id` en su registro operativo.
3. Consulte `GET /jobs/{run_id}` hasta que finalice. Luego invoque
   `POST /pipeline/process` con el `run_id` y `dry_run=true`.
4. Revise las incidencias mediante `GET /reviews` y el estado operativo. No
   apruebe un dataset con una incidencia critica pendiente.
5. Solicite aprobacion con `POST /runs/{run_id}/request-approval`. Una persona
   autorizada registra la decision con el endpoint de aprobacion. Para cada
   decision indique un responsable y una clave de idempotencia nueva; no use
   nombres personales ni secretos. Confirme estado aprobado, cantidad de
   filas, calidad y checksum.
6. Para una unica ventana de publicacion privada autorizada, active solo en
   staging `ENABLE_PRIVATE_PUBLICATION=true` y
   `ENABLE_INTERNAL_DATASET_ACCESS=true`. Mantenga fixture, publicaciones
   generales apagadas y automatizacion apagada.
7. Ejecute `POST /runs/{run_id}/private-publish` con `dry_run=false`. Confirme
   `PUBLISHED_PRIVATE`, checksum y cantidad de filas. El bucket debe seguir
   privado.
8. Solicite el acceso con
   `POST /internal/private-datasets/{dataset_id}/access`, enviando una clave
   de servicio por el mecanismo autorizado y un `request_id` nuevo de al menos
   ocho caracteres. Descargue el CSV desde la URL temporal recibida. No guarde
   ni reenvie esa URL.
9. Cierre la ventana: vuelva ambos flags temporales a `false`, confirme que no
   hay objeto publico ni URL permanente y registre el resultado.

## Prueba Vea live limitada

1. Solo despues de completar fixture, abra una ventana manual y establezca
   temporalmente `SOURCE_MODE=live` en staging.
2. Mantenga `dry_run=true`, una pagina y un maximo de tres productos. Nunca
   active schedule, publicacion general o publicacion publica.
3. Revise que el resultado se marque como canal `ONLINE`. Si aparece CAPTCHA,
   403, 429, 5xx o estructura inesperada, detengase sin reintentos agresivos.
4. Siga revision, aprobacion y la entrega privada bajo supervision humana. Al
   terminar, restaure inmediatamente `SOURCE_MODE=fixture` y todos los flags
   seguros del inicio de esta guia.

## Cargar y comparar en el dashboard

1. En la carpeta del repositorio, ejecute:

   ```powershell
   python -m http.server 8026 --bind 127.0.0.1
   ```

2. Abra `http://127.0.0.1:8026/dashboard/`.
3. En **Carga de datos**, cargue el CSV descargado. Confirme el mensaje de
   exito y la cantidad de precios antes de continuar.
4. Vaya a **Lista de compra**. Busque un producto, elija la unidad y agregue
   una cantidad. Para un CSV cloud sin unidad comparable, seleccione `un`.
5. Presione **Calcular ranking**. Revise comercio, cobertura, costo, ahorro y
   faltantes. Con una sola cadena, el ahorro entre comercios puede ser cero.
6. Para la demo local puede cargar tambien los archivos de muestra de lista,
   sucursales y ubicacion. No interprete una fuente online como precio fisico
   de sucursal.
7. Al finalizar, cierre el servidor local y confirme otra vez los flags de
   seguridad. El dashboard no requiere ni acepta una clave de servicio.
