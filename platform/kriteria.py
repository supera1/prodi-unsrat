# -*- coding: utf-8 -*-
"""Accreditation criteria labels of the programme pages (Fase 2 langkah 4, rencana §3.7, K-P25, K-P29, K-P33).

Every required page can carry the criterion of the accreditation instrument it serves ("Kriteria 2: Tata Pamong, Tata
Kelola, dan Kerja Sama"), and the accreditation page lists the pages per criterion, so an assessor finds them by
criterion. Instruments differ per accreditation body (BAN-PT's IAPS 4.0 has 9 criteria; each LAM has its own), so the
lists and the mapping page → criteria live in platform/template/kriteria.json and are prepared or confirmed by LPMPP
UNSRAT. A body is shown only once its entry is "dikonfirmasi" (with who confirmed it and when); a draft is never shown
on any site, so nothing unconfirmed is presented as fact.

    {"lembaga": [{"id": "ban-pt", "nama": "BAN-PT", "instrumen": "...", "alias": ["BAN-PT"],
                  "status": "draf" | "dikonfirmasi", "dikonfirmasi": {"oleh": "LPMPP UNSRAT", "tanggal": "2026-11-30"},
                  "kriteria": [{"nomor": "1", "nama": "Visi, Misi, Tujuan, dan Strategi"}, ...],
                  "halaman": {"visi-misi": ["1"], ...}}, ...]}

"alias" are the values of "lembaga_akreditasi" in the official data (www) that mean this body ("LAM-Teknik",
"LAM-Tek"); a value no entry claims (empty, "BAN-PT / LAM-PTIP") gets no labels.

A programme's admin can also set the criteria of its own site (K-P33): prodi/<kode>/kriteria.json holds one body in
the same shape, without alias and status. When it has criteria it is what the site shows; otherwise a body confirmed
in the shared file is shown, if any. The shared drafts serve as starting points ("usulan") for that form.

    {"nama": "LAM Teknik", "instrumen": "...", "kriteria": [{"nomor": "1", "nama": "..."}], "halaman": {"visi-misi": ["1"]}}

    python3 platform/kriteria.py periksa      check the file
    python3 platform/kriteria.py tabel        the draft mapping as Markdown, for LPMPP (docs/kriteria-akreditasi.md)
"""
from __future__ import print_function

import copy
import datetime
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

KRITERIA_JSON = os.path.join(PLATFORM, "template", "kriteria.json")
POLA_ID = re.compile(r"^[a-z][a-z0-9-]{1,30}$")
POLA_NOMOR = re.compile(r"^[0-9A-Za-z.]{1,8}$")
KONTROL = re.compile(r"[\x00-\x1f\x7f<>]")
STATUS = ("draf", "dikonfirmasi")
MAKS_NAMA = 150
MAKS_LEMBAGA = 60
MAKS_KRITERIA = 20             # criteria of one programme's body


class GagalKriteria(ValueError):
    """A programme's criteria were refused; the message is shown to its admin."""


def baca(path=None):
    with io.open(path or KRITERIA_JSON, encoding="utf-8") as f:
        return json.load(f)


def _teks(v, maks=MAKS_NAMA):
    return isinstance(v, str) and v.strip() == v and 0 < len(v) <= maks and not KONTROL.search(v)


def periksa(data, halaman_ada):
    """Problems of the file (empty list when it may be used). halaman_ada: the ids of the pages a criterion may be put
    on (the programme's own pages)."""
    masalah = []
    if not isinstance(data, dict) or not isinstance(data.get("lembaga"), list):
        return ["berkas kriteria harus berisi daftar \"lembaga\""]
    id_dipakai, alias_dipakai = set(), {}
    for i, lb in enumerate(data["lembaga"], 1):
        di = "lembaga %d" % i
        if not isinstance(lb, dict):
            masalah.append("%s: bukan objek" % di)
            continue
        if not isinstance(lb.get("id"), str) or not POLA_ID.match(lb["id"]) or lb["id"] in id_dipakai:
            masalah.append("%s: id tidak sah atau ganda" % di)
        else:
            id_dipakai.add(lb["id"])
            di = "lembaga %s" % lb["id"]
        for k in ("nama", "instrumen"):
            if not _teks(lb.get(k)):
                masalah.append("%s: %s harus teks 1-%d karakter, tanpa < > dan karakter kendali" % (di, k, MAKS_NAMA))
        alias = lb.get("alias")
        if not isinstance(alias, list) or not alias or not all(_teks(a, 60) for a in alias):
            masalah.append("%s: alias harus daftar nilai lembaga_akreditasi" % di)
        else:
            for a in alias:
                kunci = _kunci(a)
                if kunci in alias_dipakai:
                    masalah.append("%s: alias %r sudah dipakai %s" % (di, a, alias_dipakai[kunci]))
                alias_dipakai[kunci] = di
        if lb.get("status") not in STATUS:
            masalah.append("%s: status harus draf atau dikonfirmasi" % di)
        kriteria = lb.get("kriteria")
        nomor = set()
        if not isinstance(kriteria, list):
            masalah.append("%s: kriteria harus daftar" % di)
            kriteria = []
        for k in kriteria:
            if not isinstance(k, dict) or not isinstance(k.get("nomor"), str) or not POLA_NOMOR.match(k["nomor"]) \
                    or k["nomor"] in nomor or not _teks(k.get("nama")):
                masalah.append("%s: kriteria %r tidak sah (nomor unik, nama 1-%d karakter)" % (di, k, MAKS_NAMA))
            else:
                nomor.add(k["nomor"])
        halaman = lb.get("halaman")
        if not isinstance(halaman, dict):
            masalah.append("%s: halaman harus objek {id halaman: [nomor kriteria]}" % di)
            halaman = {}
        for id_, daftar in halaman.items():
            if id_ not in halaman_ada:
                masalah.append("%s: halaman %r tidak dikenal" % (di, id_))
            if not isinstance(daftar, list) or not daftar or not all(x in nomor for x in daftar) or len(set(daftar)) != len(daftar):
                masalah.append("%s: kriteria halaman %r harus nomor kriteria lembaga ini, tanpa ganda" % (di, id_))
        if lb.get("status") == "dikonfirmasi":
            konf = lb.get("dikonfirmasi")
            if not kriteria or not halaman:
                masalah.append("%s: lembaga yang dikonfirmasi harus punya kriteria dan pemetaan halaman" % di)
            if not isinstance(konf, dict) or not _teks(konf.get("oleh")) or not _tanggal(konf.get("tanggal")):
                masalah.append("%s: dikonfirmasi harus menyebut oleh siapa dan tanggal (YYYY-MM-DD)" % di)
    return masalah


def _tanggal(v):
    try:
        return isinstance(v, str) and datetime.date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def _kunci(nama):
    return re.sub(r"\s+", " ", (nama or "").strip()).upper()


def berkas_prodi(kode):
    return "prodi/%s/kriteria" % kode


def periksa_prodi(data, halaman_ada):
    """Problems of a programme's own criteria (K-P33), as messages for its admin; empty list when they may be shown."""
    if not isinstance(data, dict):
        return ["kriteria prodi harus berupa objek"]
    masalah = []
    if not _teks(data.get("nama"), MAKS_LEMBAGA):
        masalah.append("Nama lembaga harus diisi, paling panjang %d karakter, tanpa < > dan karakter kendali"
                       % MAKS_LEMBAGA)
    if data.get("instrumen", "") != "" and not _teks(data.get("instrumen")):
        masalah.append("Nama instrumen paling panjang %d karakter, tanpa < > dan karakter kendali" % MAKS_NAMA)
    kriteria = data.get("kriteria")
    if not isinstance(kriteria, list):
        return masalah + ["kriteria harus daftar"]
    if len(kriteria) > MAKS_KRITERIA:
        masalah.append("Paling banyak %d kriteria" % MAKS_KRITERIA)
    nomor = set()
    for i, k in enumerate(kriteria, 1):
        if not isinstance(k, dict) or not isinstance(k.get("nomor"), str) or not POLA_NOMOR.match(k["nomor"]):
            masalah.append("Kriteria baris %d: nomor harus 1-8 huruf atau angka (boleh titik), mis. 1, 2.1, C" % i)
        elif k["nomor"] in nomor:
            masalah.append("Kriteria baris %d: nomor %s sudah dipakai" % (i, k["nomor"]))
        else:
            nomor.add(k["nomor"])
        if not isinstance(k, dict) or not _teks(k.get("nama")):
            masalah.append("Kriteria baris %d: nama harus diisi, paling panjang %d karakter, tanpa < > dan karakter "
                           "kendali" % (i, MAKS_NAMA))
    halaman = data.get("halaman")
    if not isinstance(halaman, dict):
        return masalah + ["halaman harus objek {id halaman: [nomor kriteria]}"]
    for id_, daftar in halaman.items():
        if id_ not in halaman_ada:
            masalah.append("halaman %r tidak dikenal" % id_)
        elif not isinstance(daftar, list) or not daftar or not all(x in nomor for x in daftar) \
                or len(set(daftar)) != len(daftar):
            masalah.append("kriteria halaman %r harus nomor kriteria di atas, tanpa ganda" % id_)
    for teks in [data.get("nama"), data.get("instrumen")] + [k.get("nama") for k in kriteria if isinstance(k, dict)]:
        istilah = saringan_spam.cari(teks) if isinstance(teks, str) else None
        if istilah:
            masalah.append("memuat teks %s (%s)" % (saringan_spam.jenis(istilah), istilah))
    return masalah


def baca_prodi(kode):
    """A programme's own criteria ({} when its admin never set them)."""
    return lokasi.baca(berkas_prodi(kode)) or {}


def simpan_prodi(kode, data, halaman_ada, oleh, aksi):
    """Check and store a programme's own criteria (the previous version stays in the history). Pages without criteria
    are left out; a body without criteria clears the labels (the shared file applies again)."""
    bersih = {"nama": data.get("nama", ""), "instrumen": data.get("instrumen", ""),
              "kriteria": list(data.get("kriteria") or []),
              "halaman": {k: v for k, v in (data.get("halaman") or {}).items() if v}}
    masalah = periksa_prodi(bersih, halaman_ada)
    if masalah:
        raise GagalKriteria("; ".join(masalah))
    if not bersih["kriteria"] and bersih["halaman"]:
        raise GagalKriteria("isi daftar kriteria dulu sebelum mencentang halaman")
    lokasi.tulis(berkas_prodi(kode), bersih, oleh, "Kriteria akreditasi", aksi)


def hapus_prodi(kode, oleh):
    """Drop a programme's own criteria (kept in the history)."""
    lokasi.tulis(berkas_prodi(kode), {}, oleh, "Kriteria akreditasi", "kriteria dikosongkan")


def untuk_prodi(kode, data, nama_lembaga, halaman_ada):
    """(body, problems) whose labels a programme's site shows: its own criteria when they have any (K-P33), otherwise a
    body confirmed in the shared file (K-P29). Own criteria that do not pass periksa_prodi() show nothing."""
    sendiri = baca_prodi(kode)
    if sendiri.get("kriteria"):
        masalah = periksa_prodi(sendiri, halaman_ada)
        return (None, masalah) if masalah else (sendiri, [])
    return lembaga_untuk(data, nama_lembaga), []


def usulan(data):
    """The bodies of the shared file that have a criteria list, drafts too: starting points for a programme's form."""
    return [lb for lb in (data or {}).get("lembaga", []) if lb.get("kriteria")]


def dari_usulan(lembaga):
    """A programme's criteria filled from a body of the shared file (copied: the form changes it)."""
    return {"nama": lembaga["nama"], "instrumen": lembaga["instrumen"], "kriteria": copy.deepcopy(lembaga["kriteria"]),
            "halaman": copy.deepcopy(lembaga.get("halaman") or {})}


def lembaga_untuk(data, nama_lembaga, termasuk_draf=False):
    """The entry of a programme's accreditation body (its "lembaga_akreditasi"), or None: unknown, or not confirmed yet
    (termasuk_draf: drafts too, for the review table)."""
    if not data or not nama_lembaga:
        return None
    kunci = _kunci(nama_lembaga)
    for lb in data.get("lembaga", []):
        if any(_kunci(a) == kunci for a in lb.get("alias", [])):
            return lb if termasuk_draf or lb.get("status") == "dikonfirmasi" else None
    return None


def label(lembaga, id_halaman):
    """[(nomor, nama)] of the criteria a page serves under a body (empty without a confirmed body)."""
    if not lembaga:
        return []
    nama = {k["nomor"]: k["nama"] for k in lembaga.get("kriteria", [])}
    return [(n, nama[n]) for n in lembaga.get("halaman", {}).get(id_halaman, []) if n in nama]


def peta(lembaga, halaman_ada=None):
    """[(nomor, nama, [page id, ...])] in the instrument's order: the pages of every criterion (halaman_ada: only these
    pages, e.g. the ones a programme's site has)."""
    if not lembaga:
        return []
    hasil = []
    for k in lembaga.get("kriteria", []):
        ids = [id_ for id_, daftar in lembaga.get("halaman", {}).items() if k["nomor"] in daftar
               and (halaman_ada is None or id_ in halaman_ada)]
        hasil.append((k["nomor"], k["nama"], ids))
    return hasil


def tabel_markdown(data, label_halaman, urutan):
    """The mapping of every body as Markdown tables (pages in menu order), for LPMPP to check."""
    baris = []
    for lb in data.get("lembaga", []):
        baris.append("### %s — %s (%s)" % (lb["nama"], lb["instrumen"], "dikonfirmasi %s oleh %s" % (
            lb["dikonfirmasi"]["tanggal"], lb["dikonfirmasi"]["oleh"]) if lb["status"] == "dikonfirmasi" else "draf"))
        baris.append("")
        baris.append("Nilai `lembaga_akreditasi` di data resmi: %s." % ", ".join("`%s`" % a for a in lb["alias"]))
        baris.append("")
        if not lb.get("kriteria"):
            baris.append("Daftar kriteria belum ada: menunggu daftar dari LPMPP.")
            baris.append("")
            continue
        baris.append("| Kriteria | Halaman |")
        baris.append("|---|---|")
        for nomor, nama, ids in peta(lb):
            ids = sorted(ids, key=lambda x: urutan.index(x) if x in urutan else 99)
            baris.append("| %s. %s | %s |" % (nomor, nama, ", ".join(label_halaman.get(x, x) for x in ids) or "—"))
        tanpa = [x for x in urutan if x not in lb.get("halaman", {})]
        baris.append("")
        baris.append("Halaman tanpa kriteria: %s." % (", ".join(label_halaman.get(x, x) for x in tanpa) or "—"))
        baris.append("")
    return "\n".join(baris).rstrip() + "\n"


def main(argv=None):
    sys.path.insert(0, PLATFORM)
    sys.path.insert(0, os.path.join(PLATFORM, "bangun"))
    import isi_halaman
    import menu as menu_mod
    perintah = (argv if argv is not None else sys.argv[1:]) or ["periksa"]
    data = baca()
    if perintah[0] == "periksa":
        masalah = periksa(data, set(isi_halaman.TEMPLAT))
        for m in masalah:
            print("GAGAL", m)
        print("kriteria: %d lembaga, %s" % (len(data.get("lembaga", [])), "sah" if not masalah else "%d masalah" % len(masalah)))
        return 1 if masalah else 0
    if perintah[0] == "tabel":
        semua = menu_mod.semua_butir(menu_mod.baca_templat())
        urutan = [b["id"] for b in menu_mod.halaman(menu_mod.susun(menu_mod.baca_templat())) if b["id"] in isi_halaman.TEMPLAT]
        print(tabel_markdown(data, {k: b["label"] for k, b in semua.items()}, urutan), end="")
        return 0
    print("perintah: periksa | tabel")
    return 2


if __name__ == "__main__":
    sys.exit(main())
