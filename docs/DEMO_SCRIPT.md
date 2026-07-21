# Guion de demostracion del piloto interno

Duracion orientativa: 10 a 15 minutos. La demostracion se realiza con datos
fixture o con una ventana Vea live limitada ya autorizada.

1. **Objetivo (1 min).** Mostrar que un operador puede convertir una corrida
   controlada en un CSV privado utilizable para comparar compras.
2. **Seguridad (1 min).** Mostrar que automatizacion y publicaciones generales
   estan apagadas. Aclarar que no se muestra ninguna clave ni URL temporal.
3. **Extraccion (2 min).** Ejecutar la corrida fixture limitada y mostrar su
   `run_id`, cantidad de productos y estado de proceso.
4. **Revision (2 min).** Abrir la cola de revision, explicar que incidencias
   criticas bloquean la aprobacion y registrar una decision autorizada.
5. **Aprobacion y entrega (2 min).** Mostrar estado aprobado, checksum y la
   entrega privada controlada. Solicitar una URL temporal y descargar el CSV
   sin mostrar la URL completa.
6. **Dashboard (3 min).** Cargar el CSV, buscar un producto, seleccionar `un`
   si el CSV no incluye unidad comparable, agregar una cantidad y calcular el
   ranking. Mostrar cobertura, faltantes y ahorro.
7. **Cierre (1 min).** Restaurar los flags seguros y confirmar bucket privado,
   ausencia de publicacion publica y kill switch apagado.

Resultado esperado: el archivo se carga, la lista calcula una comparacion
entendible y todos los controles vuelven a su estado seguro.

