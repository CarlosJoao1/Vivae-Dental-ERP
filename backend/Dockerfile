# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Como o Root Directory é "backend", estes caminhos já existem no contexto:
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia TODO o código do backend
COPY . .

# O Start Command da Render vai sobrepor a porta para $PORT
CMD gunicorn -b 0.0.0.0:${PORT:-5000} --timeout 120  "app:create_app()"
