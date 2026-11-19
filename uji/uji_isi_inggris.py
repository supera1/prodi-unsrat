# -*- coding: utf-8 -*-
"""The English version of a programme's own pages, Fase 5 langkah 2 (K-P37): platform/isi_inggris.py, the ":en"
pages of isi_halaman.py, the English form of the admin (isi_admin.py) and the English pages of the builder.

- the translation memory: the texts to translate (names, codes and lists kept in spreadsheets left out, "boleh"
  fields optional, photo texts), a row added or moved in Indonesian never matched with another row's translation,
  a changed text outside a list keeping its old translation, a list item whose required text is not translated left
  out, coverage ("perlu diperbarui"), the checks (gambling text, links) and the preview's per-text filter;
- the admin: the English tab for operators and admins, the same review (submit, publish, send back, withdraw,
  discard), operators never publishing, the form's fields (once per text, the Indonesian text with each), a change of
  the Indonesian draft while translating, the English preview, the history of the English version and an old version
  made the draft, the list's English column, "perlu diperbarui" after the Indonesian page changed, completeness and
  its CSV, the superadmin's history naming the English version;
- the site: an English page only for a programme switched on and once both versions are published, its texts,
  headings, column names and fixed choices in English, the language link on both pages, the accreditation documents
  with English titles, a withdrawn English version gone, the page checks clean.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import csv
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
    print("uji_isi_inggris: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-isi-inggris-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bangun  # noqa: E402
import isi_halaman as ih  # noqa: E402
import isi_inggris as ii  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import pdf, prodi  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B = "55201", "20201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def halaman(alamat, slug="s1informatika"):
    path = os.path.join(lokasi.publik(), slug, *[x for x in alamat.split("/") if x], "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def t(teks):
    return "t." + ih.kunci_teks(teks)


try:
    # ============================================================== the translation memory
    T = ih.TEMPLAT["kerja-sama"]
    isi = {"uraian": "Kerja sama prodi.", "daftar": [
        {"mitra": "PT Alpha", "jenis": "Penelitian", "tingkat": "Nasional", "bentuk": "Riset bersama", "manfaat": "Data"},
        {"mitra": "Univ Beta", "jenis": "Pendidikan", "tingkat": "Internasional", "bentuk": "Pertukaran dosen"}]}
    en = {"teks": {"Kerja sama prodi.": "Partnerships.", "Riset bersama": "Joint research",
                   "Pertukaran dosen": "Lecturer exchange"}, "asal": {"uraian": "Kerja sama prodi."}}
    perlu = ii.perlu_terjemah(T, isi)
    cek([x["teks"] for x in perlu] == ["Kerja sama prodi.", "Riset bersama", "Data", "Pertukaran dosen"],
        "teks yang diterjemahkan, tanpa nama mitra: %r" % [x["teks"] for x in perlu])
    hasil = ii.terjemahkan(T, isi, en)
    cek(hasil["uraian"] == "Partnerships." and hasil["daftar"][0]["bentuk"] == "Joint research"
        and hasil["daftar"][0]["mitra"] == "PT Alpha" and hasil["daftar"][0]["manfaat"] is None
        and hasil["daftar"][0]["jenis"] == "Penelitian", "terjemahan diletakkan di atas isi Indonesia: %r" % hasil)
    cek(ii.cakupan(T, isi, en) == (4, 3), "cakupan: %r" % (ii.cakupan(T, isi, en),))
    geser = {"uraian": "Kerja sama program studi.",
             "daftar": [{"mitra": "CV Gamma", "jenis": "Penelitian", "tingkat": "Lokal", "bentuk": "Survei"}] + isi["daftar"]}
    hasil = ii.terjemahkan(T, geser, en)
    cek([x.get("bentuk") for x in hasil["daftar"]] == [None, "Joint research", "Lecturer exchange"]
        and hasil["uraian"] == "Partnerships.", "baris yang disisipkan tidak menggeser terjemahan; uraian lama tetap")
    cek(ii.cakupan(T, geser, en) == (5, 2), "uraian yang berubah dihitung belum diterjemahkan")
    cek(ii.cari({"teks": {"A": "a"}, "asal": {"daftar.0.bentuk": "A"}}, "daftar.0.bentuk", "B", True) == (None, None)
        and ii.cari({"teks": {"A": "a"}, "asal": {"uraian": "A"}}, "uraian", "B", False) == ("a", "lama")
        and ih.periksa("kerja-sama:en", {"teks": {"A": "a"}, "asal": {"daftar.0.bentuk": "A"}}, A),
        "terjemahan lama hanya untuk isian di luar daftar")
    TA = ih.TEMPLAT["tendik"]
    tendik = {"daftar": [{"nama": "Nama Contoh", "tugas": "Laboran"}, {"nama": "Nama Lain", "tugas": "Arsiparis"}]}
    hasil = ii.terjemahkan(TA, tendik, {"teks": {"Laboran": "Laboratory assistant"}})
    cek([x["nama"] for x in hasil["daftar"]] == ["Nama Contoh"], "baris dengan teks wajib belum diterjemahkan ditunda")
    TP = ih.TEMPLAT["publikasi"]
    pub = {"daftar": [{"judul": "Analisis Sentimen", "penulis": "Contoh, A.", "tahun": 2025}]}
    cek(ii.terjemahkan(TP, pub, {})["daftar"][0]["judul"] == "Analisis Sentimen" and ii.cakupan(TP, pub, {}) == (0, 0),
        "judul karya boleh tidak diterjemahkan")
    TT = ih.TEMPLAT["tugas-akhir"]
    ta = {"uraian": "Daftar judul.", "daftar": [{"judul": "Sistem Informasi Desa", "tahun": 2024}]}
    cek([x["teks"] for x in ii.butir_formulir(TT, ta, {})] == ["Daftar judul."], "tabel Excel tidak masuk formulir")
    TS = ih.TEMPLAT["sejarah"]
    foto_ = {"jenis": "gambar", "alt": "Gedung prodi", "varian": {}}
    sej = {"uraian": "Didirikan 1990.", "foto": [{"berkas": foto_, "keterangan": "Gedung lama"}]}
    hasil = ii.terjemahkan(TS, sej, {"teks": {"Didirikan 1990.": "Founded in 1990.", "Gedung prodi": "The building"}})
    cek(hasil["foto"][0]["berkas"]["alt"] == "The building" and hasil["foto"][0]["keterangan"] is None,
        "teks alternatif foto diterjemahkan; keterangan belum")
    sej2 = dict(sej, uraian="Didirikan 1990.\n\n- **Satu**")
    butir = ii.butir_formulir(TS, sej2, {"teks": {"Didirikan 1990.": "Founded in 1990."}, "asal": {"uraian": "Didirikan 1990."}})
    cek(butir[0]["jenis"] == "lama" and butir[0]["nilai"] == "Founded in 1990." and butir[0]["kaya"] and butir[0]["panjang"],
        "formulir menawarkan terjemahan lama untuk diperiksa")
    baru, tak = ii.dari_formulir(TS, {"teks": {"Didirikan 1990.": "Founded in 1990."}, "asal": {"uraian": "Didirikan 1990."}},
                                 {t("Didirikan 1990.\n\n- **Satu**"): "Founded in 1990.\n\n- **One**",
                                  t("Gedung lama"): "  The   old building ", "t.0000000000000000": "x"}, [sej2])
    cek(baru == {"teks": {"Didirikan 1990.\n\n- **Satu**": "Founded in 1990.\n\n- **One**", "Gedung lama": "The old building"},
                 "asal": {"uraian": "Didirikan 1990.\n\n- **Satu**"}} and tak == ["t.0000000000000000"],
        "formulir: terjemahan baru, yang lama dibuang, isian tak dikenal dilaporkan: %r %r" % (baru, tak))
    kosongkan, _t = ii.dari_formulir(TS, baru, {t("Gedung lama"): ""}, [sej2])
    cek("Gedung lama" not in kosongkan["teks"], "isian dikosongkan: terjemahannya hilang")
    cek(ih.periksa("sejarah:en", {"teks": {"Satu": "Daftar situs slot gacor"}}, A)
        and ih.periksa("sejarah:en", {"teks": {"Satu": "[a](http://x.id)"}}, A)
        and not ih.periksa("sejarah:en", {"teks": {"Satu": "[a](https://x.id)"}}, A), "pemeriksaan terjemahan")
    cek(ih.isi_sah("sejarah:en", {"teks": {"Satu": "One", "Dua": "slot gacor"}}, A)["teks"] == {"Satu": "One"},
        "pratinjau membuang terjemahan yang tidak sah saja")
    cek(ih.templat_halaman("tidak-ada:en") is None and ih.nama_berkas(A, "sejarah:en") == "prodi/%s/halaman-sejarah-en" % A,
        "berkas versi Inggris")

    # ============================================================== the platform
    os.makedirs(os.environ["WWW_DATA"])
    pa = dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering")
    for nama, isi_ in {"prodi": {"program": [pa, prodi(B, "Teknik Elektro")]},
                       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering",
                                          "jenis": "fakultas", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                       "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi_, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)
    ih.terbitkan(A, "sejarah", {"uraian": "Prodi didirikan tahun 1990.", "linimasa": [
        {"tahun": 1990, "peristiwa": "Prodi didirikan"}, {"tahun": 2010, "peristiwa": "Akreditasi pertama"}]}, "penguji")
    sertifikat = media.simpan_pdf(A, pdf(), "Sertifikat")
    ih.terbitkan(A, "akreditasi", {"dokumen": [{"judul": "Sertifikat akreditasi", "tahun": 2024, "berkas": sertifikat}]},
                 "penguji")

    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("opa", "operator", [A])):
        akun_baru(nama, peran, p, super_)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    klien = {}
    for i, nama in enumerate(("superuji", "adma", "opa")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (60 + i)
        c.get("/masuk")
        with c.session_transaction() as s_:
            token = s_["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ks, ka, ko = klien["superuji"], klien["adma"], klien["opa"]

    def kirim(c, url, **data):
        with c.session_transaction() as s_:
            data["csrf"] = s_["csrf"]
        return c.post(url, data=data)

    E = "/prodi/%s/halaman/sejarah/en" % A

    def versi_en():
        return str(ih.baca(A, "sejarah:en").get("versi", 0))

    def versi_id():
        return str(ih.baca(A, "sejarah").get("versi", 0))

    # ============================================================== the admin: the English tab
    teks = ko.get("/prodi/%s/halaman/sejarah" % A).get_data(as_text=True)
    cek('aria-label="Bahasa isi halaman"' in teks and 'href="%s"' % E in teks, "tab English di penyunting")
    teks = ko.get(E).get_data(as_text=True)
    cek("Sejarah: versi Inggris" in teks and teks.count('class="terjemah__sumber"') == 3 and "Prodi didirikan tahun 1990." in teks
        and 'name="%s"' % t("Akreditasi pertama") in teks and "belum diaktifkan superadmin" in teks
        and 'lang="id"><span class="tersembunyi">Teks Indonesia: </span>' in teks, "formulir Inggris: setiap teks dengan aslinya")
    r = kirim(ko, E, versi=versi_en(), versi_id=versi_id(), aksi="ajukan",
              **{t("Prodi didirikan tahun 1990."): "The study program was founded in 1990.",
                 t("Prodi didirikan"): "The study program was founded", t("Akreditasi pertama"): "slot gacor"})
    cek(r.status_code == 302 and ih.draf(ih.baca(A, "sejarah:en"))["status"] == "draf"
        and "memuat teks judi" in ko.get(E).get_data(as_text=True), "pengajuan dengan teks judi ditolak; ketikan tetap di draf")
    r = kirim(ko, E, versi=versi_en(), versi_id=versi_id(), aksi="ajukan",
              **{t("Prodi didirikan tahun 1990."): "The study program was founded in 1990.",
                 t("Prodi didirikan"): "The study program was founded", t("Akreditasi pertama"): "First accreditation"})
    d = ih.draf(ih.baca(A, "sejarah:en"))
    cek(r.status_code == 302 and d["status"] == "menunggu" and d["isi"]["teks"]["Akreditasi pertama"] == "First accreditation"
        and d["isi"]["asal"] == {"uraian": "Prodi didirikan tahun 1990."}, "operator mengajukan versi Inggris: %r" % d)
    r = kirim(ko, E, versi=versi_en(), versi_id=versi_id(), aksi="terbitkan")
    cek(r.status_code == 403 and ih.terbit(A, "sejarah:en") is None, "operator tidak menerbitkan versi Inggris")
    teks = ka.get(E + "/pratinjau").get_data(as_text=True)
    cek('<html lang="en">' in teks and "The study program was founded in 1990." in teks and ">Timeline<" in teks
        and ">Year<" in teks and "Prodi didirikan" not in teks, "pratinjau Inggris")
    r = kirim(ka, E, versi=versi_en(), versi_id=versi_id(), aksi="kembalikan", catatan="Periksa ejaan.")
    cek(r.status_code == 302 and ih.draf(ih.baca(A, "sejarah:en"))["status"] == "dikembalikan", "admin mengembalikan")
    r = kirim(ka, E, versi=versi_en(), versi_id=versi_id(), aksi="terbitkan",
              **{t("Prodi didirikan tahun 1990."): "The study program was founded in 1990.",
                 t("Prodi didirikan"): "The study program was founded", t("Akreditasi pertama"): "First accreditation"})
    cek(r.status_code == 302 and ih.terbit(A, "sejarah:en") and ih.draf(ih.baca(A, "sejarah:en")) is None,
        "admin menerbitkan versi Inggris")
    cek(halaman("en/profil/sejarah") is None, "situs: tanpa saklar superadmin belum ada versi Inggris")

    # ============================================================== the site
    registri.atur(A, "penguji", inggris=True)
    b = bangun.Pembangun(produksi=False)
    b.bangun()
    cek(not b.peringatan, "bangun tanpa peringatan: %r" % b.peringatan[:3])
    sej_en = halaman("en/profil/sejarah") or ""
    cek("The study program was founded in 1990." in sej_en and "<th scope=\"col\">Year</th>" in sej_en
        and "<th scope=\"col\">Event</th>" in sej_en and "First accreditation" in sej_en and "Prodi didirikan" not in sej_en
        and '<html lang="en">' in sej_en, "halaman Sejarah Inggris")
    cek('hreflang="en" lang="en">English</a>' in halaman("profil/sejarah") and ">History</a>" in halaman("en/profil"),
        "tautan bahasa dan menu Inggris memuat Sejarah")
    cek(halaman("en/profil/visi-misi") is None and ">Vision, Mission" not in halaman("en/profil"),
        "halaman tanpa versi Inggris tidak ada di menu Inggris")
    teks = ka.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek("Versi Inggris: <strong>1 dari 22</strong>" in teks and 'href="%s">Terbit' % E in teks, "daftar: kolom English")
    teks = ka.get(E).get_data(as_text=True)
    cek("/s1informatika/en/profil/sejarah/\">Lihat versi Inggris di situs" in teks, "penyunting menautkan versi Inggris di situs")

    # the accreditation documents with English titles
    EA = "/prodi/%s/halaman/akreditasi/en" % A
    r = kirim(ka, EA, versi="0", versi_id=str(ih.baca(A, "akreditasi")["versi"]), aksi="terbitkan",
              **{t("Sertifikat akreditasi"): "Accreditation certificate"})
    akr = halaman("en/profil/akreditasi") or ""
    cek(r.status_code == 302 and "Accreditation certificate" in akr and ">Accreditation documents<" in akr
        and "PDF, 1 pages" in akr, "dokumen akreditasi berjudul Inggris")

    # the Indonesian page changes: a new row, a new introduction
    ih.terbitkan(A, "sejarah", {"uraian": "Prodi didirikan tahun 1990 di Manado.", "linimasa": [
        {"tahun": 1990, "peristiwa": "Prodi didirikan"}, {"tahun": 2010, "peristiwa": "Akreditasi pertama"},
        {"tahun": 2024, "peristiwa": "Akreditasi Unggul"}]}, "penguji")
    bangun.Pembangun(produksi=False).bangun()
    sej_en = halaman("en/profil/sejarah") or ""
    cek("The study program was founded in 1990." in sej_en and "2024" not in sej_en and "First accreditation" in sej_en,
        "versi Indonesia berubah: uraian lama tetap, baris baru menunggu terjemahan")
    k = ii.keadaan(A, "sejarah")
    cek(k["perlu"] == 2 and k["tayang"], "perlu diperbarui: 2 teks")
    teks = ka.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek("perlu diperbarui (2 teks)" in teks and "1 halaman berversi Inggris perlu diperbarui" in teks, "daftar: perlu diperbarui")
    teks = ka.get(E).get_data(as_text=True)
    cek("Perlu diperbarui:</strong> 2 teks" in teks and "berubah sejak diterjemahkan; isian ini masih berisi terjemahan" in teks,
        "penyunting menandai teks yang berubah")
    r = kirim(ka, E, versi=versi_en(), versi_id=versi_id(), aksi="terbitkan",
              **{t("Prodi didirikan tahun 1990 di Manado."): "The study program was founded in Manado in 1990.",
                 t("Prodi didirikan"): "The study program was founded", t("Akreditasi pertama"): "First accreditation",
                 t("Akreditasi Unggul"): "Excellent accreditation"})
    sej_en = halaman("en/profil/sejarah") or ""
    cek(r.status_code == 302 and "founded in Manado in 1990" in sej_en and "Excellent accreditation" in sej_en
        and ii.keadaan(A, "sejarah")["perlu"] == 0, "diperbarui: terbit lengkap")
    cek(ih.terbit(A, "sejarah:en")["teks"].keys() == {"Prodi didirikan tahun 1990 di Manado.", "Prodi didirikan",
                                                      "Akreditasi pertama", "Akreditasi Unggul"},
        "terjemahan yang tidak dipakai lagi dibuang")

    # a change of the Indonesian draft while translating
    r = kirim(ka, E, versi=versi_en(), versi_id="0", aksi="simpan", **{"t.0123456789abcdef": "Lost"})
    cek(r.status_code == 302 and "berubah saat Anda menerjemahkan" in ka.get(E).get_data(as_text=True),
        "perubahan versi Indonesia saat menerjemahkan diberitahukan")

    # the history of the English version
    teks = ka.get(E + "/riwayat").get_data(as_text=True)
    lama = re.findall(r'/en/riwayat/([0-9-]+)\?bagian=terbit', teks)
    cek("Riwayat: Sejarah (versi Inggris)" in teks and lama, "riwayat versi Inggris")
    if lama:
        teks = ka.get(E + "/riwayat/%s?bagian=terbit" % lama[-1]).get_data(as_text=True)
        cek('<html lang="en">' in teks and "Kembali ke riwayat versi Inggris" in teks, "versi lama Inggris dipratinjau")
        r = kirim(ka, E + "/riwayat/%s" % lama[-1], versi=versi_en(), bagian="terbit")
        cek(r.status_code == 302 and ih.draf(ih.baca(A, "sejarah:en")) is not None, "versi lama Inggris dijadikan draf")
        kirim(ka, E, versi=versi_en(), versi_id=versi_id(), aksi="buang")
        cek(ih.draf(ih.baca(A, "sejarah:en")) is None, "draf versi Inggris dibuang")
    teks = ks.get("/super/riwayat").get_data(as_text=True)
    cek("halaman Sejarah (versi Inggris)" in teks, "riwayat superadmin menyebut versi Inggris")

    # completeness
    teks = ks.get("/super/kelengkapan").get_data(as_text=True)
    cek("aktif, 1/22" in teks, "kelengkapan: kolom versi Inggris")
    baris = list(csv.reader(io.StringIO(ks.get("/super/kelengkapan.csv").get_data(as_text=True).lstrip("﻿"))))
    kolom = dict(zip(baris[0], [b_ for b_ in baris[1:] if b_[0] == A][0]))
    cek(kolom["inggris_aktif"] == "ya" and kolom["wajib_terbit_en"] == "1" and kolom["perlu_diperbarui_en"] == "0",
        "CSV kelengkapan: %r" % {k_: kolom[k_] for k_ in ("inggris_aktif", "wajib_terbit_en", "perlu_diperbarui_en")})

    jumlah, temuan = periksa_situs(lokasi.publik(), "isi-inggris")
    cek(not temuan, "pemeriksaan halaman: %r" % temuan[:5])

    # withdrawn: the English page goes, the Indonesian one stays
    r = kirim(ka, E, versi=versi_en(), versi_id=versi_id(), aksi="tarik")
    cek(r.status_code == 302 and halaman("en/profil/sejarah") is None and halaman("profil/sejarah")
        and "bar-atas__bahasa" not in halaman("profil/sejarah"), "versi Inggris ditarik dari situs")
    cek(ii.keadaan(A, "sejarah")["draf"] is not None, "terjemahan yang ditarik tetap di draf")
    # the Indonesian page withdrawn: its English version does not show either
    kirim(ka, E, versi=versi_en(), versi_id=versi_id(), aksi="terbitkan")
    cek(halaman("en/profil/sejarah") is not None, "versi Inggris terbit lagi")
    ih.tarik(A, "sejarah", "penguji")
    bangun.Pembangun(produksi=False).bangun()
    cek(halaman("en/profil/sejarah") is None and not ii.keadaan(A, "sejarah")["tayang"]
        and ih.terbit(A, "sejarah:en") is not None, "versi Indonesia ditarik: versi Inggris tidak tampil")
    # published Indonesian content that fails the checks now (a word added to the spam filter): neither version shows
    data = ih.baca(A, "sejarah")
    data["terbit"] = {"isi": {"uraian": "Prodi didirikan tahun 1990 di Manado. Slot gacor.", "linimasa": [
        {"tahun": 1990, "peristiwa": "Prodi didirikan"}]}, "oleh": "penguji", "waktu": "2026-11-19T10:00:00"}
    lokasi.tulis_json(lokasi.path_data(ih.nama_berkas(A, "sejarah")), data)
    bangun.Pembangun(produksi=False).bangun()
    cek(halaman("profil/sejarah") is not None and "Slot gacor" not in halaman("profil/sejarah")
        and halaman("en/profil/sejarah") is None, "isi Indonesia yang tidak lolos: versi Inggris juga tidak tampil")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_isi_inggris: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
