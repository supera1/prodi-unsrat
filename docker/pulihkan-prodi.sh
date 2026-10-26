#!/bin/sh
# Restore the stack's data on the VM from the copies of cadangan-prodi.sh (docs/deploy.md §9):
#   sudo /usr/local/sbin/pulihkan-prodi 2026-11-01
# Replaces the whole content of the volumes prodi-data and prodi-rahasia with the copies of that date. Everything
# written after the copy is lost, so the script asks first (YAKIN=1 skips the question). The three containers are
# stopped meanwhile and started again; the admin rebuilds every site at its start.
#   STACK, TUJUAN: as in cadangan-prodi.sh
set -eu
STACK="${STACK:-prodi-unsrat}"
TUJUAN="${TUJUAN:-/srv/cadangan-prodi}"
GAMBAR="prodi-unsrat-web:latest"
TANGGAL="${1:-}"

case "$TANGGAL" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
    *) echo "Pakai: pulihkan-prodi YYYY-MM-DD   (cadangan yang ada:)" >&2
       ls "$TUJUAN" | sed -n 's/^prodi-data-\(.*\)\.tgz$/  \1/p' >&2
       exit 1 ;;
esac
for v in prodi-data prodi-rahasia; do
    if [ ! -s "$TUJUAN/${v}-${TANGGAL}.tgz" ]; then
        echo "Tidak ada $TUJUAN/${v}-${TANGGAL}.tgz" >&2
        exit 1
    fi
done
if [ "${YAKIN:-0}" != "1" ]; then
    printf "Isi volume %s_prodi-data dan %s_prodi-rahasia diganti dengan cadangan %s. Ketik PULIHKAN untuk lanjut: " \
        "$STACK" "$STACK" "$TANGGAL"
    read -r jawab
    [ "$jawab" = "PULIHKAN" ] || { echo "Dibatalkan."; exit 1; }
fi

KONTAINER="${STACK}-pemantau-1 ${STACK}-web-1 ${STACK}-admin-1"
# shellcheck disable=SC2086
docker stop $KONTAINER > /dev/null
trap 'docker start '"$KONTAINER"' > /dev/null' EXIT
for v in prodi-data prodi-rahasia; do
    # the archive is checked whole before anything in the volume is removed
    docker run --rm -v "${STACK}_${v}:/data" -v "$TUJUAN:/cadangan:ro" "$GAMBAR" sh -c \
        "tar tzf /cadangan/${v}-${TANGGAL}.tgz > /dev/null && find /data -mindepth 1 -delete && tar xzf /cadangan/${v}-${TANGGAL}.tgz -C /data"
    echo "$v dipulihkan dari cadangan $TANGGAL"
done
