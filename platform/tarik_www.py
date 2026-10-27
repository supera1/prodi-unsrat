# -*- coding: utf-8 -*-
"""Copy the official programme data from www.unsrat.ac.id into the platform (K-P6: one way, www -> prodi).

Reads prodi.json, unit.json, kalender.json and situs.json from a folder, checks them, compares them with the copy the
platform has (warisan/*) and, when asked, writes the new copy. Nothing is written when any check fails: a broken or
tampered source never reaches the programme sites. The folder is WWW_DATA (lokasi.py; read only) on a developer's
machine; on the server it is an upload of the superadmin prepared by impor_www.py (K-P18), or the starting copy
data-awal/www/ of a new VM.

    python3 platform/tarik_www.py              preview: what would change
    python3 platform/tarik_www.py --terapkan   apply (the previous copy goes to the version history)
    python3 platform/tarik_www.py --terapkan --paksa   apply even when many programmes disappeared at once

Rules (docs/rencana-fase-01.md §5):
- only the fields in FIELD_PRODI / FIELD_UNIT are kept; the rest of www's data is not copied;
- a programme that disappears from www is kept, marked "hilang_dari_www" with the date, for the superadmin to review;
- a programme new in www is copied but has no site until the superadmin registers it with a slug (registri.py);
- gambling text anywhere in the copied data stops the pull (www may have been defaced);
- when more than BATAS_HILANG of the programmes disappear at once the pull stops unless --paksa is given.
"""
from __future__ import print_function

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import lokasi  # noqa: E402
import saringan_spam  # noqa: E402
from slug import AWALAN_JENJANG  # noqa: E402

# Official fields copied from www's prodi.json. Everything here is shown on (or used by) the programme sites.
FIELD_PRODI = ("kode_pddikti", "nama", "nama_en", "jenjang", "gelar", "sks", "unit_kode", "unit", "website", "surel",
               "bidang_kerja", "bidang_kerja_en", "cpl", "akreditasi", "lembaga_akreditasi", "berlaku_hingga",
               "internasional", "slug", "slug_en")
FIELD_CPL = ("kode", "isi", "isi_en", "kurikulum")
FIELD_UNIT = ("kode", "nama", "nama_en", "jenis", "website", "surel", "bendera")
# From www's situs.json only what the programme sites show about the university (header, footer, contact page).
FIELD_SITUS = ("identitas", "kontak", "media_sosial", "utilitas")
# www's own page address of a programme ("slug") is kept when www gives it, but not required: www's Excel export,
# which the superadmin may upload instead of prodi.json (impor_www.py), does not have it
WAJIB_PRODI = ("kode_pddikti", "nama", "jenjang", "unit_kode", "unit")

# Shown to the superadmin as gaps to fill in www (empty fields are never made up here).
KEKURANGAN = (("cpl", "CPL"), ("akreditasi", "status akreditasi"), ("lembaga_akreditasi", "lembaga akreditasi"),
              ("gelar", "gelar"), ("sks", "jumlah SKS"), ("surel", "surel prodi"), ("bidang_kerja", "bidang kerja lulusan"),
              ("nama_en", "nama bahasa Inggris"))

POLA_KODE = re.compile(r"^[0-9A-Za-z]{3,12}$")
POLA_TANGGAL = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAKS_TEKS = 10000
BATAS_HILANG = 0.10
SUMBER = ("prodi", "unit", "kalender", "situs")


class GagalTarik(Exception):
    """The source failed a check; .masalah lists every problem found."""

    def __init__(self, masalah):
        Exception.__init__(self, "%d masalah pada data www" % len(masalah))
        self.masalah = masalah


# ------------------------------------------------------------------ reading and checking the source

def _teks(nilai, boleh_kosong=True):
    return isinstance(nilai, str) and len(nilai) <= MAKS_TEKS and (boleh_kosong or nilai.strip() != "")


def periksa_prodi(p):
    """Problems with one programme record from www (empty list when it is fine)."""
    if not isinstance(p, dict):
        return ["bukan objek"]
    masalah = []
    for f in WAJIB_PRODI:
        if not _teks(p.get(f), boleh_kosong=False):
            masalah.append("%s kosong atau bukan teks" % f)
    if _teks(p.get("kode_pddikti"), False) and not POLA_KODE.match(p["kode_pddikti"]):
        masalah.append("kode_pddikti tidak sah: %r" % p["kode_pddikti"])
    if p.get("jenjang") not in AWALAN_JENJANG:
        masalah.append("jenjang tidak dikenal: %r" % p.get("jenjang"))
    for f in FIELD_PRODI:
        if f in WAJIB_PRODI or f in ("sks", "cpl"):
            continue
        if f in p and p[f] is not None and not _teks(p[f]):
            masalah.append("%s bukan teks" % f)
    sks = p.get("sks")
    if sks is not None and sks != "" and not (isinstance(sks, int) and not isinstance(sks, bool) and 0 < sks < 400):
        masalah.append("sks tidak sah: %r" % (sks,))
    if p.get("berlaku_hingga") and not POLA_TANGGAL.match(str(p["berlaku_hingga"])):
        masalah.append("berlaku_hingga bukan tanggal: %r" % p["berlaku_hingga"])
    cpl = p.get("cpl", [])
    if not isinstance(cpl, list):
        masalah.append("cpl bukan daftar")
    else:
        for i, c in enumerate(cpl):
            if not isinstance(c, dict) or not _teks(c.get("isi"), False) or not all(
                    c.get(f) is None or _teks(c.get(f)) for f in FIELD_CPL):
                masalah.append("cpl ke-%d tidak sah" % (i + 1))
    return masalah


def _rapikan_prodi(p):
    hasil = {f: p.get(f) for f in FIELD_PRODI if f != "cpl"}
    hasil = {k: ("" if v is None and k != "sks" else v) for k, v in hasil.items()}
    if hasil.get("sks") == "":
        hasil["sks"] = None
    hasil["cpl"] = [{f: c.get(f) or "" for f in FIELD_CPL} for c in (p.get("cpl") or [])]
    return hasil


def _semua_teks(isi, jalur=""):
    """Every string in a JSON value, with where it is: [(path, text), ...]."""
    if isinstance(isi, str):
        yield jalur, isi
    elif isinstance(isi, dict):
        for k, v in isi.items():
            for x in _semua_teks(v, "%s.%s" % (jalur, k) if jalur else str(k)):
                yield x
    elif isinstance(isi, list):
        for i, v in enumerate(isi):
            for x in _semua_teks(v, "%s[%d]" % (jalur, i)):
                yield x


def _baca_json(folder, nama):
    path = os.path.join(folder, nama + ".json")
    with open(path, "rb") as f:
        mentah = f.read()
    return json.loads(mentah.decode("utf-8")), hashlib.sha256(mentah).hexdigest()


def baca_sumber(folder=None, keterangan=None):
    """Read and check www's data. Returns {"prodi": {...}, "unit": {...}, "kalender": {...}, "meta": {...}}
    in the shape the platform stores; raises GagalTarik listing every problem. keterangan: where the data came from, as
    recorded in warisan/meta.json (default: the folder)."""
    folder = folder or lokasi.www_data()
    masalah, mentah, sidik = [], {}, {}
    for nama in SUMBER:
        try:
            mentah[nama], sidik[nama] = _baca_json(folder, nama)
        except (IOError, OSError, ValueError) as e:
            masalah.append("%s.json tidak terbaca: %s" % (nama, e))
    if masalah:
        raise GagalTarik(masalah)

    program = mentah["prodi"].get("program") if isinstance(mentah["prodi"], dict) else None
    if not isinstance(program, list) or not program:
        raise GagalTarik(["prodi.json tidak memuat daftar program"])
    prodi, dilihat = [], set()
    for i, p in enumerate(program):
        label = p.get("kode_pddikti") if isinstance(p, dict) else None
        for m in periksa_prodi(p):
            masalah.append("prodi %s (urutan %d): %s" % (label or "?", i + 1, m))
        if label in dilihat:
            masalah.append("prodi %s: kode PDDIKTI ganda" % label)
        dilihat.add(label)
        if isinstance(p, dict):
            prodi.append(_rapikan_prodi(p))

    daftar_unit = mentah["unit"].get("unit") if isinstance(mentah["unit"], dict) else None
    if not isinstance(daftar_unit, list) or not daftar_unit:
        masalah.append("unit.json tidak memuat daftar unit")
        daftar_unit = []
    unit = []
    for u in daftar_unit:
        if not isinstance(u, dict) or not _teks(u.get("kode"), False) or not _teks(u.get("nama"), False):
            masalah.append("unit tidak sah: %r" % (u.get("kode") if isinstance(u, dict) else u))
            continue
        unit.append({f: u.get(f) for f in FIELD_UNIT if f in u})
    kode_unit = {u["kode"] for u in unit}
    for p in prodi:
        if unit and p.get("unit_kode") not in kode_unit:
            masalah.append("prodi %s: unit_kode %r tidak ada di unit.json" % (p.get("kode_pddikti"), p.get("unit_kode")))

    kalender = mentah["kalender"]
    if not isinstance(kalender, dict) or not isinstance(kalender.get("semester"), list):
        masalah.append("kalender.json tidak memuat daftar semester")

    situs = mentah["situs"] if isinstance(mentah["situs"], dict) else {}
    universitas = {f: situs.get(f) for f in FIELD_SITUS}
    if not isinstance(universitas["identitas"], dict) or not isinstance(universitas["kontak"], dict):
        masalah.append("situs.json tidak memuat identitas dan kontak")
    # utility links: the Indonesian list, and only full addresses (www's relative ones point inside www)
    utilitas = universitas["utilitas"] if isinstance(universitas["utilitas"], dict) else {}
    universitas["utilitas"] = [t for t in (utilitas.get("id") or []) if isinstance(t, dict)
                               and _teks(t.get("label"), False) and str(t.get("href", "")).startswith("https://")]
    universitas["media_sosial"] = [m for m in (universitas["media_sosial"] or []) if isinstance(m, dict)
                                   and _teks(m.get("nama"), False) and str(m.get("url", "")).startswith("https://")]

    hasil = {
        "prodi": {"tampilkan_berlaku_hingga": bool(mentah["prodi"].get("tampilkan_berlaku_hingga")),
                  "program": sorted(prodi, key=lambda p: p["kode_pddikti"])},
        "unit": {"unit": unit},
        "kalender": kalender,
        "situs": universitas,
    }
    for nama in SUMBER:
        for jalur, teks in _semua_teks(hasil[nama]):
            istilah = saringan_spam.cari(teks)
            if istilah:
                masalah.append("teks %s %r di %s.json %s" % (saringan_spam.jenis(istilah), istilah, nama, jalur))
    if masalah:
        raise GagalTarik(masalah)
    hasil["meta"] = {"sumber": keterangan or folder, "sidik": sidik, "jumlah_prodi": len(prodi)}
    return hasil


# ------------------------------------------------------------------ comparing with the platform's copy

def kekurangan(p):
    """Labels of the official fields a programme still lacks (to be filled in www, never here)."""
    return [label for f, label in KEKURANGAN
            if p.get(f) in (None, "", []) or (f == "akreditasi" and p.get(f) == "belum")]   # "belum": www's "not filled in"


def _beda_cpl(lama, baru):
    lama_k = {c["kode"] or c["isi"]: c for c in lama}
    baru_k = {c["kode"] or c["isi"]: c for c in baru}
    hasil = []
    for k in baru_k:
        if k not in lama_k:
            hasil.append("CPL ditambah: %s" % k)
        elif baru_k[k] != lama_k[k]:
            hasil.append("CPL diubah: %s" % k)
    hasil += ["CPL dihapus: %s" % k for k in lama_k if k not in baru_k]
    return hasil


def gabungkan(lama, sumber, hari_ini=None):
    """The new warisan/prodi.json from the old copy and the checked source, plus a report of the differences.

    Returns (baru, laporan) with laporan = {"baru": [kode], "hilang": [kode], "kembali": [kode],
    "berubah": {kode: [description, ...]}}.
    """
    hari_ini = hari_ini or datetime.date.today().isoformat()
    lama_k = {p["kode_pddikti"]: p for p in (lama or {}).get("program", [])}
    sumber_k = {p["kode_pddikti"]: p for p in sumber["program"]}
    laporan = {"baru": [], "hilang": [], "kembali": [], "berubah": {}}
    program = []
    for kode, p in sumber_k.items():
        tua = lama_k.get(kode)
        if tua is None:
            laporan["baru"].append(kode)
        else:
            if tua.get("hilang_dari_www"):
                laporan["kembali"].append(kode)
            beda = ["%s: %r -> %r" % (f, tua.get(f), p.get(f)) for f in FIELD_PRODI
                    if f != "cpl" and tua.get(f) != p.get(f)]
            beda += _beda_cpl(tua.get("cpl", []), p.get("cpl", []))
            if beda:
                laporan["berubah"][kode] = beda
        program.append(dict(p))
    for kode, tua in lama_k.items():
        if kode not in sumber_k:
            tetap = dict(tua)
            if not tetap.get("hilang_dari_www"):
                tetap["hilang_dari_www"] = hari_ini
                laporan["hilang"].append(kode)
            program.append(tetap)
    baru = {"tampilkan_berlaku_hingga": sumber["tampilkan_berlaku_hingga"],
            "program": sorted(program, key=lambda p: p["kode_pddikti"])}
    for k in laporan:
        if isinstance(laporan[k], list):
            laporan[k].sort()
    return baru, laporan


def pratinjau(folder=None, keterangan=None):
    """Check the source and compare it with the platform's copy, without writing anything.

    Returns {"sumber": <baca_sumber result>, "prodi": <new warisan/prodi>, "laporan": {...}}, where laporan also has
    "unit_berubah", "kalender_berubah", "tampilan_berubah", "kekurangan" {kode: [labels]}, "belum_terdaftar" [kode],
    "hilang_terlalu_banyak" (bool) and "pertama" (bool: the platform has no copy yet)."""
    sumber = baca_sumber(folder, keterangan)
    lama = lokasi.baca("warisan/prodi")
    prodi, laporan = gabungkan(lama, sumber["prodi"])
    laporan["pertama"] = lama is None
    laporan["tampilan_berubah"] = bool(lama) and lama.get("tampilkan_berlaku_hingga") != prodi["tampilkan_berlaku_hingga"]
    laporan["unit_berubah"] = lokasi.baca("warisan/unit") != sumber["unit"]
    laporan["kalender_berubah"] = lokasi.baca("warisan/kalender") != sumber["kalender"]
    laporan["universitas_berubah"] = lokasi.baca("warisan/universitas") != sumber["situs"]
    laporan["kekurangan"] = {p["kode_pddikti"]: kekurangan(p) for p in prodi["program"]
                             if kekurangan(p) and not p.get("hilang_dari_www")}
    terdaftar = {r["kode_pddikti"] for r in (lokasi.baca("registri") or {}).get("prodi", [])}
    laporan["belum_terdaftar"] = sorted(p["kode_pddikti"] for p in prodi["program"]
                                        if p["kode_pddikti"] not in terdaftar and not p.get("hilang_dari_www"))
    aktif_lama = [p for p in (lama or {}).get("program", []) if not p.get("hilang_dari_www")]
    laporan["hilang_terlalu_banyak"] = bool(aktif_lama) and len(laporan["hilang"]) > BATAS_HILANG * len(aktif_lama)
    # fields changed by a programme itself that www now changes too: the programme's value stays (data_prodi.py)
    import data_prodi
    laporan["bentrok"] = data_prodi.bentrok_jika_ditarik(prodi)
    return {"sumber": sumber, "prodi": prodi, "laporan": laporan}


def ada_perubahan(laporan):
    return bool(laporan["pertama"] or laporan["baru"] or laporan["hilang"] or laporan["kembali"] or laporan["berubah"]
                or laporan["unit_berubah"] or laporan["kalender_berubah"] or laporan["universitas_berubah"]
                or laporan["tampilan_berubah"])


def terapkan(oleh, folder=None, paksa=False, keterangan=None):
    """Pull and write the new copy. Returns the report; raises GagalTarik when the source fails a check or when too
    many programmes disappeared at once (unless paksa)."""
    hasil = pratinjau(folder, keterangan)
    laporan = hasil["laporan"]
    if laporan["hilang_terlalu_banyak"] and not paksa:
        raise GagalTarik(["%d prodi hilang sekaligus dari data www (batas %d%%); periksa sumbernya, atau terapkan "
                          "dengan --paksa bila memang benar" % (len(laporan["hilang"]), int(BATAS_HILANG * 100))])
    if not ada_perubahan(laporan):
        return laporan
    bagian = "Tarik data www"
    lokasi.tulis("warisan/prodi", hasil["prodi"], oleh, bagian, "tarik data www")
    if laporan["unit_berubah"]:
        lokasi.tulis("warisan/unit", hasil["sumber"]["unit"], oleh, bagian, "tarik data www")
    if laporan["kalender_berubah"]:
        lokasi.tulis("warisan/kalender", hasil["sumber"]["kalender"], oleh, bagian, "tarik data www")
    if laporan["universitas_berubah"]:
        lokasi.tulis("warisan/universitas", hasil["sumber"]["situs"], oleh, bagian, "tarik data www")
    meta = dict(hasil["sumber"]["meta"])
    meta.update({"ditarik": datetime.datetime.now().isoformat(timespec="seconds"), "oleh": oleh})
    lokasi.tulis("warisan/meta", meta, oleh, bagian, "tarik data www")
    import data_prodi
    laporan["dirapikan"] = data_prodi.rapikan(oleh)       # programme changes that www now has too
    return laporan


# ------------------------------------------------------------------ command line

def cetak_laporan(laporan, nama):
    def n(kode):
        return "%s %s" % (kode, nama.get(kode, ""))
    if laporan["pertama"]:
        print("Salinan pertama: %d prodi." % len(nama))
    for judul, kunci in (("Prodi baru di www", "baru"), ("Hilang dari www (ditandai, tidak dihapus)", "hilang"),
                         ("Muncul kembali di www", "kembali"), ("Belum terdaftar (belum punya slug)", "belum_terdaftar")):
        if laporan[kunci]:
            print("%s: %d" % (judul, len(laporan[kunci])))
            for k in laporan[kunci]:
                print("  - " + n(k))
    if laporan["berubah"]:
        print("Berubah: %d prodi" % len(laporan["berubah"]))
        for k, beda in sorted(laporan["berubah"].items()):
            print("  - " + n(k))
            for b in beda:
                print("      " + b)
    for kunci, judul in (("unit_berubah", "Data fakultas/unit berubah"), ("kalender_berubah", "Kalender akademik berubah"),
                         ("universitas_berubah", "Identitas/kontak universitas berubah"),
                         ("tampilan_berubah", "Pengaturan tampil 'berlaku hingga' berubah")):
        if laporan[kunci]:
            print(judul + ".")
    if laporan.get("bentrok"):
        print("Bentrok dengan data yang diubah prodi (data prodi tetap dipakai): %d prodi" % len(laporan["bentrok"]))
        for k, f in sorted(laporan["bentrok"].items()):
            print("  - %s: %s" % (n(k), ", ".join(f)))
    if laporan["kekurangan"]:
        print("Data resmi yang masih kosong (dilengkapi di www): %d prodi" % len(laporan["kekurangan"]))
        for k, label in sorted(laporan["kekurangan"].items()):
            print("  - %s: %s" % (n(k), ", ".join(label)))
    if not ada_perubahan(laporan):
        print("Tidak ada perubahan.")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tarik data resmi prodi dari www.unsrat.ac.id")
    ap.add_argument("--terapkan", action="store_true", help="tulis salinan baru (tanpa ini hanya pratinjau)")
    ap.add_argument("--paksa", action="store_true", help="terapkan walau banyak prodi hilang sekaligus")
    ap.add_argument("--sumber", help="folder data www (bawaan: WWW_DATA)")
    ap.add_argument("--oleh", default="baris-perintah", help="nama yang dicatat di riwayat")
    a = ap.parse_args(argv)
    try:
        hasil = pratinjau(a.sumber)
        nama = {p["kode_pddikti"]: "%s %s" % (p["jenjang"], p["nama"]) for p in hasil["prodi"]["program"]}
        if a.terapkan:
            laporan = terapkan(a.oleh, a.sumber, a.paksa)
            cetak_laporan(laporan, nama)
            print("Diterapkan." if ada_perubahan(laporan) else "")
        else:
            cetak_laporan(hasil["laporan"], nama)
            if ada_perubahan(hasil["laporan"]):
                print("Pratinjau saja; jalankan dengan --terapkan untuk menulis.")
    except GagalTarik as e:
        print("Data www TIDAK ditarik:")
        for m in e.masalah:
            print("  - " + m)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
