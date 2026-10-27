# -*- coding: utf-8 -*-
"""A programme's own pages in the admin (Fase 2 langkah 2): the 22 required accreditation pages and the 2 optional
ones, written in forms built from their content templates (isi_halaman.py, penyunting.py). akses("prodi"): operators
too; publishing a draft (by an admin, K-P24) comes in langkah 3.

    /prodi/<kode>/halaman                     the pages and what they hold (nothing yet, a draft, published)
    /prodi/<kode>/halaman/<id>                the form of a page; POST aksi=simpan | pratinjau | batal | kembalikan |
                                              tambah:<list> | hapus|naik|turun:<list>.<i>
    /prodi/<kode>/halaman/<id>/pratinjau      the draft as the site would show it, with the site's styles
    /prodi/<kode>/pratinjau/warna.css         the programme's colours, for the preview
    /aset-situs/<nama>                        the site's style sheets (tokens.css, prodi.css), for the preview

A POST first checks the version the form was made from: a form from an older version (someone saved in between) is
refused and nothing is stored. Then the form is read into the draft, uploads are checked and stored (media.py), the
button is applied and the draft is stored. Only "Simpan draf" (and discarding a draft) keeps the previous content in
the history; the list buttons and the preview do not, so the history holds saves rather than every click. The site
keeps showing the published content all along.
"""
from __future__ import print_function

import copy
import os
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, PLATFORM)
sys.path.insert(0, ADMIN)
sys.path.insert(0, os.path.join(PLATFORM, "bangun"))

from flask import Response, abort, flash, g, redirect, render_template, request, send_from_directory, url_for  # noqa: E402
from markupsafe import Markup  # noqa: E402

import bangun as bangun_mod  # noqa: E402
import data_prodi  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import menu as menu_mod  # noqa: E402
import penyunting  # noqa: E402
import warna as warna_mod  # noqa: E402
from akses import akses  # noqa: E402

ASET_SITUS = ("tokens.css", "prodi.css")
PRIVASI = ("Jangan mengunggah data pribadi: NIK, nomor HP, alamat rumah, nilai atau IPK perorangan, data kesehatan, atau "
           "dokumen internal akreditasi yang memuat data pribadi. Daftar tenaga kependidikan dan prestasi cukup memuat "
           "nama dan peran.")


def halaman_prodi(kode):
    """The programme's own pages in menu order: [(group label, [menu entry + "sembunyi", ...])]. A label the
    programme gave a page in its menu settings is used; "sembunyi": an optional page the programme hides."""
    atur = (lokasi.baca("prodi/%s/situs" % kode) or {}).get("menu")
    atur = atur if isinstance(atur, dict) else {}

    def pengaturan(id_):
        return atur.get(id_) if isinstance(atur.get(id_), dict) else {}
    hasil = []
    for k in menu_mod.baca_templat():
        anak = [dict(a, label=(pengaturan(a["id"]).get("label") or a["label"]),
                     sembunyi=bool(pengaturan(a["id"]).get("sembunyi")))
                for a in k.get("anak", []) if a["id"] in ih.TEMPLAT]
        if anak:
            hasil.append((pengaturan(k["id"]).get("label") or k["label"], anak))
    return hasil


def keadaan(data):
    """What a page holds, for the list: {"status": "kosong" | "draf" | "terbit", "draf": draft or None,
    "terbit": published record or None}."""
    d, t = ih.draf(data), data.get("terbit") if isinstance(data.get("terbit"), dict) else None
    return {"status": "terbit" if t else ("draf" if d else "kosong"), "draf": d, "terbit": t}


def dihapus_sah(x):
    return (isinstance(x, dict) and isinstance(x.get("jalur"), str) and bool(penyunting.POLA_JALUR.match(x["jalur"]))
            and isinstance(x.get("indeks"), int) and x["indeks"] >= 0 and "nilai" in x)


def pasang(app, alat):

    def ini_(kode, id_):
        """The menu entry of a page of this programme that has a content template, or 404."""
        if id_ not in ih.TEMPLAT:
            abort(404)
        for _kelompok, anak in halaman_prodi(kode):
            for a in anak:
                if a["id"] == id_:
                    return a
        abort(404)

    def url_berkas(kode, rekam):
        return rekam["url"] if "url" in rekam else url_for("berkas_prodi", kode=kode, jalur=rekam["jalur"])

    def berkas_ada(rekam):
        if "url" in rekam:
            return media.url_sah(rekam["url"])
        jalur = rekam.get("jalur")
        return media.jalur_sah(jalur) and os.path.isfile(os.path.join(lokasi.unggahan(), *jalur.split("/")))

    def masalah_draf(id_, isi, kode):
        return penyunting.masalah_tampil(ih.TEMPLAT[id_], isi, ih.daftar_masalah(id_, isi, kode))

    def tampil_sunting(kode, ini, data):
        templat = ih.TEMPLAT[ini["id"]]
        isi = copy.deepcopy(ih.isi_kerja(data))
        masalah = masalah_draf(ini["id"], isi, kode)
        galat = {}
        for jalur, _tempat, pesan in masalah:
            galat.setdefault(jalur, pesan)
        buka = request.args.get("buka", "")
        d = ih.draf(data)
        t = penyunting.Tampil(galat, lambda r: url_berkas(kode, r), [buka] if penyunting.POLA_JALUR.match(buka) else [],
                              d.get("dihapus") if d and dihapus_sah(d.get("dihapus")) else None)
        return render_template("halaman_sunting.html", pr=g.prodi, ini=ini, data=data, k=keadaan(data),
                               formulir=Markup(penyunting.formulir(templat, isi, t)), masalah=masalah,
                               id_galat=penyunting._id, privasi=PRIVASI)

    def bentrok(kode, ini, pesan):
        """A form made from an older version: nothing was stored (409)."""
        return render_template("halaman_bentrok.html", pr=g.prodi, ini=ini, pesan=pesan), 409

    # -------------------------------------------------------------- the list of pages

    @app.route("/prodi/<kode>/halaman")
    @akses("prodi")
    def isi_daftar(kode):
        kelompok = [(label, [dict(a, k=keadaan(ih.baca(kode, a["id"]))) for a in anak])
                    for label, anak in halaman_prodi(kode)]
        semua = [a for _l, anak in kelompok for a in anak]
        jumlah = {"wajib": sum(1 for a in semua if a.get("jenis") == "wajib"),
                  "terbit": sum(1 for a in semua if a.get("jenis") == "wajib" and ih.terisi(kode, a["id"]))}
        return render_template("halaman_daftar.html", pr=g.prodi, kelompok=kelompok, jumlah=jumlah)

    # -------------------------------------------------------------- one page

    @app.route("/prodi/<kode>/halaman/<id_>")
    @akses("prodi")
    def isi_sunting(kode, id_):
        return tampil_sunting(kode, ini_(kode, id_), ih.baca(kode, id_))

    @app.route("/prodi/<kode>/halaman/<id_>", methods=["POST"])
    @akses("prodi")
    def isi_simpan(kode, id_):
        ini = ini_(kode, id_)
        templat = ih.TEMPLAT[id_]
        aksi = request.form.get("aksi", "simpan")
        try:
            versi = int(request.form.get("versi", ""))
        except ValueError:
            abort(400, "Formulir tidak lengkap. Muat ulang halaman lalu coba lagi.")
        if aksi not in ("simpan", "pratinjau", "batal", "kembalikan") and aksi.partition(":")[0] not in penyunting.AKSI_DAFTAR:
            abort(400)
        data = ih.baca(kode, id_)
        try:
            ih.cek_versi(data, versi)
        except ih.GagalIsi as e:
            return bentrok(kode, ini, str(e))
        oleh = g.akun["nama"]
        if aksi == "batal":
            try:
                ih.buang_draf(kode, id_, oleh, versi)
            except ih.GagalIsi as e:
                return bentrok(kode, ini, str(e))
            alat.catat("isi-draf-dibuang", prodi=kode, halaman=id_)
            flash("Draf dibuang. %s" % ("Penyunting kembali memuat isi yang sudah terbit." if data.get("terbit")
                                         else "Halaman ini kembali kosong."), "ok")
            return redirect(url_for("isi_sunting", kode=kode, id_=id_))

        d = ih.draf(data)
        dasar = copy.deepcopy(ih.isi_kerja(data))
        k = penyunting.Konteks(request.form, request.files, kode)
        isi = penyunting.baca(templat, dasar, k)
        tujuan, dihapus = None, None
        try:
            if aksi == "kembalikan":
                if not (d and dihapus_sah(d.get("dihapus"))):
                    raise penyunting.DaftarPenuh("Tidak ada butir yang dapat dikembalikan.")
                tujuan = penyunting.kembalikan(templat, isi, d["dihapus"])
            elif aksi.partition(":")[0] in penyunting.AKSI_DAFTAR:
                tujuan, dihapus = penyunting.terapkan_aksi(templat, isi, aksi)
        except penyunting.TombolSalah:
            abort(400)
        except penyunting.DaftarPenuh as e:
            flash(str(e), "galat")
        if aksi == "simpan" and not k.galat:
            # empty rows go; not while an upload was refused, so the row it was meant for stays to try again
            isi = ih.rapikan(templat, isi)
        # the item offered back after a removal is offered until the next request: that one stores the draft anyway
        berubah = isi != ih.isi_kerja(data) or dihapus is not None or bool(d and d.get("dihapus"))
        if berubah:
            try:
                ih.simpan_draf(kode, id_, isi, oleh, versi, riwayat=aksi == "simpan", dihapus=dihapus)
            except ih.GagalIsi as e:
                if "baru saja diubah" in str(e):
                    return bentrok(kode, ini, str(e))
                flash("Draf tidak disimpan: %s." % e, "galat")
                return redirect(url_for("isi_sunting", kode=kode, id_=id_))
        for jalur, pesan in k.galat:
            flash("%s — %s" % (penyunting.label_jalur(templat, jalur), pesan), "galat")
        if k.baru:
            alat.catat("isi-berkas-diunggah", prodi=kode, halaman=id_, jumlah=len(k.baru))
        if aksi == "pratinjau":
            return redirect(url_for("isi_pratinjau", kode=kode, id_=id_))
        if aksi == "simpan":
            if berubah:
                alat.catat("isi-draf-disimpan", prodi=kode, halaman=id_)
                n = len(masalah_draf(id_, isi, kode))
                flash("Draf disimpan. Situs tetap menampilkan isi yang sudah terbit." + (
                    " Masih ada %d isian yang perlu diperbaiki sebelum halaman ini dapat diterbitkan." % n if n else ""), "ok")
            elif not k.galat:
                flash("Tidak ada perubahan untuk disimpan.", "info")
            return redirect(url_for("isi_sunting", kode=kode, id_=id_))
        if tujuan is None:
            return redirect(url_for("isi_sunting", kode=kode, id_=id_))
        return redirect(url_for("isi_sunting", kode=kode, id_=id_, buka=tujuan) + "#" + penyunting._id(tujuan))

    # -------------------------------------------------------------- the preview

    @app.route("/prodi/<kode>/halaman/<id_>/pratinjau")
    @akses("prodi")
    def isi_pratinjau(kode, id_):
        ini = ini_(kode, id_)
        data = ih.baca(kode, id_)
        isi = ih.isi_kerja(data)
        bagian, hilang = ih.tampilan(id_, ih.isi_sah(id_, isi, kode), berkas_ada)
        return render_template("halaman_pratinjau.html", pr=g.prodi, ini=ini, k=keadaan(data), hilang=hilang,
                               isi_html=bangun_mod.bagian_html(bagian, lambda r: url_berkas(kode, r)) if bagian else "",
                               n_masalah=len(masalah_draf(id_, isi, kode)))

    @app.route("/prodi/<kode>/pratinjau/warna.css")
    @akses("prodi")
    def isi_warna_css(kode):
        situs = lokasi.baca("prodi/%s/situs" % kode) or {}
        p = data_prodi.efektif(kode) or {}
        unit = data_prodi.unit_per_kode().get(p.get("unit_kode"), {})
        return Response(warna_mod.css(warna_mod.warna_prodi(situs.get("palet"), unit.get("bendera"))), mimetype="text/css")

    @app.route("/aset-situs/<nama>")
    @akses("masuk")
    def aset_situs(nama):
        if nama not in ASET_SITUS:
            abort(404)
        return send_from_directory(os.path.join(PLATFORM, "template", "aset", "css"), nama, mimetype="text/css", max_age=0)
