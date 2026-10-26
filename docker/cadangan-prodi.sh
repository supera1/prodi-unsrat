#!/bin/sh
# Daily backup of the stack's data on the VM (docs/deploy.md §9), run by cron on the VM itself, e.g.
#   30 1 * * *  root  /usr/local/sbin/cadangan-prodi >> /var/log/cadangan-prodi.log 2>&1
#
# Copies the volumes prodi-data (data, history, audit log, uploads) and prodi-rahasia (accounts, session key) to
# TUJUAN as <volume>-<date>.tgz and removes copies older than SIMPAN_HARI days. The admin container is stopped for the
# few seconds of the copy, so the account database and the data files are copied at rest; the sites stay online (the
# web container serves them) and the admin comes back by itself, also when the copy fails. Copy TUJUAN off the VM too.
#
#   STACK        stack name, the prefix of the volume and container names (default prodi-unsrat)
#   TUJUAN       folder for the copies (default /srv/cadangan-prodi)
#   SIMPAN_HARI  days to keep (default 14)
set -eu
STACK="${STACK:-prodi-unsrat}"
TUJUAN="${TUJUAN:-/srv/cadangan-prodi}"
SIMPAN_HARI="${SIMPAN_HARI:-14}"
GAMBAR="prodi-unsrat-web:latest"          # the stack's own Alpine image: tar and gzip, nothing to download
TANGGAL="$(date +%F)"

mkdir -p "$TUJUAN"
chmod 0700 "$TUJUAN"
trap 'docker start "${STACK}-admin-1" > /dev/null' EXIT
docker stop "${STACK}-admin-1" > /dev/null
for v in prodi-data prodi-rahasia; do
    # readable by root only: the copy of prodi-rahasia holds the password hashes
    docker run --rm -v "${STACK}_${v}:/data:ro" -v "$TUJUAN:/cadangan" "$GAMBAR" \
        sh -c "umask 077 && tar czf /cadangan/${v}-${TANGGAL}.tgz -C /data ."
done
find "$TUJUAN" -name 'prodi-*.tgz' -mtime "+$SIMPAN_HARI" -delete
echo "$(date '+%F %T') cadangan prodi: $(ls "$TUJUAN"/*-"$TANGGAL".tgz | tr '\n' ' ')"
