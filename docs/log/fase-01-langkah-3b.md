# Fase 1 · Langkah 3b — Pengumuman dan berita (26 Oktober 2026)

Branch: `fase/01-3b-pengumuman` (bercabang dari `fase/01-3-template`). Keputusan: K-P14.

## Yang dikerjakan
- **Model data** `platform/pengumuman.py` → `prodi/<kode>/pengumuman.json`.
  - Isian: judul, tanggal, kategori, ringkasan (wajib), isi teks biasa (paragraf, daftar "- ", tautan https otomatis),
    foto (1 utama + 6 galeri), PDF (maks. 3), sematkan, tanggal kedaluwarsa.
  - Status `draf` → `menunggu` → `terbit` → `ditarik`; tidak ada hapus permanen, setiap perubahan masuk riwayat.
  - Alamat tetap dari tanggal + judul (`2026-10-20-jadwal-uts`), tidak berubah walau judul diubah.
  - Ditolak: HTML di teks mana pun, teks judi, teks terlalu panjang, kategori/tanggal tidak sah, foto tanpa teks
    alternatif, alamat berkas yang tidak dibuat sistem (mis. `../../`).
  - Perintah baris `tambah | daftar | status` sampai formulir admin ada (langkah 6).
- **Kategori** `platform/template/kategori.json`: Pengumuman Akademik, Berita Kegiatan, Prestasi Mahasiswa, Prestasi
  Dosen, Penelitian dan Publikasi, Pengabdian kepada Masyarakat, Kerja Sama.
- **Unggahan** `platform/media.py`.
  - Foto JPEG/PNG ≤ 10 MB, lebar ≥ 600 px, dikodekan ulang ke JPEG 1600/800/400 px (EXIF/GPS terbuang, PNG
    transparan diberi latar putih).
  - PDF ≤ 20 MB: harus PDF sah, berhalaman, tidak terkunci; ditolak bila berisi JavaScript/Launch/formulir
    kirim/berkas sisipan/RichMedia/XFA (pemeriksaan dari admin www) atau teks judi di 30 halaman pertama.
  - Penyimpanan `lokal` (pengembangan; diterbitkan generator ke `publik/unggahan/`) atau `gcs`
    (`<GCS_PREFIX>prodi/<kode>/`, `Content-Disposition: inline` untuk PDF). Nama acak, tidak pernah ditimpa.
- **Halaman** (generator + template):
  - Menu utama mendapat butir **Pengumuman**.
  - `/<slug>/pengumuman/` (12 per halaman, `/halaman/<n>/`), `/kategori/<id>/`, `/arsip/<tahun>/`, satu halaman per
    pengumuman, `rss.xml`.
  - Beranda prodi: "Pengumuman terbaru" = yang disematkan dan masih berlaku + 3 terbaru.
  - **Kabar terkait** otomatis di halaman akreditasi: Organisasi dan Prestasi, Prestasi dan Pengembangan Dosen,
    Penelitian, Publikasi, Pengabdian kepada Masyarakat, Kerja Sama.
  - PDF: pembaca bawaan browser di layar ≥ 760 px; tombol "Buka PDF" dan "Unduh" selalu ada; di ponsel pembacanya
    tidak dimuat sama sekali (hemat kuota).
  - Pratinjau tautan (Open Graph + Twitter card) di semua halaman prodi; foto utama pengumuman dipakai sebagai gambar.
  - CSP ditambah `frame-src 'self' https://storage.googleapis.com` untuk pembaca PDF.
  - `sitemap.xml` (produksi) kini disusun dari semua halaman yang ada di `publik/`, termasuk pengumuman.
- **Uji**: `uji/uji_pengumuman.py`; pemeriksa halaman dipindah ke `uji/pemeriksa_halaman.py` (dipakai bersama).

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 5 rangkaian, 0 gagal. `uji_pengumuman` mencakup: EXIF/GPS terbuang, GIF/WebP/berkas palsu ditolak, PDF
ber-JavaScript (juga nama tersamar `/J#61vaScript`), Launch, sisipan, terkunci, dan berteks judi ditolak; penyimpanan
lokal dan GCS (klien palsu) tidak menimpa; status draf/menunggu/ditarik tidak terbit dan tidak ditautkan; kedaluwarsa;
paging; kategori; arsip; kabar terkait; RSS; Open Graph; menarik pengumuman menghapus halaman dan berkasnya dari situs
tetapi berkas asli tetap tersimpan; bangun satu prodi tidak menghapus berkas prodi lain; sitemap produksi lengkap.

Diperiksa di browser: beranda S1 Teknik Informatika dengan 4 pengumuman **contoh** (bertanda [CONTOH], hanya di data
lokal komputer pengembang, tidak masuk Git), halaman daftar dengan saringan kategori, halaman pengumuman dengan foto dan
PDF terbuka di pembaca bawaan browser, "Kabar terkait" di halaman Kerja Sama, dan tampilan ponsel 375 px.

## Catatan untuk langkah berikutnya
- Langkah 6: formulir pengumuman (unggah foto/PDF, pratinjau), operator mengajukan → admin prodi menyetujui,
  peringatan privasi (jangan unggah NIK, nomor HP, nilai mahasiswa).
- Langkah 7: bangun ulang terjadwal harian supaya pengumuman kedaluwarsa turun dari beranda; volume `unggahan` bila
  memakai penyimpanan lokal, atau kredensial GCS untuk `PRODI_PENYIMPANAN=gcs`.
