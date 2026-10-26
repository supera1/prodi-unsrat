# -*- coding: utf-8 -*-
"""Superadmin pages of the admin (langkah 5, rencana §8). Every route here is akses("super").

    /                         (dasbor, app.py) for the superadmin: summary and what needs attention
    /super/prodi              registered programmes; programmes new in www, to register with a slug
    /super/prodi/<kode>       one programme: official data, slug and old slugs, active, lecturer link, rebuild
    /super/dosen              bulk import of lecturer links (CSV/Excel) with a preview
    /super/tarik              the official data from www: preview, then apply
    /super/riwayat            version history of the data files: compare with now, restore
    /super/bangun             rebuild status, rebuild everything
    /super/akun/<id>          an account's name, role and programmes

Every change is logged (audit.py) and followed by a rebuild of what it affects (pembangun.py): one programme for its
lecturer link or a restored file of its own, everything for a slug, an active switch, official data or the registry.
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import re
import secrets
import sys
import time

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))
sys.path.insert(0, ADMIN)

from flask import abort, flash, g, make_response, redirect, render_template, request, url_for  # noqa: E402

import akun as akun_mod  # noqa: E402
import beda  # noqa: E402
import data_prodi  # noqa: E402
import impor_dosen  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import slug as slug_mod  # noqa: E402
import tarik_www  # noqa: E402
from akses import akses  # noqa: E402

POLA_KODE = re.compile(r"^[0-9A-Za-z]{3,12}$")
POLA_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,64}$")
POLA_FILTER_BERKAS = re.compile(r"^(registri|warisan(/[a-z]+)?|prodi/[0-9A-Za-z]{3,12}(/[a-z][a-z0-9-]*)?)$")
SEMENTARA_DETIK = 30 * 60


def pasang(app, alat):
    """Add the superadmin routes. alat: helpers of app.py (catat, antrean, info_prodi, kelompok_prodi)."""

    # -------------------------------------------------------------- helpers

    def kode_terdaftar(kode):
        r = registri.cari(registri.baca(), kode) if POLA_KODE.match(kode or "") else None
        if r is None:
            abort(404)
        return r

    def ikhtisar():
        """One row per registered programme, with what the superadmin needs to see about it (its effective data:
        www's with the programme's own changes)."""
        war = data_prodi.semua_efektif()
        bentrok = data_prodi.semua_bentrok()
        semua_akun = akun_mod.semua()
        hasil = []
        for r in registri.baca()["prodi"]:
            p = war.get(r["kode_pddikti"])
            kode = r["kode_pddikti"]
            hasil.append({
                "kode": kode, "slug": r["slug"], "slug_lama": r.get("slug_lama", []), "aktif": r.get("aktif", False),
                "dosen_url": r.get("dosen_url") or "", "diubah": r.get("diubah", ""),
                "nama": registri.nama_tampil(p) if p else "(tidak ada di data resmi)", "jenjang": p["jenjang"] if p else "",
                "unit": p["unit"] if p else "", "hilang": p is None or bool(p.get("hilang_dari_www")),
                "kekurangan": tarik_www.kekurangan(p) if p else [],
                "admin": sum(1 for a in semua_akun if a["aktif"] and a["peran"] == "admin" and kode in a["prodi"]),
                "operator": sum(1 for a in semua_akun if a["aktif"] and a["peran"] == "operator" and kode in a["prodi"]),
                "timpaan": sorted(data_prodi.baca(kode)["timpaan"]), "bentrok": [b[0] for b in bentrok.get(kode, [])],
            })
        return sorted(hasil, key=registri.kunci_urut)

    def ringkasan():
        baris = ikhtisar()
        aktif = [r for r in baris if r["aktif"]]
        return {"terdaftar": len(baris), "aktif": len(aktif), "belum": registri.belum_terdaftar(),
                "tanpa_admin": [r for r in aktif if not r["admin"]], "hilang": [r for r in baris if r["hilang"]],
                "kurang": [r for r in aktif if r["kekurangan"]], "tanpa_dosen": [r for r in aktif if not r["dosen_url"]],
                "bentrok": [r for r in baris if r["bentrok"]], "timpaan": sum(1 for r in baris if r["timpaan"]),
                "meta": lokasi.baca("warisan/meta") or {}, "bangun": alat.antrean.status}
    alat.ringkasan = ringkasan
    alat.nama_berkas = lambda berkas: nama_berkas(berkas)

    def oleh():
        return g.akun["nama"]

    def bangun(kode=None):
        alat.antrean.minta(kode, oleh())

    # one-time stores for two-step forms (a preview, then "apply"), kept outside the data folder
    def folder_sementara():
        return os.path.join(lokasi.rahasia(), "sementara")

    def simpan_sementara(jenis, isi):
        folder = folder_sementara()
        os.makedirs(folder, exist_ok=True)
        for n in os.listdir(folder):                    # forget what was never applied
            path = os.path.join(folder, n)
            if time.time() - os.path.getmtime(path) > SEMENTARA_DETIK:
                os.remove(path)
        token = secrets.token_urlsafe(24)
        with io.open(os.open(os.path.join(folder, token + ".json"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                     "w", encoding="utf-8") as f:
            json.dump({"jenis": jenis, "oleh": g.akun["id"], "waktu": time.time(), "isi": isi}, f)
        return token

    def ambil_sementara(jenis, token):
        """The stored content once (it is removed), or None if unknown, of another account, of another kind or old."""
        if not POLA_TOKEN.match(token or ""):
            return None
        path = os.path.join(folder_sementara(), token + ".json")
        if not os.path.isfile(path):
            return None
        with io.open(path, encoding="utf-8") as f:
            data = json.load(f)
        os.remove(path)
        if data.get("jenis") != jenis or data.get("oleh") != g.akun["id"] or time.time() - data.get("waktu", 0) > SEMENTARA_DETIK:
            return None
        return data["isi"]

    # -------------------------------------------------------------- programmes

    def halaman_prodi(kode_status=200):
        belum = [dict(p, tampil=registri.nama_tampil(p), usulan=slug_mod.usulan(p["jenjang"], p["nama"]))
                 for p in registri.belum_terdaftar()]
        return render_template("super_prodi.html", baris=ikhtisar(), belum=belum), kode_status

    @app.route("/super/prodi")
    @akses("super")
    def super_prodi():
        return halaman_prodi()

    @app.route("/super/prodi/daftar", methods=["POST"])
    @akses("super")
    def super_prodi_daftar():
        kode = (request.form.get("kode") or "").strip()
        slug = (request.form.get("slug") or "").strip().lower()
        try:
            registri.daftarkan(kode, slug, oleh())
        except registri.GagalRegistri as e:
            flash("Prodi %s tidak didaftarkan: %s" % (kode, e), "galat")
            return halaman_prodi(400)
        alat.catat("prodi-didaftarkan", prodi=kode, slug=slug)
        bangun(kode)
        flash("Prodi %s didaftarkan di /%s/ dan sedang dibangun." % (kode, slug), "ok")
        return redirect(url_for("super_prodi_detail", kode=kode))

    def halaman_detail(kode, kode_status=200):
        r = kode_terdaftar(kode)
        baris = [b for b in ikhtisar() if b["kode"] == kode][0]
        p = data_prodi.semua_efektif().get(kode)
        anggota = [a for a in akun_mod.semua() if kode in a["prodi"]]
        situs = alat.info_prodi(kode)
        return render_template("super_prodi_detail.html", r=r, b=baris, p=p, anggota=anggota, situs=situs,
                               timpaan=baris["timpaan"], bentrok=baris["bentrok"],
                               riwayat_prodi=[v for v in riwayat.daftar(500) if v["berkas"].startswith("prodi/%s/" % kode)][:10]), kode_status

    @app.route("/super/prodi/<kode>")
    @akses("super")
    def super_prodi_detail(kode):
        return halaman_detail(kode)

    @app.route("/super/prodi/<kode>/slug", methods=["POST"])
    @akses("super")
    def super_prodi_slug(kode):
        r = kode_terdaftar(kode)
        baru, lama = (request.form.get("slug") or "").strip().lower(), r["slug"]
        if baru == lama:
            flash("Slug tidak berubah.", "info")
            return redirect(url_for("super_prodi_detail", kode=kode))
        try:
            registri.ganti_slug(kode, baru, oleh())
        except registri.GagalRegistri as e:
            flash("Slug tidak diubah: %s" % e, "galat")
            return halaman_detail(kode, 400)
        alat.catat("slug-diubah", prodi=kode, lama=lama, baru=baru)
        bangun()                                       # the old folder must go and the redirects be rewritten
        flash("Slug diubah: /%s/ → /%s/. Alamat lama dialihkan permanen (301) setelah web server memuat ulang "
              "konfigurasinya." % (lama, baru), "ok")
        return redirect(url_for("super_prodi_detail", kode=kode))

    @app.route("/super/prodi/<kode>/aktif", methods=["POST"])
    @akses("super")
    def super_prodi_aktif(kode):
        kode_terdaftar(kode)
        aktif = request.form.get("aktif") == "1"
        registri.atur(kode, oleh(), aktif=aktif)
        alat.catat("prodi-diaktifkan" if aktif else "prodi-dinonaktifkan", prodi=kode)
        bangun()
        flash("Situs prodi %s. Situs dibangun ulang." % ("diaktifkan" if aktif else "dinonaktifkan"), "ok")
        return redirect(url_for("super_prodi_detail", kode=kode))

    @app.route("/super/prodi/<kode>/dosen", methods=["POST"])
    @akses("super")
    def super_prodi_dosen(kode):
        r = kode_terdaftar(kode)
        url = (request.form.get("dosen_url") or "").strip()
        try:
            registri.atur(kode, oleh(), dosen_url=url)
        except registri.GagalRegistri as e:
            flash("Tautan dosen tidak disimpan: %s" % e, "galat")
            return halaman_detail(kode, 400)
        alat.catat("tautan-dosen-diubah", prodi=kode, lama=r.get("dosen_url") or "", baru=url)
        if r.get("aktif"):
            bangun(kode)
        flash("Tautan dosen %s." % ("disimpan" if url else "dikosongkan"), "ok")
        return redirect(url_for("super_prodi_detail", kode=kode))

    @app.route("/super/prodi/<kode>/bangun", methods=["POST"])
    @akses("super")
    def super_prodi_bangun(kode):
        r = kode_terdaftar(kode)
        if not r.get("aktif"):
            flash("Situs prodi ini nonaktif; aktifkan dulu.", "galat")
            return redirect(url_for("super_prodi_detail", kode=kode))
        alat.catat("bangun-diminta", prodi=kode, cakupan=kode)
        bangun(kode)
        flash("Situs prodi sedang dibangun ulang.", "ok")
        return redirect(url_for("super_prodi_detail", kode=kode))

    # -------------------------------------------------------------- lecturer links

    def nama_semua():
        return {k: registri.nama_tampil(p) for k, p in data_prodi.semua_efektif().items()}

    @app.route("/super/dosen")
    @akses("super")
    def super_dosen():
        baris = ikhtisar()
        return render_template("super_dosen.html", baris=baris, terisi=sum(1 for b in baris if b["dosen_url"]))

    @app.route("/super/dosen/templat.csv")
    @akses("super")
    def super_dosen_templat():
        info = {k: {"jenjang": p["jenjang"], "nama": p["nama"], "unit": p["unit"]} for k, p in registri.warisan_per_kode().items()}
        resp = make_response(impor_dosen.templat_csv(registri.baca()["prodi"], info))
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = 'attachment; filename="tautan-dosen-prodi.csv"'
        return resp

    @app.route("/super/dosen/impor", methods=["POST"])
    @akses("super")
    def super_dosen_impor():
        berkas = request.files.get("berkas")
        try:
            if not berkas or not berkas.filename:
                raise ValueError("Pilih berkas CSV atau Excel (.xlsx).")
            baris = impor_dosen.baca_tabel(berkas.filename, berkas.read(impor_dosen.MAKS_BERKAS + 1))
        except ValueError as e:
            flash(str(e), "galat")
            return render_template("super_dosen.html", baris=ikhtisar(), terisi=None), 400
        rencana = impor_dosen.rencana(baris, registri.baca()["prodi"], nama_semua())
        token = simpan_sementara("dosen", {u["kode"]: u["baru"] for u in rencana["ubah"]}) if rencana["ubah"] else None
        alat.catat("tautan-dosen-pratinjau", berkas=berkas.filename[:100], ubah=len(rencana["ubah"]), galat=len(rencana["galat"]))
        return render_template("super_dosen_pratinjau.html", rencana=rencana, token=token, nama_berkas=berkas.filename)

    @app.route("/super/dosen/terapkan", methods=["POST"])
    @akses("super")
    def super_dosen_terapkan():
        ubah = ambil_sementara("dosen", request.form.get("token"))
        if ubah is None:
            flash("Pratinjau impor sudah tidak berlaku (dipakai, kedaluwarsa, atau milik akun lain). Unggah ulang berkasnya.",
                  "galat")
            return redirect(url_for("super_dosen"))
        try:
            registri.atur_banyak(ubah, oleh())
        except registri.GagalRegistri as e:
            flash("Impor dibatalkan: %s" % e, "galat")
            return redirect(url_for("super_dosen"))
        alat.catat("tautan-dosen-diimpor", prodi=sorted(ubah), jumlah=len(ubah))
        aktif = {r["kode_pddikti"] for r in registri.baca()["prodi"] if r.get("aktif")}
        for kode in sorted(set(ubah) & aktif):
            bangun(kode)                               # many at once become one full rebuild (pembangun.py)
        flash("Tautan dosen %d prodi disimpan; situsnya dibangun ulang." % len(ubah), "ok")
        return redirect(url_for("super_dosen"))

    # -------------------------------------------------------------- official data from www

    def sidik_sumber(hasil):
        return hashlib.sha256(json.dumps(hasil["sumber"]["meta"]["sidik"], sort_keys=True).encode("utf-8")).hexdigest()[:32]

    def halaman_tarik(kode_status=200, masalah=None):
        meta = lokasi.baca("warisan/meta") or {}
        if masalah is None:
            try:
                hasil = tarik_www.pratinjau()
            except tarik_www.GagalTarik as e:
                masalah = e.masalah
        if masalah is not None:
            return render_template("super_tarik.html", masalah=masalah, meta=meta, laporan=None, sidik=""), kode_status
        nama = {p["kode_pddikti"]: registri.nama_tampil(p) for p in hasil["prodi"]["program"]}
        return render_template("super_tarik.html", masalah=None, meta=meta, laporan=hasil["laporan"], nama=nama,
                               ada=tarik_www.ada_perubahan(hasil["laporan"]), sidik=sidik_sumber(hasil),
                               batas_hilang=int(tarik_www.BATAS_HILANG * 100)), kode_status

    @app.route("/super/tarik")
    @akses("super")
    def super_tarik():
        return halaman_tarik()

    @app.route("/super/tarik/terapkan", methods=["POST"])
    @akses("super")
    def super_tarik_terapkan():
        try:
            hasil = tarik_www.pratinjau()
        except tarik_www.GagalTarik as e:
            alat.catat("tarik-data-www-ditolak", masalah=len(e.masalah))
            return halaman_tarik(400, e.masalah)
        if request.form.get("sidik") != sidik_sumber(hasil):
            flash("Data www berubah sejak pratinjau dibuat. Periksa pratinjau terbaru di bawah, lalu terapkan lagi.", "galat")
            return redirect(url_for("super_tarik"))
        try:
            laporan = tarik_www.terapkan(oleh(), paksa=request.form.get("paksa") == "1")
        except tarik_www.GagalTarik as e:
            alat.catat("tarik-data-www-ditolak", masalah=len(e.masalah))
            return halaman_tarik(400, e.masalah)
        if not tarik_www.ada_perubahan(laporan):
            flash("Tidak ada perubahan dari data www.", "info")
            return redirect(url_for("super_tarik"))
        alat.catat("tarik-data-www", baru=len(laporan["baru"]), hilang=len(laporan["hilang"]),
                   berubah=len(laporan["berubah"]), kembali=len(laporan["kembali"]))
        bangun()
        flash("Data resmi dari www diterapkan; semua situs dibangun ulang.", "ok")
        return redirect(url_for("super_tarik"))

    # -------------------------------------------------------------- version history

    def nama_berkas(berkas):
        m = re.match(r"^prodi/([0-9A-Za-z]{3,12})/(.+)$", berkas)
        if m:
            return "%s — %s" % (nama_semua().get(m.group(1), m.group(1)), {"situs": "identitas dan beranda",
                                                                            "pengumuman": "pengumuman",
                                                                            "data": "data prodi"}.get(m.group(2), m.group(2)))
        return {"registri": "Registri prodi (slug, aktif, tautan dosen)", "warisan/prodi": "Data resmi prodi dari www",
                "warisan/unit": "Data fakultas dari www", "warisan/kalender": "Kalender akademik dari www",
                "warisan/universitas": "Identitas universitas dari www", "warisan/meta": "Catatan tarik data"}.get(berkas, berkas)

    @app.route("/super/riwayat")
    @akses("super")
    def super_riwayat():
        saring = request.args.get("berkas", "")
        if saring and not POLA_FILTER_BERKAS.match(saring):
            abort(404)
        semua = riwayat.daftar(5000)
        daftar = [v for v in semua if not saring or v["berkas"] == saring or v["berkas"].startswith(saring + "/")][:300]
        pilihan = sorted({v["berkas"] for v in semua})
        return render_template("super_riwayat.html", daftar=daftar, saring=saring, pilihan=pilihan, nama_berkas=nama_berkas)

    @app.route("/super/riwayat/lihat")
    @akses("super")
    def super_riwayat_lihat():
        berkas, versi = request.args.get("berkas", ""), request.args.get("versi", "")
        try:
            hasil = beda.beda_versi(berkas, versi)
        except ValueError:
            abort(404)
        return render_template("riwayat_lihat.html", berkas=berkas, versi=versi, judul_berkas=nama_berkas(berkas),
                               kembali=url_for("super_riwayat", berkas=berkas),
                               pulihkan=url_for("super_riwayat_pulihkan"), **hasil)

    @app.route("/super/riwayat/pulihkan", methods=["POST"])
    @akses("super")
    def super_riwayat_pulihkan():
        berkas, versi = request.form.get("berkas", ""), request.form.get("versi", "")
        try:
            riwayat.pulihkan(berkas, versi, oleh(), "Riwayat")
        except ValueError:
            abort(404)
        m = re.match(r"^prodi/([0-9A-Za-z]{3,12})/", berkas)
        alat.catat("versi-dipulihkan", prodi=m.group(1) if m else None, berkas=berkas, versi=versi)
        aktif = {r["kode_pddikti"] for r in registri.baca()["prodi"] if r.get("aktif")}
        bangun(m.group(1) if m and m.group(1) in aktif else None)
        flash("Versi %s dari %s dipulihkan (isi sebelumnya disimpan sebagai versi baru); situs dibangun ulang." % (
            versi, nama_berkas(berkas)), "ok")
        return redirect(url_for("super_riwayat", berkas=berkas))

    # -------------------------------------------------------------- rebuilds

    @app.route("/super/bangun")
    @akses("super")
    def super_bangun():
        return render_template("super_bangun.html", status=alat.antrean.status)

    @app.route("/super/bangun/semua", methods=["POST"])
    @akses("super")
    def super_bangun_semua():
        alat.catat("bangun-diminta", cakupan="semua")
        bangun()
        flash("Semua situs sedang dibangun ulang.", "ok")
        return redirect(url_for("super_bangun"))

    # -------------------------------------------------------------- accounts: name, role, programmes

    def halaman_ubah_akun(sasaran, kode_status=200):
        return render_template("super_akun_ubah.html", sasaran=sasaran, kelompok=alat.kelompok_prodi()), kode_status

    @app.route("/super/akun/<int:id_>")
    @akses("super")
    def super_akun_ubah(id_):
        sasaran = akun_mod.ambil(id_) or abort(404)
        return halaman_ubah_akun(sasaran)

    @app.route("/super/akun/<int:id_>/ubah", methods=["POST"])
    @akses("super")
    def super_akun_simpan(id_):
        sasaran = akun_mod.ambil(id_) or abort(404)
        f = request.form
        prodi = alat.prodi_dari_formulir()
        try:
            baru = akun_mod.ubah(g.akun, id_, f.get("nama_lengkap", ""), f.get("peran", ""), prodi)
        except akun_mod.GagalAkun as e:
            flash(str(e), "galat")
            return halaman_ubah_akun(sasaran, 400)
        alat.catat("akun-diubah", prodi=sorted(set(sasaran["prodi"]) | set(baru["prodi"])), akun=baru["nama"],
                   peran_lama=sasaran["peran"], peran=baru["peran"], prodi_lama=",".join(sasaran["prodi"]),
                   prodi_baru=",".join(baru["prodi"]))
        flash("Akun %s disimpan." % baru["nama"], "ok")
        return redirect(url_for("akun_semua"))
