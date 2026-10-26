# -*- coding: utf-8 -*-
"""Step 2 of phase 1: pulling the official data from www (tarik_www.py), the registry (registri.py), the version
history (riwayat.py) and the data paths (lokasi.py).

Runs on a small made-up www data folder in a temporary directory, so it needs neither the www checkout nor any
package outside the standard library. When the www checkout sits next to this repository, a full pull of its real
data is checked as well.
"""
from __future__ import print_function

import copy
import io
import json
import os
import shutil
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AKAR, "platform"))

KERJA = tempfile.mkdtemp(prefix="prodi-uji-data-")
WWW = os.path.join(KERJA, "www")
os.environ["PRODI_DATA"] = os.path.join(KERJA, "data")
os.environ["PRODI_RIWAYAT"] = os.path.join(KERJA, "riwayat")
os.environ["WWW_DATA"] = WWW

import lokasi  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import tarik_www  # noqa: E402

# www's real data: the sibling checkout on a developer's machine, else the starting copy shipped with this repository
# (platform/data-awal/www/, impor_www.py), so these checks run inside the Docker image too
WWW_ASLI = os.path.join(os.path.dirname(AKAR), "website-unsrat-2026", "site", "mockup", "data")
if not os.path.isfile(os.path.join(WWW_ASLI, "prodi.json")):
    WWW_ASLI = os.path.join(AKAR, "platform", "data-awal", "www")

gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def harus_gagal(fungsi, pesan, *args, **kw):
    try:
        fungsi(*args, **kw)
    except (tarik_www.GagalTarik, registri.GagalRegistri, ValueError) as e:
        return e
    gagal.append(pesan)
    return None


def prodi(kode, nama, jenjang="S1", cpl=2, **lain):
    p = {"kode_pddikti": kode, "nama": nama, "nama_asli": nama.upper(), "nama_en": nama + " (EN)", "jenjang": jenjang,
         "gelar": "S.T.", "sks": 144, "unit_kode": "ft", "unit": "Fakultas Teknik", "website": "", "surel": "a@unsrat.ac.id",
         "bidang_kerja": "Bidang kerja.", "bidang_kerja_en": "", "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Teknik",
         "berlaku_hingga": "2030-01-01", "internasional": "", "slug": "s1-" + nama.lower().replace(" ", "-"),
         "slug_en": "", "terjemahan_diperiksa": False,
         "cpl": [{"kode": "CPL %d" % i, "isi": "Capaian %d." % i, "isi_en": "", "kurikulum": "2025/2026"} for i in range(1, cpl + 1)]}
    p.update(lain)
    return p


AWAL = {
    "prodi": {"jumlah": 3, "tampilkan_berlaku_hingga": False, "program": [
        prodi("55201", "Teknik Informatika"), prodi("20201", "Teknik Elektro"), prodi("21201", "Teknik Mesin", cpl=0)]},
    "unit": {"catatan": "", "unit": [{"kode": "ft", "nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering",
                                      "jenis": "fakultas", "website": "", "surel": "", "bendera": {"dasar": "#0000ff"},
                                      "pimpinan": [{"peran": "Dekan", "nama": "Seseorang"}]}]},
    "kalender": {"judul": "Kalender akademik", "teks": "", "semester": []},
    "situs": {"identitas": {"nama": {"id": "Universitas Sam Ratulangi"}}, "kontak": {"surel": "r@unsrat.ac.id"},
              "media_sosial": [{"nama": "Instagram", "url": "https://instagram.com/x"}, {"nama": "Jahat", "url": "javascript:x"}],
              "utilitas": {"id": [{"label": "PMB", "href": "https://regmaba.unsrat.ac.id"},
                                  {"label": "Pengumuman", "href": "pengumuman.html"}]},
              "menu": {"id": []}},
}


def tulis_www(isi):
    os.makedirs(WWW, exist_ok=True)
    for nama, data in isi.items():
        with io.open(os.path.join(WWW, nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)


def tulis_csv(baris):
    path = os.path.join(KERJA, "slug.csv")
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n")
        for kode, jenjang, nama, slug in baris:
            f.write("%s,%s,%s,Fakultas Teknik,%s,https://prodi.unsrat.ac.id/%s/,x\n" % (kode, jenjang, nama, slug, slug))
    return path


try:
    # --- lokasi: only known data file names, never a path outside the data folder
    for nama in ("../x", "warisan/../registri", "prodi/55201/../../x", "prodi/55201/Situs", "konten/berita", ""):
        harus_gagal(lokasi.path_data, "nama berkas %r harus ditolak" % nama, nama)
    cek(lokasi.path_data("prodi/55201/situs").startswith(lokasi.data()), "path_data harus di dalam PRODI_DATA")

    # --- first pull
    tulis_www(AWAL)
    hasil = tarik_www.pratinjau()
    cek(hasil["laporan"]["pertama"], "tarikan pertama harus ditandai pertama")
    cek(lokasi.baca("warisan/prodi") is None, "pratinjau tidak boleh menulis")
    tarik_www.terapkan("penguji")
    w = lokasi.baca("warisan/prodi")
    cek(len(w["program"]) == 3, "tarikan pertama harus memuat 3 prodi")
    p = {x["kode_pddikti"]: x for x in w["program"]}["55201"]
    cek("nama_asli" not in p and "terjemahan_diperiksa" not in p, "kolom di luar FIELD_PRODI tidak boleh disalin")
    cek(set(p) == set(tarik_www.FIELD_PRODI), "kolom prodi harus tepat FIELD_PRODI")
    cek("pimpinan" not in lokasi.baca("warisan/unit")["unit"][0], "data pimpinan fakultas tidak boleh disalin")
    cek(lokasi.baca("warisan/meta")["oleh"] == "penguji", "meta harus mencatat penarik")
    uni = lokasi.baca("warisan/universitas")
    cek(set(uni) == set(tarik_www.FIELD_SITUS), "dari situs.json hanya FIELD_SITUS yang disalin: %r" % sorted(uni))
    cek([t["label"] for t in uni["utilitas"]] == ["PMB"], "tautan utilitas relatif www tidak boleh disalin")
    cek([m["nama"] for m in uni["media_sosial"]] == ["Instagram"], "media sosial tanpa https tidak boleh disalin")
    lap = tarik_www.pratinjau()["laporan"]
    cek(not tarik_www.ada_perubahan(lap), "tarikan ulang tanpa perubahan harus kosong: %r" % lap)
    cek(lap["kekurangan"].get("21201") == ["CPL"], "prodi tanpa CPL harus dilaporkan kurang CPL")
    cek(tarik_www.kekurangan({"akreditasi": "belum", "cpl": [1], "lembaga_akreditasi": "x", "gelar": "x", "sks": 1,
                              "surel": "x", "bidang_kerja": "x", "nama_en": "x"}) == ["status akreditasi"],
        "akreditasi 'belum' dihitung sebagai data kosong")
    cek(lap["belum_terdaftar"] == ["20201", "21201", "55201"], "semua prodi belum terdaftar sebelum registri")

    # --- registry from a slug list
    harus_gagal(registri.siapkan_dari_csv, "kode yang tidak ada di data resmi harus ditolak", "penguji",
                tulis_csv([("55201", "S1", "Teknik Informatika", "s1informatika"), ("99999", "S1", "Fiktif", "s1fiktif")]))
    harus_gagal(registri.siapkan_dari_csv, "slug ganda harus ditolak", "penguji",
                tulis_csv([("55201", "S1", "Teknik Informatika", "s1informatika"), ("20201", "S1", "Teknik Elektro", "s1informatika")]))
    harus_gagal(registri.siapkan_dari_csv, "jenjang yang tidak cocok harus ditolak", "penguji",
                tulis_csv([("55201", "S2", "Teknik Informatika", "s2informatika")]))
    cek(lokasi.baca("registri") is None, "registri yang gagal tidak boleh tertulis")
    n = registri.siapkan_dari_csv("penguji", tulis_csv([("55201", "S1", "Teknik Informatika", "s1informatika"),
                                                       ("20201", "S1", "Teknik Elektro", "s1elektro")]))
    cek(n == 2, "registri awal harus mendaftarkan 2 prodi")
    cek(registri.siapkan_dari_csv("penguji") == 0, "registri yang sudah ada tidak boleh ditimpa")
    cek(lokasi.baca("prodi/55201/situs") == registri.situs_bawaan(), "situs.json bawaan harus dibuat")
    cek(tarik_www.pratinjau()["laporan"]["belum_terdaftar"] == ["21201"], "21201 harus tetap belum terdaftar")

    # --- registering, slugs and settings
    harus_gagal(registri.daftarkan, "slug milik prodi lain harus ditolak", "21201", "s1elektro", "penguji")
    harus_gagal(registri.daftarkan, "slug dengan jenjang salah harus ditolak", "21201", "s2mesin", "penguji")
    harus_gagal(registri.daftarkan, "prodi yang tidak ada harus ditolak", "88888", "s1apa", "penguji")
    registri.daftarkan("21201", "s1mesin", "penguji")
    harus_gagal(registri.daftarkan, "mendaftar dua kali harus ditolak", "21201", "s1mesin2", "penguji")
    registri.ganti_slug("55201", "s1ti", "penguji")
    r = registri.cari(registri.baca(), "55201")
    cek(r["slug"] == "s1ti" and r["slug_lama"] == ["s1informatika"], "slug lama harus disimpan: %r" % r)
    cek(registri.cari_slug(registri.baca(), "s1informatika") == (r, True), "slug lama harus tetap ditemukan")
    harus_gagal(registri.ganti_slug, "slug lama prodi lain tidak boleh dipakai", "20201", "s1informatika", "penguji")
    registri.ganti_slug("55201", "s1informatika", "penguji")
    r = registri.cari(registri.baca(), "55201")
    cek(r["slug"] == "s1informatika" and r["slug_lama"] == ["s1ti"], "kembali ke slug lama: %r" % r)
    registri.atur("55201", "penguji", dosen_url="https://dosen.unsrat.ac.id/prodi/s1-teknik-informatika")
    for buruk in ("http://dosen.unsrat.ac.id/x", "https://dosen.unsrat.ac.id.jahat.com/x", "javascript:alert(1)",
                  "https://dosen.unsrat.ac.id/x\"onmouseover=1"):
        harus_gagal(registri.atur, "tautan dosen %r harus ditolak" % buruk, "55201", "penguji", dosen_url=buruk)
    registri.atur("20201", "penguji", aktif=False)
    cek(registri.cari(registri.baca(), "20201")["aktif"] is False, "prodi harus bisa dinonaktifkan")

    # --- changes in www are reported, and the history keeps the previous copy
    berubah = copy.deepcopy(AWAL)
    ti = berubah["prodi"]["program"][0]
    ti["akreditasi"] = "Baik Sekali"
    ti["cpl"][0]["isi"] = "Capaian satu yang baru."
    ti["cpl"].append({"kode": "CPL 9", "isi": "Tambahan.", "isi_en": "", "kurikulum": "2025/2026"})
    berubah["prodi"]["program"].append(prodi("26201", "Teknik Industri"))
    tulis_www(berubah)
    lap = tarik_www.terapkan("penguji")
    beda = lap["berubah"].get("55201", [])
    cek(any(b.startswith("akreditasi:") for b in beda), "perubahan akreditasi harus dilaporkan: %r" % beda)
    cek("CPL diubah: CPL 1" in beda and "CPL ditambah: CPL 9" in beda, "perubahan CPL harus dilaporkan: %r" % beda)
    cek(lap["baru"] == ["26201"] and "26201" in lap["belum_terdaftar"], "prodi baru di www harus dilaporkan")
    versi = [v for v in riwayat.daftar() if v["berkas"] == "warisan/prodi"]
    cek(len(versi) == 1, "salinan lama warisan/prodi harus masuk riwayat")
    riwayat.pulihkan("warisan/prodi", versi[0]["versi"], "penguji", "uji")
    cek(len(lokasi.baca("warisan/prodi")["program"]) == 3, "pemulihan versi harus mengembalikan salinan lama")
    tarik_www.terapkan("penguji")

    # --- a programme that disappears is kept and marked; when it returns the mark goes
    hilang = copy.deepcopy(berubah)
    hilang["prodi"]["program"] = [x for x in hilang["prodi"]["program"] if x["kode_pddikti"] != "21201"]
    tulis_www(hilang)
    lap = tarik_www.pratinjau()["laporan"]
    cek(lap["hilang"] == ["21201"], "prodi hilang harus dilaporkan")
    cek(lap["hilang_terlalu_banyak"], "1 dari 4 prodi hilang melewati batas 10%")
    harus_gagal(tarik_www.terapkan, "terlalu banyak yang hilang harus ditolak tanpa paksa", "penguji")
    tarik_www.terapkan("penguji", paksa=True)
    tetap = {x["kode_pddikti"]: x for x in lokasi.baca("warisan/prodi")["program"]}
    cek("21201" in tetap and tetap["21201"].get("hilang_dari_www"), "prodi hilang harus tetap ada dan ditandai")
    cek(not tarik_www.ada_perubahan(tarik_www.pratinjau()["laporan"]), "tanda hilang tidak boleh dilaporkan ulang")
    tulis_www(berubah)
    lap = tarik_www.terapkan("penguji")
    cek(lap["kembali"] == ["21201"], "prodi yang muncul lagi harus dilaporkan kembali")
    cek(not any(x.get("hilang_dari_www") for x in lokasi.baca("warisan/prodi")["program"]), "tanda hilang harus dihapus")

    # --- a broken or tampered source is refused as a whole and nothing is written
    sebelum = lokasi.baca("warisan/prodi")
    buruk = [
        ("judi di CPL", lambda d: d["prodi"]["program"][0]["cpl"][0].update(isi="Daftar slot gacor di sini")),
        ("judi dengan huruf samaran", lambda d: d["prodi"]["program"][1].update(bidang_kerja="situs s1ot g4cor")),
        ("judi di kalender", lambda d: d["kalender"].update(teks="togel online")),
        ("kode PDDIKTI ganda", lambda d: d["prodi"]["program"][1].update(kode_pddikti="55201")),
        ("kode PDDIKTI berbahaya", lambda d: d["prodi"]["program"][1].update(kode_pddikti="../../x")),
        ("nama kosong", lambda d: d["prodi"]["program"][0].update(nama="")),
        ("jenjang tak dikenal", lambda d: d["prodi"]["program"][0].update(jenjang="D3")),
        ("sks bukan angka", lambda d: d["prodi"]["program"][0].update(sks="banyak")),
        ("tanggal salah", lambda d: d["prodi"]["program"][0].update(berlaku_hingga="besok")),
        ("cpl tanpa isi", lambda d: d["prodi"]["program"][0]["cpl"].append({"kode": "CPL X"})),
        ("unit tidak dikenal", lambda d: d["prodi"]["program"][0].update(unit_kode="fx")),
        ("daftar program kosong", lambda d: d["prodi"].update(program=[])),
        ("kalender rusak", lambda d: d.update(kalender=[])),
        ("judi di kontak universitas", lambda d: d["situs"]["kontak"].update(surel="maxwin88@gacor.id slot")),
        ("situs tanpa kontak", lambda d: d["situs"].pop("kontak")),
    ]
    for label, ubah in buruk:
        d = copy.deepcopy(berubah)
        ubah(d)
        tulis_www(d)
        e = harus_gagal(tarik_www.terapkan, "sumber dengan %s harus ditolak" % label, "penguji")
        if e is not None and label.startswith("judi"):
            cek(any("teks judi" in m for m in e.masalah), "%s harus ditolak karena teks judi: %r" % (label, e.masalah))
        cek(lokasi.baca("warisan/prodi") == sebelum, "sumber dengan %s tidak boleh menulis apa pun" % label)
    with io.open(os.path.join(WWW, "prodi.json"), "w", encoding="utf-8") as f:
        f.write("{bukan json")
    harus_gagal(tarik_www.terapkan, "JSON rusak harus ditolak", "penguji")
    shutil.rmtree(WWW)
    harus_gagal(tarik_www.terapkan, "folder www yang tidak ada harus ditolak", "penguji")
    cek(tarik_www.main(["--terapkan"]) == 1, "baris perintah harus keluar dengan kode 1 saat gagal")

    # --- the real www data, when the checkout is there
    if os.path.isfile(os.path.join(WWW_ASLI, "prodi.json")):
        os.environ["PRODI_DATA"] = os.path.join(KERJA, "data-asli")
        hasil = tarik_www.pratinjau(WWW_ASLI)
        cek(len(hasil["prodi"]["program"]) == 97, "data www asli harus memuat 97 prodi")
        tarik_www.terapkan("penguji", WWW_ASLI)
        cek(registri.siapkan_dari_csv("penguji") == 97, "registri dari slug.csv harus mendaftarkan 97 prodi")
        cek(tarik_www.pratinjau(WWW_ASLI)["laporan"]["belum_terdaftar"] == [], "semua prodi www harus terdaftar")
        cek(len(os.listdir(os.path.join(lokasi.data(), "prodi"))) == 97, "97 situs.json harus dibuat")
        print("data www asli: 97 prodi ditarik dan didaftarkan")
    else:
        print("data www asli tidak ditemukan, bagian itu dilewati")
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_data: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
