# -*- coding: utf-8 -*-
""""Terjemahkan semua", Fase 5 langkah 5a (K-P37): platform/admin/terjemah_semua.py, the review filters of the lists of
pages and announcements, and the English editor's "... dan buka berikutnya" buttons (isi_admin.py).

- without a provider: no button, the job refused;
- the plan: pages in menu order whose Indonesian working content (published or a draft) has untranslated texts,
  without the lists kept in spreadsheets and the hidden pages; an English draft waiting for approval left out; the
  announcements the account may change, never withdrawn ones; nothing overwritten;
- an operator's job: English drafts marked "mesin", their status kept, typed translations kept, its own announcements
  only; usage counted; the audit log; the result page; nothing left to translate afterwards;
- an admin's job: every announcement; limits (an item that does not fit waits, a smaller one goes on); a failing
  provider stops the job and changes nothing; a page changed while it was translated is left as the other person
  saved it;
- the background mode: the page shows the progress and reloads itself, a second job is refused while one runs;
- the review: the lists' filters, the dashboard's links, "Ajukan dan buka berikutnya" / "Terbitkan dan buka
  berikutnya" from page to page until none is left.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import flask  # noqa: F401
except ImportError:
    print("uji_terjemahkan_semua: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-terjemahkan-semua-")
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
import isi_halaman as ih  # noqa: E402
import isi_inggris as ii  # noqa: E402
import pengumuman as pg  # noqa: E402
import registri  # noqa: E402
import tampilan_prodi as tp  # noqa: E402
import tarik_www  # noqa: E402
import terjemah_mesin as tm  # noqa: E402
from formulir_uji import prodi  # noqa: E402

A = "55201"
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def en_draf(id_):
    return ih.draf(ih.baca(A, id_ + ":en"))


try:
    # ============================================================== a programme with pages and announcements
    os.makedirs(os.environ["WWW_DATA"])
    pa = dict(prodi(A, "Teknik Informatika"), nama_en="Informatics Engineering")
    for nama, isi_ in {"prodi": {"program": [pa]},
                       "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "nama_en": "Faculty of Engineering",
                                          "jenis": "fakultas", "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                       "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi_, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n" % A)
    registri.siapkan_dari_csv("penguji", path_csv)
    registri.atur(A, "penguji", inggris=True)        # the English version exists only when switched on (K-P38)

    # published, with one text translated by hand
    ih.terbitkan(A, "sejarah", {"uraian": "Prodi berdiri tahun 1990.", "linimasa": [
        {"tahun": 1990, "peristiwa": "Prodi didirikan"}, {"tahun": 2010, "peristiwa": "Akreditasi pertama"}]}, "penguji")
    ih.terbitkan(A, "sejarah:en", {"teks": {"Prodi didirikan": "The study program was founded"}, "asal": {}}, "penguji")
    # an Indonesian draft only
    ih.simpan_draf(A, "penjaminan-mutu", {"uraian": "Sistem penjaminan mutu internal prodi."}, "opa")
    # fully translated already
    ih.terbitkan(A, "peraturan", {"uraian": "Peraturan akademik."}, "penguji")
    ih.terbitkan(A, "peraturan:en", {"teks": {"Peraturan akademik.": "Academic regulations."},
                                     "asal": {"uraian": "Peraturan akademik."}}, "penguji")
    # an English version waiting for approval, and an Indonesian draft with a new field since (a changed text keeps
    # its old translation, marked to be updated: only texts without any translation are sent to the machine)
    ih.terbitkan(A, "survei-kepuasan", {"uraian": "Survei kepuasan mahasiswa."}, "penguji")
    ih.ajukan(A, "survei-kepuasan:en", {"teks": {"Survei kepuasan mahasiswa.": "Student satisfaction survey."},
                                        "asal": {"uraian": "Survei kepuasan mahasiswa."}}, "opa")
    ih.simpan_draf(A, "survei-kepuasan", {"uraian": "Survei kepuasan mahasiswa.",
                                          "tindak_lanjut": "Tindak lanjut hasil survei."}, "opa")
    # a list kept in a spreadsheet
    ih.terbitkan(A, "tugas-akhir", {"uraian": "Judul tugas akhir mahasiswa.",
                                    "daftar": [{"judul": "Sistem Informasi Desa %d" % i, "tahun": 2024} for i in range(3)]},
                 "penguji")
    # a hidden optional page
    ih.terbitkan(A, "jadwal", {"uraian": "Jadwal kuliah semester ini."}, "penguji")
    tp.atur(A, {"menu": {"jadwal": {"sembunyi": True}}}, "penguji")

    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    for nama, peran in (("adma", "admin"), ("opa", "operator"), ("opc", "operator")):
        akun_baru(nama, peran, [A], super_)
    K1 = pg.tambah(A, {"judul": "Jadwal ujian", "kategori": "akademik", "tanggal": "2026-11-10",
                       "ringkasan": "Jadwal ujian semester.", "isi": "Ujian dimulai Senin."}, "opa", "draf")
    K2 = pg.tambah(A, {"judul": "Kuliah umum", "kategori": "kegiatan", "tanggal": "2026-11-08",
                       "ringkasan": "Kuliah umum bersama praktisi."}, "adma", "terbit")
    K3 = pg.tambah(A, {"judul": "Pengumuman lama", "kategori": "akademik", "tanggal": "2026-10-01",
                       "ringkasan": "Sudah tidak berlaku."}, "adma", "ditarik")
    K4 = pg.tambah(A, {"judul": "Seminar", "kategori": "kegiatan", "tanggal": "2026-11-09",
                       "ringkasan": "Seminar nasional."}, "opc", "draf")

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
    T = "/prodi/%s/terjemahkan-semua" % A
    L = "/prodi/%s/halaman" % A

    # ============================================================== without a provider
    tanpa = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    ko = klien(tanpa, "opa", "103.84.116.70")
    teks = ko.get(T).get_data(as_text=True)
    cek("belum disambungkan" in teks and "Ya, terjemahkan semua" not in teks
        and ">Terjemahkan semua</a>" not in ko.get(L).get_data(as_text=True)
        and kirim(ko, T).status_code == 400, "tanpa penyedia: tanpa tombol, pekerjaan ditolak")

    # ============================================================== an operator's job
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron",
                            "TERJEMAH_PENYEDIA": "tiruan", "TERJEMAH_BATAS_HARIAN": "100000"})
    ko, ka, ks = klien(app, "opa", "103.84.116.61"), klien(app, "adma", "103.84.116.62"), klien(app, "superuji", "103.84.116.63")
    cek(">Terjemahkan semua</a>" in ko.get(L).get_data(as_text=True)
        and ">Terjemahkan semua</a>" in ka.get("/prodi/%s/" % A).get_data(as_text=True)
        and ">Terjemahkan semua</a>" in ko.get("/prodi/%s/pengumuman" % A).get_data(as_text=True),
        "tombol Terjemahkan semua di daftar halaman, Ringkasan, dan daftar pengumuman")
    teks = ko.get(T).get_data(as_text=True)
    urutan = [teks.find(x) for x in (">Sejarah<", ">Penjaminan Mutu<", ">Tugas Akhir<", ">Jadwal ujian<")]
    cek(all(i > 0 for i in urutan) and urutan == sorted(urutan) and "Ya, terjemahkan semua" in teks
        and "<strong>3 halaman</strong> dan <strong>1 pengumuman</strong>" in teks
        and ">Peraturan<" not in teks and ">Jadwal Kuliah" not in teks and "Kuliah umum" not in teks
        and "Seminar" not in teks and "Pengumuman lama" not in teks
        and "Survei Kepuasan</a>: versi Inggrisnya menunggu persetujuan admin prodi" in teks,
        "rencana operator: halaman menurut menu, pengumumannya sendiri, yang dilewati")
    sumber_sejarah = ["Prodi berdiri tahun 1990.", "Akreditasi pertama"]
    harap_karakter = sum(map(len, sumber_sejarah + ["Sistem penjaminan mutu internal prodi.", "Judul tugas akhir mahasiswa.",
                                                    "Jadwal ujian", "Jadwal ujian semester.", "Ujian dimulai Senin."]))
    r = kirim(ko, T)
    cek(r.status_code == 302 and r.headers["Location"].endswith(T), "pekerjaan dijalankan")
    sej = en_draf("sejarah")
    cek(sej and sej["status"] == "draf" and sej["isi"]["teks"]["Prodi didirikan"] == "The study program was founded"
        and sej["isi"]["teks"]["Prodi berdiri tahun 1990."] == "(EN) Prodi berdiri tahun 1990."
        and sorted(sej["isi"]["mesin"]) == sorted(sumber_sejarah), "sejarah: terjemahan mesin, ketikan sendiri tetap: %r" % sej)
    pm = en_draf("penjaminan-mutu")
    cek(pm and pm["isi"]["teks"] == {"Sistem penjaminan mutu internal prodi.": "(EN) Sistem penjaminan mutu internal prodi."},
        "draf Indonesia ikut diterjemahkan")
    ta = en_draf("tugas-akhir")
    cek(ta and list(ta["isi"]["teks"]) == ["Judul tugas akhir mahasiswa."], "judul tabel Excel tidak ikut: %r" % (ta or {}).get("isi"))
    cek(en_draf("survei-kepuasan")["status"] == "menunggu" and en_draf("survei-kepuasan")["isi"]["teks"] == {
        "Survei kepuasan mahasiswa.": "Student satisfaction survey."} and en_draf("peraturan") is None
        and en_draf("jadwal") is None,
        "yang menunggu persetujuan, yang sudah lengkap, dan yang disembunyikan tidak berubah")
    k1, k2, k4 = pg.cari(A, K1), pg.cari(A, K2), pg.cari(A, K4)
    cek(k1["en"]["judul"] == "(EN) Jadwal ujian" and sorted(k1["en"]["mesin"]) == ["isi", "judul", "ringkasan"]
        and "en" not in k2 and "en" not in k4 and "en" not in pg.cari(A, K3), "pengumuman: hanya milik operator itu")
    cek(tm.pemakaian(A)["hari"].get(tm.hari_ini()) == harap_karakter,
        "pemakaian: %r dari %d" % (tm.pemakaian(A)["hari"].get(tm.hari_ini()), harap_karakter))
    log = ks.get("/super/audit").get_data(as_text=True)
    cek(log.count("isi-en-terjemahan-mesin") >= 3 and "pengumuman-en-terjemahan-mesin" in log
        and "terjemahkan-semua-dimulai" in log and "terjemahkan-semua-selesai" in log, "log audit")
    teks = ko.get(T).get_data(as_text=True)
    cek("Hasil terakhir" in teks and teks.count(">Diterjemahkan<") == 4 and "Selesai." in teks
        and "Tidak ada yang perlu diterjemahkan" in teks, "halaman hasil: %d diterjemahkan" % teks.count(">Diterjemahkan<"))
    r = kirim(ko, T)
    cek(r.status_code == 302 and "Tidak ada yang perlu diterjemahkan" in ko.get(T).get_data(as_text=True),
        "dijalankan lagi: tidak ada yang perlu diterjemahkan")

    # ============================================================== the review filters and the dashboard
    teks = ko.get(L + "?status=mesin").get_data(as_text=True)
    cek("Terjemahan mesin belum diperiksa (3)" in teks and ">Sejarah</a>" in teks and ">Tugas Akhir</a>" in teks
        and ">Peraturan</a>" not in teks, "saringan daftar halaman: terjemahan mesin belum diperiksa")
    teks = ko.get("/prodi/%s/pengumuman?en=mesin" % A).get_data(as_text=True)
    cek("Terjemahan mesin belum diperiksa (1)" in teks and "Jadwal ujian" in teks and "Seminar" not in teks
        and ko.get("/prodi/%s/pengumuman?en=lain" % A).status_code == 404, "saringan daftar pengumuman")
    teks = ka.get("/prodi/%s/" % A).get_data(as_text=True)
    cek("halaman?status=mesin\"><strong>3</strong> halaman dengan terjemahan mesin" in teks
        and "pengumuman?en=mesin\"><strong>1</strong> pengumuman dengan terjemahan mesin" in teks,
        "Ringkasan menautkan saringan")

    # ============================================================== an admin's job, limits, failures
    teks = ka.get(T).get_data(as_text=True).split("Terjemahkan lagi")[-1]       # the plan, not the last result
    cek("Kuliah umum" in teks and "Seminar" in teks and "Pengumuman lama" not in teks and "Jadwal ujian" not in teks,
        "rencana admin: semua pengumuman yang belum diterjemahkan, tanpa yang ditarik")
    ih.simpan_draf(A, "kerja-sama", {"uraian": "Kerja sama dengan mitra industri dan pemerintah daerah " * 4}, "adma")
    app.penerjemah.gagal = "kuota karakter akun DeepL sudah habis untuk periode ini"
    pakai = tm.pemakaian(A)["hari"].get(tm.hari_ini())
    kirim(ka, T)
    teks = ka.get(T).get_data(as_text=True)
    cek(en_draf("kerja-sama") is None and "en" not in pg.cari(A, K2) and tm.pemakaian(A)["hari"].get(tm.hari_ini()) == pakai
        and "Terjemahan dihentikan: kuota karakter akun DeepL" in teks and ">Gagal<" in teks and "Tidak dijalankan" in teks,
        "penyedia gagal: pekerjaan berhenti, tidak ada yang berubah")
    app.penerjemah.gagal = None
    # today's limit fits the announcements but not the long page
    sempit = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "sinkron",
                               "TERJEMAH_PENYEDIA": "tiruan", "TERJEMAH_BATAS_HARIAN": str(pakai + 100)})
    kas = klien(sempit, "adma", "103.84.116.64")
    kirim(kas, T)
    teks = kas.get(T).get_data(as_text=True)
    cek(en_draf("kerja-sama") is None and "Belum (batas tercapai)" in teks
        and pg.cari(A, K2).get("en", {}).get("ringkasan") == "(EN) Kuliah umum bersama praktisi."
        and pg.cari(A, K4).get("en", {}).get("judul") == "(EN) Seminar", "batas: yang tidak muat menunggu, yang lain jalan")
    # a page changed by someone else while it is translated is left as they saved it
    asli = app.penerjemah.terjemahkan

    def sambil_diubah(teks_):
        ih.simpan_draf(A, "kerja-sama:en", {"teks": {}, "asal": {}}, "orang-lain")
        return asli(teks_)
    app.penerjemah.terjemahkan = sambil_diubah
    kirim(ka, T)
    app.penerjemah.terjemahkan = asli
    teks = ka.get(T).get_data(as_text=True)
    cek(en_draf("kerja-sama")["oleh"] == "orang-lain" and not en_draf("kerja-sama")["isi"].get("mesin")
        and "diubah orang lain saat diterjemahkan" in teks, "diubah saat diterjemahkan: dilewati, simpanan orang lain tetap")

    # ============================================================== the background mode
    latar = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "latar",
                              "TERJEMAH_PENYEDIA": "tiruan"})
    kl = klien(latar, "adma", "103.84.116.65")
    buka, asli_l = threading.Event(), latar.penerjemah.terjemahkan

    def tertahan(teks_):
        buka.wait(10)
        return asli_l(teks_)
    latar.penerjemah.terjemahkan = tertahan
    r = kirim(kl, T)
    teks = kl.get(T).get_data(as_text=True)
    cek(r.status_code == 302 and "Sedang menerjemahkan" in teks and '<meta http-equiv="refresh" content="5">' in teks
        and "Ya, terjemahkan semua" not in teks and "Terjemahkan semua sedang berjalan" in kl.get(L).get_data(as_text=True),
        "latar: kemajuan dan muat ulang sendiri")
    kirim(kl, T)
    cek("sedang berjalan untuk prodi ini" in kl.get(T).get_data(as_text=True), "latar: pekerjaan kedua ditolak")
    buka.set()
    for _i in range(100):
        if not latar.terjemah_semua.keadaan(A)["berjalan"]:
            break
        time.sleep(0.1)
    cek(not latar.terjemah_semua.keadaan(A)["berjalan"] and en_draf("kerja-sama")["isi"].get("mesin")
        and "Hasil terakhir" in kl.get(T).get_data(as_text=True), "latar: pekerjaan selesai")

    # ============================================================== review from page to page
    def formulir_en(id_, **ubah):
        sumber, versi_id = ii.isi_sumber(A, id_)
        data = ih.baca(A, id_ + ":en")
        en = ii.rapi(ih.isi_kerja(data))
        f = {"t." + b["kunci"]: b["nilai"] for b in ii.butir_formulir(ih.templat_halaman(id_), sumber, en)}
        f.update(versi=str(data.get("versi", 0)), versi_id=str(versi_id), periksa_mesin="1")
        f.update(ubah)
        return f
    teks = ko.get(L + "/sejarah/en").get_data(as_text=True)
    cek('value="ajukan-lanjut">Ajukan dan buka berikutnya' in teks
        and "Halaman berikutnya yang perlu diperiksa: Penjaminan Mutu" in teks, "operator: tombol ajukan dan buka berikutnya")
    r = kirim(ko, L + "/sejarah/en", **formulir_en("sejarah", aksi="ajukan-lanjut"))
    cek(r.status_code == 302 and r.headers["Location"].endswith(L + "/penjaminan-mutu/en")
        and en_draf("sejarah")["status"] == "menunggu" and not en_draf("sejarah")["isi"].get("mesin"),
        "operator: diajukan lalu halaman berikutnya: %s" % r.headers.get("Location"))
    # a submitted English draft holding machine texts is not the operator's next page (it cannot submit it again)
    data = ih.baca(A, "survei-kepuasan:en")
    ih.simpan_draf(A, "survei-kepuasan:en", dict(ih.isi_kerja(data), teks={
        "Survei kepuasan mahasiswa.": "Student satisfaction survey.", "Tindak lanjut hasil survei.": "(EN) Follow-up."},
        mesin=["Tindak lanjut hasil survei."]), "adma", data["versi"])
    cek(en_draf("survei-kepuasan")["status"] == "menunggu"
        and "Halaman berikutnya yang perlu diperiksa: Penjaminan Mutu" in ko.get(L + "/tugas-akhir/en").get_data(as_text=True)
        and "Halaman berikutnya yang perlu diperiksa: Survei Kepuasan" in ka.get(L + "/tugas-akhir/en").get_data(as_text=True),
        "halaman berikutnya: draf yang menunggu persetujuan hanya untuk admin")
    r = kirim(ko, L + "/penjaminan-mutu/en", **formulir_en("penjaminan-mutu", aksi="ajukan-lanjut", periksa_mesin=""))
    cek(r.status_code == 302 and r.headers["Location"].endswith(L + "/penjaminan-mutu/en")
        and en_draf("penjaminan-mutu")["status"] == "draf", "belum dicentang: tidak diajukan, tetap di halaman itu")
    teks = ka.get(L + "/sejarah/en").get_data(as_text=True)
    cek('value="terbitkan-lanjut">Terbitkan dan buka berikutnya' in teks, "admin: tombol terbitkan dan buka berikutnya")
    cek("Halaman berikutnya yang perlu diperiksa: Sejarah" in ka.get(L + "/survei-kepuasan/en").get_data(as_text=True),
        "admin: pengajuan tanpa terjemahan mesin juga termasuk halaman berikutnya")
    url, dikunjungi = L + "/sejarah/en", []
    for _i in range(12):
        id_ = url.split("/halaman/")[1].split("/")[0]
        dikunjungi.append(id_)
        r = kirim(ka, url, **formulir_en(id_, aksi="terbitkan-lanjut"))
        url = r.headers.get("Location", "")
        if "/en" not in url:
            break
        url = url[url.index("/prodi/"):]
    cek(url.endswith(L) and "sejarah" in dikunjungi and "penjaminan-mutu" in dikunjungi and "survei-kepuasan" in dikunjungi
        and all(ih.terbit(A, x + ":en") for x in dikunjungi) and not any(en_draf(x) for x in dikunjungi),
        "admin: terbitkan dari halaman ke halaman sampai tidak ada lagi: %r" % dikunjungi)
    teks = ka.get(L).get_data(as_text=True)
    cek("Tidak ada lagi halaman dengan terjemahan mesin yang perlu diperiksa atau menunggu persetujuan" in teks,
        "pesan: tidak ada lagi yang perlu diperiksa")
    teks = ka.get(L + "?status=mesin").get_data(as_text=True)
    cek("Tidak ada lagi halaman dengan terjemahan mesin yang belum diperiksa." in teks, "saringan kosong")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_terjemahkan_semua: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
