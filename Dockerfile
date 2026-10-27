# Admin, site builder and integrity monitor of prodi.unsrat.ac.id (K-P17). The admin container builds every programme
# site into the volume "publik"; the web container (docker/web.Dockerfile) serves it with Nginx; the pemantau
# container (this image too) checks it every 10 minutes. Guide: docs/deploy.md
FROM python:3.12-slim-bookworm

# UJI_SAAT_BUILD=0 skips the test suites below (only for an urgent redeploy; docs/deploy.md)
ARG UJI_SAAT_BUILD=1
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    TZ=Asia/Makassar \
    PORT=8791 \
    PRODI_DATA=/srv/prodi/data \
    PRODI_RIWAYAT=/srv/prodi/riwayat \
    PRODI_LOG=/srv/prodi/log \
    PRODI_UNGGAHAN=/srv/prodi/unggahan \
    PRODI_MANIFES=/srv/prodi/manifes-publik.json \
    PRODI_PUBLIK=/srv/publik \
    PRODI_NGINX=/srv/nginx-buatan \
    PRODI_RAHASIA=/srv/prodi-rahasia \
    PRODI_PENYIMPANAN=lokal

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --user-group --no-create-home --home-dir /app --shell /usr/sbin/nologin prodi

WORKDIR /app
COPY platform/admin/requirements.txt platform/admin/constraints.txt /tmp/
# constraints.txt: the exact versions that passed every test suite inside this image
RUN pip install --no-cache-dir -r /tmp/requirements.txt -c /tmp/constraints.txt && rm /tmp/requirements.txt /tmp/constraints.txt

COPY platform/ /app/platform/
COPY uji/ /app/uji/
COPY docs/asal-modul.md /app/docs/asal-modul.md
# the guide is a page of the admin too (/panduan, platform/admin/panduan.py)
COPY docs/panduan-admin-prodi.md /app/docs/panduan-admin-prodi.md
COPY docker/admin-mulai.sh /usr/local/bin/admin-mulai
COPY docker/pemantau.sh /usr/local/bin/pemantau

# The code stays root's and read only for the admin: everything it writes lives in the volumes under /srv. Files
# copied from a Windows checkout can arrive without read permission.
RUN chmod -R u+rwX,go+rX,go-w /app \
    && chmod 0755 /usr/local/bin/admin-mulai /usr/local/bin/pemantau \
    && mkdir -p /srv/prodi /srv/prodi-rahasia /srv/publik /srv/nginx-buatan \
    && chown prodi:prodi /srv/prodi /srv/prodi-rahasia /srv/publik /srv/nginx-buatan \
    && chmod 0700 /srv/prodi-rahasia

USER prodi
# every test suite, inside this very image and as the user that runs the admin; the runner clears PRODI_* so no test
# can reach the volumes (uji/jalankan-semua.py)
RUN if [ "$UJI_SAAT_BUILD" != "0" ]; then python uji/jalankan-semua.py; fi

EXPOSE 8791
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 8791), 4)"
ENTRYPOINT ["/usr/local/bin/admin-mulai"]
