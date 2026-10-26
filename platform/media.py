# -*- coding: utf-8 -*-
"""Uploaded photos and PDFs of programme content (announcements and news), checked before anything is stored.

Photos: JPEG or PNG only (admin/gambar_aman.py opens them with those two decoders only), at most MAKS_FOTO bytes and
MAKS_PIKSEL pixels, at least LEBAR_MIN pixels wide. Every photo is decoded and re-encoded as JPEG in the widths of
LEBAR, which drops EXIF (GPS position of a phone photo), comments and anything hidden after the image data.

PDFs: at most MAKS_PDF bytes, a real PDF with pages, not password-protected, without active content (scripts, launch
actions, forms that submit, embedded files, rich media, XFA) and without gambling text in its first pages. The
active-content check is adapted from the www admin (site/admin/app.py periksa_pdf / konten_aktif_pdf, commit 37b5e6d).

Programme logos (langkah 6): SVG cleaned by admin/svg_aman.py (from www) and kept as it is, or JPEG/PNG re-encoded as
PNG (transparency kept) in the heights of TINGGI_LOGO; the width follows the logo (at most 4 times its height).

Hero backgrounds (langkah 3c, K-P15): JPEG or PNG, at least HERO_MIN pixels, cropped at upload to 3:1 for wide
screens (2400 and 1600 px) and 4:3 for phones (1200 x 900), around the chosen focus (FOKUS).

Storage (K-P11), chosen with PRODI_PENYIMPANAN:
    lokal (default)  files under PRODI_UNGGAHAN/<kode>/; the builder publishes them under publik/unggahan/<kode>/
    gcs              Google Cloud Storage, bucket GCS_BUCKET, folder <GCS_PREFIX>prodi/<kode>/, key file GCS_KUNCI
File names are random and a file is never overwritten, so a published address always shows what was published.
"""
from __future__ import print_function

import datetime
import io
import os
import re
import secrets
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PLATFORM, "admin"))
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import gambar_aman  # noqa: E402
import svg_aman  # noqa: E402
import lokasi  # noqa: E402
import saringan_spam  # noqa: E402

MAKS_FOTO = 10 * 1024 * 1024
MAKS_PIKSEL = 60 * 1000 * 1000
LEBAR_MIN = 600
LEBAR = (1600, 800, 400)
MAKS_PDF = 20 * 1024 * 1024
MAKS_HERO = 15 * 1024 * 1024
HERO_MIN = (2400, 800)
VARIAN_HERO = {"2400": ((2400, 800), 3.0), "1600": ((1600, 533), 3.0), "ponsel": ((1200, 900), 4 / 3.0)}
FOKUS = ("tengah", "kiri", "kanan", "atas", "bawah")
PETUNJUK_HERO = ("Foto latar bagian depan: JPEG atau PNG, paling besar 15 MB, minimal 2400 × 800 piksel (rasio 3:1). "
                 "Foto dipotong otomatis menjadi 3:1 untuk layar lebar dan 4:3 untuk ponsel di sekitar titik fokus "
                 "(tengah, kiri, kanan, atas, atau bawah), lalu diberi lapisan warna prodi agar teks tetap terbaca.")
HALAMAN_DIPERIKSA = 30            # pages whose text is checked for gambling spam
POLA_JALUR = re.compile(r"^[0-9A-Za-z]{3,12}/[0-9]{6}-[0-9a-f]{12}(-[0-9]{2,4})?\.(jpg|png|svg|pdf)$")
MAKS_LOGO = 5 * 1024 * 1024
TINGGI_LOGO = (56, 112, 168)
RASIO_LOGO = (0.5, 4.0)               # width / height

KUNCI_PDF_AKTIF = {"/JS", "/JavaScript", "/Launch", "/EmbeddedFile", "/EmbeddedFiles", "/RichMedia", "/XFA"}
AKSI_PDF_AKTIF = {"/JavaScript", "/Launch", "/ImportData", "/RichMediaExecute", "/SubmitForm"}


# ------------------------------------------------------------------ photos

def olah_foto(data):
    """{width: (jpeg bytes, (w, h))} for the widths in LEBAR (never wider than the original, no two of the same
    size), or ValueError."""
    if not data:
        raise ValueError("Pilih foto.")
    if len(data) > MAKS_FOTO:
        raise ValueError("Foto terlalu besar (maksimal %d MB)." % (MAKS_FOTO // 1024 // 1024))
    im = gambar_aman.buka(data, "Foto harus %s." % gambar_aman.TEKS_FORMAT, MAKS_PIKSEL)
    if im.width < LEBAR_MIN:
        raise ValueError("Foto terlalu kecil (lebar minimal %d piksel)." % LEBAR_MIN)
    from PIL import Image
    if im.mode in ("RGBA", "LA", "P"):
        rgba = im.convert("RGBA")
        latar = Image.new("RGB", rgba.size, (255, 255, 255))
        latar.paste(rgba, mask=rgba.getchannel("A"))
        im = latar
    else:
        im = im.convert("RGB")
    hasil, ukuran_dibuat = {}, set()
    for lebar in LEBAR:
        salin = im if im.width <= lebar else im.resize((lebar, round(im.height * lebar / im.width)), Image.LANCZOS)
        if salin.size in ukuran_dibuat:          # a narrow original: no second copy of the same size
            continue
        ukuran_dibuat.add(salin.size)
        buf = io.BytesIO()
        salin.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
        hasil[lebar] = (buf.getvalue(), salin.size)
    return hasil


def potong(im, rasio, fokus="tengah"):
    """The largest box of the given width/height ratio inside the picture, placed by the focus."""
    lebar, tinggi = im.size
    if lebar / float(tinggi) > rasio:                 # too wide: cut the sides
        w = int(round(tinggi * rasio))
        x = {"kiri": 0, "kanan": lebar - w}.get(fokus, (lebar - w) // 2)
        return im.crop((x, 0, x + w, tinggi))
    h = int(round(lebar / rasio))                     # too tall: cut top and bottom
    y = {"atas": 0, "bawah": tinggi - h}.get(fokus, (tinggi - h) // 2)
    return im.crop((0, y, lebar, y + h))


def olah_hero(data, fokus="tengah"):
    """{key of VARIAN_HERO: (jpeg bytes, (w, h))}, or ValueError with a message for the admin."""
    from PIL import Image
    if fokus not in FOKUS:
        raise ValueError("Titik fokus harus salah satu dari: %s." % ", ".join(FOKUS))
    if not data:
        raise ValueError("Pilih foto latar.")
    if len(data) > MAKS_HERO:
        raise ValueError("Foto latar terlalu besar (maksimal %d MB)." % (MAKS_HERO // 1024 // 1024))
    im = gambar_aman.buka(data, "Foto latar harus %s." % gambar_aman.TEKS_FORMAT, MAKS_PIKSEL).convert("RGB")
    if im.width < HERO_MIN[0] or im.height < HERO_MIN[1]:
        raise ValueError("Foto latar terlalu kecil (%d × %d piksel); minimal %d × %d piksel." % (
            im.width, im.height, HERO_MIN[0], HERO_MIN[1]))
    hasil = {}
    for kunci, (ukuran, rasio) in VARIAN_HERO.items():
        salin = potong(im, rasio, fokus).resize(ukuran, Image.LANCZOS)
        buf = io.BytesIO()
        salin.save(buf, "JPEG", quality=80, optimize=True, progressive=True)
        hasil[kunci] = (buf.getvalue(), salin.size)
    return hasil


# ------------------------------------------------------------------ PDFs

def konten_aktif_pdf(pdf, batas=50000):
    """The first sign of active content found in the PDF's objects (also inside compressed object streams,
    which a byte search cannot see), or None. Page contents are not decoded."""
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject
    tumpukan, dilihat, n = [pdf.trailer], set(), 0
    while tumpukan and n < batas:
        o = tumpukan.pop()
        if isinstance(o, IndirectObject):
            if (o.idnum, o.generation) in dilihat:
                continue
            dilihat.add((o.idnum, o.generation))
            o = o.get_object()
        n += 1
        if isinstance(o, DictionaryObject):
            for k, v in o.items():
                if k in KUNCI_PDF_AKTIF:
                    return k
                if k == "/S" and v in AKSI_PDF_AKTIF:
                    return v
                if k not in ("/Parent", "/P"):
                    tumpukan.append(v)
        elif isinstance(o, ArrayObject):
            tumpukan.extend(o)
    return None


def periksa_pdf(data):
    """Number of pages of a PDF that passed every check, or ValueError with a message for the admin."""
    from pypdf import PdfReader
    if not data:
        raise ValueError("Pilih berkas PDF.")
    if len(data) > MAKS_PDF:
        raise ValueError("Berkas PDF terlalu besar (maksimal %d MB)." % (MAKS_PDF // 1024 // 1024))
    if not data.startswith(b"%PDF-"):
        raise ValueError("Isi berkas bukan PDF yang sah.")
    try:
        pdf = PdfReader(io.BytesIO(data))
        if pdf.is_encrypted:
            raise ValueError("PDF terkunci kata sandi; unggah versi tanpa kata sandi.")
        halaman = len(pdf.pages)
        if halaman < 1:
            raise ValueError("PDF tidak memiliki halaman.")
        aktif = konten_aktif_pdf(pdf)
    except ValueError:
        raise
    except Exception:
        raise ValueError("PDF rusak atau tidak dapat dibaca.")
    # active content has no place in an announcement; names may hide letters as #xx (/J#61vaScript)
    nama = re.sub(rb"#([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), data)
    if aktif or re.search(rb"/(JavaScript|JS|Launch|EmbeddedFiles?|RichMedia|XFA)\b", nama):
        raise ValueError("PDF berisi skrip, formulir aktif, atau berkas sisipan. Ekspor ulang PDF tanpa konten aktif.")
    for i in range(min(halaman, HALAMAN_DIPERIKSA)):
        try:
            teks = pdf.pages[i].extract_text() or ""
        except Exception:
            continue          # a page whose text cannot be read (e.g. a scan) is not a reason to refuse the file
        istilah = saringan_spam.cari(teks)
        if istilah:
            raise ValueError("PDF memuat istilah terlarang (“%s”, halaman %d)." % (istilah, i + 1))
    return halaman


# ------------------------------------------------------------------ storage

def _nama_acak(akhiran):
    return "%s-%s%s" % (datetime.date.today().strftime("%Y%m"), secrets.token_hex(6), akhiran)


class PenyimpananLokal(object):
    """Files under PRODI_UNGGAHAN; records carry "jalur" (relative to that folder)."""
    jenis = "lokal"

    def simpan(self, kode, nama, data, tipe):
        jalur = "%s/%s" % (kode, nama)
        path = os.path.join(lokasi.unggahan(), kode, nama)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "xb") as f:            # "x": never overwrite
            f.write(data)
        return {"jalur": jalur}


class PenyimpananGCS(object):
    """Google Cloud Storage; records carry the public "url"."""
    jenis = "gcs"

    def __init__(self, klien=None):
        self.bucket_nama = os.environ.get("GCS_BUCKET") or ""
        self.awalan = (os.environ.get("GCS_PREFIX") or "").strip("/")
        self.awalan = self.awalan + "/" if self.awalan else ""
        if not self.bucket_nama:
            raise ValueError("GCS_BUCKET belum diisi")
        if klien is None:
            from google.cloud import storage
            klien = storage.Client.from_service_account_json(os.environ["GCS_KUNCI"])
        self.bucket = klien.bucket(self.bucket_nama)

    def simpan(self, kode, nama, data, tipe):
        objek = "%sprodi/%s/%s" % (self.awalan, kode, nama)
        blob = self.bucket.blob(objek)
        if blob.exists():
            raise ValueError("nama berkas sudah dipakai di GCS: %s" % objek)
        blob.cache_control = "public, max-age=31536000, immutable"   # names are never reused
        if tipe == "application/pdf":
            blob.content_disposition = "inline"
        blob.upload_from_string(data, content_type=tipe)
        return {"url": "https://storage.googleapis.com/%s/%s" % (self.bucket_nama, objek)}


def penyimpanan():
    jenis = os.environ.get("PRODI_PENYIMPANAN") or "lokal"
    if jenis == "gcs":
        return PenyimpananGCS()
    if jenis == "lokal":
        return PenyimpananLokal()
    raise ValueError("PRODI_PENYIMPANAN harus lokal atau gcs")


def simpan_foto(kode, data, alt, gudang=None):
    """Check, re-encode and store a photo. Returns its media record:
    {"jenis": "gambar", "alt", "lebar", "tinggi", "varian": {"1600": {"jalur"|"url", "lebar", "tinggi"}, ...}}."""
    alt = (alt or "").strip()
    if not alt:
        raise ValueError("Teks alternatif foto wajib diisi (gambarkan isi foto untuk pembaca layar).")
    varian = olah_foto(data)
    gudang = gudang or penyimpanan()
    dasar = _nama_acak("")
    hasil = {}
    for lebar, (isi, (w, h)) in sorted(varian.items(), reverse=True):
        rekam = gudang.simpan(kode, "%s-%d.jpg" % (dasar, lebar), isi, "image/jpeg")
        rekam.update(lebar=w, tinggi=h)
        hasil[str(lebar)] = rekam
    besar = hasil[str(max(LEBAR))]
    return {"jenis": "gambar", "alt": alt, "lebar": besar["lebar"], "tinggi": besar["tinggi"], "varian": hasil}


def simpan_foto_hero(kode, data, fokus="tengah", gudang=None):
    """Check, crop and store a hero background. Returns {"jenis": "hero", "fokus", "varian": {"2400": {...}, ...}}."""
    varian = olah_hero(data, fokus)
    gudang = gudang or penyimpanan()
    dasar = _nama_acak("")
    hasil = {}
    for kunci, (isi, (w, h)) in varian.items():
        rekam = gudang.simpan(kode, "%s-%d.jpg" % (dasar, w), isi, "image/jpeg")
        rekam.update(lebar=w, tinggi=h)
        hasil[kunci] = rekam
    return {"jenis": "hero", "fokus": fokus, "varian": hasil}


def _adalah_svg(nama_berkas, data):
    return (nama_berkas or "").lower().endswith(".svg") or data.lstrip()[:300].lower().find(b"<svg") >= 0


def simpan_logo(kode, data, nama_berkas="", gudang=None):
    """Check and store a programme logo. Returns {"jenis": "logo", "format": "svg"|"png", "lebar", "tinggi",
    "varian": {"svg": {...}} or {"56": {...}, "112": {...}, "168": {...}}}."""
    if not data:
        raise ValueError("Pilih berkas logo.")
    if len(data) > MAKS_LOGO:
        raise ValueError("Berkas logo terlalu besar (maksimal 5 MB).")
    gudang = gudang or penyimpanan()
    if _adalah_svg(nama_berkas, data):
        try:
            bersih, w, h, _dibuang = svg_aman.bersihkan(data)
        except ValueError:
            raise
        except Exception:
            raise ValueError("SVG rusak atau tidak dapat dibaca.")
        if not w or not h or not RASIO_LOGO[0] <= w / float(h) <= RASIO_LOGO[1]:
            raise ValueError("Bentuk logo tidak sesuai (lebar dibagi tinggi harus 0,5–4).")
        rekam = gudang.simpan(kode, _nama_acak(".svg"), bersih, "image/svg+xml")
        return {"jenis": "logo", "format": "svg", "lebar": int(round(w)), "tinggi": int(round(h)), "varian": {"svg": rekam}}
    from PIL import Image
    im = gambar_aman.buka(data, "Logo harus %s, atau SVG." % gambar_aman.TEKS_FORMAT, MAKS_PIKSEL).convert("RGBA")
    if im.height < max(TINGGI_LOGO):
        raise ValueError("Logo terlalu kecil (tinggi minimal %d piksel; disarankan SVG atau PNG 512 piksel)." % max(TINGGI_LOGO))
    if not RASIO_LOGO[0] <= im.width / float(im.height) <= RASIO_LOGO[1]:
        raise ValueError("Bentuk logo tidak sesuai (lebar dibagi tinggi harus 0,5–4; sekarang %d × %d)." % im.size)
    dasar = _nama_acak("")
    hasil = {}
    for t in TINGGI_LOGO:
        salin = im.resize((max(1, round(im.width * t / im.height)), t), Image.LANCZOS)
        buf = io.BytesIO()
        salin.save(buf, "PNG", optimize=True)
        rekam = gudang.simpan(kode, "%s-%d.png" % (dasar, t), buf.getvalue(), "image/png")
        rekam.update(lebar=salin.width, tinggi=t)
        hasil[str(t)] = rekam
    return {"jenis": "logo", "format": "png", "lebar": im.width, "tinggi": im.height, "varian": hasil}


def simpan_pdf(kode, data, judul, gudang=None):
    """Check and store a PDF. Returns {"jenis": "pdf", "judul", "halaman", "ukuran", "jalur"|"url"}."""
    judul = (judul or "").strip()
    if not judul:
        raise ValueError("Judul PDF wajib diisi.")
    halaman = periksa_pdf(data)
    gudang = gudang or penyimpanan()
    rekam = gudang.simpan(kode, _nama_acak(".pdf"), data, "application/pdf")
    rekam.update(jenis="pdf", judul=judul, halaman=halaman, ukuran=len(data))
    return rekam


def jalur_sah(jalur):
    """True for a local file path the builder may publish (shape made by _nama_acak, nothing else)."""
    return bool(POLA_JALUR.match(jalur or ""))


def url_sah(url):
    # nothing that could end an HTML attribute or a CSS url("...") early
    return isinstance(url, str) and url.startswith("https://storage.googleapis.com/") and not re.search(r"[\s\"'<>\\()]", url)
