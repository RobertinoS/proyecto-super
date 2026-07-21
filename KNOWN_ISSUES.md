# Limitaciones conocidas del piloto interno

Fecha: 2026-07-21.

Estas limitaciones no impiden el flujo del piloto interno ni habilitan trabajo
adicional durante el cierre.

1. La fuente Vea del piloto identifica precios del canal `ONLINE`; no debe
   presentarse como precio fisico de una sucursal ni como una ruta de compra
   confirmada.
2. Un CSV privado proveniente directamente de la canalizacion cloud puede no
   contener `unidad_base` ni matching entre comercios. El dashboard usa el
   nombre exacto del producto como grupo de comparacion; para ese archivo el
   operador debe elegir unidad `un` antes de agregarlo a la lista.
3. Con datos de una sola cadena, el ranking mostrara una sola opcion y el
   ahorro entre comercios sera cero. Es un resultado esperado, no un error.
4. La disponibilidad live de Vea puede cambiar o aplicar restricciones. Ante
   CAPTCHA, 403, 429, 5xx o estructura no reconocida, se detiene la prueba y
   se vuelve a fixture; no se evaden protecciones.
5. La autenticacion humana Supabase Auth/JWT sigue experimental. El piloto
   opera solo mediante FastAPI y una clave de servicio entregada por un canal
   seguro; esa clave nunca se pega en el dashboard.
6. No hay publicacion publica, schedule automatico, revocacion/restauracion
   automatica, interfaz administrativa ni operacion multicomercio completa.

