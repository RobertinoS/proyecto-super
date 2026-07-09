# Instalacion

## 1. Crear entorno virtual

```bash
cd "C:\Users\Rober\Desktop\Proyecto Super"
python -m venv .venv
.venv\Scripts\activate
```

## 2. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

Dependencias principales: `requests`, `pandas`, `beautifulsoup4`, `lxml`, `python-dotenv`, `Unidecode`, `rapidfuzz`, `PyYAML`, `pytest`.

## 3. Preparar variables locales

```bash
copy .env.example .env
```

Editar `.env` solo si queres cambiar rutas. No guardar secretos.

## 4. Ejecutar

```bash
python src/run_pipeline.py --all
```

Comandos utiles:

```bash
python src/run_pipeline.py --discover
python src/run_pipeline.py --scrape all
python src/run_pipeline.py --export
```

## 5. Abrir dashboard

```bash
python -m http.server 8000
```

Abrir `http://localhost:8000/app/`.

## Errores frecuentes en Windows

- `Acceso denegado`: usar la ruta writable `C:\Users\Rober\Desktop\Proyecto Super`.
- `pytest no se reconoce`: usar `python -m pytest`.
- `No module named dotenv`: ejecutar `python -m pip install -r requirements.txt`.
- Dashboard sin datos: ejecutar `python src/run_pipeline.py --export` y abrir con `http.server`, no directo con doble clic.
