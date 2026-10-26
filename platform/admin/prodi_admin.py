# -*- coding: utf-8 -*-
"""Pages of a programme's admin (akses("prodi", "admin"): the programme's admins and the superadmin).

    /prodi/<kode>/data                     the programme's data (name, degree, credits, accreditation, CPL, ...):
                                           change it here; www's value stays visible next to every changed field
    /prodi/<kode>/data/<field>/www         use www's value again for a field (drop the local change)
    /prodi/<kode>/data/<field>/tetap       keep the local value after www changed the field (end the conflict)

Langkah 5b (K-P16). The rest of the programme admin's pages come in langkah 6.
"""
from __future__ import print_function

import os
import re
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))
sys.path.insert(0, ADMIN)

from flask import abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

import data_prodi  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
from akses import akses  # noqa: E402

JUMLAH_CPL_KOSONG = 3          # empty CPL rows offered for new items (no JavaScript)


def isian_dari_formulir(form, p):
    """{field: value} for the fields present in the form, in the types data_prodi expects."""
    hasil = {}
    for f, (_label, _maks, jenis) in data_prodi.FIELD_UBAH.items():
        if jenis == "cpl":
            if "cpl_jumlah" not in form:
                continue
            try:
                n = min(int(form.get("cpl_jumlah", "0")), data_prodi.MAKS_CPL + JUMLAH_CPL_KOSONG)
            except ValueError:
                abort(400)
            cpl = []
            for i in range(n):
                isi = (form.get("cpl-%d-isi" % i) or "").strip()
                if not isi:
                    continue                 # an emptied row removes that CPL
                cpl.append({"kode": (form.get("cpl-%d-kode" % i) or "").strip(), "isi": isi,
                            "isi_en": (form.get("cpl-%d-isi_en" % i) or "").strip(),
                            "kurikulum": (form.get("cpl-%d-kurikulum" % i) or "").strip()})
            hasil["cpl"] = cpl
            continue
        if f not in form:
            continue
        v = form.get(f, "").strip()
        if jenis == "sks":
            if v and not re.match(r"^\d{1,3}$", v):
                hasil[f] = "tidak sah"           # refused by data_prodi with its message
            else:
                hasil[f] = int(v) if v else None
        else:
            hasil[f] = v
    return hasil


def pasang(app, alat):

    def halaman_data(kode, kode_status=200):
        p_www = {x["kode_pddikti"]: x for x in (lokasi.baca("warisan/prodi") or {}).get("program", [])}.get(kode)
        if p_www is None:
            abort(404)
        data = data_prodi.baca(kode)
        p = data_prodi.gabung(p_www, data)
        unit = sorted(data_prodi.unit_prodi().values(), key=lambda u: u["nama"])
        akreditasi_ada = sorted({x.get("akreditasi") for x in (lokasi.baca("warisan/prodi") or {}).get("program", [])
                                 if x.get("akreditasi")})
        lembaga_ada = sorted({x.get("lembaga_akreditasi") for x in (lokasi.baca("warisan/prodi") or {}).get("program", [])
                              if x.get("lembaga_akreditasi")})
        return render_template("prodi_data.html", pr=g.prodi, p=p, www=p_www, data=data, field=data_prodi.FIELD_UBAH,
                               bentrok={b[0]: b for b in data_prodi.bentrok(kode, p_www, data)}, unit=unit,
                               jenjang=list(registri.slug_mod.AWALAN_JENJANG), kosong=JUMLAH_CPL_KOSONG,
                               akreditasi_ada=akreditasi_ada, lembaga_ada=lembaga_ada), kode_status

    def bangun(kode):
        r = registri.cari(registri.baca(), kode)
        if r and r.get("aktif"):
            alat.antrean.minta(kode, g.akun["nama"])

    @app.route("/prodi/<kode>/data", methods=["GET"])
    @akses("prodi", "admin")
    def data_prodi_lihat(kode):
        return halaman_data(kode)

    @app.route("/prodi/<kode>/data", methods=["POST"])
    @akses("prodi", "admin")
    def data_prodi_simpan(kode):
        p_www = {x["kode_pddikti"]: x for x in (lokasi.baca("warisan/prodi") or {}).get("program", [])}.get(kode)
        if p_www is None:
            abort(404)
        try:
            berubah = data_prodi.simpan(kode, isian_dari_formulir(request.form, p_www), g.akun["nama"])
        except data_prodi.GagalData as e:
            flash("Data tidak disimpan: %s" % e, "galat")
            return halaman_data(kode, 400)
        if not berubah:
            flash("Tidak ada yang berubah.", "info")
        else:
            alat.catat("data-prodi-diubah", prodi=kode, kolom=",".join(berubah))
            bangun(kode)
            flash("Data disimpan (%s); situs prodi dibangun ulang." % ", ".join(
                data_prodi.FIELD_UBAH[f][0] for f in berubah), "ok")
        return redirect(url_for("data_prodi_lihat", kode=kode))

    def kolom(f):
        if f not in data_prodi.FIELD_UBAH:
            abort(404)
        return f

    @app.route("/prodi/<kode>/data/<f>/www", methods=["POST"])
    @akses("prodi", "admin")
    def data_prodi_pakai_www(kode, f):
        if data_prodi.pakai_www(kode, kolom(f), g.akun["nama"]):
            alat.catat("data-prodi-pakai-www", prodi=kode, kolom=f)
            bangun(kode)
            flash("%s kembali memakai data www." % data_prodi.FIELD_UBAH[f][0], "ok")
        return redirect(url_for("data_prodi_lihat", kode=kode))

    @app.route("/prodi/<kode>/data/<f>/tetap", methods=["POST"])
    @akses("prodi", "admin")
    def data_prodi_tetap(kode, f):
        if data_prodi.tetap(kode, kolom(f), g.akun["nama"]):
            alat.catat("data-prodi-tetap", prodi=kode, kolom=f)
            flash("%s tetap memakai data prodi; tanda bentrok dihapus." % data_prodi.FIELD_UBAH[f][0], "ok")
        return redirect(url_for("data_prodi_lihat", kode=kode))
