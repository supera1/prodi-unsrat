# -*- coding: utf-8 -*-
"""Build the static programme sites into PRODI_PUBLIK (rencana Fase 1 §7).

    python3 platform/bangun/bangun.py                  every active programme + the root pages (staging)
    python3 platform/bangun/bangun.py --prodi 55201    one programme (by PDDIKTI code) + the root pages
    python3 platform/bangun/bangun.py --produksi       production form (also: PRODI_MODE=produksi)

Inputs: warisan/* (official data from www, tarik_www.py) with each programme's own changes (prodi/<kode>/data.json,
data_prodi.py), registri.json and prodi/<kode>/situs.json (lokasi.py),
platform/template/menu.json, platform/data-awal/palet.json, and the templates and assets in platform/template/.

Output (PRODI_PUBLIK, the only folder the web server serves):

    index.html, 404.html, robots.txt, sitemap.xml (production only)
    aset/...                         shared style sheets and pictures
    <slug>/index.html                programme home page
    <slug>/<group>/[<page>/]index.html
    <slug>/warna.css                 the programme's colours (custom properties only)
    <slug>/pengumuman/               announcements and news (pengumuman.py): list pages (/halaman/<n>/), one page per
                                     item (/<id>/), per category (/kategori/<id>/), per year (/arsip/<yyyy>/), rss.xml
    unggahan/<kode>/...              uploaded photos and PDFs of published items and pages (PRODI_PENYIMPANAN=lokal only)

plus PRODI_MANIFES (SHA-256 of every published file, for pemantau/cek_integritas.py) and
PRODI_NGINX/slug-lama.conf (301 redirects of old slugs, included by Nginx).

Modes, as in www (ADR A-16 there): staging (default) adds a strip and <meta name="robots" content="noindex">, and
robots.txt forbids every crawler; production drops both, adds <link rel="canonical"> with the full address
(PRODI_ALAMAT, default https://prodi.unsrat.ac.id) and writes sitemap.xml.

Every link is relative to the page, so the sites also work under a path (a load balancer serving /beta/), except
404.html, which Nginx serves at any depth and therefore links from the site root.
"""
from __future__ import print_function

import argparse
import datetime
import email.utils
import hashlib
import io
import json
import os
import posixpath
import re
import sys
from xml.sax.saxutils import escape as xml_escape

BANGUN = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.dirname(BANGUN)
TEMPLATE = os.path.join(PLATFORM, "template")
sys.path.insert(0, PLATFORM)
sys.path.insert(0, BANGUN)

from jinja2 import Environment, FileSystemLoader, StrictUndefined  # noqa: E402
from markupsafe import Markup, escape  # noqa: E402

import data_prodi  # noqa: E402
import isi_halaman  # noqa: E402
import kriteria as kriteria_mod  # noqa: E402
import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import media  # noqa: E402
import pengumuman as pengumuman_mod  # noqa: E402
import registri  # noqa: E402
import tampilan_prodi  # noqa: E402
import warna as warna_mod  # noqa: E402
from slug import POLA_SLUG  # noqa: E402

ALAMAT_BAWAAN = "https://prodi.unsrat.ac.id"
WWW = "https://www.unsrat.ac.id"
# Pages of www the sites link to, by their path in www's data (website-unsrat-2026), and where the www that is live
# today has them: the new www is not live yet, and the current one answers 404 at kalender-akademik.html and
# pengumuman.html (pre-production audit, 27 October 2026). Empty this table when the new www goes live.
WWW_SEKARANG = {"kalender-akademik.html": "kalender-akademik/", "pengumuman.html": "category/pengumuman/"}
DOSEN_UMUM = "https://dosen.unsrat.ac.id"

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://storage.googleapis.com; "
       "frame-src 'self' https://storage.googleapis.com; connect-src 'self'; object-src 'none'; base-uri 'self'; "
       "form-action 'self'")
FONT = ("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400..800;1,400..700"
        "&display=swap")

JENJANG_PANJANG = registri.JENJANG_PANJANG
# sections of the root page, in this order
KELOMPOK_JENJANG = (("sarjana", "Sarjana (S1)", ("S1",)), ("magister", "Magister (S2)", ("S2",)),
                    ("doktor", "Doktor (S3)", ("S3",)), ("profesi", "Profesi", ("Profesi",)),
                    ("spesialis", "Spesialis dan Subspesialis", ("Sp-1", "Sp-2")))
BULAN = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember")
BERKAS_AKAR = ("index.html", "404.html", "robots.txt", "sitemap.xml")
MD_TAUTAN = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\s]{1,500})\)")
URL_ISI = re.compile(r"https://[^\s<>\"']+")
PER_HALAMAN = 12          # items per list page of announcements
DI_BERANDA = 3            # newest announcements on a programme's home page, besides the pinned ones
TERKAIT = 5               # items under "Kabar terkait" on an accreditation page
WITA = datetime.timezone(datetime.timedelta(hours=8))


class GagalBangun(Exception):
    pass


# ------------------------------------------------------------------ small helpers used by the templates

nama_tampil = registri.nama_tampil


def tanggal(iso):
    """'2030-08-15' -> '15 Agustus 2030' ('' for anything else)."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    if not m or not 1 <= int(m.group(2)) <= 12:
        return ""
    return "%d %s %s" % (int(m.group(3)), BULAN[int(m.group(2)) - 1], m.group(1))


def alamat_www(jalur):
    """The address of a page of www from its path in www's data (see WWW_SEKARANG)."""
    jalur = jalur.lstrip("/")
    return "%s/%s" % (WWW, WWW_SEKARANG.get(jalur, jalur))


def tautan_md(teks):
    """Escape text from www and turn its [label](address) links into links; a relative address points into www."""
    hasil, awal = [], 0
    for m in MD_TAUTAN.finditer(teks or ""):
        hasil.append(escape(teks[awal:m.start()]))
        href = m.group(2)
        if not href.startswith("https://"):
            href = None if (":" in href.split("/")[0] or href.startswith("//")) else alamat_www(href)
        hasil.append(Markup('<a href="%s">%s</a>') % (href, m.group(1)) if href else escape(m.group(1)))
        awal = m.end()
    hasil.append(escape((teks or "")[awal:]))
    return Markup("").join(hasil)


def _tautkan(teks):
    """Escape a line of text and turn its https:// addresses into links (trailing punctuation stays text)."""
    hasil, awal = [], 0
    for m in URL_ISI.finditer(teks):
        url = m.group(0).rstrip(".,;:!?)")
        hasil.append(escape(teks[awal:m.start()]))
        hasil.append(Markup('<a href="%s">%s</a>') % (url, url))
        awal = m.start() + len(url)
    hasil.append(escape(teks[awal:]))
    return Markup("").join(hasil)


def teks_isi(teks):
    """The body of an announcement: paragraphs (separated by an empty line) and "- " lists; never raw HTML."""
    blok = []
    for bagian in re.split(r"\n\s*\n", (teks or "").strip()):
        baris = [b.strip() for b in bagian.splitlines() if b.strip()]
        if not baris:
            continue
        if all(b.startswith("- ") for b in baris):
            blok.append(Markup("<ul>%s</ul>") % Markup("").join(Markup("<li>%s</li>") % _tautkan(b[2:]) for b in baris))
        else:
            blok.append(Markup("<p>%s</p>") % Markup("<br>").join(_tautkan(b) for b in baris))
    return Markup("\n").join(blok)


def foto_varian(f, lebar=None):
    """A stored size of a photo: the one made for `lebar` if there is one, else the largest one not wider than it,
    else the smallest (lebar=None: the largest)."""
    v = sorted(f["varian"].values(), key=lambda r: r["lebar"])
    if lebar is None:
        return v[-1]
    if str(lebar) in f["varian"]:
        return f["varian"][str(lebar)]
    cocok = [r for r in v if r["lebar"] <= lebar]
    return cocok[-1] if cocok else v[0]


def ukuran(n):
    """1234567 -> '1,2 MB'."""
    if n >= 1024 * 1024:
        return ("%.1f MB" % (n / 1024.0 / 1024.0)).replace(".", ",")
    return "%d KB" % max(1, round(n / 1024.0))


def json_ld(isi):
    """A JSON-LD block that cannot end the <script> element early."""
    teks = json.dumps(isi, ensure_ascii=False, indent=1).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return Markup('<script type="application/ld+json">\n%s\n</script>' % teks)


def sha(isi):
    return hashlib.sha256(isi).hexdigest()


def lingkungan():
    """The Jinja2 environment of the site's page templates, with the site's filters."""
    env = Environment(loader=FileSystemLoader(os.path.join(TEMPLATE, "halaman")), autoescape=True,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters.update(tanggal=tanggal, tautan_md=tautan_md, json_ld=json_ld, teks_isi=teks_isi, ukuran=ukuran,
                       foto_varian=foto_varian, akreditasi=registri.label_akreditasi)
    env.globals.update(nama_tampil=nama_tampil, JENJANG_PANJANG=JENJANG_PANJANG, alamat_www=alamat_www,
                       NAMA_MEDIA_SOSIAL={k: v[0] for k, v in tampilan_prodi.MEDIA_SOSIAL.items()})
    return env


def bagian_html(bagian, media_url):
    """The sections of a programme's own page (isi_halaman.tampilan) as the site shows them, with the macros of
    _isi.html: the admin's preview."""
    return Markup(lingkungan().from_string('{% from "_isi.html" import bagian_isi with context %}'
                                           '{% for b in bagian %}{{ bagian_isi(b) }}{% endfor %}')
                  .render(bagian=bagian, media_url=media_url))


# ------------------------------------------------------------------ the builder

class Pembangun(object):
    def __init__(self, produksi=False, alamat=None, hari_ini=None):
        self.produksi = produksi
        self.hari_ini = hari_ini or datetime.date.today().isoformat()
        self.alamat = (alamat or os.environ.get("PRODI_ALAMAT") or ALAMAT_BAWAAN).rstrip("/")
        warisan = lokasi.baca("warisan/prodi")
        if not warisan:
            raise GagalBangun("data resmi belum ada: jalankan dulu platform/tarik_www.py --terapkan")
        self.tampil_berlaku = bool(warisan.get("tampilkan_berlaku_hingga"))
        # www's data with each programme's own changes put over it (data_prodi.py, K-P16)
        self.prodi = data_prodi.semua_efektif()
        self.unit = {u["kode"]: u for u in (lokasi.baca("warisan/unit") or {}).get("unit", [])}
        self.kalender = lokasi.baca("warisan/kalender") or {}
        self.univ = lokasi.baca("warisan/universitas") or {}
        self.registri = (lokasi.baca("registri") or {}).get("prodi", [])
        self.templat = menu_mod.baca_templat()
        self.palet = warna_mod.baca_palet()
        self.kategori = pengumuman_mod.baca_kategori()
        self.label_kategori = {k["id"]: k["label"] for k in self.kategori}
        self.env = lingkungan()
        self.berkas = {}      # published path -> bytes
        self.versi = {}       # published asset path -> short hash, for ?v=
        self.peringatan = []
        # accreditation criteria labels: only bodies LPMPP confirmed are shown (K-P29); a broken file shows none
        try:
            self.kriteria = kriteria_mod.baca()
            masalah = kriteria_mod.periksa(self.kriteria, set(isi_halaman.TEMPLAT))
        except (OSError, ValueError) as e:
            masalah = [str(e)]
        if masalah:
            self.peringatan.append("label kriteria akreditasi diabaikan: %s" % "; ".join(masalah[:3]))
            self.kriteria = None

    # -------------------------------------------------------------- which programmes

    def aktif(self):
        """Registry entries that get a site: active, with a valid slug and official data."""
        hasil = []
        for r in self.registri:
            if not r.get("aktif"):
                continue
            if not POLA_SLUG.match(r.get("slug") or ""):
                self.peringatan.append("prodi %s: slug %r tidak sah, dilewati" % (r["kode_pddikti"], r.get("slug")))
            elif r["kode_pddikti"] not in self.prodi:
                self.peringatan.append("prodi %s terdaftar tetapi tidak ada di data resmi, dilewati" % r["kode_pddikti"])
            else:
                hasil.append(r)
        return hasil

    # -------------------------------------------------------------- paths and links

    @staticmethod
    def jalur_halaman(slug, alamat):
        return posixpath.join(slug, alamat, "index.html") if alamat else posixpath.join(slug, "index.html")

    def penaut(self, berkas_ini, mutlak=False):
        """(ke, aset) link functions for the page published at `berkas_ini`."""
        folder = posixpath.dirname(berkas_ini) or "."

        def ke(tujuan):
            """Link to a folder ('' = site root, 's1informatika/profil') or a file ('aset/x.css')."""
            if mutlak:
                return "/" + (tujuan + "/" if tujuan and "." not in posixpath.basename(tujuan) else tujuan)
            rel = posixpath.relpath(tujuan or ".", folder)
            if "." in posixpath.basename(tujuan or ""):
                return rel
            return "./" if rel == "." else rel + "/"

        def aset(jalur):
            return "%s?v=%s" % (ke(jalur), self.versi[jalur])

        return ke, aset

    def kanonik(self, jalur_folder):
        return "%s/%s" % (self.alamat, jalur_folder + "/" if jalur_folder else "") if self.produksi else ""

    # -------------------------------------------------------------- output

    def simpan(self, jalur, isi):
        self.berkas[jalur] = isi.encode("utf-8") if isinstance(isi, str) else isi

    def aset_statis(self):
        akar = os.path.join(TEMPLATE, "aset")
        for folder, _d, nama in os.walk(akar):
            for n in sorted(nama):
                if n.startswith("."):
                    continue
                path = os.path.join(folder, n)
                rel = "aset/" + os.path.relpath(path, akar).replace(os.sep, "/")
                with open(path, "rb") as f:
                    self.simpan(rel, f.read())
        unsrat = [p for p in self.palet if p["id"] == warna_mod.CADANGAN][0]
        self.simpan("aset/css/warna-unsrat.css", warna_mod.css(dict(warna_mod.turunan(unsrat["utama"], unsrat["aksen"]),
                                                                    keterangan=unsrat["nama"])))
        for jalur, isi in self.berkas.items():
            if jalur.startswith("aset/"):
                self.versi[jalur] = sha(isi)[:10]

    def render(self, templat, jalur, **konteks):
        mutlak = konteks.pop("mutlak", False)
        ke, aset = self.penaut(jalur, mutlak)
        def media_url(rekam):
            return rekam["url"] if "url" in rekam else ke("unggahan/" + rekam["jalur"])

        konteks.setdefault("sub", False)
        konteks.update(ke=ke, aset=aset, media_url=media_url, media_mutlak=self.media_mutlak, alamat=self.alamat,
                       produksi=self.produksi, csp=CSP, font=FONT, univ=self.univ, www=WWW,
                       tahun=self.univ.get("identitas", {}).get("tahun_hak_cipta") or str(datetime.date.today().year))
        self.simpan(jalur, self.env.get_template(templat).render(**konteks))

    def media_mutlak(self, rekam):
        """Full address of a stored file (link previews, RSS)."""
        return rekam["url"] if "url" in rekam else "%s/unggahan/%s" % (self.alamat, rekam["jalur"])

    # -------------------------------------------------------------- one programme

    def situs(self, kode):
        return lokasi.baca("prodi/%s/situs" % kode) or {}

    def menu_prodi(self, kode):
        try:
            return menu_mod.susun(self.templat, self.situs(kode).get("menu"))
        except menu_mod.GagalMenu as e:
            self.peringatan.append("prodi %s: pengaturan menu diabaikan (%s)" % (kode, e))
            return menu_mod.susun(self.templat)

    def bangun_prodi(self, r):
        kode, slug = r["kode_pddikti"], r["slug"]
        p = self.prodi[kode]
        situs = self.situs(kode)
        unit = self.unit.get(p["unit_kode"], {"nama": p["unit"]})
        w = warna_mod.warna_prodi(situs.get("palet"), unit.get("bendera"), self.palet)
        if situs.get("palet") not in (None, warna_mod.BAWAAN, w["palet"]):
            self.peringatan.append("prodi %s: %s" % (kode, w["keterangan"]))
        hero = self.hero_prodi(kode, p, unit, situs, w)
        logo, media_sosial = self.identitas_prodi(kode, situs)

        def url_foto(rekam):      # from <slug>/warna.css
            return rekam["url"] if "url" in rekam else posixpath.relpath("unggahan/" + rekam["jalur"], slug)
        warna_css = posixpath.join(slug, "warna.css")
        self.simpan(warna_css, warna_mod.css(w) + tampilan_prodi.css(hero["latar"], w, url_foto))
        self.versi[warna_css] = sha(self.berkas[warna_css])[:10]
        menu = self.menu_prodi(kode)
        tagline = (situs.get("tagline") or "").strip()
        kabar = self.pengumuman_prodi(kode)
        berlaku = [b for b in kabar if pengumuman_mod.masih_berlaku(b, self.hari_ini)]
        di_beranda = [b for b in berlaku if b.get("sematkan")] + [b for b in berlaku if not b.get("sematkan")][:DI_BERANDA]
        terkait = {}
        for k in self.kategori:
            isi = [b for b in kabar if b["kategori"] == k["id"]]
            for halaman_id in k["halaman"]:
                if isi:
                    terkait.setdefault(halaman_id, []).append({"kategori": k, "butir": isi[:TERKAIT], "jumlah": len(isi)})
        lembaga = kriteria_mod.lembaga_untuk(self.kriteria, p.get("lembaga_akreditasi"))
        urut = [b["id"] for b in menu_mod.halaman(menu)]             # the pages this site has, in menu order
        ada = {b["id"]: b for b in menu_mod.halaman(menu)}
        peta_kriteria = [{"nomor": n, "nama": nama, "halaman": [ada[x] for x in sorted(ids, key=urut.index)]}
                         for n, nama, ids in kriteria_mod.peta(lembaga, set(ada))]
        umum = dict(p=p, r=r, slug=slug, situs=situs, tagline=tagline, unit=unit, menu=menu,
                    nama=nama_tampil(p), warna_css=warna_css, tampil_berlaku=self.tampil_berlaku,
                    dosen_url=r.get("dosen_url") or "", dosen_umum=DOSEN_UMUM, kalender=self.kalender,
                    kurikulum=sorted({c["kurikulum"] for c in p.get("cpl", []) if c.get("kurikulum")}),
                    kabar_beranda=di_beranda, terkait=terkait, label_kategori=self.label_kategori, hero=hero,
                    logo=logo, media_sosial=media_sosial, lembaga_kriteria=lembaga, peta_kriteria=peta_kriteria,
                    hari_ini=self.hari_ini)
        for e in menu:
            for ini in [e] + e.get("anak", []):
                kelompok = e if e["kelompok"] and ini is not e else None
                if ini["templat"] == "pengumuman":
                    self.bangun_pengumuman(slug, ini, kabar, umum)
                    continue
                if ini["kelompok"]:
                    templat = "kelompok.html"
                elif ini["templat"]:
                    templat = ini["templat"] + ".html"
                else:
                    templat = "isi.html"
                folder = posixpath.join(slug, ini["alamat"]) if ini["alamat"] else slug
                konteks = dict(umum, ini=ini, kelompok=kelompok, kanonik=self.kanonik(folder))
                konteks["label_kriteria"] = kriteria_mod.label(lembaga, ini["id"])
                if templat == "isi.html" or ini["id"] in isi_halaman.TEMPLAT:
                    konteks["isi_bagian"] = self.isi_halaman_prodi(kode, ini["id"])
                if ini["alamat"] == "":
                    konteks["json_ld"] = self.json_ld_prodi(p, unit, folder)
                    if hero["latar"]["jenis"] == "foto":
                        konteks["og_gambar"] = self.media_mutlak(hero["latar"]["foto"]["varian"]["1600"])
                self.render(templat, self.jalur_halaman(slug, ini["alamat"]), **konteks)

    def isi_halaman_prodi(self, kode, id_halaman):
        """The sections of a programme's own page (isi_halaman.py, Fase 2), or None while it has no content to show:
        the page then says the programme is still filling it. Content that fails the checks is not shown at all."""
        if id_halaman not in isi_halaman.TEMPLAT:
            return None
        isi = isi_halaman.terbit(kode, id_halaman)
        if isi is None:
            return None
        if self.produksi and isi_halaman.bertanda_contoh(isi):
            self.peringatan.append("prodi %s: isi halaman %s bertanda %s, tidak diterbitkan di produksi"
                                   % (kode, id_halaman, isi_halaman.CONTOH))
            return None
        masalah = isi_halaman.periksa(id_halaman, isi, kode)
        if masalah:
            self.peringatan.append("prodi %s: isi halaman %s diabaikan (%s)" % (kode, id_halaman, "; ".join(masalah[:3])))
            return None
        bagian, hilang = isi_halaman.tampilan(id_halaman, isi, self.terbitkan_media)
        if hilang:
            self.peringatan.append("prodi %s: halaman %s: %d berkas tidak ditemukan, dilewati" % (kode, id_halaman, hilang))
        return bagian or None

    def identitas_prodi(self, kode, situs):
        """(logo, social media) of a programme, each only when its settings pass the checks."""
        logo = situs.get("logo")
        if logo is not None:
            masalah = tampilan_prodi.periksa_identitas({"logo": logo})
            if masalah or not all(self.terbitkan_media(v) for v in logo["varian"].values()):
                self.peringatan.append("prodi %s: logo diabaikan (%s)" % (kode, "; ".join(masalah) or "berkasnya tidak ada"))
                logo = None
        media_sosial = situs.get("media_sosial") or []
        masalah = tampilan_prodi.periksa_identitas({"media_sosial": media_sosial})
        if masalah:
            self.peringatan.append("prodi %s: media sosial diabaikan (%s)" % (kode, "; ".join(masalah)))
            media_sosial = []
        return logo, media_sosial

    def hero_prodi(self, kode, p, unit, situs, w):
        """The front section of the home page: the admin's settings over the defaults from the official data."""
        bawaan, resmi = tampilan_prodi.bawaan_dan_resmi(p, unit["nama"])
        try:
            hero = tampilan_prodi.susun(bawaan, resmi, situs, w)
        except tampilan_prodi.GagalTampilan as e:
            self.peringatan.append("prodi %s: pengaturan beranda diabaikan (%s)" % (kode, e))
            return tampilan_prodi.susun(bawaan, resmi, {}, w)
        if hero["latar"]["jenis"] == "foto" and not all(
                self.terbitkan_media(v) for v in hero["latar"]["foto"]["varian"].values()):
            self.peringatan.append("prodi %s: foto latar beranda tidak ditemukan, dipakai latar bawaan" % kode)
            hero["latar"] = {"jenis": "pucat"}
        return hero

    def pengumuman_prodi(self, kode):
        """Published announcements of a programme whose files are all there (local files are published here)."""
        hasil = []
        for b in pengumuman_mod.terbit(pengumuman_mod.baca(kode)):
            if self.produksi and isi_halaman.bertanda_contoh(b):
                self.peringatan.append("prodi %s: pengumuman %s bertanda %s, tidak diterbitkan di produksi"
                                       % (kode, b["id"], isi_halaman.CONTOH))
                continue
            rekam = [v for f in b.get("foto", []) for v in f["varian"].values()] + list(b.get("pdf", []))
            if all(self.terbitkan_media(r) for r in rekam):
                hasil.append(b)
            else:
                self.peringatan.append("prodi %s: pengumuman %s dilewati, berkasnya tidak ada" % (kode, b["id"]))
        return hasil

    def terbitkan_media(self, rekam):
        if "url" in rekam:
            return media.url_sah(rekam["url"])
        jalur = rekam.get("jalur")
        path = os.path.join(lokasi.unggahan(), *jalur.split("/")) if media.jalur_sah(jalur) else None
        if not path or not os.path.isfile(path):
            return False
        if "unggahan/" + jalur not in self.berkas:
            with open(path, "rb") as f:
                self.simpan("unggahan/" + jalur, f.read())
        return True

    def bangun_pengumuman(self, slug, ini, kabar, umum):
        """List pages, one page per item, category and year archives, and the RSS feed."""
        dasar = ini["alamat"]
        kategori_ada = [dict(k, jumlah=sum(1 for b in kabar if b["kategori"] == k["id"])) for k in self.kategori]
        kategori_ada = [k for k in kategori_ada if k["jumlah"]]
        tahun_ada = sorted({b["tanggal"][:4] for b in kabar}, reverse=True)
        bersama = dict(umum, ini=ini, kelompok=None, kategori_ada=kategori_ada, tahun_ada=tahun_ada,
                       dasar_pengumuman=dasar)
        self.daftar_berhalaman(slug, dasar, kabar, dict(bersama, saring=None))
        for k in kategori_ada:
            self.daftar_berhalaman(slug, "%s/kategori/%s" % (dasar, k["id"]),
                                   [b for b in kabar if b["kategori"] == k["id"]],
                                   dict(bersama, saring={"jenis": "kategori", "id": k["id"], "label": k["label"]}))
        for t in tahun_ada:
            self.daftar_berhalaman(slug, "%s/arsip/%s" % (dasar, t), [b for b in kabar if b["tanggal"][:4] == t],
                                   dict(bersama, saring={"jenis": "tahun", "id": t, "label": "Arsip %s" % t}))
        for b in kabar:
            folder = posixpath.join(slug, dasar, b["id"])
            lain = [x for x in kabar if x["id"] != b["id"]][:3]
            foto = b.get("foto", [])
            og = self.media_mutlak(foto_varian(foto[0])) if foto else None
            self.render("pengumuman_detail.html", posixpath.join(folder, "index.html"),
                        **dict(bersama, b=b, lain=lain, sub=True, kanonik=self.kanonik(folder), og_gambar=og,
                               og_jenis="article"))
        self.simpan(posixpath.join(slug, dasar, "rss.xml"), self.rss(slug, dasar, kabar, umum["nama"]))

    def daftar_berhalaman(self, slug, dasar, butir, konteks):
        potong = [butir[i:i + PER_HALAMAN] for i in range(0, len(butir), PER_HALAMAN)] or [[]]
        for nomor, isi in enumerate(potong, 1):
            alamat = dasar if nomor == 1 else "%s/halaman/%d" % (dasar, nomor)
            folder = posixpath.join(slug, alamat)
            self.render("pengumuman_daftar.html", posixpath.join(folder, "index.html"),
                        **dict(konteks, butir=isi, nomor=nomor, jumlah_halaman=len(potong), dasar_daftar=dasar,
                               sub=bool(konteks["saring"]) or nomor > 1, kanonik=self.kanonik(folder)))

    def rss(self, slug, dasar, kabar, nama):
        """RSS 2.0 of the newest 20 items, with full addresses (feeds need them, also on staging)."""
        situs = "%s/%s/%s/" % (self.alamat, slug, dasar)

        def x(t):
            return xml_escape(t or "")
        baris = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', "<channel>",
                 "<title>%s</title>" % x("Pengumuman %s — Universitas Sam Ratulangi" % nama),
                 "<link>%s</link>" % x(situs),
                 "<description>%s</description>" % x("Pengumuman, berita kegiatan, dan prestasi Program Studi %s." % nama),
                 "<language>id</language>",
                 '<atom:link href="%srss.xml" rel="self" type="application/rss+xml"/>' % x(situs)]
        for b in kabar[:20]:
            waktu = datetime.datetime.fromisoformat(b["tanggal"]).replace(tzinfo=WITA)
            alamat = "%s%s/" % (situs, b["id"])
            baris += ["<item>", "<title>%s</title>" % x(b["judul"]), "<link>%s</link>" % x(alamat),
                      '<guid isPermaLink="true">%s</guid>' % x(alamat),
                      "<pubDate>%s</pubDate>" % email.utils.format_datetime(waktu),
                      "<category>%s</category>" % x(self.label_kategori.get(b["kategori"], "")),
                      "<description>%s</description>" % x(b["ringkasan"]), "</item>"]
        return "\n".join(baris + ["</channel>", "</rss>"]) + "\n"

    def json_ld_prodi(self, p, unit, folder):
        isi = {"@context": "https://schema.org", "@type": "EducationalOccupationalProgram", "name": nama_tampil(p),
               "provider": {"@type": "CollegeOrUniversity", "name": "Universitas Sam Ratulangi", "url": WWW + "/"},
               "programType": JENJANG_PANJANG.get(p["jenjang"], p["jenjang"])}
        if p.get("nama_en"):
            isi["alternateName"] = p["nama_en"]
        if p.get("gelar"):
            isi["educationalCredentialAwarded"] = p["gelar"]
        if p.get("sks"):
            isi["numberOfCredits"] = p["sks"]
        if self.produksi:
            isi["url"] = "%s/%s/" % (self.alamat, folder)
        return isi

    # -------------------------------------------------------------- root pages

    def bangun_akar(self, aktif):
        daftar = sorted(aktif, key=lambda r: (self.prodi[r["kode_pddikti"]]["nama"], r["kode_pddikti"]))
        kelompok = []
        for id_, judul, jenjang in KELOMPOK_JENJANG:
            isi = [dict(r=r, p=self.prodi[r["kode_pddikti"]],
                        unit=self.unit.get(self.prodi[r["kode_pddikti"]]["unit_kode"], {}).get("nama")
                        or self.prodi[r["kode_pddikti"]]["unit"])
                   for r in daftar if self.prodi[r["kode_pddikti"]]["jenjang"] in jenjang]
            if isi:
                kelompok.append({"id": id_, "judul": judul, "prodi": isi})
        self.render("akar.html", "index.html", kelompok=kelompok, jumlah=len(daftar), kanonik=self.kanonik(""),
                    warna_css="aset/css/warna-unsrat.css")
        self.render("404.html", "404.html", mutlak=True, kanonik="", warna_css="aset/css/warna-unsrat.css")
        if self.produksi:
            self.simpan("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % self.alamat)
        else:
            self.simpan("robots.txt", "# Staging: tidak untuk diindeks.\nUser-agent: *\nDisallow: /\n")

    def peta_situs(self):
        """sitemap.xml of every page now in PRODI_PUBLIK (also those a one-programme build did not touch)."""
        akar, alamat = lokasi.publik(), []
        for folder, _d, nama in os.walk(akar):
            if "index.html" in nama:
                rel = os.path.relpath(folder, akar).replace(os.sep, "/")
                alamat.append("%s/%s" % (self.alamat, "" if rel == "." else rel + "/"))
        alamat.sort(key=lambda a: (a.count("/"), a))
        baris = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        baris += ["<url><loc>%s</loc></url>" % xml_escape(a) for a in alamat]
        return "\n".join(baris + ["</urlset>"]) + "\n"

    def konfigurasi_redirect(self, aktif):
        """Nginx rewrites of old slugs to the current one (K-P1); the path under the slug is kept."""
        baris = ["# Dibuat oleh platform/bangun/bangun.py (%s). Jangan diubah tangan." % datetime.date.today().isoformat(),
                 "# Slug lama prodi dialihkan permanen ke slug sekarang."]
        for r in sorted(aktif, key=lambda r: r["slug"]):
            for lama in r.get("slug_lama", []):
                if POLA_SLUG.match(lama) and POLA_SLUG.match(r["slug"]):
                    baris.append("rewrite ^/%s(/.*)?$ /%s$1 permanent;" % (lama, r["slug"]))
        return "\n".join(baris) + "\n"

    # -------------------------------------------------------------- the whole build

    def bangun(self, kode=None):
        """Build everything, or one programme (plus the root pages). Returns (written, removed, scope)."""
        aktif = self.aktif()
        self.aset_statis()
        if kode is None:
            sasaran = aktif
            cakupan = None
        else:
            sasaran = [r for r in aktif if r["kode_pddikti"] == kode]
            if not sasaran:
                raise GagalBangun("prodi %s tidak aktif atau tidak terdaftar" % kode)
            cakupan = [sasaran[0]["slug"] + "/", "unggahan/%s/" % kode, "aset/"] + list(BERKAS_AKAR)
        for r in sasaran:
            self.bangun_prodi(r)
        self.bangun_akar(aktif)
        # production: sitemap.xml is written below, once every page is in place, so it is not removed here
        hasil = tulis_keluaran(self.berkas, cakupan, tetap=("sitemap.xml",) if self.produksi else ())
        if self.produksi:
            _tulis_jika_beda(os.path.join(lokasi.publik(), "sitemap.xml"), self.peta_situs().encode("utf-8"))
        tulis_manifes()
        os.makedirs(lokasi.nginx_buatan(), exist_ok=True)
        _tulis_jika_beda(os.path.join(lokasi.nginx_buatan(), "slug-lama.conf"),
                         self.konfigurasi_redirect(aktif).encode("utf-8"))
        return hasil


# ------------------------------------------------------------------ writing PRODI_PUBLIK

def _tulis_jika_beda(path, isi):
    if os.path.isfile(path):
        with open(path, "rb") as f:
            if f.read() == isi:
                return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(isi)
    os.replace(tmp, path)
    return True


def _dalam_cakupan(rel, cakupan):
    return cakupan is None or any(rel == c or (c.endswith("/") and rel.startswith(c)) for c in cakupan)


def tulis_keluaran(berkas, cakupan=None, tetap=()):
    """Write the built files that changed and remove files in scope that the build no longer makes.
    cakupan: None (the whole site) or a list of published paths and folder prefixes ending in "/".
    tetap: published paths never removed here (written separately)."""
    akar = lokasi.publik()
    ditulis = sum(1 for rel, isi in sorted(berkas.items()) if _tulis_jika_beda(os.path.join(akar, *rel.split("/")), isi))
    dihapus = 0
    for folder, _d, nama in os.walk(akar, topdown=False):
        for n in nama:
            path = os.path.join(folder, n)
            rel = os.path.relpath(path, akar).replace(os.sep, "/")
            if rel not in berkas and rel not in tetap and _dalam_cakupan(rel, cakupan):
                os.remove(path)
                dihapus += 1
        if folder != akar and not os.listdir(folder):
            os.rmdir(folder)
    return ditulis, dihapus, "semua" if cakupan is None else cakupan[0].rstrip("/")


def tulis_manifes():
    """SHA-256 of every file in PRODI_PUBLIK, in the format pemantau/cek_integritas.py reads."""
    akar, isi = lokasi.publik(), {}
    for folder, _d, nama in os.walk(akar):
        for n in nama:
            path = os.path.join(folder, n)
            with open(path, "rb") as f:
                isi[os.path.relpath(path, akar).replace(os.sep, "/")] = sha(f.read())
    data = {"dibuat": datetime.datetime.now().isoformat(timespec="seconds"), "berkas": dict(sorted(isi.items()))}
    lokasi.tulis_json(lokasi.manifes(), data)
    return len(isi)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bangun situs statis program studi")
    ap.add_argument("--prodi", help="kode PDDIKTI satu prodi (bawaan: semua)")
    ap.add_argument("--produksi", action="store_true", help="bentuk produksi (juga PRODI_MODE=produksi)")
    a = ap.parse_args(argv)
    produksi = a.produksi or os.environ.get("PRODI_MODE") == "produksi"
    # a scheduled daily rebuild (langkah 7) takes expired announcements off the home pages
    try:
        b = Pembangun(produksi=produksi)
        ditulis, dihapus, cakupan = b.bangun(a.prodi)
    except (GagalBangun, menu_mod.GagalMenu) as e:
        print("Bangun GAGAL: %s" % e)
        return 1
    for p in b.peringatan:
        print("PERINGATAN %s" % p)
    print("Bangun %s (%s): %d berkas ditulis, %d dihapus, %d halaman di %s" % (
        cakupan, "produksi" if produksi else "staging", ditulis, dihapus,
        sum(1 for k in b.berkas if k.endswith(".html")), lokasi.publik()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
