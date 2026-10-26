# Rencana Fase 1 — Fondasi Platform `prodi.unsrat.ac.id`

Status: **disetujui** (26 Oktober 2026), pertanyaan §12 sudah dijawab. Dikerjakan per langkah (§10).
Lampiran: [`platform/data-awal/slug.csv`](../platform/data-awal/slug.csv) — alamat singkat 97 prodi (disetujui).

---

## 0. Keputusan yang sudah diambil

| No | Keputusan | Sumber |
|---|---|---|
| K-P1 | Slug singkat, ditetapkan manual oleh superadmin (mis. `s1informatika`) | Pengguna, 26 Okt 2026 |
| K-P2 | Tidak ada peran admin fakultas. Peran: superadmin, admin prodi (koordinator), operator | Pengguna |
| K-P3 | Seluruh 97 prodi mendapat situs, termasuk 7 Profesi dan 12 Spesialis (Sp-1/Sp-2) | Pengguna |
| K-P4 | Situs prodi lama dialihkan (redirect) oleh admin jaringan/VM UNSRAT, di luar pekerjaan ini | Pengguna |
| K-P5 | Hosting di VM yang sama dengan www, sebagai stack Docker terpisah | Pengguna |
| K-P6 | Data resmi prodi bersumber dari www (satu arah www → prodi); prodi hanya bisa mengusulkan perubahan | Masukan awal, disetujui |
| K-P7 | Pola teknis sama dengan www: generator halaman statis + admin Flask, admin hanya dari jaringan/VPN UNSRAT | Masukan awal, disetujui |
| K-P8 | Slug dari `slug.csv`: kata "Teknik"/"Ilmu" dihilangkan, sebagian memakai singkatan | Pengguna, 26 Okt 2026 |
| K-P9 | Repo `prodi-unsrat` | Pengguna |
| K-P10 | Tanpa 2FA; akun admin wajib memakai sandi kuat | Pengguna |
| K-P11 | Logo dan unggahan disimpan di Google Cloud Storage (bucket yang sama dengan www, folder `prodi/`) | Pengguna |
| K-P12 | Tanpa SMTP: sandi diganti sendiri oleh pemilik akun atau direset superadmin | Pengguna |
| K-P13 | Port situs dan admin di VM diinformasikan kemudian | Pengguna |

## 1. Tujuan Fase 1

Membangun **fondasi** yang dipakai semua fase berikutnya. Setelah Fase 1 selesai:

1. Ke-97 situs prodi **terbangun otomatis** dari data www, dengan template induk yang seragam, dan tayang
   di staging (`noindex`).
2. Ada **akun per orang** dengan 3 peran, sandi kuat, dan pembatasan akses per prodi yang teruji.
3. Superadmin bisa: mendaftarkan prodi dan menetapkan slug, mengelola akun, menarik data terbaru dari www
   dengan pratinjau perubahan, dan melihat log audit.
4. Admin prodi bisa: mengganti identitas tampilan (tagline, warna dari palet, logo), mengatur menu
   (ganti label, urutkan, sembunyikan menu opsional), dan mengelola operator prodinya.
5. Stack Docker terpisah berjalan di VM yang sama, lengkap dengan pemantau *deface*.

## 2. Di luar lingkup Fase 1 (masuk fase berikutnya)

| Pekerjaan | Fase |
|---|---|
| Editor isi halaman (sejarah, VMTS, kurikulum, dokumen mutu, fasilitas, dll.), berita/pengumuman, unggah dokumen | 2 (pilot 3 prodi) |
| Alur persetujuan isi operator → admin prodi | 2 |
| Usulan perubahan data resmi (CPL dll.) dari prodi ke superadmin | 2 |
| Halaman "Dokumen Akreditasi" dan label kriteria per lembaga akreditasi | 2 |
| Landing page dengan pencarian dan filter | 3 (Fase 1 hanya daftar prodi sederhana) |
| Peluncuran ke 97 prodi, pelatihan operator, panduan | 4 |
| Versi bahasa Inggris `/<slug>/en/` (alamat sudah dicadangkan di Fase 1) | 5 |
| Redirect situs prodi lama | Admin UNSRAT (K-P4) |

## 3. Arsitektur

```
VM yang sama (Portainer)
├── Stack "website-unsrat" (sudah ada, tidak diubah)
│     web :454 · admin :455 · pemantau
│     volume unsrat-data ──────────────┐  (berisi data/prodi.json, unit.json, kalender.json)
│                                      │  dipasang HANYA-BACA
└── Stack "prodi-unsrat" (baru)         ▼
      prodi-web      Nginx: situs publik + admin (hanya IP UNSRAT/VPN); port menyusul (K-P13)
      prodi-admin    Flask + generator; membaca data www, menulis halaman ke volume prodi-publik
      prodi-pemantau cek integritas tiap 10 menit (pakai ulang site/pemantau dari www)
      volume prodi-data, prodi-rahasia, prodi-publik
```

- **Repo baru** (usulan: `supera1/prodi-unsrat`), tidak dicampur dengan repo www. Modul yang terbukti aman di www
  **disalin** (bukan di-*import* lintas repo) dan dicatat asal versinya: `gambar_aman.py`, `svg_aman.py`,
  `saringan_spam.py`, `cek_integritas.py`, `riwayat.py`, pola `_rakit-publik.py`, pola CSP/Nginx, `tokens.css`.
- **Data www dibaca lewat volume**, bukan lewat internet: volume data stack www dipasang hanya-baca ke
  `prodi-admin` sebagai *external volume*. Tidak ada port atau API baru di sisi www, dan www tidak perlu diubah.
  (Nama volume di Portainer biasanya berawalan nama stack, mis. `website-unsrat_unsrat-data`; dipastikan saat deploy.)
- **Domain**: `prodi.unsrat.ac.id` diarahkan ke load balancer yang sama, diteruskan ke port situs prodi.
  Admin dibuka lewat awalan jalur (pola `ADMIN_AWALAN` seperti `/zz` di www) dan dibatasi `ADMIN_IP_BOLEH`.
  Pengaturan DNS dan load balancer dikerjakan admin VM UNSRAT; repo menyediakan panduannya.
- **Tanpa paket baru** selain yang sudah dipakai www (Flask, Werkzeug, argon2-cffi, Pillow, pypdf, openpyxl,
  defusedxml, waitress, google-cloud-storage). Akun disimpan di SQLite (pustaka standar Python).

### Struktur repo usulan

```
prodi-unsrat/
├── CLAUDE.md, README.md
├── docs/  keputusan.md · keamanan.md · deploy-portainer.md · log/fase-01.md
├── docker-compose.yml · Dockerfile · docker/ (nginx, skrip mulai)
├── platform/
│   ├── admin/          Flask: akun, peran, superadmin, admin prodi
│   ├── bangun/         generator halaman statis + perakit folder publik
│   ├── template/       template induk: menu.json, halaman (Jinja2), aset (CSS/JS/gambar)
│   ├── data-awal/      registri awal (slug dari usulan-slug.csv yang disetujui), palet warna
│   └── pemantau/
└── uji/
```

## 4. Model data

Kunci tetap setiap prodi adalah **kode PDDIKTI** (unik untuk 97 prodi, sudah diperiksa), bukan slug. Dengan
begitu slug bisa diganti tanpa memindahkan folder data, dan slug lama otomatis dialihkan (301).

| Berkas | Isi | Siapa yang mengubah |
|---|---|---|
| `data/registri.json` | per prodi: `kode_pddikti`, `slug`, `slug_lama[]`, `aktif`, `dosen_url`, tanggal dibuat | Superadmin |
| `data/warisan/prodi.json` | salinan data resmi dari www (nama, jenjang, gelar, SKS, CPL, bidang kerja, akreditasi, lembaga, berlaku hingga, internasional, surel, fakultas) + waktu tarik | Hanya proses "Tarik data www" |
| `data/warisan/unit.json`, `kalender.json` | nama & warna bendera fakultas, kalender akademik | Hanya proses tarik |
| `data/prodi/<kode>/situs.json` | identitas: tagline, palet warna, logo, kontak tambahan, media sosial, pengaturan menu | Admin prodi, superadmin |
| `data/prodi/<kode>/halaman/*.json` | isi halaman lokal (kerangka saja di Fase 1; editor di Fase 2) | Fase 2 |
| `platform/template/menu.json` | template induk: pohon menu, setiap butir bertanda `otomatis` / `wajib` / `opsional` | Superadmin (lewat rilis kode) |
| `rahasia/akun.sqlite` | akun, peran, keanggotaan prodi, hash sandi (argon2) | Superadmin, admin prodi (operator) |
| `admin/riwayat/`, `admin/log/audit.jsonl` | versi setiap berkas data dan log setiap aksi (siapa, prodi mana, apa) | Otomatis |

**Data `null` / kosong tidak dikarang.** Contoh: 4 prodi tanpa CPL dan 7 prodi tanpa lembaga akreditasi tampil
dengan keterangan "sedang dilengkapi" dan masuk daftar kekurangan di dasbor superadmin.

## 5. Sinkronisasi data dari www

Skrip `tarik_www.py`, dijalankan dari tombol superadmin (dan opsional terjadwal harian):

1. Baca `prodi.json`, `unit.json`, `kalender.json` dari volume www (hanya-baca); validasi skema.
2. Bandingkan dengan `data/warisan/` → **pratinjau perubahan** per prodi (field mana berubah, CPL ditambah/dihapus).
3. Superadmin menerapkan → versi lama disimpan ke riwayat → situs prodi yang terdampak dibangun ulang.
4. Prodi baru di www muncul sebagai **"belum terdaftar"** sampai superadmin menetapkan slugnya.
   Prodi yang hilang dari www **tidak dihapus**, hanya ditandai untuk ditinjau.

Konsekuensinya: "menambah program studi baru" dilakukan dengan menambahkannya dulu di superadmin www (sumber
data resmi), lalu mendaftarkannya di platform prodi. Ini menjaga satu sumber kebenaran.

## 6. Akun, peran, dan keamanan

| | Superadmin | Admin prodi | Operator |
|---|---|---|---|
| Daftarkan / nonaktifkan prodi, tetapkan slug | ✅ | — | — |
| Tarik data www, lihat log audit semua prodi | ✅ | — | — |
| Buat akun superadmin & admin prodi | ✅ | — | — |
| Buat / nonaktifkan operator prodinya | ✅ | ✅ | — |
| Identitas & menu prodi | ✅ | ✅ | — |
| Isi halaman (Fase 2) | ✅ | ✅ | ✅ (perlu persetujuan) |

- Satu akun boleh memegang lebih dari satu prodi (mis. koordinator S2 dan S3 bidang yang sama).
- **Pembatasan per prodi diperiksa di server** pada setiap rute yang memuat kode prodi, lewat satu dekorator.
  Ada uji khusus: akun prodi A yang mencoba membuka/mengubah prodi B harus mendapat 403 (uji IDOR).
- **Sandi kuat wajib** (K-P10, pengganti 2FA): argon2 (seperti www), minimal 12 karakter, memuat huruf dan angka,
  ditolak bila ada di daftar sandi umum atau memuat nama pengguna / nama prodi. Sandi sementara dari superadmin wajib
  diganti saat pertama masuk.
- Dipakai ulang dari www: penguncian login (per alamat & per akun), batas sesi 2 jam diam / 12 jam total, sesi
  terikat sidik sandi, CSRF, CSP tanpa skrip *inline*, pembatasan IP admin, saringan spam judi pada semua teks.
- Tanpa surel (K-P12): pemilik akun mengganti sandinya sendiri di menu Akun; superadmin bisa mereset sandi siapa pun,
  admin prodi bisa mereset sandi operator prodinya. Setiap reset tercatat di log audit.
- Akun superadmin pertama dibuat dari baris perintah di kontainer (`siapkan.py --superadmin`), seperti www.

## 7. Template induk dan generator

**Alamat:** `prodi.unsrat.ac.id/<slug>/…`; root `/` berisi daftar prodi per jenjang dan fakultas (versi sederhana
landing page). Alamat yang dicadangkan dan tidak boleh dipakai sebagai slug: `assets`, `cari`, `en`, `data`,
`admin`, `api`, `zz`, `404`.

**Halaman yang dibangun di Fase 1** (menu sesuai masukan awal):

| Menu | Halaman | Jenis | Isi di Fase 1 |
|---|---|---|---|
| Beranda | beranda | otomatis | nama, jenjang, gelar, akreditasi + masa berlaku, fakultas, ringkasan bidang kerja |
| Profil | sejarah · VMTS · struktur organisasi & tata pamong · penjaminan mutu · kerja sama | wajib | kerangka "sedang dilengkapi" |
| Profil | akreditasi | otomatis + wajib | status, lembaga, berlaku hingga, akreditasi internasional; sertifikat di Fase 2 |
| Akademik | profil lulusan & CPL | otomatis | bidang kerja + daftar CPL dan tahun kurikulum |
| Akademik | spesifikasi program studi | otomatis | jenjang, gelar, SKS, kode PDDIKTI, fakultas |
| Akademik | kalender akademik | otomatis | dari kalender www |
| Akademik | kurikulum · peraturan & panduan | wajib | kerangka |
| Dosen & Tendik | dosen tetap | otomatis | tautan ke `dosen_url` prodi (dari daftar yang akan diberikan); sementara ke dosen.unsrat.ac.id |
| Dosen & Tendik | tenaga kependidikan · prestasi & pengembangan SDM | wajib | kerangka |
| Riset & PkM | penelitian · publikasi · PkM · luaran & HKI | wajib | kerangka |
| Mahasiswa & Alumni | penerimaan · layanan · organisasi & prestasi · lulusan & tracer study · survei kepuasan | wajib | kerangka; penerimaan menaut ke PMB |
| Fasilitas | laboratorium · ruang · perpustakaan · sistem informasi | wajib | kerangka |
| Kontak | kontak | otomatis | surel prodi, fakultas, alamat kampus |

Catatan:
- Halaman "kerangka" di staging menampilkan pesan "sedang dilengkapi". Sebelum produksi (Fase 4) diputuskan apakah
  halaman wajib yang masih kosong disembunyikan dari menu atau tetap tampil.
- **Tampilan**: memakai token desain www (`tokens.css`, Plus Jakarta Sans) supaya terasa satu keluarga dengan
  www.unsrat.ac.id. Header: lambang UNSRAT + nama prodi + fakultas; footer: tautan UNSRAT.
- **Warna**: admin prodi memilih dari **palet ±8 pasangan warna** yang kontrasnya sudah lolos WCAG AA (diuji saat build
  dengan kode yang sama seperti `pratinjau_warna.py`). Bawaan: warna bendera fakultas dari `unit.json` bila lolos uji
  kontras, kalau tidak warna UNSRAT (#3500FF / #F2B705).
- **Menu**: admin prodi boleh mengganti label, mengurutkan dalam satu kelompok, dan menyembunyikan butir `opsional`.
  Butir `wajib` dan `otomatis` tidak bisa dihapus. Penambahan halaman sendiri masuk Fase 2 bersama editor.
- Standar www tetap berlaku: tanpa JavaScript tetap berfungsi, satu `h1`, responsif dari 320 px, JSON-LD
  `CollegeOrUniversity`/`EducationalOccupationalProgram`, `canonical`, `sitemap.xml` per situs.
- **Bangun bertahap**: menyimpan identitas satu prodi hanya membangun ulang situs prodi itu (±40 halaman), bukan 97 situs.

## 8. Admin di Fase 1

**Superadmin**
- Dasbor: jumlah prodi aktif, prodi tanpa admin, kelengkapan data warisan, waktu tarik data terakhir.
- Prodi: daftar 97 prodi, tetapkan/ubah slug (dengan peringatan redirect), aktif/nonaktif, isi `dosen_url`,
  impor massal `dosen_url` dari Excel/CSV (untuk daftar URL dosen yang akan diberikan).
- Akun: buat, nonaktifkan, reset sandi, atur keanggotaan prodi.
- Tarik data www (pratinjau → terapkan). Riwayat & pemulihan versi. Log audit dengan saringan per prodi/akun.

**Admin prodi**
- Dasbor prodinya: tautan pratinjau situs, daftar halaman wajib yang belum terisi (untuk persiapan akreditasi).
- Identitas: tagline, palet warna (dengan pratinjau), logo prodi opsional (PNG/JPEG/SVG yang disanitasi, disimpan di GCS
  folder `prodi/<kode>/`), media sosial.
- Menu: label, urutan, sembunyikan opsional.
- Operator: buat, nonaktifkan, reset sandi.

**Operator** (Fase 1): bisa masuk dan melihat dasbor; fitur edit isi datang di Fase 2.

## 9. Uji (folder `uji/`, pola sama dengan www)

- Generator: 97 situs terbangun; setiap halaman lolos cek struktur (satu `h1`, tautan internal hidup, CSP,
  judul & deskripsi), tidak ada slug ganda atau bertabrakan dengan alamat cadangan.
- Tarik data: pratinjau benar untuk perubahan CPL/akreditasi; prodi baru/hilang ditangani sesuai §5.
- Akun & akses: login, penguncian, aturan sandi kuat, ganti & reset sandi, **matriks peran × rute** (setiap rute
  dicoba oleh setiap peran dan prodi lain), CSRF.
- Keamanan unggahan logo dan saringan spam judi.
- Uji di dalam image Docker sebelum deploy, seperti www.

## 10. Urutan kerja (satu branch per langkah, setiap langkah ditinjau sebelum lanjut)

1. **Kerangka repo**: struktur folder, `CLAUDE.md`, `docs/keputusan.md` (salin K-P1…K-P7), salinan modul aman dari www.
2. **Model data + tarik data www** + registri awal dari `usulan-slug.csv` yang sudah disetujui.
3. **Template induk + generator**: menu.json, halaman Jinja2, token desain, palet warna, root daftar prodi,
   perakit folder publik, sitemap/robots per mode.
4. **Akun & peran**: SQLite, login, aturan sandi kuat, ganti/reset sandi, dekorator akses per prodi, audit log.
5. **Superadmin**: prodi, slug, akun, tarik data, riwayat, impor `dosen_url`.
6. **Admin prodi**: identitas, palet, logo, menu, operator.
7. **Docker & deploy staging**: compose stack terpisah, Nginx, pemantau, panduan Portainer + catatan DNS/LB untuk admin VM.
8. **Uji menyeluruh + `docs/log/fase-01.md`** (cara verifikasi manual, sisa pekerjaan, keputusan yang perlu dikonfirmasi).

## 11. Kriteria selesai Fase 1

- [ ] 97 situs prodi tayang di staging (noindex) di bawah slug yang disetujui.
- [ ] Data resmi di situs prodi sama persis dengan www (diuji otomatis).
- [ ] Akun per orang dengan 3 peran dan sandi kuat; uji matriks akses lulus tanpa kebocoran antar-prodi.
- [ ] Admin prodi bisa mengganti tagline, warna, logo, dan menu; perubahannya tampil setelah bangun ulang otomatis.
- [ ] Stack `prodi-unsrat` berjalan di VM tanpa mengubah stack www.
- [ ] Seluruh uji lulus di dalam image; log fase ditulis.

## 12. Jawaban atas pertanyaan sebelum mulai (26 Oktober 2026)

| No | Pertanyaan | Jawaban |
|---|---|---|
| 1 | Slug | Disetujui seperti `slug.csv` (K-P8) |
| 2 | Nama repo | `prodi-unsrat` (K-P9) |
| 3 | Kode QR 2FA | Tidak perlu 2FA; sandi kuat (K-P10) |
| 4 | Penyimpanan logo | Google Cloud Storage (K-P11) |
| 5 | SMTP | Tidak perlu; reset oleh pemilik akun / superadmin (K-P12) |
| 6 | Port & domain | Diinformasikan kemudian (K-P13) |
