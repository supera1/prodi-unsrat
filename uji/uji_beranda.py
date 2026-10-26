# -*- coding: utf-8 -*-
"""Step 3c of phase 1: the front section (hero) of a programme's home page (platform/tampilan_prodi.py,
media.olah_hero, the hero part of bangun.py).

Checks the settings rules (texts, colours, cards; the official values cannot be overridden), the readability of every
background for every palette and faculty colour, the cropping of background photos, and the built pages and style
sheets of a made-up programme with each kind of background.

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
for sub in ("platform", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image
    import jinja2  # noqa: F401
except ImportError:
    print("uji_beranda: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-beranda-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"),
                  ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
for nama in ("PRODI_MODE", "PRODI_PENYIMPANAN"):
    os.environ.pop(nama, None)

import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import registri  # noqa: E402
import tampilan_prodi as tp  # noqa: E402
import tarik_www  # noqa: E402
import warna  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

WWW_ASLI = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026", "site", "mockup", "data")
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def foto(lebar, tinggi, kiri=(255, 0, 0), kanan=(0, 0, 255), fmt="JPEG"):
    """Left half one colour, right half another (top/bottom for tall crops are tested with atas/bawah)."""
    im = Image.new("RGB", (lebar, tinggi), kanan)
    im.paste(Image.new("RGB", (lebar // 2, tinggi), kiri), (0, 0))
    buf = io.BytesIO()
    im.save(buf, fmt)
    return buf.getvalue()


def warna_tengah(data):
    with Image.open(io.BytesIO(data)) as im:
        return im.convert("RGB").getpixel((im.width // 2, im.height // 2))


try:
    # --- settings rules
    cek(tp.periksa({}) == [] and tp.periksa(None) == [], "tanpa pengaturan: sah")
    sah = {"latar": {"jenis": "warna", "warna": "#1F3A5F"}, "label": "Label", "judul": "Judul", "subjudul": "Sub",
           "kartu": {"gelar": {"label": "Gelar lulusan", "urutan": 0}, "sks": {"sembunyi": True}},
           "kartu_tambahan": [{"label": "Mahasiswa aktif", "nilai": "812", "keterangan": "Oktober 2026"}]}
    cek(tp.periksa(sah, "Kalimat.") == [], "pengaturan sah diterima: %r" % tp.periksa(sah, "Kalimat."))
    for label, ubah in (("nilai kartu resmi ditimpa", {"kartu": {"akreditasi": {"nilai": "Unggul"}}}),
                        ("kartu resmi tak dikenal", {"kartu": {"rektor": {"label": "x"}}}),
                        ("kartu tambahan > 2", {"kartu_tambahan": [{"label": "a", "nilai": "1"}] * 3}),
                        ("kartu tambahan tanpa nilai", {"kartu_tambahan": [{"label": "a", "nilai": " "}]}),
                        ("judul terlalu panjang", {"judul": "x" * 101}),
                        ("label HTML", {"label": "<script>x</script>"}),
                        ("judul judi", {"judul": "Prodi slot gacor"}),
                        ("kunci tak dikenal", {"warna_teks": "#fff"}),
                        ("jenis latar tak dikenal", {"latar": {"jenis": "video"}}),
                        ("kode warna rusak", {"latar": {"jenis": "warna", "warna": "biru"}}),
                        ("warna abu tengah", {"latar": {"jenis": "warna", "warna": "#808080"}}),
                        ("foto belum ada", {"latar": {"jenis": "foto"}}),
                        ("foto jalur berbahaya", {"latar": {"jenis": "foto", "foto": {"jenis": "hero", "varian": {
                            k: {"jalur": "../../x.jpg"} for k in media.VARIAN_HERO}}}}),
                        ("foto dari host lain", {"latar": {"jenis": "foto", "foto": {"jenis": "hero", "varian": {
                            k: {"url": "https://jahat.com/x.jpg"} for k in media.VARIAN_HERO}}}}),
                        ("URL foto yang menutup url() CSS", {"latar": {"jenis": "foto", "foto": {"jenis": "hero", "varian": {
                            k: {"url": "https://storage.googleapis.com/b/x.jpg\");}body{display:none"} for k in media.VARIAN_HERO}}}}),
                        ("urutan bukan angka", {"kartu": {"gelar": {"urutan": "satu"}}})):
        cek(tp.periksa(ubah), "pengaturan dengan %s harus ditolak" % label)
    cek(tp.periksa({}, "x" * 301), "kalimat pengantar terlalu panjang ditolak")
    cek(tp.teks_untuk_latar("#FFFFFF")[0] == warna.GELAP and tp.teks_untuk_latar("#000033")[0] == warna.PUTIH,
        "latar terang -> teks gelap, latar gelap -> teks putih")

    # --- readability of every background, for every palette and every faculty colour
    calon = [warna.warna_prodi(p["id"], None) for p in warna.baca_palet()]
    if os.path.isfile(os.path.join(WWW_ASLI, "unit.json")):
        with io.open(os.path.join(WWW_ASLI, "unit.json"), encoding="utf-8") as f:
            calon += [warna.warna_prodi(None, u["bendera"]) for u in json.load(f)["unit"] if u.get("bendera")]
    for w in calon:
        nama = "%s/%s" % (w["palet"], w["utama"])
        cek(warna.kontras(w["utama"], w["utama_pucat"]) >= 4.5, "latar pucat %s: label" % nama)
        cek(warna.kontras(warna.GELAP, w["utama_pucat"]) >= 4.5, "latar pucat %s: judul" % nama)
        cek(warna.kontras(tp.REDUP, w["utama_pucat"]) >= 4.5, "latar pucat %s: subjudul %.2f" % (nama, warna.kontras(tp.REDUP, w["utama_pucat"])))
        cek(warna.kontras(warna.PUTIH, w["utama"]) >= 4.5, "latar utama %s: teks putih" % nama)
        a = tp.lapisan_foto(w["utama_gelap"])
        terang = warna.campur(warna.PUTIH, w["utama_gelap"], a)
        cek(warna.kontras(warna.PUTIH, terang) >= 4.5, "latar foto %s: teks putih di atas bagian putih foto" % nama)
    for hex_ in ("#000000", "#FFFFFF", "#1F3A5F", "#F2B705", "#3500FF", "#E6E6F5", "#5A5A5A"):
        hasil = tp.teks_untuk_latar(hex_)
        cek(hasil and warna.kontras(hasil[0], hex_) >= 4.5, "warna pilihan %s harus punya teks yang terbaca" % hex_)

    # --- background photos
    cek(media.olah_hero.__defaults__ == ("tengah",), "fokus bawaan tengah")
    for data, label in ((foto(2399, 800), "lebar 2399"), (foto(2400, 799), "tinggi 799"), (foto(2400, 800, fmt="GIF"), "GIF"),
                        (b"bukan gambar", "bukan gambar"), (b"\xff\xd8" + b"0" * media.MAKS_HERO, "terlalu besar")):
        try:
            media.olah_hero(data)
            gagal.append("foto latar %s harus ditolak" % label)
        except ValueError:
            pass
    try:
        media.olah_hero(foto(2400, 800), "pojok")
        gagal.append("fokus tak dikenal harus ditolak")
    except ValueError:
        pass
    h = media.olah_hero(foto(4000, 1000))
    cek({k: v[1] for k, v in h.items()} == {"2400": (2400, 800), "1600": (1600, 533), "ponsel": (1200, 900)},
        "ukuran potongan: %r" % {k: v[1] for k, v in h.items()})
    for k, (isi, _u) in h.items():
        with Image.open(io.BytesIO(isi)) as im:
            cek(im.format == "JPEG" and not im.getexif(), "potongan %s JPEG tanpa EXIF" % k)
    # a wide photo, left half red: the phone crop shows red with focus "kiri", blue with "kanan"
    kiri = warna_tengah(media.olah_hero(foto(4000, 1000), "kiri")["ponsel"][0])
    kanan = warna_tengah(media.olah_hero(foto(4000, 1000), "kanan")["ponsel"][0])
    cek(kiri[0] > 200 and kiri[2] < 60 and kanan[2] > 200 and kanan[0] < 60, "titik fokus kiri/kanan: %r %r" % (kiri, kanan))
    # a tall photo, top half green: the wide crop shows green with focus "atas"
    tinggi = Image.new("RGB", (2400, 2400), (0, 0, 255))
    tinggi.paste(Image.new("RGB", (2400, 1200), (0, 255, 0)), (0, 0))
    buf = io.BytesIO()
    tinggi.save(buf, "PNG")
    atas = warna_tengah(media.olah_hero(buf.getvalue(), "atas")["2400"][0])
    cek(atas[1] > 200 and atas[2] < 60, "titik fokus atas pada foto tinggi: %r" % (atas,))

    # --- a made-up programme with each kind of background
    os.makedirs(os.environ["WWW_DATA"])
    www = {"prodi": {"tampilkan_berlaku_hingga": False, "program": [
               {"kode_pddikti": "55201", "nama": "Teknik Informatika", "nama_en": "Informatics Engineering", "jenjang": "S1",
                "unit_kode": "ft", "unit": "Fakultas Teknik", "slug": "a", "gelar": "S.Kom.", "sks": 144,
                "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Infokom", "internasional": "AUN-QA", "cpl": []},
               {"kode_pddikti": "20201", "nama": "Teknik Elektro", "jenjang": "S1", "unit_kode": "ft",
                "unit": "Fakultas Teknik", "slug": "b", "gelar": "S.T.", "akreditasi": "Baik Sekali", "cpl": []},
               {"kode_pddikti": "21201", "nama": "Teknik Mesin", "jenjang": "S1", "unit_kode": "ft",
                "unit": "Fakultas Teknik", "slug": "c", "cpl": []}]},
           "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
           "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}
    for nama, isi in www.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n55201,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "20201,S1,Teknik Elektro,FT,s1elektro,x,x\n21201,S1,Teknik Mesin,FT,s1mesin,x,x\n")
    registri.siapkan_dari_csv("penguji", path_csv)

    tp.ganti_foto("55201", foto(3000, 1200), "tengah", "penguji")
    tp.atur("55201", {"tagline": "Kalimat \"pengantar\" & <bukan tag>".replace("<bukan tag>", "lainnya"),
                      "beranda": dict(lokasi.baca("prodi/55201/situs")["beranda"], judul="Informatika UNSRAT",
                                      kartu={"akreditasi": {"label": "Peringkat akreditasi"}, "internasional": {"sembunyi": True},
                                             "sks": {"urutan": 0}},
                                      kartu_tambahan=[{"label": "Mahasiswa aktif", "nilai": "812", "keterangan": "Oktober 2026"}])},
            "penguji")
    tp.atur("20201", {"beranda": {"latar": {"jenis": "warna", "warna": "#F2B705"}, "subjudul": "Teks bebas"}}, "penguji")
    try:
        tp.atur("21201", {"beranda": {"latar": {"jenis": "warna", "warna": "#808080"}}}, "penguji")
        gagal.append("atur dengan warna yang tidak terbaca harus ditolak")
    except tp.GagalTampilan:
        pass
    try:
        tp.atur("21201", {"warna_bebas": "#ffffff"}, "penguji")
        gagal.append("atur hanya untuk pengaturan yang dikenal")
    except tp.GagalTampilan:
        pass
    # settings written past the checks (e.g. by hand) are ignored with a warning, never published
    lokasi.tulis("prodi/21201/situs", {"beranda": {"kartu": {"gelar": {"nilai": "Prof."}}, "judul": "<b>x</b>"}}, "penguji", "uji", "uji")

    b = bangun.Pembangun(hari_ini="2026-10-26")
    b.bangun()
    pub = lokasi.publik()

    def baca(rel):
        with io.open(os.path.join(pub, rel), encoding="utf-8") as f:
            return f.read()

    jumlah, temuan = periksa_situs(pub, "beranda")
    gagal.extend(temuan)
    cek(any("21201" in x and "pengaturan beranda diabaikan" in x for x in b.peringatan), "pengaturan tidak sah diperingatkan")

    ti = baca("s1informatika/index.html")
    cek('class="pahlawan pahlawan--foto"' in ti, "beranda berfoto memakai kelas pahlawan--foto")
    cek(">Informatika UNSRAT</h1>" in ti, "judul dari admin")
    cek("<title>S1 Teknik Informatika — Universitas Sam Ratulangi</title>" in ti, "judul halaman tetap nama resmi")
    cek("Kalimat &#34;pengantar&#34; &amp; lainnya" in ti, "kalimat pengantar di-escape")
    kartu = re.findall(r"<dt>([^<]+)</dt>\s*<dd>([^<]+)", ti)
    cek([k[0] for k in kartu] == ["Beban studi", "Peringkat akreditasi", "Gelar", "Mahasiswa aktif"],
        "urutan, label, dan kartu tambahan: %r" % kartu)
    cek(("Peringkat akreditasi", "Unggul ") in kartu and ("Gelar", "S.Kom.") in kartu, "nilai kartu resmi tetap dari www: %r" % kartu)
    cek("AUN-QA" not in ti.split('<section class="pahlawan', 1)[1].split("</section>", 1)[0], "kartu yang disembunyikan tidak tampil")
    cek('lang="en">Informatics Engineering' in ti, "subjudul bawaan (nama Inggris) ditandai lang=en")
    cek('property="og:image" content="https://prodi.unsrat.ac.id/unggahan/55201/' in ti, "pratinjau tautan memakai foto latar")

    css = baca("s1informatika/warna.css")
    cek("--hero-teks: #FFFFFF;" in css and ".pahlawan--foto" in css, "warna.css: teks putih dan aturan foto")
    url = re.findall(r'url\("([^"]+)"\)', css)
    cek(len(url) == 3, "tiga ukuran foto latar di warna.css")
    for u in url:
        cek(os.path.isfile(os.path.normpath(os.path.join(pub, "s1informatika", u))), "foto latar %s harus diterbitkan" % u)
    cek("/ %s)" % tp.lapisan_foto(warna.warna_prodi(None, {"dasar": "#000099", "tulisan": "#FFFF00"})["utama_gelap"]) in css,
        "lapisan foto memakai opasitas yang dihitung")

    te = baca("s1elektro/index.html")
    cek('pahlawan--warna' in te and "--hero-latar: #F2B705;" in baca("s1elektro/warna.css")
        and "--hero-teks: %s;" % warna.GELAP in baca("s1elektro/warna.css"), "latar kuning -> teks gelap")
    cek('<p class="pahlawan__en">Teks bebas</p>' in te, "subjudul bebas tanpa lang=en")
    cek("Baik Sekali" in te, "akreditasi resmi elektro")

    tm = baca("s1mesin/index.html")
    cek("pahlawan--pucat" in tm and "<b>x</b>" not in tm and ">S1 Teknik Mesin</h1>" in tm, "pengaturan tidak sah: bawaan dipakai")
    cek("Prof." not in tm, "nilai kartu yang dipalsukan tidak pernah tampil")
    cek("--hero-latar" not in baca("s1mesin/warna.css"), "latar pucat tanpa aturan hero tambahan")

    cek(not cek_integritas.periksa(pub, lokasi.manifes())[0], "cek integritas bersih")
    # the photo file going missing: the site falls back to the default background instead of a broken one
    v = lokasi.baca("prodi/55201/situs")["beranda"]["latar"]["foto"]["varian"]["1600"]
    os.remove(os.path.join(lokasi.unggahan(), *v["jalur"].split("/")))
    b = bangun.Pembangun(hari_ini="2026-10-26")
    b.bangun("55201")
    cek("pahlawan--pucat" in baca("s1informatika/index.html") and any("foto latar" in x for x in b.peringatan),
        "foto latar hilang: latar bawaan dan peringatan")
    jumlah, temuan = periksa_situs(pub, "beranda-2")
    gagal.extend(temuan)
    print("beranda: %d halaman diperiksa" % jumlah)
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_beranda: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
