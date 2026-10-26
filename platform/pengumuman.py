# -*- coding: utf-8 -*-
"""Announcements and news of a programme (langkah 3b): prodi/<kode>/pengumuman.json.

One kind of item for both announcements and news, told apart by a category from platform/template/kategori.json.
An item:

    {"id": "2026-10-26-jadwal-uts",          date + words of the title; fixed once created (it is the address)
     "judul", "tanggal" (YYYY-MM-DD), "kategori", "ringkasan" (list, search engines, link previews), "isi",
     "foto": [media.simpan_foto records; the first is the main photo], "pdf": [media.simpan_pdf records],
     "sematkan": bool (kept at the top of the home page), "kedaluwarsa": "" or YYYY-MM-DD (leaves the home page
     after that day, stays in the archive), "status": draf | menunggu | terbit | ditarik,
     "dibuat", "diubah", "oleh"}

"isi" is plain text: paragraphs separated by an empty line, lines starting with "- " form a list, https:// addresses
become links (bangun.py teks_isi). No HTML is accepted anywhere. Published items are never deleted, only withdrawn
("ditarik"); every change keeps the previous file in the version history (lokasi.tulis).

Until the admin exists (langkah 6), items are added from the command line:

    python3 platform/pengumuman.py tambah --prodi 55201 --judul "Jadwal UTS" --kategori akademik \\
        --ringkasan "Jadwal ujian tengah semester gasal 2026/2027." --isi isi.txt \\
        --foto poster.jpg --alt "Poster jadwal UTS" --pdf jadwal.pdf --judul-pdf "Jadwal UTS" --terbit
    python3 platform/pengumuman.py daftar --prodi 55201
    python3 platform/pengumuman.py status --prodi 55201 --id 2026-10-26-jadwal-uts --jadi ditarik
then rebuild: .venv/bin/python platform/bangun/bangun.py --prodi 55201
"""
from __future__ import print_function

import argparse
import datetime
import io
import json
import os
import re
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import lokasi  # noqa: E402
import media  # noqa: E402
import saringan_spam  # noqa: E402

KATEGORI_JSON = os.path.join(PLATFORM, "template", "kategori.json")
STATUS = ("draf", "menunggu", "terbit", "ditarik")
POLA_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$")
POLA_TANGGAL = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAKS = {"judul": 150, "ringkasan": 300, "isi": 20000, "alt": 200, "judul_pdf": 150}
MAKS_FOTO = 7             # the main photo + 6 in the gallery
MAKS_PDF = 3
MAKS_ID = 70


class GagalPengumuman(ValueError):
    pass


def baca_kategori(path=KATEGORI_JSON):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)["kategori"]


def baca(kode):
    return lokasi.baca("prodi/%s/pengumuman" % kode) or {"butir": []}


def _tanggal_sah(teks):
    if not POLA_TANGGAL.match(teks or ""):
        return False
    try:
        datetime.date.fromisoformat(teks)
        return True
    except ValueError:
        return False


def _periksa_teks(label, nilai, maks, wajib, masalah):
    if not isinstance(nilai, str):
        masalah.append("%s harus berupa teks" % label)
        return
    if wajib and not nilai.strip():
        masalah.append("%s wajib diisi" % label)
    if len(nilai) > maks:
        masalah.append("%s terlalu panjang (maksimal %d karakter)" % (label, maks))
    if re.search(r"<\s*/?\s*[a-zA-Z!]", nilai):
        masalah.append("%s tidak boleh memuat HTML" % label)
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", nilai):
        masalah.append("%s memuat karakter kendali" % label)
    istilah = saringan_spam.cari(nilai)
    if istilah:
        masalah.append("%s memuat istilah terlarang (“%s”)" % (label, istilah))


def _periksa_media_alamat(rekam):
    if "url" in rekam:
        return media.url_sah(rekam["url"])
    return media.jalur_sah(rekam.get("jalur"))


def periksa(b, kategori=None):
    """Problems with one item (empty list when it may be saved)."""
    kategori = kategori if kategori is not None else baca_kategori()
    if not isinstance(b, dict):
        return ["butir bukan objek"]
    masalah = []
    if not POLA_ID.match(str(b.get("id", ""))) or len(b["id"]) > MAKS_ID:
        masalah.append("id tidak sah")
    _periksa_teks("Judul", b.get("judul"), MAKS["judul"], True, masalah)
    _periksa_teks("Ringkasan", b.get("ringkasan"), MAKS["ringkasan"], True, masalah)
    _periksa_teks("Isi", b.get("isi", ""), MAKS["isi"], False, masalah)
    if not _tanggal_sah(b.get("tanggal")):
        masalah.append("tanggal tidak sah")
    if b.get("kedaluwarsa") and not _tanggal_sah(b["kedaluwarsa"]):
        masalah.append("tanggal kedaluwarsa tidak sah")
    elif b.get("kedaluwarsa") and _tanggal_sah(b.get("tanggal")) and b["kedaluwarsa"] < b["tanggal"]:
        masalah.append("tanggal kedaluwarsa sebelum tanggal pengumuman")
    if b.get("kategori") not in {k["id"] for k in kategori}:
        masalah.append("kategori tidak dikenal")
    if b.get("status") not in STATUS:
        masalah.append("status tidak dikenal")
    if not isinstance(b.get("sematkan", False), bool):
        masalah.append("sematkan harus ya/tidak")
    foto, pdf = b.get("foto", []), b.get("pdf", [])
    if not isinstance(foto, list) or len(foto) > MAKS_FOTO:
        masalah.append("foto paling banyak %d" % MAKS_FOTO)
        foto = []
    if not isinstance(pdf, list) or len(pdf) > MAKS_PDF:
        masalah.append("PDF paling banyak %d" % MAKS_PDF)
        pdf = []
    for i, f in enumerate(foto):
        if not isinstance(f, dict) or f.get("jenis") != "gambar" or not isinstance(f.get("varian"), dict) or not f["varian"]:
            masalah.append("foto ke-%d tidak sah" % (i + 1))
            continue
        _periksa_teks("Teks alternatif foto ke-%d" % (i + 1), f.get("alt"), MAKS["alt"], True, masalah)
        if not all(isinstance(v, dict) and _periksa_media_alamat(v) for v in f["varian"].values()):
            masalah.append("alamat foto ke-%d tidak sah" % (i + 1))
    for i, p in enumerate(pdf):
        if not isinstance(p, dict) or p.get("jenis") != "pdf" or not _periksa_media_alamat(p):
            masalah.append("PDF ke-%d tidak sah" % (i + 1))
            continue
        _periksa_teks("Judul PDF ke-%d" % (i + 1), p.get("judul"), MAKS["judul_pdf"], True, masalah)
    return masalah


def buat_id(tanggal, judul, dipakai):
    """'2026-10-26-jadwal-uts-gasal' from the date and the first words of the title; unique among `dipakai`."""
    kata = re.sub(r"[^a-z0-9]+", "-", judul.lower().encode("ascii", "ignore").decode("ascii")).strip("-")
    kata = kata[:MAKS_ID - 15].rstrip("-") or "pengumuman"
    dasar = "%s-%s" % (tanggal, kata)
    hasil, n = dasar, 2
    while hasil in dipakai:
        hasil, n = "%s-%d" % (dasar, n), n + 1
    return hasil


def _sekarang():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _simpan(kode, data, oleh, aksi):
    lokasi.tulis("prodi/%s/pengumuman" % kode, data, oleh, "Pengumuman", aksi)


def tambah(kode, isian, oleh, status="draf"):
    """Add an item from `isian` (judul, ringkasan, kategori, and optionally tanggal, isi, foto, pdf, sematkan,
    kedaluwarsa). Media must already be stored (media.simpan_foto / simpan_pdf). Returns the new id."""
    data = baca(kode)
    tanggal = isian.get("tanggal") or datetime.date.today().isoformat()
    b = {"id": "", "judul": (isian.get("judul") or "").strip(), "tanggal": tanggal,
         "kategori": isian.get("kategori"), "ringkasan": (isian.get("ringkasan") or "").strip(),
         "isi": (isian.get("isi") or "").strip(), "foto": isian.get("foto") or [], "pdf": isian.get("pdf") or [],
         "sematkan": bool(isian.get("sematkan")), "kedaluwarsa": isian.get("kedaluwarsa") or "", "status": status,
         "dibuat": _sekarang(), "diubah": _sekarang(), "oleh": oleh}
    if _tanggal_sah(tanggal):
        b["id"] = buat_id(tanggal, b["judul"] or "pengumuman", {x["id"] for x in data["butir"]})
    masalah = periksa(b)
    if masalah:
        raise GagalPengumuman("; ".join(masalah))
    data["butir"].append(b)
    _simpan(kode, data, oleh, "tambah %s (%s)" % (b["id"], status))
    return b["id"]


def _cari(data, id_):
    for b in data["butir"]:
        if b["id"] == id_:
            return b
    raise GagalPengumuman("pengumuman %s tidak ada" % id_)


BOLEH_DIUBAH = ("judul", "tanggal", "kategori", "ringkasan", "isi", "foto", "pdf", "sematkan", "kedaluwarsa")


def ubah(kode, id_, perubahan, oleh):
    """Change fields of an item. The id (its address) stays the same even when the title or date changes."""
    data = baca(kode)
    b = _cari(data, id_)
    tidak_boleh = set(perubahan) - set(BOLEH_DIUBAH)
    if tidak_boleh:
        raise GagalPengumuman("tidak bisa diubah: %s" % ", ".join(sorted(tidak_boleh)))
    baru = dict(b, **perubahan)
    baru["diubah"] = _sekarang()
    masalah = periksa(baru)
    if masalah:
        raise GagalPengumuman("; ".join(masalah))
    b.update(baru)
    _simpan(kode, data, oleh, "ubah %s" % id_)


def ganti_status(kode, id_, status, oleh):
    """draf -> menunggu (an operator asks for approval) -> terbit (published) -> ditarik (withdrawn) and back."""
    if status not in STATUS:
        raise GagalPengumuman("status tidak dikenal: %s" % status)
    data = baca(kode)
    b = _cari(data, id_)
    lama = b["status"]
    b["status"] = status
    b["diubah"] = _sekarang()
    _simpan(kode, data, oleh, "%s: %s -> %s" % (id_, lama, status))


def masih_berlaku(b, hari_ini):
    return not b.get("kedaluwarsa") or b["kedaluwarsa"] >= hari_ini


def terbit(data):
    """Published items that pass the checks, newest first (date, then creation time)."""
    kategori = baca_kategori()
    hasil = [b for b in data.get("butir", []) if b.get("status") == "terbit" and not periksa(b, kategori)]
    return sorted(hasil, key=lambda b: (b["tanggal"], b.get("dibuat", "")), reverse=True)


# ------------------------------------------------------------------ command line

def _baca_berkas(path):
    with open(path, "rb") as f:
        return f.read()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pengumuman dan berita prodi (sementara, sebelum admin tersedia)")
    sub = ap.add_subparsers(dest="perintah", required=True)
    t = sub.add_parser("tambah", help="tambah pengumuman")
    t.add_argument("--prodi", required=True, help="kode PDDIKTI")
    t.add_argument("--judul", required=True)
    t.add_argument("--kategori", required=True, choices=[k["id"] for k in baca_kategori()])
    t.add_argument("--ringkasan", required=True)
    t.add_argument("--isi", help="berkas teks berisi isi pengumuman")
    t.add_argument("--tanggal", help="YYYY-MM-DD (bawaan: hari ini)")
    t.add_argument("--foto", action="append", default=[], help="JPEG/PNG; yang pertama menjadi foto utama")
    t.add_argument("--alt", action="append", default=[], help="teks alternatif, satu per --foto, urutan sama")
    t.add_argument("--pdf", action="append", default=[], help="berkas PDF")
    t.add_argument("--judul-pdf", action="append", default=[], help="judul PDF, satu per --pdf, urutan sama")
    t.add_argument("--sematkan", action="store_true")
    t.add_argument("--kedaluwarsa", default="", help="YYYY-MM-DD")
    t.add_argument("--terbit", action="store_true", help="langsung terbit (bawaan: draf)")
    t.add_argument("--oleh", default="baris-perintah")
    d = sub.add_parser("daftar", help="daftar pengumuman satu prodi")
    d.add_argument("--prodi", required=True)
    s = sub.add_parser("status", help="ganti status pengumuman")
    s.add_argument("--prodi", required=True)
    s.add_argument("--id", required=True)
    s.add_argument("--jadi", required=True, choices=STATUS)
    s.add_argument("--oleh", default="baris-perintah")
    a = ap.parse_args(argv)
    if not lokasi.NAMA_SAH.match("prodi/%s/pengumuman" % a.prodi):
        print("kode prodi tidak sah")
        return 1
    try:
        if a.perintah == "tambah":
            if len(a.alt) != len(a.foto) or len(a.judul_pdf) != len(a.pdf):
                raise GagalPengumuman("setiap --foto perlu --alt, setiap --pdf perlu --judul-pdf")
            isi = io.open(a.isi, encoding="utf-8").read() if a.isi else ""
            foto = [media.simpan_foto(a.prodi, _baca_berkas(p), alt) for p, alt in zip(a.foto, a.alt)]
            pdf = [media.simpan_pdf(a.prodi, _baca_berkas(p), j) for p, j in zip(a.pdf, a.judul_pdf)]
            id_ = tambah(a.prodi, {"judul": a.judul, "kategori": a.kategori, "ringkasan": a.ringkasan, "isi": isi,
                                   "tanggal": a.tanggal, "foto": foto, "pdf": pdf, "sematkan": a.sematkan,
                                   "kedaluwarsa": a.kedaluwarsa}, a.oleh, "terbit" if a.terbit else "draf")
            print("Ditambahkan: %s" % id_)
        elif a.perintah == "daftar":
            for b in sorted(baca(a.prodi)["butir"], key=lambda b: b["tanggal"], reverse=True):
                print("%-9s %s  %s%s" % (b["status"], b["id"], b["judul"], "  [disematkan]" if b.get("sematkan") else ""))
        else:
            ganti_status(a.prodi, a.id, a.jadi, a.oleh)
            print("Status %s: %s" % (a.id, a.jadi))
    except (GagalPengumuman, ValueError, IOError) as e:
        print("GAGAL: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
