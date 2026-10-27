# -*- coding: utf-8 -*-
"""The content of a programme's own pages (Fase 2, K-P23): the 22 required accreditation pages ("wajib") and the 2
optional ones of the master menu (platform/template/menu.json), and the documents of the accreditation page (langkah 4,
K-P29: its status comes from the official data, the programme adds the certificate, the decree and other public
documents).

Every page has a content template (TEMPLAT): sections of fields, lists and tables that follow the page's description in
the menu and what accreditation asks for, plus free extra sections at the end. The template drives:
- periksa(): what may be stored: types, lengths, choices, links to https:// addresses only, uploaded files of this
  programme only, no gambling text;
- tampilan(): what the builder shows (headings, paragraphs, lists, tables, cards, documents, photos, links), as plain
  data for the Jinja2 templates. Text is escaped here; only the limited markup ([text](https://...), **bold**, "- "
  lists, bare https:// addresses) becomes HTML;
- the form of the admin (langkah 2: the form editor of www's superadmin, site/admin/editor.py, adapted). The nodes use
  the same vocabulary as that editor for this reason.

Stored in prodi/<kode>/halaman-<id>.json (lokasi.py):
    {"versi": n, "terbit": {"isi": {...}, "oleh", "waktu"} or null,
     "draf": {"isi": {...}, "status": "draf" | "menunggu" | "dikembalikan", "oleh", "waktu", "diajukan": {"oleh",
              "waktu"}, "catatan": {"isi", "oleh", "waktu"}} or null,
     "diubah": {"oleh", "waktu"}}
The site shows "terbit" only. The admin's editor (admin/isi_admin.py) works on the draft (K-P24, K-P27): an operator
submits it (ajukan), a programme admin publishes it (terbitkan) or sends it back with a note (kembalikan), and can take
published content off the site (tarik). Every change counts up "versi", and a change made from an older version is
refused, so two people editing a page never overwrite each other silently. Every deliberate action (save, submit,
publish, send back, withdraw, discard, an old version made the draft) keeps the previous content in the history. Keys
a template does not know are kept, so a template changed after the pilot never loses content.

    python3 platform/isi_halaman.py daftar --prodi <kode>       which pages have published content
    python3 platform/isi_halaman.py contoh --prodi <kode>       fill every empty page with [CONTOH] content, to look at
                                                                the pages (never over real content, never in production)
    python3 platform/isi_halaman.py tarik --prodi <kode> [--halaman <id>]   take a page (or all) off the site
"""
from __future__ import print_function

import argparse
import datetime
import json
import os
import re
import sys
import threading

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
    # the accreditation page ("otomatis"): its status from the official data, these documents from the programme
    "akreditasi": halaman(
        ("dokumen", dokumen_daftar("Dokumen akreditasi", "Sertifikat akreditasi, SK akreditasi, dan ringkasan hasil akreditasi "
                                                         "yang boleh dipublikasikan. Jangan unggah LED, LKPS, atau dokumen "
                                                         "lain yang memuat data pribadi.", 20)),
        ("uraian", paragraf("Keterangan", maks=3000))),
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


def _periksa(node, v, tempat, kode, masalah, jalur=""):
    """Append (path, where, problem) for every problem of a value. path: the dotted field name of the form
    ("kerja_sama.0.mitra"); where: the same in words ("Daftar kerja sama baris 1, Mitra")."""
    j = node["jenis"]

    def salah(pesan):
        masalah.append((jalur, tempat, pesan))

    if j == "objek":
        if v is None:
            v = {}
        if not isinstance(v, dict):
            salah("bukan objek")
            return
        for kunci, n in node["bidang"]:
            label = n.get("label") or "Uraian"
            _periksa(n, v.get(kunci), "%s, %s" % (tempat, label) if tempat else label, kode, masalah,
                     "%s.%s" % (jalur, kunci) if jalur else kunci)
        return
    if j == "daftar":
        if v is None:
            return
        if not isinstance(v, list):
            salah("bukan daftar")
            return
        if len(v) > node["maks"]:
            salah("paling banyak %d" % node["maks"])
        isi = node["isi"]
        kata = "baris" if node["tampil"] == "tabel" else "butir"
        for i, x in enumerate(v[:node["maks"]]):
            sub, di = "%s.%d" % (jalur, i), "%s %s %d" % (tempat, kata, i + 1)
            if isi["jenis"] == "objek":
                if not isinstance(x, dict):
                    masalah.append((sub, di, "bukan objek"))
                    continue
                for kunci, n in isi["bidang"]:
                    _periksa(n, x.get(kunci), "%s, %s" % (di, n["label"]), kode, masalah, "%s.%s" % (sub, kunci))
            else:
                _periksa(isi, x, di, kode, masalah, sub)
        return
    if v is None or (isinstance(v, str) and not v.strip()):
        if node.get("wajib"):
            salah("wajib diisi")
        return
    if j == "teks":
        if not isinstance(v, str):
            salah("harus teks")
        elif len(v) > node["maks"]:
            salah("terlalu panjang (maksimal %d karakter)" % node["maks"])
        elif KONTROL.search(v) or (not node["panjang"] and "\n" in v):
            salah("memuat karakter yang tidak boleh")
        else:
            if node["kaya"]:
                m = _teks_kaya_masalah(v)
                if m:
                    salah(m)
            judi = saringan_spam.cari(v)
            if judi:
                salah("memuat teks judi (%s)" % judi)
    elif j == "bilangan":
        if isinstance(v, bool) or not isinstance(v, int):
            salah("harus angka bulat")
        elif not node["minimum"] <= v <= node["maksimum"]:
            salah("harus antara %d dan %d" % (node["minimum"], node["maksimum"]))
    elif j == "persen":
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 100 or round(v, 2) != v:
            salah("harus angka 0 sampai 100, paling banyak dua angka di belakang koma")
    elif j == "url":
        if not isinstance(v, str) or len(v) > MAKS_URL or not POLA_URL.match(v):
            salah("harus alamat lengkap yang diawali https://")
    elif j == "pilihan":
        if v not in node["opsi"]:
            salah("pilihan tidak dikenal")
    elif j == "centang":
        if not isinstance(v, bool):
            salah("harus ya atau tidak")
    elif j == "dokumen":
        if not (isinstance(v, dict) and v.get("jenis") == "pdf" and _media_sah(v, kode)
                and isinstance(v.get("ukuran"), int) and isinstance(v.get("halaman"), int)):
            salah("berkas PDF tidak sah")
    elif j == "foto":
        varian = v.get("varian") if isinstance(v, dict) else None
        if not (isinstance(v, dict) and v.get("jenis") == "gambar" and isinstance(varian, dict) and varian
                and all(isinstance(x, dict) and _media_sah(x, kode) and isinstance(x.get("lebar"), int)
                        and isinstance(x.get("tinggi"), int) for x in varian.values())):
            salah("foto tidak sah")
        elif not isinstance(v.get("alt"), str) or not v["alt"].strip() or len(v["alt"]) > 200 or saringan_spam.cari(v["alt"]):
            salah("teks alternatif foto wajib diisi (maksimal 200 karakter, tanpa teks judi)")


def _semua_masalah(id_halaman, isi, kode):
    templat = TEMPLAT.get(id_halaman)
    if templat is None:
        return [("", "", "halaman %r tidak punya templat isi" % (id_halaman,))]
    if not POLA_KODE.match(kode or ""):
        return [("", "", "kode prodi tidak sah")]
    masalah = []
    _periksa(templat, isi, "", kode, masalah)
    return masalah


def periksa(id_halaman, isi, kode):
    """Problems with a page's content, each saying where it is (empty list when it may be stored)."""
    return ["%s: %s" % (t, p) if t else p for _j, t, p in _semua_masalah(id_halaman, isi, kode)]


def daftar_masalah(id_halaman, isi, kode):
    """Every problem as (form field name, where in words, problem); the field name is "" for the page itself."""
    return _semua_masalah(id_halaman, isi, kode)


def periksa_jalur(id_halaman, isi, kode):
    """{form field name: its first problem}, for marking the fields of the editor ("" = the page itself)."""
    hasil = {}
    for j, _t, p in _semua_masalah(id_halaman, isi, kode):
        hasil.setdefault(j, p)
    return hasil


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

MAKS_DRAF = 2 * 1024 * 1024    # bytes of one page's draft as JSON; a full 300-row table with long texts stays under 1 MB
MAKS_CATATAN = 500             # an admin's note when sending a draft back (as for announcements)
STATUS_DRAF = ("draf", "menunggu", "dikembalikan")
NAMA_STATUS_DRAF = {"draf": "masih draf", "menunggu": "menunggu persetujuan", "dikembalikan": "dikembalikan"}
# reading a page, checking its version and writing it happen under this lock, so two saves of the admin (one process,
# several threads) can never both pass the check
_KUNCI = threading.Lock()


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


def draf(data):
    """The draft in a page's stored data (baca()): {"isi", "status", "oleh", "waktu"}, or None."""
    d = data.get("draf")
    return d if isinstance(d, dict) and isinstance(d.get("isi"), dict) else None


def isi_kerja(data):
    """What the editor starts from: the draft, else the published content, else nothing yet."""
    t = data.get("terbit")
    return (draf(data) or (t if isinstance(t, dict) and isinstance(t.get("isi"), dict) else {"isi": {}}))["isi"]


def terisi(kode, id_halaman):
    """True when the page shows content of its own on the site (published, valid, not empty)."""
    isi = terbit(kode, id_halaman)
    return isi is not None and not periksa(id_halaman, isi, kode) and not kosong(TEMPLAT[id_halaman], isi)


def _sekarang():
    return datetime.datetime.now().isoformat(timespec="seconds")


def cek_versi(data, versi):
    """versi: the version a change was made from; any other stored version means someone saved in between."""
    if versi is not None and versi != data.get("versi", 0):
        d = data.get("diubah") if isinstance(data.get("diubah"), dict) else {}
        oleh = " oleh %s (%s)" % (d["oleh"], str(d.get("waktu", "")).replace("T", " ")) if d.get("oleh") else " orang lain"
        raise GagalIsi("halaman ini baru saja diubah%s; muat ulang lalu ulangi perubahan Anda" % oleh)


def _tulis(kode, id_halaman, data, oleh, aksi, riwayat=True):
    """Store a page's data under a new version; riwayat: keep the previous content in the history first."""
    data["versi"] = data.get("versi", 0) + 1
    data["diubah"] = {"oleh": oleh, "waktu": _sekarang()}
    berkas = nama_berkas(kode, id_halaman)
    if riwayat:
        lokasi.tulis(berkas, data, oleh, "Isi halaman", "%s %s" % (aksi, id_halaman))
    else:
        lokasi.tulis_json(lokasi.path_data(berkas), data)
    return data["versi"]


def terbitkan(kode, id_halaman, isi, oleh, versi=None, dari_draf=False):
    """Publish content (checked first; nothing is written when it fails). versi: see cek_versi. dari_draf: the content
    is the page's draft as the editor holds it (a programme admin publishing, K-P24): the draft is done with, and who
    submitted it is kept with the published content. Returns the new version."""
    nama_berkas(kode, id_halaman)
    masalah = periksa(id_halaman, isi, kode)
    if masalah:
        raise GagalIsi("%d isian perlu diperbaiki: %s" % (len(masalah), "; ".join(masalah[:5])))
    if dari_draf and kosong(TEMPLAT[id_halaman], isi):
        raise GagalIsi("halaman ini belum berisi apa pun untuk diterbitkan")
    with _KUNCI:
        data = baca(kode, id_halaman)
        cek_versi(data, versi)
        data["terbit"] = {"isi": isi, "oleh": oleh, "waktu": _sekarang()}
        if dari_draf:
            d = draf(data)
            if d and d.get("diajukan"):
                data["terbit"]["diajukan"] = d["diajukan"]
            data["draf"] = None
        return _tulis(kode, id_halaman, data, oleh, "terbitkan")


def tarik(kode, id_halaman, oleh, versi=None, isi=None):
    """Take a page's content off the site; the page says again that the programme is filling it. The content stays in
    the history, and becomes the draft when there is none, so the editor still holds it. isi: what the editor holds
    (it becomes the draft). Returns the new version."""
    if isi is not None:
        _boleh_disimpan(kode, id_halaman, isi)
    with _KUNCI:
        data = baca(kode, id_halaman)
        if data.get("terbit") is None:
            return data.get("versi", 0)
        cek_versi(data, versi)
        if isi is not None:
            data["draf"] = _draf_dari(isi, oleh, draf(data))
        elif draf(data) is None and isinstance(data["terbit"], dict) and isinstance(data["terbit"].get("isi"), dict):
            data["draf"] = {"isi": data["terbit"]["isi"], "status": "draf", "oleh": oleh, "waktu": _sekarang()}
        data["terbit"] = None
        return _tulis(kode, id_halaman, data, oleh, "tarik")


def node_jalur(templat, jalur):
    """The template node of a form field name ("kerja_sama.0.bukti"), or None."""
    node = templat
    for p in jalur.split(".") if isinstance(jalur, str) and jalur else [None]:
        if node["jenis"] == "objek":
            node = dict(node["bidang"]).get(p)
        elif node["jenis"] == "daftar" and isinstance(p, str) and p.isdigit():
            node = node["isi"]
        else:
            return None
        if node is None:
            return None
    return node


def _berkas_sendiri(node, v, kode):
    """True when every file a value refers to is a stored file of this programme."""
    j = node["jenis"]
    if v is None:
        return True
    if j == "objek":
        return not isinstance(v, dict) or all(_berkas_sendiri(n, v.get(k), kode) for k, n in node["bidang"])
    if j == "daftar":
        return not isinstance(v, list) or all(_berkas_sendiri(node["isi"], x, kode) for x in v)
    if j == "dokumen":
        return _media_sah(v, kode)
    if j == "foto":
        varian = v.get("varian") if isinstance(v, dict) else None
        return isinstance(varian, dict) and bool(varian) and all(_media_sah(x, kode) for x in varian.values())
    return True


def simpan_draf(kode, id_halaman, isi, oleh, versi=None, riwayat=True, dihapus=None):
    """Store content as the page's draft; the site keeps showing the published content. A draft may be unfinished
    (required fields empty, values not valid yet): the checks apply when it is published. Its files must be the
    programme's own, and it may not be larger than MAKS_DRAF. versi: see cek_versi. riwayat: keep the previous content
    in the history (an explicit save); the editor's list buttons and preview store without it, so the history holds
    saves rather than every click. dihapus: the list item the editor just removed ({"jalur", "indeks", "nilai"}),
    offered back until the next save. Returns the new version."""
    _boleh_disimpan(kode, id_halaman, isi, dihapus)
    with _KUNCI:
        data = baca(kode, id_halaman)
        cek_versi(data, versi)
        data["draf"] = _draf_dari(isi, oleh, draf(data))
        if dihapus:
            data["draf"]["dihapus"] = dihapus
        return _tulis(kode, id_halaman, data, oleh, "simpan draf", riwayat)


def buang_draf(kode, id_halaman, oleh, versi=None):
    """Drop the draft (it stays in the history); the editor starts again from the published content. Returns the
    new version."""
    with _KUNCI:
        data = baca(kode, id_halaman)
        if data.get("draf") is None:
            return data.get("versi", 0)
        cek_versi(data, versi)
        data["draf"] = None
        return _tulis(kode, id_halaman, data, oleh, "buang draf")


def _boleh_disimpan(kode, id_halaman, isi, dihapus=None):
    """What a draft must be, whatever its status: an object, files of this programme only, at most MAKS_DRAF."""
    nama_berkas(kode, id_halaman)
    if not isinstance(isi, dict):
        raise GagalIsi("isi halaman harus berupa objek")
    templat = TEMPLAT[id_halaman]
    if not _berkas_sendiri(templat, isi, kode):
        raise GagalIsi("draf merujuk berkas yang bukan milik prodi ini")
    if dihapus is not None:
        node = node_jalur(templat, dihapus.get("jalur")) if isinstance(dihapus, dict) else None
        if node is None or node["jenis"] != "daftar" or not isinstance(dihapus.get("indeks"), int) \
                or not _berkas_sendiri(node["isi"], dihapus.get("nilai"), kode):
            raise GagalIsi("butir yang dihapus tidak sah")
    if len(json.dumps([isi, dihapus], ensure_ascii=False).encode("utf-8")) > MAKS_DRAF:
        raise GagalIsi("draf terlalu besar (maksimal %d MB)" % (MAKS_DRAF // 1024 // 1024))


def _draf_dari(isi, oleh, lama=None):
    """The draft record for new content: its status (with who submitted it, the admin's note) stays what it was, so
    editing a submitted or returned draft keeps it so until it is submitted again or cancelled."""
    d = {"isi": isi, "status": "draf", "oleh": oleh, "waktu": _sekarang()}
    if lama:
        d["status"] = lama.get("status") if lama.get("status") in STATUS_DRAF else "draf"
        for k in ("diajukan", "catatan"):
            if k in lama:
                d[k] = lama[k]
    return d


def _siap_diterbitkan(id_halaman, isi, kode):
    masalah = periksa(id_halaman, isi, kode)
    if masalah:
        raise GagalIsi("%d isian perlu diperbaiki: %s" % (len(masalah), "; ".join(masalah[:5])))
    if kosong(TEMPLAT[id_halaman], isi):
        raise GagalIsi("halaman ini belum berisi apa pun")


def ajukan(kode, id_halaman, isi, oleh, versi=None):
    """Submit content for publishing (K-P24): it becomes the draft, waiting for a programme admin. It must pass every
    check already, so an admin never gets a draft that cannot be published. Returns the new version."""
    _boleh_disimpan(kode, id_halaman, isi)
    _siap_diterbitkan(id_halaman, isi, kode)
    with _KUNCI:
        data = baca(kode, id_halaman)
        cek_versi(data, versi)
        waktu = _sekarang()
        data["draf"] = {"isi": isi, "status": "menunggu", "oleh": oleh, "waktu": waktu,
                        "diajukan": {"oleh": oleh, "waktu": waktu}}
        return _tulis(kode, id_halaman, data, oleh, "ajukan")


def _ubah_status(kode, id_halaman, oleh, versi, isi, dari, aksi, ubah):
    """Change the status of the draft (it must be in one of `dari`); isi: what the editor holds, stored with it."""
    if isi is not None:
        _boleh_disimpan(kode, id_halaman, isi)
    with _KUNCI:
        data = baca(kode, id_halaman)
        cek_versi(data, versi)
        d = draf(data)
        if d is None or d.get("status") not in dari:
            raise GagalIsi("tindakan ini hanya untuk draf yang %s" % " atau ".join(NAMA_STATUS_DRAF[x] for x in dari))
        d = dict(d, isi=isi if isi is not None else d["isi"], oleh=oleh, waktu=_sekarang())
        d.pop("dihapus", None)
        ubah(d)
        data["draf"] = d
        return _tulis(kode, id_halaman, data, oleh, aksi)


def batal_ajukan(kode, id_halaman, oleh, versi=None, isi=None):
    """Take a submission back: the draft is an ordinary draft again. Returns the new version."""
    def ubah(d):
        d["status"] = "draf"
        d.pop("diajukan", None)
    return _ubah_status(kode, id_halaman, oleh, versi, isi, ("menunggu",), "batal ajukan", ubah)


def kembalikan(kode, id_halaman, catatan, oleh, versi=None, isi=None):
    """Send a submitted draft back to its writers with a note (required): what to fix before submitting it again.
    Returns the new version."""
    catatan = re.sub(r"[ \t]+", " ", (catatan or "").replace("\r\n", "\n")).strip()
    if not catatan:
        raise GagalIsi("tulis catatan untuk penulis: apa yang perlu diperbaiki")
    if len(catatan) > MAKS_CATATAN or KONTROL.search(catatan):
        raise GagalIsi("catatan paling banyak %d karakter, tanpa karakter kendali" % MAKS_CATATAN)
    if saringan_spam.cari(catatan):
        raise GagalIsi("catatan memuat teks judi")

    def ubah(d):
        d["status"] = "dikembalikan"
        d["catatan"] = {"isi": catatan, "oleh": oleh, "waktu": _sekarang()}
    return _ubah_status(kode, id_halaman, oleh, versi, isi, ("menunggu",), "kembalikan", ubah)


def pakai_versi(kode, id_halaman, versi_lama, bagian, oleh, versi=None):
    """Make the published content or the draft of an old version (riwayat.py) the page's draft: an old version comes
    back through the same review as any change, never straight onto the site. Returns the new version."""
    import riwayat as riwayat_mod
    if bagian not in ("terbit", "draf"):
        raise GagalIsi("bagian versi tidak dikenal")
    try:
        path = riwayat_mod.baca_versi(nama_berkas(kode, id_halaman), versi_lama)
    except ValueError as e:
        raise GagalIsi(str(e))
    with open(path, encoding="utf-8") as f:
        lama = json.load(f)
    rekam = lama.get(bagian) if isinstance(lama, dict) else None
    if not isinstance(rekam, dict) or not isinstance(rekam.get("isi"), dict):
        raise GagalIsi("versi itu tidak memuat %s" % ("isi terbit" if bagian == "terbit" else "draf"))
    _boleh_disimpan(kode, id_halaman, rekam["isi"])
    with _KUNCI:
        data = baca(kode, id_halaman)
        cek_versi(data, versi)
        data["draf"] = {"isi": rekam["isi"], "status": "draf", "oleh": oleh, "waktu": _sekarang()}
        return _tulis(kode, id_halaman, data, oleh, "pakai versi %s" % versi_lama)


def keadaan(kode, id_halaman, data=None):
    """What a page holds, for the lists and the completeness tables (K-P24, rencana §3.6):
    {"status": "terbit" (published; "tayang": the site shows it) | "menunggu" | "dikembalikan" | "draf" | "kosong",
     "draf": the draft or None, "terbit": the published record or None, "waktu": the last change}."""
    data = baca(kode, id_halaman) if data is None else data
    d, t = draf(data), data.get("terbit") if isinstance(data.get("terbit"), dict) else None
    tayang = bool(t) and isinstance(t.get("isi"), dict) and not periksa(id_halaman, t["isi"], kode) \
        and not kosong(TEMPLAT[id_halaman], t["isi"])
    diubah = data.get("diubah") if isinstance(data.get("diubah"), dict) else {}
    return {"status": "terbit" if t else (d.get("status") if d and d.get("status") in STATUS_DRAF else
                                          ("draf" if d else "kosong")),
            "tayang": tayang, "draf": d, "terbit": t,
            "waktu": diubah.get("waktu") or (d or {}).get("waktu") or (t or {}).get("waktu") or ""}


def rapikan(node, v):
    """The value without list items that hold nothing (a row added and left empty)."""
    if node["jenis"] == "objek" and isinstance(v, dict):
        return dict(v, **{k: rapikan(n, v[k]) for k, n in node["bidang"] if k in v})
    if node["jenis"] == "daftar" and isinstance(v, list):
        return [rapikan(node["isi"], x) for x in v if not kosong(node["isi"], x)]
    return v


def _saring(node, v, kode):
    j = node["jenis"]
    if j == "objek":
        if not isinstance(v, dict):
            return {}
        return dict(v, **{k: _saring(n, v.get(k), kode) for k, n in node["bidang"]})
    if j == "daftar":
        return [_saring(node["isi"], x, kode) for x in v[:node["maks"]]] if isinstance(v, list) else []
    masalah = []
    _periksa(node, v, "", kode, masalah)
    return None if masalah else v


def isi_sah(id_halaman, isi, kode):
    """A copy of content with every value that fails the checks left out: what the admin's preview of an unfinished
    draft shows (the site only ever shows content that passes them all)."""
    return _saring(TEMPLAT[id_halaman], isi, kode)


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
