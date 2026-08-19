FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        binutils \
        # binutils provides objdump/ar, which GeoDjango's ctypes-based
        # GDAL bindings use to introspect the installed libgdal .so on
        # Debian-based images
    && rm -rf /var/lib/apt/lists/*

# UID/GID 1000 matches the typical host dev user, avoiding a
# permission mismatch against the docker-compose.yml bind mount
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.wsgi:application", "--workers", "1", "--bind", "0.0.0.0:8000"]
