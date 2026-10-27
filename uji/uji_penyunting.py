# -*- coding: utf-8 -*-
"""Fase 2 langkah 2: the editor of a programme's own pages (platform/admin/penyunting.py, isi_admin.py) and the drafts
of isi_halaman.py.

- the form of every template: unique ids, a label for every field, no inline script or style, under the admin's limit
  of form parts with every list full; reading an unchanged form gives back exactly the content it was made from
  (every template, with real files);
- reading what is typed: numbers with thousand separators, decimals with a comma, values not valid yet kept as typed
  (and marked), one-line texts, control characters, choices the template does not offer, unknown keys kept; the form
  can never add list items or file records by itself;
- the list buttons (add, remove and put back, move) and their limits; buttons a page does not show are refused;
- drafts: versions, the history only on explicit saves, a save from an older version refused (also from two threads at
  once), other programmes' files refused, size limit, discarding, empty rows dropped, the preview leaving out values
  that are not valid yet, a restored version going on counting;
- through the admin: the list of pages, adding rows and filling them, PDFs and photos (with their checks), problems
  marked at their field and listed with links, two people editing the same page, discarding, the preview with the
  site's styles and macros, escaping everywhere, operators writing too, the site unchanged by drafts, the audit log.
Who may open each route at all is tested in uji_admin.py.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import copy
import io
import json
import os
import re
import shutil
import sys
import tempfile
import threading

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import flask  # noqa: F401
    from werkzeug.datastructures import MultiDict
except ImportError:
    print("uji_penyunting: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-penyunting-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import bangun  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import penyunting as py  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import Formulir, gambar, pdf, prodi  # noqa: E402

A, B = "55201", "20201"
IP = "103.84.116.30"
MENYUSUL = "Informasi ini sedang dilengkapi oleh Program Studi"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def tanpa_judul_pdf(x):
    """Content with the titles of its PDFs left out (the editor keeps them in step with their row)."""
    if isinstance(x, dict):
        return {k: tanpa_judul_pdf(v) for k, v in x.items() if not (k == "judul" and x.get("jenis") == "pdf")}
    if isinstance(x, list):
        return [tanpa_judul_pdf(v) for v in x]
    return x


def jumlah_unggahan():
    return sum(len(n) for _a, _d, n in os.walk(lokasi.unggahan()))


def versi_riwayat(kode, id_):
    return len([v for v in riwayat.daftar(100000) if v["berkas"] == "prodi/%s/halaman-%s" % (kode, id_)])


try:
    # ============================================================== platform with two programmes
    os.makedirs(os.environ["WWW_DATA"])
    for nama, isi in {"prodi": {"program": [prodi(A, "Teknik Informatika"), prodi(B, "Teknik Elektro")]},
                      "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "jenis": "fakultas",
                                         "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                      "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)
    foto_a = media.simpan_foto(A, gambar(1200, 900), "Gedung laboratorium")
    pdf_a = media.simpan_pdf(A, pdf(), "Dokumen uji")
    foto_b = media.simpan_foto(B, gambar(800, 600), "Foto prodi lain")
    pdf_b = media.simpan_pdf(B, pdf(), "Dokumen prodi lain")

    def berkas_a(jenis):
        return dict(pdf_a) if jenis == "dokumen" else json.loads(json.dumps(foto_a))

    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    MAKS_BAGIAN = app.config["MAX_FORM_PARTS"]

    # ============================================================== the form of every template
    def url_uji(rekam):
        return "/berkas/" + rekam.get("jalur", "")
    for id_, templat in ih.TEMPLAT.items():
        cek(py.bagian_form(templat) < MAKS_BAGIAN, "%s: formulir penuh (%d bagian) di bawah batas %d" % (
            id_, py.bagian_form(templat), MAKS_BAGIAN))
        for label, isi in (("kosong", {}), ("contoh", ih.isi_contoh(id_, 3, berkas_a))):
            html = py.formulir(templat, isi, py.Tampil(url_berkas=url_uji))
            f = Formulir(html, semua=True)
            ganda = sorted({x for x in f.id if f.id.count(x) > 1})
            cek(not ganda, "%s (%s): id ganda %r" % (id_, label, ganda[:5]))
            tanpa_label = [x for x in f.kontrol if x not in f.label_for]
            cek(not tanpa_label, "%s (%s): isian tanpa label %r" % (id_, label, tanpa_label[:5]))
            cek("<script" not in html and " style=" not in html, "%s (%s): tanpa skrip/gaya sebaris" % (id_, label))
            hasil = py.baca(templat, copy.deepcopy(isi), py.Konteks(f.data(), {}, A))
            if label == "kosong":
                cek(ih.kosong(templat, hasil) and not ih.periksa(id_, hasil, A), "%s: formulir kosong tetap kosong" % id_)
            else:
                cek(tanpa_judul_pdf(hasil) == tanpa_judul_pdf(isi),
                    "%s: formulir yang tidak diubah memberi isi yang sama" % id_)
                cek(not ih.periksa(id_, hasil, A), "%s: isi contoh dari formulir tetap lolos" % id_)

    # ============================================================== reading what is typed
    T = ih.TEMPLAT["kerja-sama"]
    awal = {"uraian": "Lama.", "kunci_lama": "disimpan", "daftar": [
        {"mitra": "Universitas X", "jenis": "Penelitian", "tingkat": "Nasional", "bukti": dict(pdf_a), "lain": 1}]}

    def baca_form(isi, isian, templat=T, kode=A):
        k = py.Konteks(MultiDict(isian), {}, kode)
        return py.baca(templat, copy.deepcopy(isi), k)
    h = baca_form(awal, {"daftar.0.mulai": "2.025", "daftar.0.selesai": "20o5", "daftar.0.mitra": " Universitas\r\nY \x07",
                         "daftar.0.jenis": "Hiburan", "uraian": "Baris satu\r\n\r\nBaris\x0bdua"})
    r = h["daftar"][0]
    cek(r["mulai"] == 2025 and r["selesai"] == "20o5", "tahun ber-titik dibaca, tahun salah disimpan apa adanya: %r" % r)
    cek(r["mitra"] == "Universitas Y", "teks satu baris: baris baru jadi spasi, karakter kendali dibuang: %r" % r["mitra"])
    cek(r["jenis"] == "Penelitian", "pilihan yang tidak ditawarkan diabaikan")
    cek(h["uraian"] == "Baris satu\n\nBaris\ndua", "paragraf: baris tetap, jeda baris Word jadi baris baru: %r" % h["uraian"])
    cek(h["kunci_lama"] == "disimpan" and r["lain"] == 1, "kunci yang tidak dikenal templat disimpan")
    cek(r["bukti"]["jalur"] == pdf_a["jalur"] and r["bukti"]["judul"] == "Bukti kerja sama: Universitas Y",
        "PDF tetap, judulnya mengikuti barisnya: %r" % r["bukti"].get("judul"))
    cek(any("Tahun selesai: harus angka bulat" in m for m in ih.periksa("kerja-sama", h, A)), "tahun salah ditandai pemeriksaan")
    h = baca_form(awal, {"daftar.0.bukti": json.dumps(pdf_b), "berkas::daftar.0.bukti": "x", "daftar.1.mitra": "Baru",
                         "daftar.0.mitra": "Universitas X"})
    cek(h["daftar"][0]["bukti"]["jalur"] == pdf_a["jalur"] and len(h["daftar"]) == 1,
        "formulir tidak bisa memasang rekaman berkas atau menambah baris sendiri")
    h = baca_form(awal, {"hapus::daftar.0.bukti": "1"})
    cek(h["daftar"][0]["bukti"] is None, "berkas dilepas lewat kotak centang")
    h = baca_form(awal, {})
    cek(h["uraian"] == "Lama." and h["daftar"][0]["mitra"] == "Universitas X", "isian yang tidak dikirim tidak berubah")
    S = ih.TEMPLAT["survei-kepuasan"]
    for teks_, harap in (("87,5", 87.5), ("100", 100), ("100%", 100), (" 0,25 ", 0.25), ("", None), ("abc", "abc"),
                         ("87,555", 87.555)):
        h = baca_form({"hasil": [{"survei": "Alumni", "aspek": "Layanan"}]}, {"hasil.0.baik": teks_}, S)
        cek(h["hasil"][0]["baik"] == harap, "persen %r dibaca %r, dapat %r" % (teks_, harap, h["hasil"][0]["baik"]))
    h = baca_form({"hasil": [{"survei": "Alumni", "aspek": "Layanan", "baik": 87.555}]}, {}, S)
    html = py.formulir(S, h, py.Tampil())
    cek('value="87,555"' in html, "persen yang belum sah ditampilkan apa adanya, tidak dibulatkan")
    P = ih.TEMPLAT["penelitian"]
    h = baca_form({"daftar": [{"judul": "J", "tahun": 2024, "mahasiswa": True}]}, {"daftar.0.judul": "J"}, P)
    cek(h["daftar"][0]["mahasiswa"] is False, "kotak centang yang tidak dicentang menjadi tidak")
    K = ih.TEMPLAT["kurikulum"]
    for teks_, harap in (("1.234", 1234), ("7", 7), (" 3 ", 3), ("1.5", "1.5"), ("", None), ("-2", -2)):
        h = baca_form({"mata_kuliah": [{"nama": "Algoritma"}]}, {"mata_kuliah.0.sks": teks_}, K)
        cek(h["mata_kuliah"][0]["sks"] == harap, "angka %r dibaca %r, dapat %r" % (teks_, harap, h["mata_kuliah"][0]["sks"]))
    cek(any("SKS: harus antara 0 dan 30" in m for m in ih.periksa("kurikulum", {"mata_kuliah": [
        {"nama": "A", "semester": 1, "sks": -2}]}, A)), "angka di luar batas ditandai")
    # a choice the template no longer offers stays until it is changed
    html = py.formulir(T, {"daftar": [{"mitra": "M", "jenis": "Hiburan"}]}, py.Tampil())
    cek('<option value="Hiburan" selected>' in html, "pilihan lama tetap tampil terpilih")
    cek(baca_form({"daftar": [{"mitra": "M", "jenis": "Hiburan"}]}, {"daftar.0.jenis": "Hiburan"})["daftar"][0]["jenis"] == "Hiburan",
        "pilihan lama yang dikirim ulang tetap disimpan (pemeriksaan menandainya)")

    # escaping in the form
    jahat = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
    html = py.formulir(T, {"uraian": jahat, "daftar": [{"mitra": jahat, "jenis": jahat}]}, py.Tampil())
    cek("<script" not in html and "<img src=x" not in html and "&lt;script&gt;" in html, "formulir meng-escape semua nilai")

    # ============================================================== the list buttons
    isi = {"daftar": [{"mitra": "A"}, {"mitra": "B"}, {"mitra": "C"}]}
    cek(py.terapkan_aksi(T, isi, "tambah:daftar") == ("daftar.3", None) and isi["daftar"][3] == {}, "tambah baris di akhir")
    cek(py.terapkan_aksi(T, isi, "naik:daftar.2") == ("daftar.1", None) and [x.get("mitra") for x in isi["daftar"]][:3] == ["A", "C", "B"],
        "naikkan baris")
    cek(py.terapkan_aksi(T, isi, "turun:daftar.0")[0] == "daftar.1" and isi["daftar"][1]["mitra"] == "A", "turunkan baris")
    tujuan, dihapus = py.terapkan_aksi(T, isi, "hapus:daftar.1")
    cek(tujuan == "daftar" and dihapus == {"jalur": "daftar", "indeks": 1, "nilai": {"mitra": "A"}} and len(isi["daftar"]) == 3,
        "hapus baris mengembalikan butir yang dihapus")
    cek(py.kembalikan(T, isi, dihapus) == "daftar.1" and isi["daftar"][1] == {"mitra": "A"}, "butir yang dihapus dikembalikan ke tempatnya")
    isi2 = {}
    cek(py.terapkan_aksi(T, isi2, "tambah:daftar")[0] == "daftar.0" and isi2 == {"daftar": [{}]}, "tambah ke daftar yang belum ada")
    for aksi in ("naik:daftar.0", "turun:daftar.3", "hapus:daftar.9", "tambah:uraian", "tambah:../x", "tambah:tidakada",
                 "hapus:daftar", "tambah:daftar.0.mitra", "hapus:daftar.0.mitra", "geser:daftar.0", "tambah:", "hapus:daftar.-1",
                 "hapus:daftar.\uff11", "tambah:Daftar"):
        try:
            py.terapkan_aksi(T, copy.deepcopy(isi), aksi)
            gagal.append("tombol %r harus ditolak" % aksi)
        except py.TombolSalah:
            pass
    penuh = {"tautan": [{"label": "x", "alamat": "https://a.id/"}] * 10}
    try:
        py.terapkan_aksi(ih.TEMPLAT["perpustakaan"], penuh, "tambah:tautan")
        gagal.append("daftar penuh harus menolak tambah")
    except py.DaftarPenuh as e:
        cek("paling banyak" in str(e) and len(penuh["tautan"]) == 10, "pesan daftar penuh")

    # problems inside a row still entirely empty are not marked; the place of a problem in words matches the checks
    isi = {"daftar": [{}, {"mitra": "", "jenis": "Penelitian"}]}
    m = py.masalah_tampil(T, isi, ih.daftar_masalah("kerja-sama", isi, A))
    cek(m and all(j.startswith("daftar.1.") for j, _t, _p in m), "baris kosong tidak ditandai, baris setengah terisi ditandai: %r" % m)
    for id_ in ("kerja-sama", "visi-misi", "survei-kepuasan", "laboratorium"):
        contoh = ih.isi_contoh(id_, 2)
        rusak = json.loads(json.dumps(contoh).replace('"[CONTOH] ', '"' + "x" * 12000))
        for j, tempat, _p in ih.daftar_masalah(id_, rusak, A):
            cek(py.label_jalur(ih.TEMPLAT[id_], j) == tempat, "%s: tempat %r == %r" % (id_, py.label_jalur(ih.TEMPLAT[id_], j), tempat))

    # ============================================================== drafts (isi_halaman)
    cek(ih.simpan_draf(A, "sejarah", {"uraian": "Draf pertama."}, "penguji", riwayat=False) == 1, "draf pertama: versi 1")
    data = ih.baca(A, "sejarah")
    cek(ih.draf(data)["isi"] == {"uraian": "Draf pertama."} and data["terbit"] is None and data["diubah"]["oleh"] == "penguji",
        "draf tersimpan, isi terbit tidak berubah")
    cek(ih.isi_kerja(data) == {"uraian": "Draf pertama."}, "penyunting mulai dari draf")
    cek(versi_riwayat(A, "sejarah") == 0, "simpanan tanpa riwayat")
    cek(ih.simpan_draf(A, "sejarah", {"uraian": "Draf kedua."}, "penguji", versi=1) == 2 and versi_riwayat(A, "sejarah") == 1,
        "simpanan biasa masuk riwayat")
    try:
        ih.simpan_draf(A, "sejarah", {"uraian": "Dari versi lama."}, "lain", versi=1)
        gagal.append("draf dari versi lama harus ditolak")
    except ih.GagalIsi as e:
        cek("baru saja diubah oleh penguji" in str(e), "pesan bentrok menyebut siapa: %s" % e)
    for isi, pesan in (("bukan objek", "bukan objek"), ({"foto": [{"berkas": foto_b}]}, "foto prodi lain"),
                       ({"dokumen": [{"judul": "x", "berkas": pdf_b}]}, "PDF prodi lain"),
                       ({"uraian": "x" * (ih.MAKS_DRAF + 10)}, "terlalu besar")):
        id_ = "visi-misi" if "dokumen" in isi else "sejarah"
        sebelum = ih.baca(A, id_)
        try:
            ih.simpan_draf(A, id_, isi, "penguji")
            gagal.append("draf %s harus ditolak" % pesan)
        except ih.GagalIsi:
            pass
        cek(ih.baca(A, id_) == sebelum, "draf %s yang ditolak tidak menulis apa pun" % pesan)
        if ih.baca(A, id_) != sebelum:                 # keep the rest of the suite on the state it expects
            lokasi.tulis_json(lokasi.path_data(ih.nama_berkas(A, id_)), sebelum) if sebelum.get("versi") else \
                os.remove(lokasi.path_data(ih.nama_berkas(A, id_)))
    try:
        ih.simpan_draf(A, "sejarah", {}, "penguji", dihapus={"jalur": "foto", "indeks": 0, "nilai": {"berkas": foto_b}})
        gagal.append("butir terhapus berisi berkas prodi lain harus ditolak")
    except ih.GagalIsi:
        pass
    cek(ih.draf(ih.baca(A, "sejarah"))["isi"] == {"uraian": "Draf kedua."}, "draf yang ditolak tidak menulis apa pun")
    # two saves at once from the same version: exactly one wins
    v = ih.baca(A, "sejarah")["versi"]
    hasil_utas, mulai = [], threading.Barrier(8)

    def simpan_bersamaan(n):
        mulai.wait()
        try:
            ih.simpan_draf(A, "sejarah", {"uraian": "Utas %d" % n}, "utas%d" % n, versi=v, riwayat=False)
            hasil_utas.append(n)
        except ih.GagalIsi:
            pass
    utas = [threading.Thread(target=simpan_bersamaan, args=(n,)) for n in range(8)]
    for x in utas:
        x.start()
    for x in utas:
        x.join()
    cek(len(hasil_utas) == 1 and ih.baca(A, "sejarah")["versi"] == v + 1, "simpanan bersamaan: tepat satu yang menang (%r)" % hasil_utas)
    # discarding, emptied rows, the preview's copy, a restored version
    v = ih.baca(A, "sejarah")["versi"]
    n_riwayat = versi_riwayat(A, "sejarah")
    cek(ih.buang_draf(A, "sejarah", "penguji", v) == v + 1 and ih.draf(ih.baca(A, "sejarah")) is None
        and versi_riwayat(A, "sejarah") == n_riwayat + 1, "draf dibuang, tetap ada di riwayat")
    cek(ih.isi_kerja(ih.baca(A, "sejarah")) == {}, "tanpa draf dan isi terbit penyunting mulai kosong")
    rapi = ih.rapikan(ih.TEMPLAT["sejarah"], {"uraian": "U", "linimasa": [{}, {"tahun": 2000}, {"peristiwa": ""}], "foto": [{}]})
    cek(rapi == {"uraian": "U", "linimasa": [{"tahun": 2000}], "foto": []}, "baris kosong dibuang saat disimpan: %r" % rapi)
    sah = ih.isi_sah("sejarah", {"uraian": "[x](javascript:alert(1))", "linimasa": [{"tahun": "20o5", "peristiwa": "Berdiri"},
                                                                                  {"tahun": 1990, "peristiwa": "Akreditasi"}]}, A)
    cek(sah["uraian"] is None and sah["linimasa"][0]["tahun"] is None and sah["linimasa"][1]["tahun"] == 1990,
        "pratinjau meninggalkan nilai yang belum sah: %r" % sah)
    bagian, _h = ih.tampilan("sejarah", sah)
    cek(bagian and bagian[0]["jenis"] == "tabel" and len(bagian[0]["baris"]) == 2, "pratinjau isi yang belum sah tetap tampil")
    v1 = ih.terbitkan(A, "visi-misi", {"visi": "Visi lama."}, "penguji")
    v2 = ih.terbitkan(A, "visi-misi", {"visi": "Visi baru."}, "penguji", versi=v1)
    lama = [x for x in riwayat.daftar(1000) if x["berkas"] == "prodi/%s/halaman-visi-misi" % A][0]
    riwayat.pulihkan("prodi/%s/halaman-visi-misi" % A, lama["versi"], "penguji", "uji")
    data = ih.baca(A, "visi-misi")
    cek(ih.terbit(A, "visi-misi") == {"visi": "Visi lama."} and data["versi"] == v2 + 1,
        "versi yang dipulihkan terus menghitung (bukan kembali ke %d): %r" % (v1, data["versi"]))
    try:
        ih.terbitkan(A, "visi-misi", {"visi": "Dari formulir sebelum pemulihan."}, "lain", versi=v1)
        gagal.append("formulir yang dibuka sebelum pemulihan harus ditolak")
    except ih.GagalIsi:
        pass
    ih.tarik(A, "visi-misi", "penguji")

    # ============================================================== through the admin
    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_, sementara, SANDI[nama])
        return akun.ambil(id_)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("opa", "operator", [A]), ("admb", "admin", [B])):
        akun_baru(nama, peran, p, super_)
    klien = {}
    for i, nama in enumerate(("adma", "opa", "admb")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (40 + i)
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ka, ko = klien["adma"], klien["opa"]
    URL = "/prodi/%s/halaman/" % A

    def buka(c, id_, tambahan=""):
        r = c.get(URL + id_ + tambahan)
        cek(r.status_code == 200, "buka penyunting %s: %s" % (id_, r.status_code))
        return r.get_data(as_text=True)

    def kirim(c, id_, html, aksi="simpan", ubah=None, berkas=None):
        f = Formulir(html)
        data = f.data(ubah, aksi)
        for nama in f.berkas:                       # a browser sends every file field, empty when nothing is chosen
            data.add(nama, (io.BytesIO(b""), ""))
        for nama, (isi, nama_berkas) in (berkas or {}).items():
            data.poplist(nama)
            data.add(nama, (io.BytesIO(isi), nama_berkas))
        return c.post(URL + id_, data=data, content_type="multipart/form-data")

    # the list of pages
    r = ka.get("/prodi/%s/halaman" % A)
    teks = r.get_data(as_text=True)
    cek(r.status_code == 200 and teks.count('href="%s' % URL) == len(ih.TEMPLAT), "daftar memuat ke-24 halaman")
    cek("0 dari 22" in teks and "Belum diisi" in teks, "daftar: jumlah halaman wajib yang berisi")
    cek("Isi halaman" in ka.get("/prodi/%s/" % A).get_data(as_text=True) and
        'href="/prodi/%s/halaman"' % A in ka.get("/prodi/%s/" % A).get_data(as_text=True), "dasbor menautkan isi halaman")
    for id_ in ih.TEMPLAT:
        html = buka(ka, id_)
        f = Formulir(html)
        cek(("versi", "0") in f.isian or any(n == "versi" for n, _v in f.isian), "%s: formulir membawa versi" % id_)
        cek("<script" not in html and " style=" not in html, "%s: penyunting tanpa skrip/gaya sebaris" % id_)
        tombol = re.findall(r'<button type="submit"[^>]* value="([^"]+)"', html[html.index("formulir--sunting"):])
        cek(tombol and tombol[0] == "simpan", "%s: Enter di isian menekan Simpan draf, bukan tombol daftar: %r" % (id_, tombol[:1]))
    cek(ka.get(URL + "tidak-ada").status_code == 404 and ka.get(URL + "akreditasi").status_code == 404,
        "halaman tanpa templat isi tidak punya penyunting")

    # adding a row, filling it, a value not valid yet, a PDF
    html = buka(ka, "kerja-sama")
    r = kirim(ka, "kerja-sama", html, "tambah:daftar")
    cek(r.status_code == 302 and r.headers["Location"].endswith("?buka=daftar.0#f-daftar-0"), "tambah baris: ke baris baru %s" % r.headers.get("Location"))
    data = ih.baca(A, "kerja-sama")
    cek(ih.draf(data)["isi"]["daftar"] == [{}] and versi_riwayat(A, "kerja-sama") == 0, "baris baru di draf, tanpa riwayat")
    html = buka(ka, "kerja-sama", "?buka=daftar.0")
    cek(re.search(r'<details class="butir-sunting" id="f-daftar-0" open>', html) and "ringkasan-galat" not in html,
        "baris baru terbuka, tanpa tanda galat")
    n_berkas = jumlah_unggahan()
    r = kirim(ka, "kerja-sama", html, ubah={"daftar.0.mitra": "Universitas X", "daftar.0.jenis": "Penelitian",
                                            "daftar.0.tingkat": "Nasional", "daftar.0.mulai": "20o5"},
              berkas={"berkas::daftar.0.bukti": (pdf(), "mou.pdf")})
    cek(r.status_code == 302, "simpan draf: %s" % r.status_code)
    baris = ih.draf(ih.baca(A, "kerja-sama"))["isi"]["daftar"][0]
    cek(baris["mitra"] == "Universitas X" and baris["mulai"] == "20o5", "isian tersimpan apa adanya: %r" % baris)
    cek(isinstance(baris.get("bukti"), dict) and baris["bukti"]["judul"] == "Bukti kerja sama: Universitas X"
        and jumlah_unggahan() == n_berkas + 1, "PDF diunggah dan diberi judul barisnya")
    cek(versi_riwayat(A, "kerja-sama") == 1, "simpan draf masuk riwayat")
    html = buka(ka, "kerja-sama")
    cek('id="ringkasan-galat"' in html and 'href="#f-daftar-0-mulai">Daftar kerja sama baris 1, Tahun mulai</a>: harus angka bulat' in html,
        "ringkasan masalah menautkan isiannya")
    tag = re.search(r'<input id="f-daftar-0-mulai" [^>]*>', html)
    cek(tag and 'value="20o5"' in tag.group(0) and 'aria-invalid="true"' in tag.group(0) and "f-daftar-0-mulai-galat" in tag.group(0)
        and '<p class="galat-isian" id="f-daftar-0-mulai-galat">harus angka bulat</p>' in html, "isian salah ditandai dan tetap apa adanya")
    cek('href="/prodi/%s/berkas/%s"' % (A, baris["bukti"]["jalur"]) in html, "PDF yang tersimpan ditautkan di formulir")
    cek(ih.terbit(A, "kerja-sama") is None, "situs tetap tanpa isi selama draf dikerjakan")
    r = kirim(ka, "kerja-sama", html, ubah={"daftar.0.mulai": "2005"})
    cek("ringkasan-galat" not in buka(ka, "kerja-sama"), "tahun dibetulkan: tidak ada masalah lagi")
    r = kirim(ka, "kerja-sama", buka(ka, "kerja-sama"))
    cek(r.status_code == 302 and "Tidak ada perubahan" in ka.get(r.headers["Location"]).get_data(as_text=True),
        "simpan tanpa perubahan tidak menulis apa pun")
    n_berkas = jumlah_unggahan()
    r = kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), berkas={"berkas::daftar.0.bukti": (b"%PDF-1.4\nsampah", "rusak.pdf")})
    teks = ka.get(r.headers["Location"]).get_data(as_text=True)
    cek("Daftar kerja sama baris 1, Bukti kerja sama — PDF tidak disimpan: PDF rusak" in teks and jumlah_unggahan() == n_berkas,
        "PDF rusak ditolak dengan tempatnya, tidak ada berkas tersimpan")
    cek(ih.draf(ih.baca(A, "kerja-sama"))["isi"]["daftar"][0]["bukti"]["jalur"] == baris["bukti"]["jalur"], "PDF lama tetap")

    # a second row, moving, removing and putting back
    kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), "tambah:daftar")
    kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), ubah={"daftar.1.mitra": "Pemda Y", "daftar.1.jenis": "Pengabdian kepada masyarakat",
                                                          "daftar.1.tingkat": "Lokal"})
    r = kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), "naik:daftar.1")
    cek(r.headers["Location"].endswith("?buka=daftar.0#f-daftar-0") and
        [x["mitra"] for x in ih.draf(ih.baca(A, "kerja-sama"))["isi"]["daftar"]] == ["Pemda Y", "Universitas X"], "naikkan baris")
    r = kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), "hapus:daftar.0")
    cek(r.headers["Location"].endswith("#f-daftar") and len(ih.draf(ih.baca(A, "kerja-sama"))["isi"]["daftar"]) == 1, "hapus baris")
    html = buka(ka, "kerja-sama")
    cek("Baris 1 (Pemda Y · Pengabdian kepada masyarakat · Lokal) baru saja dihapus." in html and 'value="pulihkan-butir"' in html,
        "baris yang baru dihapus ditawarkan kembali")
    r = kirim(ka, "kerja-sama", html, "pulihkan-butir")
    cek(r.headers["Location"].endswith("?buka=daftar.0#f-daftar-0") and
        [x["mitra"] for x in ih.draf(ih.baca(A, "kerja-sama"))["isi"]["daftar"]] == ["Pemda Y", "Universitas X"], "baris dikembalikan")
    cek('value="pulihkan-butir"' not in buka(ka, "kerja-sama"), "tawaran kembalikan hilang setelah dipakai")
    kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), "hapus:daftar.0")
    kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), "tambah:daftar")
    cek('value="pulihkan-butir"' not in buka(ka, "kerja-sama"), "tawaran kembalikan hanya sampai simpanan berikutnya")
    r = kirim(ka, "kerja-sama", buka(ka, "kerja-sama"))
    cek([x.get("mitra") for x in ih.draf(ih.baca(A, "kerja-sama"))["isi"]["daftar"]] == ["Universitas X"], "baris kosong dibuang saat simpan")

    # buttons and forms the page never shows
    html = buka(ka, "kerja-sama")
    for aksi in ("tambah:../x", "tambah:uraian", "hapus:daftar.9", "hapus", "geser:daftar.0", "publikasikan", "batal"):
        cek(kirim(ka, "kerja-sama", html, aksi).status_code == 400, "tombol %r ditolak" % aksi)
    cek(kirim(ka, "kerja-sama", html, ubah={"versi": None}).status_code == 400, "formulir tanpa versi ditolak")
    cek(kirim(ka, "kerja-sama", html, ubah={"versi": "x"}).status_code == 400, "versi bukan angka ditolak")

    # two people editing the same page
    html_op = buka(ko, "kerja-sama")
    kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), ubah={"uraian": "Pengantar dari admin."})
    v = ih.baca(A, "kerja-sama")["versi"]
    n_berkas = jumlah_unggahan()
    r = kirim(ko, "kerja-sama", html_op, ubah={"uraian": "Pengantar dari operator."}, berkas={"berkas::daftar.0.bukti": (pdf(), "lain.pdf")})
    teks = r.get_data(as_text=True)
    cek(r.status_code == 409 and "baru saja diubah oleh adma" in teks and "Perubahan Anda belum disimpan" in teks,
        "simpanan dari versi lama ditolak dengan nama pengubahnya: %s" % r.status_code)
    cek(ih.baca(A, "kerja-sama")["versi"] == v and ih.draf(ih.baca(A, "kerja-sama"))["isi"]["uraian"] == "Pengantar dari admin."
        and jumlah_unggahan() == n_berkas, "simpanan yang ditolak tidak menulis apa pun, termasuk berkas")
    cek(kirim(ko, "kerja-sama", html_op, "tambah:daftar").status_code == 409, "tombol daftar dari versi lama juga ditolak")
    r = kirim(ko, "kerja-sama", buka(ko, "kerja-sama"), ubah={"uraian": "Pengantar dari operator."})
    cek(r.status_code == 302 and ih.draf(ih.baca(A, "kerja-sama"))["isi"]["uraian"] == "Pengantar dari operator.",
        "operator menyimpan draf dari versi terbaru")

    # photos
    html = buka(ka, "sejarah")
    kirim(ka, "sejarah", html, "tambah:foto")
    html = buka(ka, "sejarah")
    n_berkas = jumlah_unggahan()
    r = kirim(ka, "sejarah", html, berkas={"berkas::foto.0.berkas": (gambar(1200, 800), "gedung.jpg")})
    teks = ka.get(r.headers["Location"]).get_data(as_text=True)
    cek("Foto butir 1, Foto — Foto tidak disimpan: Teks alternatif foto wajib diisi" in teks and jumlah_unggahan() == n_berkas,
        "foto tanpa teks alternatif ditolak")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), ubah={"alt::foto.0.berkas": "Gedung kuliah", "foto.0.keterangan": "Gedung 2020"},
              berkas={"berkas::foto.0.berkas": (gambar(1200, 800), "gedung.jpg")})
    f0 = ih.draf(ih.baca(A, "sejarah"))["isi"]["foto"][0]
    cek(f0["berkas"]["alt"] == "Gedung kuliah" and set(f0["berkas"]["varian"]) == {"1600", "800", "400"} and
        jumlah_unggahan() == n_berkas + 3, "foto diunggah: tiga ukuran, teks alternatif: %r" % f0["berkas"].get("varian", {}).keys())
    html = buka(ka, "sejarah")
    cek('alt="Gedung kuliah"' in html and "/prodi/%s/berkas/%s" % (A, f0["berkas"]["varian"]["400"]["jalur"]) in html,
        "foto kecil tampil di formulir dengan teks alternatifnya")
    kirim(ka, "sejarah", html, ubah={"alt::foto.0.berkas": "Gedung kuliah dari depan"})
    cek(ih.draf(ih.baca(A, "sejarah"))["isi"]["foto"][0]["berkas"]["alt"] == "Gedung kuliah dari depan", "teks alternatif diubah saja")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), berkas={"berkas::foto.0.berkas": (gambar(300, 200), "kecil.jpg")})
    cek("Foto tidak disimpan: Foto terlalu kecil" in ka.get(r.headers["Location"]).get_data(as_text=True), "foto terlalu kecil ditolak")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), berkas={"berkas::foto.0.berkas": (b"<svg onload=alert(1)>", "x.jpg")})
    cek("Foto tidak disimpan" in ka.get(r.headers["Location"]).get_data(as_text=True) and
        ih.draf(ih.baca(A, "sejarah"))["isi"]["foto"][0]["berkas"]["alt"] == "Gedung kuliah dari depan", "berkas bukan foto ditolak")
    kirim(ka, "sejarah", buka(ka, "sejarah"), ubah={"hapus::foto.0.berkas": "1"})
    d = ih.draf(ih.baca(A, "sejarah"))["isi"]
    cek(d["foto"][0]["berkas"] is None and d["foto"][0]["keterangan"] == "Gedung 2020", "foto dilepas, keterangannya tetap")
    cek("Foto butir 1, Foto</a>: wajib diisi" in buka(ka, "sejarah"), "foto galeri yang dilepas ditandai wajib")

    # escaping, the preview
    kirim(ka, "sejarah", buka(ka, "sejarah"), ubah={
        "uraian": "<script>alert(1)</script> Berdiri **1985**. Lihat [situs](https://www.unsrat.ac.id/).\n\n- satu\n- dua",
        "hapus::foto.0.berkas": None})
    kirim(ka, "sejarah", buka(ka, "sejarah"), "tambah:linimasa")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "pratinjau", ubah={"linimasa.0.tahun": "19x5", "linimasa.0.peristiwa": "Berdiri"})
    cek(r.status_code == 302 and r.headers["Location"].endswith(URL + "sejarah/pratinjau"), "simpan dan pratinjau")
    r = ka.get(URL + "sejarah/pratinjau")
    teks = r.get_data(as_text=True)
    cek(r.status_code == 200 and "<h1>Sejarah</h1>" in teks and 'class="isi-bagian isi-bagian--paragraf"' in teks,
        "pratinjau memakai makro situs")
    cek("&lt;script&gt;alert(1)&lt;/script&gt;" in teks and "<script" not in teks and "<strong>1985</strong>" in teks
        and '<a href="https://www.unsrat.ac.id/">situs</a>' in teks, "pratinjau meng-escape teks, markah terbatas jadi HTML")
    cek("19x5" not in teks and "Berdiri" in teks and "isian yang belum sah tidak ditampilkan" in teks,
        "nilai yang belum sah tidak tampil di pratinjau, jumlahnya disebut")
    cek('href="/aset-situs/prodi.css"' in teks and 'href="/aset-situs/tokens.css"' in teks and
        'href="/prodi/%s/pratinjau/warna.css"' % A in teks and "Kembali ke penyunting" in teks, "pratinjau memakai gaya situs")
    cek(" style=" not in teks, "pratinjau tanpa gaya sebaris")
    html = buka(ka, "sejarah")
    cek("&lt;script&gt;alert(1)&lt;/script&gt;" in html and "<script>alert" not in html, "penyunting meng-escape isi draf")
    r = ka.get("/aset-situs/prodi.css")
    cek(r.status_code == 200 and r.mimetype == "text/css" and ".tabel-gulir" in r.get_data(as_text=True), "gaya situs untuk pratinjau")
    for nama in ("admin.css", "..%2Fadmin%2Fapp.py", "warna.css"):
        cek(ka.get("/aset-situs/" + nama).status_code == 404, "aset situs lain ditolak: %s" % nama)
    r = ka.get("/prodi/%s/pratinjau/warna.css" % A)
    cek(r.status_code == 200 and r.mimetype == "text/css" and "--prodi-utama:" in r.get_data(as_text=True), "warna prodi untuk pratinjau")
    # a preview of a page with a stored photo and PDF shows them through the admin's file route
    kirim(ka, "laboratorium", buka(ka, "laboratorium"), "tambah:daftar")
    kirim(ka, "laboratorium", buka(ka, "laboratorium"), ubah={"daftar.0.nama": "Lab Jaringan", "alt::daftar.0.foto": "Ruang lab"},
          berkas={"berkas::daftar.0.foto": (gambar(1200, 800), "lab.jpg"), "berkas::daftar.0.sop": (pdf(), "sop.pdf")})
    lab = ih.draf(ih.baca(A, "laboratorium"))["isi"]["daftar"][0]
    teks = ka.get(URL + "laboratorium/pratinjau").get_data(as_text=True)
    cek("Lab Jaringan" in teks and "/prodi/%s/berkas/%s" % (A, lab["sop"]["jalur"]) in teks and
        "/prodi/%s/berkas/%s" % (A, lab["foto"]["varian"]["800"]["jalur"]) in teks and 'alt="Ruang lab"' in teks,
        "pratinjau memuat foto dan PDF lewat rute berkas admin")
    cek(lab["sop"]["judul"] == "SOP penggunaan: Lab Jaringan", "judul PDF kartu mengikuti namanya")

    # every page through the editor with full sample content: an unchanged form saves nothing
    for id_ in ih.TEMPLAT:
        if id_ in ("kerja-sama", "sejarah", "laboratorium"):
            continue
        ih.simpan_draf(A, id_, ih.isi_contoh(id_, 3, berkas_a), "penguji", riwayat=False)
        kirim(ka, id_, buka(ka, id_))                   # the titles of the PDFs follow their rows once
        isi_awal = ih.draf(ih.baca(A, id_))["isi"]
        v = ih.baca(A, id_)["versi"]
        r = kirim(ka, id_, buka(ka, id_))
        cek(r.status_code == 302 and ih.baca(A, id_)["versi"] == v and ih.draf(ih.baca(A, id_))["isi"] == isi_awal,
            "%s: formulir tanpa perubahan tidak menulis apa pun" % id_)
        teks = ka.get(URL + id_ + "/pratinjau").get_data(as_text=True)
        cek("isi-bagian" in teks and "[CONTOH]" in teks, "%s: pratinjau isi contoh" % id_)
        html = buka(ka, id_)
        f = Formulir(html)
        tanpa_label = [x for x in f.kontrol if x not in f.label_for]
        cek(not tanpa_label and len(f.id) == len(set(f.id)), "%s: halaman penyunting: label dan id (%r)" % (id_, tanpa_label[:3]))

    # discarding a draft
    v = ih.baca(A, "kerja-sama")["versi"]
    r = kirim(ka, "kerja-sama", buka(ka, "kerja-sama"), "buang")
    cek(r.status_code == 302 and ih.draf(ih.baca(A, "kerja-sama")) is None and "Halaman ini kembali kosong" in
        ka.get(r.headers["Location"]).get_data(as_text=True), "buang draf")
    cek(any(x["aksi"] == "buang draf kerja-sama" for x in riwayat.daftar(1000)), "draf yang dibuang ada di riwayat")

    # a page with published content: the editor starts from it, the site keeps it until a draft is published
    ih.buang_draf(A, "perpustakaan", "penguji")
    ih.terbitkan(A, "perpustakaan", {"uraian": "Perpustakaan fakultas.", "tautan": [{"label": "Repositori",
                                                                                   "alamat": "https://repo.unsrat.ac.id/"}]}, "penguji")
    html = buka(ka, "perpustakaan")
    cek("Perpustakaan fakultas." in html and "Terbit" in html, "penyunting memuat isi terbit")
    kirim(ka, "perpustakaan", html, ubah={"uraian": "Perpustakaan fakultas dan universitas."})
    cek(ih.terbit(A, "perpustakaan")["uraian"] == "Perpustakaan fakultas." and
        ih.draf(ih.baca(A, "perpustakaan"))["isi"]["uraian"] == "Perpustakaan fakultas dan universitas.", "draf di samping isi terbit")
    b = bangun.Pembangun(produksi=False)
    b.bangun(A)
    with io.open(os.path.join(lokasi.publik(), "s1informatika", "fasilitas", "perpustakaan", "index.html"), encoding="utf-8") as f:
        situs = f.read()
    with io.open(os.path.join(lokasi.publik(), "s1informatika", "profil", "sejarah", "index.html"), encoding="utf-8") as f:
        situs_sejarah = f.read()
    cek("Perpustakaan fakultas." in situs and "dan universitas" not in situs and MENYUSUL in situs_sejarah,
        "situs hanya menampilkan isi terbit, bukan draf")
    for _i in range(10):
        kirim(ka, "perpustakaan", buka(ka, "perpustakaan"), "tambah:tautan")
    teks = ka.get(URL + "perpustakaan").get_data(as_text=True)
    cek(len(ih.draf(ih.baca(A, "perpustakaan"))["isi"]["tautan"]) == 10 and "jumlah paling banyak" in teks
        and 'value="tambah:tautan"' not in teks, "daftar penuh: tombol tambah hilang")
    r = kirim(ka, "perpustakaan", buka(ka, "perpustakaan"), "tambah:tautan")
    cek(r.status_code == 302 and "jumlah paling banyak" in ka.get(r.headers["Location"]).get_data(as_text=True)
        and len(ih.draf(ih.baca(A, "perpustakaan"))["isi"]["tautan"]) == 10, "tambah ke daftar penuh ditolak dengan pesan")

    # the list, other programmes, the audit log
    teks = ka.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek("1 dari 22" in teks and '<span class="status status--draf">Draf</span>' in teks and
        re.search(r'status--terbit">Terbit</span>[^<]*<br><span class="status status--draf">Draf</span>', teks),
        "daftar halaman: keadaan setiap halaman, juga halaman terbit yang punya draf")
    with klien["admb"].session_transaction() as s_:
        token_b = s_["csrf"]
    cek(klien["admb"].get(URL + "sejarah").status_code == 403 and
        kirim(klien["admb"], "sejarah", buka(ka, "sejarah"), ubah={"csrf": token_b}).status_code == 403,
        "admin prodi lain tidak bisa membuka atau menyimpan")
    log = audit.baca(prodi=A, batas=10000)
    for aksi in ("isi-draf-disimpan", "isi-berkas-diunggah", "isi-draf-dibuang"):
        cek(any(x["aksi"] == aksi and x.get("halaman") for x in log), "log audit mencatat %s" % aksi)
    print("uji_penyunting: %d templat, %d isian formulir kerja sama" % (len(ih.TEMPLAT), py.bagian_form(ih.TEMPLAT["kerja-sama"])))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_penyunting: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
