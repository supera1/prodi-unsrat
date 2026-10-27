# -*- coding: utf-8 -*-
"""Fase 2 langkah 3: the workflow of a programme's own pages (K-P24) and their completeness (rencana §3.6).

- isi_halaman.py: submitting (only content that passes every check), taking a submission back, sending back with a
  note (required, checked), publishing a draft (it is done with; who submitted it is kept), withdrawing (the content
  becomes the draft), an old version made the draft, every action from an older version refused, the state of a
  page (empty, draft, waiting, returned, published, published but not shown);
- through the admin, with real rebuilds: an operator writes and submits, edits while waiting, takes it back, may not
  publish, send back, withdraw or discard a waiting draft whatever it sends; an admin sends back with a note, the
  operator fixes and submits again, the admin publishes (the site shows it), publishes a change directly, withdraws
  (the site says "sedang dilengkapi" again); two people acting on the same version; the page's history, an old
  version previewed and made the draft; the list's filters, the dashboards, the superadmin's completeness table and
  its CSV; the audit log.
Who may open each route at all is tested in uji_admin.py.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import csv
import io
import json
import os
import re
import shutil
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import flask  # noqa: F401
except ImportError:
    print("uji_alur_isi: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-alur-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import audit  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import Formulir, prodi  # noqa: E402

A, B = "55201", "20201"
MENYUSUL = "Informasi ini sedang dilengkapi oleh Program Studi"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def harus_gagal(fungsi, potongan, pesan, *args, **kw):
    try:
        fungsi(*args, **kw)
    except ih.GagalIsi as e:
        cek(potongan in str(e), "%s: pesan %r" % (pesan, str(e)))
        return
    gagal.append(pesan)


def versi_riwayat(kode, id_):
    return [v for v in riwayat.daftar(100000) if v["berkas"] == "prodi/%s/halaman-%s" % (kode, id_)]


def halaman_situs(alamat):
    path = os.path.join(lokasi.publik(), "s1informatika", *alamat.split("/"), "index.html")
    with io.open(path, encoding="utf-8") as f:
        return f.read()


SEJARAH = {"uraian": "Program studi berdiri pada 1985.", "linimasa": [{"tahun": 1985, "peristiwa": "Berdiri"}]}

try:
    # ============================================================== platform with two programmes
    os.makedirs(os.environ["WWW_DATA"])
    for nama, isi in {"prodi": {"program": [prodi(A, "Teknik Informatika"), prodi(B, "Teknik Elektro")]},
                      "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "jenis": "fakultas",
                                         "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                      "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)

    # ============================================================== the workflow (isi_halaman.py)
    id_ = "visi-misi"
    harus_gagal(ih.ajukan, "isian perlu diperbaiki", "isi yang tidak lolos tidak bisa diajukan", A, id_,
                {"misi": ["Misi.", "x" * 600]}, "op")
    harus_gagal(ih.ajukan, "belum berisi", "isi kosong tidak bisa diajukan", A, id_, {"misi": []}, "op")
    v = ih.simpan_draf(A, id_, {"visi": "Visi awal."}, "op")
    cek(ih.keadaan(A, id_)["status"] == "draf", "keadaan: draf")
    v = ih.ajukan(A, id_, {"visi": "Visi diajukan."}, "op", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "menunggu" and d["diajukan"]["oleh"] == "op" and d["isi"] == {"visi": "Visi diajukan."},
        "diajukan: menunggu, dengan pengajunya")
    cek(versi_riwayat(A, id_)[0]["aksi"] == "ajukan %s" % id_, "pengajuan masuk riwayat")
    cek(ih.keadaan(A, id_)["status"] == "menunggu", "keadaan: menunggu")
    v = ih.simpan_draf(A, id_, {"visi": "Visi diajukan, diperbaiki."}, "op", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "menunggu" and d["diajukan"]["oleh"] == "op", "menyunting draf yang diajukan tetap menunggu")
    harus_gagal(ih.ajukan, "baru saja diubah oleh op", "pengajuan dari versi lama ditolak", A, id_, {"visi": "x"}, "lain", versi=v - 1)
    for catatan, potongan in (("", "tulis catatan"), ("  \n ", "tulis catatan"), ("x" * 501, "paling banyak 500"),
                              ("Perbaiki\x07", "karakter kendali"), ("Lihat slot gacor", "judi")):
        harus_gagal(ih.kembalikan, potongan, "catatan %r ditolak" % catatan[:20], A, id_, catatan, "adm", versi=v)
    for fungsi, args in ((ih.kembalikan, (A, id_, "Catatan.", "adm")), (ih.batal_ajukan, (A, id_, "op")),
                         (ih.buang_draf, (A, id_, "op")), (ih.terbitkan, (A, id_, {"visi": "V."}, "adm"))):
        harus_gagal(fungsi, "baru saja diubah", "%s dari versi lama ditolak" % fungsi.__name__, *args, versi=v - 1)
    v = ih.kembalikan(A, id_, "Tambahkan  strategi\r\npencapaian.", "adm", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "dikembalikan" and d["catatan"]["isi"] == "Tambahkan strategi\npencapaian." and d["catatan"]["oleh"] == "adm"
        and d["isi"]["visi"] == "Visi diajukan, diperbaiki.", "dikembalikan dengan catatan, isi tetap")
    harus_gagal(ih.kembalikan, "menunggu persetujuan", "hanya draf yang menunggu bisa dikembalikan", A, id_, "Lagi.", "adm", versi=v)
    harus_gagal(ih.batal_ajukan, "menunggu persetujuan", "hanya draf yang menunggu bisa dibatalkan", A, id_, "op", versi=v)
    v = ih.simpan_draf(A, id_, {"visi": "Visi.", "strategi": ["Strategi satu."]}, "op", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "dikembalikan" and d["catatan"]["isi"].startswith("Tambahkan"), "draf yang dikembalikan tetap membawa catatannya")
    v = ih.ajukan(A, id_, d["isi"], "op", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "menunggu" and "catatan" not in d, "diajukan lagi: catatan lama selesai")
    v = ih.batal_ajukan(A, id_, "op", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "draf" and "diajukan" not in d, "pengajuan dibatalkan")
    v = ih.ajukan(A, id_, d["isi"], "op", versi=v)
    harus_gagal(ih.terbitkan, "belum berisi", "isi kosong tidak diterbitkan dari draf", A, id_, {"misi": []}, "adm", versi=v, dari_draf=True)
    v = ih.terbitkan(A, id_, ih.draf(ih.baca(A, id_))["isi"], "adm", versi=v, dari_draf=True)
    data = ih.baca(A, id_)
    cek(data["draf"] is None and data["terbit"]["isi"]["visi"] == "Visi." and data["terbit"]["diajukan"]["oleh"] == "op"
        and data["terbit"]["oleh"] == "adm", "diterbitkan dari draf: draf selesai, pengajunya dicatat")
    k = ih.keadaan(A, id_)
    cek(k["status"] == "terbit" and k["tayang"], "keadaan: terbit dan tampil")
    v = ih.tarik(A, id_, "adm", versi=v)
    data = ih.baca(A, id_)
    d = ih.draf(data) or {}
    cek(data["terbit"] is None and d.get("isi", {}).get("visi") == "Visi." and d.get("status") == "draf",
        "ditarik: isinya menjadi draf")
    v = ih.terbitkan(A, id_, {"visi": "Visi baru."}, "adm", versi=v, dari_draf=True)
    v = ih.simpan_draf(A, id_, {"visi": "Draf berikutnya."}, "op", versi=v)
    v = ih.tarik(A, id_, "adm", versi=v)
    cek(ih.draf(ih.baca(A, id_))["isi"] == {"visi": "Draf berikutnya."}, "ditarik dengan draf: draf yang ada tetap")
    cek(ih.tarik(A, id_, "adm", versi=v) == v, "tarik halaman yang tidak terbit tidak menulis apa pun")
    v_t = ih.terbitkan(A, id_, {"visi": "Sementara."}, "adm", versi=v)
    harus_gagal(ih.tarik, "baru saja diubah", "tarik dari versi lama ditolak", A, id_, "adm", versi=v_t - 1)
    v = ih.tarik(A, id_, "adm", versi=v_t)
    # an old version made the draft
    def isi_versi(x):
        with io.open(riwayat.baca_versi("prodi/%s/halaman-%s" % (A, id_), x["versi"]), encoding="utf-8") as f:
            return json.load(f)
    versi = versi_riwayat(A, id_)
    lama = [x for x in versi if isi_versi(x).get("terbit")][-1]          # the oldest version with published content
    v = ih.pakai_versi(A, id_, lama["versi"], "terbit", "op", versi=v)
    d = ih.draf(ih.baca(A, id_))
    cek(d["status"] == "draf" and d["isi"] == {"visi": "Visi.", "strategi": ["Strategi satu."]} and
        versi_riwayat(A, id_)[0]["aksi"].startswith("pakai versi"),
        "versi lama dijadikan draf: %r" % d["isi"])
    harus_gagal(ih.pakai_versi, "versi tidak", "versi yang tidak ada ditolak", A, id_, "20000101-000000-000000", "terbit", "op", versi=v)
    harus_gagal(ih.pakai_versi, "versi tidak", "nama versi yang aneh ditolak", A, id_, "../../rahasia", "terbit", "op", versi=v)
    harus_gagal(ih.pakai_versi, "tidak dikenal", "bagian versi yang aneh ditolak", A, id_, lama["versi"], "diubah", "op", versi=v)
    kosong_ = [x for x in versi if not isi_versi(x).get("terbit")][-1]
    harus_gagal(ih.pakai_versi, "tidak memuat isi terbit", "versi tanpa isi terbit", A, id_, kosong_["versi"], "terbit", "op", versi=v)
    # a published page whose content no longer passes the checks is published but not shown
    path = lokasi.path_data(ih.nama_berkas(A, "tendik"))
    lokasi.tulis_json(path, {"versi": 1, "terbit": {"isi": {"daftar": [{"nama": ""}]}, "oleh": "x", "waktu": "2026-01-01T00:00:00"},
                             "draf": None})
    k = ih.keadaan(A, "tendik")
    cek(k["status"] == "terbit" and not k["tayang"], "isi terbit yang tidak lolos: terbit, tidak tampil")
    os.remove(path)
    cek(ih.keadaan(A, "ruang")["status"] == "kosong", "keadaan: kosong")
    for x in ("visi-misi",):
        os.remove(lokasi.path_data(ih.nama_berkas(A, x)))

    # ============================================================== through the admin
    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("opa", "operator", [A]), ("admb", "admin", [B])):
        akun_baru(nama, peran, p, super_)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    klien = {}
    for i, nama in enumerate(("superuji", "adma", "opa", "admb")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (60 + i)
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ks, ka, ko = klien["superuji"], klien["adma"], klien["opa"]
    URL = "/prodi/%s/halaman/" % A

    def buka(c, id_h, tambahan=""):
        r = c.get(URL + id_h + tambahan)
        cek(r.status_code == 200, "buka %s: %s" % (id_h, r.status_code))
        return r.get_data(as_text=True)

    def kirim(c, id_h, html, aksi="simpan", ubah=None):
        f = Formulir(html)
        data = f.data(ubah, aksi)
        for nama in f.berkas:
            data.add(nama, (io.BytesIO(b""), ""))
        return c.post(URL + id_h, data=data, content_type="multipart/form-data")

    def pesan(c, r):
        return c.get(r.headers["Location"]).get_data(as_text=True) if r.status_code == 302 else r.get_data(as_text=True)

    def tombol(html):
        return re.findall(r'<button type="submit"[^>]* name="aksi" value="([^"]+)"', html)

    # an operator writes and submits
    kirim(ko, "sejarah", buka(ko, "sejarah"), "tambah:linimasa")
    html = buka(ko, "sejarah")
    cek({"ajukan"} <= set(tombol(html)) and not {"terbitkan", "kembalikan", "tarik"} & set(tombol(html)),
        "operator: tombol ajukan, tanpa terbitkan/kembalikan/tarik: %r" % tombol(html))
    r = kirim(ko, "sejarah", html, "ajukan", {"uraian": "Program studi berdiri pada 1985.", "linimasa.0.tahun": "19x5",
                                              "linimasa.0.peristiwa": "Berdiri"})
    teks = pesan(ko, r)
    d = ih.draf(ih.baca(A, "sejarah"))
    cek("Belum diajukan: 1 isian perlu diperbaiki" in teks and d["status"] == "draf" and d["isi"]["linimasa"][0]["tahun"] == "19x5",
        "pengajuan dengan isian salah ditolak, ketikan disimpan sebagai draf")
    r = kirim(ko, "sejarah", buka(ko, "sejarah"), "ajukan", {"linimasa.0.tahun": "1985"})
    d = ih.draf(ih.baca(A, "sejarah"))
    cek(r.status_code == 302 and "Diajukan untuk diterbitkan" in pesan(ko, r) and d["status"] == "menunggu"
        and d["isi"]["linimasa"] == [{"tahun": 1985, "peristiwa": "Berdiri"}], "operator mengajukan")
    html = buka(ko, "sejarah")
    cek("batal-ajukan" in tombol(html) and "ajukan" not in tombol(html) and "buang" not in tombol(html),
        "draf yang diajukan: operator hanya bisa membatalkan pengajuan, tidak membuang")
    kirim(ko, "sejarah", html, ubah={"uraian": "Program studi berdiri pada tahun 1985."})
    d = ih.draf(ih.baca(A, "sejarah"))
    cek(d["status"] == "menunggu" and d["isi"]["uraian"].endswith("tahun 1985."), "menyunting draf yang diajukan tetap menunggu")
    v = ih.baca(A, "sejarah")["versi"]
    for aksi in ("terbitkan", "kembalikan", "tarik"):
        r = kirim(ko, "sejarah", buka(ko, "sejarah"), aksi, {"catatan": "x"})
        cek(r.status_code == 403 and ih.baca(A, "sejarah")["versi"] == v, "operator tidak bisa %s (%s)" % (aksi, r.status_code))
    r = kirim(ko, "sejarah", buka(ko, "sejarah"), "buang")
    cek("tidak dapat dibuang" in pesan(ko, r) and ih.draf(ih.baca(A, "sejarah")) is not None, "operator tidak membuang draf yang menunggu")
    r = kirim(ko, "sejarah", buka(ko, "sejarah"), "batal-ajukan")
    cek("Pengajuan dibatalkan" in pesan(ko, r) and ih.draf(ih.baca(A, "sejarah"))["status"] == "draf", "operator membatalkan pengajuan")
    kirim(ko, "sejarah", buka(ko, "sejarah"), "ajukan")
    cek(ih.draf(ih.baca(A, "sejarah"))["status"] == "menunggu", "diajukan lagi")

    # what the admin sees: the list, the dashboard
    teks = ka.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek("1 halaman menunggu persetujuan Anda" in teks and "Menunggu persetujuan (1)" in teks and "diajukan" in teks and "oleh opa" in teks,
        "daftar admin: halaman yang menunggu")
    teks = ka.get("/prodi/%s/halaman?status=menunggu" % A).get_data(as_text=True)
    cek(teks.count('href="%s' % URL) == 1 and "Sejarah" in teks, "saringan menunggu: satu halaman")
    cek(ka.get("/prodi/%s/halaman?status=aneh" % A).status_code == 404, "saringan yang tidak dikenal")
    teks = ka.get("/prodi/%s/" % A).get_data(as_text=True)
    cek("1 halaman menunggu persetujuan Anda" in teks and "0 dari 22" in teks, "dasbor admin: halaman yang menunggu")
    html = buka(ka, "sejarah")
    cek({"terbitkan", "kembalikan"} <= set(tombol(html)) and 'name="catatan"' in html and "diajukan" in html,
        "admin: tombol terbitkan dan kembalikan dengan catatan")

    # sent back with a note, fixed, submitted again
    r = kirim(ka, "sejarah", html, "kembalikan", {"catatan": ""})
    cek("Belum dikembalikan: tulis catatan" in pesan(ka, r) and ih.draf(ih.baca(A, "sejarah"))["status"] == "menunggu",
        "kembalikan tanpa catatan ditolak")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "kembalikan", {"catatan": "Tambahkan foto gedung <b>lama</b>."})
    d = ih.draf(ih.baca(A, "sejarah"))
    cek("Dikembalikan ke penulis" in pesan(ka, r) and d["status"] == "dikembalikan" and d["catatan"]["oleh"] == "adma",
        "admin mengembalikan dengan catatan")
    html = buka(ko, "sejarah")
    cek("Catatan dari adma" in html and "Tambahkan foto gedung &lt;b&gt;lama&lt;/b&gt;." in html and "ajukan" in tombol(html),
        "operator melihat catatan (di-escape) dan bisa mengajukan lagi")
    teks = ko.get("/prodi/%s/" % A).get_data(as_text=True)
    cek("1 halaman dikembalikan dengan catatan" in teks, "dasbor operator: halaman yang dikembalikan")
    kirim(ko, "sejarah", html, "ajukan", {"uraian": "Program studi berdiri pada tahun 1985 di Manado."})
    cek(ih.draf(ih.baca(A, "sejarah"))["status"] == "menunggu", "diperbaiki dan diajukan lagi")

    # two people on the same version
    html_admin = buka(ka, "sejarah")
    kirim(ko, "sejarah", buka(ko, "sejarah"), ubah={"uraian": "Program studi berdiri pada tahun 1985 di Manado, Sulawesi Utara."})
    r = kirim(ka, "sejarah", html_admin, "terbitkan")
    cek(r.status_code == 409 and "baru saja diubah oleh opa" in r.get_data(as_text=True) and ih.terbit(A, "sejarah") is None,
        "menerbitkan dari versi lama ditolak, tidak ada yang terbit")

    # published: the site shows it
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "terbitkan")
    data = ih.baca(A, "sejarah")
    cek(r.status_code == 302 and "Diterbitkan" in pesan(ka, r) and data["draf"] is None and
        data["terbit"]["isi"]["uraian"].endswith("Sulawesi Utara.") and data["terbit"]["diajukan"]["oleh"] == "opa",
        "admin menerbitkan draf yang diajukan")
    situs = halaman_situs("profil/sejarah")
    cek("Sulawesi Utara." in situs and MENYUSUL not in situs and "Berdiri" in situs, "situs menampilkan isi yang terbit")
    teks = ka.get("/prodi/%s/" % A).get_data(as_text=True)
    cek("1 dari 22" in teks and "menunggu persetujuan Anda" not in teks, "dasbor: satu halaman wajib terbit")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "terbitkan")
    cek("Tidak ada perubahan untuk diterbitkan" in pesan(ka, r) and ih.baca(A, "sejarah")["versi"] == data["versi"],
        "terbitkan tanpa perubahan tidak menulis apa pun")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "terbitkan", {"linimasa.0.peristiwa": "Jurusan berdiri"})
    cek(ih.terbit(A, "sejarah")["linimasa"][0]["peristiwa"] == "Jurusan berdiri" and ih.draf(ih.baca(A, "sejarah")) is None
        and "Jurusan berdiri" in halaman_situs("profil/sejarah"), "admin menerbitkan perubahan langsung")
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "terbitkan", {"linimasa.0.tahun": "19x5"})
    cek("Belum diterbitkan: 1 isian perlu diperbaiki" in pesan(ka, r) and ih.terbit(A, "sejarah")["linimasa"][0]["tahun"] == 1985
        and ih.draf(ih.baca(A, "sejarah"))["isi"]["linimasa"][0]["tahun"] == "19x5", "isi yang tidak lolos tidak terbit, menjadi draf")
    kirim(ka, "sejarah", buka(ka, "sejarah"), "buang")
    cek(ih.draf(ih.baca(A, "sejarah")) is None, "admin membuang draf")

    # withdrawn: the site says "sedang dilengkapi" again; the content is the draft
    r = kirim(ka, "sejarah", buka(ka, "sejarah"), "tarik")
    data = ih.baca(A, "sejarah")
    cek("Ditarik dari situs" in pesan(ka, r) and data["terbit"] is None and ih.draf(data)["isi"]["linimasa"][0]["peristiwa"] == "Jurusan berdiri",
        "ditarik, isinya menjadi draf")
    cek(MENYUSUL in halaman_situs("profil/sejarah") and "Jurusan berdiri" not in halaman_situs("profil/sejarah"),
        "situs kembali sedang dilengkapi")
    html = buka(ka, "sejarah")
    cek("tarik" not in tombol(html), "tanpa isi terbit tidak ada tombol tarik")

    # the page's history; an old version made the draft
    r = ka.get(URL + "sejarah/riwayat")
    teks = r.get_data(as_text=True)
    for nama in ("Diajukan", "Dikembalikan dengan catatan", "Pengajuan dibatalkan", "Diterbitkan", "Ditarik dari situs", "Draf dibuang"):
        cek(nama in teks, "riwayat halaman menyebut %r" % nama)
    cek(r.status_code == 200 and "Isi terbit" in teks and "Draf (menunggu persetujuan)" in teks, "riwayat: isi setiap versi")
    versi = versi_riwayat(A, "sejarah")
    tarik_v = [x for x in versi if x["aksi"] == "tarik sejarah"][0]
    r = ka.get(URL + "sejarah/riwayat/%s?bagian=terbit" % tarik_v["versi"])
    teks = r.get_data(as_text=True)
    cek(r.status_code == 200 and "Versi lama" in teks and "Jurusan berdiri" in teks and "Kembali ke riwayat halaman" in teks,
        "pratinjau versi lama")
    cek(ka.get(URL + "sejarah/riwayat/%s?bagian=draf" % tarik_v["versi"]).status_code == 404, "bagian yang tidak ada di versi itu")
    cek(ka.get(URL + "sejarah/riwayat/20000101-000000-000000").status_code == 404 and
        ka.get(URL + "sejarah/riwayat/bukan-versi").status_code == 404, "versi yang tidak ada")
    terbit_lama = [x for x in versi if x["aksi"] == "terbitkan sejarah"][-1]      # before the first publish: the waiting draft
    html = ko.get(URL + "sejarah/riwayat").get_data(as_text=True)
    f = Formulir(html, semua=True)
    v = ih.baca(A, "sejarah")["versi"]
    with ko.session_transaction() as s:
        token = s["csrf"]
    r = ko.post(URL + "sejarah/riwayat/%s" % terbit_lama["versi"], data={"csrf": token, "versi": str(v), "bagian": "draf"})
    d = ih.draf(ih.baca(A, "sejarah"))
    cek(r.status_code == 302 and d["status"] == "draf" and d["isi"]["uraian"].endswith("Sulawesi Utara.") and
        d["isi"]["linimasa"][0]["peristiwa"] == "Berdiri", "operator menjadikan draf lama sebagai draf: %r" % d["isi"].get("uraian"))
    cek("Versi lama dijadikan draf" in ko.get(r.headers["Location"]).get_data(as_text=True), "pesan versi lama")
    r = ko.post(URL + "sejarah/riwayat/%s" % terbit_lama["versi"], data={"csrf": token, "versi": str(v), "bagian": "draf"})
    cek(r.status_code == 409, "versi lama dari formulir lama ditolak")
    r = ko.post(URL + "sejarah/riwayat/%s" % terbit_lama["versi"], data={"csrf": token, "versi": "x", "bagian": "draf"})
    cek(r.status_code == 400, "tanpa versi ditolak")
    r = ko.post(URL + "sejarah/riwayat/%s" % terbit_lama["versi"], data={"csrf": token, "versi": str(v + 1), "bagian": "aneh"})
    cek(r.status_code == 400, "bagian aneh ditolak")
    cek(ih.terbit(A, "sejarah") is None, "versi lama tidak pernah langsung ke situs")

    # completeness: a second page waiting, then the superadmin's table and its CSV
    kirim(ko, "perpustakaan", buka(ko, "perpustakaan"), "tambah:tautan")
    kirim(ko, "perpustakaan", buka(ko, "perpustakaan"), "ajukan", {
        "uraian": "Perpustakaan fakultas.", "tautan.0.label": "Repositori", "tautan.0.alamat": "https://repo.unsrat.ac.id/"})
    kirim(ka, "perpustakaan", buka(ka, "perpustakaan"), "terbitkan")
    kirim(ko, "ruang", buka(ko, "ruang"), "ajukan", {"uraian": "Ruang kuliah di gedung A."})
    kirim(ko, "laboratorium", buka(ko, "laboratorium"), ubah={"uraian": "Laboratorium (draf)."})
    teks = ks.get("/super/kelengkapan").get_data(as_text=True)
    cek("Teknik Informatika" in teks and "Teknik Elektro" in teks and ">1/22<" in teks and ">0/22<" in teks,
        "kelengkapan: setiap prodi dengan jumlah halaman wajib terbit")
    cek("<strong>1</strong> halaman menunggu persetujuan" in teks and "<strong>0</strong> dari 2 situs aktif" in teks,
        "kelengkapan: ringkasan")
    r = ks.get("/super/kelengkapan.csv")
    cek(r.status_code == 200 and r.mimetype == "text/csv" and "kelengkapan-halaman-prodi.csv" in r.headers.get("Content-Disposition", ""),
        "unduhan CSV")
    teks = r.get_data(as_text=True)
    cek(teks.startswith("﻿"), "CSV ber-BOM untuk Excel")
    baris = list(csv.reader(io.StringIO(teks.lstrip("﻿"))))
    kepala, data_a = baris[0], [b for b in baris[1:] if b[0] == A][0]
    kolom = dict(zip(kepala, data_a))
    cek(kepala[:13] == ["kode_pddikti", "jenjang", "nama", "fakultas", "slug", "aktif", "wajib_terbit", "wajib_total", "menunggu",
                        "dikembalikan", "draf", "terakhir_diubah", "kriteria_akreditasi"]
        and len(kepala) == 13 + len(ih.TEMPLAT), "kolom CSV: %r" % kepala[:13])
    cek(kolom["wajib_terbit"] == "1" and kolom["wajib_total"] == "22" and kolom["menunggu"] == "1" and kolom["draf"] == "2",
        "CSV: jumlah prodi A: %r" % [kolom[x] for x in ("wajib_terbit", "menunggu", "draf")])
    cek(kolom["Perpustakaan dan Referensi"].startswith("terbit 20") and kolom["Ruang Kuliah dan Ruang Pendukung"] == "menunggu persetujuan"
        and kolom["Sejarah"] == "draf"
        and kolom["Kerja Sama"] == "belum diisi" and "Jadwal Kuliah dan Ujian (opsional)" in kolom, "CSV: keadaan setiap halaman")
    cek(len(baris) == 3 and [b for b in baris[1:] if b[0] == B][0][6] == "0", "CSV: semua prodi terdaftar: %r" % [b[:7] for b in baris[1:]])
    cek(ka.get("/super/kelengkapan").status_code == 403 and ka.get("/super/kelengkapan.csv").status_code == 403,
        "kelengkapan hanya untuk superadmin")
    teks = ks.get("/").get_data(as_text=True)
    cek('href="/super/kelengkapan"' in teks, "dasbor superadmin menautkan kelengkapan")

    # the audit log
    log = audit.baca(prodi=A, batas=10000)
    for aksi in ("isi-diajukan", "isi-pengajuan-dibatalkan", "isi-dikembalikan", "isi-diterbitkan", "isi-ditarik", "isi-versi-dipakai"):
        cek(any(x["aksi"] == aksi and x.get("halaman") for x in log), "log audit mencatat %s" % aksi)
    print("uji_alur_isi: %d versi riwayat halaman sejarah" % len(versi_riwayat(A, "sejarah")))
except Exception as e:                 # a step that went wrong stops the flow; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.append("alur berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
    gagal.insert(0, gagal.pop())
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_alur_isi: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
