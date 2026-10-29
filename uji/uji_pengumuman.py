# -*- coding: utf-8 -*-
"""Step 3b of phase 1: announcements and news (platform/pengumuman.py, platform/media.py, the pages in bangun.py).

Photos and PDFs are made here (Pillow, a hand-written PDF, pypdf), stored with the local storage in a temporary
directory; the GCS storage is checked against a fake client. Then a made-up programme gets announcements in every
state and the built pages are checked: lists and their pages, categories, years, one page per item, the home page,
"Kabar terkait" on accreditation pages, RSS, link previews, withdrawing, and the page and integrity checks.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image
    import jinja2  # noqa: F401
    import pypdf
except ImportError:
    print("uji_pengumuman: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-pengumuman-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"),
                  ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
for nama in ("PRODI_MODE", "PRODI_PENYIMPANAN"):
    os.environ.pop(nama, None)

import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import pengumuman  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

HARI_INI = "2026-10-26"
logging.getLogger("pypdf").setLevel(logging.ERROR)     # the broken-PDF cases are expected to make it complain
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def harus_gagal(fungsi, pesan, *args, **kw):
    try:
        fungsi(*args, **kw)
    except (ValueError, pengumuman.GagalPengumuman) as e:
        return e
    gagal.append(pesan)
    return None


# ------------------------------------------------------------------ made-up files

def jpeg(lebar=1200, tinggi=800, exif_gps=False, fmt="JPEG", mode="RGB"):
    im = Image.new(mode, (lebar, tinggi), (20, 60, 160) if mode == "RGB" else (20, 60, 160, 128))
    buf = io.BytesIO()
    if exif_gps:
        exif = Image.Exif()
        exif[0x010F] = "PonselUji"                     # Make
        exif[0x8825] = {1: "N", 2: (1.0, 29.0, 0.0)}  # GPS
        im.save(buf, fmt, exif=exif)
    else:
        im.save(buf, fmt)
    return buf.getvalue()


def pdf(teks="Jadwal ujian", katalog_tambahan=b""):
    """A one-page PDF with real text, written by hand (correct cross-reference table)."""
    isi = b"BT /F1 24 Tf 72 720 Td (" + teks.encode("latin-1") + b") Tj ET"
    objek = [b"<< /Type /Catalog /Pages 2 0 R " + katalog_tambahan + b" >>",
             b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
             b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
             b"/Resources << /Font << /F1 5 0 R >> >> >>",
             b"<< /Length %d >>\nstream\n" % len(isi) + isi + b"\nendstream",
             b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    keluar, letak = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objek, 1):
        letak.append(len(keluar))
        keluar += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(keluar)
    keluar += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objek) + 1) + b"".join(b"%010d 00000 n \n" % x for x in letak)
    keluar += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objek) + 1, xref)
    return bytes(keluar)


def pdf_terkunci():
    w = pypdf.PdfWriter()
    w.add_blank_page(612, 792)
    w.encrypt("rahasia")
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


class BlobPalsu(object):
    def __init__(self, gudang, nama):
        self.gudang, self.nama = gudang, nama
        self.cache_control = self.content_disposition = None

    def exists(self):
        return self.nama in self.gudang.isi

    def upload_from_string(self, data, content_type):
        self.gudang.isi[self.nama] = (data, content_type, self.cache_control, self.content_disposition)


class KlienPalsu(object):
    def __init__(self):
        self.isi = {}

    def bucket(self, nama):
        self.nama_bucket = nama
        return self

    def blob(self, nama):
        return BlobPalsu(self, nama)


try:
    # --- photos
    hasil = media.olah_foto(jpeg(2000, 1000, exif_gps=True))
    cek(sorted(hasil) == [400, 800, 1600], "foto lebar harus punya 3 ukuran: %r" % sorted(hasil))
    cek(hasil[1600][1] == (1600, 800), "ukuran 1600 harus menjaga rasio")
    for lebar, (isi, _ukuran) in hasil.items():
        with Image.open(io.BytesIO(isi)) as im:
            cek(im.format == "JPEG" and not im.getexif(), "foto %d harus JPEG tanpa EXIF/GPS" % lebar)
    sempit = media.olah_foto(jpeg(700, 500))
    cek(sorted(sempit) == [400, 1600] and sempit[1600][1] == (700, 500), "foto sempit tanpa ukuran ganda: %r" % sorted(sempit))
    png = media.olah_foto(jpeg(900, 600, fmt="PNG", mode="RGBA"))
    with Image.open(io.BytesIO(png[1600][0])) as im:
        cek(im.format == "JPEG" and im.mode == "RGB", "PNG transparan menjadi JPEG berlatar putih")
    harus_gagal(media.olah_foto, "foto terlalu kecil harus ditolak", jpeg(500, 400))
    harus_gagal(media.olah_foto, "GIF harus ditolak", jpeg(800, 600, fmt="GIF", mode="RGB"))
    harus_gagal(media.olah_foto, "WebP harus ditolak", jpeg(800, 600, fmt="WEBP"))
    harus_gagal(media.olah_foto, "bukan gambar harus ditolak", b"<?php echo 1; ?>")
    harus_gagal(media.olah_foto, "foto kosong harus ditolak", b"")
    harus_gagal(media.olah_foto, "foto melebihi batas ukuran berkas harus ditolak", b"\xff\xd8" + b"0" * (media.MAKS_FOTO + 1))
    harus_gagal(media.simpan_foto, "foto tanpa teks alternatif harus ditolak", "55201", jpeg(), "  ")

    # --- PDFs
    cek(media.periksa_pdf(pdf()) == 1, "PDF sah harus lolos (1 halaman)")
    harus_gagal(media.periksa_pdf, "bukan PDF harus ditolak", b"<html>bukan pdf</html>")
    harus_gagal(media.periksa_pdf, "PDF rusak harus ditolak", b"%PDF-1.4\nsampah")
    harus_gagal(media.periksa_pdf, "PDF terkunci harus ditolak", pdf_terkunci())
    harus_gagal(media.periksa_pdf, "PDF dengan JavaScript harus ditolak",
                pdf(katalog_tambahan=b"/OpenAction << /S /JavaScript /JS (app.alert(1)) >>"))
    harus_gagal(media.periksa_pdf, "PDF dengan nama tersamar /J#61vaScript harus ditolak",
                pdf(katalog_tambahan=b"/OpenAction << /S /J#61vaScript /JS (x) >>"))
    harus_gagal(media.periksa_pdf, "PDF dengan aksi Launch harus ditolak",
                pdf(katalog_tambahan=b"/OpenAction << /S /Launch /F (cmd.exe) >>"))
    harus_gagal(media.periksa_pdf, "PDF dengan berkas sisipan harus ditolak",
                pdf(katalog_tambahan=b"/Names << /EmbeddedFiles << /Names [] >> >>"))
    e = harus_gagal(media.periksa_pdf, "PDF berisi teks judi harus ditolak", pdf("Daftar slot gacor maxwin"))
    cek(e is None or "terlarang" in str(e), "penolakan PDF judi harus menyebut istilah terlarang")
    harus_gagal(media.periksa_pdf, "PDF melebihi batas ukuran harus ditolak", b"%PDF-" + b"0" * media.MAKS_PDF)
    harus_gagal(media.simpan_pdf, "PDF tanpa judul harus ditolak", "55201", pdf(), "")

    # --- storage
    lokal = media.PenyimpananLokal()
    r = lokal.simpan("55201", "202610-aaaaaaaaaaaa.pdf", b"x", "application/pdf")
    cek(r == {"jalur": "55201/202610-aaaaaaaaaaaa.pdf"}, "penyimpanan lokal mengembalikan jalur")
    try:
        lokal.simpan("55201", "202610-aaaaaaaaaaaa.pdf", b"y", "application/pdf")
        gagal.append("penyimpanan lokal tidak boleh menimpa berkas")
    except FileExistsError:
        pass
    for jalur, sah in (("55201/202610-0123456789ab-800.jpg", True), ("55201/202610-0123456789ab.pdf", True),
                       ("../etc/passwd", False), ("55201/../../x.pdf", False), ("55201/foto.php", False),
                       ("55201/202610-0123456789ab.jpg.php", False), ("", False)):
        cek(media.jalur_sah(jalur) == sah, "jalur_sah(%r) harus %s" % (jalur, sah))
    for url, sah in (("https://storage.googleapis.com/unsrat-web/prodi/55201/a.jpg", True),
                     ("https://jahat.com/a.jpg", False), ("javascript:alert(1)", False),
                     ('https://storage.googleapis.com/x/a.jpg" onerror="x', False)):
        cek(media.url_sah(url) == sah, "url_sah(%r) harus %s" % (url, sah))
    os.environ.update(GCS_BUCKET="unsrat-web", GCS_PREFIX="staging/")
    palsu = KlienPalsu()
    gcs = media.PenyimpananGCS(klien=palsu)
    rekam = media.simpan_pdf("55201", pdf(), "Jadwal", gudang=gcs)
    nama_objek = list(palsu.isi)[0]
    cek(nama_objek.startswith("staging/prodi/55201/") and nama_objek.endswith(".pdf"), "objek GCS di folder prodi: %s" % nama_objek)
    cek(rekam["url"] == "https://storage.googleapis.com/unsrat-web/" + nama_objek, "URL publik GCS")
    _data, tipe, cache, disposisi = palsu.isi[nama_objek]
    cek(tipe == "application/pdf" and disposisi == "inline" and "immutable" in cache, "PDF di GCS: tipe, inline, cache")
    foto = media.simpan_foto("55201", jpeg(), "Foto uji", gudang=gcs)
    cek(len(foto["varian"]) == 3 and all(media.url_sah(v["url"]) for v in foto["varian"].values()), "foto ke GCS: 3 ukuran")
    harus_gagal(gcs.simpan, "objek GCS yang sudah ada tidak boleh ditimpa", "55201", nama_objek.split("/")[-1], b"x", "application/pdf")
    os.environ["PRODI_PENYIMPANAN"] = "s3"
    harus_gagal(media.penyimpanan, "penyimpanan tak dikenal harus ditolak")
    os.environ.pop("PRODI_PENYIMPANAN")

    # --- the model
    kode = "55201"
    dasar = {"judul": "Jadwal UTS", "kategori": "akademik", "ringkasan": "Jadwal ujian tengah semester.", "tanggal": "2026-10-20"}
    id1 = pengumuman.tambah(kode, dasar, "penguji")
    cek(id1 == "2026-10-20-jadwal-uts", "id dari tanggal dan judul: %s" % id1)
    id2 = pengumuman.tambah(kode, dasar, "penguji")
    cek(id2 == "2026-10-20-jadwal-uts-2", "id ganda diberi akhiran: %s" % id2)
    cek(pengumuman.buat_id("2026-01-01", "Ąkreditasi Ünggul!!", set()) == "2026-01-01-kreditasi-nggul", "id hanya ASCII")
    cek(pengumuman.buat_id("2026-01-01", "x" * 200, set()).__len__() <= pengumuman.MAKS_ID, "id dibatasi panjangnya")
    for label, ubah in (("HTML di judul", {"judul": "<script>alert(1)</script>"}),
                        ("HTML di isi", {"isi": "Halo <img src=x onerror=alert(1)>"}),
                        ("judi di ringkasan", {"ringkasan": "info slot gacor"}),
                        ("judul terlalu panjang", {"judul": "x" * 151}),
                        ("ringkasan kosong", {"ringkasan": " "}),
                        ("kategori tak dikenal", {"kategori": "gosip"}),
                        ("tanggal salah", {"tanggal": "2026-02-30"}),
                        ("kedaluwarsa sebelum tanggal", {"kedaluwarsa": "2026-10-01"}),
                        ("foto dengan jalur berbahaya", {"foto": [{"jenis": "gambar", "alt": "x", "varian": {"800": {"jalur": "../../etc/passwd", "lebar": 1, "tinggi": 1}}}]}),
                        ("foto tanpa alt", {"foto": [{"jenis": "gambar", "alt": "", "varian": {"800": {"jalur": "55201/202610-0123456789ab-800.jpg", "lebar": 1, "tinggi": 1}}}]}),
                        ("PDF dari host lain", {"pdf": [{"jenis": "pdf", "judul": "x", "url": "https://jahat.com/x.pdf"}]}),
                        ("terlalu banyak PDF", {"pdf": [{"jenis": "pdf", "judul": "x", "jalur": "55201/202610-0123456789ab.pdf"}] * 4})):
        harus_gagal(pengumuman.tambah, "pengumuman dengan %s harus ditolak" % label, kode, dict(dasar, **ubah), "penguji")
    pengumuman.ubah(kode, id1, {"judul": "Jadwal UTS (diperbarui)", "tanggal": "2026-10-21"}, "penguji")
    b = [x for x in pengumuman.baca(kode)["butir"] if x["id"] == id1][0]
    cek(b["judul"] == "Jadwal UTS (diperbarui)" and b["id"] == id1, "mengubah judul tidak mengubah id/alamat")
    harus_gagal(pengumuman.ubah, "id tidak boleh diubah", kode, id1, {"id": "lain"}, "penguji")
    harus_gagal(pengumuman.ubah, "status tidak diubah lewat ubah()", kode, id1, {"status": "terbit"}, "penguji")
    harus_gagal(pengumuman.ubah, "pengubahan yang tidak sah ditolak", kode, id1, {"judul": "<b>x</b>"}, "penguji")
    harus_gagal(pengumuman.ganti_status, "status tak dikenal ditolak", kode, id1, "hapus", "penguji")
    cek(pengumuman.terbit(pengumuman.baca(kode)) == [], "draf tidak ikut terbit")
    cek(any(v["berkas"] == "prodi/55201/pengumuman" for v in __import__("riwayat").daftar()), "perubahan masuk riwayat")
    lokasi.tulis_json(lokasi.path_data("prodi/55201/pengumuman"), {"butir": []})

    # --- command line
    berkas_foto = os.path.join(KERJA, "f.jpg")
    with open(berkas_foto, "wb") as f:
        f.write(jpeg())
    cek(pengumuman.main(["tambah", "--prodi", kode, "--judul", "Uji CLI", "--kategori", "kegiatan", "--ringkasan", "R",
                         "--foto", berkas_foto]) == 1, "--foto tanpa --alt harus gagal")
    cek(pengumuman.main(["tambah", "--prodi", "../x", "--judul", "U", "--kategori", "kegiatan", "--ringkasan", "R"]) == 1,
        "kode prodi berbahaya harus ditolak")
    cek(pengumuman.main(["tambah", "--prodi", kode, "--judul", "Uji CLI", "--kategori", "kegiatan", "--ringkasan", "R",
                         "--tanggal", "2024-05-01", "--foto", berkas_foto, "--alt", "Foto CLI", "--terbit"]) == 0,
        "tambah lewat baris perintah")
    cek(len(pengumuman.terbit(pengumuman.baca(kode))) == 1, "pengumuman dari baris perintah terbit")

    # --- a made-up programme with announcements in every state, then the build
    os.makedirs(os.environ["WWW_DATA"])
    www = {"prodi": {"tampilkan_berlaku_hingga": False, "program": [
               {"kode_pddikti": "55201", "nama": "Teknik Informatika", "jenjang": "S1", "unit_kode": "ft",
                "unit": "Fakultas Teknik", "slug": "s1-ti", "gelar": "S.Kom.", "sks": 144, "cpl": []},
               {"kode_pddikti": "20201", "nama": "Teknik Elektro", "jenjang": "S1", "unit_kode": "ft",
                "unit": "Fakultas Teknik", "slug": "s1-te", "cpl": []}]},
           "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
           "kalender": {"semester": []},
           "situs": {"identitas": {"nama": {"id": "Universitas Sam Ratulangi"}}, "kontak": {}}}
    for nama, isi in www.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n55201,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "20201,S1,Teknik Elektro,FT,s1elektro,x,x\n")
    registri.siapkan_dari_csv("penguji", path_csv)

    foto_a = media.simpan_foto(kode, jpeg(1600, 900), "Poster jadwal ujian")
    foto_b = media.simpan_foto(kode, jpeg(800, 600), "Tim lomba di panggung")
    lampiran = media.simpan_pdf(kode, pdf(), "Jadwal lengkap")

    def t(judul, tanggal, kategori, status="terbit", **lain):
        return pengumuman.tambah(kode, dict({"judul": judul, "ringkasan": "Ringkasan " + judul, "tanggal": tanggal,
                                             "kategori": kategori}, **lain), "penguji", status)
    utama = t("Jadwal UAS", "2026-10-25", "akademik", foto=[foto_a, foto_b], pdf=[lampiran], sematkan=True,
              isi="Paragraf satu: nilai 5 > 3 & \"kutip\".\n\n- butir satu\n- butir dua https://www.unsrat.ac.id/x.html.\n\nAkhir.")
    lewat = t("Pendaftaran lomba (sudah lewat)", "2026-09-01", "prestasi-mahasiswa", sematkan=True, kedaluwarsa="2026-09-30")
    draf = t("Masih draf", "2026-10-24", "kegiatan", status="draf")
    menunggu = t("Menunggu persetujuan", "2026-10-24", "kegiatan", status="menunggu")
    tarik = t("Akan ditarik", "2026-10-23", "kegiatan")
    pengumuman.ganti_status(kode, tarik, "ditarik", "penguji")
    for i in range(12):
        t("Kegiatan ke-%d" % (i + 1), "2025-%02d-10" % (i + 1), "kegiatan")
    t("Kerja sama industri", "2026-03-03", "kerja-sama")
    t("Hibah penelitian", "2026-04-04", "penelitian")
    # local files of an item that was later lost: the item is skipped with a warning
    hilang = media.simpan_foto(kode, jpeg(), "Foto yang hilang")
    t("Berkas hilang", "2026-02-02", "kegiatan", foto=[hilang])
    os.remove(os.path.join(lokasi.unggahan(), *hilang["varian"]["800"]["jalur"].split("/")))

    b = bangun.Pembangun(produksi=False, hari_ini=HARI_INI)
    b.bangun()
    pub = lokasi.publik()

    def ada(rel):
        return os.path.isfile(os.path.join(pub, rel))

    def baca(rel):
        with io.open(os.path.join(pub, rel), encoding="utf-8") as f:
            return f.read()

    p = "s1informatika/pengumuman/"
    jumlah, temuan = periksa_situs(pub, "pengumuman")
    gagal.extend(temuan)
    cek(any("Berkas hilang" in x or "berkasnya tidak ada" in x for x in b.peringatan), "berkas hilang harus diperingatkan")
    terbit = [x for x in pengumuman.terbit(pengumuman.baca(kode))]
    tampil = len(terbit) - 1                     # minus the one whose file is gone
    cek(tampil == 17, "17 pengumuman tampil, ada %d" % tampil)
    cek(ada(p + "index.html") and ada(p + "halaman/2/index.html") and not ada(p + "halaman/3/index.html"),
        "17 pengumuman = 2 halaman daftar")
    cek(baca(p + "index.html").count('class="kabar"') == 12, "12 pengumuman per halaman")
    for id_ in (utama, lewat):
        cek(ada(p + id_ + "/index.html"), "halaman pengumuman %s harus ada" % id_)
    for id_ in (draf, menunggu, tarik):
        cek(not ada(p + id_ + "/index.html"), "pengumuman %s tidak boleh terbit" % id_)
        cek(id_ not in baca(p + "index.html") and id_ not in baca("s1informatika/index.html"), "%s tidak boleh ditautkan" % id_)
    cek(not ada(p + "2026-02-02-berkas-hilang/index.html"), "pengumuman yang berkasnya hilang tidak terbit")
    for k in ("akademik", "kegiatan", "prestasi-mahasiswa", "kerja-sama", "penelitian"):
        cek(ada(p + "kategori/%s/index.html" % k), "halaman kategori %s" % k)
    cek(not ada(p + "kategori/pkm/index.html"), "kategori tanpa isi tidak dibuat")
    cek(ada(p + "kategori/kegiatan/halaman/2/index.html"), "kategori kegiatan (13 butir) punya halaman 2")
    for th in ("2026", "2025", "2024"):
        cek(ada(p + "arsip/%s/index.html" % th), "arsip tahun %s" % th)

    beranda = baca("s1informatika/index.html")
    blok = beranda.split('id="judul-kabar"')[1].split("</section>")[0]
    cek(utama in blok, "pengumuman disematkan tampil di beranda")
    cek(lewat not in blok, "pengumuman disematkan yang kedaluwarsa tidak tampil di beranda")
    cek(blok.count('class="kabar"') == 1 + bangun.DI_BERANDA, "beranda: 1 disematkan + %d terbaru" % bangun.DI_BERANDA)
    cek("Berakhir 30 September 2026" in baca(p + "kategori/prestasi-mahasiswa/index.html"), "tanda kedaluwarsa di daftar")
    cek(not ada("s1elektro/pengumuman/2026-10-25-jadwal-uas/index.html"), "pengumuman satu prodi tidak muncul di prodi lain")
    cek("Belum ada pengumuman" in baca("s1elektro/pengumuman/index.html"), "prodi tanpa pengumuman")

    detail = baca(p + utama + "/index.html")
    cek("nilai 5 &gt; 3 &amp; &#34;kutip&#34;." in detail, "isi harus di-escape")
    cek("<li>butir satu</li>" in detail, "daftar '- ' menjadi <ul>")
    cek('<a href="https://www.unsrat.ac.id/x.html">https://www.unsrat.ac.id/x.html</a>.' in detail, "alamat https menjadi tautan, titik di luar")
    cek('class="pdf__pembaca"' in detail and lampiran["jalur"].split("/")[1] in detail, "pembaca PDF memuat berkasnya")
    cek("Buka PDF" in detail and " download" in detail, "tombol Buka dan Unduh PDF")
    cek('alt="Tim lomba di panggung"' in detail, "galeri dengan teks alternatif")
    cek('property="og:type" content="article"' in detail and "og:image" in detail, "pratinjau tautan pada pengumuman")
    cek("frame-src 'self' https://storage.googleapis.com" in __import__("html").unescape(detail), "CSP mengizinkan pembaca PDF")
    cek('aria-current="true"' in detail, "menu Pengumuman ditandai sebagai bagian, bukan halaman ini")
    for halaman_id, halaman_alamat in (("organisasi-prestasi", "mahasiswa/organisasi-prestasi"), ("kerja-sama", "profil/kerja-sama"),
                                       ("penelitian", "riset/penelitian"), ("publikasi", "riset/publikasi")):
        cek("Kabar terkait" in baca("s1informatika/%s/index.html" % halaman_alamat), "kabar terkait di %s" % halaman_id)
    cek("Kabar terkait" not in baca("s1informatika/profil/sejarah/index.html"), "tanpa kabar terkait di halaman lain")
    cek(ada("unggahan/55201/" + lampiran["jalur"].split("/")[1]), "PDF lokal diterbitkan di unggahan/")

    rss = ET.fromstring(baca(p + "rss.xml").encode("utf-8"))
    item = rss.findall("./channel/item")
    cek(len(item) == 17, "RSS memuat 17 pengumuman (batas 20), ada %d" % len(item))
    cek(item[0].findtext("link") == "https://prodi.unsrat.ac.id/s1informatika/pengumuman/%s/" % utama, "RSS: tautan lengkap, terbaru dulu")
    cek(item[0].findtext("pubDate").endswith("+0800"), "RSS: waktu WITA")
    cek(ET.fromstring(baca("s1elektro/pengumuman/rss.xml").encode("utf-8")).findall("./channel/item") == [], "RSS kosong sah")
    daftar = baca(p + "index.html")
    cek("Langganan lewat RSS" not in daftar and "rss.xml</a>" not in daftar and 'class="kabar-bawah"' in daftar
        and 'type="application/rss+xml"' in daftar, "daftar pengumuman tanpa tautan RSS; umpan tetap diumumkan di kepala")
    cek('class="kabar-bawah"' not in baca("s1elektro/pengumuman/index.html"), "tanpa arsip tidak ada bagian bawah kosong")

    temuan = cek_integritas.periksa(pub, lokasi.manifes())[0]
    cek(not temuan, "cek integritas bersih: %r" % temuan[:3])

    # --- withdrawing removes the page and its files from the site; one-programme builds keep the others' files
    berkas_utama = [v["jalur"] for v in foto_a["varian"].values()] + [lampiran["jalur"]]
    pengumuman.ganti_status(kode, utama, "ditarik", "penguji")
    bangun.Pembangun(hari_ini=HARI_INI).bangun(kode)
    cek(not ada(p + utama + "/index.html"), "pengumuman ditarik hilang dari situs")
    cek(not any(ada("unggahan/" + j) for j in berkas_utama), "berkas pengumuman ditarik tidak lagi diterbitkan")
    cek(all(os.path.isfile(os.path.join(lokasi.unggahan(), *j.split("/"))) for j in berkas_utama),
        "berkas asli tetap disimpan (tidak dihapus permanen)")
    cek(any(x["id"] == utama for x in pengumuman.baca(kode)["butir"]), "pengumuman ditarik tetap ada di data")
    pengumuman.ganti_status(kode, utama, "terbit", "penguji")
    elektro = media.simpan_foto("20201", jpeg(), "Foto elektro")
    pengumuman.tambah("20201", {"judul": "Kabar elektro", "ringkasan": "R", "tanggal": "2026-10-01", "kategori": "kegiatan",
                                "foto": [elektro]}, "penguji", "terbit")
    bangun.Pembangun(hari_ini=HARI_INI).bangun()
    bangun.Pembangun(hari_ini=HARI_INI).bangun(kode)
    cek(ada("unggahan/" + elektro["varian"]["800"]["jalur"]), "bangun satu prodi tidak menghapus berkas prodi lain")
    cek(ada(p + utama + "/index.html"), "pengumuman yang diterbitkan lagi kembali tampil")

    # --- production: sitemap holds every page, also the announcements; link previews carry the address. Sample content
    # ([CONTOH], isi_halaman.py) is never published there, whoever put it in.
    contoh = t("[CONTOH] Kuliah umum", "2026-10-20", "kegiatan")
    b_produksi = bangun.Pembangun(produksi=True, hari_ini=HARI_INI, alamat="https://prodi.unsrat.ac.id")
    b_produksi.bangun()
    with io.open(os.path.join(pub, "sitemap.xml"), encoding="utf-8") as f:
        peta = f.read()
    cek(not ada(p + contoh + "/index.html") and "[CONTOH]" not in peta and "[CONTOH]" not in baca("s1informatika/index.html")
        and any(contoh in x and "tidak diterbitkan di produksi" in x for x in b_produksi.peringatan),
        "pengumuman contoh tidak terbit di produksi: %r" % b_produksi.peringatan[:4])
    halaman = sum(1 for _f, _d, n in os.walk(pub) for x in n if x == "index.html")
    cek(peta.count("<loc>") == halaman, "sitemap = semua halaman (%d), ada %d" % (halaman, peta.count("<loc>")))
    cek("<loc>https://prodi.unsrat.ac.id/s1informatika/pengumuman/%s/</loc>" % utama in peta, "sitemap memuat pengumuman")
    cek('property="og:url" content="https://prodi.unsrat.ac.id/s1informatika/pengumuman/%s/"' % utama
        in baca(p + utama + "/index.html"), "og:url produksi")
    jumlah, temuan = periksa_situs(pub, "pengumuman-produksi")
    gagal.extend(temuan)
    bangun.Pembangun(produksi=True, hari_ini=HARI_INI).bangun(kode)
    cek(os.path.isfile(os.path.join(pub, "sitemap.xml")) and "s1elektro" in io.open(os.path.join(pub, "sitemap.xml"), encoding="utf-8").read(),
        "sitemap setelah bangun satu prodi tetap memuat prodi lain")
    print("pengumuman: %d halaman diperiksa" % jumlah)
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_pengumuman: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
