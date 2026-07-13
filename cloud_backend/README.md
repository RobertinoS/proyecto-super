# Proyecto Super Cloud API

Backend FastAPI aislado para ejecutar una fuente oficial con limites, procesar calidad y preparar persistencia en Supabase. El modo predeterminado es `fixture`; no consulta internet ni publica datos.

```powershell
python -m pip install -r cloud_backend/requirements-cloud.txt
$env:SCRAPER_API_KEY = "local-test-key"
uvicorn cloud_backend.app.main:app --reload --port 8014
```

Documentacion: `http://127.0.0.1:8014/docs`.

Para una prueba real controlada se debe definir `SOURCE_MODE=live`. La publicacion sigue bloqueada mientras `ENABLE_PUBLICATION=false`.
