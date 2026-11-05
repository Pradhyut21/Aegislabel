# syntax=docker/dockerfile:1
FROM node:22.16.0-bookworm-slim AS web
WORKDIR /build
COPY frontend/package*.json ./
RUN --mount=type=secret,id=proxy_ca if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; npm ci --strict-ssl=true
COPY frontend/ ./
RUN npm run build
FROM python:3.12.10-slim-bookworm
WORKDIR /app
COPY requirements.lock.txt ./
RUN --mount=type=secret,id=proxy_ca if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; pip install --no-cache-dir -r requirements.lock.txt
COPY backend/ backend/
COPY alembic.ini ./
COPY --from=web /build/dist frontend/dist
RUN useradd --create-home aegis && mkdir -p /app/artifacts && chown -R aegis:aegis /app
USER aegis
EXPOSE 8000
CMD ["sh","-c","alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1"]
