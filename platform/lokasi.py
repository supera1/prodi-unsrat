# -*- coding: utf-8 -*-
"""Where the platform keeps its data, and safe reading and writing of the JSON data files.

    PRODI_DATA      the platform's own data (default: <repo>/data; in Docker the volume prodi-data)
    PRODI_RIWAYAT   version history of every data file (default: <PRODI_DATA>/../riwayat)
    WWW_DATA        the data folder of www.unsrat.ac.id, read only (default: the sibling checkout
                    ../website-unsrat-2026/site/mockup/data; in Docker the www data volume mounted read-only)
    PRODI_PUBLIK    the built site, the only folder the web server serves (default: <repo>/publik)
    PRODI_MANIFES   SHA-256 of every published file, for the integrity check (default: <repo>/manifes-publik.json)
    PRODI_NGINX     configuration the builder writes for Nginx, e.g. redirects of old slugs (default: <repo>/nginx-buatan)
    PRODI_UNGGAHAN  uploaded photos and PDFs when PRODI_PENYIMPANAN=lokal (default: <repo>/unggahan); the builder
                    publishes them under publik/unggahan/. With PRODI_PENYIMPANAN=gcs they go to Google Cloud Storage.

Layout of PRODI_DATA (docs/rencana-fase-01.md §4):

    registri.json                 programmes on the platform: PDDIKTI code, slug, old slugs, active, lecturer link
    warisan/prodi.json            official programme data copied from www (tarik_www.py), never edited here
    warisan/unit.json             faculties: names and flag colours
    warisan/kalender.json         academic calendar
    warisan/universitas.json      UNSRAT's name, address, phone numbers, social media and utility links
    warisan/meta.json             when the copy was taken and from where
    prodi/<kode>/situs.json       per programme: tagline, palette, logo, social media, menu settings
    prodi/<kode>/pengumuman.json  per programme: announcements and news (pengumuman.py)
"""
from __future__ import print_function

import io
import json
import os
import re

PLATFORM = os.path.dirname(os.path.abspath(__file__))
AKAR = os.path.dirname(PLATFORM)

# A data file is named by its path under PRODI_DATA without ".json": "registri", "warisan/prodi",
# "prodi/55201/situs". Only these shapes are accepted, so a name can never point outside the data folder.
NAMA_SAH = re.compile(r"^(registri|warisan/(prodi|unit|kalender|universitas|meta)|prodi/[0-9A-Za-z]{3,12}/[a-z][a-z0-9-]*)$")


def data():
    return os.path.abspath(os.environ.get("PRODI_DATA") or os.path.join(AKAR, "data"))


def riwayat():
    return os.path.abspath(os.environ.get("PRODI_RIWAYAT") or os.path.join(os.path.dirname(data()), "riwayat"))


def www_data():
    bawaan = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026", "site", "mockup", "data")
    return os.path.abspath(os.environ.get("WWW_DATA") or bawaan)


def publik():
    return os.path.abspath(os.environ.get("PRODI_PUBLIK") or os.path.join(AKAR, "publik"))


def manifes():
    return os.path.abspath(os.environ.get("PRODI_MANIFES") or os.path.join(AKAR, "manifes-publik.json"))


def nginx_buatan():
    return os.path.abspath(os.environ.get("PRODI_NGINX") or os.path.join(AKAR, "nginx-buatan"))


def unggahan():
    return os.path.abspath(os.environ.get("PRODI_UNGGAHAN") or os.path.join(AKAR, "unggahan"))


def path_data(berkas):
    """"warisan/prodi" -> absolute path of the data file. ValueError for any other shape of name."""
    if not NAMA_SAH.match(berkas or ""):
        raise ValueError("nama berkas data tidak sah: %r" % (berkas,))
    return os.path.join(data(), *berkas.split("/")) + ".json"


def baca(berkas, bawaan=None):
    """Content of a data file, or `bawaan` when it does not exist yet."""
    path = path_data(berkas)
    if not os.path.isfile(path):
        return bawaan
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def tulis_json(path, isi):
    """Write JSON atomically: a reader sees the old file or the new one, never half of it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(isi, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def tulis(berkas, isi, oleh, bagian, aksi):
    """Write a data file, keeping the previous content in the version history first."""
    import riwayat as riwayat_mod  # riwayat.py imports this module, so it is imported only when writing
    riwayat_mod.simpan_versi(berkas, oleh, bagian, aksi)
    tulis_json(path_data(berkas), isi)
