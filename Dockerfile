# ---- Build stage: install Python deps into an isolated prefix ----
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage: slim image with only what's needed to run ----
FROM python:3.12-slim

# ffmpeg is required by the resize/captions pipeline.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring in installed Python packages from the build stage (no pip cache,
# no build tools baked into the final image).
COPY --from=builder /install /usr/local

COPY . .

# Render sets $PORT at runtime; default to 5000 for local docker runs.
ENV PORT=5000
EXPOSE 5000

# Single worker: keeps memory use predictable on the free 512MB tier.
# Long timeout: video processing (especially with captions) can take a while.
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 300
