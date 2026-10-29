# Platform Website Program Studi UNSRAT — prodi.unsrat.ac.id

Satu platform untuk situs ke-97 program studi Universitas Sam Ratulangi, di `prodi.unsrat.ac.id/<slug>/`
(mis. `/s1informatika/`). Dibangun in-house oleh UPA TIK UNSRAT. Situs dipakai untuk **akreditasi** tiap prodi
(BAN-PT dan LAM), jadi struktur menunya mengikuti kriteria akreditasi dan seragam di semua prodi.

## Konteks singkat
- Saudara proyek: `../website-unsrat-2026` (www.unsrat.ac.id). Data resmi prodi (nama, jenjang, gelar, SKS, CPL,
  bidang kerja, akreditasi) **ditarik dari www**; superadmin dan admin prodi boleh mengubahnya di halaman Data prodi
  sebagai timpaan per kolom yang tetap dipakai walau www berubah (K-P16, `platform/data_prodi.py`).
- Pengelola: superadmin (UPA TIK), admin prodi (koordinator prodi), operator prodi. Mereka bukan developer —
  antarmuka harus sederhana dan sulit dirusak. Tidak ada peran admin fakultas (K-P2).
- Audiens: asesor akreditasi, calon mahasiswa, mahasiswa, alumni, pengguna lulusan. Banyak pengguna ponsel dengan
  koneksi terbatas di Indonesia Timur.
- Bahasa: Indonesia; bahasa Inggris di `/<slug>/en/` menyusul (Fase 5, alamatnya sudah dicadangkan).

## Dokumen (baca bagian yang relevan sebelum mengerjakan fitur)
- `docs/rencana-fase-01.md` — rencana Fase 1 (selesai): arsitektur, model data, peran, template, urutan kerja.
- `docs/rencana-fase-02.md` — rencana Fase 2: penyunting halaman wajib, alur isi, kelengkapan, pilot 3 prodi.
- `docs/keputusan.md` — log keputusan (K-P1, …). Tambahkan entri setiap ada keputusan baru.
- `docs/asal-modul.md` — modul yang disalin dari repo www beserta versi asalnya.
- `docs/panduan-admin-prodi.md` — panduan untuk admin prodi dan operator (juga menu Panduan di admin);
  `docs/pilot-fase-02.md` — persiapan pilot; `docs/kriteria-akreditasi.md` — draf label kriteria untuk LPMPP.
- `platform/data-awal/slug.csv` — slug 97 prodi yang disetujui. Kunci tetap prodi adalah `kode_pddikti`, bukan slug.
- Log hasil setiap langkah/fase ditulis ke `docs/log/`; ringkasan Fase 1 (kriteria, verifikasi manual, sisa pekerjaan):
  `docs/log/fase-01.md`.

## Arsitektur (sudah diputuskan)
- Generator halaman statis (Python + Jinja2) + admin Flask, pola yang sama dengan www (K-P7).
- Stack Docker `prodi-unsrat` di **VM sendiri**, di-deploy admin UNSRAT dari GitHub `supera1/prodi-unsrat` dengan
  `docker compose`, tanpa Portainer (K-P17):
  `web` (Nginx), `admin` (Flask + generator, waitress), `pemantau`. Panduan admin VM: `docs/deploy.md`. Port bawaan
  8080/8081, nilai akhir disepakati admin VM (K-P13). HTTPS di load balancer (bawaan) atau di VM (`HTTPS_DI_VM=1`).
- Semua uji berjalan saat image admin dibangun (K-P20); kontainer web hanya menerima baris pengalihan slug yang sah
  dari generator dan memuat ulang Nginx sendiri (K-P21).
- Data www **diunggah superadmin** (Excel ekspor prodi dari www, atau berkas JSON www; K-P18; `platform/impor_www.py`).
  VM baru mulai dari salinan `platform/data-awal/www/`. Folder `WWW_DATA` hanya untuk komputer pengembang. Repo ini
  tidak pernah menulis ke www.
- Akun per orang di SQLite (pustaka standar), sandi argon2, tanpa 2FA tetapi wajib sandi kuat (K-P10).
  Tanpa SMTP: sandi diganti pemilik akun atau direset superadmin (K-P12).
- Logo dan unggahan di volume lokal VM prodi (`PRODI_PENYIMPANAN=lokal`, K-P19); kode GCS tetap ada sebagai pilihan.
- Server web hanya menyajikan folder publik hasil rakitan *allow-list*; data mentah, skrip, dan riwayat tidak pernah
  ikut tersaji.

## Struktur
```
platform/admin/      Flask: akun, peran, superadmin, admin prodi
platform/bangun/     generator + perakit folder publik
platform/template/   template induk: menu.json, halaman Jinja2, aset
platform/data-awal/  slug.csv, palet warna, www/ (salinan data www untuk VM baru)
platform/pemantau/   cek integritas & saringan spam (judi, pinjol, ijazah, obat)
uji/                 skrip uji; python uji/jalankan-semua.py
docker/              Dockerfile web, konfigurasi Nginx, skrip mulai, cadangan/pulihkan (Dockerfile admin di akar)
```

## Perintah
- Lingkungan Python sekali saja: `python3 -m venv .venv && .venv/bin/pip install -r platform/admin/requirements.txt -c platform/admin/constraints.txt`.
- Semua uji: `.venv/bin/python uji/jalankan-semua.py` (dari akar repo). Uji memakai folder sementara, tidak menyentuh `data/`.
  `uji/uji_fase1.py` adalah uji penerimaan Fase 1 (kriteria rencana §11 pada data www asli, termasuk setiap nilai resmi
  ke-97 prodi dibandingkan dengan `prodi.json` www).
- Lokasi data (`platform/lokasi.py`): `PRODI_DATA` (bawaan `data/`), `PRODI_RIWAYAT` (bawaan `riwayat/` di sampingnya),
  `WWW_DATA` (bawaan `../website-unsrat-2026/site/mockup/data`, hanya dibaca).
- Tarik data resmi dari www: `python3 platform/tarik_www.py` (pratinjau), `--terapkan` (tulis; salinan lama ke riwayat).
- Registri awal 97 prodi dari `slug.csv`: `python3 platform/registri.py --siapkan` (sesudah tarik data pertama). Tautan
  dosen awal ikut dari `platform/data-awal/dosen.csv` (K-P31; format templat impor Tautan dosen), di setiap jalur
  pembuatan registri (VM baru, `--siapkan`, unggahan data www pertama).
- Unggahan data www (Excel/JSON) dibaca `platform/impor_www.py` lalu dipratinjau/diterapkan `tarik_www.py`.
  Data awal VM baru: `python3 platform/impor_www.py --isi-awal` (platform kosong saja); perbarui salinannya setelah
  menarik data www terbaru: `python3 platform/impor_www.py --tulis-data-awal --dari "..."`.
- Stack Docker lokal: `docs/deploy.md` §13 (`docker compose -p prodi-uji ...`). `uji/uji_docker.py` memeriksa berkas
  stack tanpa Docker; setiap variabel stack wajib ada di `.env.example` (tanpa nilai) dan `docs/deploy.md`.
- Bangun situs ke `publik/`: `.venv/bin/python platform/bangun/bangun.py` (semua), `--prodi <kode>` (satu prodi),
  `--produksi`. Ganti slug atau nonaktifkan prodi: bangun semua, supaya folder lama terhapus.
- Pengumuman (sebelum admin ada): `.venv/bin/python platform/pengumuman.py tambah|daftar|status --prodi <kode> ...`;
  foto/PDF lewat `platform/media.py` (`PRODI_PENYIMPANAN=lokal` ke `unggahan/`, `gcs` ke bucket). Lalu bangun `--prodi`.
- Isi halaman wajib/opsional dan dokumen halaman Akreditasi (Fase 2, K-P23, K-P29): templat, pemeriksaan, draf, dan
  tampilannya di `platform/isi_halaman.py`;
  disimpan di `data/prodi/<kode>/halaman-<id>.json` (`terbit`, `draf` berstatus draf/menunggu/dikembalikan, `versi`).
  Penyunting di admin (menu prodi "Isi halaman", K-P24, K-P27, K-P28): rute `platform/admin/isi_admin.py` (operator
  menulis/mengajukan; admin menerbitkan/mengembalikan/menarik; riwayat per halaman; kelengkapan superadmin
  `/super/kelengkapan` + CSV), formulir dari templat `platform/admin/penyunting.py`.
  Untuk pengembang: `.venv/bin/python platform/isi_halaman.py daftar|contoh|tarik --prodi <kode>` (`contoh` hanya untuk
  melihat tampilan, bertanda `[CONTOH]`, ditolak di produksi). Templat situs: `platform/template/halaman/isi.html` +
  `_isi.html`; pratinjau admin memakai makro yang sama (`bangun.bagian_html`).
- Halaman tambahan prodi (K-P35): daftar di `platform/halaman_tambahan.py` (`data/prodi/<kode>/tambahan.json`, alamat
  `/<slug>/halaman/<alamat>/`), isinya halaman `isi_halaman` dengan `TEMPLAT_TAMBAHAN` (id `x` + 6 heksa,
  `templat_halaman()`); admin di `platform/admin/tambahan_admin.py`. Sematan hanya dari daftar tetap di
  `platform/sematan.py` (Google Docs/Sheets/Slides/Forms/Drive/Calendar/Maps, YouTube); daftar itu juga mengisi CSP
  `frame-src` (`bangun.CSP`, `docker/nginx/header-keamanan.conf`) dan pemantau. Jangan menambah layanan tanpa keputusan
  baru. Bagian Sematan yang sama ada di setiap halaman bawaan, di bawah uraian (`isi_halaman.sematan_daftar`, disisipkan
  `halaman()`; K-P36).
- Halaman Tugas Akhir (K-P35): halaman opsional `bila_terisi` (tampil hanya setelah terisi); tabelnya `lewat_excel`
  (penyunting hanya meringkas, diubah lewat impor Excel), tanpa NIM. Tabel ≥ 30 baris di situs mendapat kotak cari
  `platform/template/aset/js/cari-tabel.js` (satu-satunya JavaScript situs; tanpa skrip inline, situs tetap berfungsi
  tanpa JavaScript).
- Impor Excel tabel besar (K-P34): `platform/admin/impor_tabel.py` (templat .xlsx, pratinjau, tambah/ganti ke draf
  halaman; tautan "Impor dari Excel" di penyunting). Tabel yang memenuhi syarat dihitung dari templat isi
  (`tabel_halaman`), jadi tabel baru di `isi_halaman.TEMPLAT` ikut otomatis bila syaratnya terpenuhi.
- Label kriteria akreditasi (K-P25, K-P29, K-P33): diisi admin prodi di menu prodi "Kriteria akreditasi"
  (`platform/admin/kriteria_admin.py`, `data/prodi/<kode>/kriteria.json`). `platform/template/kriteria.json` +
  `platform/kriteria.py` berisi usulan bersama; lembaga berstatus `dikonfirmasi` hanya dipakai prodi yang belum mengisi
  sendiri. `python3 platform/kriteria.py periksa|tabel`; tabelnya disalin ke `docs/kriteria-akreditasi.md` (uji
  memastikan sama). Pengembang tidak mengisi kriteria LAM tanpa daftar dari LPMPP.
- Bagian depan beranda (sebelum admin ada): `.venv/bin/python platform/tampilan_prodi.py lihat|atur|foto --prodi <kode>`.
  Nilai kartu resmi (akreditasi, gelar, SKS) tidak pernah boleh ditimpa (K-P15).
- Admin (langkah 4): sekali `python3 platform/admin/siapkan.py` (kunci sesi di `rahasia/.env`), lalu
  `.venv/bin/python platform/admin/siapkan.py --superadmin <nama> --nama-lengkap "..."` (sandi sementara ditulis ke
  `rahasia/.kredensial-<nama>.txt`); jalankan `.venv/bin/python platform/admin/app.py` → http://127.0.0.1:8791/.
- Setiap rute admin wajib `@akses(...)` (`platform/admin/akses.py`) dan wajib masuk matriks di `uji/uji_admin.py`
  (uji gagal bila ada rute baru yang belum diuji untuk semua peran).
- Halaman admin prodi di `platform/admin/prodi_admin.py` (data, identitas, beranda, menu, riwayat, berkas),
  `platform/admin/pengumuman_admin.py` (operator menulis/mengajukan, admin menerbitkan/mengembalikan/menarik), dan
  `platform/admin/isi_admin.py` (isi halaman: daftar, penyunting, draf, pratinjau; operator juga).
- Panduan admin prodi: `docs/panduan-admin-prodi.md`, juga tampil di admin (`/panduan`, `platform/admin/panduan.py`;
  Markdown sederhana, semua di-escape). Bila tombol, menu, batas, atau pesan admin berubah, perbarui panduannya:
  `uji/uji_pilot.py` memeriksanya. Masukan pengguna admin: `platform/admin/masukan_admin.py` (`masukan.json`).
  Persiapan pilot: `docs/pilot-fase-02.md`.
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
- Jangan mengubah nama atau data resmi prodi atas inisiatif sendiri; data datang dari www atau dari admin lewat halaman
  Data prodi. Situs selalu dibangun dari data efektif (`data_prodi.semua_efektif()`), bukan langsung dari `warisan/`.
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
- Produksi: admin hanya lewat HTTPS (`PRODI_MODE=produksi` tanpa `ADMIN_HTTPS=1` ditolak saat start); jaringan
  `ADMIN_IP_BOLEH`/`PROKSI_DEPAN` yang terlalu luas ditolak (`app.py`, `40-prodi-jaringan.sh`); isi bertanda `[CONTOH]`
  tidak pernah terbit di produksi (K-P32).
- Konteks ancaman nyata: domain `.ac.id` sering disusupi konten judi online lewat CMS lemah, unggahan berbahaya,
  dan akun admin curian.

## Standar minimum setiap halaman
- WCAG 2.1 AA: keyboard penuh, fokus terlihat, kontras sesuai token, satu `h1`, heading berurutan, `lang` benar.
- Tetap berfungsi tanpa JavaScript. JS frontend ≤ 100 KB gzip per halaman. Tanpa slider/carousel.
- Responsif dari lebar 320 px; tanpa scroll horizontal kecuali tabel di dalam wadahnya.
