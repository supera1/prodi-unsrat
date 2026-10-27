# -*- coding: utf-8 -*-
"""Fase 2 langkah 5: the guide for programme admins (docs/panduan-admin-prodi.md, shown in the admin) and the feedback
of the pilot (platform/admin/masukan_admin.py).

- the guide's renderer: headings with ids and a table of contents, lists with sub-items, tables, code, bold, links to
  anchors and https:// only; everything escaped (scripts, markup in a table, javascript: links stay text);
- the guide says what the admin does: every button and menu it names exists in the admin, its limits are the code's
  (PDF, photo, upload, password, session, 22 required pages), the messages it explains are the code's, the editor's
  link into it lands on a heading;
- /panduan for every role; the header links to it and to the feedback page;
- feedback: sent from a page (its address kept, another site's never), checked (required, length, control characters,
  gambling text, kind), each sender sees only its own, the superadmin's list with filters, answers read by the sender,
  the dashboard's count, the CSV (formulas neutralised), the cap on stored items, saves from many threads at once,
  the audit log.
Who may open each route at all is tested in uji_admin.py.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import csv
import glob
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
except ImportError:
    print("uji_pilot: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-pilot-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import isi_admin  # noqa: E402
import isi_halaman as ih  # noqa: E402
import masukan_admin as mk  # noqa: E402
import media  # noqa: E402
import panduan  # noqa: E402
import penyunting as py  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import prodi  # noqa: E402

A, B = "55201", "20201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def teks_kode():
    """The admin's own texts: its templates and the modules that write its messages."""
    isi = []
    for pola in ("platform/admin/templates/*.html", "platform/admin/*.py", "platform/*.py"):
        for path in glob.glob(os.path.join(AKAR, *pola.split("/"))):
            with io.open(path, encoding="utf-8") as f:
                isi.append(f.read())
    return "\n".join(isi)


try:
    # ============================================================== the renderer
    html, daftar_isi, judul = panduan.render(
        "# Judul\n\nParagraf satu\nbaris dua.\n\n## Bagian A\n\n- butir `**bukan tebal**` dan **tebal**\n  lanjutan butir\n"
        "  - sub butir\n- butir dua\n\n1. langkah satu\n   lanjutan\n2. langkah dua\n\n### Sub A\n\n"
        "| Kolom | <b>x</b> |\n|---|---|\n| [a](https://www.unsrat.ac.id/) | [b](javascript:alert(1)) |\n\n"
        "> kutipan\n\n```\n<script>alert(1)</script>\n```\n\n## Bagian A\n\n<script>alert(2)</script> [c](#bagian-a) "
        "[d](//evil.example) [e](http://contoh.id)\n")
    cek(judul == "Judul" and daftar_isi == [("bagian-a", "Bagian A"), ("bagian-a-2", "Bagian A")], "judul dan daftar isi: %r" % daftar_isi)
    for harus in ("<p>Paragraf satu baris dua.</p>", '<h2 id="bagian-a">Bagian A</h2>', '<h3 id="sub-a">Sub A</h3>',
                  "<code>**bukan tebal**</code>", "<strong>tebal</strong>", "<li>butir <code>**bukan tebal**</code> dan "
                  "<strong>tebal</strong> lanjutan butir<ul><li>sub butir</li></ul></li>", "<ol><li>langkah satu lanjutan</li>",
                  '<th scope="col">&lt;b&gt;x&lt;/b&gt;</th>', '<a href="https://www.unsrat.ac.id/">a</a>',
                  "[b](javascript:alert(1))", "<blockquote><p>kutipan</p></blockquote>",
                  "<pre><code>&lt;script&gt;alert(1)&lt;/script&gt;</code></pre>", "&lt;script&gt;alert(2)&lt;/script&gt;",
                  '<a href="#bagian-a">c</a>', "[d](//evil.example)", "[e](http://contoh.id)", 'id="bagian-a-2"'):
        cek(harus in html, "pengurai panduan menghasilkan %r" % harus)
    cek("<script" not in html and "javascript:" not in html.replace("[b](javascript:alert(1))", ""), "pengurai tidak meloloskan skrip")

    # ============================================================== the guide says what the admin does
    teks = panduan.baca()
    html, daftar_isi, judul = panduan.render(teks)
    polos = re.sub(r"<code>.*?</code>", "", html)
    cek(judul and len(daftar_isi) >= 8 and "**" not in polos and "](" not in polos, "panduan terurai tanpa sisa markah")
    cek('id="mengisi-halaman"' in html, "tautan penyunting ke panduan#mengisi-halaman punya tujuan")
    kode = teks_kode()
    for pesan in ("Formulir kedaluwarsa", "Sesi berakhir. Silakan masuk lagi.", "halaman ini baru saja diubah",
                  "Berkas atau formulir terlalu besar", "Teks alternatif foto wajib diisi",
                  "PDF berisi skrip, formulir aktif, atau berkas sisipan", "isian perlu diperbaiki",
                  "Draf yang menunggu persetujuan tidak dapat dibuang", "Tidak ada perubahan untuk disimpan"):
        cek(pesan in teks and pesan in kode, "pesan %r di panduan sama dengan di admin" % pesan)
    app_uji = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    for angka, nilai in (("paling besar 20 MB", media.MAKS_PDF), ("paling besar 10 MB", media.MAKS_FOTO),
                         ("paling banyak 40 MB", app_uji.config["MAX_CONTENT_LENGTH"])):
        cek(angka in teks and nilai == int(re.search(r"(\d+) MB", angka).group(1)) * 1024 * 1024,
            "panduan %r sama dengan batas di kode (%d)" % (angka, nilai))
    cek("lebar minimal %d piksel" % media.LEBAR_MIN in teks, "lebar minimal foto di panduan")
    cek("paling sedikit %d karakter" % akun.SANDI_MIN["admin"] in teks and akun.SANDI_MIN["admin"] == akun.SANDI_MIN["operator"],
        "panjang kata sandi di panduan")
    cek("setelah %d jam tidak dipakai" % (app_mod.SESI_MENIT // 60) in teks, "lama sesi di panduan")
    cek("22 halaman wajib" in teks and len(isi_admin.halaman_wajib()) == 22, "jumlah halaman wajib di panduan")

    # ============================================================== the admin: the guide and the feedback
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
    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("opa", "operator", [A]), ("opb", "operator", [B])):
        akun_baru(nama, peran, p, super_)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    klien = {}
    for i, nama in enumerate(("superuji", "adma", "opa", "opb")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (90 + i)
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ks, ka, ko, kb = klien["superuji"], klien["adma"], klien["opa"], klien["opb"]

    def kirim(c, url, **data):
        with c.session_transaction() as s:
            token = s["csrf"]
        return c.post(url, data=dict(data, csrf=token))

    # every button and menu the guide names, on the page and in the state where the admin shows it
    URL = "/prodi/%s/halaman/" % A

    def halaman(c, url):
        return c.get(url).get_data(as_text=True)
    ih.simpan_draf(A, "kerja-sama", {"daftar": [{"mitra": "Mitra"}]}, "opa")
    tampak = {"operator, draf": halaman(ko, URL + "kerja-sama")}
    ih.ajukan(A, "sejarah", {"uraian": "Sejarah singkat."}, "opa")
    tampak["operator, menunggu"] = halaman(ko, URL + "sejarah")
    tampak["admin, menunggu"] = halaman(ka, URL + "sejarah")
    ih.terbitkan(A, "sejarah", {"uraian": "Sejarah singkat."}, "adma", dari_draf=True)
    tampak["admin, terbit"] = halaman(ka, URL + "sejarah")
    tampak["riwayat halaman"] = halaman(ka, URL + "sejarah/riwayat")
    tampak["dasbor admin"] = halaman(ka, "/prodi/%s/" % A)
    tampak["daftar, tabel, berkas"] = py.formulir(ih.TEMPLAT["kerja-sama"], {"daftar": [{"mitra": "Mitra", "bukti": {
        "jenis": "pdf", "jalur": "%s/202610-0123456789ab.pdf" % A, "judul": "Bukti", "halaman": 1, "ukuran": 1000}},
        {"mitra": "Mitra kedua"}]}, py.Tampil(dihapus={"jalur": "daftar", "indeks": 1, "nilai": {"mitra": "Lain"}}))
    for di, labels in (("operator, draf", ("Simpan draf", "Simpan dan pratinjau", "Ajukan untuk diterbitkan", "Buang draf",
                                           "Riwayat halaman ini", "(wajib)")),
                       ("operator, menunggu", ("Batalkan pengajuan",)),
                       ("admin, menunggu", ("Terbitkan", "Kembalikan dengan catatan", "Catatan untuk penulis")),
                       ("admin, terbit", ("Terbitkan perubahan", "Tarik dari situs")),
                       ("riwayat halaman", ("Jadikan draf",)),
                       ("daftar, tabel, berkas", ("Tambah baris", "Naik", "Turun", "Hapus", "Kembalikan baris itu", "Lepas berkas ini")),
                       ("dasbor admin", ("Isi halaman", "Ringkasan", "Kesiapan situs", "Panduan", "Masukan", "Data prodi",
                                         "Identitas", "Bagian depan beranda", "Menu", "Akun", "Log audit", "Riwayat",
                                         "Pengumuman", "Keluar"))):
        for label in labels:
            cek(label in teks, "panduan menyebut %r" % label)
            cek(label in tampak[di], "%r yang disebut panduan tampil di admin (%s)" % (label, di))

    for nama, c in klien.items():
        r = c.get("/panduan")
        t = r.get_data(as_text=True)
        cek(r.status_code == 200 and "<h1>Panduan admin prodi dan operator</h1>" in t and 'href="#mengisi-halaman"' in t
            and "<script" not in t and " style=" not in t, "panduan terbuka untuk %s" % nama)
    t = ko.get("/prodi/%s/halaman/sejarah" % A).get_data(as_text=True)
    cek('href="/panduan"' in t and 'href="/masukan?dari=/prodi/%s/halaman/sejarah"' % A in t and
        'href="/panduan#mengisi-halaman"' in t, "kepala admin menautkan panduan dan masukan dari halaman ini")

    # feedback: sent, checked, seen only by its sender
    t = ko.get("/masukan?dari=/prodi/%s/halaman/kurikulum" % A).get_data(as_text=True)
    cek('name="dari" value="/prodi/%s/halaman/kurikulum"' % A in t and "Belum ada masukan dari Anda" in t, "formulir masukan")
    r = kirim(ko, "/masukan", jenis="kendala", isi="Tabel mata kuliah terlalu panjang untuk diisi satu per satu.",
              dari="/prodi/%s/halaman/kurikulum?buka=x" % A)
    data = mk.baca()["masukan"]
    cek(r.status_code == 302 and len(data) == 1 and data[0]["oleh"] == "opa" and data[0]["peran"] == "operator"
        and data[0]["prodi"] == [A] and data[0]["halaman"] == "/prodi/%s/halaman/kurikulum" % A and data[0]["status"] == "baru",
        "masukan tersimpan dengan pengirim, prodi, dan halamannya: %r" % data[:1])
    cek("Terima kasih" in ko.get(r.headers["Location"]).get_data(as_text=True), "pesan terima kasih")
    for isian, potongan in (({"jenis": "kendala", "isi": ""}, "wajib diisi"), ({"jenis": "kendala", "isi": "x" * 2001}, "paling banyak 2000"),
                            ({"jenis": "kendala", "isi": "Ada\x07"}, "karakter yang tidak boleh"),
                            ({"jenis": "kendala", "isi": "Daftar slot gacor"}, "teks judi"), ({"jenis": "pujian", "isi": "Bagus"}, "pilih jenis")):
        r = kirim(ko, "/masukan", **isian)
        cek(r.status_code == 400 and potongan in r.get_data(as_text=True) and len(mk.baca()["masukan"]) == 1,
            "masukan %r ditolak" % potongan)
    for dari, harap in (("//evil.example/x", ""), ("https://evil.example/", ""), ("/prodi/%s/<script>" % A, ""), ("", "")):
        kirim(ko, "/masukan", jenis="pertanyaan", isi="Pertanyaan dari %r" % dari, dari=dari)
        cek(mk.baca()["masukan"][-1]["halaman"] == harap, "halaman asal %r tidak disimpan" % dari)
    kirim(ko, "/masukan", jenis="usulan", isi="=HYPERLINK(\"https://evil.example\")")
    kirim(kb, "/masukan", jenis="pertanyaan", isi="Masukan prodi lain.")
    t = ko.get("/masukan").get_data(as_text=True)
    cek("Tabel mata kuliah terlalu panjang" in t and "Masukan prodi lain." not in t, "pengirim hanya melihat masukannya sendiri")
    cek("Tabel mata kuliah" not in ka.get("/masukan").get_data(as_text=True), "admin prodi tidak melihat masukan operatornya")

    # the superadmin: count, list, answer, CSV
    cek("<strong>7</strong> masukan baru" in ks.get("/").get_data(as_text=True), "dasbor superadmin: jumlah masukan baru")
    t = ks.get("/super/masukan").get_data(as_text=True)
    cek("Baru (7)" in t and "Kendala dari opa" in t and "S1 Teknik Informatika" in t and
        'href="/prodi/%s/halaman/kurikulum"' % A in t, "daftar masukan untuk superadmin")
    id_ = mk.baca()["masukan"][0]["id"]
    r = kirim(ks, "/super/masukan/%s" % id_, status="ditindaklanjuti", tanggapan="Impor Excel untuk tabel besar sedang dipertimbangkan.")
    b = mk.baca()["masukan"][0]
    cek(r.status_code == 302 and b["status"] == "ditindaklanjuti" and b["tanggapan"]["oleh"] == "superuji", "masukan ditanggapi")
    t = ko.get("/masukan").get_data(as_text=True)
    cek("Tanggapan superuji" in t and "Impor Excel untuk tabel besar sedang dipertimbangkan." in t and "Ditindaklanjuti" in t,
        "pengirim membaca tanggapannya")
    r = kirim(ks, "/super/masukan/%s" % id_, status="dibuang", tanggapan="")
    cek(r.status_code == 302 and mk.baca()["masukan"][0]["status"] == "ditindaklanjuti", "status yang tidak dikenal ditolak")
    kirim(ks, "/super/masukan/%s" % id_, status="ditunda", tanggapan="Ditunda: slot gacor")
    cek(mk.baca()["masukan"][0]["status"] == "ditindaklanjuti", "tanggapan berteks judi ditolak")
    kirim(ks, "/super/masukan/%s" % id_, status="ditunda", tanggapan="")
    b = mk.baca()["masukan"][0]
    cek(b["status"] == "ditunda" and b["tanggapan"]["isi"].startswith("Impor Excel"), "ganti status tanpa tanggapan baru: tanggapan lama tetap")
    cek(kirim(ks, "/super/masukan/20000101-000000-abcdef", status="ditunda").status_code == 404 and
        kirim(ks, "/super/masukan/bukan-id", status="ditunda").status_code == 404, "masukan yang tidak ada")
    t = ks.get("/super/masukan?status=ditunda").get_data(as_text=True)
    cek("Ditunda (1)" in t and t.count('class="kartu masukan-butir"') == 1, "saringan status")
    cek(ks.get("/super/masukan?status=aneh").status_code == 404, "saringan yang tidak dikenal")
    r = ks.get("/super/masukan.csv")
    baris = list(csv.reader(io.StringIO(r.get_data(as_text=True).lstrip("﻿"))))
    cek(r.mimetype == "text/csv" and baris[0][:3] == ["id", "waktu", "oleh"] and len(baris) == 1 + len(mk.baca()["masukan"]),
        "CSV masukan")
    cek(any(b_[7].startswith("'=HYPERLINK") for b_ in baris[1:]), "rumus di CSV masukan dinetralkan")

    # the cap, many threads at once, the audit log
    asli = mk.MAKS_SEMUA
    mk.MAKS_SEMUA = 12
    utas = [threading.Thread(target=mk.tambah, args=(super_, "usulan", "Usulan utas %d" % i)) for i in range(10)]
    for x in utas:
        x.start()
    for x in utas:
        x.join()
    data = mk.baca()["masukan"]
    cek(len(data) == 12 and sum(1 for b_ in data if b_["isi"].startswith("Usulan utas")) == 10,
        "simpanan bersamaan tidak hilang, yang tertua dilepas di atas batas: %d" % len(data))
    mk.MAKS_SEMUA = asli
    log = audit.baca(batas=10000)
    cek(any(x["aksi"] == "masukan-dikirim" and x.get("prodi") for x in log) and any(x["aksi"] == "masukan-ditanggapi" for x in log),
        "log audit mencatat masukan dan tanggapannya")
    print("uji_pilot: panduan %d bagian, %d masukan uji" % (len(daftar_isi), len(mk.baca()["masukan"])))
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_pilot: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
