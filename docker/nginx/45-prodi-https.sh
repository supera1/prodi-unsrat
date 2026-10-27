#!/bin/sh
# Run by the Nginx image before Nginx starts (/docker-entrypoint.d). Chooses what ports 80 and 8081 do:
#   HTTPS_DI_VM=0 (default)  HTTPS is ended in front of the stack (a load balancer): 80 serves the sites, 8081 the admin.
#   HTTPS_DI_VM=1            TLS here, with the certificate in /etc/nginx/tls (TLS_FOLDER on the VM): 443 serves the
#                            sites and 8443 the admin; 80 and 8081 only redirect to them. PORT_SITUS_HTTPS and
#                            PORT_ADMIN_HTTPS are their ports on the VM, used in the redirects.
set -eu
P=/etc/nginx/prodi
T=/etc/nginx/prodi-tetap
mkdir -p "$P"
rm -f /etc/nginx/conf.d/https.conf

akhiran_port() {  # ":8444", or nothing for 443
    case "$1" in
        443) echo "" ;;
        ""|*[!0-9]*) echo "45-prodi-https: port '$1' tidak sah" >&2; return 1 ;;
        *) echo ":$1" ;;
    esac
}

case "${HTTPS_DI_VM:-0}" in
    0|"")
        echo "include $T/lokasi-situs.conf;" > "$P/port-80.conf"
        echo "include $T/lokasi-admin.conf;" > "$P/port-8081.conf"
        echo "45-prodi-https: HTTP; HTTPS diakhiri di depan stack (load balancer)"
        ;;
    1)
        for f in fullchain.pem privkey.pem; do
            if [ ! -s "/etc/nginx/tls/$f" ]; then
                echo "45-prodi-https: HTTPS_DI_VM=1 tetapi $f tidak ada di TLS_FOLDER (lihat docs/deploy.md)" >&2
                exit 1
            fi
            # read for real: with its capabilities limited (docker-compose.yml) root here reads only what its owner
            # may, while "test -r" still says yes
            if ! head -c 1 "/etc/nginx/tls/$f" > /dev/null 2>&1; then
                echo "45-prodi-https: $f di TLS_FOLDER tidak bisa dibaca; berkas sertifikat harus milik root (docs/deploy.md §7B)" >&2
                exit 1
            fi
        done
        situs="$(akhiran_port "${PORT_SITUS_HTTPS:-443}")"
        admin="$(akhiran_port "${PORT_ADMIN_HTTPS:-8444}")"
        echo "location / { return 301 https://\$host$situs\$request_uri; }" > "$P/port-80.conf"
        {
            echo "include $P/admin-ip.conf;"
            echo "location / { return 301 https://\$host$admin\$request_uri; }"
        } > "$P/port-8081.conf"
        cat > /etc/nginx/conf.d/https.conf <<EOF
# Ditulis oleh 45-prodi-https.sh (HTTPS_DI_VM=1).
server {
    listen 443 ssl;
    http2 on;
    server_name _;
    include $T/tls.conf;
    include $T/lokasi-situs.conf;
}
server {
    listen 8443 ssl;
    http2 on;
    server_name _;
    include $T/tls.conf;
    include $T/lokasi-admin.conf;
}
EOF
        echo "45-prodi-https: HTTPS di VM; situs di port 443 kontainer, admin di 8443"
        ;;
    *)
        echo "45-prodi-https: HTTPS_DI_VM harus 0 atau 1" >&2
        exit 1
        ;;
esac
