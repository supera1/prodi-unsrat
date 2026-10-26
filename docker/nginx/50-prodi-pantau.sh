#!/bin/sh
# Run by the Nginx image before Nginx starts (/docker-entrypoint.d).
#
# The builder (admin container) writes the redirects of old programme slugs to /srv/nginx-buatan/slug-lama.conf
# (volume prodi-nginx, read only here). Nginx never includes that file itself: only lines of the one shape the builder
# writes are copied to /etc/nginx/prodi/slug-lama.conf, so whoever controls the admin container cannot hand Nginx any
# other directive (a path to the TLS key, a proxy, ...).
#
# A loop in the background repeats the copy every 30 seconds and reloads Nginx when the redirects changed (after
# "nginx -t"; on failure the previous file stays), and when the TLS certificate was renewed (HTTPS_DI_VM=1).
set -eu
SUMBER=/srv/nginx-buatan/slug-lama.conf
HASIL=/etc/nginx/prodi/slug-lama.conf
POLA='^rewrite \^/[a-z][a-z0-9]{2,23}\(/\.\*\)\?\$ /[a-z][a-z0-9]{2,23}\$1 permanent;$'

saring() {
    echo "# Disalin dari $SUMBER oleh 50-prodi-pantau.sh: hanya baris pengalihan slug yang sah."
    if [ -f "$SUMBER" ]; then grep -E "$POLA" "$SUMBER" || true; fi
}

sidik_tls() {
    cat /etc/nginx/tls/fullchain.pem /etc/nginx/tls/privkey.pem 2>/dev/null | md5sum
}

mkdir -p /etc/nginx/prodi
saring > "$HASIL"
echo "50-prodi-pantau: $(grep -c '^rewrite' "$HASIL" || true) pengalihan slug lama"

(
    set +e
    tls_lama="$(sidik_tls)"
    while sleep 30; do
        baru="$(saring)"
        if [ "$baru" != "$(cat "$HASIL")" ]; then
            cp "$HASIL" "$HASIL.lama"
            printf '%s\n' "$baru" > "$HASIL"
            if nginx -t -q; then
                nginx -s reload && echo "50-prodi-pantau: pengalihan slug lama diperbarui ($(grep -c '^rewrite' "$HASIL") baris); Nginx dimuat ulang"
            else
                mv "$HASIL.lama" "$HASIL"
                echo "50-prodi-pantau: pengalihan slug baru ditolak nginx -t; yang lama tetap dipakai" >&2
            fi
        fi
        if [ "${HTTPS_DI_VM:-0}" = "1" ]; then
            tls_baru="$(sidik_tls)"
            if [ "$tls_baru" != "$tls_lama" ] && nginx -t -q; then
                nginx -s reload && echo "50-prodi-pantau: sertifikat TLS diperbarui; Nginx dimuat ulang"
                tls_lama="$tls_baru"
            fi
        fi
    done
) < /dev/null &
