# -*- coding: utf-8 -*-
"""The programme's own English texts, Fase 5 langkah 2b (K-P37): the front section of the English home page
(tampilan_prodi.periksa_en, situs_inggris), English menu labels (menu.py), English names of extra pages
(halaman_tambahan.py) and of accreditation criteria (kriteria.py), in the admin's forms and on the English site.

- the checks: unknown keys, lengths, gambling text, refused with nothing stored;
- the home page: the English title, subtitle, sentence, card labels and extra cards (an empty value is the
  Indonesian one, a card without an English label stays off), the background, order and hidden cards of the
  Indonesian settings; the Indonesian home page unchanged;
- the menu: a programme's English label over the master menu's, in the site's menus and the admin's page list;
- extra pages: on the English site only with an English name and a published English version;
- criteria: English labels on English pages and the English accreditation page, only criteria with an English
  name, the English name of the instrument.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
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
    print("uji_teks_inggris: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-teks-inggris-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import halaman_tambahan as ht  # noqa: E402
import isi_halaman as ih  # noqa: E402
import kriteria as kriteria_mod  # noqa: E402
import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import tampilan_prodi as tp  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import prodi  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A = "55201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def halaman(alamat):
    path = os.path.join(lokasi.publik(), "s1informatika", *[x for x in alamat.split("/") if x], "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def situs():
    return lokasi.baca("prodi/%s/situs" % A) or {}


try:
    # ============================================================== the checks
    cek(tp.periksa_en({}) == [] and tp.periksa_en(None) == [], "tanpa teks Inggris sah")
    m = tp.periksa_en({"judul": "x" * 101, "warna": "x", "kartu": {"gelar": {"label": "Degree", "sembunyi": True}},
                       "kartu_tambahan": [{"label": "Judi online"}] * 3})
    cek(any("tidak dikenal: warna" in x for x in m) and any("Judul (Inggris) terlalu panjang" in x for x in m)
        and any("hanya labelnya" in x for x in m) and any("paling banyak 2" in x for x in m), "pemeriksaan teks Inggris: %r" % m)
    s = tp.situs_inggris({"beranda": {"latar": {"jenis": "utama"}, "judul": "Judul", "kartu": {"gelar": {"sembunyi": True,
                          "label": "Gelar akademik"}, "sks": {"urutan": 0}},
                          "kartu_tambahan": [{"label": "Mahasiswa aktif", "nilai": "812", "urutan": 1},
                                             {"label": "Dosen", "nilai": "40"}]},
                          "tagline": "Kalimat", "en": {"judul": "Title", "tagline": "Sentence",
                                                       "kartu": {"sks": {"label": "Credits"}},
                                                       "kartu_tambahan": [{"label": "Active students", "nilai": ""}]}})
    cek(s == {"beranda": {"latar": {"jenis": "utama"}, "judul": "Title",
                          "kartu": {"gelar": {"sembunyi": True}, "sks": {"urutan": 0, "label": "Credits"}},
                          "kartu_tambahan": [{"label": "Active students", "nilai": "812", "keterangan": "", "urutan": 1}]},
              "tagline": "Sentence"}, "susunan beranda Inggris: %r" % s)
    templat = menu_mod.baca_templat()
    cek(menu_mod.periksa_pengaturan(templat, {"sejarah": {"label_en": "Our History"}}) == []
        and menu_mod.periksa_pengaturan(templat, {"sejarah": {"label_en": "slot gacor"}})
        and menu_mod.periksa_pengaturan(templat, {"sejarah": {"label_en": "<b>"}}), "pemeriksaan label menu Inggris")
    susun = {b["id"]: b for b in menu_mod.halaman(menu_mod.susun(templat, {"sejarah": {"label_en": "Our History"}}))}
    cek(susun["sejarah"]["label_en"] == "Our History" and susun["visi-misi"]["label_en"] == "Vision, Mission, Objectives, "
        "and Strategies", "label Inggris prodi di atas label menu induk")
    cek(kriteria_mod.inggris(None) is None and kriteria_mod.inggris({"nama": "LAM", "instrumen": "Instrumen", "kriteria": [
        {"nomor": "1", "nama": "Visi", "nama_en": "Vision"}, {"nomor": "2", "nama": "Tata pamong"}]}) == {
        "nama": "LAM", "instrumen": "", "kriteria": [{"nomor": "1", "nama": "Vision", "nama_en": "Vision"}]},
        "kriteria Inggris hanya yang bernama Inggris")

    # ============================================================== the platform and the admin
    os.makedirs(os.environ["WWW_DATA"])
    pa = dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering", lembaga_akreditasi="LAM-Infokom")
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
    ih.terbitkan(A, "sejarah", {"uraian": "Prodi didirikan tahun 1990."}, "penguji")
    ih.terbitkan(A, "sejarah:en", {"teks": {"Prodi didirikan tahun 1990.": "Founded in 1990."},
                                   "asal": {"uraian": "Prodi didirikan tahun 1990."}}, "penguji")

    id_a, sementara = akun.buat(None, "adma", "Admin Uji", "admin", [A])
    SANDI = "Kebun 7 pagi hari nomor 1 untuk uji"
    akun.ganti_sandi(id_a, sementara, SANDI)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    ka = app.test_client()
    ka.environ_base["REMOTE_ADDR"] = "103.84.116.61"
    ka.get("/masuk")
    with ka.session_transaction() as s_:
        token = s_["csrf"]
    cek(ka.post("/masuk", data={"csrf": token, "pengguna": "adma", "sandi": SANDI}).status_code == 302, "admin masuk")

    def kirim(url, **data):
        with ka.session_transaction() as s_:
            data["csrf"] = s_["csrf"]
        return ka.post(url, data=data)

    # the home page
    teks = ka.get("/prodi/%s/beranda" % A).get_data(as_text=True)
    cek("Versi bahasa Inggris" in teks and 'placeholder="Bachelor Program in Informatics Engineering"' in teks
        and 'name="en-kartu-gelar-label"' in teks and 'placeholder="Degree"' in teks, "formulir beranda: isian Inggris")
    beranda = {"latar": "utama", "judul": "Judul Indonesia", "pengantar": "Kalimat Indonesia.",
               "kartu-gelar-sembunyi": "1", "tambahan-0-label": "Mahasiswa aktif", "tambahan-0-nilai": "812",
               "tambahan-1-label": "Dosen tetap", "tambahan-1-nilai": "40",
               "en-judul": "Informatics at UNSRAT", "en-tagline": "Study computing in Manado.",
               "en-kartu-sks-label": "Credits", "en-tambahan-0-label": "Active students", "en-tambahan-0-keterangan": "2026"}
    r = kirim("/prodi/%s/beranda" % A, **dict(beranda, **{"en-subjudul": "Situs slot gacor"}))
    cek(r.status_code == 400 and "memuat istilah terlarang" in r.get_data(as_text=True) and not situs().get("en")
        and 'value="Informatics at UNSRAT"' in r.get_data(as_text=True), "teks Inggris berjudi ditolak, isian tetap")
    r = kirim("/prodi/%s/beranda" % A, **beranda)
    cek(r.status_code == 302 and situs().get("en") == {
        "judul": "Informatics at UNSRAT", "tagline": "Study computing in Manado.", "kartu": {"sks": {"label": "Credits"}},
        "kartu_tambahan": [{"label": "Active students", "nilai": "", "keterangan": "2026"}]}, "teks Inggris beranda disimpan: %r"
        % situs().get("en"))
    en = halaman("en") or ""
    cek("Informatics at UNSRAT" in en and "Study computing in Manado." in en and ">Credits<" in en
        and ">Active students<" in en and ">812 <span class=\"fakta__kecil\">2026</span>" in en
        and "Dosen tetap" not in en and "Judul Indonesia" not in en and ">Degree<" not in en and "pahlawan--utama" in en,
        "beranda Inggris dari teks Inggris prodi")
    cek("Judul Indonesia" in (halaman("") or "") and "Kalimat Indonesia." in halaman("") and "Informatics at UNSRAT"
        not in halaman(""), "beranda Indonesia tetap")

    # the menu
    teks = ka.get("/prodi/%s/menu" % A).get_data(as_text=True)
    cek('name="label_en-profil"' in teks and 'placeholder="History"' in teks, "formulir menu: label Inggris")
    r = kirim("/prodi/%s/menu" % A, **{"label_en-profil": "About", "label_en-sejarah": "Our Story"})
    cek(r.status_code == 302 and situs()["menu"] == {"profil": {"label_en": "About"}, "sejarah": {"label_en": "Our Story"}},
        "label menu Inggris disimpan: %r" % situs().get("menu"))
    r = kirim("/prodi/%s/menu" % A, **{"label_en-sejarah": "Slot gacor"})
    cek(r.status_code == 400 and situs()["menu"]["sejarah"]["label_en"] == "Our Story", "label menu Inggris berjudi ditolak")
    en = halaman("en/profil/sejarah") or ""
    cek("<h1>Our Story</h1>" in en and ">About</a>" in en and ">Sejarah<" not in halaman("en"), "label menu Inggris di situs")
    cek("<h1>Sejarah</h1>" in (halaman("profil/sejarah") or ""), "label menu Indonesia tetap")
    teks = ka.get("/prodi/%s/halaman/sejarah/en" % A).get_data(as_text=True)
    cek('<span lang="en">Our Story</span>' in teks, "penyunting Inggris menyebut label Inggris prodi")

    # extra pages
    r = kirim("/prodi/%s/tambahan" % A, label="Database Skripsi", kelompok="akademik", alamat="", label_en="Thesis Database")
    h = ht.baca(A)[-1]
    cek(r.status_code == 302 and h.get("label_en") == "Thesis Database", "halaman tambahan dengan nama Inggris")
    ih.terbitkan(A, h["id"], {"uraian": "Daftar skripsi."}, "penguji")
    ih.terbitkan(A, h["id"] + ":en", {"teks": {"Daftar skripsi.": "List of theses."}, "asal": {"uraian": "Daftar skripsi."}},
                 "penguji")
    from bangun import Pembangun
    Pembangun(produksi=False).bangun()
    en = halaman("en/halaman/database-skripsi") or ""
    cek("<h1>Thesis Database</h1>" in en and "List of theses." in en and ">Thesis Database</a>" in halaman("en/akademik"),
        "halaman tambahan di situs Inggris")
    r = kirim("/prodi/%s/tambahan/simpan" % A, **{"label-%s" % h["id"]: "Database Skripsi", "kelompok-%s" % h["id"]: "akademik",
                                                 "label_en-%s" % h["id"]: ""})
    cek(r.status_code == 302 and "label_en" not in ht.baca(A)[-1] and halaman("en/halaman/database-skripsi") is None
        and halaman("halaman/database-skripsi"), "tanpa nama Inggris: hilang dari situs Inggris saja")
    r = kirim("/prodi/%s/tambahan/simpan" % A, **{"label-%s" % h["id"]: "Database Skripsi", "kelompok-%s" % h["id"]: "akademik",
                                                 "label_en-%s" % h["id"]: "<script>"})
    cek(r.status_code == 400 and "nama menu Inggris" in r.get_data(as_text=True), "nama Inggris tidak sah ditolak")

    # criteria
    r = kirim("/prodi/%s/kriteria" % A, nama="LAM Infokom", instrumen="Instrumen LAM Infokom", instrumen_en="LAM Infokom instrument",
              kriteria_jumlah="3", **{"k-0-nomor": "1", "k-0-nama": "Visi dan Misi", "k-0-nama_en": "Vision and Mission",
                                      "k-1-nomor": "2", "k-1-nama": "Tata Pamong", "h-sejarah": ["1", "2"]})
    tersimpan = kriteria_mod.baca_prodi(A)
    cek(r.status_code == 302 and tersimpan.get("instrumen_en") == "LAM Infokom instrument"
        and tersimpan["kriteria"] == [{"nomor": "1", "nama": "Visi dan Misi", "nama_en": "Vision and Mission"},
                                      {"nomor": "2", "nama": "Tata Pamong"}], "kriteria dengan nama Inggris: %r" % tersimpan)
    en = halaman("en/profil/sejarah") or ""
    cek("LAM Infokom accreditation criteria: Criterion 1, Vision and Mission</p>" in en and "Tata Pamong" not in en,
        "label kriteria Inggris di halaman Inggris")
    cek("Kriteria 1, Visi dan Misi; Kriteria 2, Tata Pamong" in (halaman("profil/sejarah") or ""), "label kriteria Indonesia tetap")
    akr = halaman("en/profil/akreditasi") or ""
    cek("Pages by LAM Infokom accreditation criterion" in akr and "LAM Infokom instrument" in akr
        and "Criterion 1: Vision and Mission" in akr and ">Our Story</a>" in akr and "Criterion 2" not in akr,
        "peta kriteria Inggris")
    r = kirim("/prodi/%s/kriteria" % A, nama="LAM Infokom", kriteria_jumlah="1",
              **{"k-0-nomor": "1", "k-0-nama": "Visi", "k-0-nama_en": "Judi slot online"})
    cek(r.status_code == 400 and "memuat teks judi" in r.get_data(as_text=True), "nama kriteria Inggris berjudi ditolak")

    jumlah, temuan = periksa_situs(lokasi.publik(), "teks-inggris")
    cek(not temuan, "pemeriksaan halaman: %r" % temuan[:5])
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_teks_inggris: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
