# -*- coding: utf-8 -*-
"""Programme slugs: the short address of every programme site (prodi.unsrat.ac.id/<slug>/).

Slugs are set by the superadmin (K-P1); the approved starting list is data-awal/slug.csv (K-P8). A programme is
identified by its PDDIKTI code, never by its slug, so a slug can change without moving any data.
"""
from __future__ import print_function

import csv
import io
import os
import re

PLATFORM = os.path.dirname(os.path.abspath(__file__))
CSV_AWAL = os.path.join(PLATFORM, "data-awal", "slug.csv")

POLA_SLUG = re.compile(r"^[a-z][a-z0-9]{2,23}$")

# First path segments the platform itself uses (or will use): a programme may never take one of these.
ALAMAT_CADANGAN = frozenset([
    "404", "admin", "api", "aset", "assets", "cari", "data", "en", "id", "masuk", "robots", "search", "sehat",
    "sitemap", "static", "unggahan", "zz",
])

# Every slug starts with its level, so a visitor can tell S1 from S2 of the same field at a glance.
AWALAN_JENJANG = {"S1": "s1", "S2": "s2", "S3": "s3", "Profesi": "profesi", "Sp-1": "sp1", "Sp-2": "sp2"}

KOLOM = ("kode_pddikti", "jenjang", "nama", "fakultas_unit", "slug_usulan", "alamat_usulan", "slug_di_www")

# words left out of a suggested slug, as in the approved list (K-P8): "S1 Teknik Informatika" -> s1informatika
KATA_DIBUANG = frozenset(["ilmu", "teknik", "dan", "profesi", "program", "studi"])


def usulan(jenjang, nama):
    """A suggested slug for a programme new in www; the superadmin may change it before registering (K-P1)."""
    kata = [k for k in re.findall(r"[a-z0-9]+", (nama or "").lower()) if k not in KATA_DIBUANG]
    return (AWALAN_JENJANG.get(jenjang, "") + "".join(kata))[:24]


def periksa_slug(slug, jenjang=None):
    """Return a list of problems with one slug (empty when it is valid)."""
    masalah = []
    if not POLA_SLUG.match(slug or ""):
        masalah.append("hanya huruf kecil dan angka, diawali huruf, 3-24 karakter")
    if slug in ALAMAT_CADANGAN:
        masalah.append("alamat ini dipakai sistem")
    awalan = AWALAN_JENJANG.get(jenjang)
    if jenjang is not None and (awalan is None or not (slug or "").startswith(awalan)):
        masalah.append("harus diawali jenjang (%s)" % (awalan or "jenjang tidak dikenal"))
    return masalah


def baca_csv(path=CSV_AWAL):
    """Rows of the slug list as dicts, in file order."""
    with io.open(path, encoding="utf-8", newline="") as f:
        pembaca = csv.DictReader(f)
        if tuple(pembaca.fieldnames or ()) != KOLOM:
            raise ValueError("kolom %s tidak sesuai, harus %s" % (pembaca.fieldnames, ", ".join(KOLOM)))
        return list(pembaca)


def periksa_daftar(baris):
    """Problems in a whole list: invalid slugs, duplicate slugs or codes. Returns [(kode_pddikti, message), ...]."""
    masalah = []
    slug_dipakai, kode_dipakai = {}, set()
    for b in baris:
        kode, slug = b["kode_pddikti"], b["slug_usulan"]
        if kode in kode_dipakai:
            masalah.append((kode, "kode PDDIKTI ganda"))
        kode_dipakai.add(kode)
        for m in periksa_slug(slug, b["jenjang"]):
            masalah.append((kode, "%s: %s" % (slug, m)))
        if slug in slug_dipakai:
            masalah.append((kode, "%s sudah dipakai %s" % (slug, slug_dipakai[slug])))
        slug_dipakai.setdefault(slug, kode)
    return masalah
