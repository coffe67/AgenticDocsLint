# Backend API Dockerfile (FastAPI + Uvicorn)
FROM python:3.11-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (optional: libxml etc. not required here)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy project
COPY pyproject.toml README.md ./
COPY slideforge ./slideforge
COPY config ./config
COPY schemas ./schemas
COPY docs ./docs

# Install project and API deps
RUN pip install --upgrade pip setuptools wheel \
    && pip install . \
    && pip install fastapi uvicorn[standard] requests beautifulsoup4 python-multipart python-pptx

EXPOSE 8000

CMD ["uvicorn", "slideforge.api:app", "--host", "0.0.0.0", "--port", "8000"]

