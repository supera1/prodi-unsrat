# -*- coding: utf-8 -*-
"""Modules copied from the www repository still match the SHA-256 recorded in docs/asal-modul.md.

A mismatch means a copy was changed without updating the table (or the table was not updated after porting a fix
from www). When the www repository sits next to this one, it also reports copies whose source has since changed.
"""
from __future__ import print_function

import hashlib
import io
import os
import re
import sys

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WWW = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026")
BARIS = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([0-9a-f]{12})` \|")


def sidik(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


gagal, dicek = [], 0
with io.open(os.path.join(AKAR, "docs", "asal-modul.md"), encoding="utf-8") as f:
    for teks in f:
        m = BARIS.match(teks)
        if not m:
            continue
        di_sini, asal, tercatat = m.groups()
        dicek += 1
        path = os.path.join(AKAR, di_sini)
        if not os.path.isfile(path):
            gagal.append("%s tidak ada" % di_sini)
            continue
        if sidik(path) != tercatat:
            gagal.append("%s berubah (%s, tercatat %s): perbarui docs/asal-modul.md" % (di_sini, sidik(path), tercatat))
        path_asal = os.path.join(WWW, asal)
        if os.path.isfile(path_asal) and sidik(path_asal) != tercatat:
            print("PERHATIAN %s di www sudah berubah sejak disalin: tinjau apakah perlu diterapkan di sini" % asal)

if dicek == 0:
    gagal.append("tabel di docs/asal-modul.md tidak terbaca")
for g in gagal:
    print("GAGAL", g)
print("uji_asal_modul: %d modul, %s" % (dicek, "LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
