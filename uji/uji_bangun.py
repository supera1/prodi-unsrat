# -*- coding: utf-8 -*-
"""Step 3 of phase 1: the master template, the colours and the builder (platform/bangun/).

Builds a small made-up set of programmes in a temporary directory and checks every page: one h1, lang, title and
description, CSP, no inline styles or scripts, heading order, image alternatives, unique ids, and that every link
inside the site leads to a file that exists. Then checks menu settings, colours, staging and production output,
building one programme, slug changes, inactive programmes, escaping, and the integrity check against the manifest.
When the www checkout sits next to this repository, the real 97 programmes are built and checked the same way.

Needs Jinja2 (platform/admin/requirements.txt): run with .venv/bin/python.
"""
from __future__ import print_function

import copy
import io
import json
import os
import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AKAR, "platform"))
sys.path.insert(0, os.path.join(AKAR, "platform", "bangun"))
sys.path.insert(0, os.path.join(AKAR, "platform", "pemantau"))

try:
    import jinja2  # noqa: F401
except ImportError:
    print("uji_bangun: Jinja2 belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-bangun-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"),
                  ("PRODI_NGINX", "nginx")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ.pop("PRODI_MODE", None)

import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
import warna  # noqa: E402

WWW_ASLI = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026", "site", "mockup", "data")
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


# ------------------------------------------------------------------ page checks

class Pengurai(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.tag, self.judul, self.dalam_judul, self.ld = [], "", False, []
        self.dalam_ld = False

    def handle_starttag(self, tag, attrs):
        self.tag.append((tag, dict(attrs)))
        if tag == "title":
            self.dalam_judul = True
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.dalam_ld = True
            self.ld.append("")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "title":
            self.dalam_judul = False
        if tag == "script":
            self.dalam_ld = False

    def handle_data(self, data):
        if self.dalam_judul:
            self.judul += data
        if self.dalam_ld:
            self.ld[-1] += data


def _tujuan(publik, rel_halaman, href):
    """Path of the file a link inside the site points to, or None for links that leave the site."""
    if re.match(r"^[a-z][a-z0-9+.-]*:", href) or href.startswith("//"):
        return None
    jalur = href.split("#")[0].split("?")[0]
    if not jalur:
        return None
    if jalur.startswith("/"):
        hasil = os.path.normpath(os.path.join(publik, jalur.lstrip("/")))
    else:
        hasil = os.path.normpath(os.path.join(publik, os.path.dirname(rel_halaman), jalur))
    if href.split("#")[0].split("?")[0].endswith("/") or os.path.isdir(hasil):
        hasil = os.path.join(hasil, "index.html")
    return hasil


def periksa_situs(publik, label):
    """Check every page in a built site. Returns the number of pages checked."""
    temuan, jumlah = [], 0
    for folder, _d, nama in os.walk(publik):
        for n in nama:
            if not n.endswith(".html"):
                continue
            jumlah += 1
            path = os.path.join(folder, n)
            rel = os.path.relpath(path, publik).replace(os.sep, "/")
            with io.open(path, encoding="utf-8") as f:
                teks = f.read()
            p = Pengurai()
            p.feed(teks)
            tag = p.tag
            html = [a for t, a in tag if t == "html"]
            if not html or html[0].get("lang") != "id":
                temuan.append((rel, "lang bukan id"))
            if sum(1 for t, _a in tag if t == "h1") != 1:
                temuan.append((rel, "jumlah h1 bukan 1"))
            if not p.judul.strip():
                temuan.append((rel, "judul kosong"))
            if not any(t == "meta" and a.get("name") == "description" and (a.get("content") or "").strip() for t, a in tag):
                temuan.append((rel, "meta description kosong"))
            if not any(t == "meta" and a.get("http-equiv") == "Content-Security-Policy" for t, a in tag):
                temuan.append((rel, "tanpa CSP"))
            for t, a in tag:
                if "style" in a:
                    temuan.append((rel, "atribut style pada <%s>" % t))
                if any(k.startswith("on") for k in a):
                    temuan.append((rel, "atribut on* pada <%s>" % t))
                if t == "script" and a.get("type") != "application/ld+json":
                    temuan.append((rel, "skrip selain JSON-LD"))
                if t == "img" and "alt" not in a:
                    temuan.append((rel, "gambar tanpa alt"))
            for ld in p.ld:
                try:
                    json.loads(ld)
                except ValueError:
                    temuan.append((rel, "JSON-LD tidak sah"))
            tingkat = [int(t[1]) for t, _a in tag if re.match(r"^h[1-6]$", t)]
            for a, b in zip(tingkat, tingkat[1:]):
                if b > a + 1:
                    temuan.append((rel, "heading melompat h%d -> h%d" % (a, b)))
                    break
            ids = [a["id"] for _t, a in tag if "id" in a]
            if len(ids) != len(set(ids)):
                temuan.append((rel, "id ganda"))
            for _t, a in tag:
                if a.get("aria-current") == "page" and a.get("href"):
                    if os.path.normpath(_tujuan(publik, rel, a["href"]) or "") != os.path.normpath(path):
                        temuan.append((rel, "aria-current=page menunjuk ke halaman lain: %s" % a["href"]))
            for t, a in tag:
                for atr in ("href", "src"):
                    href = a.get(atr)
                    if not href:
                        continue
                    if href.startswith("#"):
                        if href[1:] and href[1:] not in ids:
                            temuan.append((rel, "anker %s tidak ada" % href))
                        continue
                    tujuan = _tujuan(publik, rel, href)
                    if tujuan and not os.path.isfile(tujuan):
                        temuan.append((rel, "tautan mati %s" % href))
    for rel, m in temuan[:30]:
        gagal.append("%s %s: %s" % (label, rel, m))
    if len(temuan) > 30:
        gagal.append("%s: ... dan %d temuan lain" % (label, len(temuan) - 30))
    return jumlah


def baca_halaman(rel):
    with io.open(os.path.join(lokasi.publik(), rel), encoding="utf-8") as f:
        return f.read()


def ada(rel):
    return os.path.isfile(os.path.join(lokasi.publik(), rel))


# ------------------------------------------------------------------ made-up www data

def prodi(kode, nama, jenjang, unit_kode, unit, cpl=2, **lain):
    p = {"kode_pddikti": kode, "nama": nama, "nama_en": "", "jenjang": jenjang, "gelar": "S.T.", "sks": 144,
         "unit_kode": unit_kode, "unit": unit, "website": "", "surel": "prodi@unsrat.ac.id", "bidang_kerja": "Bidang kerja.",
         "bidang_kerja_en": "", "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Teknik", "berlaku_hingga": "2030-08-15",
         "internasional": "", "slug": "x", "slug_en": "",
         "cpl": [{"kode": "CPL %d" % i, "isi": "Capaian %d." % i, "isi_en": "", "kurikulum": "2025/2026"} for i in range(1, cpl + 1)]}
    p.update(lain)
    return p


WWW = {
    "prodi": {"tampilkan_berlaku_hingga": True, "program": [
        prodi("55201", "Teknik Informatika", "S1", "ft", "Fakultas Teknik", nama_en="Informatics Engineering"),
        prodi("11901", "Profesi Dokter", "Profesi", "fk", "Fakultas Kedokteran", cpl=0, akreditasi="", lembaga_akreditasi=""),
        prodi("67201", "Ilmu Politik", "S1", "fisip", "FISIP")]},
    "unit": {"unit": [
        {"kode": "ft", "nama": "Fakultas Teknik", "website": "https://fatek.unsrat.ac.id", "surel": "ft@unsrat.ac.id",
         "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}},
        {"kode": "fk", "nama": "Fakultas Kedokteran", "bendera": {"dasar": "#013300", "tulisan": "#FFFF00"}},
        {"kode": "fisip", "nama": "FISIP", "bendera": {"dasar": "#FF8500", "tulisan": "#3500FF"}}]},
    "kalender": {"judul": "Kalender", "teks": "Lihat [pengumuman resmi](pengumuman.html) dan [ini](javascript:alert(1)).",
                 "semester": [{"jenis": "gasal", "tahun_akademik": "2026/2027", "tampil": True, "catatan": "",
                               "kelompok": [{"judul": "Administrasi", "kegiatan": [{"tanggal": "1 Juli", "kegiatan": "Bayar UKT"}]}]},
                              {"jenis": "genap", "tahun_akademik": "2026/2027", "tampil": False, "kelompok": []}]},
    "situs": {"identitas": {"nama": {"id": "Universitas Sam Ratulangi"}, "moto": "Si Tou Timou Tumou Tou",
                            "tahun_hak_cipta": "2026"},
              "kontak": {"alamat": {"id": ["Jl. Kampus UNSRAT Bahu", "Manado 95115"]}, "telepon": ["(0431) 1"],
                         "surel": "r@unsrat.ac.id"},
              "media_sosial": [], "utilitas": {"id": [{"label": "PMB", "href": "https://regmaba.unsrat.ac.id"}]}},
}


def tulis_www(isi):
    os.makedirs(os.environ["WWW_DATA"], exist_ok=True)
    for nama, data in isi.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)


def siapkan_fiktif():
    tulis_www(WWW)
    tarik_www.terapkan("penguji")
    path = os.path.join(KERJA, "slug.csv")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n")
        for kode, jenjang, nama, slug in (("55201", "S1", "Teknik Informatika", "s1informatika"),
                                          ("11901", "Profesi", "Profesi Dokter", "profesidokter"),
                                          ("67201", "S1", "Ilmu Politik", "s1politik")):
            f.write("%s,%s,%s,X,%s,https://prodi.unsrat.ac.id/%s/,x\n" % (kode, jenjang, nama, slug, slug))
    registri.siapkan_dari_csv("penguji", path)


def bangun_semua(produksi=False, kode=None):
    b = bangun.Pembangun(produksi=produksi, alamat="https://prodi.unsrat.ac.id")
    b.bangun(kode)
    return b


try:
    # --- the page checker itself finds what it is meant to find
    rusak = os.path.join(KERJA, "rusak")
    os.makedirs(os.path.join(rusak, "a"))
    with io.open(os.path.join(rusak, "a", "index.html"), "w", encoding="utf-8") as f:
        f.write('<html lang="en"><head><title> </title></head><body><h1>x</h1><h3 id="d">y</h3><h1 id="d" style="x">z</h1>'
                '<img src="../a/index.html"><a href="../tidak-ada/">m</a><a href="#hilang">n</a><script>alert(1)</script>'
                '<a href="../" aria-current="page">o</a></body></html>')
    sebelum = len(gagal)
    periksa_situs(rusak, "rusak")
    ditemukan = " ".join(gagal[sebelum:])
    del gagal[sebelum:]
    for harapan in ("lang bukan id", "jumlah h1", "judul kosong", "meta description", "tanpa CSP", "atribut style",
                    "skrip selain", "gambar tanpa alt", "heading melompat", "id ganda", "tautan mati ../tidak-ada/",
                    "anker #hilang", "aria-current=page menunjuk"):
        cek(harapan in ditemukan, "pemeriksa halaman harus menemukan: %s" % harapan)

    # --- colours
    for p in warna.baca_palet():
        cek(not warna.periksa(p["utama"], p["aksen"]), "palet %s harus lolos uji kontras: %r" % (p["id"], warna.periksa(p["utama"], p["aksen"])))
    cek(any(p["id"] == warna.CADANGAN for p in warna.baca_palet()), "palet cadangan unsrat harus ada")
    cek(len({p["id"] for p in warna.baca_palet()}) == len(warna.baca_palet()), "id palet harus unik")
    cek(abs(warna.kontras("#FFFFFF", "#000000") - 21) < 0.01, "kontras hitam-putih harus 21")
    cek(warna.periksa("#FFFF00", "#000099"), "kuning sebagai warna utama harus ditolak")
    cek(warna.periksa("#12345", "#F2B705"), "kode warna rusak harus ditolak")
    for bendera in ({"dasar": "#FFFFFF", "tulisan": "#FFFFFF"}, {"dasar": "#00FF01", "tulisan": "#3500FF"},
                    {"dasar": "#FF8500", "tulisan": "#3500FF"}, {"dasar": "#C6C6C6", "tulisan": "#C6C6C6"}, None, {}):
        w = warna.warna_prodi(None, bendera)
        cek(not warna.periksa(w["utama"], w["aksen"]), "warna dari bendera %r harus lolos kontras" % (bendera,))
    cek(warna.warna_prodi(None, {"dasar": "#000099", "tulisan": "#FFFF00"})["utama"] == "#000099", "bendera FT dipakai apa adanya")
    cek(warna.warna_prodi("toska", None)["utama"] == "#0F5F66", "palet pilihan harus dipakai")
    cek(warna.warna_prodi("tidak-ada", None)["palet"] == "unsrat", "palet tak dikenal jatuh ke unsrat")
    if os.path.isfile(os.path.join(WWW_ASLI, "unit.json")):
        with io.open(os.path.join(WWW_ASLI, "unit.json"), encoding="utf-8") as f:
            for u in json.load(f)["unit"]:
                if u.get("bendera"):
                    w = warna.warna_prodi(None, u["bendera"])
                    cek(w["palet"] == "fakultas", "fakultas %s harus mendapat warna benderanya: %s" % (u["kode"], w["keterangan"]))

    # --- master menu and menu settings
    templat = menu_mod.baca_templat()
    semua = menu_mod.semua_butir(templat)
    cek(sum(1 for b in templat if b.get("anak")) == 6, "menu induk harus punya 6 kelompok")
    cek(all(b.get("jenis") or b.get("anak") for b in semua.values()), "setiap butir punya jenis atau anak")
    cek(menu_mod.periksa_pengaturan(templat, {"sejarah": {"sembunyi": True}}), "halaman wajib tidak boleh disembunyikan")
    cek(menu_mod.periksa_pengaturan(templat, {"akreditasi": {"sembunyi": True}}), "halaman otomatis tidak boleh disembunyikan")
    cek(menu_mod.periksa_pengaturan(templat, {"profil": {"urutan": 1}}), "urutan kelompok tidak boleh diubah")
    cek(menu_mod.periksa_pengaturan(templat, {"sejarah": {"label": "x" * 61}}), "label terlalu panjang harus ditolak")
    cek(menu_mod.periksa_pengaturan(templat, {"sejarah": {"label": "slot gacor"}}), "label judi harus ditolak")
    cek(menu_mod.periksa_pengaturan(templat, {"sejarah": {"label": "<b>x</b>"}}), "label dengan < > harus ditolak")
    cek(menu_mod.periksa_pengaturan(templat, {"tidak-ada": {"label": "x"}}), "butir yang tidak ada harus ditolak")
    cek(menu_mod.periksa_pengaturan(templat, {"sejarah": {"warna": "x"}}), "kunci yang tidak dikenal harus ditolak")
    cek(not menu_mod.periksa_pengaturan(templat, {"jadwal": {"sembunyi": True}, "sejarah": {"label": "Riwayat", "urutan": 9}}),
        "pengaturan yang sah harus diterima")
    m = menu_mod.susun(templat, {"jadwal": {"sembunyi": True}, "sejarah": {"label": "Riwayat Kami", "urutan": 99}})
    profil = [e for e in m if e["id"] == "profil"][0]
    cek(profil["anak"][-1]["id"] == "sejarah" and profil["anak"][-1]["label"] == "Riwayat Kami", "urutan dan label harus diterapkan")
    cek("jadwal" not in [x["id"] for x in menu_mod.halaman(m)], "butir tersembunyi tidak boleh ada di menu")

    # --- helpers
    cek(str(bangun.tautan_md("a [b](x.html) c")) == 'a <a href="https://www.unsrat.ac.id/x.html">b</a> c', "tautan relatif ke www")
    cek("href" not in str(bangun.tautan_md("[b](javascript:alert(1))")), "tautan javascript: tidak boleh jadi tautan")
    cek("href" not in str(bangun.tautan_md("[b](//jahat.com/x)")), "tautan // tidak boleh jadi tautan")
    cek("&lt;script&gt;" in str(bangun.tautan_md("<script>x</script>")), "teks kalender harus di-escape")
    cek("</script" not in str(bangun.json_ld({"name": "</script><script>alert(1)</script>"}))[:-9], "JSON-LD tidak boleh menutup <script>")
    cek(bangun.tanggal("2030-08-15") == "15 Agustus 2030" and bangun.tanggal("2030-13-01") == "", "format tanggal")
    cek(bangun.nama_tampil({"jenjang": "Profesi", "nama": "Profesi Dokter"}) == "Profesi Dokter", "nama profesi tidak diulang")
    cek(bangun.nama_tampil({"jenjang": "S1", "nama": "Teknik Informatika"}) == "S1 Teknik Informatika", "nama sarjana")

    # --- staging build of the made-up programmes
    siapkan_fiktif()
    lokasi.tulis("prodi/55201/situs", {"tagline": "<script>alert(1)</script> Unggul berbudaya", "palet": "toska", "logo": None,
                                       "media_sosial": [], "menu": {"jadwal": {"sembunyi": True},
                                                                    "sejarah": {"label": "Riwayat Kami"}}}, "penguji", "uji", "uji")
    lokasi.tulis("prodi/67201/situs", {"menu": {"sejarah": {"sembunyi": True}}}, "penguji", "uji", "uji")
    b = bangun_semua()
    n = periksa_situs(lokasi.publik(), "staging")
    halaman_per_prodi = sum(1 for _ in menu_mod.halaman(menu_mod.susun(templat)))
    cek(n == 3 * halaman_per_prodi - 1 + 2, "jumlah halaman staging %d tidak sesuai" % n)
    beranda = baca_halaman("s1informatika/index.html")
    cek("&lt;script&gt;alert(1)&lt;/script&gt; Unggul berbudaya" in beranda, "tagline harus di-escape")
    cek("<script>alert" not in beranda, "tagline tidak boleh menjadi skrip")
    cek('content="noindex, nofollow"' in beranda and "pita-staging" in beranda, "staging harus noindex dan berpita")
    cek('rel="canonical"' not in beranda, "staging tanpa canonical")
    cek("Riwayat Kami" in baca_halaman("s1informatika/profil/index.html"), "label menu baru harus tampil")
    cek(not ada("s1informatika/akademik/jadwal/index.html"), "halaman opsional tersembunyi tidak boleh dibangun")
    cek("akademik/jadwal" not in beranda, "halaman tersembunyi tidak boleh ditautkan")
    cek(ada("s1politik/profil/sejarah/index.html"), "pengaturan menu tidak sah diabaikan: halaman wajib tetap ada")
    cek(any("67201" in x and "pengaturan menu diabaikan" in x for x in b.peringatan), "pengaturan tidak sah harus diperingatkan")
    with io.open(os.path.join(lokasi.publik(), "s1informatika", "warna.css"), encoding="utf-8") as f:
        cek("#0F5F66" in f.read(), "warna.css harus memakai palet toska")
    with io.open(os.path.join(lokasi.publik(), "profesidokter", "warna.css"), encoding="utf-8") as f:
        cek("#013300" in f.read(), "warna.css profesi dokter harus warna bendera FK")
    cpl = baca_halaman("profesidokter/akademik/profil-lulusan/index.html")
    cek("Capaian pembelajaran lulusan sedang dilengkapi" in cpl, "prodi tanpa CPL harus tampil sedang dilengkapi")
    cek("Status akreditasi sedang dilengkapi" in baca_halaman("profesidokter/profil/akreditasi/index.html"), "akreditasi kosong")
    cek("15 Agustus 2030" in baca_halaman("s1informatika/profil/akreditasi/index.html"), "berlaku hingga tampil bila diizinkan")
    kal = baca_halaman("s1informatika/akademik/kalender/index.html")
    cek("Semester Gasal 2026/2027" in kal and "Genap" not in kal, "hanya semester yang tampil")
    cek('href="https://www.unsrat.ac.id/pengumuman.html"' in kal and "javascript:" not in kal, "tautan kalender aman")
    cek("Direktori Dosen UNSRAT" in baca_halaman("s1informatika/dosen/dosen-tetap/index.html"), "halaman dosen tanpa tautan khusus")
    akar = baca_halaman("index.html")
    cek(akar.count('class="kartu kartu--prodi"') == 3, "halaman akar harus memuat 3 prodi")
    with io.open(os.path.join(lokasi.publik(), "robots.txt"), encoding="utf-8") as f:
        cek("Disallow: /" in f.read(), "robots staging harus melarang")
    cek(not ada("sitemap.xml"), "staging tanpa sitemap")
    cek('href="/aset/' in baca_halaman("404.html"), "404 memakai alamat dari akar situs")

    # --- integrity check against the manifest
    temuan, jumlah = cek_integritas.periksa(lokasi.publik(), lokasi.manifes())
    cek(not temuan, "cek integritas harus bersih: %r" % temuan[:5])
    with io.open(os.path.join(lokasi.publik(), "s1politik", "index.html"), "a", encoding="utf-8") as f:
        f.write("<p>slot gacor</p>")
    with io.open(os.path.join(lokasi.publik(), "s1politik", "shell.php"), "w", encoding="utf-8") as f:
        f.write("<?php ?>")
    jenis = {t[0] for t in cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0]}
    cek({"BERUBAH", "SPAM", "ASING"} <= jenis, "cek integritas harus menemukan halaman diubah, spam, dan berkas asing: %r" % jenis)
    bangun_semua()
    cek(not ada("s1politik/shell.php"), "bangun ulang penuh harus menghapus berkas asing")
    cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "bangun ulang memulihkan situs")

    # --- one programme only, slug change, inactive programme
    lokasi.tulis("prodi/67201/situs", {"tagline": "Tagline baru"}, "penguji", "uji", "uji")
    sebelum = os.path.getmtime(os.path.join(lokasi.publik(), "s1informatika", "index.html"))
    bangun_semua(kode="67201")
    cek("Tagline baru" in baca_halaman("s1politik/index.html"), "bangun satu prodi harus menerapkan perubahannya")
    cek(os.path.getmtime(os.path.join(lokasi.publik(), "s1informatika", "index.html")) == sebelum, "prodi lain tidak boleh disentuh")
    cek(ada("profesidokter/index.html"), "bangun satu prodi tidak boleh menghapus prodi lain")
    try:
        bangun_semua(kode="99999")
        gagal.append("bangun prodi yang tidak ada harus gagal")
    except bangun.GagalBangun:
        pass
    registri.ganti_slug("55201", "s1ti", "penguji")
    bangun_semua()
    cek(ada("s1ti/index.html") and not ada("s1informatika/index.html"), "slug baru dibangun, slug lama dihapus")
    with io.open(os.path.join(lokasi.nginx_buatan(), "slug-lama.conf"), encoding="utf-8") as f:
        cek("rewrite ^/s1informatika(/.*)?$ /s1ti$1 permanent;" in f.read(), "slug lama harus dialihkan")
    registri.atur("11901", "penguji", aktif=False)
    bangun_semua()
    cek(not ada("profesidokter/index.html"), "prodi nonaktif tidak boleh dibangun")
    cek("profesidokter" not in baca_halaman("index.html"), "prodi nonaktif tidak boleh di halaman akar")
    registri.atur("11901", "penguji", aktif=True)
    registri.atur("55201", "penguji", dosen_url="https://dosen.unsrat.ac.id/prodi/55201")
    registri.ganti_slug("55201", "s1informatika", "penguji")

    # --- production build
    b = bangun_semua(produksi=True)
    periksa_situs(lokasi.publik(), "produksi")
    beranda = baca_halaman("s1informatika/index.html")
    cek("noindex" not in beranda and "pita-staging" not in beranda, "produksi tanpa noindex dan pita")
    cek('<link rel="canonical" href="https://prodi.unsrat.ac.id/s1informatika/">' in beranda, "canonical produksi")
    cek('"url": "https://prodi.unsrat.ac.id/s1informatika/"' in beranda, "JSON-LD produksi memuat alamat")
    cek('href="https://dosen.unsrat.ac.id/prodi/55201"' in baca_halaman("s1informatika/dosen/dosen-tetap/index.html"),
        "tautan dosen dari registri harus dipakai")
    with io.open(os.path.join(lokasi.publik(), "sitemap.xml"), encoding="utf-8") as f:
        peta = f.read()
    halaman_situs = sum(1 for _f, _d, nama in os.walk(lokasi.publik()) for x in nama if x.endswith(".html")) - 1  # minus 404
    cek(peta.count("<loc>") == halaman_situs, "sitemap harus memuat semua halaman (%d, ada %d)" % (halaman_situs, peta.count("<loc>")))
    cek("<loc>https://prodi.unsrat.ac.id/s1informatika/profil/sejarah/</loc>" in peta, "sitemap memuat halaman dalam")
    with io.open(os.path.join(lokasi.publik(), "robots.txt"), encoding="utf-8") as f:
        cek("Sitemap: https://prodi.unsrat.ac.id/sitemap.xml" in f.read(), "robots produksi menunjuk sitemap")
    bangun_semua()
    cek(not ada("sitemap.xml"), "kembali ke staging menghapus sitemap")

    # --- the real programmes from www
    if os.path.isfile(os.path.join(WWW_ASLI, "prodi.json")):
        for nama in ("PRODI_DATA", "PRODI_PUBLIK"):
            os.environ[nama] = os.path.join(KERJA, "asli-" + nama.lower())
        os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "asli-manifes.json")
        tarik_www.terapkan("penguji", WWW_ASLI)
        registri.siapkan_dari_csv("penguji")
        b = bangun_semua()
        cek(not b.peringatan, "bangun data asli tanpa peringatan: %r" % b.peringatan[:3])
        n = periksa_situs(lokasi.publik(), "asli")
        cek(n == 97 * halaman_per_prodi + 2, "data asli: %d halaman, harus %d" % (n, 97 * halaman_per_prodi + 2))
        cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "data asli: cek integritas bersih")
        print("data www asli: 97 prodi, %d halaman diperiksa" % n)
    else:
        print("data www asli tidak ditemukan, bagian itu dilewati")
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_bangun: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
