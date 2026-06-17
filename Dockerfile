# Stage 1: Build Vue.js frontend
FROM node:20.14.0 AS vue-builder
WORKDIR /build/openrepo
COPY frontend/ ./
RUN npm install && npm run build

# Stage 2: Build Python dependencies
FROM ubuntu:24.04 AS python-builder
RUN apt-get update && apt-get install -y \
    git \
    libapt-pkg-dev \
    libpq-dev \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY web/requirements.txt .
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 3: Production runtime image
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    createrepo-c \
    curl \
    gpg \
    gzip \
    libapt-pkg6.0 \
    libpq5 \
    nginx \
    python3 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/createrepo_c /usr/bin/createrepo

WORKDIR /app

# Copy Python virtual environment
COPY --from=python-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy compiled Vue frontend
COPY --from=vue-builder /build/openrepo/dist /app/frontend-dist

# Copy Django app
COPY web /app/django

# Copy Nginx configuration
COPY deploy/nginx/nginx.conf.prod /etc/nginx/nginx.conf

# Copy entrypoint script
COPY deploy/run_openrepoweb /usr/bin/

# Collect Django static files
RUN mkdir -p /var/lib/openrepo/packages/ && \
    /venv/bin/python /app/django/manage.py collectstatic --noinput
