# -*- coding: utf-8 -*-
"""Fase 2 langkah 4: the documents of the accreditation page and the accreditation criteria labels (K-P25, K-P29).

- platform/template/kriteria.json is valid, and docs/kriteria-akreditasi.md holds its table as it is now;
- the checks of a criteria file: ids, names (no markup), aliases claimed once (case and spaces ignored), statuses, a
  confirmed body names who confirmed it and when and maps pages, pages and criterion numbers that exist;
- a programme's body by its "lembaga_akreditasi" (aliases such as LAM-Tek / LAM-Teknik), never a draft, never an
  unclaimed value (empty, "BAN-PT / LAM-PTIP");
- the sites: no label anywhere while every body is a draft; once a body is confirmed, its labels on the pages it maps
  and the pages per criterion on the accreditation page (a hidden optional page left out), escaped; a broken file
  shows nothing and warns; the documents of the accreditation page under its official status, the note while there
  are none; the shared page checks;
- a programme's own criteria (K-P33): the checks of its file (numbers, names, spam, pages), its labels shown while the
  shared file is a draft and before a confirmed body, a broken one ignored with a warning;
- the admin: the accreditation page in the list and its editor (the official status said, not editable there), the
  label in the editor only once confirmed or set by the programme, the criteria page (filled from a proposal without
  storing, stored, refused with the reason, read-only for operators, cleared), the completeness CSV.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import copy
import csv
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
    print("uji_akreditasi: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-akreditasi-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("PRODI_RAHASIA", "rahasia"), ("PRODI_LOG", "log"),
                  ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"), ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import akun  # noqa: E402
import app as app_mod  # noqa: E402
import bangun  # noqa: E402
import isi_halaman as ih  # noqa: E402
import kriteria as kr  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import tarik_www  # noqa: E402
from formulir_uji import pdf, prodi  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B, C = "55201", "20201", "86201"
SLUG = {A: "s1informatika", B: "s1elektro", C: "s1politik"}
ASLI = kr.KRITERIA_JSON
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def halaman_situs(kode, alamat):
    path = os.path.join(lokasi.publik(), SLUG[kode], *alamat.split("/"), "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def pakai_kriteria(data):
    """Build with this criteria file (written next to the test data)."""
    path = os.path.join(KERJA, "kriteria-%d.json" % len(os.listdir(KERJA)))
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    kr.KRITERIA_JSON = path
    b = bangun.Pembangun(produksi=False)
    b.bangun()
    return b


try:
    halaman_ada = set(ih.TEMPLAT)
    menu = menu_mod.baca_templat()
    label = {k: b["label"] for k, b in menu_mod.semua_butir(menu).items()}
    urutan = [b["id"] for b in menu_mod.halaman(menu_mod.susun(menu)) if b["id"] in ih.TEMPLAT]

    # ============================================================== the file in the repository, and its document
    asli = kr.baca()
    cek(kr.periksa(asli, halaman_ada) == [], "kriteria.json sah: %r" % kr.periksa(asli, halaman_ada)[:3])
    path_dok = os.path.join(AKAR, "docs", "kriteria-akreditasi.md")
    if os.path.isfile(path_dok):
        with io.open(path_dok, encoding="utf-8") as f:
            dok = f.read()
        cek(kr.tabel_markdown(asli, label, urutan) in dok,
            "docs/kriteria-akreditasi.md memuat tabel kriteria.json yang sekarang (python3 platform/kriteria.py tabel)")
    else:
        # inside the admin image (Dockerfile) only platform/ and uji/ are there; the document is checked in the repo
        cek(not os.path.isfile(os.path.join(AKAR, "docker-compose.yml")), "docs/kriteria-akreditasi.md tidak ada")
    ban = [lb for lb in asli["lembaga"] if lb["id"] == "ban-pt"][0]
    cek(len(ban["kriteria"]) == 9 and set(ban["halaman"]) <= halaman_ada and all(
        x in {k["nomor"] for k in ban["kriteria"]} for d in ban["halaman"].values() for x in d), "draf BAN-PT: 9 kriteria")
    print("kriteria.json: %s" % ", ".join("%s %s" % (lb["nama"], lb["status"]) for lb in asli["lembaga"]))

    # ============================================================== the checks of a criteria file
    def dikonfirmasi(data, id_, **lain):
        data = copy.deepcopy(data)
        for lb in data["lembaga"]:
            if lb["id"] == id_:
                lb.update(status="dikonfirmasi", dikonfirmasi={"oleh": "LPMPP UNSRAT", "tanggal": "2026-11-30"}, **lain)
        return data
    sah = dikonfirmasi(asli, "ban-pt")
    cek(kr.periksa(sah, halaman_ada) == [], "BAN-PT dikonfirmasi: sah")

    def ubah(fungsi):
        data = copy.deepcopy(sah)
        fungsi(data)
        return kr.periksa(data, halaman_ada)
    for pesan, fungsi in (
            ("tanpa daftar lembaga", lambda d: d.pop("lembaga")),
            ("id ganda", lambda d: d["lembaga"][1].update(id="ban-pt")),
            ("id tidak sah", lambda d: d["lembaga"][1].update(id="LAM PTKes")),
            ("nama dengan markah", lambda d: d["lembaga"][0].update(nama="BAN-PT <b>")),
            ("nama kriteria dengan markah", lambda d: d["lembaga"][0]["kriteria"][0].update(nama="<script>")),
            ("alias ganda (huruf dan spasi diabaikan)", lambda d: d["lembaga"][1]["alias"].append(" ban-pt ")),
            ("alias kosong", lambda d: d["lembaga"][1].update(alias=[])),
            ("status tidak dikenal", lambda d: d["lembaga"][1].update(status="tayang")),
            ("halaman tidak dikenal", lambda d: d["lembaga"][0]["halaman"].update({"keuangan": ["5"]})),
            ("nomor kriteria tidak dikenal", lambda d: d["lembaga"][0]["halaman"].update({"sejarah": ["10"]})),
            ("nomor kriteria ganda", lambda d: d["lembaga"][0]["kriteria"].append({"nomor": "1", "nama": "Lagi"})),
            ("kriteria halaman kosong", lambda d: d["lembaga"][0]["halaman"].update({"sejarah": []})),
            ("dikonfirmasi tanpa siapa", lambda d: d["lembaga"][0].update(dikonfirmasi={"tanggal": "2026-11-30"})),
            ("dikonfirmasi tanggal salah", lambda d: d["lembaga"][0].update(dikonfirmasi={"oleh": "LPMPP", "tanggal": "30-11-2026"})),
            ("dikonfirmasi tanpa kriteria", lambda d: d["lembaga"][1].update(
                status="dikonfirmasi", dikonfirmasi={"oleh": "LPMPP", "tanggal": "2026-11-30"}))):
        cek(ubah(fungsi), "berkas kriteria %s harus ditolak" % pesan)
    cek(kr.periksa("bukan objek", halaman_ada) and kr.periksa({"lembaga": ["x"]}, halaman_ada), "bentuk berkas salah ditolak")

    # ============================================================== a programme's body
    lt = dikonfirmasi(asli, "lam-teknik", kriteria=[{"nomor": "A", "nama": "Kriteria uji & contoh"}],
                      halaman={"kurikulum": ["A"]})
    cek(kr.lembaga_untuk(asli, "BAN-PT") is None and kr.lembaga_untuk(asli, "BAN-PT", termasuk_draf=True)["id"] == "ban-pt",
        "draf tidak pernah dipakai, kecuali untuk tabel tinjauan")
    cek((kr.lembaga_untuk(sah, " ban-pt ") or {}).get("id") == "ban-pt", "nama lembaga: huruf dan spasi diabaikan")
    cek((kr.lembaga_untuk(lt, "LAM-Tek") or {}).get("id") == "lam-teknik" and
        (kr.lembaga_untuk(lt, "LAM-Teknik") or {}).get("id") == "lam-teknik", "alias LAM-Tek dan LAM-Teknik")
    for nilai in ("", None, "BAN-PT / LAM-PTIP", "LAM-Tidak-Ada"):
        cek(kr.lembaga_untuk(sah, nilai) is None, "lembaga %r tanpa label" % nilai)
    bp = kr.lembaga_untuk(sah, "BAN-PT")
    cek(kr.label(bp, "organisasi-prestasi") == [("3", "Mahasiswa"), ("9", "Luaran dan Capaian Tridharma")] and
        kr.label(bp, "sejarah") == [] and kr.label(None, "kurikulum") == [], "label halaman")
    peta = kr.peta(bp, {"visi-misi", "kurikulum"})
    cek([n for n, _nama, _ids in peta] == [str(i) for i in range(1, 10)] and peta[0][2] == ["visi-misi"] and peta[1][2] == [],
        "peta kriteria dalam urutan instrumen, hanya halaman yang ada")

    # ============================================================== the sites
    os.makedirs(os.environ["WWW_DATA"])
    program = [dict(prodi(A, "Teknik Informatika"), lembaga_akreditasi="BAN-PT", akreditasi="Unggul"),
               dict(prodi(B, "Teknik Elektro"), lembaga_akreditasi="LAM-Tek", akreditasi="Baik Sekali"),
               dict(prodi(C, "Ilmu Politik"), lembaga_akreditasi="", akreditasi="")]
    for nama, isi in {"prodi": {"program": program},
                      "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "jenis": "fakultas",
                                         "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                      "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n" + "".join("%s,S1,%s,FT,%s,x,x\n" % (k, n, SLUG[k]) for k, n in (
            (A, "Teknik Informatika"), (B, "Teknik Elektro"), (C, "Ilmu Politik"))))
    registri.siapkan_dari_csv("penguji", path_csv)
    lokasi.tulis_json(lokasi.path_data("prodi/%s/situs" % A), {"menu": {"jadwal": {"sembunyi": True}}})

    # every body still a draft: no label, no map anywhere
    b = pakai_kriteria(asli)
    jumlah = 0
    for kode in (A, B, C):
        for id_ in ih.TEMPLAT:
            teks = halaman_situs(kode, menu_mod.semua_butir(menu)[id_]["alamat"])
            if teks is not None:
                jumlah += 1
                cek("label-kriteria" not in teks and "peta-kriteria" not in teks, "%s %s: tanpa label selama draf" % (kode, id_))
    cek(jumlah >= 70, "halaman diperiksa: %d" % jumlah)
    teks = halaman_situs(A, "profil/akreditasi")
    cek("Unggul" in teks and "BAN-PT" in teks and "Sertifikat akreditasi sedang dilengkapi oleh Program Studi" in teks,
        "akreditasi tanpa dokumen: status resmi dan catatan sertifikat")

    # the documents of the accreditation page
    sertifikat = media.simpan_pdf(A, pdf(), "Sertifikat")
    ih.terbitkan(A, "akreditasi", {"dokumen": [{"judul": "Sertifikat Akreditasi BAN-PT 2023", "tahun": 2023,
                                                "keterangan": "Peringkat Unggul", "berkas": sertifikat}],
                                   "uraian": "Akreditasi berikutnya mengikuti jadwal BAN-PT."}, "penguji")

    # confirmed: BAN-PT for A, LAM Teknik (alias LAM-Tek) for B, nothing for C
    data = dikonfirmasi(lt, "ban-pt")
    b = pakai_kriteria(data)
    teks = halaman_situs(A, "profil/kerja-sama")
    cek('<p class="label-kriteria">Kriteria akreditasi BAN-PT: Kriteria 2, Tata Pamong, Tata Kelola, dan Kerja Sama</p>' in teks,
        "label kriteria di halaman wajib")
    teks = halaman_situs(A, "mahasiswa/organisasi-prestasi")
    cek("Kriteria 3, Mahasiswa; Kriteria 9, Luaran dan Capaian Tridharma" in teks, "dua kriteria pada satu halaman")
    cek("label-kriteria" not in halaman_situs(A, "profil/sejarah"), "halaman tanpa kriteria tanpa label")
    teks = halaman_situs(A, "profil/akreditasi")
    cek("Unggul" in teks and "Sertifikat Akreditasi BAN-PT 2023" in teks and "/unggahan/%s" % sertifikat["jalur"] in teks
        and "Sertifikat akreditasi sedang dilengkapi" not in teks and "Akreditasi berikutnya mengikuti jadwal BAN-PT." in teks,
        "dokumen akreditasi di bawah status resmi")
    cek(teks.index("Peringkat akreditasi") < teks.index("Sertifikat Akreditasi BAN-PT 2023") < teks.index('id="peta-kriteria"'),
        "urutan: status resmi, dokumen, peta kriteria")
    cek('<h2 id="peta-kriteria">Halaman menurut kriteria akreditasi BAN-PT</h2>' in teks and "Kriteria 6: Pendidikan" in teks
        and 'href="../../akademik/kurikulum/"' in teks and "Jadwal Kuliah dan Ujian" not in teks,
        "peta kriteria: tautan ke halaman, halaman opsional yang disembunyikan tidak ikut")
    teks = halaman_situs(B, "akademik/kurikulum")
    cek("Kriteria akreditasi LAM Teknik: Kriteria A, Kriteria uji &amp; contoh" in teks, "LAM-Tek memakai LAM Teknik, di-escape")
    cek("label-kriteria" not in halaman_situs(B, "profil/kerja-sama"), "LAM Teknik tidak memetakan kerja sama")
    cek("Sertifikat akreditasi sedang dilengkapi" in halaman_situs(B, "profil/akreditasi") and
        'id="peta-kriteria"' in halaman_situs(B, "profil/akreditasi"), "prodi tanpa dokumen: catatan tetap, peta ada")
    for alamat in ("profil/kerja-sama", "profil/akreditasi", "akademik/kurikulum"):
        teks = halaman_situs(C, alamat)
        cek("label-kriteria" not in teks and "peta-kriteria" not in teks, "lembaga kosong tanpa label: %s" % alamat)
    jumlah, temuan = periksa_situs(lokasi.publik(), "akreditasi")
    cek(not temuan, "pemeriksaan halaman bersama: %r" % temuan[:5])

    # a broken file: nothing shown, a warning
    rusak = copy.deepcopy(data)
    rusak["lembaga"][0]["halaman"]["keuangan"] = ["5"]
    b = pakai_kriteria(rusak)
    cek(any("label kriteria akreditasi diabaikan" in p for p in b.peringatan) and
        "label-kriteria" not in halaman_situs(A, "profil/kerja-sama"), "berkas rusak: tidak ada label, ada peringatan")
    with io.open(kr.KRITERIA_JSON, "w", encoding="utf-8") as f:
        f.write("{bukan json")
    b = bangun.Pembangun(produksi=False)
    cek(getattr(b, "kriteria", "tidak ada") is None and any("label kriteria" in p for p in b.peringatan),
        "berkas yang bukan JSON diabaikan")

    # ============================================================== a programme's own criteria (K-P33)
    butir = menu_mod.semua_butir(menu)
    sah = {"nama": "LAM Teknik", "instrumen": "", "kriteria": [{"nomor": "1", "nama": "Visi & Misi"},
                                                              {"nomor": "2.1", "nama": "Tata Kelola"}],
           "halaman": {"visi-misi": ["1"], "struktur-organisasi": ["1", "2.1"]}}
    cek(kr.periksa_prodi(sah, halaman_ada) == [], "kriteria prodi sah: %r" % kr.periksa_prodi(sah, halaman_ada))
    for pesan, ubah in (
            ("tanpa nama lembaga", lambda d: d.update(nama="")),
            ("nama lembaga dengan markah", lambda d: d.update(nama="<b>LAM</b>")),
            ("nomor tidak sah", lambda d: d["kriteria"][0].update(nomor="1 2")),
            ("nomor ganda", lambda d: d["kriteria"][1].update(nomor="1")),
            ("nama kriteria kosong", lambda d: d["kriteria"][0].update(nama="")),
            ("teks judi", lambda d: d["kriteria"][0].update(nama="Info slot gacor")),
            ("halaman tidak dikenal", lambda d: d["halaman"].update({"keuangan": ["1"]})),
            ("nomor halaman tidak ada", lambda d: d["halaman"].update({"visi-misi": ["3"]})),
            ("terlalu banyak kriteria", lambda d: d.update(kriteria=[{"nomor": str(i), "nama": "K%d" % i}
                                                                     for i in range(1, kr.MAKS_KRITERIA + 2)],
                                                           halaman={}))):
        d = copy.deepcopy(sah)
        ubah(d)
        cek(kr.periksa_prodi(d, halaman_ada), "kriteria prodi %s harus ditolak" % pesan)
    cek(kr.periksa_prodi(dict(sah, kriteria=[{"nomor": str(i), "nama": "K%d" % i} for i in range(1, kr.MAKS_KRITERIA + 1)],
                              halaman={}), halaman_ada) == [], "tepat %d kriteria diterima" % kr.MAKS_KRITERIA)
    try:
        kr.simpan_prodi(B, dict(sah, nama="Info togel"), halaman_ada, "penguji", "uji")
        cek(False, "simpan kriteria dengan teks judi harus ditolak")
    except kr.GagalKriteria as e:
        cek("judi" in str(e) and kr.baca_prodi(B) == {}, "penolakan menyebut alasannya, tidak ada yang tersimpan: %s" % e)
    kr.simpan_prodi(B, sah, halaman_ada, "penguji", "uji")
    cek(kr.baca_prodi(B) == sah, "kriteria prodi tersimpan apa adanya")
    b = pakai_kriteria(asli)                                  # every shared body a draft
    teks = halaman_situs(B, butir["visi-misi"]["alamat"])
    cek('<p class="label-kriteria">Kriteria akreditasi LAM Teknik: Kriteria 1, Visi &amp; Misi</p>' in teks,
        "kriteria prodi tampil walau berkas bersama masih draf, di-escape")
    cek("Kriteria 1, Visi &amp; Misi; Kriteria 2.1, Tata Kelola" in halaman_situs(B, butir["struktur-organisasi"]["alamat"]),
        "dua kriteria prodi pada satu halaman")
    teks = halaman_situs(B, "profil/akreditasi")
    cek('<h2 id="peta-kriteria">Halaman menurut kriteria akreditasi LAM Teknik</h2>' in teks and 'class="isi-info"></p>' not in teks,
        "peta kriteria prodi, tanpa baris instrumen yang kosong")
    cek("label-kriteria" not in halaman_situs(A, butir["visi-misi"]["alamat"]), "prodi lain tidak terpengaruh")
    b = pakai_kriteria(lt)                                    # LAM Teknik confirmed in the shared file
    cek("Kriteria A" not in halaman_situs(B, "akademik/kurikulum") and "Visi &amp; Misi" in
        halaman_situs(B, butir["visi-misi"]["alamat"]), "kriteria prodi didahulukan dari lembaga yang dikonfirmasi")
    lokasi.tulis_json(lokasi.path_data(kr.berkas_prodi(B)), dict(sah, nama="Promo slot gacor"))
    b = pakai_kriteria(asli)
    cek(any(p.startswith("prodi %s: label kriteria diabaikan" % B) for p in b.peringatan) and
        "label-kriteria" not in halaman_situs(B, butir["visi-misi"]["alamat"]), "kriteria prodi rusak: tanpa label, ada peringatan")
    kr.hapus_prodi(B, "penguji")
    cek(kr.baca_prodi(B) == {}, "kriteria prodi dikosongkan")

    # ============================================================== the admin
    kr.KRITERIA_JSON = ASLI
    SANDI = {}

    def akun_baru(nama, peran, prodi_, pelaku=None):
        id_a, sementara = akun.buat(pelaku, nama, nama.capitalize() + " Uji", peran, prodi_)
        SANDI[nama] = "Kebun 7 pagi hari nomor %d" % (len(SANDI) + 1)
        akun.ganti_sandi(id_a, sementara, SANDI[nama])
        return akun.ambil(id_a)
    super_ = akun_baru("superuji", "super", [])
    akun_baru("adma", "admin", [A], super_)
    akun_baru("opa", "operator", [A], super_)
    app = app_mod.buat_app({"SECRET_KEY": "k" * 64, "ADMIN_IP_BOLEH": "103.84.116.0/24", "PRODI_BANGUN": "mati"})
    klien = {}
    for i, nama in enumerate(("superuji", "adma", "opa")):
        c = app.test_client()
        c.environ_base["REMOTE_ADDR"] = "103.84.116.%d" % (80 + i)
        c.get("/masuk")
        with c.session_transaction() as s:
            token = s["csrf"]
        cek(c.post("/masuk", data={"csrf": token, "pengguna": nama, "sandi": SANDI[nama]}).status_code == 302, "%s masuk" % nama)
        klien[nama] = c
    ka, ks, ko = klien["adma"], klien["superuji"], klien["opa"]

    def kirim(c, url, data):
        with c.session_transaction() as s:
            data = dict(data, csrf=s["csrf"])
        return c.post(url, data=data)
    teks = ka.get("/prodi/%s/halaman" % A).get_data(as_text=True)
    cek('href="/prodi/%s/halaman/akreditasi">Akreditasi</a>' % A in teks and "Pelengkap" in teks,
        "daftar halaman: akreditasi sebagai pelengkap")
    teks = ka.get("/prodi/%s/halaman/akreditasi" % A).get_data(as_text=True)
    cek("Status akreditasi tampil otomatis dari data resmi prodi (Unggul, BAN-PT)" in teks and "Dokumen akreditasi" in teks
        and "Jangan unggah LED, LKPS" in teks, "penyunting akreditasi: status resmi disebut, dokumen diisi di sini")
    cek("Kriteria akreditasi BAN-PT" not in ka.get("/prodi/%s/halaman/kerja-sama" % A).get_data(as_text=True),
        "penyunting: label kriteria tidak tampil selama draf")
    with io.open(os.path.join(KERJA, "kriteria-admin.json"), "w", encoding="utf-8") as f:
        json.dump(dikonfirmasi(asli, "ban-pt"), f)
    kr.KRITERIA_JSON = os.path.join(KERJA, "kriteria-admin.json")
    cek("Kriteria akreditasi BAN-PT: Kriteria 2, Tata Pamong, Tata Kelola, dan Kerja Sama" in
        ka.get("/prodi/%s/halaman/kerja-sama" % A).get_data(as_text=True), "penyunting: label kriteria setelah dikonfirmasi")
    kr.KRITERIA_JSON = ASLI

    # the criteria page of a programme (K-P33)
    url_k = "/prodi/%s/kriteria" % A
    teks = ka.get(url_k).get_data(as_text=True)
    cek('id="nama" name="nama" type="text" value="BAN-PT"' in teks and '<option value="ban-pt">' in teks and
        "Halaman per kriteria" not in teks, "halaman kriteria: lembaga dari data resmi, usulan BAN-PT, belum ada tabel")
    r = kirim(ka, url_k + "/usulan", {"usulan": "ban-pt"})
    teks = r.get_data(as_text=True)
    cek(r.status_code == 200 and 'value="Tata Pamong, Tata Kelola, dan Kerja Sama"' in teks and
        'name="h-kerja-sama" value="2" checked' in teks and kr.baca_prodi(A) == {},
        "usulan mengisi formulir dan centang halaman tanpa menyimpan")
    cek(kirim(ka, url_k + "/usulan", {"usulan": "lam-teknik"}).status_code == 400, "usulan tanpa daftar kriteria ditolak")
    isian = {"nama": "BAN-PT", "instrumen": "IAPS 4.0", "kriteria_jumlah": "3", "k-0-nomor": "1", "k-0-nama": "Visi",
             "k-1-nomor": "2", "k-1-nama": "Tata Pamong", "k-2-nomor": "", "k-2-nama": "",
             "h-kerja-sama": "2", "h-visi-misi": ["1", "9"]}
    r = kirim(ka, url_k, dict(isian, **{"k-1-nomor": "1"}))
    cek(r.status_code == 400 and "nomor 1 sudah dipakai" in r.get_data(as_text=True) and kr.baca_prodi(A) == {},
        "nomor ganda ditolak dengan pesan, formulir tetap terisi")
    r = kirim(ka, url_k, dict(isian, **{"k-0-nama": "Judi online terpercaya"}))
    cek(r.status_code == 400 and "memuat teks judi" in r.get_data(as_text=True) and kr.baca_prodi(A) == {},
        "teks judi ditolak")
    cek(kirim(ka, url_k, isian).status_code == 302 and kr.baca_prodi(A)["halaman"] == {"kerja-sama": ["2"], "visi-misi": ["1"]},
        "kriteria tersimpan; centang nomor yang tidak ada dibuang")
    cek("Kriteria akreditasi BAN-PT: Kriteria 2, Tata Pamong" in ka.get("/prodi/%s/halaman/kerja-sama" % A).get_data(as_text=True),
        "penyunting: label kriteria yang diisi admin prodi")
    teks = ko.get(url_k).get_data(as_text=True)
    cek('action="%s"' % url_k not in teks and "Kriteria 2: Tata Pamong" in teks and "Hanya admin prodi" in teks
        and "Kriteria akreditasi</a>" in teks, "operator melihat kriteria tanpa formulir")
    cek(kirim(ko, url_k, isian).status_code == 403, "operator tidak bisa menyimpan kriteria")
    kol = dict(zip(*[b_ for b_ in csv.reader(io.StringIO(ks.get("/super/kelengkapan.csv").get_data(as_text=True).lstrip("﻿")))
                     if b_[0] in ("kode_pddikti", A)]))
    cek(kol.get("kriteria_akreditasi") == "2", "CSV kelengkapan: jumlah kriteria prodi")
    cek(kirim(ka, url_k + "/kosongkan", {}).status_code == 302 and kr.baca_prodi(A) == {}, "kriteria dikosongkan")
    cek("kriteria akreditasi" in ka.get("/prodi/%s/riwayat" % A).get_data(as_text=True),
        "riwayat prodi: versi kriteria akreditasi sebelum dikosongkan")
    baris = list(csv.reader(io.StringIO(ks.get("/super/kelengkapan.csv").get_data(as_text=True).lstrip("﻿"))))
    kolom = dict(zip(baris[0], [b_ for b_ in baris[1:] if b_[0] == A][0]))
    cek(kolom.get("Akreditasi (pelengkap)", "").startswith("terbit 20") and kolom["wajib_total"] == "22",
        "CSV kelengkapan: kolom akreditasi, 22 halaman wajib tetap")
except Exception as e:                 # a step that went wrong stops the suite; say where instead of only a traceback
    import traceback
    traceback.print_exc()
    gagal.insert(0, "uji berhenti di tengah (%s: %s); pemeriksaan sebelumnya:" % (type(e).__name__, e))
finally:
    kr.KRITERIA_JSON = ASLI
    shutil.rmtree(KERJA, ignore_errors=True)

for g_ in gagal:
    print("GAGAL", g_)
print("uji_akreditasi: %s" % ("LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
