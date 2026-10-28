# -*- coding: utf-8 -*-
"""Integrity check of the published site: finds defacement, planted files and gambling spam.

Compares a folder a web server serves (by default site/publik; on the server, its document root) with
site/manifes-publik.json, written by site/mockup/_rakit-publik.py at the last build, and reads every text file:
- BERUBAH  a published file whose content differs from the build (a defaced page, a swapped script or picture);
- ASING    a file the build did not make (a planted page, a web shell .php, an .htaccess redirect);
- HILANG   a published file that is gone;
- SPAM     gambling text (saringan_spam.py, look-alike spellings included) in a page, script, style or data file;
- SKRIP    a page without the Content-Security-Policy, an inline script, a <script>/<iframe> from a host outside
           the allow-list, an embed (<iframe> of an embed service) without a sandbox or with top navigation, or a
           meta refresh (a redirect to another site).

    python site/pemantau/cek_integritas.py [--folder <docroot>] [--manifes <manifes-publik.json>]

Exit status 1 when anything is found, so it can run from cron and raise an alarm (production: every few minutes,
plus right after every deploy).
"""
from __future__ import print_function

import argparse
import hashlib
import io
import json
import os
import re
import sys

PEMANTAU = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(PEMANTAU)
sys.path.insert(0, PEMANTAU)
sys.path.insert(0, SITE)
import saringan_spam  # noqa: E402
import sematan  # noqa: E402

# hosts the pages may load scripts or frames from: the uploads bucket and the embed services of the programmes' extra
# pages (platform/sematan.py, K-P35), as the CSP of platform/bangun/bangun.py
HOST_BOLEH = {"storage.googleapis.com"} | set(sematan.HOST)
TEKS = (".html", ".htm", ".js", ".css", ".json", ".svg", ".txt", ".xml", ".ics")
SKRIP_LUAR = re.compile(r'<(script|iframe)\b[^>]*\bsrc="(https?:)?//([^/"]+)', re.I)
IFRAME_SEMATAN = re.compile(r'<iframe\b[^>]*\bsrc="https://(%s)/[^>]*>' % "|".join(re.escape(h) for h in sematan.HOST),
                            re.I)
SKRIP_INLINE = re.compile(r"<script\b(?![^>]*\bsrc=)(?![^>]*application/(ld\+)?json)[^>]*>\s*\S", re.I)
REFRESH = re.compile(r'<meta[^>]+http-equiv="?refresh', re.I)


def sha256(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def periksa_teks(rel, teks):
    temuan = []
    istilah = saringan_spam.cari(teks)
    if istilah:
        temuan.append(("SPAM", rel, "memuat “%s”" % istilah))
    if rel.endswith((".html", ".htm")):
        if 'http-equiv="Content-Security-Policy"' not in teks:
            temuan.append(("SKRIP", rel, "halaman tanpa Content-Security-Policy"))
        if SKRIP_INLINE.search(teks):
            temuan.append(("SKRIP", rel, "skrip inline"))
        for m in SKRIP_LUAR.finditer(teks):
            if m.group(3).lower() not in HOST_BOLEH:
                temuan.append(("SKRIP", rel, "<%s> dari host lain: %s" % (m.group(1).lower(), m.group(3))))
        for m in IFRAME_SEMATAN.finditer(teks):
            if not re.search(r'\ssandbox="[^"]*"', m.group(0)) or "allow-top-navigation" in m.group(0):
                temuan.append(("SKRIP", rel, "sematan <iframe> dari %s tanpa sandbox" % m.group(1)))
        if REFRESH.search(teks):
            temuan.append(("SKRIP", rel, "meta refresh (pengalihan)"))
    return temuan


def periksa(folder, manifes):
    with io.open(manifes, encoding="utf-8") as f:
        harapan = json.load(f)["berkas"]
    temuan, ada = [], set()
    for akar, _d, berkas in os.walk(folder):
        for b in berkas:
            path = os.path.join(akar, b)
            rel = os.path.relpath(path, folder).replace(os.sep, "/")
            ada.add(rel)
            try:
                if rel not in harapan:
                    temuan.append(("ASING", rel, "tidak dibuat oleh proses bangun"))
                elif sha256(path) != harapan[rel]:
                    temuan.append(("BERUBAH", rel, "isinya berbeda dari hasil bangun"))
                if rel.lower().endswith(TEKS) or rel not in harapan:
                    with io.open(path, "rb") as f:
                        teks = f.read(5 * 1024 * 1024).decode("utf-8", "replace")
                    temuan.extend(periksa_teks(rel, teks))
            except OSError as exc:
                # e.g. an antivirus blocking a planted web shell: report it, keep checking the rest
                temuan.append(("TERKUNCI", rel, "tidak dapat dibaca (%s)" % exc.strerror))
    temuan.extend(("HILANG", rel, "tidak ada di server") for rel in sorted(set(harapan) - ada))
    return temuan, len(ada)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--folder", default=os.path.join(SITE, "publik"), help="folder yang dilayani web server")
    p.add_argument("--manifes", default=os.path.join(SITE, "manifes-publik.json"))
    a = p.parse_args()
    temuan, jumlah = periksa(a.folder, a.manifes)
    for jenis, rel, ket in temuan[:200]:
        print("%-8s %s: %s" % (jenis, rel, ket))
    print("%d berkas diperiksa, %d temuan" % (jumlah, len(temuan)))
    sys.exit(1 if temuan else 0)


if __name__ == "__main__":
    main()
