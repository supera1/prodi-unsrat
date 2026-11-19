# -*- coding: utf-8 -*-
"""The languages of the programme sites (Fase 5, K-P37): Indonesian, and English at /<slug>/en/.

The site's templates write their fixed text in Indonesian inside _("..."), formatted with `| format(...)` where it
holds values ("Program Studi %s"). _() gives the text itself on an Indonesian page and its English text from the
dictionary platform/template/teks-en.json on an English page; a text missing from the dictionary stops the build of
an English page (KeyError), and uji/uji_inggris.py checks that every _("...") of the templates is in it. The
dictionary also holds the labels and choices of the content templates (isi_halaman.py) and a few texts that come
with the data (the university's utility links, the accreditation ranks), which data_bahasa() translates when it
knows them and leaves as they are otherwise.

    python3 platform/bahasa.py periksa      every text the templates use is in the dictionary
"""
from __future__ import print_function

import io
import json
import os
import re
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(PLATFORM, "template")
KAMUS_JSON = os.path.join(TEMPLATE, "teks-en.json")
BAHASA = ("id", "en")
# _("...") or _('...') in a template: the Indonesian text, without escaped quotes inside
POLA_TEKS = re.compile(r"""\b_\(\s*(?:"([^"\\]*)"|'([^'\\]*)')\s*\)""")
POLA_FORMAT = re.compile(r"%[sd]")

JENJANG_EN = {"S1": "Bachelor", "S2": "Master", "S3": "Doctoral", "Profesi": "Professional", "Sp-1": "Specialist",
              "Sp-2": "Subspecialist"}
BULAN_EN = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
            "November", "December")

_kamus = {}


def kamus(path=KAMUS_JSON):
    """{Indonesian text: English text} of the dictionary (read once)."""
    if path not in _kamus:
        with io.open(path, encoding="utf-8") as f:
            _kamus[path] = json.load(f)["teks"]
    return _kamus[path]


def penerjemah(bahasa, lunak=False):
    """The _() of a page in this language. lunak: a text the dictionary does not know stays as it is (data)."""
    if bahasa == "id":
        return lambda teks: teks
    k = kamus()

    def _(teks):
        if teks in k:
            return k[teks]
        if lunak:
            return teks
        raise KeyError("teks %r belum ada di %s" % (teks, os.path.relpath(KAMUS_JSON, PLATFORM)))
    return _


def jenjang_panjang(jenjang, bahasa):
    import registri
    if bahasa == "en":
        return JENJANG_EN.get(jenjang, jenjang)
    return registri.JENJANG_PANJANG.get(jenjang, jenjang)


def nama_tampil(p, bahasa):
    """The name of a programme as its site shows it: "S1 Teknik Informatika"; in English, from its official English
    name: "Bachelor Program in Informatics Engineering" (an English name that already says it is a professional
    programme stays as it is)."""
    import registri
    if bahasa != "en" or not p.get("nama_en"):
        return registri.nama_tampil(p)
    nama = p["nama_en"].strip()
    if p["jenjang"] == "Profesi" and "profession" in nama.lower():
        return nama
    return "%s Program in %s" % (JENJANG_EN.get(p["jenjang"], p["jenjang"]), nama)


def label_akreditasi(nilai, bahasa):
    import registri
    label = registri.label_akreditasi(nilai)
    return penerjemah(bahasa, lunak=True)(label) if label else ""


def tanggal_en(iso):
    """'2030-08-15' -> 'August 15, 2030' ('' for anything else); the Indonesian form is bangun.tanggal()."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    if not m or not 1 <= int(m.group(2)) <= 12:
        return ""
    return "%s %d, %s" % (BULAN_EN[int(m.group(2)) - 1], int(m.group(3)), m.group(1))


def teks_templat(folder=os.path.join(TEMPLATE, "halaman")):
    """{Indonesian text: [template file, ...]} of every _("...") in the site's templates."""
    hasil = {}
    for nama in sorted(os.listdir(folder)):
        if nama.endswith(".html"):
            with io.open(os.path.join(folder, nama), encoding="utf-8") as f:
                for m in POLA_TEKS.finditer(f.read()):
                    hasil.setdefault(m.group(1) if m.group(1) is not None else m.group(2), []).append(nama)
    return hasil


def periksa(path=KAMUS_JSON):
    """Problems of the dictionary against the templates: texts missing, empty English, placeholders that differ."""
    k = kamus(path)
    masalah = ["%r (%s) belum ada di kamus" % (t, ", ".join(sorted(set(f)))) for t, f in sorted(teks_templat().items())
               if t not in k]
    for t, en in sorted(k.items()):
        if not isinstance(en, str) or not en.strip():
            masalah.append("%r: terjemahan kosong" % t)
        elif sorted(POLA_FORMAT.findall(t)) != sorted(POLA_FORMAT.findall(en)):
            masalah.append("%r: penanda %%s/%%d berbeda dengan %r" % (t, en))
    return masalah


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] != ["periksa"]:
        print(__doc__)
        return 2
    masalah = periksa()
    for m in masalah:
        print("MASALAH", m)
    print("kamus: %d teks, %d dipakai templat, %d masalah" % (len(kamus()), len(teks_templat()), len(masalah)))
    return 1 if masalah else 0


if __name__ == "__main__":
    sys.exit(main())
