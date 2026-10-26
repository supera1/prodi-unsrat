# -*- coding: utf-8 -*-
"""The approved slug list (platform/data-awal/slug.csv) and the slug rules in platform/slug.py.

When the www repository sits next to this one (../website-unsrat-2026), the list is also compared with the
official programme data there: the same 97 PDDIKTI codes, the same names and levels.
"""
from __future__ import print_function

import io
import json
import os
import sys

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AKAR, "platform"))

import slug  # noqa: E402

WWW_PRODI = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026", "site", "mockup", "data", "prodi.json")

gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


# --- rules
cek(slug.periksa_slug("s1informatika", "S1") == [], "s1informatika harus sah")
cek(slug.periksa_slug("sp1jantung", "Sp-1") == [], "sp1jantung harus sah")
cek(slug.periksa_slug("S1Informatika", "S1"), "huruf besar harus ditolak")
cek(slug.periksa_slug("s1-informatika", "S1"), "tanda hubung harus ditolak")
cek(slug.periksa_slug("s1", "S1"), "slug terlalu pendek harus ditolak")
cek(slug.periksa_slug("s2informatika", "S1"), "awalan jenjang yang salah harus ditolak")
cek(slug.periksa_slug("admin"), "alamat cadangan harus ditolak")
cek(slug.periksa_slug("s1" + "a" * 30, "S1"), "slug terlalu panjang harus ditolak")
cek(slug.periksa_daftar([
    {"kode_pddikti": "1", "jenjang": "S1", "slug_usulan": "s1aaa"},
    {"kode_pddikti": "2", "jenjang": "S1", "slug_usulan": "s1aaa"},
]), "slug ganda harus ditemukan")

# --- the approved list
baris = slug.baca_csv()
cek(len(baris) == 97, "slug.csv harus berisi 97 prodi, ada %d" % len(baris))
for kode, pesan in slug.periksa_daftar(baris):
    gagal.append("slug.csv %s: %s" % (kode, pesan))
cek(any(b["slug_usulan"] == "s1informatika" for b in baris), "contoh pengguna s1informatika harus ada")
for b in baris:
    cek(b["alamat_usulan"] == "https://prodi.unsrat.ac.id/%s/" % b["slug_usulan"],
        "alamat_usulan %s tidak cocok dengan slug" % b["kode_pddikti"])

# --- against the official data in the www repository, when it is there
if os.path.isfile(WWW_PRODI):
    with io.open(WWW_PRODI, encoding="utf-8") as f:
        resmi = {p["kode_pddikti"]: p for p in json.load(f)["program"]}
    di_csv = {b["kode_pddikti"]: b for b in baris}
    for kode in sorted(set(resmi) - set(di_csv)):
        gagal.append("prodi %s (%s) ada di www tetapi tidak punya slug" % (kode, resmi[kode]["nama"]))
    for kode in sorted(set(di_csv) - set(resmi)):
        gagal.append("slug.csv memuat kode %s yang tidak ada di www" % kode)
    for kode in sorted(set(resmi) & set(di_csv)):
        for kolom in ("nama", "jenjang"):
            cek(resmi[kode][kolom] == di_csv[kode][kolom],
                "%s %s: www '%s', slug.csv '%s'" % (kode, kolom, resmi[kode][kolom], di_csv[kode][kolom]))
    print("dibandingkan dengan data www: %d prodi" % len(resmi))
else:
    print("data www tidak ditemukan di %s, perbandingan dilewati" % WWW_PRODI)

for g in gagal:
    print("GAGAL", g)
print("uji_slug: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
