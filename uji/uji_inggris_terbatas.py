# -*- coding: utf-8 -*-
"""The English version only for the programmes the superadmin switched it on for (K-P38: the programmes in
international accreditation, because of DeepL's quota).

A programme whose switch is off (B, which had an English version before) has, for its admin and operators, no English
tab, column, card, form part, field, or machine translation button, and no "Terjemahkan semua"; its English routes
answer 404 (also in uji_admin.py); posting the old machine translation action spends nothing. Saving its forms the
way a browser does (no English fields) keeps every stored English value: the home section's English texts, the menu's
English labels, an extra page's English name, the criteria's English names, an announcement's English version. Its
site has no English version. A programme whose switch is on (A) has all of it. The superadmin's dashboard lists the
programmes with the English version; switching B on brings its English parts back with their stored values.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
import shutil
import sys
import tempfile
from html.parser import HTMLParser

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import flask  # noqa: F401
except ImportError:
    print("uji_inggris_terbatas: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-inggris-terbatas-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)
for v in ("TERJEMAH_PENYEDIA", "TERJEMAH_KUNCI", "TERJEMAH_BATAS_HARIAN", "TERJEMAH_BATAS_BULANAN"):
    os.environ.pop(v, None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import halaman_tambahan  # noqa: E402
import isi_halaman as ih  # noqa: E402
import kriteria as kriteria_mod  # noqa: E402
import lokasi  # noqa: E402
import pengumuman as pg  # noqa: E402
import registri  # noqa: E402
import tampilan_prodi as tp  # noqa: E402
import tarik_www  # noqa: E402
import terjemah_mesin as tm  # noqa: E402
from formulir_uji import prodi  # noqa: E402

A, B = "55201", "20201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


class AmbilFormulir(HTMLParser):
    """What a browser sends for the form posted to `aksi` (no button pressed; unchecked boxes and radios left out)."""

    def __init__(self, html, aksi):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.aksi, self.dalam, self.isian, self._area, self._pilih = aksi, False, [], None, None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self.dalam = a.get("action") == self.aksi
        if self.dalam and tag == "option" and self._pilih is not None:
            self._pilih[1] = a.get("value", "") if self._pilih[1] is None else self._pilih[1]
            if "selected" in a:
                self._pilih[2] = a.get("value", "")
            return
        if not self.dalam or not a.get("name"):
            return
        if tag == "input":
            jenis = a.get("type", "text")
            if jenis in ("checkbox", "radio"):
                if "checked" in a:
                    self.isian.append((a["name"], a.get("value", "on")))
            elif jenis not in ("file", "submit", "button"):
                self.isian.append((a["name"], a.get("value", "")))
        elif tag == "textarea":
            self._area = [a["name"], ""]
        elif tag == "select":
            self._pilih = [a["name"], None, None]

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if self._area is not None:
            self._area[1] += data

    def handle_endtag(self, tag):
        if tag == "form":
            self.dalam = False
        elif tag == "textarea" and self._area is not None:
            self.isian.append((self._area[0], self._area[1][1:] if self._area[1].startswith("\n") else self._area[1]))
            self._area = None
        elif tag == "select" and self._pilih is not None:
            nama, pertama, pilih = self._pilih
            self.isian.append((nama, pilih if pilih is not None else pertama))
            self._pilih = None


try:
    # ============================================================== two programmes; B had an English version before
    os.makedirs(os.environ["WWW_DATA"])
    for nama, isi_ in {"prodi": {"program": [dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering"),
                                             dict(prodi(B, "Teknik Elektro"), nama_en="Electrical Engineering")]},
                       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering",
                                          "jenis": "fakultas", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                       "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi_, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)
    registri.atur(A, "penguji", inggris=True)
    for k in (A, B):
        ih.terbitkan(k, "sejarah", {"uraian": "Prodi berdiri tahun 1990."}, "penguji")
        ih.terbitkan(k, "sejarah:en", {"teks": {"Prodi berdiri tahun 1990.": "Founded in 1990."},
                                       "asal": {"uraian": "Prodi berdiri tahun 1990."}}, "penguji")
        tp.atur(k, {"en": {"judul": "Engineering at UNSRAT"}, "menu": {"profil": {"label_en": "About us"}}}, "penguji")
        halaman_tambahan.tambah(k, "Video Profil", "profil", "", "penguji", label_en="Profile Video")
        kriteria_mod.simpan_prodi(k, {"nama": "LAM Teknik", "instrumen": "Instrumen LAM Teknik",
                                      "instrumen_en": "LAM Teknik Instrument",
                                      "kriteria": [{"nomor": "1", "nama": "Visi", "nama_en": "Vision"}],
                                      "halaman": {"sejarah": ["1"]}}, set(ih.TEMPLAT), "penguji", "uji")
    # B's English draft waiting for approval, from before its switch was turned off
    ih.ajukan(B, "sejarah:en", {"teks": {"Prodi berdiri tahun 1990.": "It was founded in 1990."},
                                "asal": {"uraian": "Prodi berdiri tahun 1990."}}, "penguji")
    K = {k: pg.tambah(k, {"judul": "Seminar nasional", "kategori": "kegiatan", "tanggal": "2026-11-10",
                          "ringkasan": "Seminar nasional bersama mitra.",
                          "en": {"judul": "National seminar", "ringkasan": "A national seminar with partners.",
                                 "asal": {}}}, "penguji", "draf") for k in (A, B)}

    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("admb", "admin", [B]), ("opb", "operator", [B])):
        akun_baru(nama, peran, p, super_)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron",
                            "TERJEMAH_PENYEDIA": "tiruan"})

    def klien(nama, ip):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = ip
        c.get("/masuk")
        with c.session_transaction() as s_:
            token = s_["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302,
            "%s masuk" % nama)
        return c
    ka, kb, ob, ks = klien("adma", "103.84.116.61"), klien("admb", "103.84.116.62"), klien("opb", "103.84.116.63"), \
        klien("superuji", "103.84.116.64")

    def kirim_formulir(c, halaman_, aksi, **ubah):
        """Post the form of a page the way a browser does, with some fields changed."""
        f = AmbilFormulir(c.get(halaman_).get_data(as_text=True), aksi)
        data = [(k, v) for k, v in f.isian if k not in ubah] + list(ubah.items())
        cek(f.isian, "formulir %s ada di %s" % (aksi, halaman_))
        return c.post(aksi, data=dict(data) if len({k for k, _v in data}) == len(data) else data)

    # ============================================================== B, switched off: nothing in English
    TANDA = ("lang=\"en\"", "Versi bahasa Inggris", "bahasa Inggris)", "Label Inggris", "Terjemahkan semua",
             "Terjemahkan dari versi Indonesia", "Terjemahan mesin", ">English<")
    for c in (kb, ob):
        for url in ("/prodi/%s/" % B, "/prodi/%s/halaman" % B, "/prodi/%s/halaman/sejarah" % B, "/prodi/%s/pengumuman" % B,
                    "/prodi/%s/pengumuman/%s" % (B, K[B]) if c is kb else "/prodi/%s/pengumuman/baru" % B):
            teks = c.get(url).get_data(as_text=True)
            ada = [t for t in TANDA if t in teks]
            cek(not ada, "saklar mati: %s tanpa bagian bahasa Inggris (%s)" % (url, ada))
    for url in ("/prodi/%s/beranda" % B, "/prodi/%s/menu" % B, "/prodi/%s/tambahan" % B, "/prodi/%s/kriteria" % B):
        teks = kb.get(url).get_data(as_text=True)
        ada = [t for t in TANDA if t in teks]
        cek(not ada, "saklar mati: %s tanpa isian bahasa Inggris (%s)" % (url, ada))
    cek("Menunggu persetujuan (0)" in kb.get("/prodi/%s/halaman" % B).get_data(as_text=True)
        and "halaman menunggu persetujuan Anda" not in kb.get("/prodi/%s/" % B).get_data(as_text=True),
        "saklar mati: draf Inggris yang tersembunyi tidak dihitung")
    cek(all(kb.get(u).status_code == 404 for u in ("/prodi/%s/halaman/sejarah/en" % B, "/prodi/%s/terjemahkan-semua" % B,
                                                    "/prodi/%s/pengumuman?en=mesin" % B, "/prodi/%s/halaman?status=mesin" % B)),
        "saklar mati: rute versi Inggris 404")
    # saving every form the way a browser does keeps the stored English values
    kirim_formulir(kb, "/prodi/%s/beranda" % B, "/prodi/%s/beranda" % B, judul="Teknik Elektro UNSRAT")
    kirim_formulir(kb, "/prodi/%s/menu" % B, "/prodi/%s/menu" % B, **{"label-profil": "Tentang kami"})
    kirim_formulir(kb, "/prodi/%s/tambahan" % B, "/prodi/%s/tambahan/simpan" % B)
    kirim_formulir(kb, "/prodi/%s/kriteria" % B, "/prodi/%s/kriteria" % B, **{"k-0-nama": "Visi dan misi"})
    r = kirim_formulir(kb, "/prodi/%s/pengumuman/%s" % (B, K[B]), "/prodi/%s/pengumuman/%s" % (B, K[B]),
                       ringkasan="Seminar nasional bersama mitra industri.", aksi_simpan="terjemahkan")
    tanpa_en = pg.tambah(B, {"judul": "Kuliah umum", "kategori": "kegiatan", "tanggal": "2026-11-11",
                             "ringkasan": "Kuliah umum bersama praktisi."}, "admb", "draf")
    kirim_formulir(kb, "/prodi/%s/pengumuman/%s" % (B, tanpa_en), "/prodi/%s/pengumuman/%s" % (B, tanpa_en),
                   aksi_simpan="terjemahkan")
    cek(not pg.cari(B, tanpa_en).get("en"), "pengumuman tanpa versi Inggris: aksi terjemahkan tidak dijalankan")
    situs_b = lokasi.baca("prodi/%s/situs" % B)
    kb_data = kriteria_mod.baca_prodi(B)
    kabar_b = pg.cari(B, K[B])
    cek(situs_b["beranda"].get("judul") == "Teknik Elektro UNSRAT" and situs_b["en"] == {"judul": "Engineering at UNSRAT"},
        "beranda: perubahan tersimpan, teks Inggris tetap: %r" % situs_b.get("en"))
    cek(situs_b["menu"]["profil"] == {"label": "Tentang kami", "label_en": "About us"},
        "menu: label Inggris tetap: %r" % situs_b["menu"].get("profil"))
    cek(halaman_tambahan.baca(B)[0].get("label_en") == "Profile Video", "halaman tambahan: nama Inggris tetap")
    cek(kb_data["kriteria"] == [{"nomor": "1", "nama": "Visi dan misi", "nama_en": "Vision"}]
        and kb_data.get("instrumen_en") == "LAM Teknik Instrument", "kriteria: nama Inggris tetap: %r" % kb_data)
    cek(r.status_code == 302 and kabar_b["ringkasan"] == "Seminar nasional bersama mitra industri."
        and kabar_b["en"]["judul"] == "National seminar" and "mesin" not in kabar_b["en"]
        and not tm.pemakaian(B)["hari"], "pengumuman: versi Inggris tetap, tanpa terjemahan mesin, tanpa pemakaian")
    cek(not os.path.isdir(os.path.join(os.environ["PRODI_PUBLIK"], "s1elektro", "en"))
        and os.path.isdir(os.path.join(os.environ["PRODI_PUBLIK"], "s1elektro")), "situs B tanpa versi Inggris")

    # ============================================================== A, switched on: everything in English
    teks = ka.get("/prodi/%s/" % A).get_data(as_text=True)
    cek('<h2 id="judul-en">Versi bahasa Inggris</h2>' in teks and ">Terjemahkan semua</a>" in teks, "A: kotak di Ringkasan")
    teks = ka.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek(">English</th>" in teks and "Versi Inggris: <strong>" in teks, "A: kolom English di daftar halaman")
    cek('aria-label="Bahasa isi halaman"' in ka.get("/prodi/%s/halaman/sejarah" % A).get_data(as_text=True), "A: tab English")
    teks = ka.get("/prodi/%s/pengumuman/%s" % (A, K[A])).get_data(as_text=True)
    cek("Versi bahasa Inggris (opsional)" in teks and "Simpan dan terjemahkan dari versi Indonesia" in teks,
        "A: bagian Inggris pengumuman dengan terjemahan mesin")
    for url, tanda in (("beranda", "<legend>Versi bahasa Inggris</legend>"), ("menu", "Label Inggris"),
                       ("tambahan", "Nama menu (bahasa Inggris)"), ("kriteria", "Nama kriteria (bahasa Inggris)")):
        cek(tanda in ka.get("/prodi/%s/%s" % (A, url)).get_data(as_text=True), "A: isian Inggris di %s" % url)

    # ============================================================== the superadmin
    teks = ks.get("/").get_data(as_text=True)
    cek("Versi bahasa Inggris dan terjemahan mesin aktif untuk <strong>1</strong> prodi" in teks
        and "S1 Teknik Informatika</a>" in teks.split("aktif untuk")[1].split("</li>")[0]
        and "Elektro" not in teks.split("aktif untuk")[1].split("</li>")[0], "dasbor superadmin: daftar prodi berversi Inggris")
    cek("hanya untuk prodi yang mengikuti akreditasi internasional" in ks.get("/super/prodi/%s" % B).get_data(as_text=True),
        "keterangan saklar")
    with ks.session_transaction() as s_:
        token = s_["csrf"]
    cek(ks.post("/super/prodi/%s/inggris" % B, data={"csrf": token, "inggris": "1"}).status_code == 302, "saklar B dinyalakan")
    teks = kb.get("/prodi/%s/beranda" % B).get_data(as_text=True)
    cek('value="Engineering at UNSRAT"' in teks and 'value="About us"' in kb.get("/prodi/%s/menu" % B).get_data(as_text=True)
        and 'value="Profile Video"' in kb.get("/prodi/%s/tambahan" % B).get_data(as_text=True)
        and 'value="Vision"' in kb.get("/prodi/%s/kriteria" % B).get_data(as_text=True)
        and 'value="National seminar"' in kb.get("/prodi/%s/pengumuman/%s" % (B, K[B])).get_data(as_text=True)
        and kb.get("/prodi/%s/halaman/sejarah/en" % B).status_code == 200
        and os.path.isdir(os.path.join(os.environ["PRODI_PUBLIK"], "s1elektro", "en")),
        "saklar dinyalakan: bagian Inggris kembali dengan nilai tersimpan, situs Inggris dibangun")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_inggris_terbatas: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
