# -*- coding: utf-8 -*-
"""The content of a programme's own pages (Fase 2, K-P23): the 22 required accreditation pages ("wajib") and the 2
optional ones of the master menu (platform/template/menu.json).

Every page has a content template (TEMPLAT): sections of fields, lists and tables that follow the page's description in
the menu and what accreditation asks for, plus free extra sections at the end. The template drives:
- periksa(): what may be stored: types, lengths, choices, links to https:// addresses only, uploaded files of this
  programme only, no gambling text;
- tampilan(): what the builder shows (headings, paragraphs, lists, tables, cards, documents, photos, links), as plain
  data for the Jinja2 templates. Text is escaped here; only the limited markup ([text](https://...), **bold**, "- "
  lists, bare https:// addresses) becomes HTML;
- the form of the admin (langkah 2: the form editor of www's superadmin, site/admin/editor.py, adapted). The nodes use
  the same vocabulary as that editor for this reason.

Stored in prodi/<kode>/halaman-<id>.json (lokasi.py), every version kept in the history:
    {"versi": n, "terbit": {"isi": {...}, "oleh", "waktu"} or null, "draf": {...} or null}
The site shows "terbit" only; drafts and their approval come in langkah 3 (K-P24). Keys a template does not know are
kept, so a template changed after the pilot never loses content.

    python3 platform/isi_halaman.py daftar --prodi <kode>       which pages have published content
    python3 platform/isi_halaman.py contoh --prodi <kode>       fill every empty page with [CONTOH] content, to look at
                                                                the pages (never over real content, never in production)
    python3 platform/isi_halaman.py tarik --prodi <kode> [--halaman <id>]   take a page (or all) off the site
"""
from __future__ import print_function

import argparse
import datetime
import os
import re
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

from markupsafe import Markup, escape  # noqa: E402

import lokasi  # noqa: E402
import media  # noqa: E402
import saringan_spam  # noqa: E402

POLA_KODE = re.compile(r"^[0-9A-Za-z]{3,12}$")
KONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
POLA_URL = re.compile(r"^https://[A-Za-z0-9.-]+(:[0-9]{1,5})?(/[^\s<>\"'\\]*)?$")
# [text](address) in a paragraph, or a bare https:// address
TAUTAN = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\s]{1,500})\)|(https://[^\s<>\"'\\]{1,500})")
TEBAL = re.compile(r"\*\*(\S(?:[^*\n]{0,298}\S)?)\*\*")
MAKS_URL = 500
CONTOH = "[CONTOH]"
TAMPIL = ("daftar", "tabel", "kartu", "dokumen", "galeri", "tautan", "bagian")
SKALAR = ("teks", "bilangan", "persen", "url", "pilihan", "centang", "dokumen")


class GagalIsi(ValueError):
    """Content that may not be stored; the message is for the programme admin."""


# ------------------------------------------------------------------ template nodes (the vocabulary of www's editor.py)

def teks(label, wajib=False, maks=300, panjang=False, kaya=False, bantuan=""):
    """A line of text (or, panjang, several lines). kaya: the limited markup of a paragraph."""
    return {"jenis": "teks", "label": label, "wajib": wajib, "maks": maks, "panjang": panjang, "kaya": kaya,
            "bantuan": bantuan}


def paragraf(label="", maks=10000, bantuan=""):
    """Paragraphs with links and bold. An empty label shows no heading (the page's own introduction)."""
    return teks(label, maks=maks, panjang=True, kaya=True, bantuan=bantuan or
                "Paragraf dipisah baris kosong. Tautan: [teks](https://...); huruf tebal: **teks**; daftar: baris "
                "yang diawali \"- \".")


def bilangan(label, minimum=0, maksimum=10 ** 7, wajib=False, bantuan="", format="angka"):
    return {"jenis": "bilangan", "label": label, "minimum": minimum, "maksimum": maksimum, "wajib": wajib,
            "bantuan": bantuan, "format": format}


def tahun(label="Tahun", wajib=False):
    return bilangan(label, 1900, 2100, wajib, "Empat angka, mis. 2025.", format="tahun")


def persen(label, wajib=False):
    """0 to 100, at most two decimals (a comma or a point)."""
    return {"jenis": "persen", "label": label, "wajib": wajib, "bantuan": "0 sampai 100, mis. 87,5."}


def url(label="Alamat", wajib=False, bantuan="Alamat lengkap yang diawali https://"):
    return {"jenis": "url", "label": label, "wajib": wajib, "bantuan": bantuan}


def pilihan(label, opsi, wajib=False):
    return {"jenis": "pilihan", "label": label, "opsi": list(opsi), "wajib": wajib, "bantuan": ""}


def centang(label):
    return {"jenis": "centang", "label": label, "bantuan": ""}


def objek(label, bidang):
    """bidang: [(key, node), ...]."""
    return {"jenis": "objek", "label": label, "bidang": bidang}


def daftar(label, isi, tampil, maks=100, bernomor=False, bantuan=""):
    """A list that can grow, shrink and be reordered. tampil: how the site shows it (TAMPIL)."""
    return {"jenis": "daftar", "label": label, "isi": isi, "tampil": tampil, "maks": maks, "bernomor": bernomor,
            "bantuan": bantuan}


def dokumen(label="Berkas PDF", wajib=True):
    """A PDF stored with media.simpan_pdf (no active content, no gambling text, at most 20 MB)."""
    return {"jenis": "dokumen", "label": label, "wajib": wajib, "bantuan": "PDF, paling besar 20 MB."}


def foto(label="Foto", wajib=True):
    """A photo stored with media.simpan_foto (JPEG/PNG, re-encoded; its alternative text is part of it)."""
    return {"jenis": "foto", "label": label, "wajib": wajib, "bantuan": "JPEG atau PNG; teks alternatif wajib."}


# ------------------------------------------------------------------ shared pieces

TINGKAT = ("Lokal", "Nasional", "Internasional")


def dokumen_daftar(label="Dokumen", bantuan="", maks=50):
    return daftar(label, objek("Dokumen", [("judul", teks("Judul dokumen", wajib=True, maks=200)), ("tahun", tahun()),
                                           ("keterangan", teks("Keterangan", maks=300)), ("berkas", dokumen())]),
                  "dokumen", maks, bantuan=bantuan)


def foto_daftar(label="Foto", maks=6):
    return daftar(label, objek("Foto", [("berkas", foto()), ("keterangan", teks("Keterangan foto", maks=300))]), "galeri", maks)


def tautan_daftar(label="Tautan", maks=10):
    return daftar(label, objek("Tautan", [("label", teks("Nama tautan", wajib=True, maks=150)),
                                          ("alamat", url(wajib=True))]), "tautan", maks)


def uraian(label="", bantuan=""):
    return paragraf(label, bantuan=bantuan)


TAMBAHAN = daftar("Bagian tambahan", objek("Bagian", [("judul", teks("Judul bagian", wajib=True, maks=150)),
                                                      ("isi", paragraf("Isi bagian"))]),
                  "bagian", 10, bantuan="Untuk hal yang belum ada tempatnya di atas.")


def halaman(*bagian):
    """A page: its sections, then the free extra sections."""
    return objek("", list(bagian) + [("tambahan", TAMBAHAN)])


def tabel(label, kolom, maks=200, bantuan=""):
    return daftar(label, objek("Baris", kolom), "tabel", maks, bantuan=bantuan)


def kartu(label, bidang, maks=50, bantuan=""):
    return daftar(label, objek("Kartu", bidang), "kartu", maks, bantuan=bantuan)


def butir(label, maks=30, bernomor=True, panjang_butir=500):
    return daftar(label, teks("Butir", wajib=True, maks=panjang_butir), "daftar", maks, bernomor)


# ------------------------------------------------------------------ the templates (rencana Fase 2 §3.3)

TEMPLAT = {
    # Profil
    "sejarah": halaman(
        ("uraian", uraian()),
        ("linimasa", tabel("Linimasa", [("tahun", tahun(wajib=True)), ("peristiwa", teks("Peristiwa", wajib=True, maks=300))], 60)),
        ("foto", foto_daftar())),
    "visi-misi": halaman(
        ("visi", paragraf("Visi keilmuan", maks=1500)),
        ("misi", butir("Misi")),
        ("tujuan", butir("Tujuan")),
        ("sasaran", butir("Sasaran")),
        ("strategi", butir("Strategi pencapaian")),
        ("keterkaitan", paragraf("Keterkaitan dengan visi dan misi fakultas dan universitas")),
        ("dokumen", dokumen_daftar(bantuan="Mis. SK penetapan visi, misi, tujuan, dan strategi."))),
    "struktur-organisasi": halaman(
        ("bagan", foto_daftar("Bagan organisasi", 2)),
        ("pejabat", tabel("Pengelola program studi", [("jabatan", teks("Jabatan", wajib=True, maks=120)),
                                                     ("nama", teks("Nama", wajib=True, maks=150)),
                                                     ("periode", teks("Periode", maks=40))], 40)),
        ("tata_pamong", paragraf("Tata pamong dan tata kelola")),
        ("dokumen", dokumen_daftar(bantuan="Mis. SK struktur organisasi, uraian tugas."))),
    "penjaminan-mutu": halaman(
        ("uraian", uraian()),
        ("dokumen", dokumen_daftar("Dokumen mutu", "Standar mutu, SOP, laporan audit mutu internal, tindak lanjut."))),
    "kerja-sama": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Daftar kerja sama", [
            ("mitra", teks("Mitra", wajib=True, maks=200)),
            ("jenis", pilihan("Bidang", ("Pendidikan", "Penelitian", "Pengabdian kepada masyarakat"), wajib=True)),
            ("tingkat", pilihan("Tingkat", TINGKAT, wajib=True)),
            ("bentuk", teks("Bentuk kegiatan", maks=300)),
            ("mulai", tahun("Tahun mulai")),
            ("selesai", tahun("Tahun selesai")),
            ("manfaat", teks("Manfaat bagi program studi", maks=500)),
            ("bukti", dokumen("Bukti kerja sama", wajib=False))], 300))),
    # Akademik
    "kurikulum": halaman(
        ("struktur", paragraf("Struktur kurikulum")),
        ("mata_kuliah", tabel("Mata kuliah", [
            ("semester", bilangan("Semester", 1, 14, wajib=True)),
            ("kode", teks("Kode", maks=20)),
            ("nama", teks("Mata kuliah", wajib=True, maks=150)),
            ("sks", bilangan("SKS", 0, 30, wajib=True)),
            ("sifat", pilihan("Sifat", ("Wajib", "Pilihan"))),
            ("rps", dokumen("RPS", wajib=False))], 250)),
        ("dokumen", dokumen_daftar(bantuan="Mis. dokumen kurikulum, SK kurikulum."))),
    "peraturan": halaman(
        ("uraian", uraian()),
        ("dokumen", dokumen_daftar("Peraturan dan panduan", "Peraturan akademik, panduan pembimbingan akademik, panduan "
                                                            "tugas akhir."))),
    "jadwal": halaman(
        ("uraian", uraian()),
        ("jadwal", tabel("Jadwal", [("kegiatan", teks("Kegiatan", wajib=True, maks=200)),
                                    ("waktu", teks("Waktu", wajib=True, maks=100)),
                                    ("tempat", teks("Tempat", maks=150))], 100)),
        ("dokumen", dokumen_daftar("Jadwal dalam PDF"))),
    # Dosen dan Tendik
    "kelompok-keahlian": halaman(
        ("uraian", uraian()),
        ("daftar", kartu("Kelompok keahlian", [("nama", teks("Nama kelompok", wajib=True, maks=150)),
                                               ("ketua", teks("Ketua", maks=150)),
                                               ("anggota", teks("Anggota", maks=1000, panjang=True)),
                                               ("topik", teks("Topik penelitian", maks=1000, panjang=True))], 30))),
    "tendik": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Tenaga kependidikan", [("nama", teks("Nama", wajib=True, maks=150)),
                                                ("tugas", teks("Tugas atau jabatan", wajib=True, maks=150)),
                                                ("unit", teks("Unit kerja", maks=150))], 100))),
    "pengembangan-sdm": halaman(
        ("uraian", uraian()),
        ("studi_lanjut", tabel("Studi lanjut dosen", [("nama", teks("Nama dosen", wajib=True, maks=150)),
                                                      ("jenjang", teks("Jenjang", maks=30)),
                                                      ("bidang", teks("Bidang studi", maks=150)),
                                                      ("institusi", teks("Perguruan tinggi", maks=200)),
                                                      ("tahun", tahun("Tahun mulai"))], 100)),
        ("pelatihan", tabel("Pelatihan, seminar, dan sertifikasi", [("nama", teks("Nama dosen", wajib=True, maks=150)),
                                                                    ("kegiatan", teks("Kegiatan", wajib=True, maks=300)),
                                                                    ("tingkat", pilihan("Tingkat", TINGKAT)),
                                                                    ("tahun", tahun())], 200)),
        ("prestasi", tabel("Prestasi dosen", [("nama", teks("Nama dosen", wajib=True, maks=150)),
                                              ("prestasi", teks("Prestasi", wajib=True, maks=300)),
                                              ("tingkat", pilihan("Tingkat", TINGKAT)),
                                              ("tahun", tahun())], 200))),
    # Riset dan PkM
    "penelitian": halaman(
        ("agenda", paragraf("Agenda penelitian")),
        ("daftar", tabel("Penelitian", [("judul", teks("Judul", wajib=True, maks=300)),
                                        ("ketua", teks("Ketua", maks=150)),
                                        ("tahun", tahun(wajib=True)),
                                        ("dana", teks("Sumber dana", maks=150)),
                                        ("mahasiswa", centang("Melibatkan mahasiswa"))], 300))),
    "publikasi": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Publikasi", [("judul", teks("Judul", wajib=True, maks=300)),
                                       ("penulis", teks("Penulis", maks=300)),
                                       ("wadah", teks("Jurnal, prosiding, atau media", maks=200)),
                                       ("tahun", tahun(wajib=True)),
                                       ("tautan", url("Tautan (DOI/URL)"))], 500))),
    "pkm": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Pengabdian kepada masyarakat", [("judul", teks("Judul", wajib=True, maks=300)),
                                                          ("ketua", teks("Ketua", maks=150)),
                                                          ("mitra", teks("Mitra atau lokasi", maks=200)),
                                                          ("tahun", tahun(wajib=True)),
                                                          ("dana", teks("Sumber dana", maks=150)),
                                                          ("mahasiswa", centang("Melibatkan mahasiswa"))], 300))),
    "luaran": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Luaran penelitian dan pengabdian", [
            ("jenis", pilihan("Jenis", ("HKI (hak cipta, merek, desain)", "Paten", "Buku", "Teknologi tepat guna",
                                        "Produk", "Lainnya"), wajib=True)),
            ("judul", teks("Judul", wajib=True, maks=300)),
            ("tahun", tahun()),
            ("nomor", teks("Nomor atau identitas", maks=100)),
            ("tautan", url("Tautan"))], 300))),
    # Mahasiswa dan Alumni
    "penerimaan": halaman(
        ("uraian", uraian()),
        ("tautan", tautan_daftar("Tautan penerimaan", 5)),
        ("data", tabel("Data penerimaan", [("tahun", teks("Tahun akademik", wajib=True, maks=20)),
                                           ("daya_tampung", bilangan("Daya tampung")),
                                           ("pendaftar", bilangan("Pendaftar")),
                                           ("lulus", bilangan("Lulus seleksi")),
                                           ("baru", bilangan("Mahasiswa baru"))], 20))),
    "layanan": halaman(
        ("uraian", uraian()),
        ("layanan", kartu("Layanan mahasiswa", [("nama", teks("Nama layanan", wajib=True, maks=150)),
                                                ("uraian", paragraf("Uraian", maks=3000)),
                                                ("tautan", url("Tautan"))], 20))),
    "organisasi-prestasi": halaman(
        ("uraian", uraian()),
        ("organisasi", kartu("Organisasi kemahasiswaan", [("nama", teks("Nama organisasi", wajib=True, maks=150)),
                                                          ("uraian", teks("Uraian", maks=1000, panjang=True))], 30)),
        ("prestasi", tabel("Prestasi mahasiswa", [("kegiatan", teks("Kegiatan atau lomba", wajib=True, maks=200)),
                                                  ("tingkat", pilihan("Tingkat", TINGKAT, wajib=True)),
                                                  ("tahun", tahun(wajib=True)),
                                                  ("capaian", teks("Capaian", wajib=True, maks=150))], 300,
                                                  "Tanpa nama mahasiswa bila tidak perlu; jangan cantumkan NIM."))),
    "alumni": halaman(
        ("uraian", uraian()),
        ("tracer", tabel("Hasil studi pelacakan lulusan", [("tahun", tahun("Tahun lulus", wajib=True)),
                                                           ("lulusan", bilangan("Jumlah lulusan")),
                                                           ("terlacak", bilangan("Terlacak")),
                                                           ("masa_tunggu", teks("Rata-rata masa tunggu", maks=50)),
                                                           ("kesesuaian", teks("Kesesuaian bidang kerja", maks=50))], 30)),
        ("dokumen", dokumen_daftar("Laporan studi pelacakan"))),
    "survei-kepuasan": halaman(
        ("uraian", uraian()),
        ("hasil", tabel("Hasil survei kepuasan", [
            ("survei", pilihan("Responden", ("Mahasiswa", "Alumni", "Pengguna lulusan", "Dosen", "Tenaga kependidikan",
                                             "Mitra", "Lainnya"), wajib=True)),
            ("tahun", tahun()),
            ("aspek", teks("Aspek", wajib=True, maks=200)),
            ("sangat_baik", persen("Sangat baik (%)")),
            ("baik", persen("Baik (%)")),
            ("cukup", persen("Cukup (%)")),
            ("kurang", persen("Kurang (%)"))], 200)),
        ("tindak_lanjut", paragraf("Tindak lanjut")),
        ("dokumen", dokumen_daftar("Laporan survei"))),
    # Fasilitas
    "laboratorium": halaman(
        ("uraian", uraian()),
        ("daftar", kartu("Laboratorium dan studio", [("nama", teks("Nama", wajib=True, maks=150)),
                                                     ("fungsi", teks("Fungsi", maks=300)),
                                                     ("kapasitas", bilangan("Kapasitas (orang)")),
                                                     ("peralatan", teks("Peralatan utama", maks=1000, panjang=True)),
                                                     ("foto", foto(wajib=False)),
                                                     ("sop", dokumen("SOP penggunaan", wajib=False))], 40))),
    "ruang": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Ruang", [("jenis", teks("Jenis ruang", wajib=True, maks=100)),
                                   ("jumlah", bilangan("Jumlah")),
                                   ("kapasitas", bilangan("Kapasitas per ruang")),
                                   ("keterangan", teks("Keterangan", maks=300))], 50)),
        ("foto", foto_daftar("Foto ruang", 8))),
    "perpustakaan": halaman(
        ("uraian", uraian()),
        ("tautan", tautan_daftar("Tautan sumber referensi"))),
    "sistem-informasi": halaman(
        ("uraian", uraian()),
        ("daftar", tabel("Sistem informasi", [("nama", teks("Nama sistem", wajib=True, maks=150)),
                                              ("fungsi", teks("Fungsi", maks=300)),
                                              ("tautan", url("Tautan"))], 50))),
}


# ------------------------------------------------------------------ checking stored content

def _teks_kaya_masalah(v):
    for m in TAUTAN.finditer(v):
        if m.group(2) is not None and not POLA_URL.match(m.group(2)):
            return "tautan harus berupa alamat lengkap yang diawali https://"
    return None


def _media_sah(rekam, kode):
    if not isinstance(rekam, dict):
        return False
    if "url" in rekam:
        return media.url_sah(rekam["url"])
    jalur = rekam.get("jalur")
    return media.jalur_sah(jalur) and jalur.split("/")[0] == kode


def _periksa(node, v, tempat, kode, masalah):
    j = node["jenis"]
    di = "%s: " % tempat if tempat else ""
    if j == "objek":
        if v is None:
            v = {}
        if not isinstance(v, dict):
            masalah.append("%sbukan objek" % di)
            return
        for kunci, n in node["bidang"]:
            label = n.get("label") or "Uraian"
            _periksa(n, v.get(kunci), "%s, %s" % (tempat, label) if tempat else label, kode, masalah)
        return
    if j == "daftar":
        if v is None:
            return
        if not isinstance(v, list):
            masalah.append("%sbukan daftar" % di)
            return
        if len(v) > node["maks"]:
            masalah.append("%spaling banyak %d" % (di, node["maks"]))
        isi = node["isi"]
        kata = "baris" if node["tampil"] == "tabel" else "butir"
        for i, x in enumerate(v[:node["maks"]], 1):
            if isi["jenis"] == "objek":
                if not isinstance(x, dict):
                    masalah.append("%s%s %d bukan objek" % (di, kata, i))
                    continue
                for kunci, n in isi["bidang"]:
                    _periksa(n, x.get(kunci), "%s %s %d, %s" % (tempat, kata, i, n["label"]), kode, masalah)
            else:
                _periksa(isi, x, "%s %s %d" % (tempat, kata, i), kode, masalah)
        return
    kosong_ = v is None or (isinstance(v, str) and not v.strip())
    if kosong_:
        if node.get("wajib"):
            masalah.append("%swajib diisi" % di)
        return
    if j == "teks":
        if not isinstance(v, str):
            masalah.append("%sharus teks" % di)
        elif len(v) > node["maks"]:
            masalah.append("%sterlalu panjang (maksimal %d karakter)" % (di, node["maks"]))
        elif KONTROL.search(v) or (not node["panjang"] and "\n" in v):
            masalah.append("%smemuat karakter yang tidak boleh" % di)
        else:
            if node["kaya"]:
                m = _teks_kaya_masalah(v)
                if m:
                    masalah.append(di + m)
            judi = saringan_spam.cari(v)
            if judi:
                masalah.append("%smemuat teks judi (%s)" % (di, judi))
    elif j == "bilangan":
        if isinstance(v, bool) or not isinstance(v, int):
            masalah.append("%sharus angka bulat" % di)
        elif not node["minimum"] <= v <= node["maksimum"]:
            masalah.append("%sharus antara %d dan %d" % (di, node["minimum"], node["maksimum"]))
    elif j == "persen":
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 100 or round(v, 2) != v:
            masalah.append("%sharus angka 0 sampai 100, paling banyak dua angka di belakang koma" % di)
    elif j == "url":
        if not isinstance(v, str) or len(v) > MAKS_URL or not POLA_URL.match(v):
            masalah.append("%sharus alamat lengkap yang diawali https://" % di)
    elif j == "pilihan":
        if v not in node["opsi"]:
            masalah.append("%spilihan tidak dikenal" % di)
    elif j == "centang":
        if not isinstance(v, bool):
            masalah.append("%sharus ya atau tidak" % di)
    elif j == "dokumen":
        if not (isinstance(v, dict) and v.get("jenis") == "pdf" and _media_sah(v, kode)
                and isinstance(v.get("ukuran"), int) and isinstance(v.get("halaman"), int)):
            masalah.append("%sberkas PDF tidak sah" % di)
    elif j == "foto":
        varian = v.get("varian") if isinstance(v, dict) else None
        if not (isinstance(v, dict) and v.get("jenis") == "gambar" and isinstance(varian, dict) and varian
                and all(isinstance(x, dict) and _media_sah(x, kode) and isinstance(x.get("lebar"), int)
                        and isinstance(x.get("tinggi"), int) for x in varian.values())):
            masalah.append("%sfoto tidak sah" % di)
        elif not isinstance(v.get("alt"), str) or not v["alt"].strip() or len(v["alt"]) > 200 or saringan_spam.cari(v["alt"]):
            masalah.append("%steks alternatif foto wajib diisi (maksimal 200 karakter, tanpa teks judi)" % di)


def periksa(id_halaman, isi, kode):
    """Problems with a page's content (empty list when it may be stored)."""
    templat = TEMPLAT.get(id_halaman)
    if templat is None:
        return ["halaman %r tidak punya templat isi" % (id_halaman,)]
    if not POLA_KODE.match(kode or ""):
        return ["kode prodi tidak sah"]
    masalah = []
    _periksa(templat, isi, "", kode, masalah)
    return masalah


def kosong(node, v):
    """True when a value holds nothing that would show on the site."""
    j = node["jenis"]
    if v is None:
        return True
    if j == "objek":
        return not isinstance(v, dict) or all(kosong(n, v.get(k)) for k, n in node["bidang"])
    if j == "daftar":
        return not v
    if j == "centang":
        return v is not True
    if isinstance(v, str):
        return not v.strip()
    return False


def media_isi(node, v):
    """Every stored file a value refers to: [record, ...] (photo variants and PDFs)."""
    hasil = []
    if v is None:
        return hasil
    j = node["jenis"]
    if j == "objek" and isinstance(v, dict):
        for k, n in node["bidang"]:
            hasil += media_isi(n, v.get(k))
    elif j == "daftar" and isinstance(v, list):
        for x in v:
            hasil += media_isi(node["isi"], x)
    elif j == "dokumen" and isinstance(v, dict):
        hasil.append(v)
    elif j == "foto" and isinstance(v, dict):
        hasil += list((v.get("varian") or {}).values())
    return hasil


# ------------------------------------------------------------------ what the site shows

def _tebal(teks):
    """Escaped text with **bold** as <strong> (the markup is applied to the escaped text, so it adds no other HTML)."""
    return Markup(TEBAL.sub(r"<strong>\1</strong>", str(escape(teks))))


def _baris(teks):
    """One line: links ([text](https://...) and bare https:// addresses) and bold; everything else escaped."""
    hasil, awal = [], 0
    for m in TAUTAN.finditer(teks):
        hasil.append(_tebal(teks[awal:m.start()]))
        if m.group(1) is not None:
            if POLA_URL.match(m.group(2)):
                hasil.append(Markup('<a href="%s">%s</a>') % (m.group(2), _tebal(m.group(1))))
            else:                                       # never stored (periksa); shown as plain text all the same
                hasil.append(_tebal(m.group(0)))
            awal = m.end()
        else:
            alamat = m.group(3).rstrip(".,;:!?)")
            hasil.append(Markup('<a href="%s">%s</a>') % (alamat, alamat) if POLA_URL.match(alamat) else escape(alamat))
            awal = m.start() + len(alamat)
    hasil.append(_tebal(teks[awal:]))
    return Markup("").join(hasil)


def teks_kaya(teks):
    """Paragraphs (separated by an empty line), "- " lists, line breaks, links and bold; never raw HTML."""
    blok = []
    for bagian in re.split(r"\n\s*\n", (teks or "").strip()):
        baris = [b.strip() for b in bagian.splitlines() if b.strip()]
        if not baris:
            continue
        if all(b.startswith("- ") for b in baris):
            blok.append(Markup("<ul>%s</ul>") % Markup("").join(Markup("<li>%s</li>") % _baris(b[2:]) for b in baris))
        else:
            blok.append(Markup("<p>%s</p>") % Markup("<br>").join(_baris(b) for b in baris))
    return Markup("\n").join(blok)


def angka(v, format="angka"):
    """1234 -> '1.234'; a year stays '2025'; 87.5 -> '87,5'."""
    if format == "tahun":
        return str(v)
    if isinstance(v, float) and not v.is_integer():
        return ("%.2f" % v).rstrip("0").replace(".", ",")
    return "{:,}".format(int(v)).replace(",", ".")


def sel(node, v):
    """One value as shown in a table cell or a card: {"jenis": "teks"|"tautan"|"dokumen"|"ya"|"kosong", ...}."""
    j = node["jenis"]
    if kosong(node, v):
        return {"jenis": "kosong"}
    if j == "teks":
        return {"jenis": "teks", "html": teks_kaya(v) if node["kaya"] else Markup("<br>").join(escape(b) for b in v.splitlines())}
    if j == "bilangan":
        return {"jenis": "teks", "html": escape(angka(v, node["format"]))}
    if j == "persen":
        return {"jenis": "teks", "html": escape(angka(v) + "%")}
    if j == "url":
        pendek = re.sub(r"^https://(www\.)?", "", v).rstrip("/")
        return {"jenis": "tautan", "alamat": v, "label": pendek if len(pendek) <= 40 else pendek[:39] + "…"}
    if j == "pilihan":
        return {"jenis": "teks", "html": escape(v)}
    if j == "centang":
        return {"jenis": "ya"}
    if j == "dokumen":
        return {"jenis": "dokumen", "rekam": v}
    return {"jenis": "kosong"}


def _paragraf_polos(teks):
    return Markup("<p>%s</p>") % Markup("<br>").join(escape(b) for b in teks.splitlines() if b.strip())


def tampilan(id_halaman, isi, media_ok=lambda rekam: True):
    """The sections the site shows, in order, without empty ones: ([section, ...], files missing).

    A section is {"jenis", "judul", "id", ...}: "paragraf" (html), "daftar" (butir, bernomor), "tabel" (kolom, baris of
    cells), "kartu" (kartu: judul, rincian [(label, cell)], uraian [(label, html)], foto, dokumen [(label, record)]),
    "dokumen" (dokumen: judul, tahun, keterangan, rekam), "galeri" (foto: rekam, keterangan), "tautan" (label, alamat).
    Extra sections become "paragraf" sections with their own heading.

    media_ok(record) publishes a stored file and says whether it is there. A missing file is counted; the item it
    belongs to is left out when the file is required (a document of a document list, a photo of a gallery), and only
    the file is left out when it is optional (the proof of a partnership, the SOP of a laboratory)."""
    templat = TEMPLAT[id_halaman]
    hasil, hilang = [], [0]
    isi = isi if isinstance(isi, dict) else {}

    def tersedia(node, nilai):
        ok = all(media_ok(r) for r in media_isi(node, nilai))
        if not ok:
            hilang[0] += 1
        return ok

    def butir_tampil(isi_node, x):
        """The item with its unavailable optional files removed, or None when a required file is unavailable."""
        x = dict(x)
        for k, n in isi_node["bidang"]:
            if n["jenis"] in ("dokumen", "foto") and not kosong(n, x.get(k)) and not tersedia(n, x[k]):
                if n.get("wajib"):
                    return None
                x[k] = None
        return x

    for kunci, node in templat["bidang"]:
        v = isi.get(kunci)
        if kosong(node, v):
            continue
        dasar = {"judul": node["label"], "id": "bagian-%s" % kunci.replace("_", "-")}
        if node["jenis"] == "teks":
            hasil.append(dict(dasar, jenis="paragraf", html=teks_kaya(v)))
            continue
        tampil, isi_node = node["tampil"], node["isi"]
        if isi_node["jenis"] != "objek":                    # a list of lines
            hasil.append(dict(dasar, jenis="daftar", bernomor=node["bernomor"],
                              butir=[_baris(x) for x in v if not kosong(isi_node, x)]))
            continue
        item = [b for b in (butir_tampil(isi_node, x) for x in v if not kosong(isi_node, x)) if b is not None]
        bidang = isi_node["bidang"]
        if not item:
            continue
        if tampil == "tabel":
            hasil.append(dict(dasar, jenis="tabel", kolom=[n["label"] for _k, n in bidang],
                              baris=[[sel(n, x.get(k)) for k, n in bidang] for x in item]))
        elif tampil == "kartu":
            kartu_ = []
            for x in item:
                k = {"judul": x.get(bidang[0][0]) or "", "rincian": [], "uraian": [], "foto": None, "dokumen": []}
                for kunci_b, n in bidang[1:]:
                    nilai = x.get(kunci_b)
                    if kosong(n, nilai):
                        continue
                    if n["jenis"] == "foto":
                        k["foto"] = nilai
                    elif n["jenis"] == "dokumen":
                        k["dokumen"].append((n["label"], nilai))
                    elif n["jenis"] == "teks" and n["panjang"]:
                        k["uraian"].append((n["label"], teks_kaya(nilai) if n["kaya"] else _paragraf_polos(nilai)))
                    else:
                        k["rincian"].append((n["label"], sel(n, nilai)))
                kartu_.append(k)
            hasil.append(dict(dasar, jenis="kartu", kartu=kartu_))
        elif tampil == "dokumen":
            hasil.append(dict(dasar, jenis="dokumen", dokumen=[
                {"judul": x.get("judul"), "tahun": x.get("tahun"), "keterangan": x.get("keterangan") or "",
                 "rekam": x.get("berkas")} for x in item if x.get("berkas")]))
        elif tampil == "galeri":
            hasil.append(dict(dasar, jenis="galeri", foto=[{"rekam": x.get("berkas"), "keterangan": x.get("keterangan") or ""}
                                                         for x in item if x.get("berkas")]))
        elif tampil == "tautan":
            hasil.append(dict(dasar, jenis="tautan", tautan=[{"label": x.get("label"), "alamat": x.get("alamat")} for x in item]))
        elif tampil == "bagian":
            for i, x in enumerate(item, 1):
                hasil.append({"jenis": "paragraf", "judul": x.get("judul") or "", "id": "%s-%d" % (dasar["id"], i),
                              "html": teks_kaya(x.get("isi") or "")})
    return [b for b in hasil if b.get("html") or b.get("butir") or b.get("baris") or b.get("kartu") or b.get("dokumen")
            or b.get("foto") or b.get("tautan")], hilang[0]


# ------------------------------------------------------------------ stored content

def nama_berkas(kode, id_halaman):
    if not POLA_KODE.match(kode or "") or id_halaman not in TEMPLAT:
        raise GagalIsi("prodi atau halaman tidak dikenal")
    return "prodi/%s/halaman-%s" % (kode, id_halaman)


def baca(kode, id_halaman):
    data = lokasi.baca(nama_berkas(kode, id_halaman))
    return data if isinstance(data, dict) else {"versi": 0, "terbit": None, "draf": None}


def terbit(kode, id_halaman):
    """The published content of a page, or None."""
    t = baca(kode, id_halaman).get("terbit")
    return t.get("isi") if isinstance(t, dict) else None


def terisi(kode, id_halaman):
    """True when the page shows content of its own on the site (published, valid, not empty)."""
    isi = terbit(kode, id_halaman)
    return isi is not None and not periksa(id_halaman, isi, kode) and not kosong(TEMPLAT[id_halaman], isi)


def _sekarang():
    return datetime.datetime.now().isoformat(timespec="seconds")


def terbitkan(kode, id_halaman, isi, oleh, versi=None):
    """Publish content (checked first; nothing is written when it fails). versi: the version the change was made
    from; a different stored version means someone else saved in between, and the save is refused. Returns the new
    version."""
    berkas = nama_berkas(kode, id_halaman)
    masalah = periksa(id_halaman, isi, kode)
    if masalah:
        raise GagalIsi("; ".join(masalah[:20]))
    data = baca(kode, id_halaman)
    if versi is not None and versi != data.get("versi", 0):
        raise GagalIsi("halaman ini baru saja diubah orang lain; muat ulang lalu ulangi perubahan Anda")
    data["versi"] = data.get("versi", 0) + 1
    data["terbit"] = {"isi": isi, "oleh": oleh, "waktu": _sekarang()}
    lokasi.tulis(berkas, data, oleh, "Isi halaman", "terbitkan %s" % id_halaman)
    return data["versi"]


def tarik(kode, id_halaman, oleh):
    """Take a page's content off the site (it is kept in the history). Returns the new version."""
    berkas = nama_berkas(kode, id_halaman)
    data = baca(kode, id_halaman)
    if data.get("terbit") is None:
        return data.get("versi", 0)
    data["versi"] = data.get("versi", 0) + 1
    data["terbit"] = None
    lokasi.tulis(berkas, data, oleh, "Isi halaman", "tarik %s" % id_halaman)
    return data["versi"]


# ------------------------------------------------------------------ sample content (looking at the pages; tests)

def _wajib_tanpa_berkas(node, v):
    """True when an item of a list lacks a required file."""
    return node["jenis"] == "objek" and isinstance(v, dict) and any(
        n["jenis"] in ("dokumen", "foto") and n.get("wajib") and not v.get(k) for k, n in node["bidang"])


def _contoh(node, n, berkas_contoh):
    j = node["jenis"]
    if j == "objek":
        hasil = {}
        for k, sub in node["bidang"]:
            v = _contoh(sub, n, berkas_contoh)
            if v is not None:
                hasil[k] = v
        return hasil
    if j == "daftar":
        hasil = [_contoh(node["isi"], n, berkas_contoh) for _i in range(min(n, node["maks"]))]
        return [v for v in hasil if v is not None and not _wajib_tanpa_berkas(node["isi"], v)]
    if j == "teks":
        if node["kaya"]:
            return ("%s %s. Paragraf contoh dengan **huruf tebal** dan [tautan ke www](https://www.unsrat.ac.id/).\n\n"
                    "- butir pertama\n- butir kedua" % (CONTOH, node["label"] or "Uraian"))[:node["maks"]]
        return ("%s %s" % (CONTOH, node["label"]))[:node["maks"]]
    if j == "bilangan":
        return 2025 if node["format"] == "tahun" else max(node["minimum"], min(node["maksimum"], 12))
    if j == "persen":
        return 42.5
    if j == "url":
        return "https://www.unsrat.ac.id/"
    if j == "pilihan":
        return node["opsi"][0]
    if j == "centang":
        return True
    if j in ("dokumen", "foto"):
        return berkas_contoh(j) if berkas_contoh else None
    return None


def isi_contoh(id_halaman, n=3, berkas_contoh=None):
    """Content for every field of a page, marked [CONTOH]: n items per list. berkas_contoh(jenis) gives a stored file
    record ("dokumen" or "foto"); without it, list items that need a file are left out."""
    return _contoh(TEMPLAT[id_halaman], n, berkas_contoh)


# ------------------------------------------------------------------ command line

def main(argv=None):
    ap = argparse.ArgumentParser(description="Isi halaman wajib dan opsional prodi")
    sub = ap.add_subparsers(dest="perintah", required=True)
    for nama, bantuan in (("daftar", "halaman mana yang sudah berisi"), ("contoh", "isi contoh [CONTOH] ke halaman kosong"),
                          ("tarik", "turunkan isi dari situs")):
        p = sub.add_parser(nama, help=bantuan)
        p.add_argument("--prodi", required=True, help="kode PDDIKTI")
        if nama == "tarik":
            p.add_argument("--halaman", help="id halaman (bawaan: semua)")
    a = ap.parse_args(argv)
    kode = a.prodi
    if not POLA_KODE.match(kode):
        print("kode prodi tidak sah")
        return 1
    if a.perintah == "daftar":
        for id_ in TEMPLAT:
            print("%-22s %s" % (id_, "berisi" if terisi(kode, id_) else "kosong"))
        return 0
    if a.perintah == "contoh":
        if os.environ.get("PRODI_MODE") == "produksi":
            print("Isi contoh tidak boleh dipakai di produksi.")
            return 1
        n = 0
        for id_ in TEMPLAT:
            if terbit(kode, id_) is None:
                terbitkan(kode, id_, isi_contoh(id_), "contoh")
                n += 1
        print("%d halaman diisi contoh; bangun ulang prodi ini untuk melihatnya." % n)
        return 0
    halaman_ = [a.halaman] if a.halaman else list(TEMPLAT)
    for id_ in halaman_:
        try:
            tarik(kode, id_, "baris-perintah")
        except GagalIsi as e:
            print("GAGAL %s: %s" % (id_, e))
            return 1
    print("%d halaman ditarik; bangun ulang prodi ini." % len(halaman_))
    return 0


if __name__ == "__main__":
    sys.exit(main())
