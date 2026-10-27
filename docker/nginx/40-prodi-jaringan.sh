#!/bin/sh
# Run by the Nginx image before Nginx starts (/docker-entrypoint.d). Writes three files from the stack's variables
# (adapted from www's docker/nginx/40-unsrat-jaringan.sh, docs/asal-modul.md):
#   /etc/nginx/prodi/admin-ip.conf      allow <each network of ADMIN_IP_BOLEH>; deny all;   (the admin)
#   /etc/nginx/prodi/real-ip.conf       the visitor's address from X-Forwarded-For, trusted only from PROKSI_DEPAN
#   /etc/nginx/prodi/admin-awalan.conf  X-Forwarded-Prefix from ADMIN_AWALAN, e.g. /admin when the admin is opened under
#                                       a path of a shared address
# The networks are comma-separated, e.g. 103.84.116.0/24 or 130.211.0.0/22,35.191.0.0/16.
set -euf                  # -f: no file-name expansion of the values below
mkdir -p /etc/nginx/prodi

ADMIN_IP="${ADMIN_IP_BOLEH:-103.84.116.0/24}"
PROKSI="${PROKSI_DEPAN:-}"

jaringan() {  # the networks of a list (separated by commas, spaces or tabs), one per line
    printf '%s\n' "$1" | tr ', \t' '\n\n\n' | grep -v '^$' || true
}

salah() {
    echo "40-prodi-jaringan: $*" >&2
    exit 1
}

# Anything that is not an address or network, a network that is too wide, or a wrong ADMIN_AWALAN stops the start
# before any file is written. Checked here, in the script itself: an "exit" inside $(...) would only leave that
# subshell (www's 40-unsrat-jaringan.sh has that flaw: there a wrong value silently leaves the admin closed to
# everybody, or a list of networks cut short).
# periksa <name> <value> <shortest IPv4 prefix> <shortest IPv6 prefix>: ADMIN_IP_BOLEH=0.0.0.0/0 would open the admin
# to the whole internet (the admin, app.py, refuses the same), and a wide PROKSI_DEPAN would let anybody in it name
# their own address in X-Forwarded-For, e.g. one of ADMIN_IP_BOLEH.
periksa() {
    for n in $(jaringan "$2"); do
        case "$n" in
            *[!0-9a-fA-F:./]*|*/*/*|*/|/*) salah "$1 berisi '$n', bukan alamat jaringan" ;;
            */*) pjg="${n##*/}" ;;
            *) continue ;;                                  # one address
        esac
        case "$n" in
            *:*) min=$4 maks=128 ;;
            *) min=$3 maks=32 ;;
        esac
        case "$pjg" in *[!0-9]*|????*) salah "$1 berisi '$n', bukan alamat jaringan" ;; esac
        [ "$pjg" -le "$maks" ] || salah "$1 berisi '$n', bukan alamat jaringan"
        [ "$pjg" -ge "$min" ] || salah "$1 berisi '$n', jaringan yang terlalu luas (paling luas /$3 untuk IPv4, /$4 untuk IPv6)"
    done
}
periksa ADMIN_IP_BOLEH "$ADMIN_IP" 8 32
periksa PROKSI_DEPAN "$PROKSI" 16 48
[ -n "$(jaringan "$ADMIN_IP")" ] || salah "ADMIN_IP_BOLEH tidak berisi jaringan"
awalan="${ADMIN_AWALAN:-}"
awalan="${awalan%/}"
case "$awalan" in
    "") ;;
    /*) case "$awalan" in *[!A-Za-z0-9/._-]*|*//*) salah "ADMIN_AWALAN '$awalan' tidak sah" ;; esac ;;
    *) salah "ADMIN_AWALAN harus diawali / (mis. /admin)" ;;
esac

{
    for n in $(jaringan "$ADMIN_IP"); do echo "allow $n;"; done
    echo "deny all;"
} > /etc/nginx/prodi/admin-ip.conf

: > /etc/nginx/prodi/real-ip.conf
if [ -n "$(jaringan "$PROKSI")" ]; then
    {
        for n in $(jaringan "$PROKSI"); do echo "set_real_ip_from $n;"; done
        echo "real_ip_header X-Forwarded-For;"
        echo "real_ip_recursive on;"
    } > /etc/nginx/prodi/real-ip.conf
fi

# The header is always set (empty = not sent), so a visitor can never send one of their own.
echo "proxy_set_header X-Forwarded-Prefix \"$awalan\";" > /etc/nginx/prodi/admin-awalan.conf

echo "40-prodi-jaringan: admin untuk $ADMIN_IP; proksi depan: ${PROKSI:-tidak ada}; awalan admin: ${awalan:-tidak ada}"
