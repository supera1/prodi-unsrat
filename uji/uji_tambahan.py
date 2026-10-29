# -*- coding: utf-8 -*-
"""A programme's extra pages and their embedded content (K-P35): platform/halaman_tambahan.py, platform/sematan.py,
isi_halaman.TEMPLAT_TAMBAHAN, the builder, the integrity check and platform/admin/tambahan_admin.py.

- embeds: share links and embed codes of the allowed services become their embed address, anything else is refused
  with the reason (other hosts, http, short links, edit links, folders, markup), a stored address passes only in the
  form normalkan() makes, the CSP allows exactly those hosts (www.google.com only for maps);
- the list of extra pages: addresses made from names, the checks (names, spam, groups, addresses, limit), add, change,
  reorder, remove, history;
- the site: an extra page only once published, under /<slug>/halaman/<alamat>/, after its group's own pages; the embed
  as a sandboxed frame without top navigation, with a title and a link to open it; escaped; renamed and moved without
  changing its address; off the site when withdrawn or removed; a broken list ignored with a warning; the admin's
  preview without frames; the integrity check clean, and finding a frame without sandbox;
- the admin: who manages the pages, adding (with refusals), the editor for operators (an embed code pasted becomes
  the embed address), publishing builds the page, renaming, moving, reordering, removing, another programme's page,
  the superadmin's list, the history's names, completeness unchanged.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import html
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
    print("uji_tambahan: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-tambahan-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import halaman_tambahan as ht  # noqa: E402
import isi_admin  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import sematan  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import prodi  # noqa: E402

A, B = "55201", "20201"
SLUG = {A: "s1informatika", B: "s1elektro"}
FORM = "https://docs.google.com/forms/d/e/1FAIpQLSdAbCdEfGhIjKlMnOpQr/viewform?embedded=true"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def halaman_situs(kode, alamat):
    path = os.path.join(lokasi.publik(), SLUG[kode], *alamat.split("/"), "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def bangun_semua():
    b = bangun.Pembangun(produksi=False)
    b.bangun()
    return b


try:
    # ============================================================== embeds
    diterima = {
        '<iframe src="%s" width="640" height="1200" frameborder="0">Memuat…</iframe>' % FORM: FORM,
        "https://docs.google.com/forms/d/e/1FAIpQLSdAbCdEfGhIjKlMnOpQr/viewform?usp=sf_link": FORM,
        "https://docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUv/edit?usp=sharing":
            "https://docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUv/preview",
        "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUv/edit#gid=0":
            "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUv/preview",
        '<iframe src="https://docs.google.com/spreadsheets/d/e/2PACX-1vAbCdEfGhIjKlMnOp/pubhtml?widget=true&amp;headers=false"></iframe>':
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vAbCdEfGhIjKlMnOp/pubhtml?widget=true&headers=false",
        "https://docs.google.com/document/d/e/2PACX-1vAbCdEfGhIjKlMnOp/pub":
            "https://docs.google.com/document/d/e/2PACX-1vAbCdEfGhIjKlMnOp/pub?embedded=true",
        "https://docs.google.com/presentation/d/1AbCdEfGhIjKlMnOpQrStUv/edit#slide=id.p":
            "https://docs.google.com/presentation/d/1AbCdEfGhIjKlMnOpQrStUv/embed",
        "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUv/view?usp=sharing":
            "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUv/preview",
        "https://drive.google.com/open?id=1AbCdEfGhIjKlMnOpQrStUv": "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUv/preview",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?si=abc": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "<iframe width='560' src='//www.youtube.com/embed/dQw4w9WgXcQ?si=x' title='YouTube'></iframe>":
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988!2d124.8!3d1.45" style="border:0;" allowfullscreen=""></iframe>':
            "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3988!2d124.8!3d1.45",
        "https://calendar.google.com/calendar/embed?src=prodi%40unsrat.ac.id&ctz=Asia%2FMakassar":
            "https://calendar.google.com/calendar/embed?src=prodi@unsrat.ac.id&ctz=Asia/Makassar",
    }
    for teks, harus in diterima.items():
        hasil, pesan = sematan.normalkan(teks)
        cek(hasil == harus and pesan is None, "sematan %r -> %r (%s)" % (teks[:60], hasil, pesan))
        cek(hasil is None or sematan.normalkan(hasil)[0] == hasil, "bentuk sematan tetap: %r" % hasil)
        cek(hasil is None or sematan.periksa(hasil) is None, "alamat sematan yang sah lolos: %r" % hasil)
    ditolak = {
        "https://informatika.unsrat.ac.id/database-skripsi-ta/": "hanya dari Google Docs",
        "https://evil.example/embed": "hanya dari Google Docs",
        "http://docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUv/edit": "diawali https://",
        "javascript:alert(1)": "diawali https://",
        "https://user:pw@docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUv/edit": "diawali https://",
        "https://docs.google.com:8443/document/d/1AbCdEfGhIjKlMnOpQrStUv/edit": "diawali https://",
        "https://docs.google.com/forms/d/1AbCdEfGhIjKlMnOpQrStUv/edit": "tombol Kirim",
        "https://forms.gle/AbCdEf123": "forms.gle",
        "https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUv": "folder Google Drive",
        "https://www.google.com/maps/place/UNSRAT": "Sematkan peta",
        "https://maps.app.goo.gl/AbCd": "Sematkan peta",
        "https://www.youtube.com/watch?v=pendek": "video YouTube",
        'https://docs.google.com/document/d/1AbCdEfGh"onload="x/edit': "tidak sah",
        "<script>alert(1)</script>": "kode sematan",
        "": "kosong",
    }
    for teks, harus in ditolak.items():
        hasil, pesan = sematan.normalkan(teks)
        cek(hasil is None and pesan and harus in pesan, "sematan %r ditolak dengan alasan %r: %r" % (teks[:60], harus, pesan))
    cek("belum diubah" in (sematan.periksa("https://youtu.be/dQw4w9WgXcQ") or ""), "alamat berbagi yang belum diubah ditolak")
    cek(sematan.periksa(None) and sematan.periksa(FORM) is None, "periksa alamat sematan")
    cek(sematan.layanan(FORM) == "Google Forms" and sematan.layanan("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ") == "YouTube"
        and sematan.layanan("https://evil.example/") == "", "nama layanan")
    cek(sematan.CSP_FRAME.split() == ["https://calendar.google.com", "https://docs.google.com", "https://drive.google.com",
                                      "https://www.google.com/maps/embed", "https://www.youtube-nocookie.com"],
        "CSP frame-src hanya layanan sematan: %r" % sematan.CSP_FRAME)
    cek("frame-src 'self' https://storage.googleapis.com %s;" % sematan.CSP_FRAME in bangun.CSP, "CSP situs memuat layanan sematan")
    cek("allow-top-navigation" not in sematan.SANDBOX and "allow-scripts" in sematan.SANDBOX, "sandbox tanpa navigasi atas")

    # ============================================================== the list of extra pages
    for label, harus in (("Database Skripsi/TA", "database-skripsi-ta"), ("2024 Wisuda", "h-2024-wisuda"),
                         ("Ékspor Ímpor", "ekspor-impor"), ("", "halaman"), ("!!!", "halaman"), ("x" * 80, "x" * 40)):
        cek(ht.alamat_dari(label) == harus, "alamat dari %r: %r" % (label, ht.alamat_dari(label)))
    kelompok = ht.kelompok_ada()
    cek(set(kelompok) == {"profil", "akademik", "dosen", "riset", "mahasiswa", "fasilitas"}, "kelompok: %r" % sorted(kelompok))
    sah = [{"id": "x0a1b2c", "label": "Database Skripsi", "kelompok": "akademik", "alamat": "database-skripsi"},
           {"id": "x0a1b2d", "label": "Video Profil", "kelompok": "profil", "alamat": "video-profil"}]
    cek(ht.periksa(sah) == [], "daftar halaman tambahan sah: %r" % ht.periksa(sah))
    for pesan, ubah in (
            ("nama kosong", lambda d: d[0].update(label="")),
            ("nama terlalu panjang", lambda d: d[0].update(label="x" * 61)),
            ("nama dengan markah", lambda d: d[0].update(label="<b>Skripsi</b>")),
            ("nama judi", lambda d: d[0].update(label="Info slot gacor")),
            ("nama ganda", lambda d: d[1].update(label="database skripsi")),
            ("kelompok tidak dikenal", lambda d: d[0].update(kelompok="beranda")),
            ("alamat dengan huruf besar", lambda d: d[0].update(alamat="Database")),
            ("alamat diawali angka", lambda d: d[0].update(alamat="1skripsi")),
            ("alamat dengan garis miring", lambda d: d[0].update(alamat="a/b")),
            ("alamat ganda", lambda d: d[1].update(alamat="database-skripsi")),
            ("id tidak sah", lambda d: d[0].update(id="../x")),
            ("id ganda", lambda d: d[1].update(id="x0a1b2c")),
            ("lebih dari 10", lambda d: d.extend({"id": "x1%05x" % i, "label": "H%d" % i, "kelompok": "riset",
                                                   "alamat": "h-%d" % i} for i in range(9)))):
        d = [dict(x) for x in sah]
        ubah(d)
        cek(ht.periksa(d), "daftar halaman tambahan %s harus ditolak" % pesan)
    cek("judi" in ht.periksa([dict(sah[0], label="Info slot gacor")])[0], "penolakan nama menyebut jenisnya")

    # ============================================================== the platform for the site and the admin
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

    # add, change, reorder, remove
    h1 = ht.tambah(A, "Database Skripsi", "akademik", "", "penguji")
    cek(ih.POLA_TAMBAHAN.match(h1["id"]) and h1["alamat"] == "database-skripsi" and h1["dibuat"]["oleh"] == "penguji",
        "tambah: id, alamat dari nama: %r" % h1)
    h2 = ht.tambah(A, "Video Profil", "akademik", "video", "penguji")
    for pesan, fungsi in (("alamat ganda", lambda: ht.tambah(A, "Lain", "akademik", "video", "penguji")),
                          ("kelompok", lambda: ht.tambah(A, "Lain", "kontak", "", "penguji")),
                          ("urutan", lambda: ht.ubah(A, {h1["id"]: {"urutan": 100}}, "penguji"))):
        try:
            fungsi()
            cek(False, "harus ditolak: %s" % pesan)
        except ht.GagalTambahan:
            pass
    ht.ubah(A, {h2["id"]: {"urutan": 0}, h1["id"]: {"urutan": 1}}, "penguji")
    cek([h["id"] for h in ht.baca(A)] == [h2["id"], h1["id"]], "urutan diubah")
    cek(ht.hapus(A, "x999999", "penguji") is None and ht.hapus(A, h2["id"], "penguji")["id"] == h2["id"]
        and [h["id"] for h in ht.baca(A)] == [h1["id"]], "hapus")
    cek(any(v["berkas"] == ht.berkas(A) for v in riwayat.daftar(100)), "versi daftar sebelumnya di riwayat")

    # the content template
    cek(ih.templat_halaman(h1["id"]) is ih.TEMPLAT_TAMBAHAN and ih.templat_halaman("x12") is None
        and ih.templat_halaman("x0a1b2C") is None and ih.nama_berkas(A, h1["id"]) == "prodi/%s/halaman-%s" % (A, h1["id"]),
        "templat halaman tambahan")
    isi_sah = {"uraian": "Daftar judul skripsi **2020-2026**.",
               "sematan": [{"judul": "Daftar <judul> skripsi", "alamat": FORM, "tinggi": "Tinggi", "keterangan": "Diperbarui tiap semester."},
                           {"judul": "Video", "alamat": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"}],
               "tautan": [{"label": "Repositori", "alamat": "https://repo.unsrat.ac.id/"}]}
    cek(ih.periksa(h1["id"], isi_sah, A) == [], "isi halaman tambahan sah: %r" % ih.periksa(h1["id"], isi_sah, A))
    for pesan, sematan_ in (("alamat luar", {"judul": "X", "alamat": "https://evil.example/x"}),
                            ("alamat berbagi mentah", {"judul": "X", "alamat": "https://youtu.be/dQw4w9WgXcQ"}),
                            ("tanpa judul", {"alamat": FORM}),
                            ("tinggi tidak dikenal", {"judul": "X", "alamat": FORM, "tinggi": "Raksasa"})):
        cek(ih.periksa(h1["id"], {"sematan": [sematan_]}, A), "sematan %s harus ditolak" % pesan)
    bagian, _hilang = ih.tampilan(h1["id"], isi_sah)
    s = [b for b in bagian if b["jenis"] == "sematan"][0]
    cek(s["judul"] == "" and [x["layanan"] for x in s["sematan"]] == ["Google Forms", "YouTube"]
        and [x["tinggi"] for x in s["sematan"]] == ["tinggi", "sedang"], "tampilan sematan: %r" % s)

    # ============================================================== the site
    b = bangun_semua()
    cek(halaman_situs(A, "halaman/database-skripsi") is None and h1["label"] not in halaman_situs(A, "akademik"),
        "belum terbit: tidak ada di situs dan menu")
    ih.terbitkan(A, h1["id"], isi_sah, "penguji")
    b = bangun_semua()
    teks = halaman_situs(A, "halaman/database-skripsi")
    cek(teks is not None, "halaman tambahan terbit di /<slug>/halaman/<alamat>/")
    teks = teks or ""
    iframe = re.findall(r"<iframe[^>]*>", teks)
    cek(len(iframe) == 2 and all('sandbox="%s"' % sematan.SANDBOX in f and 'loading="lazy"' in f and "referrerpolicy=" in f
                                 for f in iframe), "bingkai bersandbox, malas dimuat: %r" % iframe)
    cek('src="%s"' % FORM in teks and 'title="Daftar &lt;judul&gt; skripsi"' in teks
        and "<h2 id=\"bagian-sematan-1\">Daftar &lt;judul&gt; skripsi</h2>" in teks, "judul sematan di-escape, jadi judul bingkai")
    cek('target="_blank" rel="noopener">Buka Google Forms di tab baru' in teks and "Buka YouTube di tab baru" in teks,
        "tautan buka di tab baru")
    cek("sematan--tinggi" in teks and "sematan--sedang sematan--video" in teks, "kelas tinggi dan video")
    cek("frame-src 'self' https://storage.googleapis.com %s;" % sematan.CSP_FRAME in html.unescape(teks),
        "CSP halaman memuat layanan sematan")
    teks_ak = halaman_situs(A, "akademik")
    cek('href="../halaman/database-skripsi/">Database Skripsi</a>' in teks_ak
        and teks_ak.index("Jadwal Kuliah dan Ujian") < teks_ak.index('>Database Skripsi</a></h2>'),
        "di indeks kelompok, sesudah halaman bawaan")
    cek(halaman_situs(B, "halaman/database-skripsi") is None, "prodi lain tidak terpengaruh")
    temuan = [t for rel in ("halaman/database-skripsi", "akademik")
              for t in cek_integritas.periksa_teks("%s/%s/index.html" % (SLUG[A], rel), halaman_situs(A, rel))]
    cek(temuan == [], "pemeriksaan integritas bersih: %r" % temuan)
    for pesan, ubah in (("tanpa sandbox", lambda x: x.replace(' sandbox="%s"' % sematan.SANDBOX, "")),
                        ("navigasi atas", lambda x: x.replace(sematan.SANDBOX, sematan.SANDBOX + " allow-top-navigation"))):
        cek(any(t[0] == "SKRIP" for t in cek_integritas.periksa_teks("x/index.html", ubah(teks))),
            "pemantau melaporkan bingkai %s" % pesan)
    cek(any("evil.example" in t[2] for t in cek_integritas.periksa_teks(
        "x/index.html", teks.replace("https://docs.google.com/forms", "https://evil.example/forms"))), "pemantau: host lain")
    cek(not cek_integritas.periksa_teks("x/index.html", teks.replace(
        "</main>", '<iframe class="pdf__pembaca" src="../unggahan/a.pdf" title="PDF"></iframe></main>')),
        "PDF di bingkai dari situs sendiri tidak dilaporkan")
    pratinjau = str(bangun.bagian_html(ih.tampilan(h1["id"], isi_sah)[0], lambda r: ""))
    cek("<iframe" not in pratinjau and "Pratinjau admin tidak memuat isi dari situs lain" in pratinjau
        and "Buka Google Forms di tab baru" in pratinjau, "pratinjau admin tanpa bingkai")

    # renamed and moved: same address
    ht.ubah(A, {h1["id"]: {"label": "Skripsi dan TA", "kelompok": "riset"}}, "penguji")
    b = bangun_semua()
    cek(">Skripsi dan TA</a></h2>" in halaman_situs(A, "riset") and ">Skripsi dan TA</a></h2>" not in halaman_situs(A, "akademik")
        and "<h1" in (halaman_situs(A, "halaman/database-skripsi") or ""), "nama dan kelompok diganti, alamat tetap")
    ih.tarik(A, h1["id"], "penguji")
    b = bangun_semua()
    cek(halaman_situs(A, "halaman/database-skripsi") is None and "Skripsi dan TA" not in halaman_situs(A, "riset"),
        "ditarik: hilang dari situs dan menu")
    lokasi.tulis_json(lokasi.path_data(ht.berkas(A)), {"halaman": [dict(ht.baca(A)[0], label="Promo slot gacor")]})
    ih.terbitkan(A, h1["id"], isi_sah, "penguji")
    b = bangun_semua()
    cek(any(p.startswith("prodi %s: halaman tambahan diabaikan" % A) for p in b.peringatan)
        and halaman_situs(A, "halaman/database-skripsi") is None, "daftar rusak: diabaikan dengan peringatan")
    ih.tarik(A, h1["id"], "penguji")
    lokasi.tulis_json(lokasi.path_data(ht.berkas(A)), {"halaman": []})

    # ============================================================== the admin
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
        with c.session_transaction() as s_:
            token = s_["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ks, ka, ko, kb = klien["superuji"], klien["adma"], klien["opa"], klien["admb"]

    def kirim(c, url, **data):
        with c.session_transaction() as s_:
            data["csrf"] = s_["csrf"]
        return c.post(url, data=data)

    U = "/prodi/%s/tambahan" % A
    teks = ka.get(U).get_data(as_text=True)
    cek("Belum ada halaman tambahan" in teks and 'href="%s"' % U in teks and "Buat halaman dan isi" in teks, "halaman tambahan kosong")
    cek("Halaman tambahan</a>" not in ko.get("/prodi/%s/" % A).get_data(as_text=True), "operator tanpa menu halaman tambahan")
    r = kirim(ka, U, label="Pendaftaran Seminar", kelompok="mahasiswa", alamat="")
    baru = ht.baca(A)[-1]
    cek(r.status_code == 302 and r.headers["Location"].endswith("/prodi/%s/halaman/%s" % (A, baru["id"]))
        and baru["alamat"] == "pendaftaran-seminar" and baru["kelompok"] == "mahasiswa", "buat: lalu ke penyunting")
    for data, harus in (({"label": "Info slot gacor", "kelompok": "mahasiswa"}, "memuat teks judi"),
                        ({"label": "Lain", "kelompok": "mahasiswa", "alamat": "pendaftaran-seminar"}, "sudah dipakai"),
                        ({"label": "Lain", "kelompok": "mahasiswa", "alamat": "Bukan Alamat"}, "alamat harus"),
                        ({"label": "Lain", "kelompok": "beranda"}, "kelompok menu tidak dikenal")):
        r = kirim(ka, U, **data)
        cek(r.status_code == 400 and harus in r.get_data(as_text=True) and len(ht.baca(A)) == 1,
            "buat ditolak (%s): %s" % (harus, r.status_code))

    # the editor: the operator writes, an embed code pasted becomes the embed address
    E = "/prodi/%s/halaman/%s" % (A, baru["id"])
    teks = ko.get(E).get_data(as_text=True)
    cek("Sematan" in teks and "Dokumen PDF" in teks and "Lihat halaman ini di situs" not in teks,
        "penyunting halaman tambahan, tanpa tautan situs sebelum terbit")
    ih.simpan_draf(A, baru["id"], {"sematan": [{}]}, "opa")
    cek("Alamat atau kode sematan" in ko.get(E).get_data(as_text=True), "isian alamat sematan")
    versi = ih.baca(A, baru["id"])["versi"]
    r = kirim(ko, E, versi=str(versi), aksi="ajukan", uraian="Pendaftaran seminar proposal.",
              **{"sematan.0.judul": "Formulir pendaftaran", "sematan.0.tinggi": "Tinggi",
                 "sematan.0.alamat": '<iframe src="%s" width="640" height="900">Memuat…</iframe>' % FORM.replace("&", "&amp;")})
    d = ih.draf(ih.baca(A, baru["id"]))
    cek(r.status_code == 302 and d and d["status"] == "menunggu" and d["isi"]["sematan"][0]["alamat"] == FORM,
        "operator mengajukan; kode sematan menjadi alamat sematan: %r" % (d and d["isi"].get("sematan")))
    teks = ka.get(E + "/pratinjau").get_data(as_text=True)
    cek("<iframe" not in teks and "Pratinjau admin tidak memuat isi dari situs lain" in teks, "pratinjau admin tanpa bingkai")
    teks = ko.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek("Pendaftaran Seminar" in teks and "Tambahan" in teks, "daftar isi halaman memuat halaman tambahan")
    r = kirim(ka, E, versi=str(ih.baca(A, baru["id"])["versi"]), aksi="terbitkan", uraian="Pendaftaran seminar proposal.",
              **{"sematan.0.judul": "Formulir pendaftaran", "sematan.0.tinggi": "Tinggi", "sematan.0.alamat": FORM})
    teks = halaman_situs(A, "halaman/pendaftaran-seminar") or ""
    cek(r.status_code == 302 and 'src="%s"' % FORM in teks and "Pendaftaran Seminar" in halaman_situs(A, "mahasiswa"),
        "terbitkan membangun halaman tambahan")
    cek("halaman/pendaftaran-seminar/\">Lihat halaman ini di situs" in ka.get(E).get_data(as_text=True),
        "tautan ke situs sesudah terbit")
    r = isi_admin.ringkasan_isi(A)
    cek(r["wajib"] == 22 and r["terbit"] == 0 and baru["id"] in r["halaman"], "kelengkapan tetap 22 halaman wajib")

    # an embed on a built-in page (K-P36): the Jadwal page, right under its introduction, from a Drive share link
    J = "/prodi/%s/halaman/jadwal" % A
    DRIVE = "https://drive.google.com/file/d/1PdfJadwalKuliahContoh0123/preview"
    teks = ko.get(J).get_data(as_text=True)
    cek(teks.index('id="f-uraian"') < teks.index('id="f-sematan"') < teks.index('id="f-jadwal"')
        and "Cara menyematkan:<br>PDF di Google Drive: Bagikan" in teks and "Siapa saja yang memiliki link" in teks
        and "Tambah sematan" in teks, "penyunting Jadwal: Sematan di bawah Uraian, cara menyematkan per baris")
    r = kirim(ko, J, versi="0", aksi="tambah:sematan", uraian="Jadwal kuliah semester ganjil.")
    d = ih.draf(ih.baca(A, "jadwal"))
    cek(r.status_code == 302 and d and d["isi"].get("sematan") == [{}]
        and "Alamat atau kode sematan" in ko.get(J).get_data(as_text=True), "Tambah sematan: isian sematan terbuka")
    r = kirim(ko, J, versi=str(ih.baca(A, "jadwal")["versi"]), aksi="ajukan", uraian="Jadwal kuliah semester ganjil.",
              **{"sematan.0.judul": "Jadwal kuliah", "sematan.0.alamat": "https://evil.example/jadwal"})
    d = ih.draf(ih.baca(A, "jadwal"))
    cek(r.status_code == 302 and d and d["status"] == "draf" and "hanya dari Google Docs" in ko.get(J).get_data(as_text=True),
        "sematan dari layanan lain ditolak; ketikan tetap di draf")
    r = kirim(ko, J, versi=str(ih.baca(A, "jadwal")["versi"]), aksi="ajukan", uraian="Jadwal kuliah semester ganjil.",
              **{"sematan.0.judul": "Jadwal kuliah", "sematan.0.tinggi": "Tinggi",
                 "sematan.0.alamat": DRIVE.replace("/preview", "/view?usp=sharing")})
    d = ih.draf(ih.baca(A, "jadwal"))
    cek(r.status_code == 302 and d["status"] == "menunggu" and d["isi"]["sematan"][0]["alamat"] == DRIVE,
        "tautan berbagi Google Drive menjadi alamat sematan: %r" % d["isi"].get("sematan"))
    r = kirim(ka, J, versi=str(ih.baca(A, "jadwal")["versi"]), aksi="terbitkan", uraian="Jadwal kuliah semester ganjil.",
              **{"sematan.0.judul": "Jadwal kuliah", "sematan.0.tinggi": "Tinggi", "sematan.0.alamat": DRIVE})
    teks = halaman_situs(A, "akademik/jadwal") or ""
    cek(r.status_code == 302 and 'src="%s"' % DRIVE in teks and 'sandbox="%s"' % sematan.SANDBOX in teks
        and "sematan--tinggi" in teks and "Buka Google Drive di tab baru" in teks
        and teks.index("Jadwal kuliah semester ganjil.") < teks.index("<iframe"),
        "Jadwal terbit dengan sematan Google Drive di bawah uraian")
    bawaan = ks.get("/super/tambahan").get_data(as_text=True).split("Sematan di halaman bawaan")[-1]
    cek("Jadwal Kuliah dan Ujian" in bawaan and "Google Drive" in bawaan and "akademik/jadwal/\">situs" in bawaan,
        "daftar superadmin memuat sematan di halaman bawaan")

    # renaming, moving, reordering, removing; another programme
    h3 = ht.tambah(A, "Video Profil", "profil", "", "adma")
    r = kirim(ka, U + "/simpan", **{"label-%s" % baru["id"]: "Seminar Proposal", "kelompok-%s" % baru["id"]: "akademik",
                                    "urutan-%s" % baru["id"]: "1", "label-%s" % h3["id"]: "Video Profil",
                                    "kelompok-%s" % h3["id"]: "profil", "urutan-%s" % h3["id"]: "0"})
    cek(r.status_code == 302 and [(h["label"], h["kelompok"]) for h in ht.baca(A)] ==
        [("Video Profil", "profil"), ("Seminar Proposal", "akademik")], "simpan nama, kelompok, urutan")
    cek("Seminar Proposal" in halaman_situs(A, "akademik") and halaman_situs(A, "halaman/pendaftaran-seminar"),
        "situs dibangun ulang, alamat tetap")
    r = kirim(ka, U + "/simpan", **{"urutan-%s" % h3["id"]: "abc"})
    cek(r.status_code == 400 and "urutan harus angka" in r.get_data(as_text=True), "urutan tidak sah ditolak")
    cek(kb.get("/prodi/%s/halaman/%s" % (A, baru["id"])).status_code == 403
        and kb.get("/prodi/%s/halaman/%s" % (B, baru["id"])).status_code == 404, "halaman prodi lain: 403/404")
    teks = ks.get("/super/tambahan").get_data(as_text=True)
    cek("Seminar Proposal" in teks and "Google Forms" in teks and "Video Profil" in teks and "Teknik Informatika" in teks,
        "daftar superadmin dengan layanan sematan")
    teks = ks.get("/super/riwayat").get_data(as_text=True)
    cek("halaman tambahan Seminar Proposal" in teks and "daftar halaman tambahan" in teks, "nama di riwayat")
    r = kirim(ka, U + "/%s/hapus" % baru["id"])
    cek(r.status_code == 302 and [h["id"] for h in ht.baca(A)] == [h3["id"]]
        and halaman_situs(A, "halaman/pendaftaran-seminar") is None and "Seminar Proposal" not in halaman_situs(A, "akademik"),
        "hapus: hilang dari menu dan situs")
    cek("halaman tambahan %s (sudah dihapus)" % baru["id"] in ks.get("/super/riwayat").get_data(as_text=True),
        "riwayat menyebut halaman yang dihapus")
    cek(ka.get(E).status_code == 404, "penyunting halaman yang dihapus: 404")
    for i in range(9):
        ht.tambah(A, "Halaman %d" % i, "fasilitas", "", "adma")
    teks = ka.get(U).get_data(as_text=True)
    r = kirim(ka, U, label="Kesebelas", kelompok="riset")
    cek("jumlah paling banyak" in teks and r.status_code == 400 and "paling banyak 10" in r.get_data(as_text=True),
        "paling banyak 10 halaman")
    cek("tambahan-dibuat" in ka.get("/prodi/%s/audit" % A).get_data(as_text=True), "tercatat di log audit")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_tambahan: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
