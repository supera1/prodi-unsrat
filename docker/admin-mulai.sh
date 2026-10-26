#!/bin/sh
# Start of the admin container (Dockerfile): the session key; on a new VM the starting copy of www's data and the
# registry of the approved slugs; a build of every programme site into the volume "publik" (served by the web
# container); then the admin with waitress. Guide: docs/deploy.md
set -eu
cd /app
mkdir -p "$PRODI_DATA" "$PRODI_RIWAYAT" "$PRODI_LOG" "$PRODI_UNGGAHAN"

python platform/admin/siapkan.py                  # <PRODI_RAHASIA>/.env with the session key: made once, then kept
if ! python platform/impor_www.py --isi-awal; then
    echo "PERINGATAN: data awal tidak diterapkan (lihat di atas). Unggah data www di admin, halaman Data www."
fi

echo "Membangun semua situs (mode ${PRODI_MODE:-staging})..."
if ! python platform/bangun/bangun.py; then
    # the web container keeps serving what was built last; the admin still starts so the data can be put right
    echo "PERINGATAN: bangun ulang gagal; situs tetap menyajikan hasil bangun terakhir. Periksa log di atas."
fi

if ! python platform/admin/siapkan.py --ada-superadmin > /dev/null; then
    echo "Belum ada akun superadmin. Di VM, dari folder repositori (mis. /opt/prodi-unsrat), jalankan:"
    echo "  sudo docker compose exec admin python platform/admin/siapkan.py --superadmin <nama> --nama-lengkap \"Nama Lengkap\""
    echo "Admin tetap berjalan; halaman masuknya menunggu akun itu (docs/deploy.md)."
fi

cd /app/platform/admin
# --no-clear-untrusted-proxy-headers: waitress 3 drops X-Forwarded-For/-Proto/-Prefix by default, before the app's
# ProxyFix (PROXY_TERPERCAYA=1) reads them; the admin would then see the web container's address and refuse everyone
# with 403. Only the web container (Nginx) reaches this port, and it always overwrites those headers.
exec waitress-serve --listen="0.0.0.0:${PORT:-8791}" --threads=8 --ident=prodi-admin \
    --no-clear-untrusted-proxy-headers --call app:buat_app
