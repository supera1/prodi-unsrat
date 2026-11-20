# -*- coding: utf-8 -*-
"""Announcements and news of a programme (langkah 3b): prodi/<kode>/pengumuman.json.

One kind of item for both announcements and news, told apart by a category from platform/template/kategori.json.
An item:

    {"id": "2026-10-26-jadwal-uts",          date + words of the title; fixed once created (it is the address)
     "judul", "tanggal" (YYYY-MM-DD), "kategori", "ringkasan" (list, search engines, link previews), "isi",
     "foto": [media.simpan_foto records; the first is the main photo], "pdf": [media.simpan_pdf records],
     "sematkan": bool (kept at the top of the home page), "kedaluwarsa": "" or YYYY-MM-DD (leaves the home page
     after that day, stays in the archive), "status": draf | menunggu | terbit | ditarik,
     "dibuat", "diubah", "oleh" (who wrote it), "catatan" (the admin's note when sending it back; never published),
     "en": optional English version (Fase 5 langkah 4, K-P37), see below}

English version: "en": {"judul", "ringkasan", "isi" (same plain text rules), "mesin": {field: machine translation not
yet checked by a person}, "asal": {field: the Indonesian text it was translated from}}. It follows the item's own
status and workflow; photos and PDFs are shared. The English site shows an item (inggris()) once it is published and
its English title, summary and (when the Indonesian one has one) body are filled in with no unchecked machine text.

Workflow (langkah 6): an operator writes a draft and submits it ("menunggu"); a programme admin publishes it
("terbit") or sends it back to draft with a note (kembalikan). Admins may also write and publish directly.

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
MAKS = {"judul": 150, "ringkasan": 300, "isi": 20000, "alt": 200, "judul_pdf": 150, "catatan": 500}
MAKS_FOTO = 7             # the main photo + 6 in the gallery
MAKS_PDF = 3
MAKS_ID = 70
TEKS_EN = ("judul", "ringkasan", "isi")
LABEL_EN = {"judul": "Judul (Inggris)", "ringkasan": "Ringkasan (Inggris)", "isi": "Isi (Inggris)"}


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


def _periksa_en(en, masalah):
    """The English version of an item: optional texts (judul and ringkasan together), machine marks, sources."""
    if not isinstance(en, dict) or set(en) - set(TEKS_EN) - {"mesin", "asal"}:
        masalah.append("versi Inggris tidak sah")
        return
    for k in TEKS_EN:
        _periksa_teks(LABEL_EN[k], en.get(k, ""), MAKS[k], False, masalah)
    if isinstance(en.get("isi", ""), str) and (en.get("isi") or "").strip() \
            and not all(isinstance(en.get(k), str) and en[k].strip() for k in ("judul", "ringkasan")):
        masalah.append("versi Inggris perlu judul dan ringkasan bila isinya diisi")
    for kunci in ("mesin", "asal"):
        nilai = en.get(kunci, {})
        if not isinstance(nilai, dict) or set(nilai) - set(TEKS_EN) or \
                not all(isinstance(v, str) and len(v) <= MAKS[k] for k, v in nilai.items()):
            masalah.append("versi Inggris: %s tidak sah" % kunci)


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
    if b.get("catatan"):
        _periksa_teks("Catatan", b["catatan"], MAKS["catatan"], False, masalah)
    if "en" in b:
        _periksa_en(b["en"], masalah)
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
    kedaluwarsa, en). Media must already be stored (media.simpan_foto / simpan_pdf). Returns the new id."""
    data = baca(kode)
    tanggal = isian.get("tanggal") or datetime.date.today().isoformat()
    b = {"id": "", "judul": (isian.get("judul") or "").strip(), "tanggal": tanggal,
         "kategori": isian.get("kategori"), "ringkasan": (isian.get("ringkasan") or "").strip(),
         "isi": (isian.get("isi") or "").strip(), "foto": isian.get("foto") or [], "pdf": isian.get("pdf") or [],
         "sematkan": bool(isian.get("sematkan")), "kedaluwarsa": isian.get("kedaluwarsa") or "", "status": status,
         "dibuat": _sekarang(), "diubah": _sekarang(), "oleh": oleh}
    if isian.get("en"):
        b["en"] = isian["en"]
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


BOLEH_DIUBAH = ("judul", "tanggal", "kategori", "ringkasan", "isi", "foto", "pdf", "sematkan", "kedaluwarsa", "en")


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


def kembalikan(kode, id_, catatan, oleh):
    """Send a submitted item back to draft with a note for its writer."""
    catatan = (catatan or "").strip()
    masalah = []
    _periksa_teks("Catatan", catatan, MAKS["catatan"], True, masalah)
    if masalah:
        raise GagalPengumuman("; ".join(masalah))
    data = baca(kode)
    b = _cari(data, id_)
    b.update(status="draf", catatan=catatan, diubah=_sekarang())
    _simpan(kode, data, oleh, "%s dikembalikan ke draf" % id_)


def cari(kode, id_):
    """The item `id_` of a programme (GagalPengumuman when there is none)."""
    if not POLA_ID.match(id_ or ""):
        raise GagalPengumuman("pengumuman tidak ditemukan")
    return _cari(baca(kode), id_)


def masih_berlaku(b, hari_ini):
    return not b.get("kedaluwarsa") or b["kedaluwarsa"] >= hari_ini


def terbit(data):
    """Published items that pass the checks, newest first (date, then creation time)."""
    kategori = baca_kategori()
    hasil = [b for b in data.get("butir", []) if b.get("status") == "terbit" and not periksa(b, kategori)]
    return sorted(hasil, key=lambda b: (b["tanggal"], b.get("dibuat", "")), reverse=True)


# ------------------------------------------------------------------ English version (Fase 5 langkah 4)

def keadaan_en(b):
    """The state of an item's English version: "kosong" (none), "belum-lengkap" (title, summary, or body missing),
    "mesin" (unchecked machine translation), or "siap" (shown on the English site once the item is published)."""
    en = b.get("en") or {}
    if not any((en.get(k) or "").strip() for k in TEKS_EN):
        return "kosong"
    if not (en.get("judul") or "").strip() or not (en.get("ringkasan") or "").strip() \
            or ((b.get("isi") or "").strip() and not (en.get("isi") or "").strip()):
        return "belum-lengkap"
    if en.get("mesin"):
        return "mesin"
    return "siap"


def perlu_diperbarui(b):
    """The fields whose Indonesian text changed since its English text was written."""
    en = b.get("en") or {}
    asal = en.get("asal") or {}
    return [k for k in TEKS_EN if (en.get(k) or "").strip() and k in asal and asal[k] != (b.get(k) or "")]


def inggris(b):
    """The item as the English site shows it (its English texts, the shared date, category, photos and PDFs), or
    None while its English version is not ready (keadaan_en)."""
    if keadaan_en(b) != "siap":
        return None
    en = b["en"]
    hasil = {k: v for k, v in b.items() if k not in ("en", "catatan")}
    hasil.update(judul=en["judul"].strip(), ringkasan=en["ringkasan"].strip(), isi=(en.get("isi") or "").strip())
    return hasil


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
