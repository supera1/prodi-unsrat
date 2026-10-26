# -*- coding: utf-8 -*-
"""Step 5b of phase 1: a programme's own changes to its official data (platform/data_prodi.py, the data page in
platform/admin/prodi_admin.py, and their use by the builder and the pull from www).

Checks the override rules (a value equal to www's is no override; every field validated; the whole record must stay
valid), the effective data the sites are built with, the conflicts when www changes an overridden field (the local
value stays; "pakai data www" and "tetap" resolve it), overrides dropped once www has the same value, the data form
(CPL rows added, changed, removed), and the published pages. Who may open the data page is tested in uji_admin.py.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import copy
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
    import jinja2  # noqa: F401
except ImportError:
    print("uji_data_prodi: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-dataprodi-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
for nama in ("PRODI_MODE", "PRODI_PENYIMPANAN"):
    os.environ.pop(nama, None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import data_prodi as dp  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B = "55201", "20201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def harus_gagal(fungsi, pesan, *args):
    try:
        fungsi(*args)
    except dp.GagalData as e:
        return e
    gagal.append(pesan)


def prodi(kode, nama, **lain):
    p = {"kode_pddikti": kode, "nama": nama, "nama_en": "Informatics", "jenjang": "S1", "gelar": "S.Kom.", "sks": 144,
         "unit_kode": "ft", "unit": "Fakultas Teknik", "website": "", "surel": "ti@unsrat.ac.id", "bidang_kerja": "Pengembang.",
         "bidang_kerja_en": "", "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Infokom", "berlaku_hingga": "2030-08-15",
         "internasional": "", "slug": "x", "slug_en": "",
         "cpl": [{"kode": "CPL 1", "isi": "Capaian satu.", "isi_en": "", "kurikulum": "2025/2026"},
                 {"kode": "CPL 2", "isi": "Capaian dua.", "isi_en": "", "kurikulum": "2025/2026"}]}
    p.update(lain)
    return p


WWW = {"prodi": {"tampilkan_berlaku_hingga": True, "program": [prodi(A, "Teknik Informatika"),
                                                               prodi(B, "Teknik Elektro", gelar="S.T.", akreditasi="Baik")]},
       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "jenis": "fakultas",
                          "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}},
                         {"kode": "fmipa", "nama": "Fakultas MIPA", "jenis": "fakultas",
                          "bendera": {"dasar": "#FFFFFF", "tulisan": "#3500FF"}},
                         {"kode": "upa-tik", "nama": "UPA TIK", "jenis": "upa"}]},
       "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}


def tulis_www(isi):
    os.makedirs(os.environ["WWW_DATA"], exist_ok=True)
    for nama, data in isi.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f)


def baca(rel):
    with io.open(os.path.join(lokasi.publik(), rel), encoding="utf-8") as f:
        return f.read()


try:
    tulis_www(WWW)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)

    # --- the override rules
    cek(dp.simpan(A, {"akreditasi": "Unggul"}, "penguji") == [], "nilai sama dengan www bukan perubahan")
    cek(not dp.baca(A)["timpaan"], "tanpa timpaan")
    cek(dp.simpan(A, {"akreditasi": "Baik Sekali", "gelar": "S.Kom"}, "penguji") == ["akreditasi", "gelar"], "dua kolom diubah")
    d = dp.baca(A)
    cek(d["timpaan"] == {"akreditasi": "Baik Sekali", "gelar": "S.Kom"} and d["dasar"]["akreditasi"] == "Unggul",
        "timpaan menyimpan nilai www sebelumnya: %r" % d)
    cek(dp.efektif(A)["akreditasi"] == "Baik Sekali" and dp.semua_efektif()[B]["akreditasi"] == "Baik", "data efektif")
    cek([x for x in lokasi.baca("warisan/prodi")["program"] if x["kode_pddikti"] == A][0]["akreditasi"] == "Unggul",
        "salinan www tidak pernah diubah")
    dp.simpan(A, {"gelar": "S.Kom."}, "penguji")
    cek("gelar" not in dp.baca(A)["timpaan"], "kembali ke nilai www menghapus timpaan")
    unit = dp.unit_per_kode()
    for f, v, label in (("nama", " ", "nama kosong"), ("bidang_kerja", "Kerja <script>x</script>", "HTML"),
                        ("nama_en", "slot gacor", "judi"), ("jenjang", "D3", "jenjang"), ("sks", 0, "SKS 0"),
                        ("sks", 500, "SKS 500"), ("sks", "tidak sah", "SKS bukan angka"), ("unit_kode", "fx", "unit"),
                        ("unit_kode", "upa-tik", "unit yang bukan fakultas"),
                        ("surel", "bukan-surel", "surel"), ("berlaku_hingga", "2026-02-30", "tanggal"),
                        ("cpl", [{"kode": "C", "isi": ""}], "CPL tanpa isi"), ("cpl", [{"isi": "x"}] * 41, "CPL terlalu banyak"),
                        ("cpl", [{"isi": "x", "bobot": 1}], "kolom CPL asing"), ("cpl", [{"isi": "Capaian judi togel online"}], "CPL judi"),
                        ("kode_pddikti", "99999", "kode tidak bisa diubah"), ("slug", "lain", "slug www tidak bisa diubah")):
        harus_gagal(dp.simpan, "%s harus ditolak" % label, A, {f: v}, "penguji")
    cek(dp.baca(A)["timpaan"] == {"akreditasi": "Baik Sekali"}, "penolakan tidak mengubah apa pun")
    dp.simpan(A, {"unit_kode": "fmipa", "sks": 146}, "penguji")
    cek(dp.efektif(A)["unit"] == "Fakultas MIPA" and dp.efektif(A)["sks"] == 146, "pindah fakultas memperbarui nama fakultas")
    dp.simpan(A, {"unit_kode": "ft", "sks": 144}, "penguji")

    # --- the admin: accounts, the data form
    super_id, s0 = akun.buat(None, "superuji", "Super Uji", "super")
    akun.ganti_sandi(super_id, s0, "Biru laut 7 menara pagi")
    adm_id, s1 = akun.buat(akun.ambil(super_id), "adma", "Admin A", "admin", [A])
    akun.ganti_sandi(adm_id, s1, "Kopi hangat 42 senja")
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    c = app.test_client()
    c.environ_base["REMOTE_ADDR"] = "103.84.116.10"
    c.get("/masuk")
    with c.session_transaction() as s:
        token = s["csrf"]
    cek(c.post("/masuk", data={"csrf": token, "pengguna": "adma", "sandi": "Kopi hangat 42 senja"}).status_code == 302, "admin masuk")

    def kirim(url, **data):
        with c.session_transaction() as s:
            data["csrf"] = s["csrf"]
        return c.post(url, data=data)

    def formulir(p, **ubah):
        """What the browser sends for the data page of p, with some fields changed."""
        f = {k: ("" if p.get(k) is None else str(p.get(k))) for k in dp.FIELD_UBAH if k != "cpl"}
        cpl = ubah.pop("cpl", p["cpl"])
        f.update(ubah)
        f["cpl_jumlah"] = str(len(cpl) + 3)
        for i, x in enumerate(cpl):
            for k in ("kode", "isi", "isi_en", "kurikulum"):
                f["cpl-%d-%s" % (i, k)] = x.get(k, "")
        return f

    teks = c.get("/prodi/%s/data" % A).get_data(as_text=True)
    cek("Baik Sekali" in teks and "diubah di sini" in teks and "Data www: Unggul" in teks, "halaman data menandai kolom yang diubah")
    app.antrean.minta(None, "penguji")
    cek("Baik Sekali" in baca("s1informatika/index.html") and "Baik Sekali" in baca("s1informatika/profil/akreditasi/index.html"),
        "situs memakai akreditasi yang diubah")
    cek("Baik Sekali" not in baca("s1elektro/index.html"), "prodi lain tidak terpengaruh")

    # CPL: change the first, remove the second, add a new one; SKS from the number field
    p = dp.efektif(A)
    cpl = [dict(p["cpl"][0], isi="Capaian satu, diperbarui."), dict(p["cpl"][1], isi=""),
           {"kode": "CPL 3", "isi": "Capaian baru.", "isi_en": "New outcome.", "kurikulum": "2025/2026"}]
    r = kirim("/prodi/%s/data" % A, **formulir(p, cpl=cpl, sks="146"))
    cek(r.status_code == 302, "simpan formulir data: %s" % r.status_code)
    p = dp.efektif(A)
    cek([x["kode"] for x in p["cpl"]] == ["CPL 1", "CPL 3"] and p["cpl"][0]["isi"] == "Capaian satu, diperbarui.",
        "CPL diubah, dihapus, dan ditambah: %r" % p["cpl"])
    cek(p["sks"] == 146 and isinstance(p["sks"], int), "SKS dari formulir menjadi angka")
    halaman = baca("s1informatika/akademik/profil-lulusan/index.html")
    cek("Capaian satu, diperbarui." in halaman and "Capaian baru." in halaman and "Capaian dua." not in halaman,
        "halaman CPL dibangun ulang dengan CPL baru")
    cek("146 SKS" in baca("s1informatika/index.html"), "kartu SKS di beranda memakai data prodi")
    cek("2 butir (2 berbeda dari www)" in c.get("/prodi/%s/data" % A).get_data(as_text=True), "ringkasan CPL menyebut butir yang berbeda")
    cek(kirim("/prodi/%s/data" % A, **formulir(p, sks="banyak")).status_code == 400 and dp.efektif(A)["sks"] == 146,
        "SKS tidak sah ditolak lewat formulir")
    cek(kirim("/prodi/%s/data" % A, **formulir(p, bidang_kerja="<b>x</b>")).status_code == 400, "HTML ditolak lewat formulir")
    cek(kirim("/prodi/%s/data" % A, **formulir(p)).status_code == 302, "simpan tanpa perubahan")
    cek(any(x["aksi"] == "data-prodi-diubah" and "cpl" in x.get("kolom", "") for x in audit.baca(prodi=A)), "perubahan tercatat")

    # --- www changes: conflicts on overridden fields, other fields follow www
    baru = copy.deepcopy(WWW)
    baru["prodi"]["program"][0].update(akreditasi="Baik", nama_en="Informatics Engineering")
    tulis_www(baru)
    lap = tarik_www.pratinjau()["laporan"]
    cek(lap["bentrok"] == {A: ["akreditasi"]}, "pratinjau menunjukkan bentrok: %r" % lap.get("bentrok"))
    lap = tarik_www.terapkan("penguji")
    p = dp.efektif(A)
    cek(p["akreditasi"] == "Baik Sekali", "data prodi tetap dipakai saat bentrok")
    cek(p["nama_en"] == "Informatics Engineering", "kolom yang tidak diubah prodi mengikuti www")
    cek([b[0] for b in dp.bentrok(A)] == ["akreditasi"], "bentrok tercatat")
    teks = c.get("/prodi/%s/data" % A).get_data(as_text=True)
    cek("bentrok dengan www" in teks and "Tetap data prodi" in teks, "halaman data menunjukkan bentrok")
    cek(kirim("/prodi/%s/data/akreditasi/tetap" % A).status_code == 302 and not dp.bentrok(A)
        and dp.efektif(A)["akreditasi"] == "Baik Sekali", "tetap: bentrok selesai, data prodi tetap")
    cek(kirim("/prodi/%s/data/akreditasi/www" % A).status_code == 302 and dp.efektif(A)["akreditasi"] == "Baik"
        and "akreditasi" not in dp.baca(A)["timpaan"], "pakai data www: timpaan dihapus")
    cek("Baik Sekali" not in baca("s1informatika/index.html"), "situs dibangun ulang dengan data www")
    cek(c.post("/prodi/%s/data/bukan_kolom/www" % A, data={"csrf": "x"}).status_code in (400, 404), "kolom tak dikenal ditolak")
    with c.session_transaction() as s:
        token = s["csrf"]
    cek(c.post("/prodi/%s/data/../www" % A, data={"csrf": token}).status_code == 404, "jalur kolom aneh ditolak")

    # www catches up with the programme's CPL: the override is dropped after the pull
    sama = copy.deepcopy(baru)
    sama["prodi"]["program"][0]["cpl"] = dp.efektif(A)["cpl"]
    tulis_www(sama)
    lap = tarik_www.terapkan("penguji")
    cek(lap.get("dirapikan") == {A: ["cpl"]} and "cpl" not in dp.baca(A)["timpaan"], "timpaan yang sudah sama dengan www dihapus")
    cek(dp.efektif(A)["cpl"] == sama["prodi"]["program"][0]["cpl"], "CPL tetap sama setelah dirapikan")

    # --- names in the admin follow the programme's data; the superadmin dashboard counts changes and conflicts
    dp.simpan(A, {"nama": "Informatika"}, "penguji")
    cek("S1 Informatika" in c.get("/prodi/%s/" % A).get_data(as_text=True), "nama baru dipakai di admin")
    dp.simpan(A, {"lembaga_akreditasi": "LAM-INFOKOM"}, "penguji")
    beda = copy.deepcopy(sama)
    beda["prodi"]["program"][0]["lembaga_akreditasi"] = "LAMINFOKOM"
    tulis_www(beda)
    tarik_www.terapkan("penguji")
    s = app.test_client()
    s.environ_base["REMOTE_ADDR"] = "103.84.116.11"
    s.get("/masuk")
    with s.session_transaction() as x:
        token = x["csrf"]
    s.post("/masuk", data={"csrf": token, "pengguna": "superuji", "sandi": "Biru laut 7 menara pagi"})
    teks = s.get("/").get_data(as_text=True)
    cek("<strong>1</strong> prodi dengan data yang bentrok dengan www" in teks
        and "<strong>1</strong> prodi mengubah data resminya sendiri" in teks, "dasbor superadmin: timpaan dan bentrok")
    cek("lembaga_akreditasi" in s.get("/super/prodi/%s" % A).get_data(as_text=True), "halaman prodi superadmin menyebut kolomnya")

    app.antrean.minta(None, "penguji")
    jumlah, temuan = periksa_situs(lokasi.publik(), "data-prodi")
    gagal.extend(temuan)
    print("data prodi: %d halaman diperiksa" % jumlah)
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_data_prodi: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
