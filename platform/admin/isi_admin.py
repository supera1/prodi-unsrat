# -*- coding: utf-8 -*-
"""A programme's own pages in the admin (Fase 2): the 22 required accreditation pages and the 2 optional ones, written in
forms built from their content templates (isi_halaman.py, penyunting.py), submitted, published and withdrawn (K-P24).
akses("prodi"): operators too, except where noted.

    /prodi/<kode>/halaman                     the pages and what they hold (?status=menunggu|dikembalikan|draf|terbit|kosong,
                                              or mesin: English drafts with machine translations not checked yet)
    /prodi/<kode>/halaman/<id>                the form of a page; POST aksi=simpan | pratinjau | ajukan | batal-ajukan |
                                              kembalikan | terbitkan | tarik | buang | pulihkan-butir |
                                              tambah:<list> | hapus|naik|turun:<list>.<i>
    /prodi/<kode>/halaman/<id>/pratinjau      the draft as the site would show it, with the site's styles
    /prodi/<kode>/halaman/<id>/riwayat        the page's versions; /riwayat/<versi> one of them (POST: make it the draft)
    /prodi/<kode>/halaman/<id>/en             its English version (Fase 5, K-P37, isi_inggris.py): the Indonesian texts
                                              with an English field each; POST aksi=simpan | pratinjau | ajukan |
                                              batal-ajukan | kembalikan | terbitkan | tarik | buang | terjemahkan
                                              (machine translation, terjemah_mesin.py; its texts are checked before
                                              they are submitted or published: periksa_mesin=1) | ajukan-lanjut |
                                              terbitkan-lanjut (then the next page waiting for a check, berikutnya()).
                                              /en/pratinjau, /en/riwayat and /en/riwayat/<versi> as for the page.
                                              "Terjemahkan semua" for every page at once: terjemah_semua.py
    /prodi/<kode>/pratinjau/warna.css         the programme's colours, for the previews
    /aset-situs/<nama>                        the site's style sheets (tokens.css, prodi.css), for the previews
    /super/kelengkapan (.csv)                 akses("super"): the required pages of every programme, for LPMPP

Who may do what (checked here for every request, whatever the form says):
    operator   writes the draft, submits it (it must pass every check), takes a submission back, discards a draft that
               is not waiting; never publishes, sends back or withdraws
    admin      (and superadmin) everything: publishes a draft (or the form's content directly), sends a submitted draft
               back with a note, withdraws published content (it becomes the draft again)
Every button saves what the form holds first. A POST first checks the version the form was made from: a form from an
older version (someone saved in between) is refused and nothing is stored. Only deliberate actions keep the previous
content in the history; the list buttons and the preview do not (K-P27). Publishing and withdrawing rebuild the site.
"""
from __future__ import print_function

import copy
import csv
import io
import json
import os
import sys

ADMIN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(ADMIN)
sys.path.insert(0, PLATFORM)
sys.path.insert(0, ADMIN)
sys.path.insert(0, os.path.join(PLATFORM, "bangun"))

from flask import (Response, abort, flash, g, make_response, redirect, render_template, request,  # noqa: E402
                   send_from_directory, url_for)
from markupsafe import Markup  # noqa: E402

import bangun as bangun_mod  # noqa: E402
import data_prodi  # noqa: E402
import halaman_tambahan  # noqa: E402
import impor_dosen  # noqa: E402
import impor_tabel  # noqa: E402
import isi_halaman as ih  # noqa: E402
import isi_inggris  # noqa: E402
import kriteria as kriteria_mod  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import menu as menu_mod  # noqa: E402
import penyunting  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import terjemah_mesin  # noqa: E402
import warna as warna_mod  # noqa: E402
from akses import akses  # noqa: E402

ASET_SITUS = ("tokens.css", "prodi.css")
PRIVASI = ("Jangan mengunggah data pribadi: NIK, nomor HP, alamat rumah, nilai atau IPK perorangan, data kesehatan, atau "
           "dokumen internal akreditasi yang memuat data pribadi. Daftar tenaga kependidikan dan prestasi cukup memuat "
           "nama dan peran.")
STATUS = ("menunggu", "dikembalikan", "draf", "terbit", "kosong")
STATUS_SARING = STATUS + ("mesin",)      # the list's filters; mesin: English drafts with unchecked machine translations
NAMA_STATUS = {"kosong": "Belum diisi", "draf": "Draf", "menunggu": "Menunggu persetujuan", "dikembalikan": "Dikembalikan",
               "terbit": "Terbit", "mesin": "Terjemahan mesin belum diperiksa"}
# what a button does with the page, besides saving what the form holds
AKSI = ("simpan", "pratinjau", "ajukan", "batal-ajukan", "kembalikan", "terbitkan", "tarik", "buang", "pulihkan-butir")
ADMIN_SAJA = ("kembalikan", "terbitkan", "tarik")
SENGAJA = ("simpan", "ajukan", "batal-ajukan", "kembalikan", "terbitkan", "tarik")   # empty rows go first
BERHASIL = {"ajukan": "Diajukan untuk diterbitkan; admin prodi akan memeriksa dan menerbitkannya.",
            "batal-ajukan": "Pengajuan dibatalkan; kembali menjadi draf.",
            "kembalikan": "Dikembalikan ke penulis dengan catatan.",
            "terbitkan": "Diterbitkan; situs prodi dibangun ulang.",
            "tarik": "Ditarik dari situs; halaman kembali “sedang dilengkapi” dan isinya tetap ada di draf. Situs prodi "
                     "dibangun ulang."}
GAGAL = {"ajukan": "Belum diajukan", "batal-ajukan": "Pengajuan tidak dibatalkan", "kembalikan": "Belum dikembalikan",
         "terbitkan": "Belum diterbitkan", "tarik": "Belum ditarik"}
AUDIT = {"ajukan": "isi-diajukan", "batal-ajukan": "isi-pengajuan-dibatalkan", "kembalikan": "isi-dikembalikan",
         "terbitkan": "isi-diterbitkan", "tarik": "isi-ditarik"}
AKSI_EN = tuple(a for a in AKSI if a != "pulihkan-butir") + ("terjemahkan",)
LANJUT = "-lanjut"               # ajukan-lanjut, terbitkan-lanjut: then open the next page waiting for a check
# the history: the change that followed a version
PERUBAHAN = (("simpan draf", "Draf disimpan"), ("batal ajukan", "Pengajuan dibatalkan"), ("ajukan", "Diajukan"),
             ("kembalikan", "Dikembalikan dengan catatan"), ("terbitkan", "Diterbitkan"), ("tarik", "Ditarik dari situs"),
             ("buang draf", "Draf dibuang"), ("pakai versi", "Versi lama dijadikan draf"),
             ("sebelum pemulihan", "Dipulihkan dari menu Riwayat"))
RIWAYAT_TAMPIL = 50


def adalah_admin(akun):
    return akun["peran"] in ("super", "admin")


def halaman_prodi(kode):
    """The programme's own pages in menu order: [(group label, [menu entry + "sembunyi", ...])]. A label the
    programme gave a page in its menu settings is used; "sembunyi": an optional page the programme hides. The
    programme's extra pages (K-P35) follow the pages of their group, with or without published content."""
    atur = (lokasi.baca("prodi/%s/situs" % kode) or {}).get("menu")
    atur = atur if isinstance(atur, dict) else {}
    tambahan = [h for h in halaman_tambahan.baca(kode) if isinstance(h, dict) and ih.POLA_TAMBAHAN.match(str(h.get("id")))]

    def pengaturan(id_):
        return atur.get(id_) if isinstance(atur.get(id_), dict) else {}
    hasil = []
    for k in menu_mod.baca_templat():
        anak = [dict(a, label=(pengaturan(a["id"]).get("label") or a["label"]),
                     label_en=(pengaturan(a["id"]).get("label_en") or a["label_en"]),
                     sembunyi=bool(pengaturan(a["id"]).get("sembunyi")))
                for a in k.get("anak", []) if a["id"] in ih.TEMPLAT]
        anak += [dict(halaman_tambahan.butir_menu(h), sembunyi=False,
                      deskripsi="Halaman tambahan prodi: tampil di situs setelah diterbitkan, sesudah halaman lain di "
                                "kelompok ini.")
                 for h in tambahan if h.get("kelompok") == k["id"]]
        if anak:
            hasil.append((pengaturan(k["id"]).get("label") or k["label"], anak))
    return hasil


def halaman_wajib():
    """The ids of the required pages, in menu order (the same for every programme: they cannot be hidden)."""
    return [b["id"] for b in menu_mod.halaman(menu_mod.susun(menu_mod.baca_templat()))
            if b.get("jenis") == "wajib" and b["id"] in ih.TEMPLAT]


def ringkasan_isi(kode, wajib=None):
    """What a programme's own pages hold: {"halaman": {id: isi_halaman.keadaan}, "wajib": number of required pages,
    "terbit": required pages the site shows, "kosong": required pages with nothing yet, "menunggu" / "dikembalikan" /
    "draf": drafts of any page in that status (either language), "terakhir": the last change; "en": {id: the English
    version's isi_inggris.keadaan}, "en_terbit": required pages whose English version shows, "en_perlu": pages whose
    published English version lacks translations of the Indonesian published content, "en_mesin": pages whose English
    draft holds machine translations not checked yet}."""
    wajib = halaman_wajib() if wajib is None else wajib
    hasil = {"halaman": {}, "en": {}, "wajib": len(wajib), "terbit": 0, "kosong": 0, "menunggu": 0, "dikembalikan": 0,
             "draf": 0, "terakhir": "", "en_terbit": 0, "en_perlu": 0, "en_mesin": 0}
    tambahan = [h["id"] for h in halaman_tambahan.baca(kode) if isinstance(h, dict)
                and ih.POLA_TAMBAHAN.match(str(h.get("id")))]
    for id_ in list(ih.TEMPLAT) + tambahan:
        k = ih.keadaan(kode, id_)
        hasil["halaman"][id_] = k
        en = hasil["en"][id_] = isi_inggris.keadaan(kode, id_, k)
        if id_ in wajib:
            hasil["terbit"] += k["tayang"]
            hasil["kosong"] += k["status"] == "kosong"
            hasil["en_terbit"] += en["tayang"]
        hasil["en_perlu"] += bool(en["terbit"] and en["perlu"])
        hasil["en_mesin"] += mesin_belum(en)
        for x in (k, en):                       # a draft waiting in either language is one to look at
            status_draf = (x["draf"] or {}).get("status")
            if status_draf in ih.STATUS_DRAF:
                hasil[status_draf] += 1
        hasil["terakhir"] = max(hasil["terakhir"], k["waktu"] or "", en["waktu"] or "")
    return hasil


def saring_cocok(k, status):
    """Does a page fall under a status of the list's filter? A published page with a draft counts under both."""
    return (status == "terbit" and k["terbit"] is not None) or (status == "kosong" and k["status"] == "kosong") or \
        (k["draf"] is not None and k["draf"].get("status") == status)


def dihapus_sah(x):
    return (isinstance(x, dict) and isinstance(x.get("jalur"), str) and bool(penyunting.POLA_JALUR.match(x["jalur"]))
            and isinstance(x.get("indeks"), int) and x["indeks"] >= 0 and "nilai" in x)


def inti(x):
    """Content without its empty values (an empty text, an unticked box, a missing key are all "nothing"), to tell
    whether a form changed anything."""
    if isinstance(x, dict):
        hasil = {k: inti(v) for k, v in x.items()}
        return {k: v for k, v in hasil.items() if v not in (None, "", False, {}, [])}
    if isinstance(x, list):
        return [inti(v) for v in x]
    return x


def mesin_belum(k):
    """Does the English version (its keadaan, or {"draf": draft}) hold machine translations nobody checked yet?"""
    isi = (k.get("draf") or {}).get("isi")
    return bool(isinstance(isi, dict) and isi.get("mesin"))


def saring_cocok_en(k, status):
    """saring_cocok for the English version: a draft of it in that status; mesin: machine translations to check."""
    if status == "mesin":
        return mesin_belum(k)
    return status in ih.STATUS_DRAF and k["draf"] is not None and k["draf"].get("status") == status


def keadaan_teks(k):
    """A page's state in a few words, for the CSV of the completeness table."""
    if k["terbit"] is not None:
        teks = "terbit %s" % (k["terbit"].get("waktu") or "")[:10]
        if not k["tayang"]:
            teks += " (tidak tampil: isi tidak lolos pemeriksaan)"
    else:
        teks = NAMA_STATUS[k["status"]].lower()
    if k["draf"] and k["terbit"] is not None:
        teks += "; draf %s" % NAMA_STATUS[k["draf"].get("status", "draf")].lower()
    return teks


def nama_perubahan(aksi):
    for awal, nama in PERUBAHAN:
        if (aksi or "").startswith(awal):
            return nama
    return aksi or ""


def pasang(app, alat):

    def ini_(kode, id_):
        """The menu entry of a page of this programme that has a content template, or 404."""
        if ih.templat_halaman(id_) is None:
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

    def berikutnya(kode, id_, admin):
        """The next page after id_ (menu order, going round) whose English draft waits for this account: machine
        translations not checked yet (for an operator, not while that draft waits for approval), or, for an admin, a
        submitted draft. None when there is none."""
        urut = [a for _label, anak in halaman_prodi(kode) for a in anak]
        ids = [a["id"] for a in urut]
        i = ids.index(id_) if id_ in ids else -1
        for a in urut[i + 1:] + urut[:max(i, 0)]:
            d = ih.draf(ih.baca(kode, isi_inggris.id_en(a["id"])))
            if d is None:
                continue
            menunggu = d.get("status") == "menunggu"
            if (mesin_belum({"draf": d}) and (admin or not menunggu)) or (admin and menunggu):
                return a
        return None

    def masalah_draf(id_, isi, kode):
        return penyunting.masalah_tampil(ih.templat_halaman(id_), isi, ih.daftar_masalah(id_, isi, kode))

    def bangun(kode):
        r = registri.cari(registri.baca(), kode)
        if r and r.get("aktif"):
            alat.antrean.minta(kode, g.akun["nama"])

    def tampil_sunting(kode, ini, data):
        templat = ih.templat_halaman(ini["id"])
        isi = copy.deepcopy(ih.isi_kerja(data))
        masalah = masalah_draf(ini["id"], isi, kode)
        galat = {}
        for jalur, _tempat, pesan in masalah:
            galat.setdefault(jalur, pesan)
        buka = request.args.get("buka", "")
        d = ih.draf(data)
        t = penyunting.Tampil(galat, lambda r: url_berkas(kode, r), [buka] if penyunting.POLA_JALUR.match(buka) else [],
                              d.get("dihapus") if d and dihapus_sah(d.get("dihapus")) else None,
                              url_for("isi_impor", kode=kode, id_=ini["id"]) if impor_tabel.tabel_halaman(ini["id"]) else None)
        return render_template("halaman_sunting.html", pr=g.prodi, ini=ini, data=data, k=ih.keadaan(kode, ini["id"], data),
                               formulir=Markup(penyunting.formulir(templat, isi, t)), masalah=masalah,
                               id_galat=penyunting._id, privasi=PRIVASI, admin=adalah_admin(g.akun),
                               maks_catatan=ih.MAKS_CATATAN, kriteria=label_kriteria(kode, ini["id"]),
                               impor=[n["label"] for _k, n in impor_tabel.tabel_halaman(ini["id"])],
                               resmi=data_prodi.efektif(kode) if ini["id"] == "akreditasi" else None)

    def label_kriteria(kode, id_):
        """(body, [(number, name)]) of the criteria a page serves, as the site shows them (K-P29, K-P33)."""
        try:
            data = kriteria_mod.baca()
        except (OSError, ValueError):
            data = None
        if data is not None and kriteria_mod.periksa(data, set(ih.TEMPLAT)):
            data = None
        lembaga, _masalah = kriteria_mod.untuk_prodi(kode, data, (data_prodi.efektif(kode) or {}).get("lembaga_akreditasi"),
                                                     set(ih.TEMPLAT))
        return lembaga, kriteria_mod.label(lembaga, id_)

    def bentrok(kode, ini, pesan):
        """A form made from an older version: nothing was stored (409)."""
        return render_template("halaman_bentrok.html", pr=g.prodi, ini=ini, pesan=pesan), 409

    def pratinjau(kode, ini, isi, **tambahan):
        """The preview page of some content of a page (the site's macros and styles)."""
        bagian, hilang = ih.tampilan(ini["id"], ih.isi_sah(ini["id"], isi, kode), berkas_ada)
        return render_template("halaman_pratinjau.html", pr=g.prodi, ini=ini, hilang=hilang,
                               isi_html=bangun_mod.bagian_html(bagian, lambda r: url_berkas(kode, r)) if bagian else "",
                               n_masalah=len(masalah_draf(ini["id"], isi, kode)), **tambahan)

    def pratinjau_en(kode, ini, en, **tambahan):
        """The preview of an English version: the Indonesian published content (its draft while nothing is published)
        with these translations, as the English site would show it."""
        id_ = ini["id"]
        templat = ih.templat_halaman(id_)
        data_id = ih.baca(kode, id_)
        sumber = (data_id.get("terbit") or {}).get("isi") if isinstance(data_id.get("terbit"), dict) else None
        sumber = sumber if isinstance(sumber, dict) else ih.isi_kerja(data_id)
        en_sah = ih.isi_sah(isi_inggris.id_en(id_), en, kode)
        bagian, hilang = ih.tampilan(id_, isi_inggris.terjemahkan(templat, ih.isi_sah(id_, sumber, kode), en_sah),
                                     berkas_ada, "en")
        n_masalah = len(ih.periksa(isi_inggris.id_en(id_), en, kode))
        return render_template("halaman_pratinjau.html", pr=g.prodi, ini=dict(ini, label=ini.get("label_en") or ini["label"]),
                               hilang=hilang, bahasa="en", n_masalah=n_masalah,
                               isi_html=bangun_mod.bagian_html(bagian, lambda r: url_berkas(kode, r), "en") if bagian else "",
                               **tambahan)

    # -------------------------------------------------------------- the list of pages

    @app.route("/prodi/<kode>/halaman")
    @akses("prodi")
    def isi_daftar(kode):
        status = request.args.get("status", "")
        if status and status not in STATUS_SARING:
            abort(404)
        r = ringkasan_isi(kode)
        kelompok = []
        for label, anak in halaman_prodi(kode):
            anak = [dict(a, k=r["halaman"][a["id"]], en=r["en"][a["id"]]) for a in anak]
            anak = [a for a in anak if not status or saring_cocok(a["k"], status) or saring_cocok_en(a["en"], status)]
            if anak:
                kelompok.append((label, anak))
        jumlah = {s: sum(1 for id_, k in r["halaman"].items() if saring_cocok(k, s) or saring_cocok_en(r["en"][id_], s))
                  for s in STATUS_SARING}
        reg = registri.cari(registri.baca(), kode) or {}
        return render_template("halaman_daftar.html", pr=g.prodi, kelompok=kelompok, r=r, jumlah=jumlah, status=status,
                               NAMA_STATUS=NAMA_STATUS, admin=adalah_admin(g.akun), inggris=bool(reg.get("inggris")),
                               penyedia=alat.penerjemah.nama if alat.penerjemah is not None else None,
                               terjemah_semua=alat.terjemah_semua.keadaan(kode))

    # -------------------------------------------------------------- one page

    @app.route("/prodi/<kode>/halaman/<id_>")
    @akses("prodi")
    def isi_sunting(kode, id_):
        return tampil_sunting(kode, ini_(kode, id_), ih.baca(kode, id_))

    @app.route("/prodi/<kode>/halaman/<id_>", methods=["POST"])
    @akses("prodi")
    def isi_simpan(kode, id_):
        ini = ini_(kode, id_)
        templat = ih.templat_halaman(id_)
        ke_sini = url_for("isi_sunting", kode=kode, id_=id_)
        aksi = request.form.get("aksi", "simpan")
        try:
            versi = int(request.form.get("versi", ""))
        except ValueError:
            abort(400, "Formulir tidak lengkap. Muat ulang halaman lalu coba lagi.")
        if aksi not in AKSI and aksi.partition(":")[0] not in penyunting.AKSI_DAFTAR:
            abort(400)
        admin = adalah_admin(g.akun)
        if aksi in ADMIN_SAJA and not admin:
            abort(403, "Hanya admin prodi yang dapat melakukan ini.")
        data = ih.baca(kode, id_)
        try:
            ih.cek_versi(data, versi)
        except ih.GagalIsi as e:
            return bentrok(kode, ini, str(e))
        oleh = g.akun["nama"]
        d = ih.draf(data)
        if aksi == "buang":
            if not admin and d and d.get("status") == "menunggu":
                flash("Draf yang menunggu persetujuan tidak dapat dibuang; batalkan pengajuannya dulu.", "galat")
                return redirect(ke_sini)
            try:
                ih.buang_draf(kode, id_, oleh, versi)
            except ih.GagalIsi as e:
                return bentrok(kode, ini, str(e))
            alat.catat("isi-draf-dibuang", prodi=kode, halaman=id_)
            flash("Draf dibuang. %s" % ("Penyunting kembali memuat isi yang sudah terbit." if data.get("terbit")
                                         else "Halaman ini kembali kosong."), "ok")
            return redirect(ke_sini)

        # every other button: what the form holds first (texts, uploads, a list button)
        dasar = copy.deepcopy(ih.isi_kerja(data))
        k = penyunting.Konteks(request.form, request.files, kode)
        isi = penyunting.baca(templat, dasar, k)
        tujuan, dihapus = None, None
        try:
            if aksi == "pulihkan-butir":
                if not (d and dihapus_sah(d.get("dihapus"))):
                    raise penyunting.DaftarPenuh("Tidak ada butir yang dapat dikembalikan.")
                tujuan = penyunting.kembalikan(templat, isi, d["dihapus"])
            elif aksi.partition(":")[0] in penyunting.AKSI_DAFTAR:
                tujuan, dihapus = penyunting.terapkan_aksi(templat, isi, aksi)
        except penyunting.TombolSalah:
            abort(400)
        except penyunting.DaftarPenuh as e:
            flash(str(e), "galat")
        if aksi in SENGAJA and not k.galat:
            # empty rows go; not while an upload was refused, so the row it was meant for stays to try again
            isi = ih.rapikan(templat, isi)
        for jalur, pesan in k.galat:
            flash("%s — %s" % (penyunting.label_jalur(templat, jalur), pesan), "galat")
        if k.baru:
            alat.catat("isi-berkas-diunggah", prodi=kode, halaman=id_, jumlah=len(k.baru))
        # the item offered back after a removal is offered until the next request: that one stores the draft anyway
        berubah = inti(isi) != inti(ih.isi_kerja(data)) or dihapus is not None or bool(d and d.get("dihapus"))

        def simpan_ketikan(riwayat_=True):
            if berubah:
                ih.simpan_draf(kode, id_, isi, oleh, versi, riwayat=riwayat_, dihapus=dihapus)

        try:
            if aksi in BERHASIL and k.galat:
                simpan_ketikan()
                flash("%s: ada berkas yang ditolak (lihat di atas). Isian lain disimpan sebagai draf." % GAGAL[aksi], "galat")
                return redirect(ke_sini)
            if aksi in ("ajukan", "terbitkan") and not berubah and (d is None or (aksi == "ajukan" and d.get("status") == "menunggu")):
                flash("Draf ini sudah menunggu persetujuan." if d else "Tidak ada perubahan untuk %s." % (
                    "diajukan" if aksi == "ajukan" else "diterbitkan"), "info")
                return redirect(ke_sini)
            if aksi == "ajukan":
                ih.ajukan(kode, id_, isi, oleh, versi)
            elif aksi == "terbitkan":
                ih.terbitkan(kode, id_, isi, oleh, versi, dari_draf=True)
            elif aksi == "batal-ajukan":
                ih.batal_ajukan(kode, id_, oleh, versi, isi if berubah else None)
            elif aksi == "kembalikan":
                ih.kembalikan(kode, id_, request.form.get("catatan", ""), oleh, versi, isi if berubah else None)
            elif aksi == "tarik":
                ih.tarik(kode, id_, oleh, versi, isi if berubah else None)
            else:
                simpan_ketikan(aksi == "simpan")
        except ih.GagalIsi as e:
            if "baru saja diubah" in str(e):
                return bentrok(kode, ini, str(e))
            if aksi in BERHASIL:
                # the action was refused (the checks, the draft's status): what was typed is kept as the draft
                try:
                    simpan_ketikan()
                except ih.GagalIsi as e2:
                    flash("Draf tidak disimpan: %s." % e2, "galat")
                flash("%s: %s." % (GAGAL[aksi], e), "galat")
            else:
                flash("Draf tidak disimpan: %s." % e, "galat")
            return redirect(ke_sini)

        if aksi in BERHASIL:
            alat.catat(AUDIT[aksi], prodi=kode, halaman=id_)
            if aksi in ("terbitkan", "tarik"):
                bangun(kode)
            flash(BERHASIL[aksi], "ok")
            return redirect(ke_sini)
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
            return redirect(ke_sini)
        if tujuan is None:
            return redirect(ke_sini)
        return redirect(url_for("isi_sunting", kode=kode, id_=id_, buka=tujuan) + "#" + penyunting._id(tujuan))

    # -------------------------------------------------------------- the English version (Fase 5, K-P37)

    def tampil_sunting_en(kode, ini, data_en=None, kode_status=200):
        id_ = ini["id"]
        templat = ih.templat_halaman(id_)
        data_en = ih.baca(kode, isi_inggris.id_en(id_)) if data_en is None else data_en
        sumber, versi_id = isi_inggris.isi_sumber(kode, id_)
        en = isi_inggris.rapi(ih.isi_kerja(data_en))
        butir = isi_inggris.butir_formulir(templat, sumber, en)
        galat = {}
        for jalur, _tempat, pesan in ih.daftar_masalah(isi_inggris.id_en(id_), en, kode):
            galat.setdefault(jalur, pesan)
        k_id = ih.keadaan(kode, id_)
        reg = registri.cari(registri.baca(), kode) or {}
        mesin = None
        if alat.penerjemah is not None:                  # what "Terjemahkan dari versi Indonesia" would send
            kosong_ = isi_inggris.sasaran_mesin(templat, sumber, en)
            semua = isi_inggris.sasaran_mesin(templat, sumber, en, timpa=True)
            excel = [t for t in isi_inggris.sasaran_mesin(templat, sumber, en, timpa=True, excel=True) if t not in semua]
            pakai = int(terjemah_mesin.pemakaian(kode)["hari"].get(terjemah_mesin.hari_ini(), 0))
            mesin = {"penyedia": alat.penerjemah.nama, "n": len(kosong_), "karakter": sum(map(len, kosong_)),
                     "n_semua": len(semua), "karakter_semua": sum(map(len, semua)), "n_excel": len(excel),
                     "karakter_excel": sum(map(len, excel)), "sisa": max(0, alat.batas_terjemah[0] - pakai)}
        return render_template("halaman_sunting_en.html", pr=g.prodi, ini=ini, data=data_en, versi_id=versi_id,
                               mesin=mesin, n_mesin=len(en.get("mesin", [])),
                               berikut=berikutnya(kode, id_, adalah_admin(g.akun)),
                               k=isi_inggris.keadaan(kode, id_, k_id), k_id=k_id, butir=butir, galat=galat,
                               admin=adalah_admin(g.akun), maks_catatan=ih.MAKS_CATATAN, inggris=bool(reg.get("inggris")),
                               lewat_excel=any(t["lewat_excel"] for t in isi_inggris.perlu_terjemah(templat, sumber))), \
            kode_status

    @app.route("/prodi/<kode>/halaman/<id_>/en")
    @akses("prodi")
    def isi_sunting_en(kode, id_):
        return tampil_sunting_en(kode, ini_(kode, id_))

    @app.route("/prodi/<kode>/halaman/<id_>/en", methods=["POST"])
    @akses("prodi")
    def isi_simpan_en(kode, id_):
        """The English form: the same buttons and rules as the page's own form (isi_simpan), without lists or files."""
        ini = ini_(kode, id_)
        id_en = isi_inggris.id_en(id_)
        ke_sini = url_for("isi_sunting_en", kode=kode, id_=id_)
        aksi = request.form.get("aksi", "simpan")
        lanjut = aksi in ("ajukan" + LANJUT, "terbitkan" + LANJUT)
        if lanjut:
            aksi = aksi[:-len(LANJUT)]
        try:
            versi = int(request.form.get("versi", ""))
            versi_id = int(request.form.get("versi_id", ""))
        except ValueError:
            abort(400, "Formulir tidak lengkap. Muat ulang halaman lalu coba lagi.")
        if aksi not in AKSI_EN or (aksi == "terjemahkan" and alat.penerjemah is None):
            abort(400)
        admin = adalah_admin(g.akun)
        if aksi in ADMIN_SAJA and not admin:
            abort(403, "Hanya admin prodi yang dapat melakukan ini.")
        data = ih.baca(kode, id_en)
        try:
            ih.cek_versi(data, versi)
        except ih.GagalIsi as e:
            return bentrok(kode, ini, str(e))
        oleh = g.akun["nama"]
        d = ih.draf(data)
        if aksi == "buang":
            if not admin and d and d.get("status") == "menunggu":
                flash("Draf yang menunggu persetujuan tidak dapat dibuang; batalkan pengajuannya dulu.", "galat")
                return redirect(ke_sini)
            try:
                ih.buang_draf(kode, id_en, oleh, versi)
            except ih.GagalIsi as e:
                return bentrok(kode, ini, str(e))
            alat.catat("isi-en-draf-dibuang", prodi=kode, halaman=id_)
            flash("Draf versi Inggris dibuang.", "ok")
            return redirect(ke_sini)

        # what the form holds: the translations of the Indonesian draft's and published texts
        data_id = ih.baca(kode, id_)
        terbit_id = (data_id.get("terbit") or {}).get("isi") if isinstance(data_id.get("terbit"), dict) else None
        sumber = [x for x in ((ih.draf(data_id) or {}).get("isi"), terbit_id) if isinstance(x, dict)]
        lama = isi_inggris.rapi(ih.isi_kerja(data))
        templat = ih.templat_halaman(id_)
        isi, tak_cocok = isi_inggris.dari_formulir(templat, lama, request.form, sumber)
        if tak_cocok or versi_id != data_id.get("versi", 0):
            flash("Versi Indonesia halaman ini berubah saat Anda menerjemahkan. %s" % (
                "Terjemahan untuk %d teks yang berubah tidak tersimpan; periksa lagi formulirnya." % len(tak_cocok)
                if tak_cocok else "Periksa teks yang ditandai berubah."), "galat")
        if aksi in ("ajukan", "terbitkan") and isi.get("mesin") and request.form.get("periksa_mesin") == "1":
            isi = dict(isi)
            del isi["mesin"]                       # a person checked the machine's texts (K-P37)
        berubah = inti(isi) != inti(lama)

        if aksi == "terjemahkan":
            return terjemahkan_en(kode, id_, isi, berubah, versi, ke_sini)

        def simpan_ketikan(riwayat_=True):
            if berubah:
                ih.simpan_draf(kode, id_en, isi, oleh, versi, riwayat=riwayat_)

        try:
            if aksi in ("ajukan", "terbitkan") and not berubah and (d is None or (aksi == "ajukan" and d.get("status") == "menunggu")):
                flash("Draf ini sudah menunggu persetujuan." if d else "Tidak ada perubahan untuk %s." % (
                    "diajukan" if aksi == "ajukan" else "diterbitkan"), "info")
                return redirect(ke_sini)
            if aksi == "ajukan":
                ih.ajukan(kode, id_en, isi, oleh, versi)
            elif aksi == "terbitkan":
                ih.terbitkan(kode, id_en, isi, oleh, versi, dari_draf=True)
            elif aksi == "batal-ajukan":
                ih.batal_ajukan(kode, id_en, oleh, versi, isi if berubah else None)
            elif aksi == "kembalikan":
                ih.kembalikan(kode, id_en, request.form.get("catatan", ""), oleh, versi, isi if berubah else None)
            elif aksi == "tarik":
                ih.tarik(kode, id_en, oleh, versi, isi if berubah else None)
            else:
                simpan_ketikan(aksi == "simpan")
        except ih.GagalIsi as e:
            if "baru saja diubah" in str(e):
                return bentrok(kode, ini, str(e))
            if aksi in BERHASIL:
                try:
                    simpan_ketikan()
                except ih.GagalIsi as e2:
                    flash("Draf tidak disimpan: %s." % e2, "galat")
                flash("%s: %s." % (GAGAL[aksi], e), "galat")
            else:
                flash("Draf tidak disimpan: %s." % e, "galat")
            return redirect(ke_sini)

        if aksi in BERHASIL:
            alat.catat(AUDIT[aksi].replace("isi-", "isi-en-"), prodi=kode, halaman=id_)
            if aksi in ("terbitkan", "tarik"):
                bangun(kode)
            flash(BERHASIL[aksi].replace("halaman kembali “sedang dilengkapi” dan isinya tetap ada di draf",
                                         "versi Inggris halaman ini tidak tampil lagi; terjemahannya tetap ada di draf"), "ok")
            if lanjut:
                b = berikutnya(kode, id_, admin)
                if b is not None:
                    flash("Berikutnya: %s." % b["label"], "info")
                    return redirect(url_for("isi_sunting_en", kode=kode, id_=b["id"]))
                flash("Tidak ada lagi halaman dengan terjemahan mesin yang perlu diperiksa%s." % (
                    " atau menunggu persetujuan" if admin else ""), "info")
                return redirect(url_for("isi_daftar", kode=kode))
            return redirect(ke_sini)
        if aksi == "pratinjau":
            return redirect(url_for("isi_pratinjau_en", kode=kode, id_=id_))
        if berubah:
            alat.catat("isi-en-draf-disimpan", prodi=kode, halaman=id_)
            flash("Draf versi Inggris disimpan. Situs tetap menampilkan versi Inggris yang sudah terbit.", "ok")
        else:
            flash("Tidak ada perubahan untuk disimpan.", "info")
        return redirect(ke_sini)

    def terjemahkan_en(kode, id_, isi, berubah, versi, ke_sini):
        """aksi=terjemahkan: what the form holds, with machine translations of the texts it lacks (timpa: of all;
        excel: also of the lists kept in spreadsheets), stored as the draft, marked to be checked."""
        id_en = isi_inggris.id_en(id_)
        templat = ih.templat_halaman(id_)
        sumber = ih.isi_kerja(ih.baca(kode, id_))
        oleh = g.akun["nama"]
        sasaran = isi_inggris.sasaran_mesin(templat, sumber, isi, timpa=request.form.get("timpa") == "1",
                                            excel=request.form.get("excel") == "1")
        n = sum(len(t) for t in sasaran)
        try:
            if not sasaran:
                raise terjemah_mesin.GagalTerjemah("semua teks halaman ini sudah diterjemahkan")
            terjemah_mesin.periksa_batas(kode, n, [r["kode_pddikti"] for r in registri.baca()["prodi"]],
                                         alat.batas_terjemah)
            p = data_prodi.efektif(kode) or {}
            glos = terjemah_mesin.glosarium(p, data_prodi.unit_per_kode().values(), lokasi.baca("warisan/universitas"))
            hasil = terjemah_mesin.terjemahkan(alat.penerjemah, sasaran, glos)
        except terjemah_mesin.GagalTerjemah as e:
            try:
                if berubah:
                    ih.simpan_draf(kode, id_en, isi, oleh, versi)
            except ih.GagalIsi as e2:
                if "baru saja diubah" in str(e2):
                    return bentrok(kode, ini_(kode, id_), str(e2))
                flash("Draf tidak disimpan: %s." % e2, "galat")
            flash("Terjemahan mesin tidak dijalankan: %s." % e, "galat" if sasaran else "info")
            return redirect(ke_sini)
        terjemah_mesin.catat_pemakaian(kode, n)
        try:
            ih.simpan_draf(kode, id_en, isi_inggris.pasang_mesin(templat, sumber, isi, hasil), oleh, versi)
        except ih.GagalIsi as e:
            if "baru saja diubah" in str(e):
                return bentrok(kode, ini_(kode, id_), str(e))
            flash("Draf tidak disimpan: %s." % e, "galat")
            return redirect(ke_sini)
        gagal = sum(1 for v in hasil.values() if not v)
        alat.catat("isi-en-terjemahan-mesin", prodi=kode, halaman=id_, teks=len(sasaran) - gagal, karakter=n,
                   penyedia=alat.penerjemah.nama)
        flash("%d teks diterjemahkan mesin (%s, %d karakter) dan disimpan sebagai draf. Periksa setiap isian bertanda "
              "“terjemahan mesin” sebelum mengajukan atau menerbitkan.%s" % (
                  len(sasaran) - gagal, alat.penerjemah.nama, n,
                  " %d teks tidak kembali utuh dan dibiarkan kosong; terjemahkan sendiri." % gagal if gagal else ""), "ok")
        return redirect(ke_sini)

    @app.route("/prodi/<kode>/halaman/<id_>/en/pratinjau")
    @akses("prodi")
    def isi_pratinjau_en(kode, id_):
        ini = ini_(kode, id_)
        data = ih.baca(kode, isi_inggris.id_en(id_))
        judul = "Pratinjau versi Inggris (%s)" % ("draf" if ih.draf(data) else "sudah terbit")
        return pratinjau_en(kode, ini, ih.isi_kerja(data), judul=judul, kembali=url_for("isi_sunting_en", kode=kode, id_=id_),
                            kembali_teks="Kembali ke penyunting versi Inggris")

    # -------------------------------------------------------------- previews

    @app.route("/prodi/<kode>/halaman/<id_>/pratinjau")
    @akses("prodi")
    def isi_pratinjau(kode, id_):
        ini = ini_(kode, id_)
        data = ih.baca(kode, id_)
        k = ih.keadaan(kode, id_, data)
        judul = "Pratinjau %s" % ("draf" if k["draf"] else "isi yang sudah terbit")
        return pratinjau(kode, ini, ih.isi_kerja(data), judul=judul, kembali=url_for("isi_sunting", kode=kode, id_=id_),
                         kembali_teks="Kembali ke penyunting")

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

    # -------------------------------------------------------------- the page's history

    def versi_halaman(kode, id_, versi_lama):
        """An old version of a page's data (riwayat.py), or 404."""
        try:
            path = riwayat.baca_versi(ih.nama_berkas(kode, id_), versi_lama)
        except ValueError:
            abort(404)
        with io.open(path, encoding="utf-8") as f:
            lama = json.load(f)
        return lama if isinstance(lama, dict) else abort(404)

    def bagian_versi(lama):
        """The parts of an old version that hold content: [("terbit"|"draf", label)]."""
        hasil = []
        t, d = lama.get("terbit"), ih.draf(lama)
        if isinstance(t, dict) and isinstance(t.get("isi"), dict):
            hasil.append(("terbit", "Isi terbit"))
        if d:
            hasil.append(("draf", "Draf (%s)" % NAMA_STATUS.get(d.get("status"), "Draf").lower()))
        return hasil

    def riwayat_halaman(kode, id_, en):
        """The versions of a page (en: of its English version)."""
        ini = ini_(kode, id_)
        id_simpan = isi_inggris.id_en(id_) if en else id_
        berkas = ih.nama_berkas(kode, id_simpan)
        semua = [v for v in riwayat.daftar(1000000) if v["berkas"] == berkas]
        daftar = [dict(v, perubahan=nama_perubahan(v.get("aksi")),
                       bagian=bagian_versi(versi_halaman(kode, id_simpan, v["versi"])))
                  for v in semua[:RIWAYAT_TAMPIL]]
        return render_template("halaman_riwayat.html", pr=g.prodi, ini=ini, daftar=daftar, lebih=len(semua) - len(daftar),
                               data=ih.baca(kode, id_simpan), admin=adalah_admin(g.akun), akhiran="_en" if en else "")

    def versi_lama_halaman(kode, id_, versi_lama, en):
        ini = ini_(kode, id_)
        id_simpan = isi_inggris.id_en(id_) if en else id_
        lama = versi_halaman(kode, id_simpan, versi_lama)
        ada = dict(bagian_versi(lama))
        bagian = request.args.get("bagian") or ("terbit" if "terbit" in ada else "draf")
        if bagian not in ada:
            abort(404)
        diubah = lama.get("diubah") if isinstance(lama.get("diubah"), dict) else {}
        judul = "Versi lama (%s%s), %s" % (diubah.get("waktu", "").replace("T", " ")[:16] or versi_lama,
                                           " oleh %s" % diubah["oleh"] if diubah.get("oleh") else "", ada[bagian].lower())
        kembali = url_for("isi_riwayat_en" if en else "isi_riwayat", kode=kode, id_=id_)
        if en:
            return pratinjau_en(kode, ini, lama[bagian]["isi"], judul=judul, kembali=kembali,
                                kembali_teks="Kembali ke riwayat versi Inggris")
        return pratinjau(kode, ini, lama[bagian]["isi"], judul=judul, kembali=kembali,
                         kembali_teks="Kembali ke riwayat halaman")

    def pakai_versi_halaman(kode, id_, versi_lama, en):
        ini = ini_(kode, id_)
        id_simpan = isi_inggris.id_en(id_) if en else id_
        versi_halaman(kode, id_simpan, versi_lama)
        try:
            versi = int(request.form.get("versi", ""))
        except ValueError:
            abort(400, "Formulir tidak lengkap. Muat ulang halaman lalu coba lagi.")
        bagian = request.form.get("bagian", "")
        if bagian not in ("terbit", "draf"):
            abort(400)
        try:
            ih.pakai_versi(kode, id_simpan, versi_lama, bagian, g.akun["nama"], versi)
        except ih.GagalIsi as e:
            if "baru saja diubah" in str(e):
                return bentrok(kode, ini, str(e))
            flash("Versi itu tidak dijadikan draf: %s." % e, "galat")
            return redirect(url_for("isi_riwayat_en" if en else "isi_riwayat", kode=kode, id_=id_))
        alat.catat("isi-en-versi-dipakai" if en else "isi-versi-dipakai", prodi=kode, halaman=id_, versi=versi_lama,
                   bagian=bagian)
        flash("Versi lama dijadikan draf. Periksa isinya, lalu %s." % (
            "terbitkan" if adalah_admin(g.akun) else "ajukan untuk diterbitkan"), "ok")
        return redirect(url_for("isi_sunting_en" if en else "isi_sunting", kode=kode, id_=id_))

    @app.route("/prodi/<kode>/halaman/<id_>/riwayat")
    @akses("prodi")
    def isi_riwayat(kode, id_):
        return riwayat_halaman(kode, id_, False)

    @app.route("/prodi/<kode>/halaman/<id_>/riwayat/<versi_lama>")
    @akses("prodi")
    def isi_versi(kode, id_, versi_lama):
        return versi_lama_halaman(kode, id_, versi_lama, False)

    @app.route("/prodi/<kode>/halaman/<id_>/riwayat/<versi_lama>", methods=["POST"])
    @akses("prodi")
    def isi_pakai_versi(kode, id_, versi_lama):
        return pakai_versi_halaman(kode, id_, versi_lama, False)

    @app.route("/prodi/<kode>/halaman/<id_>/en/riwayat")
    @akses("prodi")
    def isi_riwayat_en(kode, id_):
        return riwayat_halaman(kode, id_, True)

    @app.route("/prodi/<kode>/halaman/<id_>/en/riwayat/<versi_lama>")
    @akses("prodi")
    def isi_versi_en(kode, id_, versi_lama):
        return versi_lama_halaman(kode, id_, versi_lama, True)

    @app.route("/prodi/<kode>/halaman/<id_>/en/riwayat/<versi_lama>", methods=["POST"])
    @akses("prodi")
    def isi_pakai_versi_en(kode, id_, versi_lama):
        return pakai_versi_halaman(kode, id_, versi_lama, True)

    # -------------------------------------------------------------- completeness of every programme (superadmin)

    def kelengkapan():
        """One row per registered programme: its data (alat.info_prodi), ringkasan_isi(), the number of its own
        accreditation criteria (K-P33), and whether its English version is switched on (K-P37)."""
        wajib = halaman_wajib()
        baris = []
        for r in registri.baca()["prodi"]:
            info = alat.info_prodi(r["kode_pddikti"])
            if info:
                baris.append(dict(info, isi=ringkasan_isi(info["kode"], wajib), inggris=bool(r.get("inggris")),
                                  kriteria=len(kriteria_mod.baca_prodi(info["kode"]).get("kriteria") or [])))
        return sorted(baris, key=registri.kunci_urut), wajib

    @app.route("/super/kelengkapan")
    @akses("super")
    def super_kelengkapan():
        baris, wajib = kelengkapan()
        aktif = [b for b in baris if b["aktif"]]
        jumlah = {"lengkap": sum(1 for b in aktif if b["isi"]["terbit"] == len(wajib)),
                  "menunggu": sum(b["isi"]["menunggu"] for b in aktif),
                  "rata": (sum(b["isi"]["terbit"] for b in aktif) / float(len(aktif))) if aktif else 0}
        return render_template("super_kelengkapan.html", baris=baris, aktif=aktif, wajib=len(wajib), jumlah=jumlah)

    @app.route("/super/kelengkapan.csv")
    @akses("super")
    def super_kelengkapan_csv():
        baris, wajib = kelengkapan()
        butir = menu_mod.semua_butir(menu_mod.baca_templat())
        label = {k: b["label"] + {"wajib": "", "opsional": " (opsional)"}.get(b.get("jenis"), " (pelengkap)")
                 for k, b in butir.items()}
        halaman = wajib + [id_ for id_ in ih.TEMPLAT if id_ not in wajib]
        buf = io.StringIO()
        tulis = csv.writer(buf)
        tulis.writerow(["kode_pddikti", "jenjang", "nama", "fakultas", "slug", "aktif", "wajib_terbit", "wajib_total",
                        "menunggu", "dikembalikan", "draf", "terakhir_diubah", "kriteria_akreditasi", "inggris_aktif",
                        "wajib_terbit_en", "perlu_diperbarui_en"] +
                       [label.get(id_, id_) for id_ in halaman])
        for b in baris:
            x = b["isi"]
            tulis.writerow([impor_dosen.aman_csv(v) for v in [
                b["kode"], b["jenjang"], b["nama"], b["unit"], b["slug"], "ya" if b["aktif"] else "tidak", x["terbit"],
                x["wajib"], x["menunggu"], x["dikembalikan"], x["draf"], x["terakhir"].replace("T", " ")[:16],
                b["kriteria"], "ya" if b["inggris"] else "tidak", x["en_terbit"], x["en_perlu"]] +
                [keadaan_teks(x["halaman"][id_]) for id_ in halaman]])
        resp = make_response("﻿" + buf.getvalue())            # the BOM makes Excel read it as UTF-8
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = 'attachment; filename="kelengkapan-halaman-prodi.csv"'
        return resp

    alat.ringkasan_isi = ringkasan_isi
    alat.ini_halaman = ini_
