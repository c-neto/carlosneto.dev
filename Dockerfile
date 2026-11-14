# Build image for carlosneto.dev: only what sphinx-build needs.
# Rebuilt and pushed to ghcr.io by .github/workflows/docker-image.yml.

# Stage 1: install the dependencies into a venv
FROM python:3.10-slim AS deps
COPY requirements.txt /tmp/requirements.txt
# Drop local-only tools: live reload, terminal output, and an unused extension
RUN grep -vxE "sphinx-autobuild|rich|sphinxcontrib-bibtex" /tmp/requirements.txt > /tmp/req-build.txt \
    && python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r /tmp/req-build.txt \
    && /venv/bin/pip uninstall -y pip setuptools wheel \
    && find /venv -depth \( -name __pycache__ -o -name tests -o -name test \) -type d -exec rm -rf {} + \
    && find /venv -name "*.pyc" -delete

# Stage 2: runtime with only the venv
FROM python:3.10-slim
COPY --from=deps /venv /venv
ENV PATH=/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /site
