# -*- coding: utf-8 -*-
"""Run every test suite in uji/ (files named uji_*.py), each in its own Python process.

    python3 uji/jalankan-semua.py

Every suite gets its own temporary folder for every location of platform/lokasi.py, and none of the settings of a
running stack (PRODI_*, WWW_DATA, the admin's): a suite run inside the admin container (Dockerfile, docs/deploy.md)
can never reach the volumes, and a suite that forgets to set a folder of its own still writes nowhere that matters.

Exit status 1 when any suite fails.
"""
from __future__ import print_function

import glob
import os
import subprocess
import sys
import tempfile

UJI = os.path.dirname(os.path.abspath(__file__))
LOKASI = ("PRODI_DATA", "PRODI_RIWAYAT", "PRODI_PUBLIK", "PRODI_NGINX", "PRODI_RAHASIA", "PRODI_LOG", "PRODI_UNGGAHAN",
          "WWW_DATA")
PENGATURAN_STACK = ("ADMIN_IP_BOLEH", "ADMIN_HTTPS", "ADMIN_AWALAN", "PROXY_TERPERCAYA", "PORT")

hasil = []
for path in sorted(glob.glob(os.path.join(UJI, "uji_*.py"))):
    nama = os.path.basename(path)
    print("=== %s" % nama, flush=True)
    with tempfile.TemporaryDirectory(prefix="prodi-uji-") as kerja:
        env = {k: v for k, v in os.environ.items() if not k.startswith("PRODI_") and k not in PENGATURAN_STACK + LOKASI}
        env.update({k: os.path.join(kerja, k.lower()) for k in LOKASI})
        env["PRODI_MANIFES"] = os.path.join(kerja, "manifes-publik.json")
        kode = subprocess.call([sys.executable, path], cwd=os.path.dirname(UJI), env=env)
    hasil.append((nama, kode))

print()
for nama, kode in hasil:
    print("%-28s %s" % (nama, "LULUS" if kode == 0 else "GAGAL"))
gagal = [n for n, k in hasil if k != 0]
print("%d rangkaian, %d gagal" % (len(hasil), len(gagal)))
sys.exit(1 if gagal else 0)
