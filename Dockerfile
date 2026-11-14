# Build image for carlosneto.dev: sphinx-build, its dependencies and make.
# Rebuilt and pushed to ghcr.io by .github/workflows/docker-image.yml.

# Stage 1: install the dependencies into a venv
FROM python:3.10-slim AS deps
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && /venv/bin/pip uninstall -y pip setuptools wheel \
    && find /venv -depth \( -name __pycache__ -o -name tests -o -name test \) -type d -exec rm -rf {} + \
    && find /venv -name "*.pyc" -delete

# Stage 2: runtime with the venv, make (`make dirhtml`) and git (gh-pages publish)
FROM python:3.10-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends make git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=deps /venv /venv
# VENV points the Makefile at the image's virtualenv
ENV PATH=/venv/bin:$PATH \
    VENV=/venv \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /site
