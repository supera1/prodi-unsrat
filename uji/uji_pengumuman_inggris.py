# -*- coding: utf-8 -*-
"""Announcements in English, Fase 5 langkah 4 (K-P37): the "en" of an item in platform/pengumuman.py, the English part
of the announcement form (pengumuman_admin.py), and the news pages of the English site (bangun.py).

- the model: the English texts checked like the Indonesian ones (no HTML, no gambling terms), title and summary
  together, machine marks and sources only for the three texts; the state of an English version; the item as the
  English site shows it only when complete and checked; texts whose Indonesian source changed;
- the admin: English texts saved with the item; the machine translation box only with a provider; the empty English
  texts filled and marked, the use counted, the audit log; a mark gone once a person changed the text, all gone with
  the checkbox; overwriting only when asked; a failing provider changes nothing but saves the form; gambling text
  refused without saving; a changed Indonesian text flagged; the list's column;
- the site: an item with unchecked machine text or without English stays off the English site (no News menu while
  there is none); once checked: the English list, the item's page (English category, date, Indonesian photo texts
  and PDF titles marked lang="id"), the English home page's latest news, the language switch and hreflang between
  both versions, the sitemap; Indonesian pages of an item without English keep no link to English; every page passes
  the page checks.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
import re
import shutil
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import flask  # noqa: F401
except ImportError:
    print("uji_pengumuman_inggris: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-pengumuman-en-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)
for v in ("TERJEMAH_PENYEDIA", "TERJEMAH_KUNCI", "TERJEMAH_BATAS_HARIAN", "TERJEMAH_BATAS_BULANAN"):
    os.environ.pop(v, None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bangun  # noqa: E402
import media  # noqa: E402
import pengumuman as pg  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
import terjemah_mesin as tm  # noqa: E402
from formulir_uji import gambar, pdf, prodi  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A = "55201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def butir(**ubah):
    b = {"id": "2026-11-01-uji", "judul": "Jadwal ujian", "tanggal": "2026-11-01", "kategori": "akademik",
         "ringkasan": "Jadwal ujian semester.", "isi": "Ujian dimulai Senin.", "foto": [], "pdf": [], "sematkan": False,
         "kedaluwarsa": "", "status": "draf"}
    b.update(ubah)
    return b


def halaman(rel):
    path = os.path.join(os.environ["PRODI_PUBLIK"], *rel.split("/"))
    path = path if rel.endswith(".xml") else os.path.join(path, "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


try:
    # ============================================================== the model
    cek(not pg.periksa(butir()) and not pg.periksa(butir(en={})), "butir tanpa versi Inggris sah")
    sah = {"judul": "Exam schedule", "ringkasan": "The semester's exam schedule.", "isi": "Exams start on Monday.",
           "asal": {"judul": "Jadwal ujian"}, "mesin": {"isi": "Exams start on Monday."}}
    cek(not pg.periksa(butir(en=sah)), "versi Inggris sah: %r" % pg.periksa(butir(en=sah)))
    for en, harap in (("x", "versi Inggris tidak sah"), ({"judul": "A", "lain": "x"}, "versi Inggris tidak sah"),
                      ({"isi": "Only a body."}, "perlu judul dan ringkasan"),
                      ({"judul": "<b>Exam</b>", "ringkasan": "S."}, "Judul (Inggris) tidak boleh memuat HTML"),
                      ({"judul": "Exam", "ringkasan": "Play slot gacor today."}, "Ringkasan (Inggris) memuat istilah terlarang"),
                      ({"judul": "E" * 151, "ringkasan": "S."}, "Judul (Inggris) terlalu panjang"),
                      ({"judul": "E", "ringkasan": "S.", "mesin": {"foto": "x"}}, "mesin tidak sah"),
                      ({"judul": "E", "ringkasan": "S.", "asal": {"judul": 3}}, "asal tidak sah"),
                      ({"judul": "E", "ringkasan": "S.", "mesin": ["judul"]}, "mesin tidak sah")):
        masalah = pg.periksa(butir(en=en))
        cek(any(harap in m for m in masalah), "versi Inggris %r ditolak (%s): %r" % (en, harap, masalah))
    for en, isi, harap in (({}, "Isi.", "kosong"), ({"judul": "E"}, "Isi.", "belum-lengkap"),
                           ({"judul": "E", "ringkasan": "S."}, "Isi.", "belum-lengkap"),
                           ({"judul": "E", "ringkasan": "S."}, "", "siap"),
                           ({"judul": "E", "ringkasan": "S.", "isi": "B.", "mesin": {"isi": "B."}}, "Isi.", "mesin"),
                           ({"judul": "E", "ringkasan": "S.", "isi": "B."}, "Isi.", "siap")):
        cek(pg.keadaan_en(butir(en=en, isi=isi)) == harap, "keadaan versi Inggris %r: %s" % (en, pg.keadaan_en(butir(en=en, isi=isi))))
    cek(pg.inggris(butir(en=sah)) is None, "terjemahan mesin yang belum diperiksa tidak tampil")
    tampil = pg.inggris(butir(en=dict(sah, mesin={}), catatan="Catatan admin"))
    cek(tampil and tampil["judul"] == "Exam schedule" and tampil["isi"] == "Exams start on Monday."
        and tampil["tanggal"] == "2026-11-01" and "en" not in tampil and "catatan" not in tampil, "butir versi Inggris: %r" % tampil)
    cek(pg.perlu_diperbarui(butir(judul="Jadwal ujian baru", en=sah)) == ["judul"]
        and pg.perlu_diperbarui(butir(en=sah)) == [], "teks Indonesia yang berubah sejak diterjemahkan")
    with io.open(pg.KATEGORI_JSON, encoding="utf-8") as f:
        kategori = json.load(f)["kategori"]
    cek(all(k.get("label_en") for k in kategori), "setiap kategori punya nama Inggris")

    # ============================================================== a programme with its English site on
    os.makedirs(os.environ["WWW_DATA"])
    pa = dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering")
    for nama, isi_ in {"prodi": {"program": [pa]},
                       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering",
                                          "jenis": "fakultas", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                       "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi_, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n" % A)
    registri.siapkan_dari_csv("penguji", path_csv)
    registri.atur(A, "penguji", inggris=True)
    foto = media.simpan_foto(A, gambar(900, 600), "Mahasiswa menerima piala")
    lampiran = media.simpan_pdf(A, pdf(), "Surat keputusan juara")
    ID_LAMA = pg.tambah(A, {"judul": "Kuliah umum kecerdasan buatan", "kategori": "kegiatan", "tanggal": "2026-10-01",
                            "ringkasan": "Kuliah umum bersama praktisi."}, "penguji", "terbit")

    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("opa", "operator", [A])):
        akun_baru(nama, peran, p, super_)

    def klien(app, nama, ip):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = ip
        c.get("/masuk")
        with c.session_transaction() as s_:
            token = s_["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302,
            "%s masuk" % nama)
        return c

    def kirim(c, url, **data):
        with c.session_transaction() as s_:
            data["csrf"] = s_["csrf"]
        return c.post(url, data=data)
    D = "/prodi/%s/pengumuman" % A

    def formulir(b, **ubah):
        """What the form of item b sends, with changes."""
        en = b.get("en") or {}
        data = {"judul": b["judul"], "tanggal": b["tanggal"], "kategori": b["kategori"], "ringkasan": b["ringkasan"],
                "isi": b.get("isi", ""), "kedaluwarsa": b.get("kedaluwarsa", ""), "aksi_simpan": "simpan",
                "en_judul": en.get("judul", ""), "en_ringkasan": en.get("ringkasan", ""), "en_isi": en.get("isi", "")}
        for i, x in enumerate(b.get("foto", [])):
            data["foto-%d-alt" % i] = x["alt"]
        for i, x in enumerate(b.get("pdf", [])):
            data["pdf-%d-judul" % i] = x["judul"]
        data.update(ubah)
        return data

    # without a provider: English texts typed by hand, no machine translation box
    tanpa = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    ko = klien(tanpa, "opa", "103.84.116.70")
    r = kirim(ko, D + "/baru", judul="Pendaftaran wisuda", tanggal="2026-11-05", kategori="akademik",
              ringkasan="Pendaftaran wisuda dibuka.", isi="", aksi_simpan="draf", en_judul="Graduation registration",
              en_ringkasan="Graduation registration is open.", en_isi="")
    ID_TANGAN = r.headers.get("Location", "").rstrip("/").rsplit("/", 1)[-1]
    b = pg.cari(A, ID_TANGAN)
    cek(r.status_code == 302 and b["en"] == {"judul": "Graduation registration", "ringkasan": "Graduation registration is open.",
                                             "isi": "", "asal": {"judul": "Pendaftaran wisuda",
                                                                 "ringkasan": "Pendaftaran wisuda dibuka."}},
        "pengumuman baru dengan versi Inggris: %r" % b.get("en"))
    teks = ko.get(D + "/" + ID_TANGAN).get_data(as_text=True)
    cek("Versi bahasa Inggris (opsional)" in teks and "Terjemahan mesin" not in teks and 'lang="en"' in teks
        and "Versi Inggris: <strong>Lengkap</strong>" in teks, "formulir: bagian Inggris tanpa terjemahan mesin")
    cek("<td>Lengkap</td>" in ko.get(D).get_data(as_text=True), "daftar: kolom versi Inggris")
    r = kirim(ko, D + "/" + ID_TANGAN, **formulir(b, en_ringkasan="Register now at the slot gacor desk."))
    cek(r.status_code == 400 and "istilah terlarang" in r.get_data(as_text=True)
        and "slot gacor desk" in r.get_data(as_text=True)
        and pg.cari(A, ID_TANGAN)["en"]["ringkasan"] == "Graduation registration is open.",
        "teks Inggris berjudi ditolak tanpa tersimpan, ketikan tetap di formulir")

    # with the stand-in provider
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron",
                            "TERJEMAH_PENYEDIA": "tiruan", "TERJEMAH_BATAS_HARIAN": "1000"})
    ko, ka, ks = klien(app, "opa", "103.84.116.61"), klien(app, "adma", "103.84.116.62"), klien(app, "superuji", "103.84.116.63")
    ID = pg.tambah(A, {"judul": "Mahasiswa Teknik Informatika juara lomba", "kategori": "prestasi-mahasiswa",
                       "tanggal": "2026-11-10", "ringkasan": "Tim mahasiswa meraih juara pertama.",
                       "isi": "Tim kami menang.\n\n- Juara pertama\n- Info: https://unsrat.ac.id/lomba",
                       "foto": [foto], "pdf": [lampiran]}, "opa", "draf")
    U = D + "/" + ID
    teks = ko.get(U).get_data(as_text=True)
    cek("Terjemahan mesin (Tiruan)" in teks and "<strong>3 teks</strong>" in teks and 'value="terjemahkan"' in teks
        and "Sisa batas terjemahan mesin prodi ini hari ini: 1000" in teks, "kotak terjemahan mesin dengan perkiraan")
    cek("tersedia setelah pengumuman ini disimpan" in ko.get(D + "/baru").get_data(as_text=True),
        "pengumuman baru: terjemahan mesin setelah disimpan")
    b = pg.cari(A, ID)
    r = kirim(ko, U, **formulir(b, aksi_simpan="terjemahkan", en_judul="Informatics students win a contest"))
    b = pg.cari(A, ID)
    en = b.get("en", {})
    cek(r.status_code == 302 and en.get("judul") == "Informatics students win a contest"
        and en.get("ringkasan") == "(EN) Tim mahasiswa meraih juara pertama."
        and en.get("isi") == "(EN) Tim kami menang.\n\n- (EN) Juara pertama\n- (EN) Info: https://unsrat.ac.id/lomba"
        and sorted(en.get("mesin", {})) == ["isi", "ringkasan"] and en["asal"]["isi"] == b["isi"],
        "isian kosong diisi terjemahan mesin, ketikan sendiri tetap: %r" % en)
    pakai = tm.pemakaian(A)["hari"].get(tm.hari_ini(), 0)
    cek(pakai == len(b["ringkasan"]) + len(b["isi"]), "pemakaian dicatat: %r" % pakai)
    teks = ko.get(U).get_data(as_text=True)
    cek(teks.count('class="keterangan terjemah__mesin"') == 2 and "Saya sudah memeriksa versi Inggris" in teks
        and "2 teks diterjemahkan mesin" in teks and "Terjemahan mesin belum diperiksa" in teks
        and "Pratinjau isi versi Inggris" in teks, "tanda terjemahan mesin di formulir")
    cek("pengumuman-en-terjemahan-mesin" in ks.get("/super/audit").get_data(as_text=True), "log audit")
    cek("<strong>1</strong> pengumuman dengan terjemahan mesin belum diperiksa" in ko.get("/prodi/%s/" % A).get_data(as_text=True),
        "dasbor prodi: pengumuman dengan terjemahan mesin yang belum diperiksa")

    # published with unchecked machine text: the Indonesian item is on the site, the English one is not
    r = kirim(ka, U, **formulir(b, aksi_simpan="terbit"))
    cek(r.status_code == 302 and pg.cari(A, ID)["status"] == "terbit" and pg.cari(A, ID)["en"]["mesin"],
        "terbit dengan terjemahan mesin yang belum diperiksa")
    cek(halaman("s1informatika/pengumuman/" + ID) is not None and halaman("s1informatika/en/pengumuman") is None
        and ">News<" not in (halaman("s1informatika/en") or "x>News<"), "belum diperiksa: tidak ada di situs Inggris")
    cek('hreflang="en"' not in halaman("s1informatika/pengumuman/" + ID), "halaman Indonesia tanpa pasangan Inggris")

    # a changed text loses its mark; the checkbox clears the rest
    b = pg.cari(A, ID)
    kirim(ka, U, **formulir(b, en_ringkasan="Our student team won first place."))
    cek(sorted(pg.cari(A, ID)["en"]["mesin"]) == ["isi"], "teks yang diubah dianggap sudah diperiksa")
    b = pg.cari(A, ID)
    kirim(ka, U, **formulir(b, periksa_en="1"))
    b = pg.cari(A, ID)
    cek("mesin" not in b["en"] and pg.keadaan_en(b) == "siap", "dicentang: terjemahan mesin sudah diperiksa")
    teks = ka.get("/prodi/%s/" % A).get_data(as_text=True)
    cek("<strong>1</strong> pengumuman berbahasa Inggris terbit" in teks
        and "pengumuman dengan terjemahan mesin belum diperiksa" not in teks, "dasbor prodi: pengumuman Inggris terbit")

    # the English site
    daftar = halaman("s1informatika/en/pengumuman")
    detail = halaman("s1informatika/en/pengumuman/" + ID)
    beranda = halaman("s1informatika/en")
    cek(daftar and "Informatics students win a contest" in daftar and "Kuliah umum" not in daftar
        and "Graduation" not in daftar and "Student Achievements" in daftar and "<h1>News</h1>" in daftar
        and 'lang="en"' in daftar, "daftar berita Inggris: hanya pengumuman berversi Inggris")
    cek(detail and "<h1>Informatics students win a contest</h1>" in detail and "November 10, 2026" in detail
        and "Our student team won first place." in detail and "<li>(EN) Juara pertama</li>" in detail
        and '<a href="https://unsrat.ac.id/lomba">' in detail and 'alt="Mahasiswa menerima piala" lang="id"' in detail
        and '<h3 class="pdf__judul" lang="id">Surat keputusan juara</h3>' in detail and "Open PDF" in detail
        and "Attachments" in detail and "PDF, 1 pages" in detail and "Jadwal" not in detail,
        "halaman pengumuman Inggris")
    cek(beranda and "Latest news" in beranda and "Informatics students win a contest" in beranda
        and ">News<" in beranda, "beranda Inggris: berita terbaru dan menu News")
    cek(halaman("s1informatika/en/pengumuman/kategori/prestasi-mahasiswa") is not None
        and halaman("s1informatika/en/pengumuman/kategori/kegiatan") is None
        and halaman("s1informatika/en/pengumuman/arsip/2026") is not None
        and halaman("s1informatika/en/pengumuman/rss.xml") is None, "kategori dan arsip Inggris, tanpa RSS Inggris")
    id_detail = halaman("s1informatika/pengumuman/" + ID)
    cek('hreflang="en" href="https://prodi.unsrat.ac.id/s1informatika/en/pengumuman/%s/"' % ID in id_detail
        and 'hreflang="id"' in detail, "hreflang dua arah: %r" % re.findall(r"<link[^>]*hreflang[^>]*>", id_detail))
    cek('hreflang="en"' in halaman("s1informatika/pengumuman")
        and 'hreflang="en"' in halaman("s1informatika/pengumuman/kategori/prestasi-mahasiswa")
        and 'hreflang="en"' not in halaman("s1informatika/pengumuman/kategori/kegiatan")
        and 'hreflang="en"' not in halaman("s1informatika/pengumuman/" + ID_LAMA), "pasangan bahasa daftar dan kategori")
    peta = bangun.Pembangun().peta_situs()            # written by production builds only
    cek(re.search(r'<loc>[^<]*/s1informatika/pengumuman/%s/</loc><xhtml:link rel="alternate" hreflang="id"[^>]*/>'
                  r'<xhtml:link rel="alternate" hreflang="en" href="[^"]*/s1informatika/en/pengumuman/%s/"' % (ID, ID), peta),
        "sitemap memuat pengumuman Inggris sebagai pasangan")

    # a changed Indonesian text is flagged; the checkbox marks it up to date
    b = pg.cari(A, ID)
    kirim(ka, U, **formulir(b, judul="Mahasiswa Teknik Informatika juara lomba nasional"))
    teks = ka.get(U).get_data(as_text=True)
    cek(pg.perlu_diperbarui(pg.cari(A, ID)) == ["judul"] and "Teks Indonesianya berubah sejak diterjemahkan" in teks
        and pg.keadaan_en(pg.cari(A, ID)) == "siap", "teks Indonesia berubah: ditandai, tetap tampil")
    b = pg.cari(A, ID)
    kirim(ka, U, **formulir(b, periksa_en="1"))
    cek(pg.perlu_diperbarui(pg.cari(A, ID)) == [], "dicentang: versi Inggris diperbarui")

    # overwriting only when asked; a failing provider changes nothing but keeps the form
    b = pg.cari(A, ID)
    sebelum = dict(b["en"])
    kirim(ka, U, **formulir(b, aksi_simpan="terjemahkan"))
    cek(pg.cari(A, ID)["en"] == sebelum, "tanpa timpa: terjemahan yang ada tetap")
    app.penerjemah.gagal = "kuota karakter akun DeepL sudah habis untuk periode ini"
    r = kirim(ka, U, **formulir(b, aksi_simpan="terjemahkan", timpa="1", sematkan="1"))
    b2 = pg.cari(A, ID)
    cek(r.status_code == 302 and b2["en"] == sebelum and b2["sematkan"] is True
        and "kuota karakter akun DeepL" in ka.get(U).get_data(as_text=True), "penyedia gagal: formulir tersimpan, terjemahan tetap")
    app.penerjemah.gagal = None
    r = kirim(ka, U, **formulir(b2, aksi_simpan="terjemahkan", timpa="1", sematkan="1"))
    b3 = pg.cari(A, ID)
    cek(b3["en"]["judul"].startswith("(EN) ") and sorted(b3["en"]["mesin"]) == ["isi", "judul", "ringkasan"]
        and halaman("s1informatika/en/pengumuman") is None, "terjemahkan ulang: menimpa, belum tampil sampai diperiksa")
    kirim(ka, U, **formulir(b3, periksa_en="1", sematkan="1"))

    # the same Indonesian text in two fields: only the empty English one is filled
    ID_SAMA = pg.tambah(A, {"judul": "Libur", "kategori": "akademik", "tanggal": "2026-11-12", "ringkasan": "Kampus libur.",
                            "isi": "Kampus libur.", "en": {"judul": "Holiday", "ringkasan": "The campus is closed.",
                                                           "asal": {"judul": "Libur", "ringkasan": "Kampus libur."}}},
                       "adma", "draf")
    b = pg.cari(A, ID_SAMA)
    kirim(ka, D + "/" + ID_SAMA, **formulir(b, aksi_simpan="terjemahkan"))
    en = pg.cari(A, ID_SAMA)["en"]
    cek(en["ringkasan"] == "The campus is closed." and en["isi"] == "(EN) Kampus libur." and list(en["mesin"]) == ["isi"],
        "teks sama di dua isian: terjemahan yang ada tidak ditimpa: %r" % en)

    # an operator cannot change a published item, English included
    cek(kirim(ko, U, **formulir(pg.cari(A, ID), en_judul="Changed")).status_code == 403, "operator tidak mengubah yang terbit")

    jumlah, temuan = periksa_situs(os.environ["PRODI_PUBLIK"], "pengumuman-inggris")
    cek(not temuan, "pemeriksaan halaman: %r" % temuan[:5])
    cek(jumlah > 20, "halaman diperiksa: %d" % jumlah)
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_pengumuman_inggris: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
