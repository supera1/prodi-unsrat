# -*- coding: utf-8 -*-
"""Online-gambling spam filter, shared by the admin (refuses such text when it is saved) and the integrity
check (finds it on the published pages).

Defacements of .ac.id sites almost always plant gambling text and links ("slot gacor", "togel", ...),
often spelled to slip past filters. Text is normalised before matching:
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


POLA = re.compile(r"(?<![a-z0-9])(%s)(?![a-z0-9])" % "|".join(_pola_istilah(i) for i in sorted(ISTILAH, key=len, reverse=True)))


def normal(teks):
    """Lower-case text with compatibility forms folded, invisible characters removed and accents dropped."""
    teks = unicodedata.normalize("NFKC", teks or "")
    teks = TAK_TERLIHAT.sub("", teks)
    teks = unicodedata.normalize("NFKD", teks)
    teks = "".join(c for c in teks if not unicodedata.combining(c))
    return teks.lower()


def cari(teks):
    """The first gambling term found in the text (as written there), or None."""
    m = POLA.search(normal(teks))
    return m.group(1) if m else None


if __name__ == "__main__":
    import sys
    for baris in sys.argv[1:]:
        print("%r -> %r" % (baris, cari(baris)))
