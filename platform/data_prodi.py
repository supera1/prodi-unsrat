# -*- coding: utf-8 -*-
"""A programme's own changes to its official data (langkah 5b, K-P16): prodi/<kode>/data.json.

The copy from www (warisan/prodi.json, tarik_www.py) is never edited. A change made in the admin is kept here per
field, as a "timpaan" (override), with the www value it replaced:

    {"timpaan": {"akreditasi": "Baik Sekali", "cpl": [...]},
     "dasar":   {"akreditasi": "Unggul", "cpl": [...]},          www's value when the field was changed here
     "diubah":  {"akreditasi": {"oleh": "adma", "waktu": "..."}}}

The data a site is built with (efektif) is www's copy with these fields put over it. Fields without an override keep
following www. When www later changes a field that has an override (www now differs from "dasar"), the field is a
"bentrok" (conflict): the local value stays in use (decision of 26 October 2026) and the admin is shown both, with
"pakai data www" (drop the override) or "tetap" (keep it; www's new value becomes the new "dasar"). An override that
www has caught up with (same value) is dropped by rapikan() after a pull.

Who may change: the superadmin and the programme's admins, every field of FIELD_UBAH (decision of 26 October 2026).
"""
from __future__ import print_function

import datetime
import os
import re
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import lokasi  # noqa: E402
import saringan_spam  # noqa: E402
import tarik_www  # noqa: E402
from slug import AWALAN_JENJANG  # noqa: E402

# field -> (label, maximum length of text, kind)
FIELD_UBAH = {
    "nama": ("Nama program studi", 150, "teks"),
    "nama_en": ("Nama dalam bahasa Inggris", 150, "teks"),
    "jenjang": ("Jenjang", 10, "jenjang"),
    "gelar": ("Gelar lulusan", 60, "teks"),
    "sks": ("Beban studi (SKS)", 3, "sks"),
    "unit_kode": ("Fakultas", 30, "unit"),
    "surel": ("Surel program studi", 120, "surel"),
    "bidang_kerja": ("Bidang kerja lulusan", 3000, "panjang"),
    "bidang_kerja_en": ("Bidang kerja lulusan (bahasa Inggris)", 3000, "panjang"),
    "akreditasi": ("Peringkat akreditasi", 60, "teks"),
    "lembaga_akreditasi": ("Lembaga akreditasi", 60, "teks"),
    "berlaku_hingga": ("Akreditasi berlaku hingga", 10, "tanggal"),
    "internasional": ("Akreditasi internasional", 120, "teks"),
    "cpl": ("Capaian pembelajaran lulusan (CPL)", 0, "cpl"),
}
MAKS_CPL = 40
MAKS_CPL_ISI = 2000
POLA_SUREL = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[a-z]{2,}$")
POLA_KODE = re.compile(r"^[0-9A-Za-z]{3,12}$")


class GagalData(ValueError):
    pass


def _sekarang():
    return datetime.datetime.now().isoformat(timespec="seconds")


def berkas(kode):
    if not POLA_KODE.match(kode or ""):
        raise GagalData("kode prodi tidak sah")
    return "prodi/%s/data" % kode


def baca(kode):
    data = lokasi.baca(berkas(kode)) or {}
    return {"timpaan": data.get("timpaan") or {}, "dasar": data.get("dasar") or {}, "diubah": data.get("diubah") or {}}


def unit_per_kode():
    return {u["kode"]: u for u in (lokasi.baca("warisan/unit") or {}).get("unit", [])}


JENIS_UNIT_PRODI = ("fakultas", "pascasarjana")


def unit_prodi():
    """Units a programme can belong to: faculties and the graduate school, plus any unit www gives a programme."""
    dipakai = {p.get("unit_kode") for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}
    return {k: u for k, u in unit_per_kode().items() if u.get("jenis") in JENIS_UNIT_PRODI or k in dipakai}


def gabung(p_www, data, unit=None):
    """www's record with the overrides put over it (a new dict; the inputs are not changed)."""
    if p_www is None:
        return None
    hasil = dict(p_www)
    for f, v in data["timpaan"].items():
        if f in FIELD_UBAH:
            hasil[f] = v
    if "unit_kode" in data["timpaan"]:
        u = (unit if unit is not None else unit_per_kode()).get(hasil["unit_kode"])
        if u:
            hasil["unit"] = u["nama"]
    return hasil


def efektif(kode, p_www=None):
    """The data programme `kode` is shown with."""
    if p_www is None:
        p_www = {p["kode_pddikti"]: p for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}.get(kode)
    return gabung(p_www, baca(kode))


def semua_efektif():
    """{code: effective record} for every programme of www's copy (overrides only exist for registered ones)."""
    unit = unit_per_kode()
    hasil = {}
    for p in (lokasi.baca("warisan/prodi") or {}).get("program", []):
        path = lokasi.path_data(berkas(p["kode_pddikti"]))
        hasil[p["kode_pddikti"]] = gabung(p, baca(p["kode_pddikti"]), unit) if os.path.isfile(path) else p
    return hasil


def bentrok(kode, p_www=None, data=None):
    """Fields whose www value changed after they were changed here: [(field, local value, www now, www then)]."""
    if p_www is None:
        p_www = {p["kode_pddikti"]: p for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}.get(kode) or {}
    data = data or baca(kode)
    hasil = []
    for f, v in data["timpaan"].items():
        if f in data["dasar"] and p_www.get(f) != data["dasar"][f] and p_www.get(f) != v:
            hasil.append((f, v, p_www.get(f), data["dasar"][f]))
    return hasil


# ------------------------------------------------------------------ checks

def _periksa_teks(label, v, maks, masalah, wajib=False, panjang=False):
    if v is None:
        v = ""
    if not isinstance(v, str):
        masalah.append("%s harus berupa teks" % label)
        return
    if wajib and not v.strip():
        masalah.append("%s wajib diisi" % label)
    if len(v) > maks:
        masalah.append("%s terlalu panjang (maksimal %d karakter)" % (label, maks))
    if re.search(r"<\s*/?\s*[a-zA-Z!]", v):
        masalah.append("%s tidak boleh memuat HTML" % label)
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]" if panjang else r"[\x00-\x1f]", v):
        masalah.append("%s memuat karakter kendali" % label)
    istilah = saringan_spam.cari(v)
    if istilah:
        masalah.append("%s memuat istilah terlarang (“%s”)" % (label, istilah))


def periksa_nilai(f, v, unit=None):
    """Problems with one value for field f (empty list when it may be saved)."""
    if f not in FIELD_UBAH:
        return ["kolom %s tidak dapat diubah" % f]
    label, maks, jenis = FIELD_UBAH[f]
    masalah = []
    if jenis in ("teks", "panjang"):
        _periksa_teks(label, v, maks, masalah, wajib=(f == "nama"), panjang=(jenis == "panjang"))
    elif jenis == "jenjang":
        if v not in AWALAN_JENJANG:
            masalah.append("%s harus salah satu dari: %s" % (label, ", ".join(AWALAN_JENJANG)))
    elif jenis == "sks":
        if v is not None and not (isinstance(v, int) and not isinstance(v, bool) and 0 < v < 400):
            masalah.append("%s harus angka 1-399 atau kosong" % label)
    elif jenis == "unit":
        if v not in (unit if unit is not None else unit_prodi()):
            masalah.append("%s tidak dikenal" % label)
    elif jenis == "surel":
        if v and (not POLA_SUREL.match(v) or len(v) > maks):
            masalah.append("%s tidak sah" % label)
    elif jenis == "tanggal":
        if v and not tarik_www.POLA_TANGGAL.match(v):
            masalah.append("%s harus tanggal (TTTT-BB-HH) atau kosong" % label)
        elif v:
            try:
                datetime.date.fromisoformat(v)
            except ValueError:
                masalah.append("%s bukan tanggal yang ada" % label)
    elif jenis == "cpl":
        if not isinstance(v, list) or len(v) > MAKS_CPL:
            masalah.append("CPL paling banyak %d butir" % MAKS_CPL)
        else:
            for i, c in enumerate(v, 1):
                if not isinstance(c, dict) or set(c) - set(tarik_www.FIELD_CPL):
                    masalah.append("CPL ke-%d tidak sah" % i)
                    continue
                _periksa_teks("CPL ke-%d" % i, c.get("isi"), MAKS_CPL_ISI, masalah, wajib=True, panjang=True)
                _periksa_teks("CPL ke-%d (bahasa Inggris)" % i, c.get("isi_en"), MAKS_CPL_ISI, masalah, panjang=True)
                _periksa_teks("Kode CPL ke-%d" % i, c.get("kode"), 20, masalah)
                _periksa_teks("Kurikulum CPL ke-%d" % i, c.get("kurikulum"), 20, masalah)
    return masalah


# ------------------------------------------------------------------ changes

def _tulis(kode, data, oleh, aksi):
    lokasi.tulis(berkas(kode), data, oleh, "Data prodi", aksi)


def _www(kode):
    p = {p["kode_pddikti"]: p for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}.get(kode)
    if p is None:
        raise GagalData("prodi %s tidak ada di data resmi www" % kode)
    return p


def simpan(kode, perubahan, oleh):
    """Save new values ({field: value}); a value equal to www's drops the override. Returns the changed fields."""
    p_www = _www(kode)
    unit = unit_per_kode()
    masalah = []
    for f, v in perubahan.items():
        masalah += periksa_nilai(f, v, unit_prodi())
    if masalah:
        raise GagalData("; ".join(masalah))
    data = baca(kode)
    kini = gabung(p_www, data, unit)
    berubah = []
    for f, v in perubahan.items():
        if kini.get(f) == v:
            continue
        berubah.append(f)
        if p_www.get(f) == v:
            for k in ("timpaan", "dasar", "diubah"):
                data[k].pop(f, None)
        else:
            if f not in data["timpaan"]:
                data["dasar"][f] = p_www.get(f)
            data["timpaan"][f] = v
            data["diubah"][f] = {"oleh": oleh, "waktu": _sekarang()}
    if berubah:
        # the whole record must still be valid (the same checks as a pull from www)
        masalah = tarik_www.periksa_prodi(dict(gabung(p_www, data, unit), slug=p_www.get("slug") or "x"))
        if masalah:
            raise GagalData("; ".join(masalah))
        _tulis(kode, data, oleh, "ubah %s" % ", ".join(berubah))
    return berubah


def pakai_www(kode, f, oleh):
    """Drop the override of field f: the field follows www again."""
    data = baca(kode)
    if f not in data["timpaan"]:
        return False
    for k in ("timpaan", "dasar", "diubah"):
        data[k].pop(f, None)
    _tulis(kode, data, oleh, "pakai data www untuk %s" % f)
    return True


def tetap(kode, f, oleh):
    """Keep the local value of field f after www changed it: www's new value becomes the base, the conflict ends."""
    data = baca(kode)
    if f not in data["timpaan"]:
        return False
    data["dasar"][f] = _www(kode).get(f)
    data["diubah"][f] = dict(data["diubah"].get(f, {}), tetap_oleh=oleh, tetap_waktu=_sekarang())
    _tulis(kode, data, oleh, "tetap memakai data sendiri untuk %s" % f)
    return True


def rapikan(oleh):
    """After a pull: drop overrides that www has caught up with. Returns {code: [fields]}."""
    hasil = {}
    for p in (lokasi.baca("warisan/prodi") or {}).get("program", []):
        kode = p["kode_pddikti"]
        if not os.path.isfile(lokasi.path_data(berkas(kode))):
            continue
        data = baca(kode)
        sama = [f for f, v in data["timpaan"].items() if p.get(f) == v]
        if sama:
            for f in sama:
                for k in ("timpaan", "dasar", "diubah"):
                    data[k].pop(f, None)
            _tulis(kode, data, oleh, "data www sudah sama untuk %s" % ", ".join(sama))
            hasil[kode] = sama
    return hasil


def semua_bentrok():
    """{code: [conflicts]} for every programme with at least one."""
    www = {p["kode_pddikti"]: p for p in (lokasi.baca("warisan/prodi") or {}).get("program", [])}
    hasil = {}
    for kode, p in www.items():
        if os.path.isfile(lokasi.path_data(berkas(kode))):
            b = bentrok(kode, p)
            if b:
                hasil[kode] = b
    return hasil


def bentrok_jika_ditarik(sumber_prodi):
    """Conflicts a pull of `sumber_prodi` (tarik_www source) would cause or keep: {code: [fields]}."""
    hasil = {}
    for p in sumber_prodi.get("program", []):
        kode = p["kode_pddikti"]
        if os.path.isfile(lokasi.path_data(berkas(kode))):
            b = [x[0] for x in bentrok(kode, p)]
            if b:
                hasil[kode] = b
    return hasil
