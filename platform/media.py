# -*- coding: utf-8 -*-
"""Uploaded photos and PDFs of programme content (announcements and news), checked before anything is stored.

Photos: JPEG or PNG only (admin/gambar_aman.py opens them with those two decoders only), at most MAKS_FOTO bytes and
MAKS_PIKSEL pixels, at least LEBAR_MIN pixels wide. Every photo is decoded and re-encoded as JPEG in the widths of
LEBAR, which drops EXIF (GPS position of a phone photo), comments and anything hidden after the image data.

PDFs: at most MAKS_PDF bytes, a real PDF with pages, not password-protected, without active content (scripts, launch
actions, forms that submit, embedded files, rich media, XFA) and without gambling text in its first pages. The
active-content check is adapted from the www admin (site/admin/app.py periksa_pdf / konten_aktif_pdf, commit 37b5e6d).

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
import lokasi  # noqa: E402
import saringan_spam  # noqa: E402

MAKS_FOTO = 10 * 1024 * 1024
MAKS_PIKSEL = 60 * 1000 * 1000
LEBAR_MIN = 600
LEBAR = (1600, 800, 400)
MAKS_PDF = 20 * 1024 * 1024
HALAMAN_DIPERIKSA = 30            # pages whose text is checked for gambling spam
POLA_JALUR = re.compile(r"^[0-9A-Za-z]{3,12}/[0-9]{6}-[0-9a-f]{12}(-[0-9]{3,4})?\.(jpg|pdf)$")

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
    return isinstance(url, str) and url.startswith("https://storage.googleapis.com/") and not re.search(r"[\s\"'<>]", url)
