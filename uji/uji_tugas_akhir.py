# -*- coding: utf-8 -*-
"""The final projects page (K-P35 nomor 4-5): a table kept in a spreadsheet, a search box on the site, no NIM.

- the menu: "Tugas Akhir" is optional and shown only once filled ("bila_terisi", only for optional pages);
- the import: a file as programmes keep it (No, NIM, Judul Skripsi, Dosen Pembimbing 1 and 2) maps by the columns'
  other names, NIM and No are left out; up to 5,000 rows, not one more;
- the editor: the table is not a form of thousands of fields but its first rows and the way to the import; saving the
  rest of the page keeps every row;
- the site: the page only once published; columns empty in every row left out; a table of 30 rows or more marked for
  the search box and the site's own deferred script loaded, shorter tables without; the script itself small, adding
  only text (no HTML from the page's data), nothing from other hosts; no NIM anywhere; the shared page checks.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import gzip
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
    from openpyxl import Workbook
except ImportError:
    print("uji_tugas_akhir: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-tugas-akhir-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bangun  # noqa: E402
import impor_tabel as it  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import prodi  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B = "55201", "20201"
SLUG = {A: "s1informatika", B: "s1elektro"}
N = 1600
gagal, dicek = [], [0]


def cek(kondisi, pesan):
    dicek[0] += 1
    if not kondisi:
        gagal.append(pesan)


def halaman_situs(kode, alamat):
    path = os.path.join(lokasi.publik(), SLUG[kode], *alamat.split("/"), "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def xlsx(baris):
    buku = Workbook()
    ws = buku.active
    for b in baris:
        ws.append(b)
    keluar = io.BytesIO()
    buku.save(keluar)
    return keluar.getvalue()


try:
    # ============================================================== the menu
    templat = menu_mod.baca_templat()
    butir = menu_mod.semua_butir(templat)["tugas-akhir"]
    cek(butir["jenis"] == "opsional" and butir.get("bila_terisi") and butir["alamat"] == "akademik/tugas-akhir",
        "Tugas Akhir: opsional, tampil bila terisi, di Akademik")
    salah = json.loads(json.dumps(templat))
    salah[1]["anak"][1]["bila_terisi"] = True                     # Kurikulum is required
    path = os.path.join(KERJA, "menu-salah.json")
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump({"menu": salah}, f)
    try:
        menu_mod.baca_templat(path)
        cek(False, "bila_terisi pada halaman wajib harus ditolak")
    except menu_mod.GagalMenu as e:
        cek("hanya halaman opsional yang tampil bila terisi" in str(e), "pesan bila_terisi: %s" % e)

    # ============================================================== the import
    node = dict(it.tabel_halaman("tugas-akhir"))["daftar"]
    cek(node["maks"] == 5000 and node.get("lewat_excel") and it.MAKS_BARIS >= node["maks"], "tabel tugas akhir 5.000 baris")
    cek("nim" not in {k for k, _n in node["isi"]["bidang"]}, "tanpa kolom NIM")
    kepala = ["No", "NIM", "Judul Skripsi", "Dosen Pembimbing 1", "Dosen Pembimbing 2"]
    isi = [kepala] + [[i, "1002160%02d%03d" % (i // 1000, i % 1000), "Rancang Bangun Sistem Nomor %d" % i,
                       "Dosen Satu, S.T., M.T.", "Dosen Dua, S.Kom., M.Kom." if i % 3 else None] for i in range(1, N + 1)]
    berkas_ta = xlsx(isi)
    hasil = it.rencana(node, it.baca_berkas("skripsi.xlsx", berkas_ta), A)
    cek(len(hasil["baris"]) == N and not hasil["galat"] and hasil["abaikan"] == ["No", "NIM"]
        and hasil["kolom"] == ["Judul", "Pembimbing 1", "Pembimbing 2"], "berkas gaya prodi: %r" % {k: hasil[k] for k in ("abaikan", "kolom", "galat")})
    cek(not any("100216" in json.dumps(r) for r in hasil["baris"]), "NIM tidak ikut")
    cek(hasil["baris"][2] == {"judul": "Rancang Bangun Sistem Nomor 3", "pembimbing_utama": "Dosen Satu, S.T., M.T."},
        "baris tanpa pembimbing 2: %r" % hasil["baris"][2])
    for jumlah, harus in ((5000, None), (5001, "paling banyak 5000 baris")):
        try:
            it.rencana(node, [(1, ["Judul"])] + [(i + 2, ["J%d" % i]) for i in range(jumlah)], A)
            pesan = None
        except ValueError as e:
            pesan = str(e)
        cek(pesan == harus or (harus and pesan and harus in pesan), "%d baris: %r" % (jumlah, pesan))

    # ============================================================== the platform
    os.makedirs(os.environ["WWW_DATA"])
    for nama, data in {"prodi": {"program": [prodi(A, "Teknik Informatika"), prodi(B, "Teknik Elektro")]},
                       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "jenis": "fakultas",
                                          "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                       "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)
    bangun.Pembangun(produksi=False).bangun()
    cek(halaman_situs(A, "akademik/tugas-akhir") is None and "Tugas Akhir" not in halaman_situs(A, "akademik"),
        "kosong: tidak ada di situs dan menu")

    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    akun_baru("adma", "admin", [A], super_)
    akun_baru("opa", "operator", [A], super_)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    klien = {}
    for i, nama in enumerate(("adma", "opa")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (50 + i)
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ka, ko = klien["adma"], klien["opa"]

    def kirim(c, url, **data):
        with c.session_transaction() as s:
            data["csrf"] = s["csrf"]
        return c.post(url, data=data)

    # the operator imports the file into the draft
    U = "/prodi/%s/halaman/tugas-akhir" % A
    r = kirim(ko, U + "/impor", tabel="daftar", berkas=(io.BytesIO(berkas_ta), "skripsi.xlsx"))
    teks = r.get_data(as_text=True)
    m = re.search(r'name="token" value="([A-Za-z0-9_-]+)"', teks)
    cek(r.status_code == 200 and "%d siap diimpor" % N in re.sub(r"<[^>]+>", "", teks) and "diabaikan: No, NIM" in teks,
        "pratinjau impor tugas akhir")
    r = kirim(ko, U + "/impor/terapkan", token=m.group(1) if m else "", mode="ganti")
    cek(r.status_code == 302 and len(ih.draf(ih.baca(A, "tugas-akhir"))["isi"]["daftar"]) == N, "impor ke draf")

    # the editor: the first rows, the way to the import, every row kept when the rest is saved
    teks = ko.get(U).get_data(as_text=True)
    cek("(%d baris)" % N in teks and "Ditampilkan 20 baris pertama dari %d" % N in teks
        and 'href="%s/impor">Impor dari Excel</a>' % U in teks and 'name="daftar.' not in teks
        and teks.count("<tr>") <= 25, "penyunting: ringkasan, bukan ribuan isian")
    cek(len(teks) < 200 * 1024, "penyunting tetap ringan: %d B" % len(teks))
    r = kirim(ko, U, versi=str(ih.baca(A, "tugas-akhir")["versi"]), aksi="ajukan", uraian="Daftar tugas akhir mahasiswa.")
    d = ih.draf(ih.baca(A, "tugas-akhir"))
    cek(r.status_code == 302 and d["status"] == "menunggu" and len(d["isi"]["daftar"]) == N
        and d["isi"]["uraian"] == "Daftar tugas akhir mahasiswa.", "simpan isian lain: semua baris tetap")

    # the admin publishes: the site
    r = kirim(ka, U, versi=str(ih.baca(A, "tugas-akhir")["versi"]), aksi="terbitkan", uraian="Daftar tugas akhir mahasiswa.")
    teks = halaman_situs(A, "akademik/tugas-akhir") or ""
    cek(r.status_code == 302 and teks.count("<tr>") == N + 1, "terbit: tabel %d baris di situs" % N)
    cek('data-cari>' in teks and re.search(r'<script src="(\.\./)+aset/js/cari-tabel\.js\?v=[0-9a-f]+" defer></script>', teks),
        "kotak cari: tabel bertanda, skrip situs sendiri ditunda")
    cek("<th scope=\"col\">Judul</th><th scope=\"col\">Pembimbing 1</th><th scope=\"col\">Pembimbing 2</th></tr>" in teks
        and "Tahun lulus" not in teks and "Mahasiswa</th>" not in teks, "kolom yang kosong di semua baris tidak tampil")
    cek("100216" not in teks, "tanpa NIM di situs")
    cek("Tugas Akhir" in halaman_situs(A, "akademik") and halaman_situs(B, "akademik/tugas-akhir") is None,
        "terisi: di menu prodi ini saja")
    cek(len(gzip.compress(teks.encode("utf-8"))) < 120 * 1024, "halaman %d baris tetap ringan (gzip)" % N)
    jumlah, temuan = periksa_situs(lokasi.publik(), "tugas-akhir")
    cek(not temuan, "pemeriksaan halaman bersama: %r" % temuan[:5])

    # a short table: no search box, no script
    ih.terbitkan(A, "jadwal", {"jadwal": [{"kegiatan": "UTS", "waktu": "Oktober"}, {"kegiatan": "UAS", "waktu": "Desember"}]},
                 "penguji")
    bangun.Pembangun(produksi=False).bangun()
    teks = halaman_situs(A, "akademik/jadwal") or ""
    cek("<tr>" in teks and "data-cari" not in teks and "cari-tabel.js" not in teks and "Tempat</th>" not in teks,
        "tabel pendek: tanpa kotak cari, kolom kosong tidak tampil")

    # the script
    path_js = os.path.join(lokasi.publik(), "aset", "js", "cari-tabel.js")
    with io.open(path_js, encoding="utf-8") as f:
        js = f.read()
    cek(len(gzip.compress(js.encode("utf-8"))) < 5 * 1024 and "innerHTML" not in js and "eval(" not in js
        and "http" not in js and "textContent" in js and "aria-live" in js, "skrip kotak cari kecil, hanya teks")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_tugas_akhir: %d pemeriksaan, %s" % (dicek[0], "LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
