# -*- coding: utf-8 -*-
"""The spam filter (platform/pemantau/saringan_spam.py), adapted from www in the pre-production audit (docs/asal-modul.md):
besides gambling, the selling language of illegal online loans ("pinjol"), diplomas and drugs.

- every listed phrase is found, with its kind (judi / pinjol / terlarang), also when it is disguised (capitals,
  digits for letters, a dot between the letters, invisible characters, fullwidth letters);
- text a university writes about these topics itself passes: research titles on online lending, warnings about fake
  diplomas, pharmacy and public-health studies;
- the refusals of the admin, of www's data and of the integrity check name the kind (isi_halaman.py, tarik_www.py,
  masukan_admin.py, data_prodi.py, cek_integritas.py).

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import os
import shutil
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))

try:
    import jinja2  # noqa: F401
    import flask  # noqa: F401
except ImportError:
    print("uji_saringan_spam: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-spam-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"),
                  ("PRODI_LOG", "log"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)

import cek_integritas  # noqa: E402
import data_prodi  # noqa: E402
import isi_halaman as ih  # noqa: E402
import masukan_admin  # noqa: E402
import saringan_spam as ss  # noqa: E402

gagal = []

# spam as it is planted on .ac.id sites, with the term the filter must report and its kind
SPAM = [
    ("Pinjaman online DANA CEPAT CAIR tanpa BI checking", "dana cepat cair", "pinjol"),
    ("PINJOL TANPA KTP, cair dalam 5 menit!", "pinjol tanpa ktp", "pinjol"),
    ("p1nj0l cepat c4ir", "p1nj0l cepat c4ir", "pinjol"),
    ("Pinjol terpercaya, bunga 0%", "pinjol terpercaya", "pinjol"),
    ("Pinjaman online langsung cair hari ini", "pinjaman online langsung cair", "pinjol"),
    ("Aplikasi pinjol terbaik 2026", "pinjol terbaik", "pinjol"),
    ("Pinjaman tanpa​KTP", None, "pinjol"),                                # invisible character between words
    ("Pinjol mudah cair", "pinjol mudah cair", "pinjol"),
    ("Jual Ijazah Asli Terdaftar PDDikti", "jual ijazah asli", "terlarang"),
    ("Jasa pembuatan ijazah asli S1 dan S2", "jasa pembuatan ijazah asli", "terlarang"),
    ("Beli ijazah asli tanpa kuliah", "beli ijazah asli", "terlarang"),
    ("Jual obat aborsi cytotec asli", "jual obat aborsi", "terlarang"),
    ("Obat penggugur kandungan ampuh", "obat penggugur kandungan ampuh", "terlarang"),
    ("JUAL VIAGRA asli", "jual viagra", "terlarang"),
    ("ｊｕａｌ ｃｉａｌｉｓ", "jual cialis", "terlarang"),                                  # fullwidth letters
    ("Slot gacor maxwin", "slot gacor", "judi"),
    ("bonus s1ot g4cor", "s1ot g4cor", "judi"),
    ("t.o.g.e.l online", None, "judi"),
]
# what a university writes about these topics itself
BOLEH = [
    "Perlindungan hukum bagi pengguna pinjaman online ilegal",
    "Dampak pinjol terhadap kesehatan mental mahasiswa",
    "Sistem pendukung keputusan pemilihan pinjaman online terbaik dengan metode SAW",
    "Literasi keuangan dan penggunaan pinjaman online di Kota Manado",
    "Kredit tanpa agunan pada perbankan syariah",
    "Waspada penipuan jasa pembuatan ijazah palsu",
    "Pastikan ijazah asli terdaftar di PDDikti",
    "Legalisir ijazah dan transkrip nilai",
    "Identifikasi sildenafil sitrat (Viagra) dalam jamu kuat pria",
    "Penyalahgunaan obat penggugur kandungan pada remaja",
    "Pencairan dana beasiswa KIP Kuliah",
    "Peminjaman buku di perpustakaan fakultas",
]


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


try:
    # --- every listed phrase, as written and disguised, with its kind
    for jenis, daftar in (("pinjol", ss.ISTILAH_PINJOL), ("terlarang", ss.ISTILAH_LAIN), ("judi", ss.ISTILAH)):
        for istilah in daftar:
            for bentuk in (istilah, istilah.upper(), "Info: %s, hubungi kami" % istilah):
                ketemu = ss.cari(bentuk)
                cek(ketemu and ss.jenis(ketemu) == jenis, "%r harus ditemukan sebagai %s: %r" % (bentuk, jenis, ketemu))
    cek(len(set(ss.ISTILAH_PINJOL + ss.ISTILAH_LAIN)) == len(ss.ISTILAH_PINJOL + ss.ISTILAH_LAIN), "tanpa istilah ganda")
    cek(not set(ss.ISTILAH) & set(ss.ISTILAH_PINJOL + ss.ISTILAH_LAIN), "istilah judi tidak tercampur dengan yang lain")
    for teks, istilah, jenis in SPAM:
        ketemu = ss.cari(teks)
        cek(ketemu and (istilah is None or ketemu == istilah) and (jenis is None or ss.jenis(ketemu) == jenis),
            "%r harus ditemukan (%s, %s): dapat %r" % (teks, istilah, jenis, ketemu))
    for teks in BOLEH:
        cek(ss.cari(teks) is None, "%r harus lolos: dapat %r" % (teks, ss.cari(teks)))
    cek(ss.jenis("tidak dikenal") == "terlarang" and ss.jenis(None) == "terlarang", "jenis istilah tak dikenal: terlarang")

    # --- the refusals name the kind
    A = "55201"
    m = ih.periksa("sejarah", {"linimasa": [{"tahun": 2001, "peristiwa": "Pinjol cepat cair"}]}, A)
    cek(any("memuat teks pinjol (pinjol cepat cair)" in x for x in m), "isi halaman: teks pinjol: %r" % m)
    m = ih.periksa("sejarah", {"linimasa": [{"tahun": 2001, "peristiwa": "Jual ijazah asli"}]}, A)
    cek(any("memuat teks terlarang (jual ijazah asli)" in x for x in m), "isi halaman: teks terlarang: %r" % m)
    m = ih.periksa("sejarah", {"linimasa": [{"tahun": 2001, "peristiwa": "Bonus slot gacor"}]}, A)
    cek(any("memuat teks judi (slot gacor)" in x for x in m), "isi halaman: teks judi: %r" % m)
    cek(not ih.periksa("sejarah", {"linimasa": [{"tahun": 2001, "peristiwa": BOLEH[0]}]}, A), "isi halaman: judul penelitian lolos")
    try:
        masukan_admin._teks("Ada iklan: dana cepat cair", 2000, "Isi")
        gagal.append("masukan berteks pinjol harus ditolak")
    except masukan_admin.GagalMasukan as e:
        cek(str(e) == "Isi memuat teks pinjol", "pesan masukan: %s" % e)
    m = data_prodi.periksa_nilai("nama_en", "Fast loans, dana cepat cair")
    cek(any("istilah terlarang" in x and "dana cepat cair" in x for x in m), "data prodi: %r" % m)
    temuan = cek_integritas.periksa_teks("s1informatika/index.html", '<meta http-equiv="Content-Security-Policy" '
                                         'content="default-src \'self\'"><p>Pinjol tanpa KTP</p>')
    cek([t for t in temuan if t[0] == "SPAM" and "pinjol tanpa ktp" in t[2].lower()], "cek integritas: %r" % temuan)
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_saringan_spam: %d istilah, %s" % (len(ss.ISTILAH + ss.ISTILAH_PINJOL + ss.ISTILAH_LAIN),
                                              "LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
