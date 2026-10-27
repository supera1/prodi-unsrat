# -*- coding: utf-8 -*-
"""Spam filter, shared by the admin (refuses such text when it is saved) and the integrity check (finds it on the
published pages).

Defacements of .ac.id sites almost always plant gambling text and links ("slot gacor", "togel", ...); the other
spam planted there sells illegal online loans ("pinjol"), diplomas and drugs. Gambling terms are refused outright (as
in www); for the others only the selling language is listed, never the words a university writes about the topic
itself ("pinjaman online ilegal" in a research title, "ijazah palsu" in a warning, "sildenafil" in a pharmacy study).
Text is often spelled to slip past filters, and is normalised before matching:
- Unicode compatibility forms (fullwidth or mathematical letters) become plain letters;
- invisible characters (zero-width space, soft hyphen, ...) are removed;
- accents are dropped;
- digits and signs used as letters (s1ot, g4cor, $lot) are read as letters;
- in longer words a single dot, dash, underscore or asterisk between letters is ignored (g.a.c.o.r).
"""
from __future__ import print_function

import re
import unicodedata

# characters that render as nothing; spammers put them inside words
TAK_TERLIHAT = re.compile("[\u00ad\u034f\u061c\u115f\u1160\u17b4\u17b5\u180b-\u180f\u200b-\u200f\u202a-\u202e"
                          "\u2060-\u206f\u3164\ufe00-\ufe0f\ufeff\uffa0]")

# a letter and the digits or signs that are used in its place
HURUF = {"a": "a4@", "b": "b8", "e": "e3", "g": "g9", "i": "i1!|", "l": "l1|!", "o": "o0", "s": "s5$", "t": "t7", "z": "z2"}

# phrases that show up in gambling spam and practically never in a university's own text
ISTILAH = [
    "judi", "togel", "gacor", "maxwin", "sbobet", "casino", "kasino", "slot online", "slot gacor", "situs slot",
    "slot88", "slot 88", "slot777", "slot 777", "slot demo", "slot thailand", "server thailand",
    "agen slot", "daftar slot", "login slot", "link slot", "rtp live", "rtp slot", "bocoran rtp", "pola gacor",
    "scatter hitam", "toto macau", "toto togel", "situs toto", "bandar togel", "bandar bola", "bandar judi",
    "agen togel", "agen bola", "prediksi togel", "keluaran hk", "keluaran sgp", "live draw sgp", "live draw hk",
    "deposit pulsa", "depo pulsa", "bonus new member", "freebet", "free bet", "spin gratis", "akun pro", "mahjong ways",
    "pragmatic play", "kakek zeus", "zeus slot", "olympus 1000", "poker online", "dominoqq", "domino qq", "pkv games",
    "sabung ayam online",
]

# selling language of illegal online loans (prodi.unsrat.ac.id, pre-production audit 27 October 2026)
ISTILAH_PINJOL = [
    "dana cepat cair", "pinjaman cepat cair", "pinjaman online cepat cair", "pinjaman online langsung cair",
    "pinjol cepat cair", "pinjol langsung cair", "pinjol mudah cair", "pinjol tanpa jaminan", "pinjol tanpa ktp",
    "pinjaman tanpa ktp", "pinjol terpercaya", "pinjol terbaik", "pinjol bunga rendah", "tanpa bi checking",
    "tanpa bi check", "bebas bi checking", "cair dalam 5 menit", "cair 5 menit",
]
# diplomas and drugs for sale, the other spam planted on .ac.id sites
ISTILAH_LAIN = [
    "jual ijazah asli", "beli ijazah asli", "jasa ijazah asli", "jasa pembuatan ijazah asli", "ijazah asli tanpa kuliah",
    "jual obat aborsi", "obat aborsi ampuh", "jual obat penggugur", "obat penggugur kandungan ampuh", "jual cytotec",
    "cytotec asli", "jual viagra", "viagra asli", "jual cialis", "cialis asli", "jual obat kuat", "obat kuat asli",
]
JENIS = [("judi", ISTILAH), ("pinjol", ISTILAH_PINJOL), ("terlarang", ISTILAH_LAIN)]


def _pola_kata(kata):
    """Regex for one word: each letter may be written with a look-alike, and in words of five or more
    letters a single dot, dash, underscore or asterisk may stand between two letters (not a space, so
    ordinary words next to each other are not read as one: "ideas to gel" is not "togel")."""
    pemisah = r"[._\-*]?" if len(kata) >= 5 else ""
    bagian = []
    for c in kata:
        kelas = HURUF.get(c, c)
        bagian.append("[%s]" % re.escape(kelas) if len(kelas) > 1 else re.escape(c))
    return pemisah.join(bagian)


def _pola_istilah(istilah):
    return r"[\s._\-]*".join(_pola_kata(k) for k in istilah.split())


POLA = re.compile(r"(?<![a-z0-9])(%s)(?![a-z0-9])" % "|".join(
    _pola_istilah(i) for i in sorted(ISTILAH + ISTILAH_PINJOL + ISTILAH_LAIN, key=len, reverse=True)))
POLA_JENIS = [(nama, re.compile(r"^(%s)$" % "|".join(_pola_istilah(i) for i in daftar))) for nama, daftar in JENIS]


def normal(teks):
    """Lower-case text with compatibility forms folded, invisible characters removed and accents dropped."""
    teks = unicodedata.normalize("NFKC", teks or "")
    teks = TAK_TERLIHAT.sub("", teks)
    teks = unicodedata.normalize("NFKD", teks)
    teks = "".join(c for c in teks if not unicodedata.combining(c))
    return teks.lower()


def cari(teks):
    """The first spam term found in the text (as written there), or None."""
    m = POLA.search(normal(teks))
    return m.group(1) if m else None


def jenis(istilah):
    """What a term found by cari() is: "judi", "pinjol" or "terlarang" (diplomas for sale, illegal drugs)."""
    for nama, pola in POLA_JENIS:
        if pola.match(normal(istilah or "")):
            return nama
    return "terlarang"


if __name__ == "__main__":
    import sys
    for baris in sys.argv[1:]:
        print("%r -> %r (%s)" % (baris, cari(baris), jenis(cari(baris)) if cari(baris) else "-"))
