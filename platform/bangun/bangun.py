# -*- coding: utf-8 -*-
"""Build the static programme sites into PRODI_PUBLIK (rencana Fase 1 §7).

    python3 platform/bangun/bangun.py                  every active programme + the root pages (staging)
    python3 platform/bangun/bangun.py --prodi 55201    one programme (by PDDIKTI code) + the root pages
    python3 platform/bangun/bangun.py --produksi       production form (also: PRODI_MODE=produksi)

Inputs: warisan/* (official data from www, tarik_www.py), registri.json and prodi/<kode>/situs.json (lokasi.py),
platform/template/menu.json, platform/data-awal/palet.json, and the templates and assets in platform/template/.

Output (PRODI_PUBLIK, the only folder the web server serves):

    index.html, 404.html, robots.txt, sitemap.xml (production only)
    aset/...                         shared style sheets and pictures
    <slug>/index.html                programme home page
    <slug>/<group>/[<page>/]index.html
    <slug>/warna.css                 the programme's colours (custom properties only)

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

import lokasi  # noqa: E402
import menu as menu_mod  # noqa: E402
import warna as warna_mod  # noqa: E402
from slug import POLA_SLUG  # noqa: E402

ALAMAT_BAWAAN = "https://prodi.unsrat.ac.id"
WWW = "https://www.unsrat.ac.id"
DOSEN_UMUM = "https://dosen.unsrat.ac.id"

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://storage.googleapis.com; "
       "connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'")
FONT = ("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400..800;1,400..700"
        "&display=swap")

JENJANG_PANJANG = {"S1": "Sarjana", "S2": "Magister", "S3": "Doktor", "Profesi": "Profesi", "Sp-1": "Spesialis",
                   "Sp-2": "Subspesialis"}
# sections of the root page, in this order
KELOMPOK_JENJANG = (("sarjana", "Sarjana (S1)", ("S1",)), ("magister", "Magister (S2)", ("S2",)),
                    ("doktor", "Doktor (S3)", ("S3",)), ("profesi", "Profesi", ("Profesi",)),
                    ("spesialis", "Spesialis dan Subspesialis", ("Sp-1", "Sp-2")))
BULAN = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember")
BERKAS_AKAR = ("index.html", "404.html", "robots.txt", "sitemap.xml")
MD_TAUTAN = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\s]{1,500})\)")


class GagalBangun(Exception):
    pass


# ------------------------------------------------------------------ small helpers used by the templates

def nama_tampil(p):
    """"S1 Teknik Informatika", "Profesi Dokter", "Sp-1 Ilmu Penyakit Mata"."""
    if p["jenjang"] == "Profesi":
        return p["nama"] if "profesi" in p["nama"].lower() else "Profesi " + p["nama"]
    return "%s %s" % (p["jenjang"], p["nama"])


def tanggal(iso):
    """'2030-08-15' -> '15 Agustus 2030' ('' for anything else)."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso or "")
    if not m or not 1 <= int(m.group(2)) <= 12:
        return ""
    return "%d %s %s" % (int(m.group(3)), BULAN[int(m.group(2)) - 1], m.group(1))


def tautan_md(teks):
    """Escape text from www and turn its [label](address) links into links; a relative address points into www."""
    hasil, awal = [], 0
    for m in MD_TAUTAN.finditer(teks or ""):
        hasil.append(escape(teks[awal:m.start()]))
        href = m.group(2)
        if not href.startswith("https://"):
            href = None if (":" in href.split("/")[0] or href.startswith("//")) else "%s/%s" % (WWW, href.lstrip("/"))
        hasil.append(Markup('<a href="%s">%s</a>') % (href, m.group(1)) if href else escape(m.group(1)))
        awal = m.end()
    hasil.append(escape((teks or "")[awal:]))
    return Markup("").join(hasil)


def json_ld(isi):
    """A JSON-LD block that cannot end the <script> element early."""
    teks = json.dumps(isi, ensure_ascii=False, indent=1).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return Markup('<script type="application/ld+json">\n%s\n</script>' % teks)


def sha(isi):
    return hashlib.sha256(isi).hexdigest()


# ------------------------------------------------------------------ the builder

class Pembangun(object):
    def __init__(self, produksi=False, alamat=None):
        self.produksi = produksi
        self.alamat = (alamat or os.environ.get("PRODI_ALAMAT") or ALAMAT_BAWAAN).rstrip("/")
        warisan = lokasi.baca("warisan/prodi")
        if not warisan:
            raise GagalBangun("data resmi belum ada: jalankan dulu platform/tarik_www.py --terapkan")
        self.tampil_berlaku = bool(warisan.get("tampilkan_berlaku_hingga"))
        self.prodi = {p["kode_pddikti"]: p for p in warisan["program"]}
        self.unit = {u["kode"]: u for u in (lokasi.baca("warisan/unit") or {}).get("unit", [])}
        self.kalender = lokasi.baca("warisan/kalender") or {}
        self.univ = lokasi.baca("warisan/universitas") or {}
        self.registri = (lokasi.baca("registri") or {}).get("prodi", [])
        self.templat = menu_mod.baca_templat()
        self.palet = warna_mod.baca_palet()
        self.env = Environment(loader=FileSystemLoader(os.path.join(TEMPLATE, "halaman")), autoescape=True,
                               undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
        self.env.filters.update(tanggal=tanggal, tautan_md=tautan_md, json_ld=json_ld)
        self.env.globals.update(nama_tampil=nama_tampil, JENJANG_PANJANG=JENJANG_PANJANG)
        self.berkas = {}      # published path -> bytes
        self.versi = {}       # published asset path -> short hash, for ?v=
        self.peringatan = []

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
        konteks.update(ke=ke, aset=aset, produksi=self.produksi, csp=CSP, font=FONT, univ=self.univ, www=WWW,
                       tahun=self.univ.get("identitas", {}).get("tahun_hak_cipta") or str(datetime.date.today().year))
        self.simpan(jalur, self.env.get_template(templat).render(**konteks))

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
        warna_css = posixpath.join(slug, "warna.css")
        self.simpan(warna_css, warna_mod.css(w))
        self.versi[warna_css] = sha(self.berkas[warna_css])[:10]
        menu = self.menu_prodi(kode)
        tagline = (situs.get("tagline") or "").strip()
        umum = dict(p=p, r=r, slug=slug, situs=situs, tagline=tagline, unit=unit, menu=menu,
                    nama=nama_tampil(p), warna_css=warna_css, tampil_berlaku=self.tampil_berlaku,
                    dosen_url=r.get("dosen_url") or "", dosen_umum=DOSEN_UMUM, kalender=self.kalender,
                    kurikulum=sorted({c["kurikulum"] for c in p.get("cpl", []) if c.get("kurikulum")}))
        for e in menu:
            for ini in [e] + e.get("anak", []):
                kelompok = e if e["kelompok"] and ini is not e else None
                if ini["kelompok"]:
                    templat = "kelompok.html"
                elif ini["templat"]:
                    templat = ini["templat"] + ".html"
                else:
                    templat = "isi.html"
                folder = posixpath.join(slug, ini["alamat"]) if ini["alamat"] else slug
                konteks = dict(umum, ini=ini, kelompok=kelompok, kanonik=self.kanonik(folder))
                if ini["alamat"] == "":
                    konteks["json_ld"] = self.json_ld_prodi(p, unit, folder)
                self.render(templat, self.jalur_halaman(slug, ini["alamat"]), **konteks)

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
            self.simpan("sitemap.xml", self.peta_situs(aktif))
        else:
            self.simpan("robots.txt", "# Staging: tidak untuk diindeks.\nUser-agent: *\nDisallow: /\n")

    def peta_situs(self, aktif):
        alamat = [self.alamat + "/"]
        for r in sorted(aktif, key=lambda r: r["slug"]):
            for ini in menu_mod.halaman(self.menu_prodi(r["kode_pddikti"])):
                alamat.append("%s/%s/%s" % (self.alamat, r["slug"], ini["alamat"] + "/" if ini["alamat"] else ""))
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
            cakupan = [sasaran[0]["slug"] + "/", "aset/"] + list(BERKAS_AKAR)
        for r in sasaran:
            self.bangun_prodi(r)
        self.bangun_akar(aktif)
        hasil = tulis_keluaran(self.berkas, cakupan)
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


def tulis_keluaran(berkas, cakupan=None):
    """Write the built files that changed and remove files in scope that the build no longer makes.
    cakupan: None (the whole site) or a list of published paths and folder prefixes ending in "/"."""
    akar = lokasi.publik()
    ditulis = sum(1 for rel, isi in sorted(berkas.items()) if _tulis_jika_beda(os.path.join(akar, *rel.split("/")), isi))
    dihapus = 0
    for folder, _d, nama in os.walk(akar, topdown=False):
        for n in nama:
            path = os.path.join(folder, n)
            rel = os.path.relpath(path, akar).replace(os.sep, "/")
            if rel not in berkas and _dalam_cakupan(rel, cakupan):
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
