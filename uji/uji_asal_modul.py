# -*- coding: utf-8 -*-
"""Modules copied from the www repository against the SHA-256 recorded in docs/asal-modul.md.

Section "Salinan utuh": the copy must still match (a mismatch means it was changed without updating the table).
Section "Diadaptasi": the copy was changed on purpose; only the source is watched.
When the www repository sits next to this one, every source whose content has changed since it was copied is
reported, so security fixes made in www are not missed here. Inside the admin image (Dockerfile) only platform/ and
uji/ are there: the files of the stack itself (Dockerfile, docker/, docs/) are what the image was built from.
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
DI_IMAGE = not os.path.isfile(os.path.join(AKAR, "docker-compose.yml"))


def sidik(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


gagal, dicek, bagian = [], 0, None
with io.open(os.path.join(AKAR, "docs", "asal-modul.md"), encoding="utf-8") as f:
    for teks in f:
        if teks.startswith("## "):
            bagian = teks[3:].strip()
            continue
        m = BARIS.match(teks)
        if not m:
            continue
        di_sini, asal, tercatat = m.groups()
        dicek += 1
        path = os.path.join(AKAR, di_sini)
        if not os.path.isfile(path):
            if DI_IMAGE and not di_sini.startswith(("platform/", "uji/")):
                continue
            gagal.append("%s tidak ada" % di_sini)
            continue
        if bagian == "Salinan utuh" and sidik(path) != tercatat:
            gagal.append("%s berubah (%s, tercatat %s): perbarui docs/asal-modul.md" % (di_sini, sidik(path), tercatat))
        path_asal = os.path.join(WWW, asal)
        if os.path.isfile(path_asal) and sidik(path_asal) != tercatat:
            print("PERHATIAN %s di www sudah berubah sejak disalin: tinjau apakah perlu diterapkan di sini" % asal)

if dicek == 0 or bagian is None:
    gagal.append("tabel di docs/asal-modul.md tidak terbaca")
for g in gagal:
    print("GAGAL", g)
print("uji_asal_modul: %d modul, %s" % (dicek, "LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
