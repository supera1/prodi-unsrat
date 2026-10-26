#!/bin/sh
# The pemantau container (same image as the admin): every PEMANTAU_JEDA seconds (default 10 minutes) compare the
# published sites with the manifest of the last build (platform/pemantau/cek_integritas.py): pages changed, files
# planted or gone, gambling text, scripts from elsewhere. A finding is checked again a minute later, so the moment of a
# rebuild (pages written, manifest not yet) is not reported; what is still there then is reported loudly.
set -u

periksa() {
    python /app/platform/pemantau/cek_integritas.py --folder "$PRODI_PUBLIK" --manifes "$PRODI_MANIFES" 2>&1
}

sleep "${PEMANTAU_TUNDA:-300}"                       # the admin builds the sites first
while true; do
    if hasil="$(periksa)"; then
        echo "$(date '+%F %T') $(echo "$hasil" | tail -n 1)"
    else
        sleep 60
        if hasil="$(periksa)"; then
            echo "$(date '+%F %T') $(echo "$hasil" | tail -n 1) (temuan sesaat sebelumnya: bangun ulang sedang berjalan)"
        else
            echo "$hasil"
            echo "$(date '+%F %T') PEMANTAU: ADA TEMUAN di situs publik; periksa baris di atas (docs/deploy.md, bila ada temuan)"
        fi
    fi
    sleep "${PEMANTAU_JEDA:-600}"
done
