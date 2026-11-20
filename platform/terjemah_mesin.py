# -*- coding: utf-8 -*-
"""Machine translation for the English editor (Fase 5 langkah 3, K-P37): drafts of the English texts of a page, which
a person checks before they are submitted or published.

A provider (Penyedia) turns Indonesian lines into English ones. DeepL is called from the admin's server with the
standard library only (no new package): POST /v2/translate, the key in the Authorization header, the Free API's host
for a key ending in ":fx". Tiruan is a provider for the tests and for trying the editor without an account; it is
refused in production.

What is sent is the texts of the page, line by line, with their markup turned into XML that the provider keeps:
[text](https://...) becomes <a href="...">text</a> (the link's text is translated, its address never), **bold**
becomes <b>, bare addresses and the fixed terms become <keep> (ignore_tags), so official names come out as the official
data says (glosarium(): the programme's and the faculties' English names, the university's, degrees, accreditation
bodies). Lines, "- " list items and empty lines between paragraphs are put back as they were. A translation that does
not come back whole (its links changed, unknown markup) or that the spam filter refuses is left out and reported.

Use is counted in characters of the Indonesian texts sent (prodi/<kode>/terjemah-pemakaian.json): at most
TERJEMAH_BATAS_HARIAN per programme per day, and TERJEMAH_BATAS_BULANAN for the whole platform per month.

    python3 platform/terjemah_mesin.py pemakaian     this month's use per programme
"""
from __future__ import print_function

import datetime
import json
import os
import re
import sys
import threading
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape, quoteattr

try:
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen
except ImportError:                                    # pragma: no cover - Python 2 is not supported by the admin
    raise

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import lokasi  # noqa: E402
import saringan_spam  # noqa: E402

BATAS_HARIAN = 50000          # characters per programme per day (TERJEMAH_BATAS_HARIAN)
BATAS_BULANAN = 500000        # characters for the whole platform per month (TERJEMAH_BATAS_BULANAN); DeepL Free's quota
PER_PERMINTAAN = 50           # texts per request
UKURAN_PERMINTAAN = 100 * 1024   # bytes per request (DeepL accepts 128 KiB)
WAKTU_TUNGGU = 30             # seconds
POLA_TAUTAN = re.compile(r"\[([^\]\n]{1,200})\]\((https://[^)\s]{1,500})\)|(https://[^\s<>\"'\\]{1,500})")
POLA_TEBAL = re.compile(r"\*\*(\S(?:[^*\n]{0,298}\S)?)\*\*")
POLA_ALAMAT = re.compile(r"https://[^\s<>\"'\\)\]]+")
PESAN_HTTP = {403: "kunci API DeepL ditolak; periksa TERJEMAH_KUNCI di pengaturan server",
              413: "teks terlalu besar untuk sekali kirim",
              429: "DeepL sedang menerima terlalu banyak permintaan; coba lagi beberapa menit lagi",
              456: "kuota karakter akun DeepL sudah habis untuk periode ini",
              500: "DeepL sedang bermasalah; coba lagi nanti", 503: "DeepL sedang tidak tersedia; coba lagi nanti",
              504: "DeepL sedang tidak tersedia; coba lagi nanti"}

_KUNCI = threading.Lock()


class GagalTerjemah(Exception):
    """Machine translation did not happen; the message is for the programme's admin."""


# ------------------------------------------------------------------ providers

class Penyedia(object):
    nama = ""

    def terjemahkan(self, teks):
        """[XML line in Indonesian] -> [XML line in English], in the same order; GagalTerjemah when it fails."""
        raise NotImplementedError


class DeepL(Penyedia):
    nama = "DeepL"

    def __init__(self, kunci, buka=None):
        self.kunci = kunci
        host = "api-free.deepl.com" if kunci.endswith(":fx") else "api.deepl.com"
        self.alamat = "https://%s/v2/translate" % host
        self.buka = buka or urlopen

    def terjemahkan(self, teks):
        hasil = []
        for kelompok in _kelompok(teks):
            data = urlencode([("text", t) for t in kelompok] + [
                ("source_lang", "ID"), ("target_lang", "EN-US"), ("tag_handling", "xml"), ("ignore_tags", "keep"),
                ("preserve_formatting", "1")]).encode("utf-8")
            permintaan = Request(self.alamat, data=data, method="POST", headers={
                "Authorization": "DeepL-Auth-Key %s" % self.kunci, "User-Agent": "prodi-unsrat-admin",
                "Content-Type": "application/x-www-form-urlencoded"})
            try:
                with self.buka(permintaan, timeout=WAKTU_TUNGGU) as r:
                    isi = json.loads(r.read().decode("utf-8"))
            except HTTPError as e:
                raise GagalTerjemah(PESAN_HTTP.get(e.code, "DeepL menjawab dengan galat %d" % e.code))
            except (URLError, OSError, ValueError):
                raise GagalTerjemah("DeepL tidak dapat dihubungi dari server; coba lagi nanti")
            terjemahan = [x.get("text") for x in (isi.get("translations") or []) if isinstance(x, dict)] \
                if isinstance(isi, dict) else []
            if len(terjemahan) != len(kelompok) or not all(isinstance(x, str) for x in terjemahan):
                raise GagalTerjemah("jawaban DeepL tidak lengkap")
            hasil += terjemahan
        return hasil


class Tiruan(Penyedia):
    """A provider without a service, for the tests and for trying the editor: "(EN) " before each line; gagal: the
    message of a failure to simulate."""
    nama = "Tiruan"

    def __init__(self, gagal=None):
        self.gagal = gagal
        self.dikirim = []

    def terjemahkan(self, teks):
        if self.gagal:
            raise GagalTerjemah(self.gagal)
        self.dikirim += list(teks)
        return ["(EN) " + t for t in teks]


def _kelompok(teks):
    kelompok, ukuran = [], 0
    for t in teks:
        n = len(t.encode("utf-8")) + 16
        if kelompok and (len(kelompok) >= PER_PERMINTAAN or ukuran + n > UKURAN_PERMINTAAN):
            yield kelompok
            kelompok, ukuran = [], 0
        kelompok.append(t)
        ukuran += n
    if kelompok:
        yield kelompok


def penyedia_dari_pengaturan(env):
    """The provider the admin's settings name (TERJEMAH_PENYEDIA, TERJEMAH_KUNCI), or None (no machine translation).
    Raises ValueError for a setting that cannot be used."""
    nama = (env.get("TERJEMAH_PENYEDIA") or "").strip().lower()
    if not nama:
        return None
    if nama == "deepl":
        kunci = (env.get("TERJEMAH_KUNCI") or "").strip()
        if not kunci:
            raise ValueError("TERJEMAH_PENYEDIA=deepl memerlukan TERJEMAH_KUNCI (kunci API DeepL)")
        return DeepL(kunci)
    if nama == "tiruan":
        if env.get("PRODI_MODE") == "produksi":
            raise ValueError("TERJEMAH_PENYEDIA=tiruan hanya untuk uji, tidak di produksi")
        return Tiruan()
    raise ValueError("TERJEMAH_PENYEDIA tidak dikenal: %s (pilihan: deepl)" % nama)


def batas_dari_pengaturan(env):
    """(characters per programme per day, characters for the platform per month)."""
    hasil = []
    for nama, bawaan in (("TERJEMAH_BATAS_HARIAN", BATAS_HARIAN), ("TERJEMAH_BATAS_BULANAN", BATAS_BULANAN)):
        teks = (env.get(nama) or "").strip()
        try:
            hasil.append(int(teks) if teks else bawaan)
        except ValueError:
            raise ValueError("%s harus angka" % nama)
        if hasil[-1] < 0:
            raise ValueError("%s tidak boleh negatif" % nama)
    return tuple(hasil)


# ------------------------------------------------------------------ fixed terms

def glosarium(p, unit_semua, universitas=None):
    """[(Indonesian term, English term)] that machine translation must give exactly: the programme's name, every
    faculty's, the university's (official data), and terms kept as written (degree, accreditation body, UNSRAT)."""
    pasangan = []
    if p.get("nama") and p.get("nama_en"):
        pasangan.append((p["nama"], p["nama_en"]))
    for u in unit_semua:
        if isinstance(u, dict) and u.get("nama") and u.get("nama_en"):
            pasangan.append((u["nama"], u["nama_en"]))
    nama_univ = ((universitas or {}).get("identitas") or {}).get("nama") or {}
    pasangan.append((nama_univ.get("id") or "Universitas Sam Ratulangi", nama_univ.get("en") or "Sam Ratulangi University"))
    for tetap in (p.get("gelar"), p.get("lembaga_akreditasi"), "UNSRAT"):
        if tetap:
            pasangan.append((tetap, tetap))
    hasil, ada = [], set()
    for id_, en in pasangan:
        if id_.strip() and id_.lower() not in ada:
            ada.add(id_.lower())
            hasil.append((id_.strip(), en.strip()))
    return sorted(hasil, key=lambda x: -len(x[0]))          # the longest first: "Fakultas Teknik" before "Teknik"


def _pola_glosarium(glos):
    if not glos:
        return None
    return re.compile(r"(?<![\w.])(%s)(?![\w])" % "|".join(re.escape(a) for a, _b in glos), re.I)


# ------------------------------------------------------------------ markup <-> XML

def _teks_xml(teks, pola, glos):
    """Plain text (no links) as XML: escaped, bold as <b>, fixed terms as <keep>English</keep>."""
    peta = {a.lower(): b for a, b in glos}

    def istilah(bagian):
        if pola is None:
            return xml_escape(bagian)
        hasil, awal = [], 0
        for m in pola.finditer(bagian):
            hasil.append(xml_escape(bagian[awal:m.start()]))
            hasil.append("<keep>%s</keep>" % xml_escape(peta[m.group(1).lower()]))
            awal = m.end()
        hasil.append(xml_escape(bagian[awal:]))
        return "".join(hasil)
    hasil, awal = [], 0
    for m in POLA_TEBAL.finditer(teks):
        hasil.append(istilah(teks[awal:m.start()]))
        hasil.append("<b>%s</b>" % istilah(m.group(1)))
        awal = m.end()
    hasil.append(istilah(teks[awal:]))
    return "".join(hasil)


def ke_xml(baris, glos=()):
    """One line of a text (markup of isi_halaman: links, bold) as the XML a provider keeps."""
    pola = _pola_glosarium(glos)
    hasil, awal = [], 0
    for m in POLA_TAUTAN.finditer(baris):
        hasil.append(_teks_xml(baris[awal:m.start()], pola, glos))
        if m.group(1) is not None:
            hasil.append("<a href=%s>%s</a>" % (quoteattr(m.group(2)), _teks_xml(m.group(1), pola, glos)))
            awal = m.end()
        else:
            alamat = m.group(3).rstrip(".,;:!?)")
            hasil.append("<keep>%s</keep>" % xml_escape(alamat))
            awal = m.start() + len(alamat)
    hasil.append(_teks_xml(baris[awal:], pola, glos))
    return "".join(hasil)


def dari_xml(xml):
    """A translated XML line back to the markup of isi_halaman; ValueError when it holds anything else."""
    try:
        akar = ET.fromstring("<r>%s</r>" % xml)
    except ET.ParseError:
        raise ValueError("terjemahan tidak utuh")

    def isi(el, dalam_tautan=False):
        hasil = [el.text or ""]
        for anak in el:
            if anak.tag == "keep" and not len(anak):
                hasil.append(anak.text or "")
            elif anak.tag == "b":
                hasil.append("**%s**" % isi(anak, dalam_tautan).strip())
            elif anak.tag == "a" and not dalam_tautan and (anak.get("href") or "").startswith("https://"):
                hasil.append("[%s](%s)" % (isi(anak, True).strip(), anak.get("href")))
            else:
                raise ValueError("terjemahan memuat markah yang tidak dikenal")
            hasil.append(anak.tail or "")
        return "".join(hasil)
    return isi(akar)


def _baris(teks):
    """[(prefix, line)] of a text: "- " items keep their prefix; an empty line is ("", None)."""
    hasil = []
    for b in teks.replace("\r\n", "\n").split("\n"):
        s = b.strip()
        if not s:
            hasil.append(("", None))
        elif s.startswith("- "):
            hasil.append(("- ", s[2:].strip()))
        else:
            hasil.append(("", s))
    return hasil


def terjemahkan(penyedia, teks, glos=()):
    """Translate texts: {Indonesian text: English text or None (it did not come back whole, or the spam filter refused
    it)}. Raises GagalTerjemah when the provider fails (nothing is translated then)."""
    satuan, rencana = [], {}
    for t in teks:
        susunan = _baris(t)
        rencana[t] = susunan
        for _awalan, b in susunan:
            if b is not None:
                satuan.append(ke_xml(b, glos))
    keluar = penyedia.terjemahkan(satuan) if satuan else []
    if len(keluar) != len(satuan):
        raise GagalTerjemah("jawaban penyedia tidak lengkap")
    hasil, i = {}, 0
    for t, susunan in rencana.items():
        baris, utuh = [], True
        for awalan, b in susunan:
            if b is None:
                baris.append("")
                continue
            try:
                baris.append(awalan + dari_xml(keluar[i]).strip())
            except ValueError:
                utuh = False
            i += 1
        en = "\n".join(baris).strip()
        if not utuh or not en or sorted(POLA_ALAMAT.findall(t)) != sorted(POLA_ALAMAT.findall(en)) \
                or saringan_spam.cari(en):
            hasil[t] = None
        else:
            hasil[t] = en
    return hasil


# ------------------------------------------------------------------ use

def berkas_pemakaian(kode):
    return "prodi/%s/terjemah-pemakaian" % kode


def pemakaian(kode):
    data = lokasi.baca(berkas_pemakaian(kode)) or {}
    return {"hari": dict(data.get("hari") or {}), "bulan": dict(data.get("bulan") or {})}


def hari_ini():
    return datetime.date.today().isoformat()


def pakai_bulan_ini(kode_semua, hari=None):
    """Characters translated this month by every programme."""
    bulan = (hari or hari_ini())[:7]
    return sum(int(pemakaian(k)["bulan"].get(bulan, 0)) for k in kode_semua)


def periksa_batas(kode, n, kode_semua, batas, hari=None):
    """Refuse a translation of n characters beyond the limits (GagalTerjemah)."""
    hari = hari or hari_ini()
    harian, bulanan = batas
    pakai = pemakaian(kode)
    hari_ini_ = int(pakai["hari"].get(hari, 0))
    if hari_ini_ + n > harian:
        raise GagalTerjemah("batas terjemahan mesin prodi ini hari ini tercapai (%d dari %d karakter; halaman ini perlu %d)."
                            " Coba lagi besok, atau terjemahkan sebagian sendiri" % (hari_ini_, harian, n))
    bulan_ini = pakai_bulan_ini(kode_semua, hari)
    if bulan_ini + n > bulanan:
        raise GagalTerjemah("batas terjemahan mesin semua prodi bulan ini tercapai (%d dari %d karakter; halaman ini perlu "
                            "%d). Hubungi superadmin" % (bulan_ini, bulanan, n))


def catat_pemakaian(kode, n, hari=None):
    """Count n characters for a programme (today and this month); only the last 31 days are kept per day."""
    hari = hari or hari_ini()
    with _KUNCI:
        pakai = pemakaian(kode)
        pakai["hari"][hari] = int(pakai["hari"].get(hari, 0)) + n
        pakai["bulan"][hari[:7]] = int(pakai["bulan"].get(hari[:7], 0)) + n
        pakai["hari"] = dict(sorted(pakai["hari"].items())[-31:])
        lokasi.tulis_json(lokasi.path_data(berkas_pemakaian(kode)), pakai)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] != ["pemakaian"]:
        print(__doc__)
        return 2
    import registri
    bulan = hari_ini()[:7]
    total = 0
    for r in registri.baca()["prodi"]:
        n = int(pemakaian(r["kode_pddikti"])["bulan"].get(bulan, 0))
        if n:
            print("%-8s %-30s %9d" % (r["kode_pddikti"], r["slug"], n))
            total += n
    print("bulan %s: %d karakter" % (bulan, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
