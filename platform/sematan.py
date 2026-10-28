# -*- coding: utf-8 -*-
"""Embedded content of a programme's extra pages (K-P35): a Google document, sheet, presentation or form, a file in
Google Drive, a Google calendar or map, or a YouTube video, shown in a frame on the page.

The list of services (LAYANAN) is fixed: changing it is a new decision (K-P), not a setting of the admin. Only an
address is stored, never HTML. An embed code pasted from Google gives its src, and a share link becomes the
service's embed address (normalkan). The frame is made by the site's template, sandboxed without top navigation, so
the embedded page cannot move the visitor away; the site's CSP (CSP_FRAME, frame-src) and the integrity check
(pemantau, HOST) allow these hosts and no other.

    python3 platform/sematan.py <address or embed code>     what an address becomes, or why it is refused
"""
from __future__ import print_function

import html
import re
import sys

try:
    from urllib.parse import parse_qs, parse_qsl, urlencode, urlsplit
except ImportError:                                    # pragma: no cover - Python 2 is not supported by the admin
    raise

# (host, path prefix, the service's name for visitors)
LAYANAN = (
    ("docs.google.com", "/document/", "Google Docs"),
    ("docs.google.com", "/spreadsheets/", "Google Sheets"),
    ("docs.google.com", "/presentation/", "Google Slides"),
    ("docs.google.com", "/forms/", "Google Forms"),
    ("drive.google.com", "/file/", "Google Drive"),
    ("calendar.google.com", "/calendar/embed", "Google Calendar"),
    ("www.google.com", "/maps/embed", "Google Maps"),
    ("www.youtube-nocookie.com", "/embed/", "YouTube"),
)
HOST = sorted({h for h, _p, _n in LAYANAN})
# frame-src sources: whole hosts, except www.google.com, where only the map embed is a frame
CSP_FRAME = " ".join("https://www.google.com/maps/embed" if h == "www.google.com" else "https://" + h for h in HOST)
NAMA_LAYANAN = "Google Docs, Sheets, Slides, Forms, Drive, Calendar, Maps, atau YouTube"
TINGGI = ("Pendek", "Sedang", "Tinggi")
# allow-scripts and allow-same-origin together are safe here: the frame is always another origin than the site
SANDBOX = "allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
MAKS_ALAMAT = 2000

POLA_ID_GOOGLE = re.compile(r"^[A-Za-z0-9_-]{10,200}$")
POLA_ID_YOUTUBE = re.compile(r"^[A-Za-z0-9_-]{11}$")
POLA_IFRAME = re.compile(r"<iframe\b[^>]*?\bsrc\s*=\s*([\"'])(.*?)\1", re.I | re.S)


class _Tolak(Exception):
    pass


def _bagian(path):
    return [p for p in path.split("/") if p]


def _google_docs(path):
    """docs.google.com: a document, sheet or presentation shared with anyone who has the link, or published to the
    web; a form by its public link."""
    p = _bagian(path)
    if len(p) >= 3 and p[0] in ("document", "spreadsheets", "presentation") and p[1] == "d":
        if p[2] == "e":                                   # published to the web: /d/e/<id>/pub...
            if len(p) < 4 or not POLA_ID_GOOGLE.match(p[3]):
                raise _Tolak("alamat Google tidak lengkap")
            akhir = {"document": "pub?embedded=true", "spreadsheets": "pubhtml?widget=true&headers=false",
                     "presentation": "embed"}[p[0]]
            return "https://docs.google.com/%s/d/e/%s/%s" % (p[0], p[3], akhir)
        if not POLA_ID_GOOGLE.match(p[2]):
            raise _Tolak("alamat Google tidak lengkap")
        return "https://docs.google.com/%s/d/%s/%s" % (p[0], p[2], "embed" if p[0] == "presentation" else "preview")
    if len(p) >= 4 and p[0] == "forms" and p[1] == "d" and p[2] == "e" and POLA_ID_GOOGLE.match(p[3]):
        return "https://docs.google.com/forms/d/e/%s/viewform?embedded=true" % p[3]
    if len(p) >= 3 and p[0] == "forms" and p[1] == "d":
        raise _Tolak("ini tautan untuk menyunting formulir; pakai tautan dari tombol Kirim (Send) di Google Forms")
    raise _Tolak("alamat Google Docs tidak dikenali")


def _google_drive(u):
    p = _bagian(u.path)
    if len(p) >= 3 and p[0] == "file" and p[1] == "d" and POLA_ID_GOOGLE.match(p[2]):
        return "https://drive.google.com/file/d/%s/preview" % p[2]
    id_ = parse_qs(u.query).get("id", [""])[0]
    if p == ["open"] and POLA_ID_GOOGLE.match(id_):
        return "https://drive.google.com/file/d/%s/preview" % id_
    if p[:2] == ["drive", "folders"]:
        raise _Tolak("folder Google Drive tidak bisa disematkan; sematkan berkasnya satu per satu, atau pasang sebagai "
                     "tautan biasa")
    raise _Tolak("alamat Google Drive tidak dikenali")


def _youtube(u, host):
    p = _bagian(u.path)
    if host == "youtu.be":
        id_ = p[0] if p else ""
    elif p and p[0] in ("embed", "shorts", "live") and len(p) >= 2:
        id_ = p[1]
    else:
        id_ = parse_qs(u.query).get("v", [""])[0]
    if not POLA_ID_YOUTUBE.match(id_ or ""):
        raise _Tolak("alamat video YouTube tidak dikenali")
    return "https://www.youtube-nocookie.com/embed/%s" % id_


def _kueri(u):
    """The query of an address, re-encoded (what the service needs to show a calendar or a map)."""
    return urlencode(parse_qsl(u.query, keep_blank_values=True), safe="!:,*@/")


def normalkan(teks):
    """(embed address, None) for an address or an embed code of an allowed service, or (None, what is wrong)."""
    t = (teks or "").strip()
    m = POLA_IFRAME.search(t)
    if m:
        t = html.unescape(m.group(2)).strip()
    elif "<" in t:
        return None, "tempel alamatnya, atau kode sematan (embed) yang diawali <iframe"
    if t.startswith("//"):
        t = "https:" + t
    if not t:
        return None, "alamat sematan kosong"
    if len(t) > MAKS_ALAMAT or re.search(r"[\s\"'<>\\]", t):
        return None, "alamat sematan tidak sah"
    try:
        u = urlsplit(t)
        host = (u.hostname or "").lower()
    except ValueError:
        return None, "alamat sematan tidak sah"
    if u.scheme.lower() != "https" or u.username or u.password or u.port not in (None, 443):
        return None, "alamat sematan harus diawali https://"
    try:
        if host == "docs.google.com":
            return _google_docs(u.path), None
        if host == "drive.google.com":
            return _google_drive(u), None
        if host == "calendar.google.com" and u.path == "/calendar/embed" and parse_qs(u.query).get("src"):
            return "https://calendar.google.com/calendar/embed?" + _kueri(u), None
        if host in ("www.google.com", "google.com") and u.path == "/maps/embed" and parse_qs(u.query).get("pb"):
            return "https://www.google.com/maps/embed?" + _kueri(u), None
        if host in ("www.google.com", "google.com", "maps.google.com", "maps.app.goo.gl", "goo.gl"):
            raise _Tolak("untuk peta, pakai Bagikan → Sematkan peta (Embed a map) di Google Maps, lalu tempel kodenya")
        if host == "calendar.google.com":
            raise _Tolak("untuk kalender, pakai alamat dari Setelan kalender → Integrasikan kalender (Embed code)")
        if host in ("www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be", "www.youtube-nocookie.com"):
            return _youtube(u, host), None
        if host == "forms.gle":
            raise _Tolak("tautan pendek forms.gle tidak bisa disematkan; pakai kode sematan dari tombol Kirim (Send) → "
                         "<> di Google Forms")
    except _Tolak as e:
        return None, str(e)
    return None, "hanya dari %s" % NAMA_LAYANAN


def periksa(alamat):
    """What is wrong with a stored embed address (None when it may be shown): it must be exactly what normalkan()
    makes of it, so nothing but an allowed service's embed address ever reaches a page."""
    if not isinstance(alamat, str):
        return "alamat sematan tidak sah"
    hasil, pesan = normalkan(alamat)
    if pesan:
        return pesan
    if hasil != alamat:
        return "alamat sematan belum diubah ke bentuk sematan; simpan ulang formulirnya"
    return None


def layanan(alamat):
    """The service's name of an embed address ("Google Forms")."""
    try:
        u = urlsplit(alamat or "")
    except ValueError:
        return ""
    for h, awal, nama in LAYANAN:
        if u.hostname == h and u.path.startswith(awal):
            return nama
    return ""


def main(argv=None):
    teks = " ".join(argv if argv is not None else sys.argv[1:])
    hasil, pesan = normalkan(teks)
    print(hasil if hasil else "DITOLAK: %s" % pesan)
    return 0 if hasil else 1


if __name__ == "__main__":
    sys.exit(main())
