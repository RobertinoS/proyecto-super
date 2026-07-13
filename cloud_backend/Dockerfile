FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY cloud_backend/requirements-cloud.txt /app/cloud_backend/requirements-cloud.txt
RUN pip install --no-cache-dir -r /app/cloud_backend/requirements-cloud.txt

COPY cloud_backend /app/cloud_backend
COPY src /app/src

RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

CMD ["sh", "-c", "uvicorn cloud_backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
