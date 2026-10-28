# -*- coding: utf-8 -*-
"""A programme's accreditation criteria labels, set by its admin (K-P33).

    /prodi/<kode>/kriteria                 the body, its criteria and which pages serve which criterion (operators see
                                           them read-only); POST stores them (akses("prodi", "admin"))
    /prodi/<kode>/kriteria/usulan          POST: the form filled from a body of the shared file (nothing stored yet)
    /prodi/<kode>/kriteria/kosongkan       POST: drop the programme's own criteria (the shared file applies again)

The site shows them from the next build on (kriteria.untuk_prodi); every version stays in the programme's history.
No JavaScript: a criterion added to the list gets its column of check boxes once the form is stored.
"""
from __future__ import print_function

import os
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, PLATFORM)
sys.path.insert(0, ADMIN)

from flask import abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

import data_prodi  # noqa: E402
import isi_admin  # noqa: E402
import isi_halaman as ih  # noqa: E402
import kriteria as kriteria_mod  # noqa: E402
import registri  # noqa: E402
from akses import akses  # noqa: E402

BARIS_KOSONG = 3               # empty criteria rows offered for new items (no JavaScript)


def usulan_bersama():
    """The bodies of the shared file that can fill the form ([] when the file cannot be read)."""
    try:
        data = kriteria_mod.baca()
    except (OSError, ValueError):
        return []
    if kriteria_mod.periksa(data, set(ih.TEMPLAT)):
        return []
    return kriteria_mod.usulan(data)


def dari_formulir(form):
    """The criteria as typed in the form (checked by kriteria.simpan_prodi): empty rows dropped; a page's ticks that
    name a number no longer in the list are dropped too (the number was changed or its row emptied)."""
    try:
        n = min(int(form.get("kriteria_jumlah", "0")), kriteria_mod.MAKS_KRITERIA + BARIS_KOSONG)
    except ValueError:
        abort(400)
    kriteria = []
    for i in range(n):
        nomor, nama = (form.get("k-%d-nomor" % i) or "").strip(), (form.get("k-%d-nama" % i) or "").strip()
        if nomor or nama:
            kriteria.append({"nomor": nomor, "nama": nama})
    ada = {k["nomor"] for k in kriteria}
    halaman = {}
    for id_ in ih.TEMPLAT:
        dipilih = [x for x in form.getlist("h-%s" % id_) if x in ada]
        if dipilih:
            halaman[id_] = sorted(set(dipilih), key=[k["nomor"] for k in kriteria].index)
    return {"nama": (form.get("nama") or "").strip(), "instrumen": (form.get("instrumen") or "").strip(),
            "kriteria": kriteria, "halaman": halaman}


def pasang(app, alat):

    def bangun(kode):
        r = registri.cari(registri.baca(), kode)
        if r and r.get("aktif"):
            alat.antrean.minta(kode, g.akun["nama"])

    def tampil(kode, isian=None, kode_status=200):
        tersimpan = kriteria_mod.baca_prodi(kode)
        isian = isian if isian is not None else tersimpan
        lembaga_resmi = (data_prodi.efektif(kode) or {}).get("lembaga_akreditasi") or ""
        if not isian.get("nama"):
            isian = dict(isian, nama=lembaga_resmi)
        kolom = [k for k in isian.get("kriteria", []) if k.get("nomor")]
        return render_template("prodi_kriteria.html", pr=g.prodi, isian=isian, kolom=kolom, tersimpan=tersimpan,
                               kelompok=isi_admin.halaman_prodi(kode), usulan=usulan_bersama(),
                               lembaga_resmi=lembaga_resmi, admin=isi_admin.adalah_admin(g.akun),
                               kosong=BARIS_KOSONG, maks=kriteria_mod.MAKS_KRITERIA,
                               maks_nama=kriteria_mod.MAKS_NAMA, maks_lembaga=kriteria_mod.MAKS_LEMBAGA), kode_status

    @app.route("/prodi/<kode>/kriteria")
    @akses("prodi")
    def kriteria_prodi(kode):
        return tampil(kode)

    @app.route("/prodi/<kode>/kriteria", methods=["POST"])
    @akses("prodi", "admin")
    def kriteria_simpan(kode):
        isian = dari_formulir(request.form)
        try:
            kriteria_mod.simpan_prodi(kode, isian, set(ih.TEMPLAT), g.akun["nama"], "kriteria disimpan")
        except kriteria_mod.GagalKriteria as e:
            flash("Kriteria tidak disimpan: %s" % e, "galat")
            return tampil(kode, isian, 400)
        alat.catat("kriteria-diubah", prodi=kode, kriteria=len(isian["kriteria"]), halaman=len(isian["halaman"]))
        bangun(kode)
        if isian["kriteria"]:
            flash("Kriteria akreditasi disimpan. Situs prodi dibangun ulang.", "ok")
        else:
            flash("Daftar kriteria kosong, jadi tidak ada label kriteria di situs. Situs prodi dibangun ulang.", "ok")
        return redirect(url_for("kriteria_prodi", kode=kode))

    @app.route("/prodi/<kode>/kriteria/usulan", methods=["POST"])
    @akses("prodi", "admin")
    def kriteria_usulan(kode):
        pilihan = {lb["id"]: lb for lb in usulan_bersama()}
        lb = pilihan.get(request.form.get("usulan", ""))
        if lb is None:
            flash("Usulan tidak dikenal.", "galat")
            return tampil(kode, None, 400)
        flash("Formulir diisi dari usulan %s. Periksa dan sesuaikan dengan instrumen prodi Anda, lalu tekan Simpan "
              "kriteria; sebelum disimpan, situs belum berubah." % lb["nama"], "ok")
        return tampil(kode, kriteria_mod.dari_usulan(lb))

    @app.route("/prodi/<kode>/kriteria/kosongkan", methods=["POST"])
    @akses("prodi", "admin")
    def kriteria_kosongkan(kode):
        if kriteria_mod.baca_prodi(kode):
            kriteria_mod.hapus_prodi(kode, g.akun["nama"])
            alat.catat("kriteria-dikosongkan", prodi=kode)
            bangun(kode)
        flash("Kriteria akreditasi dikosongkan; label kriteria tidak tampil lagi di situs. Versi sebelumnya ada di "
              "Riwayat.", "ok")
        return redirect(url_for("kriteria_prodi", kode=kode))
