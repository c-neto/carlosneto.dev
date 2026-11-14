# Build image for carlosneto.dev: Python + Sphinx dependencies preinstalled.
# Rebuilt and pushed to ghcr.io by .github/workflows/docker-image.yml.
FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends make git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

WORKDIR /site
