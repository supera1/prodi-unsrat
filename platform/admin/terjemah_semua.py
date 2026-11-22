# -*- coding: utf-8 -*-
"""Translating a programme's pages and announcements in one go (Fase 5 langkah 5a, K-P37): "Terjemahkan semua".

    /prodi/<kode>/terjemahkan-semua     akses("prodi"), operators too: what it would translate (the confirmation), the
                                        progress of a running job, or the result of the last one; POST starts a job.
                                        404 for a programme without its English version switched on (K-P38)

What it translates, in this order (rencana):
    pages          every page of the programme in menu order whose Indonesian working content (its draft, else its
                   published content: the same source as the English editor's own button) has texts without an English
                   translation; the lists kept in spreadsheets are never sent. An English draft waiting for approval is
                   left out: its submitter asked the admin to look at exactly that text.
    announcements  every announcement the account may change (pengumuman_admin.boleh_ubah: an operator its own drafts
                   and submissions, an admin all), not withdrawn, newest first, whose English texts are empty.
Texts already translated are never overwritten.

A job runs per programme, one at a time, in a background thread (PRODI_BANGUN=latar, the default, so the form answers
at once and a load balancer never waits for DeepL) or inside the request (sinkron and mati: the tests). Per item it
reads the item again (it may have changed since the plan), checks today's and this month's limits (an item that does
not fit waits for the next run, the others go on), translates, counts the characters, and stores the result as the
English draft marked "mesin" (pages: isi_halaman.simpan_draf with the version it read, so a change made in between is
never overwritten; announcements: pengumuman.ubah). Every item goes to the audit log. A failing provider (key, quota,
network) stops the job; what was done stays. Nothing is published: a person checks every machine translation as with
the per-page button.
"""
from __future__ import print_function

import copy
import datetime
import os
import sys
import threading
import traceback

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, PLATFORM)
sys.path.insert(0, ADMIN)

from flask import abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

import audit  # noqa: E402
import data_prodi  # noqa: E402
import isi_halaman as ih  # noqa: E402
import isi_inggris  # noqa: E402
import lokasi  # noqa: E402
import pengumuman as pg  # noqa: E402
import registri  # noqa: E402
import terjemah_mesin  # noqa: E402
from akses import akses  # noqa: E402

# the state of an item after a job
NAMA_HASIL = {"diterjemahkan": "Diterjemahkan", "sudah": "Sudah diterjemahkan", "dilewati": "Dilewati",
              "belum": "Belum (batas tercapai)", "gagal": "Gagal", "tidak-dijalankan": "Tidak dijalankan"}


def _sekarang():
    return datetime.datetime.now().isoformat(timespec="seconds")


# ------------------------------------------------------------------ what would be translated

def _halaman(kode, id_):
    """(Indonesian working content, English data, English translation memory, texts to translate) of a page."""
    sumber = ih.isi_kerja(ih.baca(kode, id_))
    data_en = ih.baca(kode, isi_inggris.id_en(id_))
    en = isi_inggris.rapi(ih.isi_kerja(data_en))
    return sumber, data_en, en, isi_inggris.sasaran_mesin(ih.templat_halaman(id_), sumber, en)


def _menunggu(data_en):
    d = ih.draf(data_en)
    return bool(d and d.get("status") == "menunggu")


def rencana(kode, halaman, boleh):
    """What a job would translate now: ([item, ...], [left-out item, ...]). halaman: [(page id, label)] in menu order;
    boleh(b): may the account change announcement b. An item: {"jenis": "halaman" | "pengumuman", "id", "label",
    "teks": number of texts, "karakter"}; a left-out one has "alasan"."""
    butir, dilewati = [], []
    for id_, label in halaman:
        if ih.templat_halaman(id_) is None:
            continue
        _sumber, data_en, _en, sasaran = _halaman(kode, id_)
        if not sasaran:
            continue
        x = {"jenis": "halaman", "id": id_, "label": label, "teks": len(sasaran), "karakter": sum(map(len, sasaran))}
        if _menunggu(data_en):
            dilewati.append(dict(x, alasan="versi Inggrisnya menunggu persetujuan admin prodi"))
        else:
            butir.append(x)
    kabar = sorted(pg.baca(kode).get("butir", []), key=lambda b: (b.get("tanggal", ""), b.get("dibuat", "")), reverse=True)
    for b in kabar:
        if b.get("status") == "ditarik" or not boleh(b):
            continue
        sasaran = pg.teks_mesin(b)
        if sasaran:
            butir.append({"jenis": "pengumuman", "id": b["id"], "label": b.get("judul", b["id"]), "teks": len(sasaran),
                          "karakter": sum(map(len, sasaran))})
    return butir, dilewati


# ------------------------------------------------------------------ one job

def _satu_halaman(x, kerja):
    kode, id_ = kerja["kode"], x["id"]
    sumber, data_en, en, sasaran = _halaman(kode, id_)
    if _menunggu(data_en):
        return dict(x, status="dilewati", pesan="versi Inggrisnya menunggu persetujuan admin prodi")
    if not sasaran:
        return dict(x, status="sudah", pesan="semua teksnya sudah diterjemahkan")
    n = sum(map(len, sasaran))
    try:
        terjemah_mesin.periksa_batas(kode, n, kerja["kode_semua"], kerja["batas"])
    except terjemah_mesin.GagalTerjemah as e:
        return dict(x, status="belum", pesan=str(e))
    hasil = terjemah_mesin.terjemahkan(kerja["penyedia"], sasaran, kerja["glos"])   # GagalTerjemah stops the job
    terjemah_mesin.catat_pemakaian(kode, n)
    try:
        ih.simpan_draf(kode, isi_inggris.id_en(id_), isi_inggris.pasang_mesin(ih.templat_halaman(id_), sumber, en, hasil),
                       kerja["oleh"], data_en.get("versi", 0))
    except ih.GagalIsi as e:
        pesan = "diubah orang lain saat diterjemahkan; jalankan lagi nanti" if "baru saja diubah" in str(e) else str(e)
        return dict(x, status="dilewati", pesan=pesan, karakter=n)
    gagal = sum(1 for v in hasil.values() if not v)
    audit.catat("isi-en-terjemahan-mesin", oleh=kerja["oleh"], ip=kerja["ip"], prodi=kode, halaman=id_,
                teks=len(sasaran) - gagal, karakter=n, penyedia=kerja["penyedia"].nama, semua=1)
    return dict(x, status="diterjemahkan", teks=len(sasaran) - gagal, karakter=n, gagal=gagal)


def _satu_pengumuman(x, kerja):
    kode, id_ = kerja["kode"], x["id"]
    try:
        b = pg.cari(kode, id_)
    except pg.GagalPengumuman:
        return dict(x, status="dilewati", pesan="pengumuman ini tidak ada lagi")
    if b.get("status") == "ditarik" or not kerja["boleh"](b):
        return dict(x, status="dilewati", pesan="pengumuman ini tidak dapat diubah lagi oleh akun ini")
    sasaran = pg.teks_mesin(b)
    if not sasaran:
        return dict(x, status="sudah", pesan="semua teksnya sudah diterjemahkan")
    n = sum(map(len, sasaran))
    try:
        terjemah_mesin.periksa_batas(kode, n, kerja["kode_semua"], kerja["batas"])
    except terjemah_mesin.GagalTerjemah as e:
        return dict(x, status="belum", pesan=str(e))
    hasil = terjemah_mesin.terjemahkan(kerja["penyedia"], sasaran, kerja["glos"])
    terjemah_mesin.catat_pemakaian(kode, n)
    en, jadi, gagal = pg.pasang_mesin(pg.cari(kode, id_), hasil)     # read again: only fields still empty are filled
    if not jadi:
        return dict(x, status="dilewati", karakter=n,
                    pesan="tidak ada terjemahan yang kembali utuh" if gagal else "diubah saat diterjemahkan")
    try:
        pg.ubah(kode, id_, {"en": en}, kerja["oleh"])
    except pg.GagalPengumuman as e:
        return dict(x, status="gagal", pesan=str(e), karakter=n)
    audit.catat("pengumuman-en-terjemahan-mesin", oleh=kerja["oleh"], ip=kerja["ip"], prodi=kode, id=id_, teks=jadi,
                karakter=n, penyedia=kerja["penyedia"].nama, semua=1)
    return dict(x, status="diterjemahkan", teks=jadi, karakter=n, gagal=gagal)


def jalankan(butir, kerja, lapor):
    """Translate the items one by one; lapor(index, item with its "status" and "pesan") after each. Returns the job's
    closing message."""
    for i, x in enumerate(butir):
        lapor(i, dict(x, status="berjalan"))
        try:
            hasil = (_satu_halaman if x["jenis"] == "halaman" else _satu_pengumuman)(x, kerja)
        except terjemah_mesin.GagalTerjemah as e:              # the provider failed: the next items would fail too
            lapor(i, dict(x, status="gagal", pesan=str(e)))
            for j in range(i + 1, len(butir)):
                lapor(j, dict(butir[j], status="tidak-dijalankan", pesan="dihentikan karena terjemahan mesin gagal"))
            return "Terjemahan dihentikan: %s. Yang sudah diterjemahkan tetap tersimpan." % e
        lapor(i, hasil)
    return "Selesai."


class Pekerja(object):
    """Runs "Terjemahkan semua" jobs, one per programme at a time, and keeps the state of the last job of every
    programme (in memory: a restart of the admin forgets it, the drafts stay)."""

    def __init__(self, mode="latar"):
        self.latar = mode == "latar"
        self._kunci = threading.Lock()
        self._keadaan = {}

    def keadaan(self, kode):
        with self._kunci:
            return copy.deepcopy(self._keadaan.get(kode))

    def mulai(self, kode, butir, kerja):
        """Start a job; False when one runs for this programme already."""
        with self._kunci:
            lama = self._keadaan.get(kode)
            if lama and lama["berjalan"]:
                return False
            self._keadaan[kode] = {"berjalan": True, "mulai": _sekarang(), "selesai": None, "oleh": kerja["oleh"],
                                   "butir": [dict(x, status="menunggu") for x in butir], "pesan": ""}

        def lapor(i, x):
            with self._kunci:
                self._keadaan[kode]["butir"][i] = x

        def tugas():
            try:
                pesan = jalankan(butir, kerja, lapor)
            except Exception:                    # never leave a job "running"; the traceback goes to the server's log
                traceback.print_exc()
                pesan = "Terjemahan berhenti karena galat di server. Yang sudah diterjemahkan tetap tersimpan."
            with self._kunci:
                k = self._keadaan[kode]
                for x in k["butir"]:
                    if x["status"] in ("menunggu", "berjalan"):
                        x.update(status="tidak-dijalankan", pesan="tidak dijalankan")
                k.update(berjalan=False, selesai=_sekarang(), pesan=pesan)
            audit.catat("terjemahkan-semua-selesai", oleh=kerja["oleh"], ip=kerja["ip"], prodi=kode,
                        diterjemahkan=sum(1 for x in self.keadaan(kode)["butir"] if x["status"] == "diterjemahkan"),
                        butir=len(butir))
        if self.latar:
            threading.Thread(target=tugas, name="terjemahkan-semua-%s" % kode, daemon=True).start()
        else:
            tugas()
        return True


# ------------------------------------------------------------------ the admin pages

def pasang(app, alat):
    import isi_admin
    import pengumuman_admin

    def daftar_halaman(kode):
        """The programme's pages in menu order, without the optional ones it hides (no quota spent on them)."""
        return [(a["id"], a["label"]) for _label, anak in isi_admin.halaman_prodi(kode) for a in anak
                if not a.get("sembunyi")]

    def boleh_bagi(akun):
        return lambda b: pengumuman_admin.boleh_ubah(akun, b)

    def kode_semua():
        return [r["kode_pddikti"] for r in registri.baca()["prodi"]]

    def sisa_hari_ini(kode):
        pakai = int(terjemah_mesin.pemakaian(kode)["hari"].get(terjemah_mesin.hari_ini(), 0))
        return max(0, alat.batas_terjemah[0] - pakai)

    @app.route("/prodi/<kode>/terjemahkan-semua")
    @akses("prodi")
    def terjemahkan_semua(kode):
        isi_admin.perlu_inggris()
        keadaan = alat.terjemah_semua.keadaan(kode)
        butir, dilewati = ([], [])
        if alat.penerjemah is not None and not (keadaan and keadaan["berjalan"]):
            butir, dilewati = rencana(kode, daftar_halaman(kode), boleh_bagi(g.akun))
        return render_template("terjemahkan_semua.html", pr=g.prodi, keadaan=keadaan, butir=butir, dilewati=dilewati,
                               penyedia=alat.penerjemah.nama if alat.penerjemah is not None else None,
                               karakter=sum(x["karakter"] for x in butir), teks=sum(x["teks"] for x in butir),
                               sisa=sisa_hari_ini(kode) if alat.penerjemah is not None else 0, NAMA_HASIL=NAMA_HASIL,
                               admin=pengumuman_admin.adalah_admin(g.akun))

    @app.route("/prodi/<kode>/terjemahkan-semua", methods=["POST"])
    @akses("prodi")
    def terjemahkan_semua_mulai(kode):
        isi_admin.perlu_inggris()
        if alat.penerjemah is None:
            abort(400)
        butir, _dilewati = rencana(kode, daftar_halaman(kode), boleh_bagi(g.akun))
        if not butir:
            flash("Tidak ada yang perlu diterjemahkan: semua teks halaman dan pengumuman yang dapat Anda ubah sudah "
                  "punya terjemahan Inggris.", "info")
            return redirect(url_for("terjemahkan_semua", kode=kode))
        p = data_prodi.efektif(kode) or {}
        kerja = {"kode": kode, "oleh": g.akun["nama"], "ip": request.remote_addr, "penyedia": alat.penerjemah,
                 "batas": alat.batas_terjemah, "kode_semua": kode_semua(), "boleh": boleh_bagi(dict(g.akun)),
                 "glos": terjemah_mesin.glosarium(p, data_prodi.unit_per_kode().values(),
                                                  lokasi.baca("warisan/universitas"))}
        if not alat.terjemah_semua.mulai(kode, butir, kerja):
            flash("Terjemahkan semua sedang berjalan untuk prodi ini; tunggu sampai selesai.", "info")
            return redirect(url_for("terjemahkan_semua", kode=kode))
        alat.catat("terjemahkan-semua-dimulai", prodi=kode, butir=len(butir),
                   karakter=sum(x["karakter"] for x in butir), penyedia=alat.penerjemah.nama)
        keadaan = alat.terjemah_semua.keadaan(kode)
        if keadaan and keadaan["berjalan"]:
            flash("Terjemahan berjalan: %d halaman dan pengumuman. Halaman ini memuat ulang sendiri sampai selesai; "
                  "Anda boleh membuka halaman lain sementara itu." % len(butir), "ok")
        else:
            flash("Terjemahan selesai. Periksa setiap halaman dan pengumuman yang diterjemahkan sebelum mengajukan atau "
                  "menerbitkannya.", "ok")
        return redirect(url_for("terjemahkan_semua", kode=kode))
