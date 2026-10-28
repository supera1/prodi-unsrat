# Fase 2 langkah 7c — Halaman Tugas Akhir dengan kotak cari (K-P35 nomor 4–5)

Tanggal: 28 Oktober 2026. Branch: `fase/02-7c-tugas-akhir` (di atas `fase/02-7b-halaman-tambahan`).

## Latar
Pengguna menyetujui bahwa database skripsi dibuat sebagai tabel bawaan platform dengan impor Excel dan kotak cari,
bukan sematan, dan tanpa NIM (K-P35 nomor 4 dan 5). Contohnya, halaman WordPress Informatika, berisi 1.522 baris
(No, NIM, judul, dua pembimbing) yang ditempel dengan skrip pencarian inline.

## Yang dikerjakan
- **Menu:** halaman opsional **Tugas Akhir** (`akademik/tugas-akhir`) dengan tanda baru `bila_terisi`: hanya tampil di
  situs (dan menu) setelah prodi menerbitkan isinya, sehingga 97 situs tidak mendapat halaman kosong. Tanda itu hanya
  sah untuk halaman opsional (`menu.py`).
- **Templat isi** (`isi_halaman.py`): uraian dan "Daftar tugas akhir": judul (wajib), tahun lulus, mahasiswa,
  pembimbing 1, pembimbing 2, tautan naskah; tanpa NIM; sampai 5.000 baris; tanda `lewat_excel`.
- **Penyunting** (`penyunting.py`): tabel `lewat_excel` tidak dirender sebagai ribuan isian, tetapi 20 baris pertama
  (hanya baca), jumlah barisnya, dan tautan **Impor dari Excel**; menyimpan bagian lain halaman tidak mengubah tabelnya.
  Batas ukuran formulir tidak menghitung tabel seperti itu.
- **Impor Excel** (`impor_tabel.py`): paling banyak 5.000 baris per berkas (sebelumnya 2.000); kolom bisa dikenali
  lewat nama lain (`alias`): Judul Skripsi, Dosen Pembimbing 1/2, Pembimbing I/II, Nama Mahasiswa, …; No dan NIM
  diabaikan dan disebut di pratinjau.
- **Situs:**
  - setiap tabel 30 baris atau lebih diberi tanda `data-cari`, dan halamannya memuat `aset/js/cari-tabel.js`
    (2 KB, `defer`): kotak **Cari di tabel ini** dengan jumlah baris yang tampil diumumkan (`aria-live`). Semua kata
    harus ada di baris; huruf besar dan aksen diabaikan. Skrip hanya menulis teks, tanpa `innerHTML`, tanpa host lain.
    Tanpa JavaScript seluruh tabel tetap tampil;
  - kolom yang kosong di semua baris tidak ditampilkan (semua tabel), misalnya Mahasiswa pada data yang hanya punya
    judul dan pembimbing.
- **Uji lama yang disesuaikan:**
  - `uji_fase1.py` dulu menuntut situs tanpa berkas JavaScript sama sekali. Kini mengikuti standar CLAUDE.md:
    JavaScript hanya di `aset/js` (paling banyak 100 KB gzip), tanpa skrip inline, dan halaman tetap berfungsi tanpanya;
  - `pemeriksa_halaman.py` menerima `<script src="…aset/js/…?v=…" defer>`;
  - `uji_bangun.py` tidak menghitung halaman `bila_terisi` yang kosong;
  - `uji_isi_halaman.py` mengharapkan halaman `bila_terisi` tidak ada di prodi lain.
- **Dokumen:** K-P35 (pelaksanaan nomor 4–5), K-P34 (batas 5.000 baris), panduan admin prodi (bagian "Tugas Akhir"
  dan kotak cari), `docs/kriteria-akreditasi.md` (Tugas Akhir di "Halaman tanpa kriteria"), rencana §8, CLAUDE.md.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 22 rangkaian lulus.
- **`uji/uji_tugas_akhir.py`** (baru, 26 pemeriksaan):
  - menu dan tanda `bila_terisi`;
  - berkas gaya prodi 1.600 baris (No dan NIM diabaikan, nama kolom lain dikenali), batas 5.000/5.001 baris;
  - operator mengimpor lewat admin; penyunting hanya meringkas (< 200 KB) dan menyimpan tanpa kehilangan baris;
  - admin menerbitkan: 1.600 baris di situs, tanda kotak cari, skrip `defer`, kolom kosong hilang, tanpa NIM, ukuran
    gzip, pemeriksaan halaman bersama;
  - tabel pendek tanpa kotak cari; skrip kecil yang hanya menulis teks.
- **Uji mutasi:** 14 aturan dimatikan satu per satu; setiap kali ada uji yang gagal.
- **Dilihat di browser** (situs sementara, 1.600 baris dengan nama dosen rekaan): kotak cari muncul di atas tabel;
  "kolintang 2015" menyaring menjadi "33 dari 1600 baris", sesuai hitungan data; kolom Mahasiswa yang kosong tidak tampil.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data.
- Halaman bertabel panjang lain (publikasi, penelitian, mata kuliah) juga otomatis mendapat kotak cari.
