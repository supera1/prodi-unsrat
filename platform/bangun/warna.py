# -*- coding: utf-8 -*-
"""Colours of a programme site: the palette its admin picked, or the faculty's flag colours by default, always
checked against WCAG 2.x contrast before a page is built with them.

Every site uses two colours and three shades derived from them:

    utama         navigation band and buttons (white text on it), links and headings on white
    utama-gelap   hover/active of utama
    utama-pucat   tinted surfaces (hero, badges) with utama text on them
    aksen         a bar under the navigation band, badges with dark text
    aksen-pucat   light tint of aksen for notices

Contrast rules (SYARAT) are checked for every palette; a palette that fails is never used. The default "fakultas"
palette is computed from warisan/unit.json (bendera.dasar and bendera.tulisan); when the flag colours cannot meet the
rules even after darkening, the UNSRAT palette is used.
"""
from __future__ import print_function

import colorsys
import io
import json
import os
import re

BANGUN = os.path.dirname(os.path.abspath(__file__))
PALET_JSON = os.path.join(os.path.dirname(BANGUN), "data-awal", "palet.json")

PUTIH = "#FFFFFF"
GELAP = "#2D2527"        # unsrat-abu-900, body text
AKSEN_PUCAT = "#FEF3C7"  # unsrat-kuning-pucat
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
BAWAAN = "fakultas"
CADANGAN = "unsrat"

# (description, foreground, background, minimum ratio); names refer to keys of turunan()
SYARAT = (
    ("teks putih di atas warna utama", "putih", "utama", 4.5),
    ("teks putih di atas warna utama (sorot)", "putih", "utama_gelap", 4.5),
    ("teks warna utama di atas warna utama pucat", "utama", "utama_pucat", 4.5),
    ("teks gelap di atas warna aksen", "gelap", "aksen", 4.5),
    ("teks gelap di atas warna aksen pucat", "gelap", "aksen_pucat", 4.5),
    ("garis aksen di atas warna utama", "aksen", "utama", 3.0),
)


def _rgb(hex_):
    return tuple(int(hex_[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(max(0.0, min(1.0, c)) * 255)) for c in rgb)


def luminans(hex_):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in _rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kontras(a, b):
    la, lb = sorted((luminans(a), luminans(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def campur(hex_, dengan, t):
    """`hex_` moved a fraction t (0..1) towards `dengan` in sRGB."""
    return _hex(tuple(a + (b - a) * t for a, b in zip(_rgb(hex_), _rgb(dengan))))


def saturasi(hex_):
    return colorsys.rgb_to_hls(*_rgb(hex_))[2]


def turunan(utama, aksen):
    utama, aksen = utama.upper(), aksen.upper()
    return {"putih": PUTIH, "gelap": GELAP, "utama": utama, "utama_gelap": campur(utama, "#000000", 0.25),
            "utama_pucat": campur(utama, PUTIH, 0.9), "aksen": aksen, "aksen_pucat": campur(aksen, PUTIH, 0.75)}


def periksa(utama, aksen):
    """[(description, ratio, minimum), ...] for every rule the pair fails (empty: usable)."""
    if not (HEX.match(utama or "") and HEX.match(aksen or "")):
        return [("kode warna tidak sah", 0.0, 0.0)]
    w = turunan(utama, aksen)
    gagal = []
    for label, depan, belakang, minimum in SYARAT:
        r = kontras(w[depan], w[belakang])
        if r < minimum:
            gagal.append((label, round(r, 2), minimum))
    return gagal


def gelapkan(hex_, langkah=0.05):
    """Darken towards black just enough for white text on it and for it on its pale tint; None if impossible."""
    t = 0.0
    while t <= 0.9:
        calon = campur(hex_, "#000000", t)
        if kontras(PUTIH, calon) >= 4.5 and kontras(calon, campur(calon, PUTIH, 0.9)) >= 4.5:
            return calon
        t = round(t + langkah, 2)
    return None


def baca_palet(path=PALET_JSON):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)["palet"]


def palet_fakultas(bendera, cadangan):
    """(utama, aksen) from a faculty flag {"dasar": "#..", "tulisan": "#.."}, or None when it cannot pass."""
    if not isinstance(bendera, dict) or not HEX.match(bendera.get("dasar") or "") or not HEX.match(bendera.get("tulisan") or ""):
        return None
    dasar, tulisan = bendera["dasar"].upper(), bendera["tulisan"].upper()
    # a grey or white field carries no colour of its own: the flag's lettering is the faculty's colour then
    calon = tulisan if saturasi(dasar) < 0.2 else dasar
    utama = gelapkan(calon)
    if utama is None:
        return None
    # the accent: the flag's lettering when it is a colour (white or grey lettering is not), else UNSRAT yellow,
    # else its pale tint (a darkened orange or yellow field is too close to full yellow for the accent bar)
    for aksen in (tulisan, cadangan["aksen"], AKSEN_PUCAT):
        if aksen.upper() != calon and saturasi(aksen) >= 0.2 and not periksa(utama, aksen):
            return utama, aksen.upper()
    return None


def warna_prodi(pilihan, bendera, palet=None):
    """The colours a programme site is built with.

    pilihan: situs.json "palet" (None or "fakultas" for the default, else the id of a palette in palet.json).
    Returns turunan() plus "palet" (id actually used) and "keterangan" (why, for the admin)."""
    palet = palet if palet is not None else baca_palet()
    per_id = {p["id"]: p for p in palet}
    cadangan = per_id[CADANGAN]
    pilihan = pilihan or BAWAAN
    if pilihan != BAWAAN and pilihan in per_id and not periksa(per_id[pilihan]["utama"], per_id[pilihan]["aksen"]):
        p = per_id[pilihan]
        hasil = dict(turunan(p["utama"], p["aksen"]), palet=p["id"], keterangan=p["nama"])
        return hasil
    if pilihan == BAWAAN:
        pasangan = palet_fakultas(bendera, cadangan)
        if pasangan:
            return dict(turunan(*pasangan), palet=BAWAAN, keterangan="Warna bendera fakultas")
        keterangan = "Warna bendera fakultas tidak memenuhi kontras; dipakai warna UNSRAT"
    else:
        keterangan = "Palet %r tidak dikenal atau tidak lolos uji kontras; dipakai warna UNSRAT" % pilihan
    return dict(turunan(cadangan["utama"], cadangan["aksen"]), palet=CADANGAN, keterangan=keterangan)


def css(w):
    """The per-site style sheet: custom properties only (no inline styles anywhere, CSP style-src 'self')."""
    baris = ["/* Warna situs prodi: %s. Dibuat oleh platform/bangun/warna.py; jangan diubah tangan. */" % w["keterangan"],
             ":root {"]
    for k in ("utama", "utama_gelap", "utama_pucat", "aksen", "aksen_pucat"):
        baris.append("\t--prodi-%s: %s;" % (k.replace("_", "-"), w[k]))
    baris.append("}")
    return "\n".join(baris) + "\n"
