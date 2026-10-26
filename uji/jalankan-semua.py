# -*- coding: utf-8 -*-
"""Run every test suite in uji/ (files named uji_*.py), each in its own Python process.

    python3 uji/jalankan-semua.py

Exit status 1 when any suite fails.
"""
from __future__ import print_function

import glob
import os
import subprocess
import sys

UJI = os.path.dirname(os.path.abspath(__file__))

hasil = []
for path in sorted(glob.glob(os.path.join(UJI, "uji_*.py"))):
    nama = os.path.basename(path)
    print("=== %s" % nama, flush=True)
    kode = subprocess.call([sys.executable, path], cwd=os.path.dirname(UJI))
    hasil.append((nama, kode))

print()
for nama, kode in hasil:
    print("%-28s %s" % (nama, "LULUS" if kode == 0 else "GAGAL"))
gagal = [n for n, k in hasil if k != 0]
print("%d rangkaian, %d gagal" % (len(hasil), len(gagal)))
sys.exit(1 if gagal else 0)
