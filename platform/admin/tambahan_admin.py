# -*- coding: utf-8 -*-
"""A programme's extra pages in the admin (K-P35, platform/halaman_tambahan.py).

    /prodi/<kode>/tambahan                 the programme's extra pages; POST adds one and opens its editor
    /prodi/<kode>/tambahan/simpan          POST: the names, groups and order of the pages
    /prodi/<kode>/tambahan/<id>/hapus      POST: take a page off the menu and the site (its content stays in the history)
    /super/tambahan                        akses("super"): every programme's extra pages and what they embed, and the
                                           built-in pages that embed something (K-P36), to watch them (a page comes off
                                           the site with "Tarik dari situs" in its editor)

The programme's admins and the superadmin manage the pages; the content of a page is written in the page editor
(isi_admin.py) like any other page, operators included.
"""
from __future__ import print_function

import os
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, PLATFORM)
sys.path.insert(0, ADMIN)

from flask import abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

import halaman_tambahan as ht  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import sematan as sematan_mod  # noqa: E402
from akses import akses  # noqa: E402


def label_kelompok(kode):
    """{group id: its label on this programme's site} of the groups an extra page may go to."""
    atur = (lokasi.baca("prodi/%s/situs" % kode) or {}).get("menu")
    atur = atur if isinstance(atur, dict) else {}
    hasil = {}
    for k, label in ht.kelompok_ada().items():
        a = atur.get(k)
        hasil[k] = (a.get("label") if isinstance(a, dict) else None) or label
    return hasil


def isi_terbit(kode, id_):
    """What a page's published content holds: (embedded services, number of PDFs, number of photos)."""
    isi = ih.terbit(kode, id_) or {}
    layanan = sorted({sematan_mod.layanan(x.get("alamat")) for x in isi.get("sematan") or [] if isinstance(x, dict)}
                     - {""})
    return layanan, len(isi.get("dokumen") or []), len(isi.get("foto") or [])


def sematan_bawaan(kode):
    """The built-in pages whose published content embeds something (K-P36): [(page id, embedded services)]."""
    hasil = []
    for id_ in ih.TEMPLAT:
        sematan = [x for x in (ih.terbit(kode, id_) or {}).get("sematan") or [] if isinstance(x, dict)]
        if sematan:
            hasil.append((id_, sorted({sematan_mod.layanan(x.get("alamat")) for x in sematan} - {""})))
    return hasil


def pasang(app, alat):

    def bangun(kode):
        r = registri.cari(registri.baca(), kode)
        if r and r.get("aktif"):
            alat.antrean.minta(kode, g.akun["nama"])

    def tampil(kode, kode_status=200, isian=None):
        daftar = [dict(h, k=ih.keadaan(kode, h["id"])) for h in ht.baca(kode) if isinstance(h, dict)
                  and ih.POLA_TAMBAHAN.match(str(h.get("id")))]
        return render_template("prodi_tambahan.html", pr=g.prodi, daftar=daftar, kelompok=label_kelompok(kode),
                               isian=isian or {}, maks=ht.MAKS, maks_label=ht.MAKS_LABEL, maks_alamat=ht.MAKS_ALAMAT,
                               awalan=ht.AWALAN), kode_status

    @app.route("/prodi/<kode>/tambahan")
    @akses("prodi", "admin")
    def tambahan_prodi(kode):
        return tampil(kode)

    @app.route("/prodi/<kode>/tambahan", methods=["POST"])
    @akses("prodi", "admin")
    def tambahan_buat(kode):
        f = request.form
        try:
            h = ht.tambah(kode, f.get("label", ""), f.get("kelompok", ""), f.get("alamat", ""), g.akun["nama"])
        except ht.GagalTambahan as e:
            flash("Halaman tambahan tidak dibuat: %s." % e, "galat")
            return tampil(kode, 400, {"label": f.get("label", ""), "kelompok": f.get("kelompok", ""),
                                      "alamat": f.get("alamat", "")})
        alat.catat("tambahan-dibuat", prodi=kode, halaman=h["id"], alamat=h["alamat"])
        flash("Halaman tambahan “%s” dibuat dengan alamat %s/%s/. Isi halamannya di bawah; halaman ini tampil di situs "
              "setelah diterbitkan." % (h["label"], ht.AWALAN, h["alamat"]), "ok")
        return redirect(url_for("isi_sunting", kode=kode, id_=h["id"]))

    @app.route("/prodi/<kode>/tambahan/simpan", methods=["POST"])
    @akses("prodi", "admin")
    def tambahan_simpan(kode):
        f = request.form
        perubahan = {}
        for h in ht.baca(kode):
            p = {}
            if "label-%s" % h.get("id") in f:
                p["label"] = f.get("label-%s" % h["id"], "")
            if "kelompok-%s" % h.get("id") in f:
                p["kelompok"] = f.get("kelompok-%s" % h["id"], "")
            urutan = f.get("urutan-%s" % h.get("id"), "").strip()
            if urutan:
                try:
                    p["urutan"] = int(urutan)
                except ValueError:
                    p["urutan"] = -1                     # refused with the module's message
            perubahan[h.get("id")] = p
        try:
            ht.ubah(kode, perubahan, g.akun["nama"])
        except ht.GagalTambahan as e:
            flash("Perubahan tidak disimpan: %s." % e, "galat")
            return tampil(kode, 400)
        alat.catat("tambahan-diubah", prodi=kode, halaman=len(perubahan))
        bangun(kode)
        flash("Halaman tambahan disimpan. Situs prodi dibangun ulang.", "ok")
        return redirect(url_for("tambahan_prodi", kode=kode))

    @app.route("/prodi/<kode>/tambahan/<id_>/hapus", methods=["POST"])
    @akses("prodi", "admin")
    def tambahan_hapus(kode, id_):
        lama = ht.hapus(kode, id_, g.akun["nama"])
        if lama is None:
            abort(404)
        alat.catat("tambahan-dihapus", prodi=kode, halaman=id_, alamat=lama.get("alamat"))
        bangun(kode)
        flash("Halaman tambahan “%s” dihapus dari menu dan situs. Isinya tetap tersimpan di riwayat." % lama.get("label"),
              "ok")
        return redirect(url_for("tambahan_prodi", kode=kode))

    @app.route("/super/tambahan")
    @akses("super")
    def super_tambahan():
        baris, bawaan = [], []
        butir = menu_mod.semua_butir(menu_mod.baca_templat())
        for r in registri.baca()["prodi"]:
            info = alat.info_prodi(r["kode_pddikti"])
            if not info:
                continue
            for id_, layanan in sematan_bawaan(info["kode"]):
                bawaan.append({"prodi": info, "id": id_, "label": butir.get(id_, {}).get("label", id_), "layanan": layanan,
                               "alamat": butir.get(id_, {}).get("alamat", ""), "k": ih.keadaan(info["kode"], id_)})
            kelompok = label_kelompok(info["kode"])
            for h in ht.baca(info["kode"]):
                if not isinstance(h, dict) or not ih.POLA_TAMBAHAN.match(str(h.get("id"))):
                    continue
                layanan, n_pdf, n_foto = isi_terbit(info["kode"], h["id"])
                baris.append(dict(h, prodi=info, k=ih.keadaan(info["kode"], h["id"]), layanan=layanan, n_pdf=n_pdf,
                                  n_foto=n_foto, nama_kelompok=kelompok.get(h.get("kelompok"), h.get("kelompok"))))
        baris.sort(key=lambda b: (registri.kunci_urut(b["prodi"]), b["label"]))
        bawaan.sort(key=lambda b: (registri.kunci_urut(b["prodi"]), b["label"]))
        return render_template("super_tambahan.html", baris=baris, bawaan=bawaan, awalan=ht.AWALAN,
                               layanan=sematan_mod.NAMA_LAYANAN)
