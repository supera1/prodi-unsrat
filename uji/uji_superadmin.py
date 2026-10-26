# -*- coding: utf-8 -*-
"""Step 5 of phase 1: the superadmin pages (platform/admin/superadmin.py, pembangun.py, impor_dosen.py).

Runs the admin with Flask's test client on made-up www data in a temporary directory, with real rebuilds
(PRODI_BANGUN=sinkron), and checks what each page changes in the data AND in the published sites: slugs and their
redirects, switching sites off and on, lecturer links one by one and in bulk (CSV, semicolon CSV, Excel), pulling the
official data (preview, stale previews, a defaced source, many programmes disappearing), registering a programme new in
www, the version history (compare, restore, path tricks), accounts' roles and programmes, the audit filters, and the
rebuild queue. Who may open these pages at all is tested in uji_admin.py.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import datetime
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import flask  # noqa: F401
    import jinja2  # noqa: F401
    import openpyxl
except ImportError:
    print("uji_superadmin: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-super-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
for nama in ("PRODI_MODE", "PRODI_PENYIMPANAN"):
    os.environ.pop(nama, None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import impor_dosen  # noqa: E402
import lokasi  # noqa: E402
import pembangun  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

IP = "103.84.116.10"
A, B, C, D = "55201", "20201", "21201", "26201"
SANDI_SUPER, SANDI_ADMIN = "Biru laut 7 menara pagi", "Kopi hangat 42 senja"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def prodi(kode, nama, **lain):
    p = {"kode_pddikti": kode, "nama": nama, "nama_en": "", "jenjang": "S1", "gelar": "S.T.", "sks": 144, "unit_kode": "ft",
         "unit": "Fakultas Teknik", "website": "", "surel": "x@unsrat.ac.id", "bidang_kerja": "Bidang.", "bidang_kerja_en": "",
         "akreditasi": "Baik", "lembaga_akreditasi": "LAM-Teknik", "berlaku_hingga": "", "internasional": "", "slug": "x",
         "slug_en": "", "cpl": [{"kode": "CPL 1", "isi": "Capaian.", "isi_en": "", "kurikulum": "2025/2026"}]}
    p.update(lain)
    return p


WWW = {"prodi": {"tampilkan_berlaku_hingga": False, "program": [
           prodi(A, "Teknik Informatika", akreditasi="Unggul"), prodi(B, "Teknik Elektro"), prodi(C, "Teknik Mesin")]},
       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
       "kalender": {"semester": []},
       "situs": {"identitas": {"nama": {"id": "Universitas Sam Ratulangi"}}, "kontak": {}}}


def tulis_www(isi):
    os.makedirs(os.environ["WWW_DATA"], exist_ok=True)
    for nama, data in isi.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f)


def ada(rel):
    return os.path.isfile(os.path.join(lokasi.publik(), rel))


def baca(rel):
    with io.open(os.path.join(lokasi.publik(), rel), encoding="utf-8") as f:
        return f.read()


try:
    # --- data: three programmes in www, two of them registered, built once
    tulis_www(WWW)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)
    super_id, sementara = akun.buat(None, "superuji", "Super Uji", "super")
    akun.ganti_sandi(super_id, sementara, SANDI_SUPER)
    super_ = akun.ambil(super_id)
    adm_id, sementara = akun.buat(super_, "adma", "Admin A", "admin", [A])
    akun.ganti_sandi(adm_id, sementara, SANDI_ADMIN)

    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})

    def klien(ip=IP):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = ip
        return c

    def masuk(c, nama, sandi):
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        return c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": sandi})

    def kirim(c, url, berkas=None, **data):
        with c.session_transaction() as s:
            data["csrf"] = s.get("csrf", "")
        if berkas:
            data["berkas"] = berkas
            return c.post(url, data=data, content_type="multipart/form-data")
        return c.post(url, data=data)

    su = klien()
    cek(masuk(su, "superuji", SANDI_SUPER).status_code == 302, "superadmin masuk")
    ad = klien("103.84.116.11")
    cek(masuk(ad, "adma", SANDI_ADMIN).status_code == 302, "admin prodi masuk")
    cek(kirim(su, "/super/bangun/semua").status_code == 302 and app.antrean.status["ok"], "bangun awal: %s" % app.antrean.status)
    cek(ada("s1informatika/index.html") and ada("s1elektro/index.html"), "dua situs terbangun")

    # --- dashboard
    teks = su.get("/").get_data(as_text=True)
    cek("<strong>2</strong> situs aktif dari 2 prodi terdaftar" in teks, "dasbor: 2 situs aktif")
    cek("<strong>1</strong> prodi baru di www belum terdaftar" in teks, "dasbor: 1 belum terdaftar")
    cek("<strong>1</strong> situs aktif tanpa admin prodi" in teks and "S1 Teknik Elektro" in teks, "dasbor: elektro tanpa admin")
    cek("<strong>2</strong> situs aktif tanpa tautan dosen" in teks, "dasbor: tanpa tautan dosen")

    # --- slug: refused changes leave everything as it was
    for slug, label in (("S1 TI", "tidak sah"), ("admin", "alamat sistem"), ("s1elektro", "milik prodi lain"), ("s2ti", "jenjang salah")):
        r = kirim(su, "/super/prodi/%s/slug" % A, slug=slug)
        cek(r.status_code == 400 and registri.cari(registri.baca(), A)["slug"] == "s1informatika", "slug %s harus ditolak" % label)
    r = kirim(su, "/super/prodi/%s/slug" % A, slug="s1ti")
    cek(r.status_code == 302 and registri.cari(registri.baca(), A)["slug"] == "s1ti", "slug diubah")
    cek(ada("s1ti/index.html") and not ada("s1informatika/index.html"), "situs pindah ke slug baru, folder lama hilang")
    with io.open(os.path.join(lokasi.nginx_buatan(), "slug-lama.conf"), encoding="utf-8") as f:
        cek("rewrite ^/s1informatika(/.*)?$ /s1ti$1 permanent;" in f.read(), "alamat lama dialihkan")
    cek(kirim(su, "/super/prodi/%s/slug" % B, slug="s1informatika").status_code == 400, "slug lama prodi lain tidak bisa diambil")
    cek(any(x["aksi"] == "slug-diubah" and x.get("lama") == "s1informatika" for x in audit.baca()), "ganti slug tercatat")

    # --- switching a site off and on
    cek(kirim(su, "/super/prodi/%s/aktif" % B, aktif="0").status_code == 302, "nonaktifkan elektro")
    cek(not ada("s1elektro/index.html") and "s1elektro" not in baca("index.html"), "situs nonaktif hilang dari publik dan daftar")
    kirim(su, "/super/prodi/%s/aktif" % B, aktif="1")
    cek(ada("s1elektro/index.html"), "situs aktif lagi")
    r = kirim(su, "/super/prodi/%s/bangun" % B)
    cek(r.status_code == 302 and app.antrean.status["cakupan"] == B, "bangun ulang satu prodi: %s" % app.antrean.status["cakupan"])

    # --- one lecturer link
    r = kirim(su, "/super/prodi/%s/dosen" % A, dosen_url="https://jahat.com/dosen")
    cek(r.status_code == 400 and not registri.cari(registri.baca(), A)["dosen_url"], "tautan dosen dari situs lain ditolak")
    kirim(su, "/super/prodi/%s/dosen" % A, dosen_url="https://dosen.unsrat.ac.id/prodi/ti")
    cek('href="https://dosen.unsrat.ac.id/prodi/ti"' in baca("s1ti/dosen/dosen-tetap/index.html"), "tautan dosen tampil di situs")

    # --- lecturer links in bulk
    cek(impor_dosen._aman("=HYPERLINK(\"x\")").startswith("'") and impor_dosen._aman("biasa") == "biasa", "rumus di CSV dinetralkan")
    r = su.get("/super/dosen/templat.csv")
    templat = r.get_data(as_text=True)
    cek(r.headers["Content-Type"].startswith("text/csv") and "attachment" in r.headers["Content-Disposition"], "templat diunduh")
    cek(templat.startswith("\ufeffkode_pddikti,") and "s1ti" in templat and "https://dosen.unsrat.ac.id/prodi/ti" in templat,
        "templat memuat prodi dan tautannya")

    def unggah(isi, nama):
        return kirim(su, "/super/dosen/impor", berkas=(io.BytesIO(isi), nama))

    csv_isi = ("kode_pddikti,nama,dosen_url\n%s,Elektro,https://dosen.unsrat.ac.id/prodi/te\n%s,TI,https://jahat.com/x\n"
               "99999,Fiktif,https://dosen.unsrat.ac.id/x\n%s,TI,\n" % (B, A, A)).encode("utf-8")
    r = unggah(csv_isi, "tautan.csv")
    teks = r.get_data(as_text=True)
    cek(r.status_code == 200 and "<strong>1</strong> prodi berubah" in teks and "<strong>2</strong> baris bermasalah" in teks,
        "pratinjau impor CSV")
    cek(registri.cari(registri.baca(), B)["dosen_url"] == "", "pratinjau tidak mengubah apa pun")
    token = re.search(r'name="token" value="([^"]+)"', teks).group(1)
    cek(kirim(su, "/super/dosen/terapkan", token=token).status_code == 302, "impor diterapkan")
    cek(registri.cari(registri.baca(), B)["dosen_url"] == "https://dosen.unsrat.ac.id/prodi/te", "tautan elektro tersimpan")
    cek('href="https://dosen.unsrat.ac.id/prodi/te"' in baca("s1elektro/dosen/dosen-tetap/index.html"), "situs elektro dibangun ulang")
    kirim(su, "/super/prodi/%s/dosen" % B, dosen_url="")
    cek(kirim(su, "/super/dosen/terapkan", token=token).status_code == 302
        and registri.cari(registri.baca(), B)["dosen_url"] == "", "token impor hanya sekali pakai")
    cek(kirim(su, "/super/dosen/terapkan", token="../../rahasia/akun").status_code == 302, "token aneh ditolak")
    # semicolon CSV with a BOM and other column names; then an Excel file
    r = unggah(("\ufeffKode Prodi;Tautan\n%s;https://dosen.unsrat.ac.id/prodi/te2\n" % B).encode("utf-8"), "id.csv")
    cek("<strong>1</strong> prodi berubah" in r.get_data(as_text=True), "CSV titik koma dengan BOM")
    token = re.search(r'name="token" value="([^"]+)"', r.get_data(as_text=True)).group(1)
    path_token = os.path.join(lokasi.rahasia(), "sementara", token + ".json")
    os.utime(path_token, (time.time() - 3600, time.time() - 3600))
    with io.open(path_token, encoding="utf-8") as f:
        isi = json.load(f)
    isi["waktu"] = time.time() - 3600
    with io.open(path_token, "w", encoding="utf-8") as f:
        json.dump(isi, f)
    cek(kirim(su, "/super/dosen/terapkan", token=token).status_code == 302
        and registri.cari(registri.baca(), B)["dosen_url"] == "", "pratinjau kedaluwarsa tidak bisa diterapkan")
    buku = openpyxl.Workbook()
    lembar = buku.active
    lembar.append(["slug", "dosen_url"])
    lembar.append(["s1elektro", "https://dosen.unsrat.ac.id/prodi/te3"])
    buf = io.BytesIO()
    buku.save(buf)
    r = unggah(buf.getvalue(), "tautan.xlsx")
    cek("<strong>1</strong> prodi berubah" in r.get_data(as_text=True), "impor Excel lewat slug")
    token = re.search(r'name="token" value="([^"]+)"', r.get_data(as_text=True)).group(1)
    kirim(su, "/super/dosen/terapkan", token=token)
    cek(registri.cari(registri.baca(), B)["dosen_url"] == "https://dosen.unsrat.ac.id/prodi/te3", "tautan dari Excel tersimpan")
    for isi, nama, label in ((b"", "kosong.csv", "berkas kosong"), (b"x" * (impor_dosen.MAKS_BERKAS + 10), "besar.csv", "terlalu besar"),
                             (b"PK\x03\x04bukan-zip-sungguhan", "palsu.xlsx", "xlsx palsu"), (b"\xd0\xcf\x11\xe0lama", "lama.xls", "xls lama"),
                             (b"kode,nama\n55201,x\n", "tanpa-tautan.csv", "tanpa kolom tautan")):
        r = unggah(isi, nama)
        cek(r.status_code == 400 or "Kolom tautan tidak ditemukan" in r.get_data(as_text=True), "impor %s harus ditolak" % label)

    # --- the official data from www
    berubah = json.loads(json.dumps(WWW))
    berubah["prodi"]["program"][0]["akreditasi"] = "Baik Sekali"
    berubah["prodi"]["program"].append(prodi(D, "Teknik Industri"))
    tulis_www(berubah)
    teks = su.get("/super/tarik").get_data(as_text=True)
    cek("akreditasi: &#39;Unggul&#39; -&gt; &#39;Baik Sekali&#39;" in teks and "S1 Teknik Industri" in teks, "pratinjau tarik data")
    sidik = re.search(r'name="sidik" value="([0-9a-f]+)"', teks).group(1)
    cek(kirim(su, "/super/tarik/terapkan", sidik="0" * 32).status_code == 302
        and registri.warisan_per_kode()[A]["akreditasi"] == "Unggul", "pratinjau usang tidak diterapkan")
    cek(kirim(su, "/super/tarik/terapkan", sidik=sidik).status_code == 302
        and registri.warisan_per_kode()[A]["akreditasi"] == "Baik Sekali", "tarik data diterapkan")
    cek("Baik Sekali" in baca("s1ti/index.html"), "situs memakai data resmi baru")
    cek(any(x["aksi"] == "tarik-data-www" for x in audit.baca()), "tarik data tercatat")
    rusak = json.loads(json.dumps(berubah))
    rusak["prodi"]["program"][1]["bidang_kerja"] = "Daftar slot gacor"
    tulis_www(rusak)
    teks = su.get("/super/tarik").get_data(as_text=True)
    cek("tidak dapat ditarik" in teks and "teks judi" in teks, "sumber berisi judi ditampilkan sebagai masalah")
    cek(kirim(su, "/super/tarik/terapkan", sidik=sidik).status_code == 400
        and "gacor" not in json.dumps(lokasi.baca("warisan/prodi")), "sumber berisi judi tidak pernah diterapkan")
    hilang = json.loads(json.dumps(berubah))
    hilang["prodi"]["program"] = [p for p in hilang["prodi"]["program"] if p["kode_pddikti"] != B]
    tulis_www(hilang)
    teks = su.get("/super/tarik").get_data(as_text=True)
    sidik = re.search(r'name="sidik" value="([0-9a-f]+)"', teks).group(1)
    cek('name="paksa"' in teks, "terlalu banyak yang hilang: perlu konfirmasi")
    cek(kirim(su, "/super/tarik/terapkan", sidik=sidik).status_code == 400, "tanpa konfirmasi tidak diterapkan")
    cek(kirim(su, "/super/tarik/terapkan", sidik=sidik, paksa="1").status_code == 302
        and registri.warisan_per_kode()[B].get("hilang_dari_www"), "dengan konfirmasi diterapkan, elektro ditandai hilang")
    cek("<strong>1</strong> prodi hilang dari data www" in su.get("/").get_data(as_text=True), "dasbor menunjukkan prodi hilang")
    tulis_www(berubah)
    teks = su.get("/super/tarik").get_data(as_text=True)
    kirim(su, "/super/tarik/terapkan", sidik=re.search(r'name="sidik" value="([0-9a-f]+)"', teks).group(1))
    cek(not registri.warisan_per_kode()[B].get("hilang_dari_www"), "elektro kembali")

    # --- registering programmes new in www
    teks = su.get("/super/prodi").get_data(as_text=True)
    cek('value="s1mesin"' in teks and 'value="s1industri"' in teks, "usulan slug untuk prodi yang belum terdaftar")
    cek(kirim(su, "/super/prodi/daftar", kode=C, slug="s1elektro").status_code == 400, "daftar dengan slug terpakai ditolak")
    cek(kirim(su, "/super/prodi/daftar", kode="99999", slug="s1fiktif").status_code == 400, "daftar prodi yang tidak ada ditolak")
    cek(kirim(su, "/super/prodi/daftar", kode=C, slug="s1mesin").status_code == 302 and ada("s1mesin/index.html"),
        "prodi didaftarkan dan situsnya dibangun")
    cek("s1mesin" in baca("index.html"), "prodi baru di daftar halaman akar")

    # --- version history
    teks = su.get("/super/riwayat?berkas=registri").get_data(as_text=True)
    versi = re.findall(r"berkas=registri&amp;versi=([0-9-]+)", teks)
    cek(len(versi) >= 5, "riwayat registri berisi beberapa versi: %d" % len(versi))
    sebelum_slug = [v for v in __import__("riwayat").daftar(5000) if v["berkas"] == "registri" and "s1informatika -> s1ti" in v["aksi"]]
    cek(len(sebelum_slug) == 1, "versi sebelum ganti slug ditemukan")
    v = sebelum_slug[0]["versi"]
    teks = su.get("/super/riwayat/lihat?berkas=registri&versi=%s" % v).get_data(as_text=True)
    cek("s1informatika" in teks and "beda__hapus" in teks, "perbandingan versi menampilkan perbedaan")
    r = kirim(su, "/super/riwayat/pulihkan", berkas="registri", versi=v)
    cek(r.status_code == 302 and registri.cari(registri.baca(), A)["slug"] == "s1informatika", "versi registri dipulihkan")
    cek(ada("s1informatika/index.html") and not ada("s1ti/index.html"), "pemulihan diikuti bangun ulang")
    cek(any(x["aksi"] == "versi-dipulihkan" for x in audit.baca()), "pemulihan tercatat")
    # the whole file goes back: the programme registered after that version is unregistered again (the comparison
    # page shows this before the button is pressed), and registering it again works
    cek(registri.cari(registri.baca(), C) is None and not ada("s1mesin/index.html"), "pemulihan mengembalikan seluruh registri")
    cek(kirim(su, "/super/prodi/daftar", kode=C, slug="s1mesin").status_code == 302 and ada("s1mesin/index.html"),
        "prodi didaftarkan lagi setelah pemulihan")
    for url in ("/super/riwayat/lihat?berkas=../../rahasia/akun&versi=%s" % v, "/super/riwayat/lihat?berkas=registri&versi=../x",
                "/super/riwayat?berkas=../../etc", "/super/riwayat?berkas=prodi/../registri"):
        cek(su.get(url).status_code == 404, "jalur aneh di riwayat ditolak: %s" % url)
    cek(kirim(su, "/super/riwayat/pulihkan", berkas="prodi/../registri", versi=v).status_code == 404, "pulihkan jalur aneh ditolak")
    cek(su.get("/super/riwayat?berkas=prodi/%s" % A).status_code == 200, "saringan riwayat per prodi")
    # a page's own content (Fase 2) is named after the page in the history
    import isi_halaman
    isi_halaman.terbitkan(A, "sejarah", {"uraian": "Versi pertama."}, "superuji")
    isi_halaman.terbitkan(A, "sejarah", {"uraian": "Versi kedua."}, "superuji")
    cek("Teknik Informatika — halaman Sejarah" in su.get("/super/riwayat?berkas=prodi/%s" % A).get_data(as_text=True),
        "riwayat menamai isi halaman dengan nama halamannya")

    # --- accounts: role and programmes; the change applies to running sessions
    r = ad.get("/prodi/%s/" % C)
    cek(r.status_code == 403, "admin A belum punya akses ke prodi C: %s %s" % (r.status_code, r.headers.get("Location")))
    r = kirim(su, "/super/akun/%d/ubah" % adm_id, nama_lengkap="Admin A dan C", peran="admin", prodi=[A, C])
    cek(r.status_code == 302 and akun.ambil(adm_id)["prodi"] == sorted([A, C]), "prodi akun diubah lewat kotak centang: %s %r %s" % (
        r.status_code, akun.ambil(adm_id)["prodi"], re.findall(r'pesan--galat[^>]*>([^<]+)', r.get_data(as_text=True))))
    cek(ad.get("/prodi/%s/" % C).status_code == 200, "akses baru langsung berlaku di sesi yang sedang berjalan")
    kirim(su, "/super/akun/%d/ubah" % adm_id, nama_lengkap="Admin A", peran="operator", prodi=[A])
    cek(ad.get("/prodi/%s/" % C).status_code == 403 and ad.get("/prodi/%s/akun" % A).status_code == 403,
        "akses dicabut dan peran turun langsung berlaku")
    cek(kirim(su, "/super/akun/%d/ubah" % super_id, nama_lengkap="Super", peran="admin", prodi=[A]).status_code == 400
        and akun.ambil(super_id)["peran"] == "super", "superadmin tidak bisa mengubah perannya sendiri")
    cek(kirim(su, "/super/akun/%d/ubah" % adm_id, nama_lengkap="X", peran="operator", prodi=["99999"]).status_code == 400,
        "prodi yang tidak terdaftar ditolak")
    cek(kirim(su, "/super/akun/%d/ubah" % adm_id, nama_lengkap="<b>X</b>", peran="operator", prodi=[A]).status_code == 400,
        "nama ber-HTML ditolak")
    cek(su.get("/super/akun/999999").status_code == 404, "akun yang tidak ada 404")
    cek('type="checkbox" name="prodi" value="%s" checked' % A in su.get("/super/akun/%d" % adm_id).get_data(as_text=True),
        "kotak centang prodi menunjukkan pilihan sekarang")
    cek(any(x["aksi"] == "akun-diubah" and x.get("peran_lama") == "admin" for x in audit.baca()), "ubah akun tercatat")

    # --- audit filters
    teks = su.get("/super/audit?aksi=slug-diubah").get_data(as_text=True)
    cek("slug-diubah" in teks and "tarik-data-www" not in teks.split("<tbody>")[1], "saringan aksi")
    teks = su.get("/super/audit?prodi=%s" % C).get_data(as_text=True)
    cek("prodi-didaftarkan" in teks and "slug-diubah" not in teks.split("<tbody>")[1], "saringan prodi")
    for url in ("/super/audit?aksi=<script>", "/super/audit?prodi=../x", "/super/audit?oleh=a b"):
        cek(su.get(url).status_code == 404, "saringan tidak sah ditolak: %s" % url)

    # --- the rebuild queue
    a = pembangun.Antrean("mati")
    a._menunggu = {"1", "2"}
    cek(a._ambil() == ["1", "2"], "beberapa prodi dibangun satu per satu")
    a._menunggu = {str(i) for i in range(pembangun.BATAS_SATUAN + 1)}
    cek(a._ambil() == [None], "lebih dari %d prodi menjadi satu bangun ulang penuh" % pembangun.BATAS_SATUAN)
    a._menunggu = {None, "1"}
    cek(a._ambil() == [None] and a._ambil() is None, "bangun penuh mencakup permintaan prodi")
    try:
        pembangun.Antrean("lain")
        gagal.append("mode bangun tak dikenal harus ditolak")
    except ValueError:
        pass
    data_asli = os.environ["PRODI_DATA"]
    os.environ["PRODI_DATA"] = os.path.join(KERJA, "data-kosong")
    rusak = pembangun.Antrean("sinkron")
    rusak.minta(None, "penguji")
    os.environ["PRODI_DATA"] = data_asli
    cek(not rusak.status["ok"] and "GAGAL" in rusak.status["pesan"] and "data resmi belum ada" in rusak.status["keluaran"],
        "bangun yang gagal dilaporkan: %r" % rusak.status["pesan"])
    cek(any(x["aksi"] == "bangun-gagal" for x in audit.baca()), "bangun gagal tercatat")
    teks = su.get("/super/bangun").get_data(as_text=True)
    cek(app.antrean.status["ok"] and "pesan--ok" in teks, "halaman status bangun")
    cek("tidak dijadwalkan" in teks, "tanpa PRODI_BANGUN_HARIAN tidak ada bangun ulang harian")

    # --- the daily rebuild (langkah 7)
    for salah in ("2:30", "24:00", "02:60", "jam dua", ""):
        try:
            pembangun.Penjadwal(app.antrean, salah)
            gagal.append("jam bangun harian %r harus ditolak" % salah)
        except ValueError:
            pass
    j = pembangun.Penjadwal(app.antrean, "02:30")
    for sekarang, harus in (("2026-10-26T01:00", "2026-10-26T02:30"), ("2026-10-26T02:30", "2026-10-27T02:30"),
                            ("2026-10-26T23:59", "2026-10-27T02:30"), ("2026-12-31T03:00", "2027-01-01T02:30")):
        hasil = j.berikutnya(datetime.datetime.fromisoformat(sekarang)).isoformat(timespec="minutes")
        cek(hasil == harus, "bangun harian sesudah %s: %s, harus %s" % (sekarang, hasil, harus))
    try:
        app_mod.buat_app({"SECRET_KEY": "k" * 64, "PRODI_BANGUN": "mati", "PRODI_BANGUN_HARIAN": "25:00"})
        gagal.append("PRODI_BANGUN_HARIAN yang salah harus menghentikan admin")
    except SystemExit:
        pass
    app_harian = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron",
                                   "PRODI_BANGUN_HARIAN": "02:30"})
    sebelum = len(audit.baca(aksi="bangun-selesai", batas=10000))
    app_harian.penjadwal.bangun()
    cek(app_harian.antrean.status["ok"] and app_harian.antrean.status["cakupan"] == "semua"
        and len(audit.baca(aksi="bangun-selesai", batas=10000)) == sebelum + 1, "bangun ulang harian membangun semua")
    cek(audit.baca(aksi="bangun-terjadwal")[0]["oleh"] == "penjadwal", "bangun ulang harian tercatat")
    app = app_harian
    su = klien()
    cek(masuk(su, "superuji", SANDI_SUPER).status_code == 302, "superadmin masuk lagi")
    teks = su.get("/super/bangun").get_data(as_text=True)
    cek("setiap hari pukul 02:30" in teks and "terakhir" in teks, "halaman bangun menampilkan jadwal harian")

    jumlah, temuan = periksa_situs(lokasi.publik(), "superadmin")
    gagal.extend(temuan)
    print("superadmin: %d halaman situs diperiksa setelah semua perubahan" % jumlah)
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_superadmin: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
