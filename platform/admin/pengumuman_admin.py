# -*- coding: utf-8 -*-
"""Announcements and news of a programme in the admin (langkah 6, K-P14). akses("prodi"): operators too.

    /prodi/<kode>/pengumuman                 list (?status=menunggu|draf|terbit|ditarik; ?en=mesin: English versions with
                                             machine translations not checked yet)
    /prodi/<kode>/pengumuman/baru            form; POST creates
    /prodi/<kode>/pengumuman/<id>            form of one item; POST saves it
    /prodi/<kode>/pengumuman/<id>/status     POST aksi=ajukan|batal|terbitkan|kembalikan|tarik|arsipkan

The form also holds the item's English version (Fase 5 langkah 4, K-P37), saved with it under the same rules; its
button "Terjemahkan dari versi Indonesia" (aksi_simpan=terjemahkan) saves the form, then fills the empty English
texts with machine translations marked to be checked (terjemah_mesin.py, the same limits as the pages).

Who may do what (checked here for every request, whatever the form says):
    operator   writes drafts and submits them; changes and withdraws only its own items while they are a draft or
               waiting; never publishes
    admin      (and superadmin) everything: writes, changes any item, publishes, sends back with a note, withdraws
Nothing is ever deleted (K-P14): an item leaves the site as "ditarik" and stays in the data and the history.
Photos and PDFs go through media.py (re-encoded photos, checked PDFs) before anything is stored.
"""
from __future__ import print_function

import datetime
import os
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))
sys.path.insert(0, ADMIN)
sys.path.insert(0, os.path.join(os.path.dirname(ADMIN), "bangun"))

from flask import abort, flash, g, redirect, render_template, request, url_for  # noqa: E402

import data_prodi  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import pengumuman as pg  # noqa: E402
import registri  # noqa: E402
import terjemah_mesin  # noqa: E402
from akses import akses  # noqa: E402

PRIVASI = ("Jangan mengunggah data pribadi: NIK, nomor HP, alamat rumah, nilai, atau daftar mahasiswa beserta NIM dan "
           "nilainya. Foto orang sebaiknya atas izin yang bersangkutan.")
# action -> (statuses it applies to, new status, admin only)
AKSI = {"ajukan": (("draf",), "menunggu", False), "batal": (("menunggu",), "draf", False),
        "arsipkan": (("draf",), "ditarik", False), "terbitkan": (("draf", "menunggu", "ditarik"), "terbit", True),
        "kembalikan": (("menunggu",), "draf", True), "tarik": (("terbit",), "ditarik", True)}
NAMA_STATUS = {"draf": "Draf", "menunggu": "Menunggu persetujuan", "terbit": "Terbit", "ditarik": "Ditarik"}
NAMA_EN = {"kosong": "Belum ada", "belum-lengkap": "Belum lengkap", "mesin": "Terjemahan mesin belum diperiksa",
           "siap": "Lengkap"}


def en_dari_formulir(f, lama, id_baru):
    """The English version from the form. lama: the stored item's "en"; id_baru: the Indonesian texts being saved.
    A machine translation stays marked until its text is changed or the checkbox periksa_en is ticked; "asal" (the
    Indonesian text an English text was written for) moves on for a text that changed, and for all with periksa_en."""
    lama = lama or {}
    periksa = f.get("periksa_en") == "1"
    teks = {k: f.get("en_" + k, "").replace("\r\n", "\n").strip() for k in pg.TEKS_EN}
    if not any(teks.values()):
        return {}
    mesin = {k: v for k, v in (lama.get("mesin") or {}).items() if not periksa and teks.get(k) == v}
    asal = {}
    for k in pg.TEKS_EN:
        if not teks[k]:
            continue
        if periksa or teks[k] != (lama.get(k) or "") or k not in (lama.get("asal") or {}):
            asal[k] = id_baru.get(k) or ""
        else:
            asal[k] = lama["asal"][k]
    hasil = dict(teks, asal=asal)
    if mesin:
        hasil["mesin"] = mesin
    return hasil


def adalah_admin(akun):
    return akun["peran"] in ("super", "admin")


def boleh_ubah(akun, b):
    """May this account change item b (its text and files)?"""
    return adalah_admin(akun) or (b.get("oleh") == akun["nama"] and b["status"] in ("draf", "menunggu"))


def boleh_lihat(akun, b):
    return adalah_admin(akun) or b.get("oleh") == akun["nama"]


def pasang(app, alat):

    def item(kode, id_):
        try:
            b = pg.cari(kode, id_)
        except pg.GagalPengumuman:
            abort(404)
        if not boleh_lihat(g.akun, b):
            abort(403)
        return b

    def bangun(kode):
        r = registri.cari(registri.baca(), kode)
        if r and r.get("aktif"):
            alat.antrean.minta(kode, g.akun["nama"])

    def isian_teks(f):
        return {"judul": f.get("judul", "").strip(), "tanggal": f.get("tanggal", "").strip(),
                "kategori": f.get("kategori", ""), "ringkasan": f.get("ringkasan", "").strip(),
                "isi": f.get("isi", "").replace("\r\n", "\n").strip(), "sematkan": f.get("sematkan") == "1",
                "kedaluwarsa": f.get("kedaluwarsa", "").strip()}

    def periksa_dulu(isian, status, b=None):
        """Check the texts before any file is stored (a refused form leaves no file behind)."""
        calon = dict(b) if b else {"id": "2000-01-01-x", "foto": [], "pdf": [], "oleh": g.akun["nama"]}  # id made on saving
        calon.update(isian)
        calon["status"] = status
        return pg.periksa(calon)

    def media_baru(kode, f, files):
        """Photos and PDFs added in this form: ([photo records], [pdf records]); ValueError with the reason."""
        foto, pdf = [], []
        unggah = files.get("foto")
        if unggah and unggah.filename:
            foto.append(media.simpan_foto(kode, unggah.read(media.MAKS_FOTO + 1), f.get("foto_alt", "")))
        unggah = files.get("pdf")
        if unggah and unggah.filename:
            pdf.append(media.simpan_pdf(kode, unggah.read(media.MAKS_PDF + 1), f.get("pdf_judul", "")))
        return foto, pdf

    def status_baru(aksi_simpan, sekarang=None):
        """The status after a save button: "terbit" (admins only), "ajukan" (a draft is submitted), anything else keeps
        the status (a new item becomes a draft)."""
        if aksi_simpan == "terbit" and adalah_admin(g.akun):
            return "terbit"
        if aksi_simpan == "ajukan" and sekarang in (None, "draf"):
            return "menunggu"
        return sekarang or "draf"

    def halaman_form(kode, b=None, isian=None, kode_status=200):
        isian = isian or (b or {})
        mesin = None
        if b and alat.penerjemah is not None:            # what "Terjemahkan dari versi Indonesia" would send
            kosong_, semua = pg.teks_mesin(b), pg.teks_mesin(b, timpa=True)
            pakai = int(terjemah_mesin.pemakaian(kode)["hari"].get(terjemah_mesin.hari_ini(), 0))
            mesin = {"penyedia": alat.penerjemah.nama, "n": len(kosong_), "karakter": sum(map(len, kosong_)),
                     "n_semua": len(semua), "sisa": max(0, alat.batas_terjemah[0] - pakai)}
        return render_template("pengumuman_form.html", pr=g.prodi, b=b, isian=isian, en=isian.get("en") or {},
                               kategori=pg.baca_kategori(),
                               admin=adalah_admin(g.akun), privasi=PRIVASI, maks=pg.MAKS, maks_foto=pg.MAKS_FOTO,
                               maks_pdf=pg.MAKS_PDF, boleh=boleh_ubah(g.akun, b) if b else True,
                               hari_ini=datetime.date.today().isoformat(), NAMA_STATUS=NAMA_STATUS,
                               keadaan_en=pg.keadaan_en(isian), NAMA_EN=NAMA_EN, mesin=mesin,
                               penerjemah_ada=alat.penerjemah is not None,
                               basi_en=pg.perlu_diperbarui(b) if b else [], label_en=pg.LABEL_EN,
                               inggris_aktif=bool((registri.cari(registri.baca(), kode) or {}).get("inggris")),
                               pratinjau=_pratinjau(b), pratinjau_en=_pratinjau(b.get("en") if b else None)), kode_status

    def terjemahkan(kode, id_):
        """Fill the English texts of a saved item with machine translations (marked "mesin"); False when nothing was
        translated (the reason is flashed)."""
        b = pg.cari(kode, id_)
        timpa = request.form.get("timpa") == "1"
        sasaran = pg.teks_mesin(b, timpa)
        n = sum(len(t) for t in sasaran)
        try:
            if not sasaran:
                raise terjemah_mesin.GagalTerjemah("semua teks pengumuman ini sudah diterjemahkan")
            terjemah_mesin.periksa_batas(kode, n, [r["kode_pddikti"] for r in registri.baca()["prodi"]],
                                         alat.batas_terjemah)
            p = data_prodi.efektif(kode) or {}
            glos = terjemah_mesin.glosarium(p, data_prodi.unit_per_kode().values(), lokasi.baca("warisan/universitas"))
            hasil = terjemah_mesin.terjemahkan(alat.penerjemah, sasaran, glos)
        except terjemah_mesin.GagalTerjemah as e:
            flash("Terjemahan mesin tidak dijalankan: %s." % e, "galat" if sasaran else "info")
            return False
        terjemah_mesin.catat_pemakaian(kode, n)
        en, jadi, gagal = pg.pasang_mesin(pg.cari(kode, id_), hasil, timpa)
        try:
            pg.ubah(kode, id_, {"en": en}, g.akun["nama"])
        except pg.GagalPengumuman as e:
            flash("Terjemahan mesin tidak disimpan: %s." % e, "galat")
            return False
        alat.catat("pengumuman-en-terjemahan-mesin", prodi=kode, id=id_, teks=jadi, karakter=n,
                   penyedia=alat.penerjemah.nama)
        flash("%d teks diterjemahkan mesin (%s, %d karakter). Periksa setiap isian bertanda “terjemahan mesin”: "
              "versi Inggris baru tampil di situs setelah diperiksa.%s" % (
                  jadi, alat.penerjemah.nama, n,
                  " %d teks tidak kembali utuh dan dibiarkan kosong; terjemahkan sendiri." % gagal if gagal else ""), "ok")
        return True

    def _pratinjau(b):
        if not b or not b.get("isi"):
            return ""
        import bangun as bangun_mod
        return bangun_mod.teks_isi(b["isi"])

    # -------------------------------------------------------------- list

    @app.route("/prodi/<kode>/pengumuman")
    @akses("prodi")
    def pengumuman_daftar(kode):
        status, en = request.args.get("status", ""), request.args.get("en", "")
        if (status and status not in pg.STATUS) or en not in ("", "mesin"):
            abort(404)
        semua = [b for b in pg.baca(kode)["butir"] if boleh_lihat(g.akun, b)]
        jumlah = {s: sum(1 for b in semua if b["status"] == s) for s in pg.STATUS}
        jumlah_mesin = sum(1 for b in semua if pg.keadaan_en(b) == "mesin")
        pilih = sorted((b for b in semua if (not status or b["status"] == status)
                        and (not en or pg.keadaan_en(b) == "mesin")),
                       key=lambda b: (b["tanggal"], b.get("dibuat", "")), reverse=True)
        daftar = [b for b in pilih if b["status"] == "menunggu"] + [b for b in pilih if b["status"] != "menunggu"]
        label = {k["id"]: k["label"] for k in pg.baca_kategori()}
        return render_template("pengumuman_daftar.html", pr=g.prodi, daftar=daftar, jumlah=jumlah, status=status,
                               NAMA_STATUS=NAMA_STATUS, label=label, admin=adalah_admin(g.akun),
                               keadaan_en=pg.keadaan_en, NAMA_EN=NAMA_EN, en=en, jumlah_mesin=jumlah_mesin,
                               penyedia=alat.penerjemah.nama if alat.penerjemah is not None else None)

    # -------------------------------------------------------------- new

    @app.route("/prodi/<kode>/pengumuman/baru")
    @akses("prodi")
    def pengumuman_baru(kode):
        return halaman_form(kode, isian={"tanggal": datetime.date.today().isoformat(), "kategori": "akademik"})

    @app.route("/prodi/<kode>/pengumuman/baru", methods=["POST"])
    @akses("prodi")
    def pengumuman_buat(kode):
        isian = isian_teks(request.form)
        isian["en"] = en_dari_formulir(request.form, {}, isian)
        status = status_baru(request.form.get("aksi_simpan"))
        masalah = periksa_dulu(isian, status)
        if masalah:
            flash("Pengumuman tidak disimpan: %s" % "; ".join(masalah), "galat")
            return halaman_form(kode, isian=isian, kode_status=400)
        try:
            foto, pdf = media_baru(kode, request.form, request.files)
            id_ = pg.tambah(kode, dict(isian, foto=foto, pdf=pdf), g.akun["nama"], status)
        except (ValueError, pg.GagalPengumuman) as e:
            flash("Pengumuman tidak disimpan: %s" % e, "galat")
            return halaman_form(kode, isian=isian, kode_status=400)
        alat.catat("pengumuman-dibuat", prodi=kode, id=id_, status=status)
        if status == "terbit":
            bangun(kode)
        flash({"terbit": "Pengumuman diterbitkan; situs prodi dibangun ulang.",
               "menunggu": "Pengumuman diajukan; admin prodi akan memeriksa dan menerbitkannya.",
               "draf": "Draf disimpan."}[status], "ok")
        return redirect(url_for("pengumuman_ubah", kode=kode, id_=id_))

    # -------------------------------------------------------------- one item

    @app.route("/prodi/<kode>/pengumuman/<id_>")
    @akses("prodi")
    def pengumuman_ubah(kode, id_):
        return halaman_form(kode, b=item(kode, id_))

    @app.route("/prodi/<kode>/pengumuman/<id_>", methods=["POST"])
    @akses("prodi")
    def pengumuman_simpan(kode, id_):
        b = item(kode, id_)
        if not boleh_ubah(g.akun, b):
            abort(403, "Pengumuman ini tidak dapat Anda ubah lagi (sudah terbit atau milik akun lain).")
        f = request.form
        isian = isian_teks(f)
        isian["en"] = en_dari_formulir(f, b.get("en"), isian)
        # photos kept, with their texts; the one chosen as main photo goes first
        foto = []
        for i, x in enumerate(b.get("foto", [])):
            if f.get("foto-%d-hapus" % i):
                continue
            foto.append((f.get("foto_utama") == str(i), dict(x, alt=f.get("foto-%d-alt" % i, x.get("alt", "")).strip())))
        foto = [x for utama, x in foto if utama] + [x for utama, x in foto if not utama]
        pdf = [dict(x, judul=f.get("pdf-%d-judul" % i, x.get("judul", "")).strip())
               for i, x in enumerate(b.get("pdf", [])) if not f.get("pdf-%d-hapus" % i)]
        status = status_baru(f.get("aksi_simpan"), b["status"])
        masalah = periksa_dulu(dict(isian, foto=foto, pdf=pdf), status, b)
        if masalah:
            flash("Perubahan tidak disimpan: %s" % "; ".join(masalah), "galat")
            return halaman_form(kode, b=b, isian=dict(b, **isian), kode_status=400)
        try:
            foto_baru, pdf_baru = media_baru(kode, f, request.files)
            if len(foto) + len(foto_baru) > pg.MAKS_FOTO or len(pdf) + len(pdf_baru) > pg.MAKS_PDF:
                raise pg.GagalPengumuman("paling banyak %d foto dan %d PDF" % (pg.MAKS_FOTO, pg.MAKS_PDF))
            pg.ubah(kode, id_, dict(isian, foto=foto + foto_baru, pdf=pdf + pdf_baru), g.akun["nama"])
            if status != b["status"]:
                pg.ganti_status(kode, id_, status, g.akun["nama"])
        except (ValueError, pg.GagalPengumuman) as e:
            flash("Perubahan tidak disimpan: %s" % e, "galat")
            return halaman_form(kode, b=b, isian=dict(b, **isian), kode_status=400)
        alat.catat("pengumuman-diubah", prodi=kode, id=id_, status=status)
        diterjemahkan = f.get("aksi_simpan") == "terjemahkan" and alat.penerjemah is not None and terjemahkan(kode, id_)
        if "terbit" in (status, b["status"]):
            bangun(kode)
        if not diterjemahkan:
            flash("Perubahan disimpan%s." % ("; situs prodi dibangun ulang" if "terbit" in (status, b["status"]) else ""),
                  "ok")
        return redirect(url_for("pengumuman_ubah", kode=kode, id_=id_))

    @app.route("/prodi/<kode>/pengumuman/<id_>/status", methods=["POST"])
    @akses("prodi")
    def pengumuman_status(kode, id_):
        b = item(kode, id_)
        aksi = request.form.get("aksi", "")
        if aksi not in AKSI:
            abort(400)
        dari, ke, admin_saja = AKSI[aksi]
        if admin_saja and not adalah_admin(g.akun):
            abort(403, "Hanya admin prodi yang dapat melakukan ini.")
        if not adalah_admin(g.akun) and b.get("oleh") != g.akun["nama"]:
            abort(403)
        if b["status"] not in dari:
            flash("Tindakan ini tidak berlaku untuk pengumuman berstatus %s." % NAMA_STATUS[b["status"]].lower(), "galat")
            return redirect(url_for("pengumuman_ubah", kode=kode, id_=id_))
        try:
            if aksi == "kembalikan":
                pg.kembalikan(kode, id_, request.form.get("catatan", ""), g.akun["nama"])
            else:
                pg.ganti_status(kode, id_, ke, g.akun["nama"])
        except pg.GagalPengumuman as e:
            flash("Tidak berhasil: %s" % e, "galat")
            return redirect(url_for("pengumuman_ubah", kode=kode, id_=id_))
        alat.catat("pengumuman-%s" % aksi, prodi=kode, id=id_, status=ke)
        if "terbit" in (ke, b["status"]):
            bangun(kode)
        flash({"ajukan": "Diajukan untuk diterbitkan.", "batal": "Pengajuan dibatalkan; kembali menjadi draf.",
               "arsipkan": "Draf diarsipkan.", "terbitkan": "Diterbitkan; situs prodi dibangun ulang.",
               "kembalikan": "Dikembalikan ke penulisnya dengan catatan.",
               "tarik": "Ditarik dari situs; situs prodi dibangun ulang."}[aksi], "ok")
        return redirect(url_for("pengumuman_ubah", kode=kode, id_=id_))
