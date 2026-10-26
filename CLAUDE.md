# Platform Website Program Studi UNSRAT — prodi.unsrat.ac.id

Satu platform untuk situs ke-97 program studi Universitas Sam Ratulangi, di `prodi.unsrat.ac.id/<slug>/`
(mis. `/s1informatika/`). Dibangun in-house oleh UPA TIK UNSRAT. Situs dipakai untuk **akreditasi** tiap prodi
(BAN-PT dan LAM), jadi struktur menunya mengikuti kriteria akreditasi dan seragam di semua prodi.

## Konteks singkat
- Saudara proyek: `../website-unsrat-2026` (www.unsrat.ac.id). Data resmi prodi (nama, jenjang, gelar, SKS, CPL,
  bidang kerja, akreditasi) **bersumber dari www** dan hanya mengalir satu arah, www → prodi (K-P6).
- Pengelola: superadmin (UPA TIK), admin prodi (koordinator prodi), operator prodi. Mereka bukan developer —
  antarmuka harus sederhana dan sulit dirusak. Tidak ada peran admin fakultas (K-P2).
- Audiens: asesor akreditasi, calon mahasiswa, mahasiswa, alumni, pengguna lulusan. Banyak pengguna ponsel dengan
  koneksi terbatas di Indonesia Timur.
- Bahasa: Indonesia; bahasa Inggris di `/<slug>/en/` menyusul (Fase 5, alamatnya sudah dicadangkan).

## Dokumen (baca bagian yang relevan sebelum mengerjakan fitur)
- `docs/rencana-fase-01.md` — rencana Fase 1 yang disetujui: arsitektur, model data, peran, template, urutan kerja.
- `docs/keputusan.md` — log keputusan (K-P1, …). Tambahkan entri setiap ada keputusan baru.
- `docs/asal-modul.md` — modul yang disalin dari repo www beserta versi asalnya.
- `platform/data-awal/slug.csv` — slug 97 prodi yang disetujui. Kunci tetap prodi adalah `kode_pddikti`, bukan slug.
- Log hasil setiap langkah/fase ditulis ke `docs/log/`.

## Arsitektur (sudah diputuskan)
- Generator halaman statis (Python + Jinja2) + admin Flask, pola yang sama dengan www (K-P7).
- Stack Docker sendiri `prodi-unsrat` di VM yang sama dengan www, lewat Portainer (K-P5): `prodi-web` (Nginx),
  `prodi-admin` (Flask + generator), `prodi-pemantau`. Port menyusul (K-P13).
- Data www dibaca dari volume data stack www yang dipasang **hanya-baca**. Repo ini tidak pernah menulis ke www.
- Akun per orang di SQLite (pustaka standar), sandi argon2, tanpa 2FA tetapi wajib sandi kuat (K-P10).
  Tanpa SMTP: sandi diganti pemilik akun atau direset superadmin (K-P12).
- Logo dan unggahan di Google Cloud Storage, bucket www, folder `prodi/` (K-P11).
- Server web hanya menyajikan folder publik hasil rakitan *allow-list*; data mentah, skrip, dan riwayat tidak pernah
  ikut tersaji.

## Struktur
```
platform/admin/      Flask: akun, peran, superadmin, admin prodi
platform/bangun/     generator + perakit folder publik
platform/template/   template induk: menu.json, halaman Jinja2, aset
platform/data-awal/  slug.csv, palet warna
platform/pemantau/   cek integritas & saringan spam judi
uji/                 skrip uji; python uji/jalankan-semua.py
docker/              Dockerfile web, konfigurasi Nginx, skrip mulai
```

## Perintah
- Lingkungan Python sekali saja: `python3 -m venv .venv && .venv/bin/pip install -r platform/admin/requirements.txt -c platform/admin/constraints.txt`.
- Semua uji: `.venv/bin/python uji/jalankan-semua.py` (dari akar repo). Uji memakai folder sementara, tidak menyentuh `data/`.
- Lokasi data (`platform/lokasi.py`): `PRODI_DATA` (bawaan `data/`), `PRODI_RIWAYAT` (bawaan `riwayat/` di sampingnya),
  `WWW_DATA` (bawaan `../website-unsrat-2026/site/mockup/data`, hanya dibaca).
- Tarik data resmi dari www: `python3 platform/tarik_www.py` (pratinjau), `--terapkan` (tulis; salinan lama ke riwayat).
- Registri awal 97 prodi dari `slug.csv`: `python3 platform/registri.py --siapkan` (sesudah tarik data pertama).
- Bangun situs ke `publik/`: `.venv/bin/python platform/bangun/bangun.py` (semua), `--prodi <kode>` (satu prodi),
  `--produksi`. Ganti slug atau nonaktifkan prodi: bangun semua, supaya folder lama terhapus.
- Pengumuman (sebelum admin ada): `.venv/bin/python platform/pengumuman.py tambah|daftar|status --prodi <kode> ...`;
  foto/PDF lewat `platform/media.py` (`PRODI_PENYIMPANAN=lokal` ke `unggahan/`, `gcs` ke bucket). Lalu bangun `--prodi`.
- Bagian depan beranda (sebelum admin ada): `.venv/bin/python platform/tampilan_prodi.py lihat|atur|foto --prodi <kode>`.
  Nilai kartu resmi (akreditasi, gelar, SKS) tidak pernah boleh ditimpa (K-P15).
- Admin (langkah 4): sekali `python3 platform/admin/siapkan.py` (kunci sesi di `rahasia/.env`), lalu
  `.venv/bin/python platform/admin/siapkan.py --superadmin <nama> --nama-lengkap "..."` (sandi sementara ditulis ke
  `rahasia/.kredensial-<nama>.txt`); jalankan `.venv/bin/python platform/admin/app.py` → http://127.0.0.1:8791/.
- Setiap rute admin wajib `@akses(...)` (`platform/admin/akses.py`) dan wajib masuk matriks di `uji/uji_admin.py`
  (uji gagal bila ada rute baru yang belum diuji untuk semua peran).
- Halaman superadmin di `platform/admin/superadmin.py`. Perubahan yang memengaruhi situs memanggil bangun ulang lewat
  `platform/admin/pembangun.py`; `PRODI_BANGUN=latar` (bawaan, utas latar), `sinkron` (uji), `mati` (uji akses).
- Template: `platform/template/menu.json` (menu induk), `platform/template/kategori.json` (kategori pengumuman), `platform/template/halaman/*.html` (Jinja2, autoescape),
  `platform/template/aset/css/prodi.css`; palet pilihan `platform/data-awal/palet.json`, uji kontras di `platform/bangun/warna.py`.

## Cara kerja
- Tugas yang menyentuh lebih dari satu file: ajukan rencana dulu dan tunggu persetujuan.
- Satu langkah rencana = satu branch `fase/NN-L-nama` (mis. `fase/01-2-data`). Commit kecil, Conventional Commits,
  deskripsi boleh Bahasa Indonesia. Jangan commit langsung ke `main`.
- Setiap langkah ditinjau manusia sebelum langkah berikutnya dimulai. Tulis log ke `docs/log/`.
- Nama fungsi/variabel dan teks antarmuka berbahasa Indonesia (seperti repo www); komentar dan docstring
  berbahasa Inggris.
- Jangan mengarang fakta institusi: angka, nama pejabat, akreditasi, teks kebijakan. Data kosong tampil sebagai
  "sedang dilengkapi" dan dicatat, bukan diisi tebakan.
- Jangan mengubah nama resmi prodi; nama datang dari www.
- Menambah paket Python baru: tanya dulu. Versi dikunci di `platform/admin/constraints.txt`.
- Modul yang disalin dari www: perbaikan keamanan di www juga diterapkan di sini (lihat `docs/asal-modul.md`).

## Keamanan (tidak bisa ditawar)
- Tidak ada kredensial di repo. Rahasia di `.env` / volume rahasia; `.env.example` tanpa nilai.
- Jangan menjalankan perintah apa pun ke server staging/produksi.
- **Pembatasan akses per prodi diperiksa di server** pada setiap rute yang memuat kode prodi. Setiap rute baru
  masuk ke uji matriks peran × rute.
- Admin hanya dari jaringan UNSRAT atau VPN (`ADMIN_IP_BOLEH`).
- Escape semua keluaran (Jinja2 autoescape), CSRF di setiap formulir, CSP tanpa skrip *inline*.
- Unggahan: hanya JPEG/PNG/SVG tersanitasi (`gambar_aman.py`, `svg_aman.py`); semua teks lewat `saringan_spam.py`.
- Konteks ancaman nyata: domain `.ac.id` sering disusupi konten judi online lewat CMS lemah, unggahan berbahaya,
  dan akun admin curian.

## Standar minimum setiap halaman
- WCAG 2.1 AA: keyboard penuh, fokus terlihat, kontras sesuai token, satu `h1`, heading berurutan, `lang` benar.
- Tetap berfungsi tanpa JavaScript. JS frontend ≤ 100 KB gzip per halaman. Tanpa slider/carousel.
- Responsif dari lebar 320 px; tanpa scroll horizontal kecuali tabel di dalam wadahnya.
