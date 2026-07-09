# Checklist de validacion

1. `python -m pip install -r requirements.txt` instala dependencias.
2. `python src/run_pipeline.py --all` actualiza fuentes oficiales y exporta JSON.
3. `python src/run_pipeline.py --discover` genera `data/processed/source_discovery.csv`.
4. `python src/run_pipeline.py --export` crea JSON en `data/export/`.
5. `python -m pytest` pasa la suite local.
6. `python -m http.server 8000` permite abrir `http://localhost:8000/app/`.
7. El dashboard muestra filtros sin categorias duplicadas.
8. La lista de compra permite cargar item y cantidad.
9. La ruta eficiente multiplica subtotales por cantidad.
10. El usuario puede guardar y volver a cargar una lista.
11. `http://localhost:8000/app/promociones.html` muestra promociones y tarjetas.
12. `rg -n -uu --hidden -e "api_key|secret|token|password|private_key" .` no debe exponer secretos reales.
