# -*- coding: utf-8 -*-
"""The master menu of every programme site (platform/template/menu.json) and a programme's own menu settings.

A programme admin may (rencana §7, K-P2):
- rename any item or group (label, 1-60 characters, no gambling text);
- reorder the items inside a group (groups keep their order, so every site reads the same);
- hide an item marked "opsional". Items marked "wajib" (needed for accreditation) or "otomatis" always stay.
An optional item marked "bila_terisi" is on a site only while the programme has published its content (the builder
leaves it out otherwise), so a page few programmes use (Tugas Akhir) never shows empty on the others.

Settings live in prodi/<kode>/situs.json under "menu": {"<id>": {"label": "...", "urutan": 2, "sembunyi": true}}.
A programme's extra pages (K-P35, halaman_tambahan.py) follow the pages of the group they belong to.
"""
from __future__ import print_function

import io
import json
import os
import re
import sys

BANGUN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(BANGUN)
MENU_JSON = os.path.join(PLATFORM, "template", "menu.json")
sys.path.insert(0, os.path.join(PLATFORM, "pemantau"))

import saringan_spam  # noqa: E402

JENIS = ("otomatis", "wajib", "opsional")
TEMPLAT = ("beranda", "akreditasi", "profil_lulusan", "spesifikasi", "kalender", "dosen", "kontak", "pengumuman")
POLA_ID = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
POLA_ALAMAT = re.compile(r"^([a-z][a-z0-9-]*(/[a-z][a-z0-9-]*)*)?$")
MAKS_LABEL = 60


class GagalMenu(ValueError):
    pass


def _periksa_butir(b, induk, masalah, id_dipakai, alamat_dipakai):
    if not isinstance(b, dict) or not POLA_ID.match(str(b.get("id", ""))):
        masalah.append("butir tanpa id yang sah: %r" % (b,))
        return
    if b["id"] in id_dipakai:
        masalah.append("id ganda: %s" % b["id"])
    id_dipakai.add(b["id"])
    if not POLA_ALAMAT.match(str(b.get("alamat", "-"))):
        masalah.append("%s: alamat tidak sah" % b["id"])
    elif b["alamat"] in alamat_dipakai:
        masalah.append("%s: alamat ganda %r" % (b["id"], b["alamat"]))
    alamat_dipakai.add(b.get("alamat"))
    if induk and not str(b.get("alamat", "")).startswith(induk["alamat"] + "/"):
        masalah.append("%s: alamat harus di bawah %s/" % (b["id"], induk["alamat"]))
    if not b.get("label") or not b.get("deskripsi"):
        masalah.append("%s: label dan deskripsi wajib" % b["id"])
    if "anak" in b:
        if induk:
            masalah.append("%s: kelompok tidak boleh bersarang" % b["id"])
        for a in b["anak"]:
            _periksa_butir(a, b, masalah, id_dipakai, alamat_dipakai)
    else:
        if b.get("jenis") not in JENIS:
            masalah.append("%s: jenis harus salah satu dari %s" % (b["id"], ", ".join(JENIS)))
        if b.get("jenis") == "otomatis" and b.get("templat") not in TEMPLAT:
            masalah.append("%s: halaman otomatis perlu templat yang dikenal" % b["id"])
        if b.get("bila_terisi") and b.get("jenis") != "opsional":
            masalah.append("%s: hanya halaman opsional yang tampil bila terisi" % b["id"])


def baca_templat(path=MENU_JSON):
    """The master menu, checked. Raises GagalMenu listing every problem."""
    with io.open(path, encoding="utf-8") as f:
        menu = json.load(f)["menu"]
    masalah = []
    id_dipakai, alamat_dipakai = set(), set()
    for b in menu:
        _periksa_butir(b, None, masalah, id_dipakai, alamat_dipakai)
    if "" not in alamat_dipakai:
        masalah.append("perlu satu halaman beranda (alamat kosong)")
    if masalah:
        raise GagalMenu("; ".join(masalah))
    return menu


def semua_butir(templat):
    """Every item and group of the master menu by id."""
    hasil = {}
    for b in templat:
        hasil[b["id"]] = b
        for a in b.get("anak", []):
            hasil[a["id"]] = a
    return hasil


def periksa_pengaturan(templat, pengaturan):
    """Problems with a programme's menu settings (empty list when they can be used)."""
    if pengaturan in (None, {}):
        return []
    if not isinstance(pengaturan, dict):
        return ["pengaturan menu harus berupa objek"]
    butir = semua_butir(templat)
    masalah = []
    for id_, atur in pengaturan.items():
        b = butir.get(id_)
        if b is None:
            masalah.append("butir menu %r tidak ada di template" % id_)
            continue
        if not isinstance(atur, dict) or set(atur) - {"label", "urutan", "sembunyi"}:
            masalah.append("%s: hanya label, urutan, dan sembunyi yang bisa diatur" % id_)
            continue
        label = atur.get("label")
        if label is not None:
            if not isinstance(label, str) or not label.strip() or len(label.strip()) > MAKS_LABEL:
                masalah.append("%s: label harus 1-%d karakter" % (id_, MAKS_LABEL))
            elif saringan_spam.cari(label):
                masalah.append("%s: label memuat istilah terlarang" % id_)
            elif re.search(r"[<>\x00-\x1f]", label):
                masalah.append("%s: label memuat karakter terlarang" % id_)
        if "urutan" in atur and (not isinstance(atur["urutan"], int) or isinstance(atur["urutan"], bool)
                                 or not 0 <= atur["urutan"] <= 99):
            masalah.append("%s: urutan harus angka 0-99" % id_)
        if atur.get("sembunyi") and b.get("jenis") != "opsional":
            masalah.append("%s: hanya butir opsional yang bisa disembunyikan" % id_)
        if "urutan" in atur and "anak" in b:
            masalah.append("%s: urutan kelompok tidak bisa diubah" % id_)
    return masalah


def susun(templat, pengaturan=None, tambahan=()):
    """The menu of one programme site: labels and order applied, hidden items removed, then the programme's extra
    pages (tambahan: [(group id, entry)], halaman_tambahan.butir_menu) after the pages of their group.

    Returns a list of entries {"id", "label", "alamat", "deskripsi", "jenis", "templat", "nav", "kelompok", "anak"}:
    "kelompok" is True for a group, whose pages are in "anak" (empty for a page). Raises GagalMenu when the settings are not valid (the builder then stops for this
    programme rather than publishing a menu that breaks the rules)."""
    pengaturan = pengaturan or {}
    masalah = periksa_pengaturan(templat, pengaturan)
    if masalah:
        raise GagalMenu("; ".join(masalah))

    def jadi(b):
        atur = pengaturan.get(b["id"], {})
        return {"id": b["id"], "label": (atur.get("label") or b["label"]).strip(), "label_asli": b["label"],
                "alamat": b["alamat"], "deskripsi": b["deskripsi"], "jenis": b.get("jenis"),
                "templat": b.get("templat"), "nav": b.get("nav", True), "kelompok": "anak" in b, "anak": [],
                "bila_terisi": bool(b.get("bila_terisi"))}

    hasil = []
    for b in templat:
        e = jadi(b)
        if "anak" in b:
            # an order the admin chose wins over a default position with the same number
            anak = [(pengaturan.get(a["id"], {}).get("urutan", i), "urutan" not in pengaturan.get(a["id"], {}), i, a)
                    for i, a in enumerate(b["anak"]) if not pengaturan.get(a["id"], {}).get("sembunyi")]
            e["anak"] = [jadi(x[3]) for x in sorted(anak, key=lambda x: x[:3])]
            e["anak"] += [dict(x) for induk, x in tambahan if induk == b["id"]]
        hasil.append(e)
    return hasil


def halaman(menu):
    """Every page of a built menu (groups included, as their index pages), in menu order."""
    for e in menu:
        yield e
        for a in e.get("anak", []):
            yield a
