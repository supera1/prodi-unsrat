# -*- coding: utf-8 -*-
"""A programme's extra pages (K-P35): pages its admin adds to a group of the menu, beside the accreditation pages.

prodi/<kode>/tambahan.json (lokasi.py):
    {"halaman": [{"id": "x1a2b3c", "label": "Database Skripsi", "kelompok": "akademik", "alamat": "database-skripsi",
                  "dibuat": {"oleh", "waktu"}}, ...]}
in menu order within each group. A page's content is a page of isi_halaman.py (prodi/<kode>/halaman-<id>.json,
template TEMPLAT_TAMBAHAN: text, embedded content, PDFs, photos, links), written, submitted and published like the
others (K-P24). The site lists an extra page after the group's own pages, once it has published content; its address
is /<slug>/halaman/<alamat>/, fixed when the page is made, so links people shared keep working while its label and
group change. At most MAKS pages per programme.
"""
from __future__ import print_function

import datetime
import os
import re
import secrets
import sys
import unicodedata

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))
sys.path.insert(0, os.path.join(PLATFORM, "bangun"))

import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import saringan_spam  # noqa: E402

MAKS = 10
MAKS_LABEL = menu_mod.MAKS_LABEL
AWALAN = "halaman"                      # the folder of the extra pages on a programme's site
POLA_ID = re.compile(r"^x[0-9a-f]{6}$")
POLA_ALAMAT = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MAKS_ALAMAT = 40
LARANGAN = re.compile(r"[<>\x00-\x1f\x7f]")


class GagalTambahan(ValueError):
    """A change of the extra pages was refused; the message is shown to the programme's admin."""


def berkas(kode):
    return "prodi/%s/tambahan" % kode


def kelompok_ada(templat=None):
    """{id: label} of the master menu's groups that have pages: where an extra page may go."""
    return {b["id"]: b["label"] for b in (templat or menu_mod.baca_templat()) if b.get("anak")}


def baca(kode):
    """The programme's extra pages, in order ([] when it has none)."""
    data = lokasi.baca(berkas(kode)) or {}
    daftar = data.get("halaman") if isinstance(data, dict) else None
    return daftar if isinstance(daftar, list) else []


def periksa(daftar, kelompok=None):
    """Problems of a list of extra pages, as messages for the programme's admin (empty when it may be used)."""
    kelompok = kelompok if kelompok is not None else kelompok_ada()
    if not isinstance(daftar, list):
        return ["daftar halaman tambahan harus berupa daftar"]
    masalah = []
    if len(daftar) > MAKS:
        masalah.append("paling banyak %d halaman tambahan" % MAKS)
    id_, alamat, label = set(), set(), set()
    for i, h in enumerate(daftar, 1):
        if not isinstance(h, dict) or not POLA_ID.match(str(h.get("id", ""))):
            masalah.append("halaman tambahan %d: id tidak sah" % i)
            continue
        nama = h.get("label")
        di = "Halaman tambahan %r" % (nama if isinstance(nama, str) else h["id"])
        if h["id"] in id_:
            masalah.append("%s: id ganda" % di)
        id_.add(h["id"])
        if not isinstance(nama, str) or not nama.strip() or nama != nama.strip() or len(nama) > MAKS_LABEL:
            masalah.append("%s: nama menu harus 1-%d karakter" % (di, MAKS_LABEL))
        elif LARANGAN.search(nama):
            masalah.append("%s: nama menu memuat karakter yang tidak boleh" % di)
        elif saringan_spam.cari(nama):
            masalah.append("%s: nama menu memuat teks %s" % (di, saringan_spam.jenis(saringan_spam.cari(nama))))
        elif nama.lower() in label:
            masalah.append("%s: nama menu sudah dipakai halaman tambahan lain" % di)
        if isinstance(nama, str):
            label.add(nama.lower())
        if h.get("kelompok") not in kelompok:
            masalah.append("%s: kelompok menu tidak dikenal" % di)
        a = h.get("alamat")
        if not isinstance(a, str) or not POLA_ALAMAT.match(a) or len(a) > MAKS_ALAMAT:
            masalah.append("%s: alamat harus 2-%d huruf kecil, angka, atau tanda hubung, diawali huruf"
                           % (di, MAKS_ALAMAT))
        elif a in alamat:
            masalah.append("%s: alamat %s sudah dipakai halaman tambahan lain" % (di, a))
        else:
            alamat.add(a)
    return masalah


def simpan(kode, daftar, oleh, aksi):
    """Check and store the list (the previous version stays in the history)."""
    masalah = periksa(daftar)
    if masalah:
        raise GagalTambahan("; ".join(masalah))
    lokasi.tulis(berkas(kode), {"halaman": daftar}, oleh, "Halaman tambahan", aksi)


def alamat_dari(label):
    """An address made from a page's name: "Database Skripsi/TA" -> "database-skripsi-ta"."""
    t = unicodedata.normalize("NFKD", label or "").encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:MAKS_ALAMAT].strip("-")
    if t and not t[0].isalpha():
        t = ("h-" + t)[:MAKS_ALAMAT].strip("-")
    return t if len(t) >= 2 else "halaman"


def _id_baru(daftar):
    dipakai = {h.get("id") for h in daftar if isinstance(h, dict)}
    while True:
        id_ = "x" + secrets.token_hex(3)
        if id_ not in dipakai:
            return id_


def tambah(kode, label, kelompok, alamat, oleh):
    """Add a page at the end of its group; returns it. alamat: as typed, or made from the label when empty."""
    daftar = list(baca(kode))
    label = (label or "").strip()
    alamat = (alamat or "").strip().lower() or alamat_dari(label)
    h = {"id": _id_baru(daftar), "label": label, "kelompok": kelompok, "alamat": alamat,
         "dibuat": {"oleh": oleh, "waktu": datetime.datetime.now().isoformat(timespec="seconds")}}
    simpan(kode, daftar + [h], oleh, "tambah halaman %s" % alamat)
    return h


def ubah(kode, perubahan, oleh):
    """Change the label, the group and the order of the pages: perubahan {id: {"label", "kelompok", "urutan"}}.
    Pages keep their address. Pages without a new position keep theirs relative to the others."""
    daftar = []
    for i, h in enumerate(baca(kode)):
        p = perubahan.get(h.get("id"), {})
        baru = dict(h)
        if "label" in p:
            baru["label"] = (p["label"] or "").strip()
        if "kelompok" in p:
            baru["kelompok"] = p["kelompok"]
        urutan = p.get("urutan", i)
        if not isinstance(urutan, int) or isinstance(urutan, bool) or not 0 <= urutan <= 99:
            raise GagalTambahan("urutan harus angka 0-99")
        daftar.append((urutan, "urutan" not in p, i, baru))
    simpan(kode, [x[3] for x in sorted(daftar, key=lambda x: x[:3])], oleh, "ubah halaman tambahan")


def hapus(kode, id_, oleh):
    """Take a page off the list (its content stays in the history); returns it, or None when it is not there."""
    daftar = baca(kode)
    sisa = [h for h in daftar if h.get("id") != id_]
    if len(sisa) == len(daftar):
        return None
    lama = [h for h in daftar if h.get("id") == id_][0]
    simpan(kode, sisa, oleh, "hapus halaman %s" % lama.get("alamat"))
    return lama


def butir_menu(h):
    """An extra page as an entry of a built menu (menu.susun)."""
    return {"id": h["id"], "label": h["label"], "label_asli": h["label"], "alamat": "%s/%s" % (AWALAN, h["alamat"]),
            "deskripsi": h["label"] + ".", "jenis": "tambahan", "templat": None, "nav": True, "kelompok": False,
            "anak": []}
