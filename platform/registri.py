# -*- coding: utf-8 -*-
"""The programmes that have a site on the platform (data/registri.json) and their per-programme settings.

A programme is identified by its PDDIKTI code (K-P1). Its official data lives in warisan/prodi.json (tarik_www.py);
the registry adds what the platform decides: the slug, old slugs (redirected with 301), whether the site is active,
and the link to its lecturers on dosen.unsrat.ac.id.

    python3 platform/registri.py --siapkan    first start: registry from data-awal/slug.csv + empty settings files
"""
from __future__ import print_function

import argparse
import datetime
import os
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)

import lokasi  # noqa: E402
import slug as slug_mod  # noqa: E402

POLA_URL_DOSEN = ("https://dosen.unsrat.ac.id/", "https://www.dosen.unsrat.ac.id/")


class GagalRegistri(ValueError):
    pass


def _hari_ini():
    return datetime.date.today().isoformat()


def baca():
    return lokasi.baca("registri") or {"prodi": []}


URUTAN_JENJANG = ("S1", "S2", "S3", "Profesi", "Sp-1", "Sp-2")
JENJANG_PANJANG = {"S1": "Sarjana", "S2": "Magister", "S3": "Doktor", "Profesi": "Profesi", "Sp-1": "Spesialis",
                   "Sp-2": "Subspesialis"}


def nama_tampil(p):
    """"S1 Teknik Informatika", "Profesi Dokter", "Sp-1 Ilmu Penyakit Mata"."""
    if p["jenjang"] == "Profesi":
        return p["nama"] if "profesi" in p["nama"].lower() else "Profesi " + p["nama"]
    return "%s %s" % (p["jenjang"], p["nama"])


def kunci_urut(p):
    """Sort key for lists of programmes: by level, then name."""
    return (URUTAN_JENJANG.index(p["jenjang"]) if p.get("jenjang") in URUTAN_JENJANG else 9, p.get("nama", ""))


def belum_terdaftar():
    """Programmes in the official data (not gone from www) that have no site yet, by name."""
    terdaftar = {r["kode_pddikti"] for r in baca()["prodi"]}
    return sorted((p for p in warisan_per_kode().values()
                   if p["kode_pddikti"] not in terdaftar and not p.get("hilang_dari_www")),
                  key=kunci_urut)


def periksa_dosen_url(url):
    """A problem with a lecturer link, or None. Only addresses on https://dosen.unsrat.ac.id/ are accepted."""
    url = (url or "").strip()
    if not url:
        return None
    if not (url.startswith(POLA_URL_DOSEN) and len(url) <= 300 and not any(c.isspace() or c in "\"'<>\\" for c in url)):
        return "tautan dosen harus alamat di https://dosen.unsrat.ac.id/"
    return None


def warisan_per_kode():
    return {p["kode_pddikti"]: p for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}


def cari(registri, kode):
    for r in registri["prodi"]:
        if r["kode_pddikti"] == kode:
            return r
    return None


def cari_slug(registri, slug):
    """(entry, is_old_slug) for a slug in use or retired, or (None, False)."""
    for r in registri["prodi"]:
        if r["slug"] == slug:
            return r, False
    for r in registri["prodi"]:
        if slug in r.get("slug_lama", []):
            return r, True
    return None, False


def periksa_slug_baru(registri, kode, slug, jenjang):
    """Problems with giving `slug` to programme `kode`: the slug rules, plus no clash with another programme's
    current or old slug (an old slug keeps redirecting, so it is never handed to someone else)."""
    masalah = slug_mod.periksa_slug(slug, jenjang)
    pemilik, _lama = cari_slug(registri, slug)
    if pemilik is not None and pemilik["kode_pddikti"] != kode:
        masalah.append("%s sudah dipakai prodi %s" % (slug, pemilik["kode_pddikti"]))
    return masalah


def situs_bawaan():
    """Settings of a programme site before its admin changes anything (the template's defaults)."""
    return {"tagline": "", "palet": None, "logo": None, "media_sosial": [], "menu": {}}


def _entri(kode, slug):
    return {"kode_pddikti": kode, "slug": slug, "slug_lama": [], "aktif": True, "dosen_url": "",
            "dibuat": _hari_ini(), "diubah": _hari_ini()}


def siapkan_situs(kode, oleh):
    """Write prodi/<kode>/situs.json with the defaults when the programme has none yet. True when written."""
    berkas = "prodi/%s/situs" % kode
    if lokasi.baca(berkas) is not None:
        return False
    lokasi.tulis(berkas, situs_bawaan(), oleh, "Registri", "situs bawaan")
    return True


def siapkan_dari_csv(oleh, path=None):
    """First start: build the registry from the approved slug list. Needs warisan/prodi.json (tarik_www.py) so
    every code is checked against the official data. Does nothing when a registry exists. Returns the number of
    programmes registered."""
    if lokasi.baca("registri") is not None:
        return 0
    warisan = warisan_per_kode()
    if not warisan:
        raise GagalRegistri("data resmi belum ada: jalankan dulu tarik_www.py --terapkan")
    baris = slug_mod.baca_csv(path or slug_mod.CSV_AWAL)
    masalah = ["%s: %s" % m for m in slug_mod.periksa_daftar(baris)]
    for b in baris:
        p = warisan.get(b["kode_pddikti"])
        if p is None:
            masalah.append("%s: tidak ada di data resmi www" % b["kode_pddikti"])
        elif p["jenjang"] != b["jenjang"]:
            masalah.append("%s: jenjang %s di daftar slug, %s di data resmi" % (b["kode_pddikti"], b["jenjang"], p["jenjang"]))
    if masalah:
        raise GagalRegistri("; ".join(masalah))
    registri = {"prodi": [_entri(b["kode_pddikti"], b["slug_usulan"]) for b in baris]}
    lokasi.tulis("registri", registri, oleh, "Registri", "registri awal dari slug.csv")
    for b in baris:
        siapkan_situs(b["kode_pddikti"], oleh)
    return len(baris)


def daftarkan(kode, slug, oleh):
    """Give a programme from the official data (e.g. new in www) a site with this slug."""
    registri = baca()
    if cari(registri, kode):
        raise GagalRegistri("prodi %s sudah terdaftar" % kode)
    p = warisan_per_kode().get(kode)
    if p is None or p.get("hilang_dari_www"):
        raise GagalRegistri("prodi %s tidak ada di data resmi www" % kode)
    masalah = periksa_slug_baru(registri, kode, slug, p["jenjang"])
    if masalah:
        raise GagalRegistri("; ".join(masalah))
    registri["prodi"].append(_entri(kode, slug))
    lokasi.tulis("registri", registri, oleh, "Registri", "daftarkan %s sebagai %s" % (kode, slug))
    siapkan_situs(kode, oleh)


def ganti_slug(kode, slug_baru, oleh):
    """Change a programme's slug; the old one is kept in slug_lama and redirected."""
    registri = baca()
    r = cari(registri, kode)
    if r is None:
        raise GagalRegistri("prodi %s belum terdaftar" % kode)
    if r["slug"] == slug_baru:
        return
    p = warisan_per_kode().get(kode)
    masalah = periksa_slug_baru(registri, kode, slug_baru, p["jenjang"] if p else None)
    if masalah:
        raise GagalRegistri("; ".join(masalah))
    lama = r["slug"]
    r["slug_lama"] = [s for s in r.get("slug_lama", []) if s != slug_baru] + [lama]
    r["slug"] = slug_baru
    r["diubah"] = _hari_ini()
    lokasi.tulis("registri", registri, oleh, "Registri", "slug %s: %s -> %s" % (kode, lama, slug_baru))


def atur(kode, oleh, aktif=None, dosen_url=None):
    """Turn a site on or off, or set its lecturer link (an address on dosen.unsrat.ac.id, or empty)."""
    registri = baca()
    r = cari(registri, kode)
    if r is None:
        raise GagalRegistri("prodi %s belum terdaftar" % kode)
    if dosen_url is not None:
        dosen_url = dosen_url.strip()
        masalah = periksa_dosen_url(dosen_url)
        if masalah:
            raise GagalRegistri(masalah)
        r["dosen_url"] = dosen_url
    if aktif is not None:
        r["aktif"] = bool(aktif)
    r["diubah"] = _hari_ini()
    lokasi.tulis("registri", registri, oleh, "Registri", "atur %s" % kode)


def atur_banyak(dosen_url, oleh):
    """Set the lecturer links of many programmes at once ({code: link}), as one change in the history."""
    registri = baca()
    masalah = []
    for kode, url in dosen_url.items():
        r = cari(registri, kode)
        if r is None:
            masalah.append("prodi %s belum terdaftar" % kode)
        elif periksa_dosen_url(url):
            masalah.append("%s: %s" % (kode, periksa_dosen_url(url)))
    if masalah:
        raise GagalRegistri("; ".join(masalah))
    for kode, url in dosen_url.items():
        r = cari(registri, kode)
        r["dosen_url"] = url.strip()
        r["diubah"] = _hari_ini()
    lokasi.tulis("registri", registri, oleh, "Registri", "impor tautan dosen (%d prodi)" % len(dosen_url))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Registri prodi")
    ap.add_argument("--siapkan", action="store_true", help="buat registri awal dari data-awal/slug.csv")
    ap.add_argument("--oleh", default="baris-perintah")
    a = ap.parse_args(argv)
    if a.siapkan:
        try:
            n = siapkan_dari_csv(a.oleh)
        except GagalRegistri as e:
            print("Registri TIDAK dibuat: %s" % e)
            return 1
        print("%d prodi didaftarkan." % n if n else "Registri sudah ada; tidak diubah.")
    reg = baca()
    print("Terdaftar: %d prodi, aktif %d." % (len(reg["prodi"]), sum(1 for r in reg["prodi"] if r["aktif"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
