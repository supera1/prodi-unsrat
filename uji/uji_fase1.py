# -*- coding: utf-8 -*-
"""Acceptance test of phase 1 (docs/rencana-fase-01.md §11), on www's real data, criterion by criterion.

K1  97 programme sites in staging (noindex) under the approved slugs (platform/data-awal/slug.csv), started the way a
    new VM starts (impor_www.isi_awal); every page passes the shared page checks; the integrity check is clean.
K2  the official data on the sites is exactly www's. For every programme, every official value on the specification,
    accreditation, graduate profile/CPL, contact and home pages and in the root list is compared with www's own
    prodi.json and unit.json (not with the platform's copy). A programme's own change (K-P16) is the only difference
    allowed; it shows, and goes away with "pakai data www". The comparison is shown to catch a changed CPL and a
    changed value (it does not pass on anything).
K3  accounts per person in three roles: an admin or operator of one programme gets no page of any other programme,
    for every admin route that has a programme code, on the real registry of 97.
K4  a programme admin changes tagline, colours, logo and menu in the admin; the site shows each change after the
    automatic rebuild, and the site of another programme does not change by a single byte.
K5  the stack stands apart from www's stack: no volume, network or container of it in docker-compose.yml.
K6  every suite passes inside the image (Dockerfile runs them, this one included); the phase log is written.
Also the minimum standard of CLAUDE.md: no script in any page (works without JavaScript), page and style sizes.

www's data: the sibling checkout (../website-unsrat-2026) when it is there, else the copy shipped with the repository
(platform/data-awal/www/), so this also runs inside the image.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import gzip
import hashlib
import html
import io
import json
import os
import random
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
    from PIL import Image
except ImportError:
    print("uji_fase1: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-fase1-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www-tidak-ada"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"),
                  ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import data_prodi  # noqa: E402
import impor_www  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
import slug as slug_mod  # noqa: E402
import tarik_www  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

WWW_ASLI = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026", "site", "mockup", "data")
if not os.path.isfile(os.path.join(WWW_ASLI, "prodi.json")):
    WWW_ASLI = impor_www.DATA_AWAL
IP = "103.84.116.10"
gagal = []
TAG = re.compile(r"<[^>]+>")


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def norm(teks):
    """Text as a reader sees it: entities decoded, tags gone, white space collapsed."""
    return " ".join(html.unescape(TAG.sub(" ", "" if teks is None else str(teks))).split())


def halaman(rel):
    path = os.path.join(lokasi.publik(), *rel.split("/"))
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def tabel(isi, kelas):
    """{label: value} of a <dl class="kelas"> on a page."""
    m = re.search(r'<dl class="%s">(.*?)</dl>' % kelas, isi or "", re.S)
    return {norm(dt): norm(dd) for dt, dd in re.findall(r"<dt>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", m.group(1), re.S)} if m else {}


def sha_folder(folder):
    hasil = {}
    for akar, _d, nama in os.walk(folder):
        for n in nama:
            with open(os.path.join(akar, n), "rb") as f:
                hasil[os.path.relpath(os.path.join(akar, n), folder)] = hashlib.sha256(f.read()).hexdigest()
    return hasil


# ------------------------------------------------------------------ K2: a programme as www has it, against its pages

def bandingkan(p, unit_www, slug, tampil_berlaku, akar_html):
    """Differences between programme p of www's prodi.json and its pages: ["page: what: expected ... found ...", ...]."""
    beda = []

    def selisih(tempat, apa, harap, dapat):
        if norm(harap) != norm(dapat):
            beda.append("%s: %s: harus %r, tertulis %r" % (tempat, apa, norm(harap), dapat if dapat is None else norm(dapat)))

    def rel(alamat):
        return "%s/%s/index.html" % (slug, alamat) if alamat else "%s/index.html" % slug

    label = registri.label_akreditasi(p.get("akreditasi"))
    nama_unit = unit_www.get(p["unit_kode"], {}).get("nama") or p["unit"]
    kurikulum = sorted({c["kurikulum"] for c in p.get("cpl") or [] if c.get("kurikulum")})

    # specification: the official facts in one table
    harap = {"Nama program studi": p["nama"],
             "Jenjang": "%s (%s)" % (registri.JENJANG_PANJANG.get(p["jenjang"], p["jenjang"]), p["jenjang"]),
             "Gelar lulusan": p.get("gelar") or "Sedang dilengkapi",
             "Beban studi": "%s SKS" % p["sks"] if p.get("sks") else "Sedang dilengkapi",
             "Fakultas": nama_unit, "Perguruan tinggi": "Universitas Sam Ratulangi, Manado",
             "Kode program studi (PDDIKTI)": p["kode_pddikti"],
             "Akreditasi": (label + (" (%s)" % p["lembaga_akreditasi"] if p.get("lembaga_akreditasi") else "")) if label
             else "Sedang dilengkapi"}
    for kunci, nilai in (("Nama dalam bahasa Inggris", p.get("nama_en")), ("Akreditasi internasional", p.get("internasional")),
                         ("Surel", p.get("surel")), ("Kurikulum", ", ".join(kurikulum))):
        if nilai:
            harap[kunci] = nilai
    dapat = tabel(halaman(rel("akademik/spesifikasi")), "tabel-data")
    for kunci in sorted(set(harap) | set(dapat)):
        selisih("spesifikasi", kunci, harap.get(kunci), dapat.get(kunci))

    # accreditation
    isi = halaman(rel("profil/akreditasi"))
    if label:
        harap = {"Peringkat akreditasi": label, "Lembaga akreditasi": p.get("lembaga_akreditasi") or "Sedang dilengkapi"}
        if tampil_berlaku and bangun.tanggal(p.get("berlaku_hingga")):
            harap["Berlaku hingga"] = bangun.tanggal(p["berlaku_hingga"])
        if p.get("internasional"):
            harap["Akreditasi internasional"] = p["internasional"]
        dapat = tabel(isi, "tabel-data")
        for kunci in sorted(set(harap) | set(dapat)):
            selisih("akreditasi", kunci, harap.get(kunci), dapat.get(kunci))
    elif "Status akreditasi sedang dilengkapi" not in norm(isi):
        beda.append("akreditasi: tanpa nilai harus tertulis 'sedang dilengkapi'")

    # graduate profile: fields of work and every learning outcome, in www's order
    isi = halaman(rel("akademik/profil-lulusan")) or ""
    m = re.search(r"<h2>Bidang kerja lulusan</h2>\s*<p[^>]*>(.*?)</p>", isi, re.S)
    selisih("profil lulusan", "bidang kerja", p.get("bidang_kerja") or "Bidang kerja lulusan sedang dilengkapi.",
            m.group(1) if m else None)
    m = re.search(r'<ol class="daftar-cpl">(.*?)</ol>', isi, re.S)
    dapat = [norm(li) for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)] if m else []
    harap = [norm("%s %s" % (c["kode"], c["isi"]) if c.get("kode") else c["isi"]) for c in p.get("cpl") or []]
    if dapat != harap:
        for i in range(max(len(dapat), len(harap))):
            if i >= len(dapat) or i >= len(harap) or dapat[i] != harap[i]:
                beda.append("profil lulusan: CPL ke-%d: harus %r, tertulis %r" % (
                    i + 1, harap[i] if i < len(harap) else None, dapat[i] if i < len(dapat) else None))
                break
    if not harap and "Capaian pembelajaran lulusan sedang dilengkapi" not in norm(isi):
        beda.append("profil lulusan: tanpa CPL harus tertulis 'sedang dilengkapi'")

    # contact
    dapat = tabel(halaman(rel("kontak")), "tabel-data")
    selisih("kontak", "Surel program studi", p.get("surel") or None, dapat.get("Surel program studi"))
    selisih("kontak", "Fakultas", nama_unit, dapat.get("Fakultas"))

    # home page: the title and the official cards (K-P15: values locked to the official data)
    isi = halaman(rel("")) or ""
    m = re.search(r'<h1 id="judul-prodi">(.*?)</h1>', isi, re.S)
    selisih("beranda", "judul", registri.nama_tampil(p), m.group(1) if m else None)
    harap = {}
    if label:
        harap["Akreditasi"] = label + (" " + p["lembaga_akreditasi"] if p.get("lembaga_akreditasi") else "")
    if p.get("gelar"):
        harap["Gelar"] = p["gelar"]
    if p.get("sks"):
        harap["Beban studi"] = "%s SKS" % p["sks"]
    if p.get("internasional"):
        harap["Akreditasi internasional"] = p["internasional"]
    dapat = tabel(isi, "fakta")
    for kunci in sorted(set(harap) | set(dapat)):
        selisih("beranda", "kartu %s" % kunci, harap.get(kunci), dapat.get(kunci))

    # the root list of all programmes
    m = re.search(r'<a href="%s/">(.*?)</a></h3>(.*?)</li>' % re.escape(slug), akar_html, re.S)
    if not m:
        beda.append("halaman akar: tautan ke %s/ tidak ada" % slug)
    else:
        selisih("halaman akar", "nama", registri.nama_tampil(p), m.group(1))
        lencana = re.search(r'<span class="lencana">(.*?)</span>', m.group(2), re.S)
        selisih("halaman akar", "akreditasi", "Akreditasi " + label if label else None, lencana.group(1) if lencana else None)
    return beda


try:
    # ============================================================== K1: 97 sites in staging under the approved slugs
    pesan = impor_www.isi_awal()                       # a new VM: the starting copy and the approved slugs
    cek(len(pesan) == 2, "isi awal: %r" % pesan)
    if WWW_ASLI != impor_www.DATA_AWAL:                # on a developer's machine: www's data as it is now
        tarik_www.terapkan("penguji", WWW_ASLI, paksa=True)
    b = bangun.Pembangun(produksi=False)
    b.bangun()
    cek(not b.peringatan, "bangun tanpa peringatan: %r" % b.peringatan[:3])
    daftar_slug = slug_mod.baca_csv()
    reg = {r["kode_pddikti"]: r for r in registri.baca()["prodi"]}
    cek(len(daftar_slug) == 97 and len(reg) == 97, "97 prodi di daftar slug dan registri: %d, %d" % (len(daftar_slug), len(reg)))
    for baris in daftar_slug:
        r = reg.get(baris["kode_pddikti"])
        cek(r and r["slug"] == baris["slug_usulan"] and r["aktif"], "registri %s: %r" % (baris["kode_pddikti"], r))
        cek(halaman("%s/index.html" % baris["slug_usulan"]), "situs /%s/ ada" % baris["slug_usulan"])
    folder_akar = {n for n in os.listdir(lokasi.publik()) if os.path.isdir(os.path.join(lokasi.publik(), n))}
    cek(folder_akar - {"aset", "unggahan"} == {r["slug"] for r in reg.values()}, "tepat 97 folder situs prodi di akar")
    semua_html = [os.path.join(a, n) for a, _d, ns in os.walk(lokasi.publik()) for n in ns if n.endswith(".html")]
    tanpa_noindex = []
    for path in semua_html:
        with io.open(path, encoding="utf-8") as f:
            isi = f.read()
        if 'content="noindex' not in isi or "pita-staging" not in isi:
            tanpa_noindex.append(os.path.relpath(path, lokasi.publik()))
    cek(not tanpa_noindex, "setiap halaman staging ber-noindex dan berpita: %r" % tanpa_noindex[:3])
    cek("Disallow: /" in halaman("robots.txt") and not os.path.exists(os.path.join(lokasi.publik(), "sitemap.xml")),
        "robots staging melarang, tanpa sitemap")
    jumlah_halaman, temuan = periksa_situs(lokasi.publik(), "fase1")
    gagal.extend(temuan[:50])
    cek(jumlah_halaman == len(semua_html) and jumlah_halaman > 97 * 30, "halaman diperiksa: %d" % jumlah_halaman)
    cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "cek integritas bersih")
    print("K1: 97 situs staging, %d halaman lolos pemeriksaan halaman" % jumlah_halaman)

    # --- the minimum standard of every page (CLAUDE.md): no script, small pages and styles
    berkas_js = [n for a, _d, ns in os.walk(lokasi.publik()) for n in ns if n.endswith((".js", ".mjs"))]
    cek(not berkas_js, "tanpa berkas JavaScript: %r" % berkas_js[:3])
    terbesar, berskrip = (0, ""), []
    for path in semua_html:
        with open(path, "rb") as f:
            mentah = f.read()
        if re.search(rb"<script(?![^>]*application/ld\+json)", mentah):
            berskrip.append(os.path.relpath(path, lokasi.publik()))
        terbesar = max(terbesar, (len(gzip.compress(mentah)), os.path.relpath(path, lokasi.publik())))
    cek(not berskrip, "tanpa skrip selain data terstruktur JSON-LD: %r" % berskrip[:3])
    css = sum(len(gzip.compress(open(os.path.join(lokasi.publik(), "aset", "css", n), "rb").read()))
              for n in os.listdir(os.path.join(lokasi.publik(), "aset", "css")))
    cek(terbesar[0] < 30 * 1024 and css < 30 * 1024, "halaman terbesar %d B dan CSS %d B (gzip) di bawah 30 KB" % (terbesar[0], css))
    print("standar halaman: tanpa skrip; halaman terbesar %.1f KB gzip (%s); CSS %.1f KB gzip"
          % (terbesar[0] / 1024.0, terbesar[1], css / 1024.0))

    # ============================================================== K2: the official data is exactly www's
    with io.open(os.path.join(WWW_ASLI, "prodi.json"), encoding="utf-8") as f:
        www_prodi = json.load(f)
    with io.open(os.path.join(WWW_ASLI, "unit.json"), encoding="utf-8") as f:
        unit_www = {u["kode"]: u for u in json.load(f)["unit"]}
    tampil_berlaku = bool(www_prodi.get("tampilkan_berlaku_hingga"))
    per_kode = {p["kode_pddikti"]: p for p in www_prodi["program"]}
    akar_html = halaman("index.html")

    def semua_beda():
        hasil = {}
        for kode, r in reg.items():
            if kode not in per_kode:
                hasil[kode] = ["prodi tidak ada lagi di data www, tetapi situsnya aktif"]
                continue
            beda = bandingkan(per_kode[kode], unit_www, r["slug"], tampil_berlaku, akar_html)
            if beda:
                hasil[kode] = beda
        return hasil
    beda = semua_beda()
    cek(not beda, "data resmi di situs harus sama dengan www: %d prodi berbeda, mis. %r" % (len(beda), list(beda.items())[:2]))
    belum = sorted(set(per_kode) - set(reg))
    if belum:
        print("PERHATIAN prodi di www yang belum terdaftar (belum punya situs): %s" % ", ".join(belum))
    jumlah_cpl = sum(len(p.get("cpl") or []) for p in www_prodi["program"] if p["kode_pddikti"] in reg)
    print("K2: %d prodi dan %d CPL sama persis dengan data www (%s)" % (len(reg) - len(beda), jumlah_cpl,
          "repo www di sebelah" if WWW_ASLI != impor_www.DATA_AWAL else "salinan data www di repo"))

    # the comparison catches a changed learning outcome and a changed value (it does not pass on anything)
    contoh = random.Random(7).choice([k for k in reg if per_kode.get(k, {}).get("cpl")])
    slug_contoh = reg[contoh]["slug"]
    for rel, pola, ganti in (("%s/akademik/profil-lulusan/index.html" % slug_contoh, r'(<ol class="daftar-cpl">.*?<li>)', r"\1X"),
                             ("%s/akademik/spesifikasi/index.html" % slug_contoh, r"(<dd>%s)(</dd>)" % contoh, r"\g<1>9\2")):
        path = os.path.join(lokasi.publik(), *rel.split("/"))
        with io.open(path, encoding="utf-8") as f:
            asli = f.read()
        rusak = re.sub(pola, ganti, asli, count=1, flags=re.S)
        cek(rusak != asli, "halaman %s berhasil diubah untuk uji" % rel)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(rusak)
        cek(contoh in semua_beda(), "perbandingan harus menemukan perubahan di %s" % rel)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(asli)

    # a programme's own change (K-P16) is the one difference, and goes away with "pakai data www"
    p_contoh = per_kode[contoh]
    sks_baru = (p_contoh.get("sks") or 140) + 2
    data_prodi.simpan(contoh, {"sks": sks_baru}, "penguji")
    bangun.Pembangun(produksi=False).bangun(contoh)
    beda = semua_beda()
    cek(list(beda) == [contoh] and all("SKS" in x or "Beban studi" in x for x in beda[contoh])
        and "%d SKS" % sks_baru in norm(halaman("%s/akademik/spesifikasi/index.html" % slug_contoh)),
        "perubahan prodi sendiri tampil dan menjadi satu-satunya beda: %r" % beda)
    data_prodi.pakai_www(contoh, "sks", "penguji")
    bangun.Pembangun(produksi=False).bangun(contoh)
    cek(not semua_beda(), "setelah 'pakai data www' situs kembali sama dengan www")

    # ============================================================== K3: no programme reaches another programme
    kode = sorted(reg)
    A, B = "55201" if "55201" in reg else kode[0], kode[1] if kode[1] != "55201" else kode[2]
    lain = random.Random(3).sample([k for k in kode if k not in (A, B)], 8) + [B]
    super_id, sementara = akun.buat(None, "superuji", "Super Uji", "super")
    SANDI = {"superuji": "Biru laut 7 menara pagi", "adma": "Kopi hangat 42 senja", "opa": "Hujan 9 jendela kayu"}
    akun.ganti_sandi(super_id, sementara, SANDI["superuji"])
    super_ = akun.ambil(super_id)
    for nama, peran in (("adma", "admin"), ("opa", "operator")):
        id_, sementara = akun.buat(super_, nama, nama.capitalize() + " Uji", peran, [A])
        akun.ganti_sandi(id_, sementara, SANDI[nama])
    cek(akun.periksa_sandi("rahasia123", "admin") and akun.periksa_sandi("Kopi hangat 42", "super"), "sandi lemah ditolak")
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron"})

    def klien(nama):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = IP
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        return c
    sesi = {n: klien(n) for n in ("adma", "opa")}

    def url(aturan, kode_):
        nilai = {"kode": kode_, "id_": "1", "jalur": "%s/202610-0123456789ab.pdf" % kode_}
        return re.sub(r"<(?:[^:>]+:)?([^>]+)>", lambda m: nilai.get(m.group(1), "x"), aturan)
    rute = [(r.rule, sorted(r.methods - {"HEAD", "OPTIONS"}), getattr(app.view_functions[r.endpoint], "akses"))
            for r in app.url_map.iter_rules() if "<kode>" in r.rule]
    bocor, dicoba = [], 0
    for aturan, metode, (jenis, minimal) in rute:
        for nama, c in sesi.items():
            for k in lain:
                for m_ in metode:
                    if m_ == "GET":
                        r = c.get(url(aturan, k))
                    else:
                        with c.session_transaction() as s:
                            r = c.post(url(aturan, k), data={"csrf": s["csrf"]})
                    dicoba += 1
                    if r.status_code != 403:
                        bocor.append("%s %s oleh %s: %s" % (m_, url(aturan, k), nama, r.status_code))
            # its own programme: what @akses declares (pages that need more than the code answer 404 here)
            if "GET" in metode and "id_>" not in aturan and "<path:jalur>" not in aturan:
                boleh = jenis == "prodi" and not (minimal == "admin" and nama == "opa")
                kode_status = c.get(url(aturan, A)).status_code
                cek(kode_status in ((200, 404) if boleh else (403,)),
                    "GET %s oleh %s untuk prodinya: %s (%s)" % (url(aturan, A), nama, kode_status, "boleh" if boleh else "tidak boleh"))
    cek(not bocor, "kebocoran antar-prodi: %r" % bocor[:5])
    print("K3: %d rute berkode prodi x 2 akun x %d prodi lain = %d permintaan, 0 bocor" % (len(rute), len(lain), dicoba))

    # ============================================================== K4: a programme admin's changes reach the site
    slug_a, slug_b = reg[A]["slug"], reg[B]["slug"]
    sebelum_b = sha_folder(os.path.join(lokasi.publik(), slug_b))

    def kirim(url_, berkas=None, **data):
        c = sesi["adma"]
        with c.session_transaction() as s:
            data["csrf"] = s["csrf"]
        if berkas:
            data.update(berkas)
            return c.post(url_, data=data, content_type="multipart/form-data")
        return c.post(url_, data=data)
    p = "/prodi/%s" % A
    cek(kirim(p + "/beranda", latar="pucat", pengantar="Tagline uji penerimaan Fase 1.").status_code == 302, "tagline disimpan")
    cek("Tagline uji penerimaan Fase 1." in halaman("%s/index.html" % slug_a), "tagline tampil di beranda situs")
    cek(kirim(p + "/identitas", palet="toska").status_code == 302, "palet disimpan")
    with io.open(os.path.join(lokasi.publik(), slug_a, "warna.css"), encoding="utf-8") as f:
        cek("#0F5F66" in f.read(), "warna palet tampil di situs")
    buf = io.BytesIO()
    Image.new("RGBA", (400, 200), (20, 60, 160, 255)).save(buf, "PNG")
    cek(kirim(p + "/identitas/logo", {"logo": (io.BytesIO(buf.getvalue()), "logo.png")}).status_code == 302, "logo diunggah")
    cek('class="merek__logo"' in halaman("%s/index.html" % slug_a), "logo tampil di kepala situs")
    cek(kirim(p + "/menu", **{"label-sejarah": "Riwayat Prodi", "sembunyi-jadwal": "1"}).status_code == 302, "menu disimpan")
    cek(">Riwayat Prodi<" in halaman("%s/profil/sejarah/index.html" % slug_a)
        and not halaman("%s/akademik/jadwal/index.html" % slug_a), "label menu dan halaman tersembunyi tampil di situs")
    cek(sha_folder(os.path.join(lokasi.publik(), slug_b)) == sebelum_b, "situs prodi lain tidak berubah satu bait pun")
    cek(app.antrean.status["ok"] and app.antrean.status["cakupan"] == A, "bangun ulang otomatis satu prodi: %r" % app.antrean.status)
    jumlah_halaman, temuan = periksa_situs(lokasi.publik(), "fase1-k4")
    gagal.extend(temuan[:50])
    cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "cek integritas bersih setelah perubahan")
    print("K4: tagline, palet, logo, dan menu tampil setelah bangun ulang otomatis; situs prodi lain tetap")

    # ============================================================== K5 and K6: the stack and the log (repository only)
    if os.path.isfile(os.path.join(AKAR, "docker-compose.yml")):
        with io.open(os.path.join(AKAR, "docker-compose.yml"), encoding="utf-8") as f:
            compose = f.read()
        # www's stack is "unsrat-web" with the volumes unsrat-data/-rahasia/-publik; ours are all prodi-*
        www = re.findall(r"(?<![a-z-])unsrat-(?:web|data|publik|rahasia)\S*|external:|network_mode", compose)
        cek(not www, "stack prodi tidak memakai volume, jaringan, atau kontainer stack www: %r" % www)
        volume = re.findall(r"^  ([a-z][a-z0-9-]*):", compose.split("\nvolumes:\n")[1], re.M)
        cek(volume and all(v.startswith("prodi-") for v in volume), "volume stack bernama prodi-*: %r" % volume)
        cek(os.path.isfile(os.path.join(AKAR, "docs", "log", "fase-01.md")), "log fase docs/log/fase-01.md ditulis")
        print("K5/K6: stack terpisah dari www; log fase ada (uji ini juga berjalan di dalam image saat build)")
    else:
        print("K5/K6: di dalam image; berkas stack dan log tidak ada di sini, dilewati")
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_fase1: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
