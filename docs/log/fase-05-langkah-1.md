# Fase 5 langkah 1 — Kerangka versi bahasa Inggris (K-P37)

Tanggal: 19 November 2026. Branch: `fase/05-1-kerangka-en`.

## Latar
Langkah pertama [rencana Fase 5](../rencana-fase-05.md): versi Inggris `/<slug>/en/` dengan halaman dari data resmi
berbahasa Inggris, tombol bahasa, `hreflang`, sitemap, dan saklar per prodi. Isi yang diisi prodi menyusul di langkah 2.

## Yang dikerjakan
- **Kamus** `platform/template/teks-en.json` dan modul `platform/bahasa.py`:
  - teks tetap templat situs ditulis dalam bahasa Indonesia di dalam `_("...")`. Halaman Indonesia mendapat teks itu
    sendiri, sehingga keluarannya tidak berubah; halaman Inggris mendapat terjemahannya dari kamus;
  - teks yang belum ada di kamus menghentikan pembangunan halaman Inggris, dan `python3 platform/bahasa.py periksa`
    serta uji memastikan semua teks templat ada;
  - kamus juga memuat label dan pilihan templat isi (untuk langkah 2), peringkat akreditasi (Unggul → Excellent), dan
    tautan universitas; 237 teks;
  - nama prodi Inggris dari `nama_en`: "Bachelor Program in Informatics Engineering"; nama yang sudah menyebut
    profesi dipakai apa adanya. Jenjang, tanggal, dan bagian depan beranda juga punya bentuk Inggris.
- **Menu induk** (`menu.json`): `label_en` dan `deskripsi_en` untuk ke-39 butir, wajib menurut `menu.py`.
- **Generator** (`bangun.py`):
  - lingkungan templat per bahasa; `akar` (`<slug>` atau `<slug>/en`) untuk tautan di dalam situs prodi;
  - `/<slug>/en/` hanya untuk prodi yang registrinya bertanda `inggris`, berisi halaman dari data resmi: beranda, Profil
    Lulusan dan CPL, Spesifikasi, Akreditasi (status), Dosen Tetap, Kalender (menautkan kalender Indonesia, karena www
    belum punya versi Inggris), dan Kontak, serta kelompok menu yang memuat halaman itu. Pengumuman dan halaman yang diisi
    prodi belum ada di versi Inggris dan tidak ditautkan;
  - bagian depan beranda Inggris dari data resmi; teks depan berbahasa Indonesia milik prodi tidak dipakai, sedangkan
    latar dan urutan kartu resmi dipakai;
  - halaman yang punya dua bahasa mendapat `<link rel="alternate" hreflang>` dengan alamat lengkap dan tombol
    **English / Bahasa Indonesia** di bar atas (tautan biasa, tanpa JavaScript);
  - `sitemap.xml` (produksi) memuat halaman Inggris dengan pasangan `xhtml:link hreflang`.
- **Superadmin:** kartu **Versi bahasa Inggris** di detail prodi, rute `POST /super/prodi/<kode>/inggris` (masuk
  matriks akses), log audit `inggris-diaktifkan` / `inggris-dinonaktifkan`, lalu situs prodi dibangun ulang.
- **Pemeriksa halaman** (`uji/pemeriksa_halaman.py`): halaman di `<slug>/en/` wajib `lang="en"`, yang lain `lang="id"`.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 23 rangkaian lulus.
- **`uji/uji_inggris.py`** (baru):
  - kamus lengkap untuk templat, templat isi, dan menu; penanda `%s` sama; teks tanpa terjemahan menghentikan halaman
    Inggris; nama, tanggal, dan peringkat akreditasi Inggris;
  - tanpa saklar tidak ada `/en/`; dengan saklar tepat 10 halaman Inggris; prodi lain tidak terpengaruh;
  - setiap halaman Inggris: `lang="en"`, tanpa teks tetap Indonesia, `hreflang` dua arah, tombol bahasa dua arah,
    dan setiap tautannya menuju halaman yang ada, tidak pernah ke halaman yang belum berversi Inggris;
  - beranda, CPL, akreditasi, kontak, dan kalender Inggris; JSON-LD `inLanguage`;
  - halaman Indonesia tanpa versi Inggris tidak berubah; pemeriksaan halaman dan cek integritas bersih;
  - produksi: alamat kanonik dan sitemap dua bahasa; saklar superadmin menyalakan dan mematikan `/en/`, tercatat di log.
- **Keluaran Indonesia tidak berubah:** situs lokal dibangun ulang dengan kode ini dan dibandingkan dengan hasil bangun
  dari `main`: 0 berkas berbeda.
- **Dilihat di browser** (situs sementara dari data awal www, versi Inggris aktif untuk S1 Teknik Informatika):
  beranda, Profil Lulusan dan CPL, dan tombol bahasa di layar 1280 px; halaman Spesifikasi di layar 375 px tanpa gulir
  datar.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Registri lama tanpa tanda `inggris` berarti versi
  Inggris nonaktif.
- Langkah 2 menambah isi Inggris di penyunting; sampai itu, versi Inggris sengaja hanya memuat halaman dari data resmi.
