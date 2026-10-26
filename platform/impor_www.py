# -*- coding: utf-8 -*-
"""www.unsrat.ac.id's data uploaded by the superadmin (K-P18), and the starting copy of a new VM.

The platform runs on its own VM (K-P17) and cannot read www's data folder, so the superadmin downloads the data from
www and uploads it on the "Data www" page of the admin:

- the **Excel export of the study programmes** from www's superadmin (Impor Excel > Program studi > Unduh templat):
  sheet "Program studi" (one row per programme) and sheet "CPL" (one row per learning outcome); and/or
- www's **JSON data files**: prodi.json, unit.json (faculties), kalender.json (academic calendar) and situs.json
  (UNSRAT's identity and contacts), recognised by their content whatever their file name.

siapkan_kiriman() turns an upload into a folder with the four files in www's own format, the shape tarik_www.py reads.
A file that was not uploaded is written from the platform's current copy (warisan/*), so uploading only the Excel file
changes only the programme data. The folder is then previewed and applied by tarik_www.py exactly like WWW_DATA, with
every check of that module (the gambling-text filter included). The files taken from the current copy would undo a
change applied after the upload, so the folder records a fingerprint of the copy it was made from (sidik_dasar) and
the admin applies it only onto that same copy.

The Excel file is read the way www's own import reads it (site/admin/impor.py; docs/asal-modul.md): the header row
within the first 10 rows, www's column labels, cells as text, dates as YYYY-MM-DD. A column missing from the file
keeps the value of the current copy, and a missing CPL sheet keeps every CPL. A programme missing from the file is one
www no longer has: tarik_www marks it, and stops when too many disappear at once.

data-awal/www/ is a copy of www's data in www's format, written on a developer's machine. A new VM starts from it, so
the sites can be built before the first upload; the admin container runs --isi-awal at every start, which does nothing
once the platform has its own copy.

    python3 platform/impor_www.py --tulis-data-awal [--dari "..."]   write data-awal/www/ from the current copy
    python3 platform/impor_www.py --isi-awal          empty platform only: apply data-awal/www/, then the slug list
"""
from __future__ import print_function

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import sys
import zipfile

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)

import lokasi  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from slug import AWALAN_JENJANG  # noqa: E402

DATA_AWAL = os.path.join(PLATFORM, "data-awal", "www")
JENIS = tarik_www.SUMBER                     # prodi, unit, kalender, situs
NAMA_JENIS = {"prodi": "data program studi", "unit": "data fakultas (unit.json)",
              "kalender": "kalender akademik (kalender.json)", "situs": "identitas dan kontak universitas (situs.json)"}
BERKAS_SALINAN = ("warisan/prodi", "warisan/unit", "warisan/kalender", "warisan/universitas")
MAKS_BERKAS = 5                              # the Excel file and four JSON files at most
MAKS_UKURAN = 5 * 1024 * 1024                # per file, as www's import (www's prodi.json is about 0.7 MB)
MAKS_ISI_ZIP = 60 * 1024 * 1024
MAKS_BARIS = 5000

# column labels of www's template (site/admin/impor.py KOLOM_PRODI, KOLOM_CPL), compared without case; www's
# "Terjemahan Inggris diperiksa" is not used by the programme sites
KOLOM_PRODI = (("kode_pddikti", "Kode PDDIKTI"), ("nama", "Nama program studi"), ("jenjang", "Jenjang"),
               ("unit_kode", "Kode unit"), ("nama_en", "Nama (Inggris)"), ("gelar", "Gelar"), ("sks", "SKS"),
               ("akreditasi", "Akreditasi"), ("lembaga_akreditasi", "Lembaga akreditasi"),
               ("berlaku_hingga", "Berlaku hingga"), ("internasional", "Akreditasi internasional"),
               ("website", "Website"), ("surel", "Surel"), ("bidang_kerja", "Bidang kerja lulusan"),
               ("bidang_kerja_en", "Bidang kerja lulusan (Inggris)"))
KOLOM_CPL = (("kode_pddikti", "Kode PDDIKTI"), ("kode", "Kode CPL"), ("isi", "Isi CPL"), ("isi_en", "Isi CPL (Inggris)"),
             ("kurikulum", "Kurikulum"))
WAJIB_PRODI = {"kode_pddikti", "nama", "jenjang", "unit_kode"}
WAJIB_CPL = {"kode_pddikti", "kode", "isi"}
KONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# www's accreditation values, also written as their labels; empty (www's export of "belum") is "not filled in"
AKREDITASI = dict([(k.lower(), k) for k in registri.AKREDITASI_LABEL]
                  + [(v.lower(), k) for k, v in registri.AKREDITASI_LABEL.items()]
                  + [("belum", "belum"), ("belum dilengkapi", "belum")])


class GagalImpor(Exception):
    """The upload cannot be used; .masalah lists every problem found, for the superadmin."""

    def __init__(self, masalah):
        Exception.__init__(self, "%d masalah pada berkas unggahan" % len(masalah))
        self.masalah = masalah


# ------------------------------------------------------------------ the Excel export of www

def periksa_xlsx(data):
    """Refuse what is not a plain .xlsx workbook before it is parsed (www's periksa_xlsx): size, zip structure,
    unpacked size ("zip bomb"), macros."""
    if len(data) > MAKS_UKURAN:
        raise GagalImpor(["Berkas Excel terlalu besar (maksimal 5 MB)."])
    if not data.startswith(b"PK\x03\x04"):
        raise GagalImpor(["Isi berkas bukan file Excel .xlsx yang sah."])
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            info = z.infolist()
            nama = {i.filename for i in info}
            if len(info) > 2000 or sum(i.file_size for i in info) > MAKS_ISI_ZIP \
                    or any(i.compress_size and i.file_size > 300 * i.compress_size for i in info):
                raise GagalImpor(["Isi berkas Excel terlalu besar atau tidak wajar."])
            if "[Content_Types].xml" not in nama or "xl/workbook.xml" not in nama:
                raise GagalImpor(["Isi berkas bukan file Excel .xlsx yang sah."])
            if any(n.lower().endswith("vbaproject.bin") for n in nama) or b"macroEnabled" in z.read("[Content_Types].xml"):
                raise GagalImpor(["Berkas berisi makro. Simpan ulang sebagai Excel Workbook (.xlsx) tanpa makro."])
    except (zipfile.BadZipFile, zipfile.LargeZipFile, NotImplementedError, RuntimeError, ValueError):
        raise GagalImpor(["Berkas Excel rusak atau bukan .xlsx."])


def nilai(v):
    """A cell as clean text ("" when empty); dates as YYYY-MM-DD, whole numbers without .0 (www's nilai)."""
    if v is None:
        return ""
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat()[:10]
    if isinstance(v, bool):
        return "ya" if v else ""
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else str(v)
    if isinstance(v, int):
        return str(v)
    # only control characters and line-end styles are cleaned, so an unchanged export gives no changes
    return KONTROL.sub("", str(v)).replace("\r\n", "\n").replace("\r", "\n").strip()


def _kepala(v):
    return re.sub(r"\s+", " ", nilai(v)).strip().lower()


def _lembar(buku, judul):
    for ws in buku.worksheets:
        if ws.title.strip().lower() == judul.lower():
            return ws
    return None


def _tabel(ws, kolom, wajib):
    """({key: column index}, [(row number, {key: text})]) of a sheet whose header row (within the first 10 rows)
    has the labels of `kolom`, without empty rows. GagalImpor when the required columns are not there."""
    label = {l.lower(): k for k, l in kolom}
    baris = []
    try:
        ws.reset_dimensions()             # a wrong size recorded in the file must not cut rows off
        for n, r in enumerate(ws.iter_rows(values_only=True), 1):
            if any(nilai(v) for v in r):
                baris.append((n, list(r)))
                if len(baris) > MAKS_BARIS:
                    raise GagalImpor(["Lembar '%s' terlalu banyak baris (maksimal %d)." % (ws.title, MAKS_BARIS)])
    except GagalImpor:
        raise
    except Exception:
        raise GagalImpor(["Berkas Excel tidak dapat dibaca. Simpan ulang di Excel sebagai .xlsx lalu coba lagi."])
    for i, (n, r) in enumerate(baris):
        if n > 10:
            break
        ada = {}
        for j, h in enumerate(_kepala(c) for c in r):
            if h in label and label[h] not in ada:
                ada[label[h]] = j
        if wajib <= set(ada):
            hasil = []
            for nomor, rr in baris[i + 1:]:
                isi = {k: nilai(rr[j]) if j < len(rr) else "" for k, j in ada.items()}
                if any(isi.values()):
                    hasil.append((nomor, isi))
            return ada, hasil
    raise GagalImpor(["Lembar '%s': judul kolom %s tidak ditemukan di 10 baris teratas. Unggah berkas ekspor dari "
                      "superadmin www tanpa mengubah judul kolomnya." % (
                          ws.title, ", ".join("'%s'" % l for k, l in kolom if k in wajib))])


def baca_tanggal(teks):
    """'2029-06-30', '30-06-2029' or '30/06/2029' -> '2029-06-30' (www's baca_tanggal); ValueError otherwise."""
    for pola in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(teks, pola).date().isoformat()
        except ValueError:
            pass
    raise ValueError("tanggal '%s' tidak dikenali; tulis seperti 2029-06-30" % teks[:40])


def _isi_kolom(kunci, v, per_unit, peringatan, tempat):
    """The stored value of one programme cell; ValueError with the problem."""
    if kunci in ("nama", "jenjang", "unit_kode") and not v:
        raise ValueError("wajib diisi")
    if kunci == "jenjang":
        cocok = [j for j in AWALAN_JENJANG if j.lower() == v.lower()]
        if not cocok:
            raise ValueError("jenjang '%s' tidak dikenal; pilih %s" % (v[:40], ", ".join(AWALAN_JENJANG)))
        return cocok[0]
    if kunci == "unit_kode":
        if v.lower() not in per_unit:
            raise ValueError("kode unit '%s' tidak ada di data fakultas; unggah juga unit.json terbaru dari www" % v[:40])
        return per_unit[v.lower()]["kode"]
    if kunci == "akreditasi":
        if v.lower() in AKREDITASI or not v:
            return AKREDITASI.get(v.lower(), "belum")
        peringatan.append("%s: akreditasi '%s' belum dikenal platform; ditampilkan apa adanya." % (tempat, v[:60]))
        return v
    if kunci == "sks":
        if not v:
            return None
        if not re.match(r"^\d{1,3}$", v) or not 0 < int(v) < 400:
            raise ValueError("SKS '%s' harus angka bulat 1–399" % v[:40])
        return int(v)
    if kunci == "berlaku_hingga":
        return baca_tanggal(v) if v else ""
    return v


def baca_excel(data, prodi_lama, unit):
    """www's prodi.json from the Excel export. prodi_lama: the platform's current warisan/prodi (or None); unit: the
    faculties ({"kode", "nama", ...}) from the uploaded unit.json or the current copy.
    Returns (prodi, peringatan); GagalImpor lists every problem found."""
    periksa_xlsx(data)
    try:
        from openpyxl import load_workbook
        buku = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception:
        raise GagalImpor(["Berkas Excel tidak dapat dibaca. Simpan ulang di Excel sebagai .xlsx lalu coba lagi."])
    try:
        ws = _lembar(buku, "Program studi") or (buku.worksheets[0] if len(buku.worksheets) == 1 else None)
        if ws is None:
            raise GagalImpor(["Lembar 'Program studi' tidak ditemukan. Unggah berkas ekspor program studi dari "
                              "superadmin www."])
        kolom, baris = _tabel(ws, KOLOM_PRODI, WAJIB_PRODI)
        ws_cpl = _lembar(buku, "CPL")
        cpl_baris = _tabel(ws_cpl, KOLOM_CPL, WAJIB_CPL)[1] if ws_cpl is not None else None
    finally:
        buku.close()

    masalah, peringatan = [], []
    lama = {p["kode_pddikti"]: p for p in (prodi_lama or {}).get("program", [])}
    per_unit = {u["kode"].lower(): u for u in unit if isinstance(u, dict) and isinstance(u.get("kode"), str)}
    for k, l in KOLOM_PRODI:
        if k not in kolom:
            peringatan.append("Kolom '%s' tidak ada di berkas; nilainya tidak diubah." % l)
    program, dilihat = [], set()
    for nomor, r in baris:
        tempat = "Program studi baris %d" % nomor
        kode = r["kode_pddikti"]
        if not tarik_www.POLA_KODE.match(kode):
            masalah.append("%s: kode PDDIKTI '%s' tidak sah." % (tempat, kode[:40]))
            continue
        if kode in dilihat:
            masalah.append("%s: kode %s muncul lebih dari sekali." % (tempat, kode))
            continue
        dilihat.add(kode)
        tua = lama.get(kode, {})          # a new programme starts empty: nothing is made up for it
        p = {f: tua.get(f, "") for f in tarik_www.FIELD_PRODI}
        p.update(kode_pddikti=kode, sks=tua.get("sks"), cpl=list(tua.get("cpl", [])))
        for kunci in kolom:
            if kunci == "kode_pddikti":
                continue
            try:
                p[kunci] = _isi_kolom(kunci, r[kunci], per_unit, peringatan, tempat)
            except ValueError as e:
                masalah.append("%s, kolom %s: %s." % (tempat, dict(KOLOM_PRODI)[kunci], e))
        if p["unit_kode"].lower() in per_unit:
            p["unit"] = per_unit[p["unit_kode"].lower()].get("nama", "")
        program.append(p)

    if cpl_baris is None:
        peringatan.append("Lembar CPL tidak ada di berkas; CPL tidak diubah.")
    else:
        per_prodi = {}
        for nomor, r in cpl_baris:
            tempat = "CPL baris %d" % nomor
            if r["kode_pddikti"] not in dilihat:
                masalah.append("%s: kode PDDIKTI '%s' tidak ada di lembar Program studi." % (tempat, r["kode_pddikti"][:40]))
            elif not r["kode"] or not r["isi"]:
                masalah.append("%s: Kode CPL dan Isi CPL wajib diisi." % tempat)
            else:
                per_prodi.setdefault(r["kode_pddikti"], []).append(
                    {"kode": r["kode"], "isi": r["isi"], "isi_en": r.get("isi_en", ""), "kurikulum": r.get("kurikulum", "")})
        for p in program:
            p["cpl"] = per_prodi.get(p["kode_pddikti"], [])
    if not program and not masalah:
        masalah.append("Lembar 'Program studi' tidak berisi program studi.")
    if masalah:
        raise GagalImpor(masalah)
    return {"tampilkan_berlaku_hingga": bool((prodi_lama or {}).get("tampilkan_berlaku_hingga")), "program": program}, \
        peringatan


# ------------------------------------------------------------------ www's JSON files

def jenis_json(isi):
    """Which of www's data files this is, by its content: "prodi", "unit", "kalender", "situs", or None."""
    if not isinstance(isi, dict):
        return None
    cocok = [jenis for jenis, ya in (
        ("prodi", isinstance(isi.get("program"), list)),
        ("unit", isinstance(isi.get("unit"), list)),
        ("kalender", isinstance(isi.get("semester"), list)),
        ("situs", isinstance(isi.get("identitas"), dict) and isinstance(isi.get("kontak"), dict))) if ya]
    return cocok[0] if len(cocok) == 1 else None


def baca_json(nama, data):
    """(kind, content) of an uploaded JSON file; GagalImpor when it is not one of www's data files."""
    if len(data) > MAKS_UKURAN:
        raise GagalImpor(["%s: berkas terlalu besar (maksimal 5 MB)." % nama])
    try:
        isi = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise GagalImpor(["%s: bukan berkas JSON yang sah." % nama])
    jenis = jenis_json(isi)
    if jenis is None:
        raise GagalImpor(["%s: bukan berkas data www yang dikenal (prodi.json, unit.json, kalender.json, situs.json)." % nama])
    return jenis, isi


# ------------------------------------------------------------------ the platform's current copy

def salinan_sekarang(jenis):
    """The platform's current copy of one of www's files, in www's format; None when there is none yet."""
    if jenis == "prodi":
        w = lokasi.baca("warisan/prodi")
        if w is None:
            return None
        return {"tampilkan_berlaku_hingga": bool(w.get("tampilkan_berlaku_hingga")),
                "program": [{k: v for k, v in p.items() if k != "hilang_dari_www"} for p in w.get("program", [])
                            if not p.get("hilang_dari_www")]}
    if jenis == "situs":
        u = lokasi.baca("warisan/universitas")
        return None if u is None else dict(u, utilitas={"id": u.get("utilitas") or []})   # www's own shape
    return lokasi.baca("warisan/" + jenis)


def sidik_dasar():
    """Fingerprint of the platform's current copy of www's data (see the module docstring)."""
    h = hashlib.sha256()
    for berkas in BERKAS_SALINAN:
        h.update(json.dumps(lokasi.baca(berkas), sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\0")
    return h.hexdigest()[:32]


# ------------------------------------------------------------------ an upload

def siapkan_kiriman(berkas, folder, **catatan):
    """Turn an upload, [(file name, bytes)], into `folder` (which must not exist yet): prodi.json, unit.json,
    kalender.json and situs.json for tarik_www, and kiriman.json with what was uploaded, what came from the current
    copy, the warnings, the fingerprint of the copy, a label for warisan/meta.json, and `catatan` (who uploaded it,
    when). Returns that record. GagalImpor (and no folder) when the upload cannot be used."""
    if not berkas:
        raise GagalImpor(["Pilih berkas Excel ekspor program studi dari superadmin www, dan/atau berkas JSON data www."])
    if len(berkas) > MAKS_BERKAS:
        raise GagalImpor(["Paling banyak %d berkas sekali unggah." % MAKS_BERKAS])
    masalah, dari_berkas, excel = [], {}, None
    for nama, data in berkas:
        nama = os.path.basename((nama or "").replace("\\", "/"))[:120] or "berkas"
        akhiran = nama.lower().rsplit(".", 1)[-1] if "." in nama else ""
        try:
            if akhiran == "xlsx":
                if excel:
                    raise GagalImpor(["Unggah satu berkas Excel saja (%s dan %s)." % (excel[0], nama)])
                excel = (nama, data)      # read once the JSON files are known: an uploaded unit.json names the faculties
            elif akhiran == "json":
                jenis, isi = baca_json(nama, data)
                if jenis in dari_berkas:
                    raise GagalImpor(["%s dan %s sama-sama berisi %s; unggah salah satu." % (
                        dari_berkas[jenis][0], nama, NAMA_JENIS[jenis])])
                dari_berkas[jenis] = (nama, isi, len(data))
            elif akhiran in ("xls", "xlsm", "xlsb", "csv", "ods"):
                raise GagalImpor(["%s: format .%s tidak diterima. Unggah berkas .xlsx hasil ekspor superadmin www apa "
                                  "adanya." % (nama, akhiran)])
            else:
                raise GagalImpor(["%s: hanya berkas Excel (.xlsx) atau JSON (.json) yang diterima." % nama])
        except GagalImpor as e:
            masalah.extend(e.masalah)
    if excel and "prodi" in dari_berkas:
        masalah.append("Data program studi diunggah dua kali (%s dan %s); unggah salah satu." % (
            excel[0], dari_berkas["prodi"][0]))
    if masalah:
        raise GagalImpor(masalah)

    peringatan = []
    if excel:
        unit = (dari_berkas["unit"][1] if "unit" in dari_berkas else salinan_sekarang("unit") or {}).get("unit")
        if not isinstance(unit, list):
            raise GagalImpor(["Data fakultas belum ada di platform: unggah juga unit.json dari www."])
        prodi, peringatan = baca_excel(excel[1], lokasi.baca("warisan/prodi"), unit)
        dari_berkas["prodi"] = (excel[0], prodi, len(excel[1]))
    isi, dari_salinan = {}, []
    for jenis in JENIS:
        if jenis in dari_berkas:
            isi[jenis] = dari_berkas[jenis][1]
            continue
        isi[jenis] = salinan_sekarang(jenis)
        dari_salinan.append(jenis)
        if isi[jenis] is None:
            masalah.append("Platform belum punya %s: unggah juga berkasnya dari www." % NAMA_JENIS[jenis])
    if masalah:
        raise GagalImpor(masalah)

    catatan.update(berkas=[{"nama": v[0], "jenis": j, "ukuran": v[2]} for j, v in sorted(dari_berkas.items())],
                   dari_salinan=dari_salinan, peringatan=peringatan[:200], dasar=sidik_dasar(),
                   label="unggahan superadmin: " + ", ".join(sorted({v[0] for v in dari_berkas.values()})))
    os.makedirs(os.path.dirname(folder), exist_ok=True)
    os.mkdir(folder, 0o700)
    try:
        for jenis in JENIS:
            lokasi.tulis_json(os.path.join(folder, jenis + ".json"), isi[jenis])
        lokasi.tulis_json(os.path.join(folder, "kiriman.json"), catatan)
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return catatan


def baca_kiriman(folder):
    """The record siapkan_kiriman wrote for an upload."""
    with io.open(os.path.join(folder, "kiriman.json"), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ the starting copy of a new VM

def asal_data_awal(folder=DATA_AWAL):
    path = os.path.join(folder, "asal.json")
    if not os.path.isfile(path):
        return {}
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def tulis_data_awal(folder=DATA_AWAL, dari=None):
    """Write the platform's current copy of www's data as the starting copy of new VMs (a developer, after pulling
    fresh data from www). dari: where the copy came from, e.g. www's commit. Returns the number of programmes."""
    isi = {jenis: salinan_sekarang(jenis) for jenis in JENIS}
    kosong = [jenis for jenis in JENIS if isi[jenis] is None]
    if kosong:
        raise GagalImpor(["salinan %s belum ada: tarik data www dulu" % ", ".join(kosong)])
    for jenis in JENIS:
        lokasi.tulis_json(os.path.join(folder, jenis + ".json"), isi[jenis])
    meta = lokasi.baca("warisan/meta") or {}
    lokasi.tulis_json(os.path.join(folder, "asal.json"), {
        "diambil": (meta.get("ditarik") or datetime.date.today().isoformat())[:10],
        "dari": dari or "data www.unsrat.ac.id", "jumlah_prodi": len(isi["prodi"]["program"])})
    return len(isi["prodi"]["program"])


def isi_awal(oleh="data-awal", folder=DATA_AWAL):
    """First start of a new VM: when the platform has no copy of www's data, apply the starting copy; when it has no
    registry, register the programmes of the approved slug list. Does nothing on a platform that has both. Returns
    what was done, as lines."""
    pesan = []
    if lokasi.baca("warisan/prodi") is None:
        label = "data awal repo (salinan www %s)" % (asal_data_awal(folder).get("diambil") or "?")
        laporan = tarik_www.terapkan(oleh, folder=folder, keterangan=label)
        pesan.append("%s diterapkan: %d prodi" % (label, len(laporan["baru"])))
    if lokasi.baca("registri") is None:
        pesan.append("registri awal dari slug.csv: %d prodi" % registri.siapkan_dari_csv(oleh))
    return pesan


# ------------------------------------------------------------------ command line

def main(argv=None):
    ap = argparse.ArgumentParser(description="Data www untuk platform prodi: data awal VM baru")
    aksi = ap.add_mutually_exclusive_group(required=True)
    aksi.add_argument("--tulis-data-awal", action="store_true", help="tulis data-awal/www/ dari salinan platform sekarang")
    aksi.add_argument("--isi-awal", action="store_true", help="platform kosong saja: terapkan data-awal/www/ dan slug.csv")
    ap.add_argument("--dari", help="asal salinan untuk --tulis-data-awal, mis. commit www")
    a = ap.parse_args(argv)
    try:
        if a.tulis_data_awal:
            print("data-awal/www/: %d prodi" % tulis_data_awal(dari=a.dari))
        else:
            for baris in isi_awal() or ["data www dan registri sudah ada; data awal tidak dipakai"]:
                print(baris)
    except (GagalImpor, tarik_www.GagalTarik) as e:
        print("Data awal TIDAK diterapkan:")
        for m in e.masalah:
            print("  - " + m)
        return 1
    except registri.GagalRegistri as e:
        print("Registri awal TIDAK dibuat: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
