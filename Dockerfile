FROM node:20-slim AS frontend
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ .
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached unless pyproject.toml changes)
COPY pyproject.toml .
RUN mkdir -p mindpalace && touch mindpalace/__init__.py && \
    pip install --no-cache-dir . && \
    rm -rf mindpalace

# Now copy actual source (this layer changes often but deps are cached)
COPY mindpalace/ mindpalace/
COPY scripts/ scripts/

# Copy frontend build
COPY --from=frontend /app/web/dist web/dist

EXPOSE 8080

CMD ["uvicorn", "mindpalace.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
