# -*- coding: utf-8 -*-
"""Step 6 of phase 1: a programme admin's pages and the announcement workflow (platform/admin/prodi_admin.py,
pengumuman_admin.py), with real rebuilds (PRODI_BANGUN=sinkron) of made-up programmes in a temporary directory.

Checks what each page changes in the data AND on the published site: palette and social media, logos (PNG; an SVG
with a script is cleaned; wrong shapes refused), the front section (colour, unreadable colour refused, photo with
focus), the menu (a crafted request cannot hide a required page), announcements from an operator's draft to
publication (submit, send back with a note, resubmit, publish, change, withdraw) with photos and PDFs, what an
operator may not do whatever it sends, the programme's version history, and access to uploaded files.
Who may open each page at all is tested in uji_admin.py.

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
    from PIL import Image
    import flask  # noqa: F401
    import jinja2  # noqa: F401
except ImportError:
    print("uji_admin_prodi: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-adminprodi-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
for nama in ("PRODI_MODE", "PRODI_PENYIMPANAN"):
    os.environ.pop(nama, None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import cek_integritas  # noqa: E402
import lokasi  # noqa: E402
import pengumuman as pg  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B = "55201", "20201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def gambar(lebar, tinggi, fmt="JPEG", mode="RGB", warna=(20, 60, 160)):
    im = Image.new(mode, (lebar, tinggi), warna if mode == "RGB" else warna + (200,))
    buf = io.BytesIO()
    im.save(buf, fmt)
    return buf.getvalue()


def pdf(katalog=b""):
    isi = b"BT /F1 24 Tf 72 720 Td (Jadwal) Tj ET"
    objek = [b"<< /Type /Catalog /Pages 2 0 R " + katalog + b" >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
             b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
             b"<< /Length %d >>\nstream\n" % len(isi) + isi + b"\nendstream", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    keluar, letak = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objek, 1):
        letak.append(len(keluar))
        keluar += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(keluar)
    keluar += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objek) + 1) + b"".join(b"%010d 00000 n \n" % x for x in letak)
    keluar += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objek) + 1, xref)
    return bytes(keluar)


def prodi(kode, nama):
    return {"kode_pddikti": kode, "nama": nama, "nama_en": "", "jenjang": "S1", "gelar": "S.Kom.", "sks": 144, "unit_kode": "ft",
            "unit": "Fakultas Teknik", "website": "", "surel": "p@unsrat.ac.id", "bidang_kerja": "B.", "bidang_kerja_en": "",
            "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Infokom", "berlaku_hingga": "", "internasional": "", "slug": "x",
            "slug_en": "", "cpl": [{"kode": "CPL 1", "isi": "Capaian.", "isi_en": "", "kurikulum": "2025/2026"}]}


def ada(rel):
    return os.path.isfile(os.path.join(lokasi.publik(), rel))


def baca(rel):
    with io.open(os.path.join(lokasi.publik(), rel), encoding="utf-8") as f:
        return f.read()


def jumlah_unggahan():
    return sum(len(n) for _a, _d, n in os.walk(lokasi.unggahan()))


try:
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
        id_, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_, sementara, SANDI[nama])
        return akun.ambil(id_)
    super_ = akun_baru("superuji", "super", [])
    akun_baru("adma", "admin", [A], super_)
    akun_baru("opa", "operator", [A], super_)
    akun_baru("opa2", "operator", [A], super_)

    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    klien = {}
    for i, nama in enumerate(("adma", "opa", "opa2")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (20 + i)
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c

    def kirim(nama, url, unggahan=None, **data):
        c = klien[nama]
        with c.session_transaction() as s:
            data["csrf"] = s["csrf"]
        if unggahan:
            data.update(unggahan)
            return c.post(url, data=data, content_type="multipart/form-data")
        return c.post(url, data=data)

    def berkas(nama_kolom, isi, nama_berkas):
        return {nama_kolom: (io.BytesIO(isi), nama_berkas)}

    app.antrean.minta(None, "penguji")
    p = "/prodi/%s" % A

    # --- identity: palette and social media
    teks = klien["adma"].get(p + "/identitas").get_data(as_text=True)
    cek("Warna bendera fakultas" in teks and 'value="toska"' in teks, "halaman identitas: palet")
    r = kirim("adma", p + "/identitas", palet="toska", **{"medsos-0-jenis": "instagram",
                                                           "medsos-0-url": "https://www.instagram.com/ti.unsrat"})
    cek(r.status_code == 302, "identitas disimpan")
    cek("#0F5F66" in baca("s1informatika/warna.css"), "palet toska dipakai situs")
    cek('href="https://www.instagram.com/ti.unsrat" rel="me">Instagram' in baca("s1informatika/index.html"), "media sosial di kaki")
    for label, url, jenis in (("akun Facebook di kolom Instagram", "https://www.facebook.com/ti", "instagram"),
                              ("http biasa", "http://www.instagram.com/ti", "instagram"),
                              ("javascript", "javascript:alert(1)", "facebook"),
                              ("jenis tak dikenal", "https://example.com/x", "myspace")):
        r = kirim("adma", p + "/identitas", palet="toska", **{"medsos-0-jenis": jenis, "medsos-0-url": url})
        cek(r.status_code == 400, "media sosial %s ditolak" % label)
    cek(kirim("adma", p + "/identitas", palet="ungu-muda").status_code == 400, "palet tak dikenal ditolak")
    cek(lokasi.baca("prodi/%s/situs" % A)["media_sosial"][0]["url"] == "https://www.instagram.com/ti.unsrat",
        "penolakan tidak mengubah data")

    # --- logos
    r = kirim("adma", p + "/identitas/logo", berkas("logo", gambar(400, 200, "PNG", "RGBA"), "logo.png"))
    cek(r.status_code == 302, "logo PNG diunggah: %s" % r.status_code)
    logo = lokasi.baca("prodi/%s/situs" % A)["logo"]
    cek(logo["format"] == "png" and logo["varian"]["56"]["lebar"] == 112, "logo PNG: tinggi 56, lebar mengikuti bentuk")
    beranda = baca("s1informatika/index.html")
    cek('class="merek__logo"' in beranda and "2x" in beranda, "logo di kepala situs dengan srcset")
    cek(all(ada("unggahan/" + v["jalur"]) for v in logo["varian"].values()), "berkas logo diterbitkan")
    svg = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100" width="200" height="100">'
           b'<script>alert(1)</script><rect width="200" height="100" fill="#003366" onload="alert(2)"/>'
           b'<a href="javascript:alert(3)"><text x="10" y="50">TI</text></a></svg>')
    cek(kirim("adma", p + "/identitas/logo", berkas("logo", svg, "logo.svg")).status_code == 302, "logo SVG diunggah")
    logo = lokasi.baca("prodi/%s/situs" % A)["logo"]
    with io.open(os.path.join(lokasi.unggahan(), *logo["varian"]["svg"]["jalur"].split("/")), "rb") as f:
        isi_svg = f.read()
    cek(logo["format"] == "svg" and b"script" not in isi_svg and b"onload" not in isi_svg and b"javascript" not in isi_svg,
        "SVG dibersihkan dari skrip")
    r = klien["adma"].get(p + "/berkas/" + logo["varian"]["svg"]["jalur"])
    cek(r.status_code == 200 and "default-src 'none'" in r.headers.get("Content-Security-Policy", ""),
        "SVG di admin disajikan dengan CSP ketat")
    for isi, nama_berkas, label in ((b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100"/>', "lebar.svg", "SVG 10:1"),
                                    (gambar(100, 100, "PNG"), "kecil.png", "PNG terlalu kecil"),
                                    (b"<?php echo 1; ?>", "logo.png", "bukan gambar"),
                                    (b'<!DOCTYPE svg [<!ENTITY x "y">]><svg xmlns="http://www.w3.org/2000/svg"/>', "xxe.svg", "SVG dengan entitas")):
        cek(kirim("adma", p + "/identitas/logo", berkas("logo", isi, nama_berkas)).status_code == 400, "logo %s ditolak" % label)
    cek(kirim("adma", p + "/identitas/logo/hapus").status_code == 302 and 'class="merek__logo"' not in baca("s1informatika/index.html"),
        "logo dilepas dari situs")

    # --- the front section
    r = kirim("adma", p + "/beranda", latar="warna", warna="#1f3a5f", judul="Informatika UNSRAT", pengantar="Kalimat baru.",
              **{"kartu-sks-sembunyi": "1", "tambahan-0-label": "Mahasiswa aktif", "tambahan-0-nilai": "812"})
    cek(r.status_code == 302, "bagian depan disimpan")
    beranda = baca("s1informatika/index.html")
    cek(">Informatika UNSRAT</h1>" in beranda and "Kalimat baru." in beranda and "Mahasiswa aktif" in beranda
        and "144 SKS" not in beranda, "bagian depan di situs")
    cek("--hero-latar: #1F3A5F;" in baca("s1informatika/warna.css"), "warna latar di warna.css")
    r = kirim("adma", p + "/beranda", latar="warna", warna="#808080")
    cek(r.status_code == 400 and "sulit dibaca" in r.get_data(as_text=True)
        and lokasi.baca("prodi/%s/situs" % A)["beranda"]["latar"]["warna"] == "#1F3A5F", "warna tak terbaca ditolak")
    cek(kirim("adma", p + "/beranda", latar="foto").status_code == 400, "latar foto tanpa foto ditolak")
    cek(kirim("adma", p + "/beranda", latar="pucat", **{"kartu-gelar-urutan": "abc"}).status_code == 400, "urutan bukan angka ditolak")
    r = kirim("adma", p + "/beranda/foto", berkas("foto", gambar(3000, 1000), "latar.jpg"), fokus="kiri")
    cek(r.status_code == 302, "foto latar diunggah")
    latar = lokasi.baca("prodi/%s/situs" % A)["beranda"]["latar"]
    cek(latar["jenis"] == "foto" and latar["foto"]["fokus"] == "kiri", "foto latar dipakai dengan titik fokus")
    cek(".pahlawan--foto" in baca("s1informatika/warna.css"), "foto latar di situs")
    teks = klien["adma"].get(p + "/beranda").get_data(as_text=True)
    url_foto = re.search(r'src="(/prodi/%s/berkas/[^"]+)"' % A, teks).group(1)
    r = klien["adma"].get(url_foto)
    cek(r.status_code == 200 and r.mimetype == "image/jpeg", "pratinjau foto lewat admin")
    cek(kirim("adma", p + "/beranda/foto", berkas("foto", gambar(1200, 600), "kecil.jpg")).status_code == 400, "foto latar kecil ditolak")

    # --- the menu
    r = kirim("adma", p + "/menu", **{"label-sejarah": "Riwayat Prodi", "urutan-sejarah": "9", "sembunyi-jadwal": "1"})
    cek(r.status_code == 302, "menu disimpan")
    cek("Riwayat Prodi" in baca("s1informatika/profil/index.html") and not ada("s1informatika/akademik/jadwal/index.html"),
        "menu di situs")
    cek(kirim("adma", p + "/menu", **{"sembunyi-sejarah": "1"}).status_code == 400 and ada("s1informatika/profil/sejarah/index.html"),
        "permintaan buatan tidak bisa menyembunyikan halaman wajib")
    cek(kirim("adma", p + "/menu", **{"label-sejarah": "<b>x</b>"}).status_code == 400, "label ber-HTML ditolak")

    # --- announcements: an operator's draft to publication
    sebelum = jumlah_unggahan()
    r = kirim("opa", p + "/pengumuman/baru", berkas("foto", gambar(1200, 800), "a.jpg"), judul="Jadwal UAS", tanggal="2026-10-20",
              kategori="akademik", ringkasan="Jadwal ujian akhir.", isi="Paragraf.\n\n- satu\n- dua", aksi_simpan="ajukan")
    cek(r.status_code == 400 and jumlah_unggahan() == sebelum, "foto tanpa teks alternatif ditolak sebelum disimpan")
    r = kirim("opa", p + "/pengumuman/baru", dict(berkas("foto", gambar(1200, 800), "a.jpg"), **berkas("pdf", pdf(), "j.pdf")),
              judul="Jadwal UAS", tanggal="2026-10-20", kategori="akademik", ringkasan="Jadwal ujian akhir.",
              isi="Paragraf.\n\n- satu\n- dua", foto_alt="Poster jadwal", pdf_judul="Jadwal lengkap", aksi_simpan="terbit")
    cek(r.status_code == 302, "operator membuat pengumuman")
    b = pg.baca(A)["butir"][-1]
    id_ = b["id"]
    cek(b["status"] == "draf" and b["oleh"] == "opa", "operator tidak bisa menerbitkan lewat tombol buatan: %s" % b["status"])
    cek(not ada("s1informatika/pengumuman/%s/index.html" % id_), "draf tidak di situs")
    cek(kirim("opa", p + "/pengumuman/%s/status" % id_, aksi="terbitkan").status_code == 403, "operator tidak bisa menerbitkan")
    cek(kirim("opa", p + "/pengumuman/%s/status" % id_, aksi="ajukan").status_code == 302
        and pg.cari(A, id_)["status"] == "menunggu", "operator mengajukan")
    cek(klien["opa2"].get(p + "/pengumuman/%s" % id_).status_code == 403, "operator lain tidak melihat pengumuman ini")
    cek(kirim("opa2", p + "/pengumuman/%s" % id_, judul="Diubah orang lain").status_code == 403, "operator lain tidak bisa mengubah")
    cek("1 pengumuman menunggu persetujuan" in klien["adma"].get(p + "/").get_data(as_text=True), "admin melihat yang menunggu")
    cek(kirim("adma", p + "/pengumuman/%s/status" % id_, aksi="kembalikan", catatan="").status_code == 302
        and pg.cari(A, id_)["status"] == "menunggu", "kembalikan tanpa catatan tidak berlaku")
    kirim("adma", p + "/pengumuman/%s/status" % id_, aksi="kembalikan", catatan="Lengkapi ruang ujian.")
    b = pg.cari(A, id_)
    cek(b["status"] == "draf" and b["catatan"] == "Lengkapi ruang ujian.", "dikembalikan dengan catatan")
    cek("Lengkapi ruang ujian." in klien["opa"].get(p + "/pengumuman/%s" % id_).get_data(as_text=True), "operator melihat catatan")
    r = kirim("opa", p + "/pengumuman/%s" % id_, berkas("foto", gambar(900, 600), "b.jpg"), judul="Jadwal UAS gasal",
              tanggal="2026-10-20", kategori="akademik", ringkasan="Jadwal ujian akhir dan ruangnya.", isi="Ruang A1.",
              foto_alt="Foto ruang ujian", **{"foto-0-alt": "Poster jadwal UAS", "pdf-0-hapus": "1", "foto_utama": "0",
                                              "aksi_simpan": "ajukan"})
    b = pg.cari(A, id_)
    cek(r.status_code == 302 and b["status"] == "menunggu" and b["judul"] == "Jadwal UAS gasal" and len(b["foto"]) == 2
        and not b["pdf"] and b["foto"][0]["alt"] == "Poster jadwal UAS", "operator mengubah dan mengajukan lagi: %r" % (b["status"],))
    cek(b["id"] == id_, "alamat pengumuman tetap walau judul berubah")
    cek(kirim("adma", p + "/pengumuman/%s/status" % id_, aksi="terbitkan").status_code == 302, "admin menerbitkan")
    cek(ada("s1informatika/pengumuman/%s/index.html" % id_) and "Jadwal UAS gasal" in baca("s1informatika/pengumuman/rss.xml"),
        "pengumuman terbit di situs dan RSS")
    cek(kirim("opa", p + "/pengumuman/%s" % id_, judul="Diubah setelah terbit", tanggal="2026-10-20", kategori="akademik",
              ringkasan="R").status_code == 403, "operator tidak bisa mengubah yang sudah terbit")
    r = kirim("adma", p + "/pengumuman/%s" % id_, judul="Jadwal UAS gasal 2026/2027", tanggal="2026-10-20", kategori="akademik",
              ringkasan="Jadwal ujian akhir dan ruangnya.", isi="Ruang A1.",
              **{"foto-0-alt": "Poster jadwal UAS", "foto-1-alt": "Foto ruang ujian", "foto_utama": "1", "aksi_simpan": "simpan"})
    cek(r.status_code == 302 and "Jadwal UAS gasal 2026/2027" in baca("s1informatika/pengumuman/%s/index.html" % id_),
        "admin mengubah pengumuman terbit; situs dibangun ulang")
    cek(pg.cari(A, id_)["foto"][0]["alt"] == "Foto ruang ujian", "foto utama dipilih ulang")
    cek(kirim("adma", p + "/pengumuman/%s/status" % id_, aksi="tarik").status_code == 302
        and not ada("s1informatika/pengumuman/%s/index.html" % id_), "admin menarik dari situs")
    r = kirim("adma", p + "/pengumuman/baru", berkas("pdf", pdf(b"/OpenAction << /S /JavaScript /JS (x) >>"), "x.pdf"),
              judul="PDF berbahaya", tanggal="2026-10-21", kategori="kegiatan", ringkasan="R", pdf_judul="X", aksi_simpan="terbit")
    cek(r.status_code == 400 and "konten aktif" in r.get_data(as_text=True), "PDF berskrip ditolak")
    r = kirim("adma", p + "/pengumuman/baru", judul="Langsung terbit", tanggal="2026-10-22", kategori="kegiatan",
              ringkasan="Admin menerbitkan langsung.", aksi_simpan="terbit")
    langsung = pg.baca(A)["butir"][-1]["id"]
    cek(r.status_code == 302 and ada("s1informatika/pengumuman/%s/index.html" % langsung), "admin menerbitkan langsung")
    cek(klien["adma"].get(p + "/pengumuman/..%2F..%2Fregistri").status_code == 404, "id pengumuman aneh 404")
    teks = klien["opa"].get(p + "/pengumuman").get_data(as_text=True)
    cek("Jadwal UAS gasal" in teks and "Langsung terbit" not in teks, "operator hanya melihat pengumumannya sendiri")
    log = [x["aksi"] for x in audit.baca(prodi=A, batas=1000)]
    for aksi in ("pengumuman-dibuat", "pengumuman-ajukan", "pengumuman-kembalikan", "pengumuman-terbitkan", "pengumuman-tarik",
                 "identitas-diubah", "logo-diunggah", "beranda-diubah", "foto-latar-diunggah", "menu-diubah"):
        cek(aksi in log, "log audit mencatat %s" % aksi)

    # --- uploaded files: this programme's only
    foto = pg.cari(A, id_)["foto"][0]["varian"]["400"]["jalur"]
    cek(klien["opa"].get(p + "/berkas/" + foto).status_code == 200, "operator melihat foto prodinya")
    lain = foto.replace(A + "/", B + "/", 1)
    cek(klien["adma"].get(p + "/berkas/" + lain).status_code == 404, "berkas prodi lain lewat prodi ini 404")
    cek(klien["adma"].get(p + "/berkas/" + A + "/..%2F..%2Frahasia%2Fakun.sqlite").status_code == 404, "jalur ../ 404")

    # --- the programme's version history
    teks = klien["adma"].get(p + "/riwayat").get_data(as_text=True)
    versi = re.findall(r"berkas=prodi/%s/situs&amp;versi=([0-9-]+)" % A, teks)
    cek(len(versi) >= 5, "riwayat situs prodi: %d versi" % len(versi))
    pertama = versi[-1]                                  # the oldest: before the palette was chosen
    teks = klien["adma"].get(p + "/riwayat/lihat?berkas=prodi/%s/situs&versi=%s" % (A, pertama)).get_data(as_text=True)
    cek("toska" in teks and "beda__tambah" in teks, "perbandingan versi")
    r = kirim("adma", p + "/riwayat/pulihkan", berkas="prodi/%s/situs" % A, versi=pertama)
    cek(r.status_code == 302 and lokasi.baca("prodi/%s/situs" % A).get("palet") != "toska", "versi lama dipulihkan")
    cek("#0F5F66" not in baca("s1informatika/warna.css"), "situs dibangun ulang setelah pemulihan")
    cek(klien["adma"].get(p + "/riwayat/lihat?berkas=registri&versi=%s" % pertama).status_code == 404, "berkas di luar prodi 404")
    cek(klien["adma"].get(p + "/riwayat/lihat?berkas=prodi/%s/situs&versi=%s" % (B, pertama)).status_code == 404, "berkas prodi lain 404")
    cek(kirim("adma", p + "/riwayat/pulihkan", berkas="prodi/%s/situs" % B, versi=pertama).status_code == 404, "pulihkan prodi lain 404")

    # --- dashboards
    teks = klien["adma"].get(p + "/").get_data(as_text=True)
    cek("Kesiapan situs" in teks and "halaman wajib akreditasi" in teks, "dasbor admin: kesiapan")
    teks = klien["opa"].get(p + "/").get_data(as_text=True)
    cek("Pengumuman Anda" in teks and "Kesiapan situs" not in teks, "dasbor operator")

    app.antrean.minta(None, "penguji")
    jumlah, temuan = periksa_situs(lokasi.publik(), "admin-prodi")
    gagal.extend(temuan)
    cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "cek integritas bersih")
    print("admin prodi: %d halaman situs diperiksa" % jumlah)
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_admin_prodi: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
