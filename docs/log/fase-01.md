# Log Fase 1 — Platform situs program studi UNSRAT (26 Oktober 2026)

Rencana: [rencana-fase-01.md](../rencana-fase-01.md) · Keputusan: [keputusan.md](../keputusan.md) · Deploy:
[deploy.md](../deploy.md) · Log per langkah: `docs/log/fase-01-langkah-*.md`.

## Ringkasan

Fase 1 menghasilkan platform satu sumber untuk situs ke-97 program studi UNSRAT di `prodi.unsrat.ac.id/<slug>/`:
- **97 situs prodi** dengan menu seragam mengikuti kriteria akreditasi: 8 halaman otomatis dari data resmi (termasuk
  pengumuman dan berita), 22 halaman wajib akreditasi yang diisi di Fase 2, 2 opsional, dan halaman tiap kelompok menu
  (38 halaman per prodi; 3.688 halaman bersama halaman akar dan 404). Bagian depan beranda bisa disesuaikan prodi.
  Seluruhnya halaman statis tanpa JavaScript.
- **Data resmi dari www.unsrat.ac.id** (nama, gelar, SKS, CPL, akreditasi, fakultas, kalender), diunggah superadmin
  dari ekspor Excel atau berkas JSON www; prodi boleh mengubah data resminya sendiri, dan bentrok dengan www ditandai.
- **Admin** hanya dari jaringan/VPN UNSRAT, akun per orang dengan tiga peran (superadmin, admin prodi, operator),
  sandi kuat, riwayat versi setiap berkas data, dan log audit.
- **Stack Docker untuk VM sendiri**, di-deploy admin UNSRAT dari GitHub, dengan pemantau integritas, bangun ulang
  harian, cadangan harian, dan panduan deploy.

## Langkah

Setiap langkah satu branch, bertumpuk (setiap branch bercabang dari langkah sebelumnya), semuanya sudah di-push ke
`supera1/prodi-unsrat`. `fase/01-8-uji` memuat seluruh Fase 1; `main` belum digabung.

| Langkah | Branch | Hasil utama |
|---|---|---|
| 1 | `fase/01-1-kerangka` | Kerangka repo, dokumen, modul aman dari www (sidik asal diuji), daftar slug 97 prodi |
| 2 | `fase/01-2-data` | Tarik data resmi www (pemeriksaan, saringan judi, prodi hilang/baru), registri prodi, riwayat versi |
| 3 | `fase/01-3-template` | Menu induk akreditasi, template Jinja2, palet warna bendera fakultas dengan uji kontras, generator 97 situs |
| 3b | `fase/01-3b-pengumuman` | Pengumuman dan berita per prodi: foto/PDF aman, kategori, arsip, RSS |
| 3c | `fase/01-3c-beranda` | Bagian depan beranda per prodi: latar warna/foto, teks, kartu fakta; nilai resmi dikunci |
| 4 | `fase/01-4-akun` | Akun per orang (SQLite, argon2), tiga peran, penguncian login, CSRF, matriks akses |
| 5 | `fase/01-5-superadmin` | Prodi dan slug (pengalihan slug lama), tarik data, tautan dosen massal, riwayat dan pemulihan |
| 5b | `fase/01-5b-data-prodi` | Data resmi bisa diubah prodi per kolom (termasuk CPL); bentrok dengan www ditandai |
| 6 | `fase/01-6-admin-prodi` | Halaman admin prodi: identitas, logo, beranda, menu, pengumuman dengan alur operator → admin |
| 6b | `fase/01-6b-vm-sendiri` | Keputusan VM sendiri dan unggah data www (K-P17–K-P19); perbaikan akreditasi "belum" |
| 7 | `fase/01-7-docker` | Unggah data www, data awal VM baru, stack Docker, HTTPS dua cara, cadangan, panduan deploy |
| 8 | `fase/01-8-uji` | Uji penerimaan Fase 1, pemeriksaan 320 px, log fase ini |

## Kriteria selesai Fase 1 (rencana §11)

| Kriteria | Status | Bukti |
|---|---|---|
| 97 situs prodi tayang di staging (noindex) di bawah slug yang disetujui | **Siap**; tayang di server setelah deploy admin VM | `uji_fase1` K1: VM kosong → data awal → 97 situs di slug `slug.csv`, 3.688 halaman staging lolos pemeriksaan halaman; stack Docker dicoba utuh (langkah 7) |
| Data resmi di situs prodi sama persis dengan www (diuji otomatis) | **Selesai** | `uji_fase1` K2: setiap nilai resmi ke-97 prodi dan 1.259 CPL dibandingkan dengan `prodi.json`/`unit.json` www sendiri — 0 selisih; satu-satunya beda yang dibolehkan adalah perubahan prodi sendiri (K-P16), yang tampil dan hilang dengan "pakai data www" |
| Akun per orang, 3 peran, sandi kuat; matriks akses tanpa kebocoran antar-prodi | **Selesai** | `uji_admin`: 65 rute × 6 akun; `uji_fase1` K3: 34 rute berkode prodi × 2 akun × 9 prodi lain pada registri asli = 612 permintaan, 0 bocor |
| Admin prodi mengganti tagline, warna, logo, menu; tampil setelah bangun ulang otomatis | **Selesai** | `uji_fase1` K4 dan `uji_admin_prodi`: keempatnya tampil, situs prodi lain tidak berubah satu bait pun |
| Stack `prodi-unsrat` berjalan di VM tanpa mengubah stack www | **Siap**; menunggu deploy admin VM | Stack terpisah (nama, volume, port sendiri; `uji_fase1` K5, `uji_docker`); dicoba utuh di Docker lokal (langkah 7) |
| Seluruh uji lulus di dalam image; log fase ditulis | **Selesai** | `Dockerfile` menjalankan semua rangkaian saat build (K-P20); log ini |

## Uji otomatis

```bash
.venv/bin/python uji/jalankan-semua.py          # di komputer pengembang
sudo docker exec prodi-unsrat-admin-1 python uji/jalankan-semua.py   # di VM (juga otomatis saat build image)
```

13 rangkaian, semuanya lulus di komputer pengembang dan di dalam image:

| Rangkaian | Yang diuji |
|---|---|
| `uji_fase1` | Kriteria selesai Fase 1 pada data asli (di atas) dan standar halaman |
| `uji_data`, `uji_slug` | Tarik data www (sumber rusak, judi, prodi hilang), registri, daftar slug vs data www |
| `uji_bangun`, `uji_beranda`, `uji_pengumuman` | Generator, palet dan kontras, bagian depan, pengumuman/berita, staging/produksi, integritas |
| `uji_admin` | Akun, sandi, sesi, CSRF, penguncian, jaringan, matriks akses semua rute × semua peran |
| `uji_superadmin`, `uji_data_prodi`, `uji_admin_prodi` | Halaman superadmin dan admin prodi, perubahan data prodi, bangun ulang, riwayat |
| `uji_impor_www` | Unggah Excel/JSON www, termasuk ekspor Excel asli dari kode www (97 prodi tanpa selisih) |
| `uji_docker` | Berkas stack: CSP, saringan pengalihan slug, volume, variabel |
| `uji_asal_modul` | Modul yang disalin/diadaptasi dari www masih sesuai sidik asalnya |

Uji mutasi di sepanjang fase membuktikan uji penting tidak "selalu lulus" (mis. operator menerbitkan, akreditasi
"belum", pemilik unggahan, unggahan usang); `uji_fase1` sendiri mengubah satu CPL dan satu nilai di halaman lalu
memastikan perbandingan menemukannya.

## Pemeriksaan di browser (langkah 8)
- **Lebar 320 px**: 232 halaman (beranda dan halaman CPL ke-97 prodi, halaman akar, 404, dan semua jenis halaman di
  empat prodi) dimuat pada lebar 320 px. Satu halaman meluap 9 px: alamat surel panjang di beranda S2 Ilmu
  Pemerintahan. **Diperbaiki** (`overflow-wrap` pada `body`, juga melindungi tautan panjang di pengumuman kelak);
  sesudahnya 232 halaman tanpa gulir horizontal.
- Desktop 1280 px dan ponsel: tata letak, pita staging, kartu fakta; fokus keyboard terlihat, tautan pertama "Langsung
  ke konten utama", satu `h1`, `lang="id"`.
- Ukuran: halaman terbesar 4,7 KB gzip (profil lulusan S2 Biologi), CSS 6,5 KB gzip, tanpa JavaScript.

## Cara verifikasi manual

**Di komputer sendiri, tanpa Docker** (repo www di folder sebelahnya, atau data awal di repo):
```bash
python3 platform/impor_www.py --isi-awal         # atau: python3 platform/tarik_www.py --terapkan && python3 platform/registri.py --siapkan
.venv/bin/python platform/bangun/bangun.py
python3 -m http.server 8790 --bind 127.0.0.1 --directory publik
```
Buka http://127.0.0.1:8790/ lalu periksa:
1. Halaman akar memuat 97 prodi per jenjang; setiap kartu menuju `/<slug>/`.
2. Tiga prodi berbeda jenis (mis. `s1informatika`, `profesidokter`, satu Sp-1): beranda, Akreditasi, Profil lulusan &
   CPL, Spesifikasi, Kontak. Bandingkan nilainya dengan halaman prodi yang sama di www.unsrat.ac.id.
3. Prodi dengan data resmi kosong (mis. tanpa CPL) menulis "sedang dilengkapi", bukan nilai karangan.
4. Setiap halaman berpita "Pratinjau staging"; di ponsel tidak ada gulir ke samping.

**Dengan stack Docker** (komputer sendiri: `docs/deploy.md` §13; staging: §5 setelah deploy):
1. Masuk sebagai superadmin → dasbor: 97 situs aktif, sumber data www.
2. Data www → unggah ekspor Excel terbaru dari superadmin www → pratinjau → Terapkan.
3. Akun → buat admin prodi untuk satu prodi; masuk sebagai admin itu → ubah palet, kalimat pengantar, logo, label menu
   → periksa situs prodi itu (±beberapa detik) dan pastikan prodi lain tidak berubah.
4. Admin prodi membuat operator; operator menulis pengumuman berfoto → ajukan; admin terbitkan → tampil di beranda prodi.
5. Superadmin → Prodi → ganti slug satu prodi → alamat lama dialihkan (±30 detik).
6. Coba buka admin dari luar jaringan UNSRAT → 403.
7. Log kontainer pemantau: `0 temuan`; jalankan skrip cadangan sekali (`docs/deploy.md` §9).

## Sisa pekerjaan

**Menunggu masukan atau keputusan:**
- Daftar tautan dosen per prodi (dosen.unsrat.ac.id). Formatnya diasumsikan satu tautan per prodi (impor massal di
  superadmin); bila berupa daftar per dosen, perlu model data tambahan.
- Port akhir di VM (K-P13), nama domain/alamat admin, dan load balancer: bersama admin VM.
- Konfirmasi K-P20 (uji saat build) dan keputusan kecil lain di bawah.
- Penggabungan ke `main` (deploy disarankan dari `main`).

**Dikerjakan admin VM / pihak lain:**
- Deploy staging mengikuti `docs/deploy.md`; buat minimal dua superadmin; unggah data www terbaru.
- Admin VM www mengambilkan `unit.json`, `kalender.json`, `situs.json` www bila berubah (`docs/deploy.md` §6).
- www: perbaikan validasi jaringan di `docker/nginx/40-unsrat-jaringan.sh` sudah disiapkan di branch www
  `fase/praproduksi-cek-jaringan` (belum di-commit, menunggu persetujuan); penulisan lembaga akreditasi di www belum
  seragam (`LAM-Tek`/`LAM-Teknik`); data resmi 10 prodi masih kosong sebagian (CPL atau akreditasi), dilengkapi di www.
- Pengalihan situs prodi lama (K-P4).

**Belum dicoba:** alur Portainer itu sendiri (yang dicoba `docker compose`), Let's Encrypt sungguhan (perlu DNS dan VM
publik), pemindaian kerentanan image (trivy).

**Fase berikutnya** (rencana §2): editor isi 22 halaman wajib dan unggah dokumen, alur persetujuan isi, usulan
perubahan data resmi ke superadmin, halaman Dokumen Akreditasi (Fase 2, pilot 3 prodi); halaman akar dengan pencarian
(Fase 3); peluncuran ke 97 prodi, pelatihan, keputusan tampil/sembunyi halaman wajib yang belum diisi di produksi
(Fase 4); bahasa Inggris `/<slug>/en/` (Fase 5).

## Keputusan yang perlu dikonfirmasi

| Keputusan | Dari | Usulan sekarang |
|---|---|---|
| Uji dijalankan setiap build image; build gagal bila uji gagal (K-P20) | Langkah 7 | Ya; `UJI_SAAT_BUILD=0` hanya darurat |
| Port di VM (K-P13) | Langkah 7 | 8080 situs, 8081 admin (atau 80/443 + admin HTTPS di VM) |
| `sitemap.xml` satu di akar, bukan per prodi | Langkah 3 | Satu di akar (satu domain) |
| Font Plus Jakarta Sans dari Google Fonts, seperti www | Langkah 3 | Seperti www |
| Halaman wajib yang belum diisi di produksi: tampil "sedang dilengkapi" atau disembunyikan | Langkah 3 | Diputuskan di Fase 4 |
| Format daftar tautan dosen: satu tautan per prodi | Langkah 5 | Menunggu daftarnya |

## Catatan teknis yang perlu diketahui
- Penguncian login disimpan di memori proses admin: restart admin mengosongkannya (seperti www).
- Pemulihan versi mengembalikan seluruh berkas (mis. registri), bukan satu perubahan.
- CPL dibandingkan sebagai satu daftar: bila www mengubah satu butir setelah prodi mengubah CPL-nya, seluruh daftar
  ditandai bentrok.
- Data www mengikuti www sejauh superadmin rutin mengunggah; dasbor mengingatkan setelah 30 hari.
- Situs dibangun ulang saat admin mulai, setelah setiap perubahan, dan setiap hari 02.30 WITA.
