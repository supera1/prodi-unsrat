# -*- coding: utf-8 -*-
"""Prepare the admin: the session key, and the first superadmin (langkah 4).

    python3 platform/admin/siapkan.py                                          <PRODI_RAHASIA>/.env with a new SECRET_KEY
    .venv/bin/python platform/admin/siapkan.py --superadmin nama --nama-lengkap "Nama Lengkap"
    .venv/bin/python platform/admin/siapkan.py --daftar                         list the accounts (no passwords)

A temporary password is written once to <PRODI_RAHASIA>/.kredensial-<nama>.txt (readable by the owner only), never to
the console or to Git. Read it, log in, set your own password (the admin asks for it), then delete the file.
Further accounts are made in the admin itself (Akun), by the superadmin or, for operators, by a programme admin.
"""
from __future__ import print_function

import argparse
import io
import os
import secrets
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))

import lokasi  # noqa: E402

# networks that may open the admin. On a developer's machine also the machine itself; a server lists only UNSRAT's
# network (set ADMIN_IP_BOLEH in the stack, which wins over this file).
BAWAAN = [("ADMIN_IP_BOLEH", "103.84.116.0/24,127.0.0.1/32,::1/128"), ("PORT", "8791"),
          ("PRODI_ALAMAT_PUBLIK", "http://127.0.0.1:8790")]


def siapkan_env():
    path = os.path.join(lokasi.rahasia(), ".env")
    os.makedirs(lokasi.rahasia(), exist_ok=True)
    if os.path.isfile(path):
        print("%s sudah ada; tidak diubah." % path)
        return path
    baris = ["# Admin prodi.unsrat.ac.id. Rahasia: jangan disalin ke Git atau ke tempat lain.",
             "SECRET_KEY=%s" % secrets.token_hex(32)] + ["%s=%s" % kv for kv in BAWAAN]
    with io.open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as f:
        f.write("\n".join(baris) + "\n")
    print("Dibuat: %s" % path)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description="Siapkan admin prodi")
    ap.add_argument("--superadmin", metavar="NAMA", help="buat akun superadmin dengan nama pengguna ini")
    ap.add_argument("--nama-lengkap", default="", help="nama lengkap pemilik akun superadmin")
    ap.add_argument("--daftar", action="store_true", help="daftar akun")
    a = ap.parse_args(argv)
    siapkan_env()
    if a.superadmin or a.daftar:
        import akun
        if a.superadmin:
            try:
                id_, sandi = akun.buat(None, a.superadmin, a.nama_lengkap or a.superadmin, "super")
            except akun.GagalAkun as e:
                print("GAGAL: %s" % e)
                return 1
            path = os.path.join(lokasi.rahasia(), ".kredensial-%s.txt" % a.superadmin.strip().lower())
            with io.open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as f:
                f.write("Nama pengguna: %s\nKata sandi sementara: %s\n"
                        "Masuk ke admin, buat kata sandi sendiri, lalu hapus berkas ini.\n" % (a.superadmin, sandi))
            import audit
            audit.catat("akun-dibuat", oleh="baris-perintah", akun=a.superadmin, peran="super")
            print("Superadmin %s dibuat. Kata sandi sementara ada di %s" % (a.superadmin, path))
        if a.daftar:
            for x in akun.semua():
                print("%-20s %-9s %-8s %s" % (x["nama"], x["peran"], "aktif" if x["aktif"] else "nonaktif",
                                              ",".join(x["prodi"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
