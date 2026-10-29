# -*- coding: utf-8 -*-
"""The form of a programme's own pages (Fase 2 langkah 2), built from the page's content template (isi_halaman.TEMPLAT).

Adapted from www's schema-driven form editor (site/admin/editor.py, see docs/asal-modul.md): dotted field names
("kerja_sama.0.mitra"), lists that grow, shrink and are reordered with submit buttons (no JavaScript), list items
folded in <details>, uploads in "berkas::<path>" fields, keys the template does not know kept. What differs here:
- the nodes are isi_halaman's (persen, centang, dokumen and foto added); a list item is named by its first values;
- a value that is not valid yet (a year typed "20o5") is kept as typed, so a draft never loses what was typed: the
  checks of isi_halaman mark it, and the page cannot be published until it is fixed;
- uploads go through media.py (PDFs checked, photos re-encoded) into the programme's own files. File records never
  come from the form, only from what is stored and from the files uploaded in this request;
- the labels and buttons of a list item say which item they belong to, for screen readers ("Mitra, baris 3").
"""
from __future__ import print_function

import html
import os
import re
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))
sys.path.insert(0, os.path.join(os.path.dirname(ADMIN), "bangun"))

from bangun import ukuran  # noqa: E402

import isi_halaman as ih  # noqa: E402
import media  # noqa: E402
import sematan  # noqa: E402

UNGGAHAN = ("dokumen", "foto")
AKSI_DAFTAR = ("tambah", "hapus", "naik", "turun")
POLA_JALUR = re.compile(r"^[a-z][a-z_]*(\.([0-9]{1,4}|[a-z][a-z_]*))*$")
RIBUAN = re.compile(r"^-?[0-9]{1,3}(\.[0-9]{3})+$")          # 1.234.567
BULAT = re.compile(r"^-?[0-9]{1,9}$")
PECAHAN = re.compile(r"^[0-9]{1,3}([.,][0-9]+)?$")           # 87,5
TAUTAN_MD = re.compile(r"\[([^\]\n]+)\]\([^)\s]*\)")


# ------------------------------------------------------------------ paths and names

def _id(path):
    # keys are [a-z_] and indexes digits, so "." -> "-" keeps ids apart
    return "f-" + path.replace(".", "-")


def _e(t):
    return html.escape("" if t is None else str(t), quote=True)


def kata_butir(node):
    """How the items of a list are called: rows of a table, items of anything else (as isi_halaman's messages)."""
    return "baris" if node["tampil"] == "tabel" else "butir"


def label_jalur(templat, path):
    """A field's place in words, in the wording of isi_halaman's checks ("Daftar kerja sama baris 1, Mitra")."""
    node, nama = templat, ""
    for p in path.split("."):
        if node["jenis"] == "objek":
            node = dict(node["bidang"])[p]
            label = node.get("label") or "Uraian"
            nama = "%s, %s" % (nama, label) if nama else label
        elif node["jenis"] == "daftar":
            nama = "%s %s %d" % (nama, kata_butir(node), int(p) + 1)
            node = node["isi"]
    return nama


def ambil(isi, path):
    """The value at a path, or None."""
    for p in path.split(".") if path else []:
        if isinstance(isi, dict):
            isi = isi.get(p)
        elif isinstance(isi, list) and p.isdigit() and int(p) < len(isi):
            isi = isi[int(p)]
        else:
            return None
    return isi


def masalah_tampil(templat, isi, masalah):
    """The problems worth marking in the form ([(path, where, problem)] of isi_halaman.daftar_masalah): not those
    inside a list item that is still entirely empty (a row just added); saving the draft drops such items."""
    hasil = []
    for jalur, tempat, pesan in masalah:
        node, bagian, kosong = templat, jalur.split(".") if jalur else [], False
        for n, p in enumerate(bagian):
            if node["jenis"] == "objek":
                node = dict(node["bidang"]).get(p)
            elif node["jenis"] == "daftar":
                node = node["isi"]
                if ih.kosong(node, ambil(isi, ".".join(bagian[:n + 1]))):
                    kosong = True
                    break
            if node is None:
                break
        if not kosong:
            hasil.append((jalur, tempat, pesan))
    return hasil


# ------------------------------------------------------------------ rendering

class Tampil(object):
    """What rendering needs besides the values: the problem of each field, the address of a stored file, the list
    items to show open, the item just removed (offered back), the page's spreadsheet import (lists kept in a
    spreadsheet link there)."""

    def __init__(self, galat=None, url_berkas=lambda rekam: "", buka=(), dihapus=None, url_impor=None):
        self.galat, self.url_berkas, self.buka, self.dihapus = galat or {}, url_berkas, set(buka), dihapus
        self.url_impor = url_impor


def _tersembunyi(teks):
    return '<span class="tersembunyi">%s</span>' % _e(teks) if teks else ""


def _keterangan(node, path, t, tambahan=""):
    """The help text and the problem of a field, and the aria-describedby that points at them. A help text's line breaks
    are kept (the steps of isi_halaman.CARA_SEMATAN)."""
    bantuan = " ".join(x for x in (node.get("bantuan") or "", tambahan) if x)
    ids, isi = [], ""
    if bantuan:
        ids.append(_id(path) + "-bantuan")
        isi += '<p class="keterangan" id="%s-bantuan">%s</p>' % (_id(path), "<br>".join(_e(b) for b in bantuan.split("\n")))
    if path in t.galat:
        ids.append(_id(path) + "-galat")
        isi += '<p class="galat-isian" id="%s-galat">%s</p>' % (_id(path), _e(t.galat[path]))
    aria = (' aria-describedby="%s"' % " ".join(ids) if ids else "") + (' aria-invalid="true"' if path in t.galat else "")
    return aria, isi


def _label(node, path, konteks, teks=None):
    # the lines of a list of lines are not marked: an empty line is simply dropped when the draft is saved
    wajib = ' <span class="wajib">(wajib)</span>' if node.get("wajib") and teks is None else ""
    return '<label for="%s">%s%s%s</label>' % (_id(path), _e(teks or node.get("label") or "Uraian"), _tersembunyi(konteks), wajib)


def _angka_teks(v):
    """A stored number as typed back into its field: 87.5 -> "87,5" (a value not valid yet stays as typed)."""
    if isinstance(v, bool) or v is None:
        return ""
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v).replace(".", ",")
    return str(v)


def _skalar(node, v, path, t, konteks, label=None):
    j = node["jenis"]
    kelas = "isian"
    if j == "centang":
        aria, ket = _keterangan(node, path, t)
        return ('<div class="isian isian--centang"><input id="%s" name="%s" type="checkbox" value="1"%s%s>%s%s</div>'
                % (_id(path), _e(path), " checked" if v is True else "", aria, _label(node, path, konteks, label), ket))
    if j == "teks":
        tambahan = "Paling banyak %s karakter." % ih.angka(node["maks"]) if node["panjang"] or node["maks"] > 300 else ""
        aria, ket = _keterangan(node, path, t, tambahan)
        nilai = v if isinstance(v, str) else _angka_teks(v)
        if node["panjang"] or node["kaya"] or node["maks"] > 300:
            baris = 10 if node["kaya"] and node["maks"] >= 3000 else (4 if node["panjang"] else 2)
            # the new line after <textarea> keeps a value's own first new line (the parser drops one)
            kontrol = '<textarea id="%s" name="%s" rows="%d"%s>\n%s</textarea>' % (_id(path), _e(path), baris, aria, _e(nilai))
        else:
            kontrol = '<input id="%s" name="%s" type="text" value="%s"%s>' % (_id(path), _e(path), _e(nilai), aria)
        tanda = ' <span class="lencana">tautan, tebal, daftar</span>' if node["kaya"] else ""
        return '<div class="%s">%s%s%s%s</div>' % (kelas, _label(node, path, konteks, label), tanda, kontrol, ket)
    aria, ket = _keterangan(node, path, t)
    if j == "pilihan":
        opsi = list(node["opsi"])
        if isinstance(v, str) and v and v not in opsi:
            opsi.append(v)                    # a value the template no longer offers stays until it is changed
        pilih = '<option value="">— pilih —</option>' + "".join(
            '<option value="%s"%s>%s</option>' % (_e(o), " selected" if o == v else "", _e(o)) for o in opsi)
        kontrol = '<select id="%s" name="%s"%s>%s</select>' % (_id(path), _e(path), aria, pilih)
        kelas += " isian--pilihan"
    elif j in ("bilangan", "persen"):
        kontrol = '<input id="%s" name="%s" type="text" inputmode="%s" value="%s"%s>' % (
            _id(path), _e(path), "numeric" if j == "bilangan" else "decimal", _e(_angka_teks(v) if not isinstance(v, str) else v), aria)
        kelas += " isian--pendek"
    elif j == "url":
        kontrol = ('<input id="%s" name="%s" type="text" inputmode="url" spellcheck="false" autocomplete="off" value="%s"%s>'
                   % (_id(path), _e(path), _e(v if isinstance(v, str) else ""), aria))
    else:
        raise ValueError("jenis isian tidak dikenal: %s" % j)
    return '<div class="%s">%s%s%s</div>' % (kelas, _label(node, path, konteks, label), kontrol, ket)


def _berkas(node, v, path, t, konteks):
    """A PDF or a photo: the stored one (with a box to take it off), a file field, and for a photo its text."""
    foto = node["jenis"] == "foto"
    ada = isinstance(v, dict) and (v.get("varian") if foto else v.get("jalur") or v.get("url"))
    aria, ket = _keterangan(node, path, t)
    isi = []
    if ada and foto:
        kecil = ih.media_isi(node, v)
        kecil = sorted(kecil, key=lambda r: r.get("lebar", 0))[0] if kecil else None
        if kecil:
            isi.append('<img class="pratinjau-kecil" src="%s" alt="%s" width="160" height="%d">' % (
                _e(t.url_berkas(kecil)), _e(v.get("alt", "")),
                round(160 * (kecil.get("tinggi") or 120) / max(1, kecil.get("lebar") or 160))))
    elif ada:
        isi.append('<p class="berkas-kini"><a href="%s">%s</a> <span class="keterangan">PDF, %s halaman, %s</span></p>' % (
            _e(t.url_berkas(v)), _e(v.get("judul") or node["label"]), _e(v.get("halaman", "?")), _e(ukuran(v.get("ukuran") or 0))))
    if ada:
        isi.append('<p><label><input type="checkbox" name="hapus::%s" value="1"> Lepas %s ini%s</label></p>' % (
            _e(path), "foto" if foto else "berkas", _tersembunyi(konteks)))
    unggah = ("Ganti foto" if ada else "Unggah foto") if foto else ("Ganti dengan PDF lain" if ada else "Unggah PDF")
    isi.append('<div class="isian"><label for="%s">%s%s</label><input id="%s" name="berkas::%s" type="file" accept="%s"%s></div>' % (
        _id(path), unggah, _tersembunyi(konteks), _id(path), _e(path),
        ".jpg,.jpeg,.png,image/jpeg,image/png" if foto else ".pdf,application/pdf", aria))
    if foto:
        isi.append('<div class="isian"><label for="%s-alt">Teks alternatif foto%s <span class="wajib">(wajib)</span></label>'
                   '<input id="%s-alt" name="alt::%s" type="text" value="%s" aria-describedby="%s-alt-bantuan">'
                   '<p class="keterangan" id="%s-alt-bantuan">Gambarkan isi foto untuk pembaca layar. Isi sebelum memilih '
                   'foto baru.</p></div>' % (_id(path), _tersembunyi(konteks), _id(path), _e(path),
                                             _e(v.get("alt", "") if ada else ""), _id(path), _id(path)))
    wajib = ' <span class="wajib">(wajib)</span>' if node.get("wajib") else ""
    return '<fieldset class="isian-berkas"><legend>%s%s%s</legend>%s%s</fieldset>' % (
        _e(node["label"]), _tersembunyi(konteks), wajib, "".join(isi), ket)


def _ringkas(isi_node, item):
    """Up to three values that name a list item ("1 · IF101 · Algoritma"), for its folded header."""
    nilai = []
    if isi_node["jenis"] != "objek":
        nilai = [item] if isinstance(item, str) else []
    elif isinstance(item, dict):
        for k, n in isi_node["bidang"]:
            x = item.get(k)
            if n["jenis"] in ("teks", "pilihan", "url") and isinstance(x, str) and x.strip():
                nilai.append(x)
            elif n["jenis"] == "bilangan" and x not in (None, "") and not isinstance(x, bool):
                nilai.append(str(x))
        if not nilai:
            nilai = [x["alt"] for k, n in isi_node["bidang"] for x in [item.get(k)]
                     if n["jenis"] == "foto" and isinstance(x, dict) and isinstance(x.get("alt"), str) and x["alt"].strip()]
    teks = " · ".join(re.sub(r"\s+", " ", TAUTAN_MD.sub(r"\1", v)).strip() for v in nilai[:3])
    return teks if len(teks) <= 90 else teks[:89] + "…"


def _tombol(aksi, label, konteks="", gaya="tombol--garis"):
    return ('<button type="submit" class="tombol tombol--kecil %s" name="aksi" value="%s" formnovalidate>%s%s</button>'
            % (gaya, _e(aksi), _e(label), _tersembunyi(konteks)))


CONTOH_EXCEL = 20             # rows of a list kept in a spreadsheet shown in the editor


def _sel(x):
    if x is True:
        return "ya"
    return "" if x in (None, False) or isinstance(x, dict) else str(x)


def _daftar_excel(node, v, path, t):
    """A list kept in a spreadsheet ("lewat_excel": thousands of final projects): its first rows, read only, and the
    way to change it, the page's spreadsheet import, instead of thousands of fields."""
    v = [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []
    kolom = [(k, n) for k, n in node["isi"]["bidang"] if n["jenis"] not in ("dokumen", "foto")]
    impor = '<a href="%s">Impor dari Excel</a>' % _e(t.url_impor) if t.url_impor else "Impor dari Excel"
    isi = ['<p>Tabel ini diubah lewat Excel karena bisa sangat panjang: %s. Unduh templatnya (berisi semua baris), ubah '
           'di Excel, unggah, lalu pilih <strong>Ganti semua baris</strong> atau <strong>Tambahkan di bawah baris yang '
           'ada</strong>.</p>' % impor]
    if v:
        isi.append('<div class="tabel-gulir"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (
            "".join('<th scope="col">%s</th>' % _e(n["label"]) for _k, n in kolom),
            "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % _e(_sel(x.get(k))) for k, _n in kolom)
                    for x in v[:CONTOH_EXCEL])))
        if len(v) > CONTOH_EXCEL:
            isi.append('<p class="keterangan">Ditampilkan %d baris pertama dari %d.</p>' % (CONTOH_EXCEL, len(v)))
    bermasalah = len({k.split(".")[1] for k in t.galat if k.startswith(path + ".") and len(k.split(".")) > 1})
    if bermasalah:
        isi.append('<p class="pesan pesan--galat">%d baris perlu diperbaiki: perbaiki di Excel lalu impor ulang dengan '
                   'Ganti semua baris.</p>' % bermasalah)
    aria, ket = _keterangan(node, path, t)
    return ('<fieldset class="daftar-sunting" id="%s"><legend>%s <span class="jumlah">(%d baris)</span></legend>%s%s'
            '</fieldset>' % (_id(path), _e(node["label"]), len(v), ket, "".join(isi)))


def _daftar(node, v, path, t):
    if node.get("lewat_excel"):
        return _daftar_excel(node, v, path, t)
    v = v if isinstance(v, list) else []
    n, isi_node, kata = len(v), node["isi"], kata_butir(node)
    objek = isi_node["jenis"] == "objek"
    butir = []
    for i, x in enumerate(v):
        p = "%s.%d" % (path, i)
        konteks = ", %s %d" % (kata, i + 1)
        ada_galat = any(k == p or k.startswith(p + ".") for k in t.galat)
        kendali = '<div class="butir-sunting__kendali">%s%s%s</div>' % (
            _tombol("naik:" + p, "Naik", " %s %d" % (kata, i + 1)) if i > 0 else "",
            _tombol("turun:" + p, "Turun", " %s %d" % (kata, i + 1)) if i < n - 1 else "",
            _tombol("hapus:" + p, "Hapus", " %s %d" % (kata, i + 1), "tombol--garis tombol--bahaya"))
        if not objek:
            # a list of lines (mission, goals): one field per line, always open
            butir.append('<div class="butir-baris%s">%s%s</div>' % (
                " butir-baris--galat" if ada_galat else "",
                _skalar(isi_node, x, p, t, "", "%s %d" % (node["label"], i + 1)), kendali))
            continue
        bidang = "".join(_render(sub, (x if isinstance(x, dict) else {}).get(k), "%s.%s" % (p, k), t, konteks)
                         for k, sub in isi_node["bidang"])
        ringkas = _ringkas(isi_node, x)
        terbuka = ada_galat or n <= 3 or p in t.buka or ih.kosong(isi_node, x)
        butir.append('<details class="butir-sunting%s" id="%s"%s><summary>%s %d%s%s</summary>%s%s</details>' % (
            " butir-sunting--galat" if ada_galat else "", _id(p), " open" if terbuka else "", _e(kata.capitalize()), i + 1,
            ": " + _e(ringkas) if ringkas else " (kosong)", " — perlu diperbaiki" if ada_galat else "", kendali, bidang))
    dihapus = ""
    if t.dihapus and t.dihapus.get("jalur") == path:
        dihapus = ('<p class="pesan pesan--info">%s %d%s baru saja dihapus. %s</p>' % (
            _e(kata.capitalize()), t.dihapus["indeks"] + 1,
            " (%s)" % _e(_ringkas(isi_node, t.dihapus["nilai"])) if _ringkas(isi_node, t.dihapus["nilai"]) else "",
            _tombol("pulihkan-butir", "Kembalikan %s itu" % kata)))
    if n < node["maks"]:
        tambah = _tombol("tambah:" + path, "Tambah %s" % (kata if kata == "baris" or not objek else isi_node["label"].lower()),
                         " ke %s" % node["label"], "")
    else:
        tambah = '<p class="keterangan">Sudah %d %s, jumlah paling banyak.</p>' % (n, kata)
    aria, ket = _keterangan(node, path, t)
    return ('<fieldset class="daftar-sunting" id="%s"><legend>%s <span class="jumlah">(%d %s)</span></legend>%s%s'
            '<div class="daftar-sunting__isi">%s</div>%s</fieldset>'
            % (_id(path), _e(node["label"]), n, kata, ket, dihapus, "".join(butir), tambah))


def _render(node, v, path, t, konteks=""):
    j = node["jenis"]
    if j == "daftar":
        return _daftar(node, v, path, t)
    if j in UNGGAHAN:
        return _berkas(node, v, path, t, konteks)
    if j == "objek":
        return "".join(_render(n, (v if isinstance(v, dict) else {}).get(k), "%s.%s" % (path, k) if path else k, t, konteks)
                       for k, n in node["bidang"])
    return _skalar(node, v, path, t, konteks)


def formulir(templat, isi, t):
    """The fields of a page's form, one card per section of the page."""
    isi = isi if isinstance(isi, dict) else {}
    return "".join('<div class="kartu kartu--sunting">%s</div>' % _render(n, isi.get(k), k, t) for k, n in templat["bidang"])


# ------------------------------------------------------------------ reading the posted form

class Konteks(object):
    """What reading the form needs besides the template. unggah=False: files are not looked at (nothing is stored)."""

    def __init__(self, form, files, kode, unggah=True):
        self.form, self.files, self.kode, self.unggah = form, files, kode, unggah
        self.galat = []          # [(path, message)] of refused uploads
        self.baru = []           # records of the files stored in this request


def _teks(v, satu_baris):
    """Typed text kept as typed: line ends made one kind (Word's manual line break included), other control
    characters dropped, the ends trimmed; one line where the field holds one line."""
    v = v.replace("\r\n", "\n").replace("\r", "\n").replace("\x0b", "\n").replace("\x0c", "\n")
    v = ih.KONTROL.sub("", v)
    return (v.replace("\n", " ") if satu_baris else v).strip(" \t\n")


def _judul_pdf(induk, item, node):
    """The title stored with a PDF (the hidden text of its link in a table): the item's own title, else the field's
    label with the item's first required text ("RPS: Algoritma dan Pemrograman"), else the label."""
    if isinstance(item.get("judul"), str) and item["judul"].strip():
        return item["judul"].strip()[:200]
    for k, n in induk["bidang"]:
        if n["jenis"] == "teks" and n.get("wajib") and isinstance(item.get(k), str) and item[k].strip():
            return ("%s: %s" % (node["label"], item[k].strip()))[:200]
    return node["label"]


def _unggah(induk, node, hasil, kunci, path, k):
    lama = hasil.get(kunci) if isinstance(hasil.get(kunci), dict) else None
    berkas = k.files.get("berkas::" + path) if k.unggah else None
    ada = berkas is not None and bool(berkas.filename)
    if node["jenis"] == "foto":
        alt = k.form.get("alt::" + path)
        alt = None if alt is None else re.sub(r"\s+", " ", ih.KONTROL.sub("", alt)).strip()
        if ada:
            try:
                rekam = media.simpan_foto(k.kode, berkas.read(media.MAKS_FOTO + 1),
                                          alt if alt is not None else (lama or {}).get("alt", ""))
            except ValueError as e:
                k.galat.append((path, "Foto tidak disimpan: %s" % e))
            else:
                hasil[kunci] = rekam
                k.baru.append(rekam)
                return
        if k.form.get("hapus::" + path):
            hasil[kunci] = None
        elif lama is not None and alt is not None and alt != lama.get("alt"):
            hasil[kunci] = dict(lama, alt=alt)
        return
    judul = _judul_pdf(induk, hasil, node)
    if ada:
        try:
            rekam = media.simpan_pdf(k.kode, berkas.read(media.MAKS_PDF + 1), judul)
        except ValueError as e:
            k.galat.append((path, "PDF tidak disimpan: %s" % e))
        else:
            hasil[kunci] = rekam
            k.baru.append(rekam)
            return
    if k.form.get("hapus::" + path):
        hasil[kunci] = None
    elif lama is not None and lama.get("judul") != judul:
        hasil[kunci] = dict(lama, judul=judul)       # the title follows the row it belongs to


def _baca(node, nilai, path, k):
    j = node["jenis"]
    if j == "objek":
        hasil = dict(nilai) if isinstance(nilai, dict) else {}
        berkas = []
        for kunci, n in node["bidang"]:
            sub = "%s.%s" % (path, kunci) if path else kunci
            if n["jenis"] in UNGGAHAN:
                berkas.append((kunci, n, sub))
            else:
                hasil[kunci] = _baca(n, hasil.get(kunci), sub, k)
        for kunci, n, sub in berkas:           # after the texts, so a PDF is titled after its row
            _unggah(node, n, hasil, kunci, sub, k)
        return hasil
    if j == "daftar" and node.get("lewat_excel"):
        return nilai                           # changed through the spreadsheet import only
    if j == "daftar":
        return [_baca(node["isi"], x, "%s.%d" % (path, i), k) for i, x in enumerate(nilai if isinstance(nilai, list) else [])]
    if j == "centang":
        return path in k.form
    v = k.form.get(path)
    if v is None:
        return nilai                           # not in the form: unchanged
    if j == "url" and node.get("sematan"):
        # a share link or an embed code pasted from Google becomes the embed address (K-P35); what cannot be embedded
        # stays as typed, and the checks say why
        v = _teks(v, True)
        return (sematan.normalkan(v)[0] or v) if v else v
    if j in ("teks", "url"):
        return _teks(v, j == "url" or not node["panjang"])
    v = v.strip()
    if j == "pilihan":
        return v if v == "" or v in node["opsi"] or v == nilai else nilai
    if not v:
        return None
    if j == "bilangan":
        if RIBUAN.match(v):
            v = v.replace(".", "")
        return int(v) if BULAT.match(v) else v
    if j == "persen":
        v = v.rstrip("%").strip()
        if PECAHAN.match(v):
            x = float(v.replace(",", "."))
            return int(x) if x.is_integer() else x
        return v
    return nilai


def baca(templat, isi, k):
    """The page's content with the posted form applied (a new object; the stored one is not changed)."""
    return _baca(templat, isi, "", k)


# ------------------------------------------------------------------ list buttons

class TombolSalah(ValueError):
    """A button that does not fit the content: not one this form shows (a request made by hand)."""


class DaftarPenuh(ValueError):
    """A list already holds as many items as its template allows; the message is for the user."""


def nilai_awal(node):
    return {} if node["jenis"] == "objek" else ""


def _daftar_di(templat, isi, path):
    """(list node, the list in the content) at a path; a list the content does not have yet is made."""
    node, data, bagian = templat, isi, path.split(".")
    for n, p in enumerate(bagian):
        akhir = n == len(bagian) - 1
        if node["jenis"] == "objek":
            if not isinstance(data, dict) or p not in dict(node["bidang"]):
                raise TombolSalah(path)
            node = dict(node["bidang"])[p]
            if akhir:
                if node["jenis"] != "daftar":
                    raise TombolSalah(path)
                if not isinstance(data.get(p), list):
                    data[p] = []
                return node, data[p]
            data = data.get(p)
        elif node["jenis"] == "daftar" and p.isdigit() and not akhir:
            if not isinstance(data, list) or int(p) >= len(data):
                raise TombolSalah(path)
            node, data = node["isi"], data[int(p)]
        else:
            raise TombolSalah(path)
    raise TombolSalah(path)


def terapkan_aksi(templat, isi, aksi):
    """Apply a list button to the content (changed in place): "tambah:<list>", "hapus|naik|turun:<list>.<i>".
    Returns (path to show, the item removed or None): the new or moved item, or the list an item left.
    TombolSalah for a button that does not fit the content, DaftarPenuh when a list is full."""
    jenis, _, path = aksi.partition(":")
    if jenis not in AKSI_DAFTAR or not POLA_JALUR.match(path):
        raise TombolSalah(aksi)
    if jenis == "tambah":
        node, lst = _daftar_di(templat, isi, path)
        if len(lst) >= node["maks"]:
            raise DaftarPenuh("%s sudah berisi %d %s, jumlah paling banyak." % (node["label"], node["maks"], kata_butir(node)))
        lst.append(nilai_awal(node["isi"]))
        return "%s.%d" % (path, len(lst) - 1), None
    induk, _, i = path.rpartition(".")
    if not i.isdigit() or not induk:
        raise TombolSalah(aksi)
    node, lst = _daftar_di(templat, isi, induk)
    i = int(i)
    if i >= len(lst):
        raise TombolSalah(aksi)
    if jenis == "hapus":
        return induk, {"jalur": induk, "indeks": i, "nilai": lst.pop(i)}
    j = i - 1 if jenis == "naik" else i + 1
    if not 0 <= j < len(lst):
        raise TombolSalah(aksi)
    lst[i], lst[j] = lst[j], lst[i]
    return "%s.%d" % (induk, j), None


def kembalikan(templat, isi, dihapus):
    """Put the item removed last back where it was. Returns its path."""
    node, lst = _daftar_di(templat, isi, dihapus["jalur"])
    if len(lst) >= node["maks"]:
        raise DaftarPenuh("%s sudah berisi %d %s, jumlah paling banyak." % (node["label"], node["maks"], kata_butir(node)))
    i = min(int(dihapus["indeks"]), len(lst))
    lst.insert(i, dihapus["nilai"])
    return "%s.%d" % (dihapus["jalur"], i)


def bagian_form(templat):
    """The largest number of form parts a page's form can send (every list full): kept under the admin's limit."""
    def hitung(node):
        j = node["jenis"]
        if j == "objek":
            return sum(hitung(n) for _k, n in node["bidang"])
        if j == "daftar":                               # a list kept in a spreadsheet has no fields in the form
            return 0 if node.get("lewat_excel") else node["maks"] * hitung(node["isi"])
        return {"dokumen": 2, "foto": 3}.get(j, 1)      # a file field and its "take off" box (and a photo's text)
    return hitung(templat) + 4                           # csrf, versi, aksi, and a spare
