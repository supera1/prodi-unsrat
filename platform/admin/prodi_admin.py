# -*- coding: utf-8 -*-
"""Pages of a programme's admin (akses("prodi", "admin"): the programme's admins and the superadmin), langkah 5b-6.

    /prodi/<kode>/data                     the programme's data (name, degree, credits, accreditation, CPL, ...):
                                           change it here; www's value stays visible next to every changed field (K-P16)
    /prodi/<kode>/data/<field>/www         use www's value again for a field (drop the local change)
    /prodi/<kode>/data/<field>/tetap       keep the local value after www changed the field (end the conflict)
    /prodi/<kode>/identitas                palette, social media; /identitas/logo (upload), /identitas/logo/hapus
    /prodi/<kode>/beranda                  the front section of the home page (K-P15); /beranda/foto (upload)
    /prodi/<kode>/menu                     labels, order, hidden optional items
    /prodi/<kode>/riwayat                  versions of the programme's own data files: compare, restore
    /prodi/<kode>/berkas/<path>            an uploaded file of the programme, for previews in the admin
                                           (akses("prodi"): operators see the photos of their drafts too)

Every change is checked by the module that owns the data (data_prodi, tampilan_prodi, menu) before it is written,
logged, and followed by a rebuild of the programme's site.
"""
from __future__ import print_function

import os
import re
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(ADMIN))
sys.path.insert(0, ADMIN)

from flask import abort, flash, g, redirect, render_template, request, send_file, url_for  # noqa: E402

import beda  # noqa: E402
import data_prodi  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import tampilan_prodi  # noqa: E402
import warna as warna_mod  # noqa: E402
from akses import akses  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(ADMIN), "bangun"))
import menu as menu_mod  # noqa: E402

TIPE_BERKAS = {"jpg": "image/jpeg", "png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}

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

    # -------------------------------------------------------------- uploaded files, for previews in the admin

    def url_berkas(kode, rekam):
        return rekam["url"] if "url" in rekam else url_for("berkas_prodi", kode=kode, jalur=rekam["jalur"])
    app.jinja_env.globals["url_berkas"] = url_berkas

    @app.route("/prodi/<kode>/berkas/<path:jalur>")
    @akses("prodi")
    def berkas_prodi(kode, jalur):
        # only files the platform named itself, and only this programme's
        if not media.jalur_sah(jalur) or not jalur.startswith(kode + "/"):
            abort(404)
        path = os.path.join(lokasi.unggahan(), *jalur.split("/"))
        if not os.path.isfile(path):
            abort(404)
        akhiran = jalur.rsplit(".", 1)[1]
        resp = send_file(path, mimetype=TIPE_BERKAS[akhiran], max_age=0)
        if akhiran == "svg":            # an SVG opened by itself may not run anything
            resp.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; img-src data:"
        return resp

    # -------------------------------------------------------------- settings of the site (situs.json)

    def situs(kode):
        return lokasi.baca("prodi/%s/situs" % kode) or {}

    def simpan_situs(kode, perubahan, aksi, pesan, **rinci):
        tampilan_prodi.atur(kode, perubahan, g.akun["nama"], aksi)
        alat.catat(aksi, prodi=kode, **rinci)
        bangun(kode)
        flash(pesan + " Situs prodi dibangun ulang.", "ok")

    def unit_prodi(kode):
        p = data_prodi.efektif(kode)
        return p, data_prodi.unit_per_kode().get(p.get("unit_kode"), {"nama": p.get("unit", "")})

    # identity: palette, social media, logo

    def halaman_identitas(kode, kode_status=200):
        s = situs(kode)
        _p, unit = unit_prodi(kode)
        fakultas = warna_mod.warna_prodi(None, unit.get("bendera"))
        palet = [dict(warna_mod.turunan(x["utama"], x["aksen"]), id=x["id"], nama=x["nama"]) for x in warna_mod.baca_palet()]
        medsos = list(s.get("media_sosial") or [])
        medsos += [{"jenis": "", "url": ""}] * (tampilan_prodi.MAKS_MEDIA_SOSIAL - len(medsos))
        return render_template("prodi_identitas.html", pr=g.prodi, s=s, fakultas=fakultas, palet=palet, medsos=medsos,
                               jenis_medsos=tampilan_prodi.MEDIA_SOSIAL, pilihan=s.get("palet") or warna_mod.BAWAAN,
                               petunjuk_logo="Logo prodi (opsional): SVG, PNG, atau JPG, paling besar 5 MB; tinggi minimal "
                               "168 piksel untuk PNG/JPG; lebar dibagi tinggi 0,5–4. Ditampilkan setinggi 56 piksel di "
                               "samping lambang UNSRAT."), kode_status

    @app.route("/prodi/<kode>/identitas")
    @akses("prodi", "admin")
    def identitas_prodi(kode):
        return halaman_identitas(kode)

    @app.route("/prodi/<kode>/identitas", methods=["POST"])
    @akses("prodi", "admin")
    def identitas_simpan(kode):
        palet = request.form.get("palet") or warna_mod.BAWAAN
        medsos = []
        for i in range(tampilan_prodi.MAKS_MEDIA_SOSIAL):
            jenis, url = request.form.get("medsos-%d-jenis" % i, ""), request.form.get("medsos-%d-url" % i, "").strip()
            if url:
                medsos.append({"jenis": jenis, "url": url})
        try:
            simpan_situs(kode, {"palet": None if palet == warna_mod.BAWAAN else palet, "media_sosial": medsos},
                         "identitas-diubah", "Identitas disimpan.", palet=palet, media_sosial=len(medsos))
        except tampilan_prodi.GagalTampilan as e:
            flash("Identitas tidak disimpan: %s" % e, "galat")
            return halaman_identitas(kode, 400)
        return redirect(url_for("identitas_prodi", kode=kode))

    @app.route("/prodi/<kode>/identitas/logo", methods=["POST"])
    @akses("prodi", "admin")
    def logo_unggah(kode):
        berkas = request.files.get("logo")
        try:
            if not berkas or not berkas.filename:
                raise ValueError("Pilih berkas logo.")
            logo = media.simpan_logo(kode, berkas.read(media.MAKS_LOGO + 1), berkas.filename)
            simpan_situs(kode, {"logo": logo}, "logo-diunggah", "Logo disimpan.", format=logo["format"])
        except (ValueError, tampilan_prodi.GagalTampilan) as e:
            flash("Logo tidak disimpan: %s" % e, "galat")
            return halaman_identitas(kode, 400)
        return redirect(url_for("identitas_prodi", kode=kode))

    @app.route("/prodi/<kode>/identitas/logo/hapus", methods=["POST"])
    @akses("prodi", "admin")
    def logo_hapus(kode):
        if situs(kode).get("logo"):
            simpan_situs(kode, {"logo": None}, "logo-dilepas", "Logo dilepas dari situs (berkasnya tetap tersimpan).")
        return redirect(url_for("identitas_prodi", kode=kode))

    # the front section of the home page

    def halaman_beranda(kode, kode_status=200, isian=None):
        s = situs(kode)
        p, unit = unit_prodi(kode)
        bawaan, resmi = tampilan_prodi.bawaan_dan_resmi(p, unit["nama"])
        beranda = isian if isian is not None else (s.get("beranda") or {})
        return render_template("prodi_beranda.html", pr=g.prodi, s=s, b=beranda, bawaan=bawaan, resmi=resmi,
                               semua_resmi=tampilan_prodi.KARTU_RESMI, maks_tambahan=tampilan_prodi.MAKS_KARTU_TAMBAHAN,
                               petunjuk=media.PETUNJUK_HERO, fokus=media.FOKUS, maks=tampilan_prodi.MAKS,
                               foto=(s.get("beranda") or {}).get("latar", {}).get("foto")), kode_status

    @app.route("/prodi/<kode>/beranda")
    @akses("prodi", "admin")
    def beranda_prodi(kode):
        return halaman_beranda(kode)

    @app.route("/prodi/<kode>/beranda", methods=["POST"])
    @akses("prodi", "admin")
    def beranda_simpan(kode):
        f = request.form
        lama = situs(kode).get("beranda") or {}
        jenis = f.get("latar", "pucat")
        latar = {"jenis": jenis}
        if jenis == "warna":
            latar["warna"] = (f.get("warna") or "").strip().upper()
        elif jenis == "foto":
            foto = (lama.get("latar") or {}).get("foto")
            if not foto:
                flash("Unggah foto latar dulu (formulir di bawah), lalu pilih latar foto.", "galat")
                return halaman_beranda(kode, 400)
            latar["foto"] = foto
        beranda = {"latar": latar}
        for k in ("label", "judul", "subjudul"):
            if f.get(k, "").strip():
                beranda[k] = f.get(k).strip()
        kartu = {}
        for id_ in tampilan_prodi.KARTU_RESMI:
            atur = {}
            if f.get("kartu-%s-label" % id_, "").strip():
                atur["label"] = f.get("kartu-%s-label" % id_).strip()
            if f.get("kartu-%s-urutan" % id_, "").strip():
                try:
                    atur["urutan"] = int(f.get("kartu-%s-urutan" % id_))
                except ValueError:
                    atur["urutan"] = -1                      # refused with the module's message
            if f.get("kartu-%s-sembunyi" % id_):
                atur["sembunyi"] = True
            if atur:
                kartu[id_] = atur
        if kartu:
            beranda["kartu"] = kartu
        tambahan = []
        for i in range(tampilan_prodi.MAKS_KARTU_TAMBAHAN):
            label, nilai = f.get("tambahan-%d-label" % i, "").strip(), f.get("tambahan-%d-nilai" % i, "").strip()
            if label or nilai:
                k = {"label": label, "nilai": nilai, "keterangan": f.get("tambahan-%d-keterangan" % i, "").strip()}
                if f.get("tambahan-%d-urutan" % i, "").strip():
                    try:
                        k["urutan"] = int(f.get("tambahan-%d-urutan" % i))
                    except ValueError:
                        k["urutan"] = -1
                tambahan.append(k)
        if tambahan:
            beranda["kartu_tambahan"] = tambahan
        try:
            simpan_situs(kode, {"tagline": f.get("pengantar", "").strip(), "beranda": beranda}, "beranda-diubah",
                         "Bagian depan beranda disimpan.", latar=jenis)
        except tampilan_prodi.GagalTampilan as e:
            flash("Bagian depan tidak disimpan: %s" % e, "galat")
            return halaman_beranda(kode, 400, isian=beranda)
        return redirect(url_for("beranda_prodi", kode=kode))

    @app.route("/prodi/<kode>/beranda/foto", methods=["POST"])
    @akses("prodi", "admin")
    def beranda_foto(kode):
        berkas = request.files.get("foto")
        try:
            if not berkas or not berkas.filename:
                raise ValueError("Pilih foto latar.")
            tampilan_prodi.ganti_foto(kode, berkas.read(media.MAKS_HERO + 1), request.form.get("fokus", "tengah"),
                                      g.akun["nama"])
        except (ValueError, tampilan_prodi.GagalTampilan) as e:
            flash("Foto latar tidak disimpan: %s" % e, "galat")
            return halaman_beranda(kode, 400)
        alat.catat("foto-latar-diunggah", prodi=kode, fokus=request.form.get("fokus", "tengah"))
        bangun(kode)
        flash("Foto latar disimpan dan dipakai sebagai latar bagian depan. Situs prodi dibangun ulang.", "ok")
        return redirect(url_for("beranda_prodi", kode=kode))

    # menu

    def halaman_menu(kode, kode_status=200, pengaturan=None):
        templat = menu_mod.baca_templat()
        atur = pengaturan if pengaturan is not None else (situs(kode).get("menu") or {})
        return render_template("prodi_menu.html", pr=g.prodi, templat=templat, atur=atur,
                               maks_label=menu_mod.MAKS_LABEL), kode_status

    @app.route("/prodi/<kode>/menu")
    @akses("prodi", "admin")
    def menu_prodi(kode):
        return halaman_menu(kode)

    @app.route("/prodi/<kode>/menu", methods=["POST"])
    @akses("prodi", "admin")
    def menu_simpan(kode):
        f = request.form
        pengaturan = {}
        for b in menu_mod.baca_templat():
            butir = [(b, None)] + [(a, i) for i, a in enumerate(b.get("anak", []))]
            for x, posisi in butir:
                atur = {}
                label = f.get("label-%s" % x["id"], "").strip()
                if label and label != x["label"]:
                    atur["label"] = label
                if posisi is not None and f.get("urutan-%s" % x["id"], "").strip():
                    try:
                        urutan = int(f.get("urutan-%s" % x["id"]))
                    except ValueError:
                        urutan = -1                          # refused with the module's message
                    if urutan != posisi:
                        atur["urutan"] = urutan
                if f.get("sembunyi-%s" % x["id"]):
                    atur["sembunyi"] = True
                if atur:
                    pengaturan[x["id"]] = atur
        try:
            simpan_situs(kode, {"menu": pengaturan}, "menu-diubah", "Menu disimpan.", butir=len(pengaturan))
        except tampilan_prodi.GagalTampilan as e:
            flash("Menu tidak disimpan: %s" % e, "galat")
            return halaman_menu(kode, 400, pengaturan)
        return redirect(url_for("menu_prodi", kode=kode))

    # -------------------------------------------------------------- the programme's version history

    def berkas_milik(kode, berkas):
        if not (berkas or "").startswith("prodi/%s/" % kode):
            abort(404)
        return berkas

    @app.route("/prodi/<kode>/riwayat")
    @akses("prodi", "admin")
    def riwayat_prodi(kode):
        daftar = [v for v in riwayat.daftar(5000) if v["berkas"].startswith("prodi/%s/" % kode)][:300]
        return render_template("riwayat_prodi.html", pr=g.prodi, daftar=daftar, nama_berkas=alat.nama_berkas)

    @app.route("/prodi/<kode>/riwayat/lihat")
    @akses("prodi", "admin")
    def riwayat_prodi_lihat(kode):
        berkas, versi = berkas_milik(kode, request.args.get("berkas", "")), request.args.get("versi", "")
        try:
            hasil = beda.beda_versi(berkas, versi)
        except ValueError:
            abort(404)
        return render_template("riwayat_lihat.html", berkas=berkas, versi=versi, judul_berkas=alat.nama_berkas(berkas),
                               kembali=url_for("riwayat_prodi", kode=kode),
                               pulihkan=url_for("riwayat_prodi_pulihkan", kode=kode), **hasil)

    @app.route("/prodi/<kode>/riwayat/pulihkan", methods=["POST"])
    @akses("prodi", "admin")
    def riwayat_prodi_pulihkan(kode):
        berkas, versi = berkas_milik(kode, request.form.get("berkas", "")), request.form.get("versi", "")
        try:
            riwayat.pulihkan(berkas, versi, g.akun["nama"], "Riwayat prodi")
        except ValueError:
            abort(404)
        alat.catat("versi-dipulihkan", prodi=kode, berkas=berkas, versi=versi)
        bangun(kode)
        flash("Versi %s dipulihkan (isi sebelumnya disimpan sebagai versi baru); situs prodi dibangun ulang." % versi, "ok")
        return redirect(url_for("riwayat_prodi", kode=kode))
