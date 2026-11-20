# -*- coding: utf-8 -*-
"""Machine translation for the English editor, Fase 5 langkah 3 (K-P37): platform/terjemah_mesin.py and the
"Terjemahkan dari versi Indonesia" button of the English editor (isi_admin.py).

- markup: links (their address never translated), bold, bare addresses, "- " lists, empty lines and escaped
  characters come back as they were; the fixed terms (official names) come out as the official data says; a
  translation that comes back broken, with other markup or with gambling text is left out;
- DeepL (with a stand-in for the network): the Free and Pro hosts, the key in the Authorization header and never in a
  message, the request (Indonesian to American English, XML tags kept), batches, every error answered with a message;
- settings: no provider, DeepL without a key, the stand-in refused in production, limits;
- use: per programme per day, the platform per month, refused beyond the limits, nothing counted for a failure;
- the admin: the button only with a provider; the draft filled and marked; a mark gone once a person changed the text;
  submitting and publishing refused until the machine's texts are confirmed checked; overwriting; the titles of a list
  kept in a spreadsheet only when asked; a failing provider changes nothing; the audit log; the superadmin's dashboard;
  the key on no page.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
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
    print("uji_terjemah_mesin: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-terjemah-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)
for v in ("TERJEMAH_PENYEDIA", "TERJEMAH_KUNCI", "TERJEMAH_BATAS_HARIAN", "TERJEMAH_BATAS_BULANAN"):
    os.environ.pop(v, None)

from urllib.error import HTTPError, URLError  # noqa: E402
from urllib.parse import parse_qs  # noqa: E402

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import isi_halaman as ih  # noqa: E402
import isi_inggris as ii  # noqa: E402
import lokasi  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
import terjemah_mesin as tm  # noqa: E402
from formulir_uji import prodi  # noqa: E402

A, B = "55201", "20201"
KUNCI_UJI = "kunci-uji-0000:fx"           # not a key of any account
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


class Jawaban(object):
    def __init__(self, isi):
        self.isi = isi

    def read(self):
        return self.isi

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Jaringan(object):
    """A stand-in for urlopen: records the requests, answers with an English stand-in or with a failure."""

    def __init__(self, gagal=None, jawaban=None):
        self.permintaan, self.gagal, self.jawaban = [], gagal, jawaban

    def __call__(self, req, timeout=None):
        self.permintaan.append(req)
        if self.gagal is not None:
            raise self.gagal
        data = parse_qs(req.data.decode("utf-8"))
        isi = self.jawaban if self.jawaban is not None else {
            "translations": [{"detected_source_language": "ID", "text": "EN:" + t} for t in data["text"]]}
        return Jawaban(json.dumps(isi).encode("utf-8"))


try:
    # ============================================================== markup and fixed terms
    glos = tm.glosarium({"nama": "Teknik Informatika", "nama_en": "Informatics Engineering", "gelar": "S.Kom.",
                         "lembaga_akreditasi": "LAM-Infokom"},
                        [{"nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering"}, {"nama": "Teknik"}], {})
    cek(glos[0] == ("Universitas Sam Ratulangi", "Sam Ratulangi University")
        and ("Teknik Informatika", "Informatics Engineering") in glos and ("S.Kom.", "S.Kom.") in glos
        and ("Teknik", "Teknik") not in glos, "glosarium dari data resmi: %r" % glos)
    for baris, harap in (
            ("Program Studi Teknik Informatika, Fakultas Teknik.",
             "Program Studi <keep>Informatics Engineering</keep>, <keep>Faculty of Engineering</keep>."),
            ("Lihat [panduan **baru**](https://unsrat.ac.id/p?a=1&b=2) dan https://x.ac.id/y.",
             'Lihat <a href="https://unsrat.ac.id/p?a=1&amp;b=2">panduan <b>baru</b></a> dan <keep>https://x.ac.id/y</keep>.'),
            ("5 < 7 & 8 > 6", "5 &lt; 7 &amp; 8 &gt; 6")):
        xml = tm.ke_xml(baris, glos)
        cek(xml == harap, "ke_xml %r: %r" % (baris, xml))
    cek(tm.dari_xml('See <a href="https://unsrat.ac.id/p?a=1&amp;b=2">the <b>new</b> guide</a> &amp; '
                    '<keep>https://x.ac.id/y</keep>.') == "See [the **new** guide](https://unsrat.ac.id/p?a=1&b=2) & https://x.ac.id/y.",
        "dari_xml mengembalikan markah")
    for salah in ("<script>x</script>", '<a href="javascript:alert(1)">x</a>', "<b>tidak ditutup", '<a href="https://a.id"><a href="https://b.id">x</a></a>'):
        try:
            tm.dari_xml(salah)
            cek(False, "dari_xml menolak %r" % salah)
        except ValueError:
            pass
    sumber = "Paragraf tentang **Teknik Informatika**.\n\n- butir [satu](https://a.id/1)\n- butir dua\nbaris tiga"
    t = tm.Tiruan()
    hasil = tm.terjemahkan(t, [sumber, "Nama"], glos)
    cek(hasil[sumber] == "(EN) Paragraf tentang **Informatics Engineering**.\n\n- (EN) butir [satu](https://a.id/1)\n"
        "- (EN) butir dua\n(EN) baris tiga" and hasil["Nama"] == "(EN) Nama" and len(t.dikirim) == 5,
        "susunan baris, daftar, dan paragraf kembali: %r" % hasil)

    class Rusak(tm.Penyedia):
        def terjemahkan(self, teks):
            return [x.replace('href="https://a.id/1"', 'href="https://lain.id"').replace("Situs", "Situs slot gacor")
                    .replace("Utuh", "<i>Utuh</i>") for x in teks]
    hasil = tm.terjemahkan(Rusak(), ["Ke [sini](https://a.id/1)", "Situs prodi", "Utuh", "Aman"])
    cek(hasil == {"Ke [sini](https://a.id/1)": None, "Situs prodi": None, "Utuh": None, "Aman": "Aman"},
        "terjemahan yang rusak atau berjudi dibuang: %r" % hasil)
    cek([len(k) for k in tm._kelompok(["x"] * 120)] == [50, 50, 20]
        and [len(k) for k in tm._kelompok(["x" * 60000] * 3)] == [1, 1, 1], "pembagian permintaan")

    # ============================================================== DeepL with a stand-in for the network
    jaringan = Jaringan()
    d = tm.DeepL(KUNCI_UJI, buka=jaringan)
    keluar = d.terjemahkan(["satu", "dua"])
    req = jaringan.permintaan[0]
    data = parse_qs(req.data.decode("utf-8"))
    cek(keluar == ["EN:satu", "EN:dua"] and req.full_url == "https://api-free.deepl.com/v2/translate"
        and req.get_header("Authorization") == "DeepL-Auth-Key %s" % KUNCI_UJI and req.get_method() == "POST"
        and data["text"] == ["satu", "dua"] and data["source_lang"] == ["ID"] and data["target_lang"] == ["EN-US"]
        and data["tag_handling"] == ["xml"] and data["ignore_tags"] == ["keep"], "permintaan DeepL Free")
    cek(tm.DeepL("kunci-pro-uji").alamat == "https://api.deepl.com/v2/translate", "kunci Pro memakai api.deepl.com")
    jaringan = Jaringan()
    tm.DeepL(KUNCI_UJI, buka=jaringan).terjemahkan(["x"] * 120)
    cek(len(jaringan.permintaan) == 3, "120 teks dalam 3 permintaan")
    for galat, harap in ((HTTPError("u", 403, "Forbidden", {}, None), "kunci API DeepL ditolak"),
                         (HTTPError("u", 456, "Quota", {}, None), "kuota karakter akun DeepL sudah habis"),
                         (HTTPError("u", 429, "Too many", {}, None), "terlalu banyak permintaan"),
                         (HTTPError("u", 418, "?", {}, None), "galat 418"),
                         (URLError("tidak ada jaringan"), "tidak dapat dihubungi")):
        try:
            tm.DeepL(KUNCI_UJI, buka=Jaringan(gagal=galat)).terjemahkan(["x"])
            cek(False, "galat %r harus menjadi GagalTerjemah" % galat)
        except tm.GagalTerjemah as e:
            cek(harap in str(e) and KUNCI_UJI not in str(e), "pesan galat DeepL: %s" % e)
    try:
        tm.DeepL(KUNCI_UJI, buka=Jaringan(jawaban={"translations": []})).terjemahkan(["x"])
        cek(False, "jawaban tidak lengkap ditolak")
    except tm.GagalTerjemah as e:
        cek("tidak lengkap" in str(e), "pesan jawaban tidak lengkap")

    # ============================================================== settings
    cek(tm.penyedia_dari_pengaturan({}) is None and isinstance(tm.penyedia_dari_pengaturan(
        {"TERJEMAH_PENYEDIA": "deepl", "TERJEMAH_KUNCI": KUNCI_UJI}), tm.DeepL)
        and isinstance(tm.penyedia_dari_pengaturan({"TERJEMAH_PENYEDIA": "tiruan"}), tm.Tiruan), "penyedia dari pengaturan")
    for env, harap in (({"TERJEMAH_PENYEDIA": "deepl"}, "memerlukan TERJEMAH_KUNCI"),
                       ({"TERJEMAH_PENYEDIA": "tiruan", "PRODI_MODE": "produksi"}, "tidak di produksi"),
                       ({"TERJEMAH_PENYEDIA": "google"}, "tidak dikenal")):
        try:
            tm.penyedia_dari_pengaturan(env)
            cek(False, "pengaturan %r ditolak" % env)
        except ValueError as e:
            cek(harap in str(e), "pesan pengaturan %r: %s" % (env, e))
    cek(tm.batas_dari_pengaturan({}) == (50000, 500000) and tm.batas_dari_pengaturan(
        {"TERJEMAH_BATAS_HARIAN": "10", "TERJEMAH_BATAS_BULANAN": "20"}) == (10, 20), "batas dari pengaturan")
    try:
        tm.batas_dari_pengaturan({"TERJEMAH_BATAS_HARIAN": "banyak"})
        cek(False, "batas bukan angka ditolak")
    except ValueError:
        pass
    try:
        app_mod.buat_app({"SECRET_KEY": "k" * 64, "TERJEMAH_PENYEDIA": "deepl"})
        cek(False, "admin tidak berjalan dengan pengaturan terjemahan yang tidak sah")
    except SystemExit as e:
        cek("TERJEMAH_KUNCI" in str(e), "pesan admin: %s" % e)

    # ============================================================== use
    os.makedirs(os.environ["WWW_DATA"])
    pa = dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering")
    for nama, isi_ in {"prodi": {"program": [pa, prodi(B, "Teknik Elektro")]},
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
    tm.catat_pemakaian(B, 300, "2026-11-19")
    tm.catat_pemakaian(B, 200, "2026-11-20")
    tm.catat_pemakaian(B, 50, "2026-10-31")
    cek(tm.pemakaian(B) == {"hari": {"2026-10-31": 50, "2026-11-19": 300, "2026-11-20": 200},
                            "bulan": {"2026-10": 50, "2026-11": 500}}
        and tm.pakai_bulan_ini([A, B], "2026-11-20") == 500, "pemakaian per hari dan per bulan")
    for n, batas, harap in ((100, (250, 1000), "prodi ini hari ini"), (100, (1000, 550), "semua prodi bulan ini")):
        try:
            tm.periksa_batas(B, n, [A, B], batas, "2026-11-20")
            cek(False, "batas %r" % (batas,))
        except tm.GagalTerjemah as e:
            cek(harap in str(e), "pesan batas: %s" % e)
    tm.periksa_batas(B, 50, [A, B], (250, 1000), "2026-11-20")
    for i in range(40):
        tm.catat_pemakaian(A, 1, "2026-12-%02d" % (i % 28 + 1) if i < 28 else "2027-01-%02d" % (i - 27))
    cek(len(tm.pemakaian(A)["hari"]) == 31, "pemakaian harian disimpan 31 hari")
    lokasi.tulis_json(lokasi.path_data(tm.berkas_pemakaian(A)), {})

    # ============================================================== the admin
    ih.terbitkan(A, "sejarah", {"uraian": "Program Studi Teknik Informatika berdiri tahun 1990.", "linimasa": [
        {"tahun": 1990, "peristiwa": "Didirikan"}, {"tahun": 2010, "peristiwa": "Akreditasi pertama"}]}, "penguji")
    judul = [{"judul": "Sistem Informasi Desa %d" % i, "tahun": 2024} for i in range(3)]
    ih.terbitkan(A, "tugas-akhir", {"uraian": "Judul tugas akhir.", "daftar": judul}, "penguji")
    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran, p in (("adma", "admin", [A]), ("opa", "operator", [A])):
        akun_baru(nama, peran, p, super_)

    def klien(app, nama, ip):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = ip
        c.get("/masuk")
        with c.session_transaction() as s_:
            token = s_["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302,
            "%s masuk" % nama)
        return c

    def kirim(c, url, **data):
        with c.session_transaction() as s_:
            data["csrf"] = s_["csrf"]
        return c.post(url, data=data)
    E = "/prodi/%s/halaman/sejarah/en" % A

    def versi():
        return {"versi": str(ih.baca(A, "sejarah:en").get("versi", 0)), "versi_id": str(ih.baca(A, "sejarah")["versi"])}

    # without a provider: no button, the action refused
    tanpa = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    ko = klien(tanpa, "opa", "103.84.116.70")
    cek("Terjemahan mesin" not in ko.get(E).get_data(as_text=True)
        and kirim(ko, E, aksi="terjemahkan", **versi()).status_code == 400, "tanpa penyedia: tanpa tombol terjemahan mesin")

    # with the stand-in provider and its limits
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron",
                            "TERJEMAH_PENYEDIA": "tiruan", "TERJEMAH_BATAS_HARIAN": "1000"})
    ko, ka, ks = klien(app, "opa", "103.84.116.61"), klien(app, "adma", "103.84.116.62"), klien(app, "superuji", "103.84.116.63")
    teks = ko.get(E).get_data(as_text=True)
    cek("Terjemahan mesin (Tiruan)" in teks and "<strong>3 teks</strong>" in teks and "Sisa batas terjemahan mesin prodi ini hari ini: 1000"
        in teks and 'value="terjemahkan"' in teks, "kotak terjemahan mesin dengan perkiraan")
    r = kirim(ko, E, aksi="terjemahkan", **dict(versi(), **{"t." + ih.kunci_teks("Didirikan"): "Founded"}))
    en = ih.draf(ih.baca(A, "sejarah:en"))["isi"]
    cek(r.status_code == 302 and en["teks"]["Didirikan"] == "Founded"
        and en["teks"]["Program Studi Teknik Informatika berdiri tahun 1990."] ==
        "(EN) Program Studi Informatics Engineering berdiri tahun 1990."
        and en["teks"]["Akreditasi pertama"] == "(EN) Akreditasi pertama" and en["asal"]["uraian"]
        and sorted(en["mesin"]) == ["Akreditasi pertama", "Program Studi Teknik Informatika berdiri tahun 1990."],
        "draf diisi terjemahan mesin, ketikan sendiri tetap: %r" % en)
    pakai = tm.pemakaian(A)["hari"].get(tm.hari_ini(), 0)
    cek(pakai == len("Program Studi Teknik Informatika berdiri tahun 1990.") + len("Akreditasi pertama"), "pemakaian dicatat: %r" % pakai)
    teks = ko.get(E).get_data(as_text=True)
    cek(teks.count('class="keterangan terjemah__mesin"') == 2 and "Saya sudah memeriksa 2 terjemahan mesin" in teks
        and "2 teks diterjemahkan mesin" in teks, "tanda terjemahan mesin di formulir")
    cek("<strong>1</strong> halaman dengan terjemahan mesin belum diperiksa" in ko.get("/prodi/%s/" % A).get_data(as_text=True),
        "dasbor prodi: halaman dengan terjemahan mesin yang belum diperiksa")
    r = kirim(ko, E, aksi="ajukan", **dict(versi(), **{
        "t." + ih.kunci_teks("Program Studi Teknik Informatika berdiri tahun 1990."): "(EN) Program Studi Informatics Engineering berdiri tahun 1990.",
        "t." + ih.kunci_teks("Akreditasi pertama"): "First accreditation"}))
    d = ih.draf(ih.baca(A, "sejarah:en"))
    cek(r.status_code == 302 and d["status"] == "draf" and d["isi"]["mesin"] == ["Program Studi Teknik Informatika berdiri tahun 1990."]
        and "1 terjemahan mesin belum diperiksa" in ko.get(E).get_data(as_text=True),
        "pengajuan ditolak sebelum terjemahan mesin diperiksa; teks yang diubah dianggap sudah diperiksa")
    try:
        ih.terbitkan(A, "sejarah:en", d["isi"], "penguji")
        cek(False, "terjemahan mesin yang belum diperiksa tidak pernah terbit")
    except ih.GagalIsi:
        pass
    r = kirim(ko, E, aksi="ajukan", periksa_mesin="1", **versi())
    d = ih.draf(ih.baca(A, "sejarah:en"))
    cek(r.status_code == 302 and d["status"] == "menunggu" and "mesin" not in d["isi"], "diajukan setelah dicentang diperiksa")
    kirim(ka, E, aksi="terbitkan", **versi())
    cek(ih.terbit(A, "sejarah:en") is not None and "mesin" not in ih.terbit(A, "sejarah:en"), "admin menerbitkan")

    # overwriting, the titles of a spreadsheet list, the limits, a failing provider
    r = kirim(ka, E, aksi="terjemahkan", timpa="1", **versi())
    en = ih.draf(ih.baca(A, "sejarah:en"))["isi"]
    cek(r.status_code == 302 and en["teks"]["Akreditasi pertama"] == "(EN) Akreditasi pertama" and len(en["mesin"]) == 3,
        "terjemahkan ulang menimpa terjemahan yang ada")
    kirim(ka, E, aksi="buang", **versi())
    T = "/prodi/%s/halaman/tugas-akhir/en" % A
    v_ta = {"versi": "0", "versi_id": str(ih.baca(A, "tugas-akhir")["versi"])}
    teks = ka.get(T).get_data(as_text=True)
    cek("Terjemahkan juga 3 judul di tabel Excel" in teks, "pilihan judul tabel Excel")
    kirim(ka, T, aksi="terjemahkan", **v_ta)
    en = ih.draf(ih.baca(A, "tugas-akhir:en"))["isi"]
    cek(list(en["teks"]) == ["Judul tugas akhir."], "tanpa pilihan: judul tabel Excel tidak diterjemahkan")
    v_ta["versi"] = str(ih.baca(A, "tugas-akhir:en")["versi"])
    kirim(ka, T, aksi="terjemahkan", excel="1", **v_ta)
    en = ih.draf(ih.baca(A, "tugas-akhir:en"))["isi"]
    cek(en["teks"].get("Sistem Informasi Desa 2") == "(EN) Sistem Informasi Desa 2" and len(en["mesin"]) == 4,
        "dengan pilihan: judul tabel Excel diterjemahkan")
    sebelum = dict(tm.pemakaian(A)["hari"])
    app.penerjemah.gagal = "kuota karakter akun DeepL sudah habis untuk periode ini"
    r = kirim(ka, E, aksi="terjemahkan", timpa="1", **dict(versi(), **{"t." + ih.kunci_teks("Didirikan"): "Founded in 1990"}))
    teks = ka.get(E).get_data(as_text=True)
    cek(r.status_code == 302 and "Terjemahan mesin tidak dijalankan: kuota karakter" in teks
        and ih.draf(ih.baca(A, "sejarah:en"))["isi"]["teks"]["Didirikan"] == "Founded in 1990"
        and tm.pemakaian(A)["hari"] == sebelum, "penyedia gagal: ketikan tetap tersimpan, tanpa pemakaian")
    app.penerjemah.gagal = None
    r = kirim(ka, E, aksi="terjemahkan", **versi())
    cek(r.status_code == 302 and "semua teks halaman ini sudah diterjemahkan" in ka.get(E).get_data(as_text=True)
        and tm.pemakaian(A)["hari"] == sebelum, "tanpa teks yang perlu diterjemahkan: tidak ada yang dikirim")
    lokasi.tulis_json(lokasi.path_data(tm.berkas_pemakaian(A)), {"hari": {tm.hari_ini(): 990}, "bulan": {}})
    r = kirim(ka, E, aksi="terjemahkan", timpa="1", **versi())
    cek("batas terjemahan mesin prodi ini hari ini tercapai" in ka.get(E).get_data(as_text=True)
        and "mesin" not in ih.draf(ih.baca(A, "sejarah:en"))["isi"], "batas harian prodi")
    log = ks.get("/super/audit").get_data(as_text=True)
    cek("isi-en-terjemahan-mesin" in log, "terjemahan mesin tercatat di log audit")
    teks = ks.get("/").get_data(as_text=True)
    cek("Terjemahan mesin (Tiruan) bulan ini" in teks and "dari 500.000 karakter" in teks, "dasbor superadmin: pemakaian")

    # the key on no page
    dengan_kunci = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati",
                                     "TERJEMAH_PENYEDIA": "deepl", "TERJEMAH_KUNCI": KUNCI_UJI})
    kk, kks = klien(dengan_kunci, "adma", "103.84.116.64"), klien(dengan_kunci, "superuji", "103.84.116.65")
    halaman_ = [kk.get(E).get_data(as_text=True), kks.get("/").get_data(as_text=True),
                kks.get("/super/audit").get_data(as_text=True)]
    cek("Terjemahan mesin (DeepL)" in halaman_[0] and not any(KUNCI_UJI in h for h in halaman_),
        "kunci API tidak tampil di halaman admin")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_terjemah_mesin: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
