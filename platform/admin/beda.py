# -*- coding: utf-8 -*-
"""Comparing a stored version of a data file with what it holds now (the Riwayat pages of the superadmin and of a
programme's admin)."""
from __future__ import print_function

import difflib
import io
import json
import os
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))

import lokasi  # noqa: E402
import riwayat  # noqa: E402

MAKS_BARIS = 600


def beda_versi(berkas, versi):
    """{"beda": unified diff lines (version first), "terpotong": bool, "catatan": its history entry or None}.
    ValueError for a file name or version riwayat does not accept (so nothing outside the history is read)."""
    path = riwayat.baca_versi(berkas, versi)
    with io.open(path, encoding="utf-8") as f:
        lama = json.load(f)
    kini = lokasi.baca(berkas)
    # 4 lines of context: enough to show which programme or item a change belongs to
    beda = list(difflib.unified_diff(json.dumps(lama, ensure_ascii=False, indent=1).splitlines(),
                                     json.dumps(kini, ensure_ascii=False, indent=1).splitlines() if kini is not None else [],
                                     "versi %s" % versi, "sekarang", n=4, lineterm=""))
    catatan = [v for v in riwayat.daftar(5000) if v["berkas"] == berkas and v["versi"] == versi]
    return {"beda": beda[:MAKS_BARIS], "terpotong": len(beda) > MAKS_BARIS, "catatan": catatan[0] if catatan else None}
