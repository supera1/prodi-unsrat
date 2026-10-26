# -*- coding: utf-8 -*-
"""Version history of the data files.

Before a data file is overwritten, its current content is copied to
<PRODI_RIWAYAT>/<file>/<timestamp>.json and a line is added to <PRODI_RIWAYAT>/indeks.jsonl
(when, who, which section, what kind of change). Any version can be restored; restoring is
itself recorded, so nothing is lost.

Copied from the www admin (site/admin/riwayat.py, commit 37b5e6d); the folders and the allowed file names now
come from lokasi.py ("prodi/<kode>/situs" becomes the history folder "prodi__<kode>__situs").
"""
from __future__ import print_function

import datetime
import io
import json
import os
import re
import shutil

import lokasi
from lokasi import NAMA_SAH, path_data


def _riwayat():
    # read at every call, so PRODI_RIWAYAT set by a test or the container applies
    return lokasi.riwayat()


def _indeks():
    return os.path.join(_riwayat(), "indeks.jsonl")


def simpan_versi(berkas, oleh, bagian, aksi):
    """Keep a copy of the current file before it changes. Returns the version id (or None)."""
    sumber = path_data(berkas)
    if not os.path.isfile(sumber):
        return None
    waktu = datetime.datetime.now()
    versi = waktu.strftime("%Y%m%d-%H%M%S-%f")
    folder = os.path.join(_riwayat(), berkas.replace("/", "__"))
    os.makedirs(folder, exist_ok=True)
    shutil.copy2(sumber, os.path.join(folder, versi + ".json"))
    with io.open(_indeks(), "a", encoding="utf-8") as f:
        f.write(json.dumps({"versi": versi, "berkas": berkas, "waktu": waktu.isoformat(timespec="seconds"),
                            "oleh": oleh, "bagian": bagian, "aksi": aksi}, ensure_ascii=False) + "\n")
    return versi


def daftar(batas=200):
    """Newest first."""
    if not os.path.isfile(_indeks()):
        return []
    with io.open(_indeks(), encoding="utf-8") as f:
        baris = [json.loads(x) for x in f if x.strip()]
    return list(reversed(baris))[:batas]


def baca_versi(berkas, versi):
    # both names are checked before any path is built, so nothing outside riwayat/ is ever looked at
    if not re.match(r"^\d{8}-\d{6}-\d{6}$", versi) or not NAMA_SAH.match(berkas):
        raise ValueError("versi tidak sah")
    path = os.path.join(_riwayat(), berkas.replace("/", "__"), versi + ".json")
    if not os.path.isfile(path):
        raise ValueError("versi tidak ditemukan")
    return path


def pulihkan(berkas, versi, oleh, bagian):
    """Put an old version back (the current one is kept as a new history entry first)."""
    asal = baca_versi(berkas, versi)
    simpan_versi(berkas, oleh, bagian, "sebelum pemulihan versi %s" % versi)
    tujuan = path_data(berkas)
    tmp = tujuan + ".tmp"
    shutil.copy2(asal, tmp)
    os.replace(tmp, tujuan)
