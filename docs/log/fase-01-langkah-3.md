# Fase 1 · Langkah 3 — Template induk + generator (26 Oktober 2026)

Branch: `fase/01-3-template` (bercabang dari `fase/01-2-data`).

## Yang dikerjakan
- **Menu induk** `platform/template/menu.json`: Beranda, 6 kelompok (Profil, Akademik, Dosen dan Tendik, Riset dan PkM,
  Mahasiswa dan Alumni, Fasilitas), dan Kontak; 36 halaman per prodi.
  - 8 halaman `otomatis` (dari data www/registri): beranda, akreditasi, profil lulusan & CPL, spesifikasi, kalender,
    dosen tetap, kontak, ditambah halaman indeks tiap kelompok.
  - 23 halaman `wajib` (kebutuhan akreditasi) dan 2 `opsional` (jadwal, kelompok keahlian). Di Fase 1 halaman wajib
    berisi deskripsi + catatan "sedang dilengkapi"; isinya diedit di Fase 2.
- **Aturan menu** `platform/bangun/menu.py`: admin prodi boleh mengganti label (1–60 karakter, tanpa teks judi atau
  `< >`), mengurutkan dalam kelompok, dan menyembunyikan butir opsional. Pengaturan yang melanggar aturan diabaikan
  dan dilaporkan; situs tetap dibangun dengan menu induk.
- **Warna** `platform/bangun/warna.py` + `platform/data-awal/palet.json` (9 palet pilihan).
  - Setiap pasangan warna diuji kontras WCAG: teks putih di atas warna utama ≥ 4,5:1, teks gelap di atas aksen ≥ 4,5:1,
    garis aksen di samping warna utama ≥ 3:1, dll.
  - Bawaan: **warna bendera fakultas** dari `unit.json`. Ke-12 fakultas/pascasarjana lolos; Faperta, FH, dan FISIP
    digelapkan seperlunya, dan bila tulisan bendera putih/abu dipakai kuning UNSRAT sebagai aksen.
  - Warna per prodi ditulis ke `<slug>/warna.css` (hanya variabel CSS), sehingga CSP tetap tanpa gaya *inline*.
- **Generator** `platform/bangun/bangun.py` (Jinja2, autoescape): 97 situs = 3.591 halaman dalam ±5 detik.
  - Halaman akar `/` (daftar prodi per jenjang), `404.html`, `robots.txt`, `sitemap.xml` (produksi saja).
  - Mode staging (pita + `noindex`, robots melarang) dan produksi (`canonical`, sitemap) seperti www.
  - Semua tautan relatif (bisa disajikan di bawah jalur, mis. `/beta/`), kecuali `404.html`.
  - Versi aset `?v=<sidik>`, manifes SHA-256 untuk `cek_integritas.py`, `nginx-buatan/slug-lama.conf` untuk
    redirect 301 slug lama.
  - `--prodi <kode>` hanya menulis ulang situs satu prodi + halaman akar; prodi lain tidak disentuh.
- **Tampilan** `platform/template/aset/css/prodi.css` di atas token desain www: bar UNSRAT, kepala dengan lambang dan
  nama prodi, pita menu berwarna fakultas, menu ponsel tanpa JavaScript (`<details>`), jejak halaman, menu samping,
  kartu, tabel data, kaki halaman. Lambang diperkecil ke PNG 3–13 KB.
- **Data universitas**: `tarik_www.py` kini juga menyalin identitas, alamat, telepon, media sosial, dan tautan utilitas
  (hanya alamat `https://`) dari `situs.json` www ke `warisan/universitas.json`.
- `uji/uji_bangun.py`.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 4 rangkaian, 0 gagal. `uji_bangun` memeriksa setiap halaman (satu `h1`, `lang`, judul, deskripsi, CSP, tanpa
gaya/skrip *inline*, urutan heading, `alt`, id unik, semua tautan internal hidup, `aria-current` benar) untuk data fiktif
dan untuk **3.591 halaman dari data www asli**; juga palet, aturan menu, escaping, staging/produksi, bangun satu prodi,
ganti slug, prodi nonaktif, dan cek integritas (halaman diubah, teks judi, dan berkas `.php` tanam terdeteksi).
Pemeriksa halaman diuji dengan halaman yang sengaja rusak, supaya tidak "selalu lulus".

Diperiksa di browser (desktop dan lebar 375 px): beranda S1 Teknik Informatika (biru tua/kuning FT), halaman CPL dengan
menu samping, halaman wajib S1 Ilmu Politik (jingga FISIP), halaman akar, menu ponsel; tanpa gulir horizontal.

Melihat sendiri:
```bash
.venv/bin/python platform/bangun/bangun.py
python3 -m http.server 8790 --bind 127.0.0.1 --directory publik
```

## Keputusan kecil yang perlu dikonfirmasi
- `sitemap.xml` satu di akar (semua prodi satu domain), bukan per prodi seperti tertulis di rencana §7.
- Font Plus Jakarta Sans dimuat dari Google Fonts, sama seperti www (CSP mengizinkan `fonts.googleapis.com`).
- Halaman wajib yang belum diisi tetap tampil di staging dengan catatan "sedang dilengkapi"; keputusan untuk produksi
  (tampil atau disembunyikan) tetap di Fase 4 sesuai rencana.

## Langkah berikutnya
Langkah 4 — akun & peran: SQLite, login, aturan sandi kuat, ganti/reset sandi, akses per prodi, log audit.
