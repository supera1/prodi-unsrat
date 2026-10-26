# Web server of prodi.unsrat.ac.id: Nginx serving only the volume "publik" (built by the admin container), and the
# admin for UNSRAT's network only. The redirects of old programme slugs come from the builder through a filter
# (50-prodi-pantau.sh). HTTPS is ended in front (a load balancer) or here (HTTPS_DI_VM=1). Guide: docs/deploy.md
FROM nginx:stable-alpine

ENV TZ=Asia/Makassar
RUN apk add --no-cache tzdata \
    && rm -f /etc/nginx/conf.d/default.conf \
    && mkdir -p /srv/publik /srv/nginx-buatan /srv/acme /etc/nginx/tls /etc/nginx/prodi /etc/nginx/prodi-tetap \
    # a new volume takes the owner of this folder when the web container happens to be created first: it must stay
    # writable for the admin container (user 10001, Dockerfile), which builds into it
    && chown 10001:10001 /srv/publik /srv/nginx-buatan
COPY docker/nginx/prodi.conf /etc/nginx/conf.d/prodi.conf
COPY docker/nginx/lokasi-situs.conf docker/nginx/lokasi-admin.conf docker/nginx/tls.conf docker/nginx/header-keamanan.conf \
     /etc/nginx/prodi-tetap/
COPY docker/nginx/40-prodi-jaringan.sh docker/nginx/45-prodi-https.sh docker/nginx/50-prodi-pantau.sh /docker-entrypoint.d/
RUN chmod 0755 /docker-entrypoint.d/40-prodi-jaringan.sh /docker-entrypoint.d/45-prodi-https.sh \
               /docker-entrypoint.d/50-prodi-pantau.sh \
    && chmod 0644 /etc/nginx/conf.d/prodi.conf /etc/nginx/prodi-tetap/*.conf

EXPOSE 80 8081 443 8443
# Nginx answers, and the admin container has built the sites at least once
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/sehat && test -f /srv/publik/robots.txt || exit 1
