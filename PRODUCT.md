# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Pengunjung halaman akar `prodi.unsrat.ac.id/` adalah campuran yang sama penting (dikonfirmasi 25 November 2026):
calon mahasiswa, mahasiswa, alumni, asesor akreditasi (BAN-PT dan LAM), dan pengguna lulusan. Pekerjaan mereka di
halaman ini: menemukan satu program studi di antara 97 dan masuk ke situsnya. Banyak yang membuka dari ponsel dengan
koneksi terbatas di Indonesia Timur.

## Product Purpose
Platform situs ke-97 program studi Universitas Sam Ratulangi (Manado), satu situs per prodi di
`prodi.unsrat.ac.id/<slug>/`, dipakai terutama untuk akreditasi. Halaman akar adalah pintu masuk dan direktori:
berhasil bila pengunjung sampai ke situs prodi yang dicarinya dengan cepat dan yakin itu prodi yang benar (nama,
jenjang, fakultas, akreditasi).

## Positioning
Satu-satunya direktori resmi yang memuat ke-97 prodi UNSRAT dengan data resmi yang sama dengan www.unsrat.ac.id
(nama, jenjang, gelar, fakultas, akreditasi), dan setiap prodi punya situs lengkap dengan struktur seragam mengikuti
kriteria akreditasi.

## Operating Context
- Situs statis hasil generator Python + Jinja2; halaman akar dirender dari `platform/template/halaman/akar.html` oleh
  `bangun_akar` di `platform/bangun/bangun.py`, dengan data efektif prodi dan unit (fakultas) dari www.
- Prodi dikelompokkan per jenjang: Sarjana (S1), Magister (S2), Doktor (S3), Profesi, Spesialis dan Subspesialis.
- Pengelola situs adalah superadmin UPA TIK, admin prodi, dan operator, bukan pengembang.

## Capabilities and Constraints
- Cakupan desain baru (dikonfirmasi): **direktori akar saja**. Situs tiap prodi dan halaman isinya tetap seperti
  sekarang; gaya bersama (`prodi.css`, `dasar.html`) tidak boleh berubah bagi situs prodi.
- Standar setiap halaman (CLAUDE.md): WCAG 2.1 AA, satu `h1`, heading berurutan, fokus terlihat; tetap berfungsi tanpa
  JavaScript; JavaScript ≤ 100 KB gzip, tanpa skrip inline (CSP), tanpa skrip pihak ketiga; tanpa slider/carousel;
  responsif dari 320 px tanpa scroll horizontal.
- Semua keluaran di-escape; tidak ada fakta institusi yang dikarang. Data kosong tampil sebagai "sedang dilengkapi".
- Versi bahasa Inggris (`/<slug>/en/`) hanya untuk prodi yang saklarnya menyala; halaman akar saat ini hanya
  berbahasa Indonesia.
- Belum diputuskan: pencarian prodi di halaman akar (rencana awal menyebutnya "fase 3").

## Brand Commitments
- **Lambang UNSRAT** (`platform/template/aset/img/lambang-*.png`) wajib dipertahankan.
- **Warna bendera per fakultas** wajib dipertahankan: setiap prodi tetap membawa warna fakultasnya (data `bendera`
  di `unit.json` www: `dasar` dan `tulisan`).
- Warna resmi UNSRAT (`tokens.css`, biru #3500ff dan kuning #f2b705 dari Statuta) ada di kode, tetapi tidak dipilih
  sebagai komitmen wajib untuk halaman akar.

## Evidence on Hand
- Data resmi 97 prodi: nama, jenjang, gelar, fakultas/unit, akreditasi, nama Inggris (`platform/data-awal/www/`).
- Bendera 11 fakultas dan Program Pascasarjana (`unit.json`).
- Tidak ada foto kampus, testimoni, statistik pendaftaran, atau peringkat di repo. Jangan dikarang.

## Product Principles
- Temukan prodi secepat mungkin: nama, jenjang, dan fakultas terbaca sekilas, juga di ponsel.
- Data resmi, apa adanya: tidak ada klaim atau angka yang tidak ada di data www.
- Ringan dan tahan koneksi buruk: HTML lebih dulu, tanpa ketergantungan JavaScript.
- Satu keluarga UNSRAT: lambang dan warna fakultas membuat setiap prodi dikenali.

## Accessibility & Inclusion
WCAG 2.1 AA wajib, termasuk kontras warna fakultas yang sebagian sangat terang (Pertanian #00FF01, MIPA putih):
warna bendera tidak boleh menjadi satu-satunya pembawa teks atau makna.
