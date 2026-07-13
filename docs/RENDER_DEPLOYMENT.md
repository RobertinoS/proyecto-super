# Despliegue manual de FastAPI en Render

Sprint 14 no despliega automaticamente. `render.yaml` deja `autoDeploy: false`, fixture y publicacion desactivada.

## Pasos

1. Revisar y mergear el sprint.
2. En Render, crear Blueprint o Web Service desde el repositorio.
3. Usar Docker con `cloud_backend/Dockerfile`, contexto raiz.
4. Confirmar comando final `uvicorn ... --port $PORT`.
5. Configurar secretos desde `.env.example`; nunca pegar valores en Git.
6. Mantener `SOURCE_MODE=fixture` durante smoke inicial.
7. Configurar health check `/health` y esperar HTTP 200.
8. Probar `/docs`, autenticacion y una corrida fixture.
9. Cambiar a `SOURCE_MODE=live` solo tras revision legal/tecnica.
10. Mantener `ENABLE_PUBLICATION=false` durante Sprint 14.

Render recomienda que el servicio escuche `PORT` y permite `healthCheckPath`: [Web Services](https://render.com/docs/web-services), [Health Checks](https://render.com/docs/health-checks).

## Arranque en frio

FastAPI no recibe monitor UptimeRobot. n8n ejecuta `/health` con 120 segundos y tres intentos antes del job. Un servicio Free puede dormir tras 15 minutos y tardar cerca de un minuto en volver; el filesystem es efimero y las horas Free se comparten por workspace: [Render Free](https://render.com/docs/free).

## Logs, rollback y persistencia

- Usar logs Render sin headers sensibles.
- Rollback a una imagen/deploy anterior desde Events.
- No guardar SQLite, snapshots ni CSV persistentes en Render.
- Supabase es la persistencia; un fallo impide publicar.

## Control mensual

- UptimeRobot mantiene solo n8n.
- No crear monitor permanente para FastAPI.
- Revisar Monthly Included Usage, ancho de banda y build minutes.
- Si hay riesgo de suspension, reducir volumen/frecuencia o pagar solo el servicio critico.
- Pasar a pago por SLA, concurrencia, catalogos grandes, jobs asincronos o consumo sostenido.
