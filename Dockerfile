# syntax=docker/dockerfile:1
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m appuser && mkdir -p /app/data /app/output && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s CMD python - <<'PY' \
import urllib.request, sys
try:
    urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2)
except Exception:
    sys.exit(1)
PY
CMD ["python","-m","uvicorn","main:app","--host","0.0.0.0","--port","8080"]
