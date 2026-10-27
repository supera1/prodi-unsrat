# -*- coding: utf-8 -*-
"""Fase 2 langkah 1: the content of a programme's own pages (platform/isi_halaman.py) and how the site shows it.

- the templates: one for every required and optional page of the master menu, well formed (tables of plain columns,
  cards with a title, documents and photos with their file, extra sections last);
- the checks: every kind of wrong value is refused with where it is (required fields, lengths, years, percentages,
  choices, links to https:// only, files of this programme only, photos without alternative text, gambling text);
- the limited markup never lets HTML through (scripts, attributes, javascript: links);
- storing: versions, a save from an outdated version refused, nothing written when the content fails, taking a page
  off the site;
- the site: every section of every page with sample content and real stored files (PDF, photo), numbers, tables,
  cards, documents, galleries, the shared page checks, the integrity check; missing files, content that fails the
  checks, a hidden optional page, a page taken off; the command line.

Needs the packages of platform/admin/requirements.txt: run with .venv/bin/python.
"""
from __future__ import print_function

import io
import json
import os
import re
import shutil
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("platform", "platform/admin", "platform/bangun", "platform/pemantau"):
    sys.path.insert(0, os.path.join(AKAR, *sub.split("/")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import jinja2  # noqa: F401
    from PIL import Image
except ImportError:
    print("uji_isi_halaman: paket admin belum terpasang; jalankan dengan .venv/bin/python (lihat README)")
    sys.exit(1)

KERJA = tempfile.mkdtemp(prefix="prodi-uji-isi-")
for nama, sub in (("PRODI_DATA", "data"), ("PRODI_RIWAYAT", "riwayat"), ("WWW_DATA", "www"), ("PRODI_PUBLIK", "publik"),
                  ("PRODI_NGINX", "nginx"), ("PRODI_UNGGAHAN", "unggahan"), ("PRODI_LOG", "log"), ("PRODI_RAHASIA", "rahasia")):
    os.environ[nama] = os.path.join(KERJA, sub)
os.environ["PRODI_MANIFES"] = os.path.join(KERJA, "manifes.json")
os.environ["PRODI_PENYIMPANAN"] = "lokal"
os.environ.pop("PRODI_MODE", None)

import bangun  # noqa: E402
import cek_integritas  # noqa: E402
import isi_halaman as ih  # noqa: E402
import lokasi  # noqa: E402
import media  # noqa: E402
import menu as menu_mod  # noqa: E402
import registri  # noqa: E402
import riwayat  # noqa: E402
import tarik_www  # noqa: E402
from pemeriksa_halaman import periksa_situs  # noqa: E402

A, B = "55201", "20201"
MENYUSUL = "Informasi ini sedang dilengkapi oleh Program Studi"     # the note of a page without content
gagal = []


def cek(kondisi, pesan):
    if not kondisi:
        gagal.append(pesan)


def gambar(lebar, tinggi):
    buf = io.BytesIO()
    Image.new("RGB", (lebar, tinggi), (20, 60, 160)).save(buf, "JPEG")
    return buf.getvalue()


def pdf():
    isi = b"BT /F1 24 Tf 72 720 Td (Dokumen) Tj ET"
    objek = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
             b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
             b"<< /Length %d >>\nstream\n" % len(isi) + isi + b"\nendstream", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    keluar, letak = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objek, 1):
        letak.append(len(keluar))
        keluar += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(keluar)
    keluar += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objek) + 1) + b"".join(b"%010d 00000 n \n" % x for x in letak)
    keluar += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objek) + 1, xref)
    return bytes(keluar)


def prodi(kode, nama):
    return {"kode_pddikti": kode, "nama": nama, "nama_en": "", "jenjang": "S1", "gelar": "S.Kom.", "sks": 144, "unit_kode": "ft",
            "unit": "Fakultas Teknik", "website": "", "surel": "p@unsrat.ac.id", "bidang_kerja": "B.", "bidang_kerja_en": "",
            "akreditasi": "Unggul", "lembaga_akreditasi": "LAM-Infokom", "berlaku_hingga": "", "internasional": "", "slug": "x",
            "slug_en": "", "cpl": [{"kode": "CPL 1", "isi": "Capaian.", "isi_en": "", "kurikulum": "2025/2026"}]}


def halaman_html(slug, alamat):
    path = os.path.join(lokasi.publik(), slug, *alamat.split("/"), "index.html")
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def masalah(id_, isi, kode=A):
    return ih.periksa(id_, isi, kode)


def ada_masalah(id_, isi, potongan, kode=A):
    m = masalah(id_, isi, kode)
    cek(any(potongan in x for x in m), "%s: masalah %r harus dilaporkan, dapat %r" % (id_, potongan, m))


def bangun_semua():
    b = bangun.Pembangun(produksi=False)
    b.bangun()
    return b


try:
    os.makedirs(os.environ["WWW_DATA"])
    for nama, isi in {"prodi": {"program": [prodi(A, "Teknik Informatika"), prodi(B, "Teknik Elektro")]},
                      "unit": {"unit": [{"kode": "ft", "nama": "Fakultas Teknik", "jenis": "fakultas",
                                         "bendera": {"dasar": "#000099", "tulisan": "#FFFF00"}}]},
                      "kalender": {"semester": []}, "situs": {"identitas": {}, "kontak": {}}}.items():
        with io.open(os.path.join(os.environ["WWW_DATA"], nama + ".json"), "w", encoding="utf-8") as f:
            json.dump(isi, f)
    tarik_www.terapkan("penguji")
    path_csv = os.path.join(KERJA, "slug.csv")
    with io.open(path_csv, "w", encoding="utf-8") as f:
        f.write(",".join(registri.slug_mod.KOLOM) + "\n%s,S1,Teknik Informatika,FT,s1informatika,x,x\n"
                "%s,S1,Teknik Elektro,FT,s1elektro,x,x\n" % (A, B))
    registri.siapkan_dari_csv("penguji", path_csv)

    # ============================================================== the templates
    menu = menu_mod.baca_templat()
    diisi_prodi = {b["id"]: b for b in menu_mod.semua_butir(menu).values() if b.get("jenis") in ("wajib", "opsional")}
    # every required and optional page, and the documents of the accreditation page (langkah 4, K-P29)
    cek(set(ih.TEMPLAT) == set(diisi_prodi) | {"akreditasi"}, "satu templat untuk setiap halaman wajib/opsional dan "
        "akreditasi: kurang %r, lebih %r" % (sorted((set(diisi_prodi) | {"akreditasi"}) - set(ih.TEMPLAT)),
                                             sorted(set(ih.TEMPLAT) - set(diisi_prodi) - {"akreditasi"})))
    cek(sum(1 for b in diisi_prodi.values() if b["jenis"] == "wajib") == 22, "22 halaman wajib")

    def periksa_node(node, tempat):
        j = node.get("jenis")
        cek(j in ("teks", "bilangan", "persen", "url", "pilihan", "centang", "objek", "daftar", "dokumen", "foto"),
            "%s: jenis %r" % (tempat, j))
        if j == "objek":
            kunci = [k for k, _n in node["bidang"]]
            cek(len(kunci) == len(set(kunci)), "%s: kunci ganda" % tempat)
            for k, n in node["bidang"]:
                cek(re.match(r"^[a-z][a-z_]*$", k), "%s: kunci %r" % (tempat, k))
                periksa_node(n, "%s.%s" % (tempat, k))
        elif j == "daftar":
            cek(node["tampil"] in ih.TAMPIL and node["maks"] > 0, "%s: tampil/maks" % tempat)
            isi = node["isi"]
            periksa_node(isi, tempat + "[]")
            if node["tampil"] == "daftar":
                cek(isi["jenis"] == "teks", "%s: daftar berisi teks" % tempat)
            else:
                cek(isi["jenis"] == "objek", "%s: %s berisi objek" % (tempat, node["tampil"]))
            if node["tampil"] == "tabel":
                cek(all(n["jenis"] in ih.SKALAR for _k, n in isi["bidang"]), "%s: kolom tabel hanya nilai biasa" % tempat)
            if node["tampil"] == "kartu":
                cek(isi["bidang"][0][1]["jenis"] == "teks" and isi["bidang"][0][1]["wajib"], "%s: kartu berjudul" % tempat)
            if node["tampil"] in ("dokumen", "galeri"):
                berkas = dict(isi["bidang"]).get("berkas")
                cek(berkas and berkas["jenis"] == ("dokumen" if node["tampil"] == "dokumen" else "foto") and berkas["wajib"],
                    "%s: butir %s wajib berberkas" % (tempat, node["tampil"]))
        elif j in ("teks", "bilangan", "persen", "url", "pilihan", "dokumen", "foto"):
            cek(isinstance(node.get("label"), str), "%s: label" % tempat)
    for id_, t in ih.TEMPLAT.items():
        periksa_node(t, id_)
        cek(t["bidang"][-1][0] == "tambahan", "%s: bagian tambahan di akhir" % id_)
        cek(all(n["label"] for k, n in t["bidang"][1:]), "%s: setiap bagian sesudah pengantar berjudul" % id_)

    # ============================================================== sample content passes, empty content is empty
    foto_a = media.simpan_foto(A, gambar(1200, 900), "Gedung laboratorium")
    pdf_a = media.simpan_pdf(A, pdf(), "Dokumen uji")
    foto_b = media.simpan_foto(B, gambar(800, 600), "Foto prodi lain")
    pdf_b = media.simpan_pdf(B, pdf(), "Dokumen prodi lain")

    def berkas_a(jenis):
        return dict(pdf_a) if jenis == "dokumen" else json.loads(json.dumps(foto_a))
    for id_ in ih.TEMPLAT:
        contoh = ih.isi_contoh(id_, 3, berkas_a)
        cek(not masalah(id_, contoh), "%s: isi contoh harus lolos: %r" % (id_, masalah(id_, contoh)[:3]))
        cek(not ih.kosong(ih.TEMPLAT[id_], contoh) and ih.tampilan(id_, contoh)[0], "%s: isi contoh tampil" % id_)
        cek(not masalah(id_, {}) and ih.kosong(ih.TEMPLAT[id_], {}) and ih.tampilan(id_, {})[0] == [],
            "%s: isi kosong sah dan tidak tampil" % id_)
        cek(not masalah(id_, ih.isi_contoh(id_)), "%s: isi contoh tanpa berkas juga lolos" % id_)
    cek(not masalah("sejarah", {"uraian": "x", "kunci_lama": "disimpan"}), "kunci yang tidak dikenal templat disimpan")

    # ============================================================== every kind of wrong value
    baris = {"mitra": "Universitas X", "jenis": "Penelitian", "tingkat": "Nasional"}
    for ubah, potongan in (
            ({"mitra": ""}, "Daftar kerja sama baris 1, Mitra: wajib diisi"),
            ({"jenis": "Hiburan"}, "Bidang: pilihan tidak dikenal"),
            ({"mulai": 1800}, "harus antara 1900 dan 2100"),
            ({"mulai": "2025"}, "harus angka bulat"),
            ({"mulai": True}, "harus angka bulat"),
            ({"mitra": "x" * 201}, "terlalu panjang (maksimal 200 karakter)"),
            ({"mitra": "Mitra\x07"}, "karakter yang tidak boleh"),
            ({"mitra": "baris satu\nbaris dua"}, "karakter yang tidak boleh"),
            ({"mitra": "Daftar slot gacor"}, "teks judi"),
            ({"bukti": dict(pdf_b)}, "berkas PDF tidak sah"),
            ({"bukti": dict(pdf_a, jalur="../rahasia/akun.pdf")}, "berkas PDF tidak sah"),
            ({"bukti": {"jenis": "pdf", "jalur": pdf_a["jalur"]}}, "berkas PDF tidak sah")):
        ada_masalah("kerja-sama", {"daftar": [dict(baris, **ubah)]}, potongan)
    cek(not masalah("kerja-sama", {"daftar": [dict(baris, bukti=dict(pdf_a))]}), "baris kerja sama yang benar lolos")
    ada_masalah("kerja-sama", {"daftar": [baris] * 301}, "paling banyak 300")
    ada_masalah("kerja-sama", {"daftar": "bukan daftar"}, "bukan daftar")
    ada_masalah("kerja-sama", {"daftar": ["bukan objek"]}, "baris 1: bukan objek")
    ada_masalah("kerja-sama", "bukan objek", "bukan objek")
    for v, sah in ((87.5, True), (0, True), (100, True), (101, False), (50.555, False), ("50", False), (-1, False)):
        m = masalah("survei-kepuasan", {"hasil": [{"survei": "Alumni", "aspek": "Layanan", "baik": v}]})
        cek(not m if sah else any("0 sampai 100" in x for x in m), "persen %r %s" % (v, "lolos" if sah else "ditolak"))
    for v, sah in (("https://doi.org/10.1/x", True), ("http://doi.org/x", False), ("javascript:alert(1)", False),
                   ("https://a b.id", False), ("https://x.id/\"onmouseover=1", False), ("https://" + "a" * 500, False),
                   ("//evil.example", False)):
        m = masalah("publikasi", {"daftar": [{"judul": "J", "tahun": 2025, "tautan": v}]})
        cek(not m if sah else any("https://" in x for x in m), "tautan %r %s: %r" % (v, "lolos" if sah else "ditolak", m))
    for teks_, sah in (("Lihat [situs](https://www.unsrat.ac.id/).", True), ("[x](javascript:alert(1))", False),
                       ("[x](http://contoh.id)", False), ("[x](/relatif)", False), ("Alamat https://a.id dibiarkan.", True)):
        m = masalah("sejarah", {"uraian": teks_})
        cek(not m if sah else any("diawali https://" in x for x in m), "markah %r %s" % (teks_, "lolos" if sah else "ditolak"))
    foto_tanpa_alt = json.loads(json.dumps(foto_a))
    foto_tanpa_alt["alt"] = " "
    ada_masalah("sejarah", {"foto": [{"berkas": foto_tanpa_alt}]}, "teks alternatif foto wajib")
    ada_masalah("sejarah", {"foto": [{"berkas": foto_b}]}, "foto tidak sah")
    foto_judi = json.loads(json.dumps(foto_a))
    foto_judi["alt"] = "slot gacor"
    ada_masalah("sejarah", {"foto": [{"berkas": foto_judi}]}, "teks alternatif foto wajib")
    ada_masalah("visi-misi", {"misi": ["Misi satu", ""]}, "Misi butir 2: wajib diisi")
    cek(ih.periksa("tidak-ada", {}, A) and ih.periksa("sejarah", {}, "../x"), "halaman atau kode yang tidak dikenal")

    # ============================================================== the limited markup never lets HTML through
    for teks_, harus, tidak in (
            ("<script>alert(1)</script>", "&lt;script&gt;", "<script"),
            ('"><img src=x onerror=alert(1)>', "&lt;img", "<img"),
            ("[<b>x</b>](https://a.id/)", '<a href="https://a.id/">&lt;b&gt;x&lt;/b&gt;</a>', "<b>"),
            ('[x](https://a.id/"onmouseover=alert(1))', "[x]", "onmouseover=alert(1)\""),
            ("[x](javascript:alert(1))", "[x](javascript:alert(1))", "<a"),
            ("**tebal** dan ** bukan **", "<strong>tebal</strong> dan ** bukan **", "<strong> bukan"),
            ("Kunjungi https://www.unsrat.ac.id/.", '<a href="https://www.unsrat.ac.id/">https://www.unsrat.ac.id/</a>.', "/.\""),
            ("satu\ndua\n\ntiga", "<p>satu<br>dua</p>\n<p>tiga</p>", "<p>satu</p>"),
            ("- a\n- b", "<ul><li>a</li><li>b</li></ul>", "<p>- a")):
        html = str(ih.teks_kaya(teks_))
        cek(harus in html and tidak not in html, "markah %r -> %r" % (teks_, html))
    cek(ih.angka(1234567) == "1.234.567" and ih.angka(2025, "tahun") == "2025" and ih.angka(87.5) == "87,5"
        and ih.angka(42.25) == "42,25" and ih.angka(100.0) == "100", "format angka")

    # ============================================================== storing
    v1 = ih.terbitkan(A, "sejarah", {"uraian": "Sejarah singkat."}, "penguji")
    cek(v1 == 1 and ih.terbit(A, "sejarah") == {"uraian": "Sejarah singkat."} and ih.terisi(A, "sejarah"), "terbitkan")
    try:
        ih.terbitkan(A, "sejarah", {"uraian": "Dari versi lama."}, "lain", versi=0)
        gagal.append("simpanan dari versi lama harus ditolak")
    except ih.GagalIsi as e:
        cek("baru saja diubah" in str(e), "pesan simpanan saling menimpa: %s" % e)
    try:
        ih.terbitkan(A, "sejarah", {"uraian": "[x](javascript:alert(1))"}, "penguji")
        gagal.append("isi yang salah harus ditolak")
    except ih.GagalIsi:
        pass
    cek(ih.baca(A, "sejarah")["versi"] == 1 and ih.terbit(A, "sejarah") == {"uraian": "Sejarah singkat."},
        "isi yang ditolak tidak menulis apa pun")
    cek(ih.terbitkan(A, "sejarah", {"uraian": "Sejarah kedua."}, "penguji", versi=1) == 2, "terbitkan dari versi terbaru")
    # the history keeps the content before every save: after two saves, the first one
    versi = [v for v in riwayat.daftar(100) if v["berkas"] == "prodi/%s/halaman-sejarah" % A]
    cek(len(versi) == 1, "isi sebelumnya masuk riwayat: %d versi" % len(versi))
    cek(ih.tarik(A, "sejarah", "penguji") == 3 and ih.terbit(A, "sejarah") is None and not ih.terisi(A, "sejarah"), "tarik")
    for kode, id_ in ((A, "beranda"), (A, "tidak-ada"), ("../x", "sejarah")):
        try:
            ih.nama_berkas(kode, id_)
            gagal.append("berkas %s/%s harus ditolak" % (kode, id_))
        except ih.GagalIsi:
            pass

    # ============================================================== the site
    for id_ in ih.TEMPLAT:
        ih.terbitkan(A, id_, ih.isi_contoh(id_, 3, berkas_a), "penguji")
    isi = ih.terbit(A, "laboratorium")
    isi["daftar"][0].update(kapasitas=1234567, nama='<script>alert("x")</script> Lab')
    isi["uraian"] = '"><img src=x onerror=alert(1)> **Uraian** [lab](https://www.unsrat.ac.id/lab)'
    ih.terbitkan(A, "laboratorium", isi, "penguji")
    isi = ih.terbit(A, "kerja-sama")
    isi["daftar"][0]["mitra"] = '<img src=x onerror=alert(1)> Mitra & "rekan"'
    ih.terbitkan(A, "kerja-sama", isi, "penguji")
    isi = ih.terbit(A, "kurikulum")
    isi["mata_kuliah"] = [{"semester": 1 + i // 10, "kode": "MK%03d" % i, "nama": "Mata kuliah %d" % i, "sks": 3,
                           "sifat": "Wajib"} for i in range(80)]
    ih.terbitkan(A, "kurikulum", isi, "penguji")
    b = bangun_semua()
    cek(not b.peringatan, "bangun tanpa peringatan: %r" % b.peringatan[:3])
    for id_, butir in diisi_prodi.items():
        html = halaman_html("s1informatika", butir["alamat"])
        bagian, _h = ih.tampilan(id_, ih.terbit(A, id_))
        cek(html and MENYUSUL not in html, "%s: halaman berisi" % id_)
        for x in bagian:
            if x["judul"]:
                cek('<h2 id="%s">%s</h2>' % (x["id"], str(ih.escape(x["judul"]))) in html, "%s: judul bagian %r" % (id_, x["judul"]))
        lain = halaman_html("s1elektro", butir["alamat"])
        cek(lain and MENYUSUL in lain, "%s: prodi lain tetap kosong" % id_)
    kerja = halaman_html("s1informatika", "profil/kerja-sama")
    cek('<th scope="col">Mitra</th>' in kerja and '<caption class="tersembunyi">Daftar kerja sama</caption>' in kerja
        and 'role="region" aria-labelledby="bagian-daftar" tabindex="0"' in kerja, "tabel kerja sama aksesibel")
    cek("<td>&lt;img src=x onerror=alert(1)&gt; Mitra &amp; &#34;rekan&#34;</td>" in kerja and "<img src=x" not in kerja,
        "sel tabel ter-escape")
    tautan_pdf = re.findall(r'<a href="([^"]+\.pdf)">PDF<span class="tersembunyi">', kerja)
    cek(tautan_pdf and all(os.path.isfile(os.path.normpath(os.path.join(lokasi.publik(), "s1informatika", "profil", "kerja-sama", t)))
                           for t in tautan_pdf), "PDF bukti kerja sama diterbitkan: %r" % tautan_pdf)
    lab = halaman_html("s1informatika", "fasilitas/laboratorium")
    cek("1.234.567" in lab and "&lt;script&gt;alert(&#34;x&#34;)&lt;/script&gt; Lab" in lab and "<script>alert" not in lab
        and "&lt;img src=x onerror=alert(1)&gt;" in lab and "<strong>Uraian</strong>" in lab
        and '<a href="https://www.unsrat.ac.id/lab">lab</a>' in lab, "kartu laboratorium: angka, escaping, markah")
    cek('alt="Gedung laboratorium"' in lab and 'class="isi-kartu__judul"' in lab, "foto kartu dengan teks alternatif")
    survei = halaman_html("s1informatika", "mahasiswa/survei-kepuasan")
    cek("<td>42,5%</td>" in survei and "<td>2025</td>" in survei, "persen dan tahun di tabel")
    kurikulum = halaman_html("s1informatika", "akademik/kurikulum")
    cek(kurikulum.count("<tr>") == 81 and "MK079" in kurikulum, "tabel besar 80 mata kuliah")
    visi = halaman_html("s1informatika", "profil/visi-misi")
    cek('<ol class="isi-daftar">' in visi and "<li>[CONTOH] Butir</li>" in visi, "misi sebagai daftar bernomor")
    sejarah = halaman_html("s1informatika", "profil/sejarah")
    cek('<ul class="galeri isi-galeri">' in sejarah and "<figcaption>[CONTOH] Keterangan foto</figcaption>" in sejarah,
        "galeri foto sejarah")
    cek('<ul class="isi-dokumen">' in visi and "PDF, 1 halaman" in visi, "daftar dokumen dengan jumlah halaman dan ukuran")
    cek('<ul class="isi-tautan">' in halaman_html("s1informatika", "fasilitas/perpustakaan"), "daftar tautan")
    jumlah, temuan = periksa_situs(lokasi.publik(), "isi")
    gagal.extend(temuan[:30])
    cek(not cek_integritas.periksa(lokasi.publik(), lokasi.manifes())[0], "cek integritas bersih")

    # a missing file: a required one drops its item, an optional one only itself
    os.remove(os.path.join(lokasi.unggahan(), *pdf_a["jalur"].split("/")))
    b = bangun_semua()
    cek(any("berkas tidak ditemukan" in p for p in b.peringatan), "berkas hilang diperingatkan: %r" % b.peringatan[:2])
    visi = halaman_html("s1informatika", "profil/visi-misi")
    kerja = halaman_html("s1informatika", "profil/kerja-sama")
    cek("isi-dokumen" not in visi and "<h2 id=\"bagian-misi\">" in visi, "dokumen tanpa berkas dilewati, bagian lain tetap")
    cek("[CONTOH] Mitra" in kerja and "PDF<span" not in kerja, "baris kerja sama tetap, tanpa bukti yang hilang")
    jumlah, temuan = periksa_situs(lokasi.publik(), "isi-hilang")
    gagal.extend(temuan[:30])
    with open(os.path.join(lokasi.unggahan(), *pdf_a["jalur"].split("/")), "wb") as f:
        f.write(pdf())

    # content changed by hand so that it fails the checks is not shown at all
    data = ih.baca(A, "ruang")
    data["terbit"]["isi"]["daftar"][0]["jumlah"] = "banyak"
    lokasi.tulis_json(lokasi.path_data(ih.nama_berkas(A, "ruang")), data)
    b = bangun_semua()
    cek(any("isi halaman ruang diabaikan" in p for p in b.peringatan), "isi rusak diperingatkan")
    cek(MENYUSUL in halaman_html("s1informatika", "fasilitas/ruang"), "isi rusak tidak ditampilkan")

    # a hidden optional page is not built, its content is kept; a page taken off says "sedang dilengkapi" again
    situs = lokasi.baca("prodi/%s/situs" % A)
    situs["menu"] = {"jadwal": {"sembunyi": True}}
    lokasi.tulis_json(lokasi.path_data("prodi/%s/situs" % A), situs)
    ih.tarik(A, "sejarah", "penguji")
    b = bangun_semua()
    cek(halaman_html("s1informatika", "akademik/jadwal") is None and ih.terbit(A, "jadwal"), "halaman opsional tersembunyi")
    cek(MENYUSUL in halaman_html("s1informatika", "profil/sejarah"), "halaman yang ditarik kosong lagi")
    foto_terbit = [r["jalur"] for r in foto_a["varian"].values()]
    cek(all(os.path.isfile(os.path.join(lokasi.publik(), "unggahan", *j.split("/"))) for j in foto_terbit),
        "foto yang masih dipakai halaman lain tetap terbit")
    b = bangun.Pembangun(produksi=False)
    b.bangun(A)
    cek("[CONTOH] Mitra" in halaman_html("s1informatika", "profil/kerja-sama"), "bangun satu prodi dengan isi halaman")
    # sample content is never published in production, whoever put it there (a staging VM becomes the production one)
    b = bangun.Pembangun(produksi=True)
    b.bangun(A)
    kerja = halaman_html("s1informatika", "profil/kerja-sama")
    cek("[CONTOH]" not in kerja and MENYUSUL in kerja
        and "prodi %s: isi halaman kerja-sama bertanda [CONTOH], tidak diterbitkan di produksi" % A in b.peringatan,
        "isi contoh tidak terbit di produksi: %r" % b.peringatan[:4])

    # the command line
    cek(ih.main(["daftar", "--prodi", A]) == 0, "baris perintah: daftar")
    os.environ["PRODI_MODE"] = "produksi"
    cek(ih.main(["contoh", "--prodi", B]) == 1 and ih.terbit(B, "sejarah") is None, "contoh ditolak di produksi")
    os.environ.pop("PRODI_MODE")
    sebelum = ih.terbit(A, "kerja-sama")
    cek(ih.main(["contoh", "--prodi", A]) == 0 and ih.terbit(A, "kerja-sama") == sebelum
        and ih.terbit(A, "sejarah") is not None, "contoh hanya mengisi halaman kosong")
    cek(ih.main(["tarik", "--prodi", A, "--halaman", "sejarah"]) == 0 and ih.terbit(A, "sejarah") is None, "baris perintah: tarik")
    cek(ih.main(["daftar", "--prodi", "../x"]) == 1, "kode prodi aneh ditolak")
finally:
    shutil.rmtree(KERJA, ignore_errors=True)

for g in gagal:
    print("GAGAL", g)
print("uji_isi_halaman: %d templat, %s" % (len(ih.TEMPLAT), "LULUS" if not gagal else "%d gagal" % len(gagal)))
sys.exit(1 if gagal else 0)
