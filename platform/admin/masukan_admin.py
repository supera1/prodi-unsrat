# -*- coding: utf-8 -*-
"""Feedback from the admin's users (Fase 2 langkah 5): during the pilot, every problem, question or suggestion is
recorded with who sent it, from which page and when, and the superadmin answers it and marks it followed up or put off
(rencana §6, §9: "masukan tercatat dan ditindaklanjuti"). Without e-mail (K-P12), the answer is shown on the same page.

    /masukan                       akses("masuk"): the form (?dari=<admin page>) and the sender's own feedback
    /super/masukan                 akses("super"): all feedback (?status=baru|ditindaklanjuti|ditunda); .csv to download
    /super/masukan/<id>            POST: status and answer

Stored in masukan.json (lokasi.py): {"masukan": [{"id", "waktu", "oleh", "peran", "prodi", "jenis", "halaman", "isi",
"status", "tanggapan": {"isi", "oleh", "waktu"} or null}]}, newest last; every change goes to the audit log.
"""
from __future__ import print_function

import csv
import datetime
import io
import os
import re
import secrets
import sys
import threading

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))
sys.path.insert(0, ADMIN)
sys.path.insert(0, os.path.join(os.path.dirname(ADMIN), "pemantau"))

from flask import abort, flash, g, make_response, redirect, render_template, request, url_for  # noqa: E402

import impor_dosen  # noqa: E402
import lokasi  # noqa: E402
import saringan_spam  # noqa: E402
from akses import akses  # noqa: E402

JENIS = {"kendala": "Kendala", "pertanyaan": "Pertanyaan", "usulan": "Usulan"}
STATUS = {"baru": "Baru", "ditindaklanjuti": "Ditindaklanjuti", "ditunda": "Ditunda"}
MAKS_ISI = 2000
MAKS_TANGGAPAN = 1000
MAKS_SEMUA = 5000                  # items kept; the oldest go first beyond it
POLA_HALAMAN = re.compile(r"^/(?!/)[A-Za-z0-9/_.-]{0,200}$")       # an address of this admin, never another site
POLA_ID = re.compile(r"^[0-9]{8}-[0-9]{6}-[0-9a-f]{6}$")
KONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_KUNCI = threading.Lock()


class GagalMasukan(ValueError):
    """Feedback that may not be stored; the message is for the user."""


def baca():
    data = lokasi.baca("masukan")
    return data if isinstance(data, dict) and isinstance(data.get("masukan"), list) else {"masukan": []}


def _teks(teks, maks, nama):
    teks = (teks or "").replace("\r\n", "\n").strip()
    if not teks:
        raise GagalMasukan("%s wajib diisi" % nama)
    if len(teks) > maks:
        raise GagalMasukan("%s paling banyak %d karakter" % (nama, maks))
    if KONTROL.search(teks):
        raise GagalMasukan("%s memuat karakter yang tidak boleh" % nama)
    istilah = saringan_spam.cari(teks)
    if istilah:
        raise GagalMasukan("%s memuat teks %s" % (nama, saringan_spam.jenis(istilah)))
    return teks


def halaman_sah(halaman):
    """The admin page the feedback was sent from, or "" (anything else is dropped, never stored)."""
    halaman = (halaman or "").split("?")[0]
    return halaman if POLA_HALAMAN.match(halaman) else ""


def tambah(akun, jenis, isi, halaman=""):
    """Store a new item. Returns its id."""
    if jenis not in JENIS:
        raise GagalMasukan("pilih jenis masukan")
    isi = _teks(isi, MAKS_ISI, "Isi masukan")
    sekarang = datetime.datetime.now()
    butir = {"id": "%s-%s" % (sekarang.strftime("%Y%m%d-%H%M%S"), secrets.token_hex(3)),
             "waktu": sekarang.isoformat(timespec="seconds"), "oleh": akun["nama"], "peran": akun["peran"],
             "prodi": list(akun.get("prodi") or []), "jenis": jenis, "halaman": halaman_sah(halaman), "isi": isi,
             "status": "baru", "tanggapan": None}
    with _KUNCI:
        data = baca()
        data["masukan"] = (data["masukan"] + [butir])[-MAKS_SEMUA:]
        lokasi.tulis_json(lokasi.path_data("masukan"), data)
    return butir["id"]


def tanggapi(id_, status, tanggapan, oleh):
    """Set an item's status and answer (an empty answer keeps the one there was)."""
    with _KUNCI:
        data = baca()
        butir = [b for b in data["masukan"] if b.get("id") == id_]
        if not butir:
            raise GagalMasukan("masukan tidak ditemukan")
        if status not in STATUS:
            raise GagalMasukan("status tidak dikenal")
        tanggapan = (tanggapan or "").strip()
        if tanggapan:
            tanggapan = _teks(tanggapan, MAKS_TANGGAPAN, "Tanggapan")
        butir[0]["status"] = status
        if tanggapan:
            butir[0]["tanggapan"] = {"isi": tanggapan, "oleh": oleh,
                                     "waktu": datetime.datetime.now().isoformat(timespec="seconds")}
        lokasi.tulis_json(lokasi.path_data("masukan"), data)
    return butir[0]


def pasang(app, alat):

    def halaman_form(kode_status=200, isian=None):
        milik = [b for b in reversed(baca()["masukan"]) if b.get("oleh") == g.akun["nama"]][:100]
        dari = halaman_sah(request.values.get("dari", ""))
        return render_template("masukan.html", milik=milik, JENIS=JENIS, STATUS=STATUS, dari=dari, isian=isian or {},
                               maks=MAKS_ISI), kode_status

    @app.route("/masukan")
    @akses("masuk")
    def masukan():
        return halaman_form()

    @app.route("/masukan", methods=["POST"])
    @akses("masuk")
    def masukan_kirim():
        f = request.form
        try:
            id_ = tambah(g.akun, f.get("jenis", ""), f.get("isi", ""), f.get("dari", ""))
        except GagalMasukan as e:
            flash("Masukan belum terkirim: %s." % e, "galat")
            return halaman_form(400, {"jenis": f.get("jenis", ""), "isi": f.get("isi", "")})
        alat.catat("masukan-dikirim", prodi=list(g.akun.get("prodi") or []) or None, id=id_, jenis=f.get("jenis"))
        flash("Terima kasih, masukan Anda tersimpan. Tanggapan dari UPA TIK akan tampil di halaman ini.", "ok")
        return redirect(url_for("masukan"))

    @app.route("/super/masukan")
    @akses("super")
    def super_masukan():
        status = request.args.get("status", "")
        if status and status not in STATUS:
            abort(404)
        semua = list(reversed(baca()["masukan"]))
        jumlah = {s: sum(1 for b in semua if b.get("status") == s) for s in STATUS}
        return render_template("super_masukan.html", daftar=[b for b in semua if not status or b.get("status") == status],
                               jumlah=jumlah, status=status, JENIS=JENIS, STATUS=STATUS, maks=MAKS_TANGGAPAN,
                               nama_prodi=lambda k: (alat.info_prodi(k) or {}).get("nama", k))

    @app.route("/super/masukan.csv")
    @akses("super")
    def super_masukan_csv():
        buf = io.StringIO()
        tulis = csv.writer(buf)
        tulis.writerow(["id", "waktu", "oleh", "peran", "prodi", "jenis", "halaman", "isi", "status", "tanggapan",
                        "ditanggapi_oleh", "ditanggapi_waktu"])
        for b in baca()["masukan"]:
            t = b.get("tanggapan") or {}
            tulis.writerow([impor_dosen.aman_csv(v) for v in (
                b.get("id"), b.get("waktu"), b.get("oleh"), b.get("peran"), " ".join(b.get("prodi") or []),
                JENIS.get(b.get("jenis"), b.get("jenis")), b.get("halaman"), b.get("isi"),
                STATUS.get(b.get("status"), b.get("status")), t.get("isi", ""), t.get("oleh", ""), t.get("waktu", ""))])
        resp = make_response("﻿" + buf.getvalue())            # the BOM makes Excel read it as UTF-8
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = 'attachment; filename="masukan-admin-prodi.csv"'
        return resp

    @app.route("/super/masukan/<id_>", methods=["POST"])
    @akses("super")
    def super_masukan_tanggapi(id_):
        if not POLA_ID.match(id_):
            abort(404)
        try:
            b = tanggapi(id_, request.form.get("status", ""), request.form.get("tanggapan", ""), g.akun["nama"])
        except GagalMasukan as e:
            if "tidak ditemukan" in str(e):
                abort(404)
            flash("Tanggapan tidak disimpan: %s." % e, "galat")
            return redirect(url_for("super_masukan") + "#m-" + id_)
        alat.catat("masukan-ditanggapi", prodi=b.get("prodi") or None, id=id_, status=b["status"])
        flash("Masukan ditandai %s." % STATUS[b["status"]].lower(), "ok")
        return redirect(url_for("super_masukan") + "#m-" + id_)

    alat.jumlah_masukan_baru = lambda: sum(1 for b in baca()["masukan"] if b.get("status") == "baru")
