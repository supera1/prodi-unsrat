# -*- coding: utf-8 -*-
"""The English version of the programme sites, Fase 5 langkah 1 (K-P37): platform/bahasa.py,
platform/template/teks-en.json, the English labels of menu.json, the builder and the superadmin's switch.

- the dictionary: every _("...") of the templates, every label and choice of the content templates, the same %s/%d;
  Indonesian pages get the text itself, English ones the dictionary's, a text it does not know stops an English page;
  English names, levels, dates and accreditation ranks;
- the site: /<slug>/en/ only for a programme switched on, with the pages from the official data in English (home,
  profile and learning outcomes, specification, accreditation, lecturers, calendar, contact) and the groups that have
  them; lang="en", English text and no Indonesian fixed text; the programme's Indonesian front texts not used, its
  background kept; every link of an English page leads to a page that exists, and never to an Indonesian page the
  English version does not have; hreflang and the language link both ways on the pages that have both; the calendar
  pointing to the Indonesian one; the page checks and the integrity check clean; Indonesian pages without English
  unchanged; production: canonical addresses and the sitemap with both languages; switched off, /en/ is gone;
- the admin: the superadmin switches the English version on and off, the site is built again, the audit log has it.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import html
import io
import json
import os
import posixpath
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
    print("uji_inggris: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-inggris-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bahasa  # noqa: E402
import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import prodi  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B = "55201", "20201"
gagal = []
HALAMAN_EN = ["", "profil", "profil/akreditasi", "akademik", "akademik/profil-lulusan", "akademik/spesifikasi",
              "akademik/kalender", "dosen", "dosen/dosen-tetap", "kontak"]
# fixed Indonesian text of the templates that an English page must never show
INDONESIA = ("sedang dilengkapi", "Universitas Sam Ratulangi", "Program Studi", "Beranda", "Jelajahi", "Surel",
             "Capaian pembelajaran", "Langsung ke konten", "Semua program studi", "Fakultas Teknik", "Kriteria")


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def baca(rel):
    path = os.path.join(lokasi.publik(), *rel.split("/"))
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def halaman(slug, alamat):
    return baca(posixpath.join(slug, alamat, "index.html") if alamat else posixpath.join(slug, "index.html"))


def bangun_semua(produksi=False):
    b = bangun.Pembangun(produksi=produksi)
    b.bangun()
    return b


def folder_html(slug):
    """Folders of the pages under a programme's site, relative to it."""
    akar = os.path.join(lokasi.publik(), slug)
    return sorted(os.path.relpath(f, akar).replace(os.sep, "/").replace(".", "", 1) if f == akar else
                  os.path.relpath(f, akar).replace(os.sep, "/") for f, _d, n in os.walk(akar) if "index.html" in n)


def tautan(teks):
    return re.findall(r'<a [^>]*href="([^"]+)"', teks)


try:
    # ============================================================== the dictionary
    cek(bahasa.periksa() == [], "kamus lengkap untuk templat: %r" % bahasa.periksa()[:5])
    k = bahasa.kamus()
    for t in bahasa.teks_templat():
        cek(t in k, "teks templat %r ada di kamus" % t)
    label = set()

    def jalan(n):
        if n.get("label"):
            label.add(n["label"])
        if n["jenis"] == "pilihan":
            label.update(n["opsi"])
        for _k, s in n.get("bidang", []):
            jalan(s)
        if n["jenis"] == "daftar":
            jalan(n["isi"])
    for t in list(ih.TEMPLAT.values()) + [ih.TEMPLAT_TAMBAHAN]:
        jalan(t)
    cek(not label - set(k), "label dan pilihan templat isi ada di kamus: %r" % sorted(label - set(k))[:5])
    menu = menu_mod.baca_templat()
    for b in menu_mod.semua_butir(menu).values():
        cek(b.get("label_en") and b.get("deskripsi_en") and b["deskripsi_en"] != b["deskripsi"],
            "menu %s punya label dan deskripsi Inggris" % b["id"])
    salah = json.loads(json.dumps(menu))
    del salah[1]["anak"][0]["label_en"]
    path = os.path.join(KERJA, "menu-salah.json")
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump({"menu": salah}, f)
    try:
        menu_mod.baca_templat(path)
        cek(False, "menu tanpa label_en ditolak")
    except menu_mod.GagalMenu as e:
        cek("sejarah: label_en dan deskripsi_en wajib" in str(e), "pesan menu tanpa label_en: %s" % e)
    id_, en = bahasa.penerjemah("id"), bahasa.penerjemah("en")
    cek(id_("Beranda") == "Beranda" and id_("tidak ada di kamus") == "tidak ada di kamus" and en("Beranda") == "Home",
        "penerjemah id dan en")
    try:
        en("Teks yang tidak ada di kamus")
        cek(False, "teks tanpa terjemahan menghentikan halaman Inggris")
    except KeyError as e:
        cek("teks-en.json" in str(e), "pesan teks tanpa terjemahan: %s" % e)
    cek(bahasa.penerjemah("en", lunak=True)("PMB") == "Admissions"
        and bahasa.penerjemah("en", lunak=True)("Tautan lain") == "Tautan lain", "terjemahan data: lunak")
    cek(bahasa.nama_tampil({"jenjang": "S1", "nama": "Teknik Informatika", "nama_en": "Informatics Engineering"}, "en")
        == "Bachelor Program in Informatics Engineering"
        and bahasa.nama_tampil({"jenjang": "Profesi", "nama": "Program Profesi Insinyur",
                                "nama_en": "Professional Engineer Program"}, "en") == "Professional Engineer Program"
        and bahasa.nama_tampil({"jenjang": "S1", "nama": "Teknik Informatika", "nama_en": ""}, "en")
        == "S1 Teknik Informatika"
        and bahasa.nama_tampil({"jenjang": "S1", "nama": "Teknik Informatika", "nama_en": "X"}, "id")
        == "S1 Teknik Informatika", "nama prodi dalam bahasa Inggris")
    cek(bahasa.tanggal_en("2030-08-15") == "August 15, 2030" and bahasa.tanggal_en("2030-13-01") == "",
        "tanggal Inggris")
    cek(bahasa.label_akreditasi("Unggul", "en") == "Excellent" and bahasa.label_akreditasi("Baik Sekali", "en")
        == "Very Good" and bahasa.label_akreditasi("A", "en") == "A" and bahasa.label_akreditasi("belum", "en") == ""
        and bahasa.label_akreditasi("Unggul", "id") == "Unggul", "peringkat akreditasi Inggris")

    # ============================================================== the platform
    os.makedirs(os.environ["WWW_DATA"])
    pa = dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering",
              bidang_kerja="Pengembang perangkat lunak.", bidang_kerja_en="Software developer.",
              cpl=[{"kode": "CPL 1", "isi": "Mampu merancang sistem.", "isi_en": "Able to design systems.",
                    "kurikulum": "2025/2026"}])
    for nama, isi in {"prodi": {"program": [pa, prodi(B, "Teknik Elektro")]},
                      "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering",
                                         "jenis": "fakultas", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                      "kalender": {"semester": []},
                      "situs": {"identitas": {"nama": {"id": "Universitas Sam Ratulangi", "en": "Sam Ratulangi University"}},
                                "kontak": {"alamat": {"id": ["Jl. Kampus UNSRAT Bahu", "Kota Manado"],
                                                      "en": ["Jl. Kampus UNSRAT Bahu", "Manado, Indonesia"]},
                                           "hari": {"id": "Senin–Jumat", "en": "Monday–Friday"}, "jam": "07.30–16.00"},
                                "utilitas": {"id": [{"label": "PMB", "href": "https://regmaba.unsrat.ac.id"}]}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)
    # the programme's own Indonesian front texts and a coloured background
    situs = lokasi.baca("prodi/%s/situs" % A) or {}
    situs.update(tagline="Kampus hijau di Manado, tempat belajar rekayasa.",
                 beranda={"judul": "Judul Indonesia Khusus", "latar": {"jenis": "utama"}})
    lokasi.tulis("prodi/%s/situs" % A, situs, "penguji", "Situs", "uji")
    ih.terbitkan(A, "sejarah", {"uraian": "Sejarah singkat program studi."}, "penguji")

    bangun_semua()
    cek(halaman("s1informatika", "en") is None and "bar-atas__bahasa" not in halaman("s1informatika", ""),
        "tanpa saklar: tidak ada versi Inggris")
    sebelum = {a: halaman("s1informatika", a) for a in ("profil/sejarah", "pengumuman")}

    # ============================================================== the English version
    registri.atur(A, "penguji", inggris=True)
    b = bangun_semua()
    cek(not b.peringatan, "bangun tanpa peringatan: %r" % b.peringatan[:3])
    ada = [f for f in folder_html("s1informatika") if f == "en" or f.startswith("en/")]
    cek(sorted(ada) == sorted(posixpath.join("en", a) if a else "en" for a in HALAMAN_EN),
        "halaman versi Inggris: %r" % ada)
    cek(halaman("s1elektro", "en") is None and "bar-atas__bahasa" not in halaman("s1elektro", ""),
        "prodi lain tanpa versi Inggris")
    for a in HALAMAN_EN:
        teks = halaman("s1informatika", posixpath.join("en", a) if a else "en") or ""
        cek('<html lang="en">' in teks, "en/%s: lang en" % a)
        polos = html.unescape(re.sub(r"<[^>]+>", " ", teks.split("<body>")[1] if "<body>" in teks else teks))
        polos = polos.replace("S1 Teknik Informatika", "")           # the Indonesian name, marked lang="id"
        for t in INDONESIA:
            cek(t not in polos, "en/%s tanpa teks Indonesia %r" % (a, t))
        cek('<a class="bar-atas__bahasa" href="' in teks and 'hreflang="id" lang="id">Bahasa Indonesia</a>' in teks,
            "en/%s: tautan ke versi Indonesia" % a)
        cek('<link rel="alternate" hreflang="id" href="https://prodi.unsrat.ac.id/s1informatika/%s">'
            % (a + "/" if a else "") in teks and '<link rel="alternate" hreflang="en" href="https://prodi.unsrat.ac.id/'
            's1informatika/en/%s">' % (a + "/" if a else "") in teks, "en/%s: hreflang dua arah" % a)
        indonesia = halaman("s1informatika", a) or ""
        cek('hreflang="en" lang="en">English</a>' in indonesia and 'hreflang="en"' in indonesia,
            "%s: tautan ke versi Inggris" % (a or "beranda"))
        # every link leads to a page that exists, never to an Indonesian page without English
        folder = posixpath.join("s1informatika", "en", a) if a else "s1informatika/en"
        for h in tautan(teks):
            if re.match(r"^(https?:|mailto:|#)", h):
                continue
            tujuan = posixpath.normpath(posixpath.join(folder, h.split("?")[0]))
            cek(os.path.exists(os.path.join(lokasi.publik(), *tujuan.split("/"))), "en/%s: tautan %s ada" % (a, h))
            cek(not tujuan.startswith("s1informatika/profil/sejarah") and not tujuan.startswith("s1informatika/pengumuman"),
                "en/%s: tidak menautkan halaman tanpa versi Inggris (%s)" % (a, h))
    beranda = halaman("s1informatika", "en")
    cek("Bachelor Program in Informatics Engineering" in beranda and "Bachelor Program · Faculty of Engineering"
        in beranda and "Excellent" in beranda and "144 credits (SKS)" in beranda and "Software developer." in beranda
        and '<p class="pahlawan__en" lang="id">S1 Teknik Informatika</p>' in beranda, "beranda Inggris dari data resmi")
    cek("Judul Indonesia Khusus" not in beranda and "Kampus hijau" not in beranda and "pahlawan--utama" in beranda,
        "teks depan Indonesia tidak dipakai, latarnya tetap")
    cek('"inLanguage": "en"' in beranda and '"alternateName": "S1 Teknik Informatika"' in beranda, "JSON-LD Inggris")
    cek("Pengumuman" not in beranda and "News" not in beranda, "pengumuman tidak di versi Inggris")
    lulusan = halaman("s1informatika", "en/akademik/profil-lulusan")
    cek("Able to design systems." in lulusan and "Mampu merancang" not in lulusan and "Curriculum 2025/2026." in lulusan,
        "CPL Inggris")
    cek("Accreditation rank" in halaman("s1informatika", "en/profil/akreditasi")
        and "Sertifikat akreditasi" not in halaman("s1informatika", "en/profil/akreditasi"), "akreditasi Inggris")
    kontak = halaman("s1informatika", "en/kontak")
    cek("Manado, Indonesia" in kontak and "Monday–Friday" in kontak and "Faculty of Engineering" in kontak,
        "kontak Inggris")
    cek('href="../../../akademik/kalender/" hreflang="id">Open the academic calendar (Indonesian)'
        in halaman("s1informatika", "en/akademik/kalender"), "kalender menautkan versi Indonesia")
    cek(">Admissions<" in beranda and ">PMB<" in halaman("s1informatika", ""), "tautan universitas diterjemahkan")
    profil = halaman("s1informatika", "en/profil")
    cek(">Accreditation</a>" in profil and ">History</a>" not in profil, "kelompok Inggris hanya memuat halaman berversi Inggris")
    for a, lama in sebelum.items():
        cek(halaman("s1informatika", a) == lama, "%s tanpa versi Inggris tidak berubah" % a)
    jumlah, temuan = periksa_situs(lokasi.publik(), "inggris")
    cek(not temuan, "pemeriksaan halaman: %r" % temuan[:5])
    cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "cek integritas bersih")

    # production: canonical addresses, the sitemap with both languages
    bangun_semua(produksi=True)
    cek('<link rel="canonical" href="https://prodi.unsrat.ac.id/s1informatika/en/akademik/spesifikasi/">'
        in halaman("s1informatika", "en/akademik/spesifikasi"), "alamat kanonik Inggris")
    peta = baca("sitemap.xml")
    cek('xmlns:xhtml="http://www.w3.org/1999/xhtml"' in peta and
        '<url><loc>https://prodi.unsrat.ac.id/s1informatika/akademik/spesifikasi/</loc><xhtml:link rel="alternate" '
        'hreflang="id" href="https://prodi.unsrat.ac.id/s1informatika/akademik/spesifikasi/"/><xhtml:link '
        'rel="alternate" hreflang="en" href="https://prodi.unsrat.ac.id/s1informatika/en/akademik/spesifikasi/"/></url>'
        in peta and "<url><loc>https://prodi.unsrat.ac.id/s1informatika/profil/sejarah/</loc></url>" in peta
        and "<loc>https://prodi.unsrat.ac.id/s1informatika/en/akademik/</loc><xhtml:link" in peta,
        "sitemap dengan kedua bahasa")

    # ============================================================== the superadmin's switch
    SANDI = "Kebun 7 pagi hari nomor 1 untuk uji"
    id_a, sementara = akun.buat(None, "superuji", "Super Uji", "super", [])
    akun.ganti_sandi(id_a, sementara, SANDI)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})
    c = app.test_client()
    c.environ_base["REMOTE_ADDR"] = "103.84.116.60"
    c.get("/masuk")
    with c.session_transaction() as s_:
        token = s_["csrf"]
    cek(c.post("/masuk", data={"csrf": token, "pengguna": "superuji", "sandi": SANDI}).status_code == 302, "superadmin masuk")
    teks = c.get("/super/prodi/%s" % A).get_data(as_text=True)
    cek("Versi bahasa Inggris" in teks and "Nonaktifkan versi Inggris" in teks and "/s1informatika/en/" in teks,
        "detail prodi menampilkan saklar versi Inggris")
    with c.session_transaction() as s_:
        token = s_["csrf"]
    r = c.post("/super/prodi/%s/inggris" % A, data={"csrf": token, "inggris": "0"})
    cek(r.status_code == 302 and not registri.cari(registri.baca(), A).get("inggris") and halaman("s1informatika", "en") is None
        and "bar-atas__bahasa" not in halaman("s1informatika", ""), "dinonaktifkan: versi Inggris hilang dari situs")
    with c.session_transaction() as s_:
        token = s_["csrf"]
    r = c.post("/super/prodi/%s/inggris" % A, data={"csrf": token, "inggris": "1"})
    cek(r.status_code == 302 and registri.cari(registri.baca(), A).get("inggris") and halaman("s1informatika", "en/kontak"),
        "diaktifkan: versi Inggris dibangun")
    log = c.get("/super/audit").get_data(as_text=True)
    cek("inggris-diaktifkan" in log and "inggris-dinonaktifkan" in log, "saklar tercatat di log audit")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_inggris: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
