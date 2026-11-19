# -*- coding: utf-8 -*-
"""The English version of a programme's own pages (Fase 5 langkah 2, K-P37).

A page's English version is stored as a page of its own (isi_halaman.EN, "<id>:en"), written, submitted, published
and kept in the history like any page (K-P24). Its content is a translation memory, not a copy of the page:

    {"teks": {Indonesian text: English text}, "asal": {field outside a list: the Indonesian text it translated}}

The English page is the Indonesian published content with its texts replaced (terjemahkan()): the structure, the
rows, numbers, years, links, files and embeds stay those of the Indonesian version, so a row added, removed or moved
there is never matched with another row's translation. A text is looked up by what it says, so the same text is
translated once for the whole page. Fields of a template node with terjemah=False (names, codes) are shown as written;
"boleh" (titles of works) as written unless translated; the others need a translation: until they have one, a field
outside a list keeps the translation of what it said before (asal; the page is marked "perlu diperbarui"), and an item
of a list whose required text is not translated yet is left out of the English page.

    perlu_terjemah(templat, isi)      the texts of a content to translate (form, coverage)
    terjemahkan(templat, isi, en)     the content the English page shows
    cakupan(templat, isi, en)         (texts to translate, texts translated): "perlu diperbarui" when they differ
    keadaan(kode, id_)                the English version's state for the admin's lists
"""
from __future__ import print_function

import os
import sys

PLATFORM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLATFORM)

import isi_halaman as ih  # noqa: E402

# the alternative text of a photo: translated when the programme did, else as written (a photo is never left out)
NODE_ALT = ih.teks("Teks alternatif foto", maks=200, terjemah="boleh")
_HILANG = object()


def id_en(id_halaman):
    return id_halaman + ih.EN


def kosong_en():
    return {"teks": {}, "asal": {}}


def rapi(en):
    """A translation memory in its stored shape (whatever was stored)."""
    en = en if isinstance(en, dict) else {}
    return {"teks": dict(en["teks"]) if isinstance(en.get("teks"), dict) else {},
            "asal": dict(en["asal"]) if isinstance(en.get("asal"), dict) else {}}


def perlu_terjemah(templat, isi):
    """The texts of some Indonesian content the English version translates, in order:
    [{"jalur", "tempat" (where, in words), "teks", "node", "dalam_daftar", "lewat_excel", "kunci"}]."""
    hasil = []

    def jalan(node, v, jalur, tempat, dalam, excel):
        j = node["jenis"]
        if j == "objek":
            if isinstance(v, dict):
                for k, n in node["bidang"]:
                    label = n.get("label") or "Uraian"
                    jalan(n, v.get(k), "%s.%s" % (jalur, k) if jalur else k,
                          "%s, %s" % (tempat, label) if tempat else label, dalam, excel)
        elif j == "daftar":
            if isinstance(v, list):
                kata = "baris" if node["tampil"] == "tabel" else "butir"
                for i, x in enumerate(v):
                    jalan(node["isi"], x, "%s.%d" % (jalur, i), "%s %s %d" % (tempat, kata, i + 1), True,
                          excel or bool(node.get("lewat_excel")))
        elif j == "teks":
            if node.get("terjemah", True) is not False and isinstance(v, str) and v.strip():
                hasil.append({"jalur": jalur, "tempat": tempat, "teks": v, "node": node, "dalam_daftar": dalam,
                              "lewat_excel": excel, "kunci": ih.kunci_teks(v)})
        elif j == "foto":
            alt = v.get("alt") if isinstance(v, dict) else None
            if isinstance(alt, str) and alt.strip():
                hasil.append({"jalur": jalur + ".alt", "tempat": "%s, teks alternatif" % tempat, "teks": alt,
                              "node": NODE_ALT, "dalam_daftar": dalam, "lewat_excel": excel, "kunci": ih.kunci_teks(alt)})
    jalan(templat, isi if isinstance(isi, dict) else {}, "", "", False, False)
    return hasil


def cari(en, jalur, teks, dalam_daftar):
    """(English text, "segar" | "lama") of a text, or (None, None). "lama": a field outside a list whose Indonesian
    text changed since it was translated; its old translation stays until it is translated again."""
    teks_en = en.get("teks") or {}
    if teks in teks_en:
        return teks_en[teks], "segar"
    if not dalam_daftar:
        lama = (en.get("asal") or {}).get(jalur)
        if lama is not None and lama in teks_en:
            return teks_en[lama], "lama"
    return None, None


def terjemahkan(templat, isi, en):
    """The content the English page shows: the Indonesian content (checked, published) with its texts translated."""
    en = rapi(en)

    def alih(node, v, jalur, dalam):
        j = node["jenis"]
        if j == "objek":
            if not isinstance(v, dict):
                return v
            hasil = dict(v)
            for k, n in node["bidang"]:
                if k not in v:
                    continue
                x = alih(n, v[k], "%s.%s" % (jalur, k) if jalur else k, dalam)
                if x is _HILANG:
                    if dalam and n.get("wajib"):
                        return _HILANG                     # a required text without translation: the item waits
                    hasil[k] = None
                else:
                    hasil[k] = x
            return hasil
        if j == "daftar":
            if not isinstance(v, list):
                return v
            return [y for y in (alih(node["isi"], x, "%s.%d" % (jalur, i), True) for i, x in enumerate(v))
                    if y is not _HILANG]
        if j == "teks":
            cara = node.get("terjemah", True)
            if cara is False or not isinstance(v, str) or not v.strip():
                return v
            teks_en, _jenis = cari(en, jalur, v, dalam)
            if teks_en is not None:
                return teks_en
            return v if cara == "boleh" else _HILANG
        if j == "foto" and isinstance(v, dict) and isinstance(v.get("alt"), str):
            teks_en, _jenis = cari(en, jalur + ".alt", v["alt"], dalam)
            return dict(v, alt=teks_en) if teks_en is not None else v
        return v
    hasil = alih(templat, isi if isinstance(isi, dict) else {}, "", False)
    return hasil if isinstance(hasil, dict) else {}


def cakupan(templat, isi, en):
    """(texts that need a translation, of which translated now) of some Indonesian content: the different texts of
    the fields that are always translated (terjemah=True); "boleh" fields and photo texts do not count."""
    en = rapi(en)
    perlu = {t["teks"] for t in perlu_terjemah(templat, isi) if t["node"].get("terjemah", True) is True}
    return len(perlu), sum(1 for t in perlu if t in en["teks"])


def keadaan(kode, id_halaman, k_id=None):
    """The English version's state (isi_halaman.keadaan of "<id>:en") with "perlu": texts of the Indonesian published
    content not translated in the English published one, "tayang": the English page shows on a site that has the
    English version switched on (both versions published and valid). k_id: the Indonesian page's keadaan, when the
    caller has it already."""
    k_id = ih.keadaan(kode, id_halaman) if k_id is None else k_id
    k = ih.keadaan(kode, id_en(id_halaman))
    isi_id = (k_id["terbit"] or {}).get("isi")
    k["perlu"] = 0
    if k["terbit"] is not None and isinstance(isi_id, dict):
        perlu, ada = cakupan(ih.templat_halaman(id_halaman), isi_id, k["terbit"].get("isi"))
        k["perlu"] = perlu - ada
    k["tayang"] = bool(k["tayang"] and k_id["tayang"])
    return k


def isi_sumber(kode, id_halaman):
    """The Indonesian content an English form translates: the draft (what the writers are working on), else the
    published content; and the Indonesian page's version (to notice a change while translating)."""
    data = ih.baca(kode, id_halaman)
    return ih.isi_kerja(data), data.get("versi", 0)


def butir_formulir(templat, isi_id, en):
    """The fields of the English form: one per different text (the first place it appears), lists kept in spreadsheets
    left out. [{"kunci", "tempat", "teks", "panjang", "kaya", "maks", "wajib", "boleh", "nilai", "jenis"}]; jenis:
    "segar" (translated), "lama" (the Indonesian text changed: the old translation is offered in the field, marked to
    be checked; saving the form confirms it), None (new)."""
    en = rapi(en)
    hasil, sudah = [], set()
    for t in perlu_terjemah(templat, isi_id):
        if t["lewat_excel"] or t["teks"] in sudah:
            continue
        sudah.add(t["teks"])
        nilai, jenis = cari(en, t["jalur"], t["teks"], t["dalam_daftar"])
        n = t["node"]
        # an English text may be longer than the Indonesian one; the stored limit is MAKS_TEKS_EN
        maks = ih.MAKS_TEKS_EN if n.get("panjang") else min(ih.MAKS_TEKS_EN, max(2 * n.get("maks", 300), 100))
        hasil.append({"kunci": t["kunci"], "tempat": t["tempat"], "teks": t["teks"], "panjang": bool(n.get("panjang")),
                      "kaya": bool(n.get("kaya")), "maks": maks,
                      "wajib": n.get("terjemah", True) is True, "boleh": n.get("terjemah", True) == "boleh",
                      "nilai": nilai or "", "jenis": jenis, "jalur": t["jalur"], "dalam_daftar": t["dalam_daftar"]})
    return hasil


def dari_formulir(templat, en_lama, form, isi_sumber_):
    """The translation memory after a form was sent: form {"t.<kunci>": English text}; isi_sumber_: [Indonesian
    contents whose texts may stay translated] (the draft and the published content). A field left empty drops its
    translation; translations of texts in none of those contents go. Returns (memory, fields of texts that changed
    while translating: their keys did not match)."""
    en = rapi(en_lama)
    templat_ = templat
    butir = {}
    for isi in isi_sumber_:
        for t in perlu_terjemah(templat_, isi):
            butir.setdefault(t["kunci"], t)
    tak_cocok = []
    for nama, nilai in form.items():
        if not nama.startswith("t."):
            continue
        t = butir.get(nama[2:])
        if t is None:
            if (nilai or "").strip():
                tak_cocok.append(nama)
            continue
        nilai = (nilai or "").replace("\r\n", "\n").strip()
        if not t["node"].get("panjang"):
            nilai = " ".join(nilai.split())
        if nilai:
            en["teks"][t["teks"]] = nilai
            if not t["dalam_daftar"]:
                en["asal"][t["jalur"]] = t["teks"]
        else:
            en["teks"].pop(t["teks"], None)
            if not t["dalam_daftar"]:
                en["asal"].pop(t["jalur"], None)
    ada = {t["teks"] for isi in isi_sumber_ for t in perlu_terjemah(templat_, isi)}
    asal_ada = {t["jalur"] for isi in isi_sumber_ for t in perlu_terjemah(templat_, isi) if not t["dalam_daftar"]}
    dipakai = ada | {s for j, s in en["asal"].items() if j in asal_ada}
    en["teks"] = {s: e for s, e in en["teks"].items() if s in dipakai}
    en["asal"] = {j: s for j, s in en["asal"].items() if j in asal_ada and s in en["teks"]}
    return en, tak_cocok
