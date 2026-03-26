# Media worker image: ffmpeg for mux/transcode (Shotstack-off path). Pin versions in CI/CD.
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Override with real worker command (Python CLI, Celery, Arq media queue, etc.)
ENV FFMPEG_VERSION=system
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ffmpeg -version >/dev/null 2>&1 || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
