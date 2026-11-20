# Persiapan pilot Fase 5 — versi bahasa Inggris enam prodi

**Status (20 November 2026):** aplikasinya siap. Langkah 1–4 Fase 5 sudah ada di `main`, dan langkah 5 menunggu PR-nya
digabung. Keenam prodi pilot sudah disebutkan pengguna. Pilot berjalan di produksi (`https://prodi.unsrat.ac.id`, admin
`https://bo-prodi.unsrat.ac.id`). Sebelum mulai, admin VM perlu memperbarui stack dan memasang kunci DeepL (lihat
[Sebelum pilot](#sebelum-pilot)). Rencana: [rencana Fase 5](rencana-fase-05.md) §6; keputusan K-P37.

Panduan untuk peserta: [docs/panduan-admin-prodi.md](panduan-admin-prodi.md), bagian "Versi bahasa Inggris" dan
"Pengumuman dan berita". Panduan ini juga terbuka di admin lewat menu **Panduan**. Dokumen ini untuk superadmin UPA TIK
dan pengguna yang memimpin pilot.

## Prodi pilot

Keenam prodi disebutkan pengguna pada 20 November 2026. Mereka berasal dari tiga fakultas dan Program Pascasarjana,
dengan empat lembaga akreditasi.

| No | Prodi | Jenjang · fakultas · lembaga (data www) | Versi Inggris | Data resmi Inggris (data awal) | Admin prodi | Operator |
|---|---|---|---|---|---|---|
| 1 | S1 Teknik Informatika (55201) | S1 · Fakultas Teknik · LAM-Infokom; internasional AUN-QA | `/s1informatika/en/` | lengkap; 11/11 CPL | (diisi) | (diisi) |
| 2 | S2 Informatika (55100) | S2 · Program Pascasarjana · LAM-Infokom | `/s2informatika/en/` | lengkap; 42/42 CPL | (diisi) | (diisi) |
| 3 | S1 Biologi (46201) | S1 · FMIPA · LAMSAMA | `/s1biologi/en/` | lengkap; 10/10 CPL | (diisi) | (diisi) |
| 4 | S1 Agribisnis (54201) | S1 · Fakultas Pertanian · BAN-PT | `/s1agribisnis/en/` | lengkap; 12/12 CPL | (diisi) | (diisi) |
| 5 | S1 Kehutanan (54251) | S1 · Fakultas Pertanian · LAM-PTIP | `/s1kehutanan/en/` | lengkap; 7/7 CPL | (diisi) | (diisi) |
| 6 | S1 Agroteknologi (54211) | S1 · Fakultas Pertanian · BAN-PT | `/s1agroteknologi/en/` | lengkap; 7/7 CPL | (diisi) | (diisi) |

- "S1 Ilmu Kehutanan" yang disebut pengguna tercatat di www sebagai **S1 Kehutanan** (54251). Itu satu-satunya prodi
  kehutanan di daftar slug.
- **Data resmi Inggris** berarti nama Inggris prodi dan fakultasnya, bidang kerja lulusan berbahasa Inggris, dan CPL
  berbahasa Inggris. Angka di tabel berasal dari salinan data www di `platform/data-awal/www/` (diambil 26 Oktober
  2026). Data di produksi bisa lebih baru; keadaannya terlihat di Ringkasan prodi, kotak **Versi bahasa Inggris**.
- S2 Informatika (42 CPL) dan S1 Agribisnis (nama kurikulum CPL lebih dari 20 karakter) sebelumnya **tidak bisa
  menyimpan** formulir Data prodi sama sekali, karena data www mereka melampaui batas formulir. Hal ini juga menimpa
  19 prodi lain. Langkah 5 memperbaikinya, jadi versi yang di-deploy harus memuat langkah 5.

## Sebelum pilot

Dikerjakan superadmin UPA TIK, bersama admin VM untuk butir 0 dan 1.

0. **Versi yang di-deploy memuat Fase 5 sampai langkah 5.** Setelah PR langkah 5 digabung, admin VM memperbarui stack
   ([docs/deploy.md](deploy.md) §8: `git pull`, lalu `docker compose up -d --build`). Uji berjalan saat build; bila
   gagal, versi lama tetap berjalan.
1. **Kunci DeepL di `.env` VM** ([docs/deploy.md](deploy.md) §4A): `TERJEMAH_PENYEDIA=deepl` dan `TERJEMAH_KUNCI`.
   Kunci diserahkan langsung kepada admin VM, bukan lewat chat atau surel. Sesudah `docker compose up -d`, dasbor
   superadmin menampilkan baris **Terjemahan mesin (DeepL) bulan ini**.
   - Batas bawaan: 50.000 karakter per prodi per hari (`TERJEMAH_BATAS_HARIAN`) dan 500.000 karakter per bulan untuk
     semua prodi (`TERJEMAH_BATAS_BULANAN`, sama dengan kuota DeepL API Free).
   - Enam prodi yang memakai batas hariannya penuh menghabiskan 300.000 karakter sehari, jadi kuota bulanan Free bisa
     habis dalam dua hari. Penyunting menampilkan perkiraan jumlah karakter sebelum tombol ditekan. Bila pemakaian
     cepat naik, turunkan batas harian atau pakai paket DeepL yang lebih besar.
2. **Coba kunci sekali.** Superadmin membuka satu halaman pendek yang sudah terbit di salah satu prodi pilot, lalu
   **Isi halaman** → tab **English** → **Terjemahkan dari versi Indonesia**.
   - Hasilnya masuk draf dan bertanda terjemahan mesin. Buang drafnya bila tidak dipakai.
   - Pesan "kunci API DeepL ditolak" berarti baris `TERJEMAH_KUNCI` di `.env` perlu diperiksa, misalnya ada spasi atau
     tanda kutip yang ikut tersalin.
3. **Data resmi berbahasa Inggris.** Buka Ringkasan setiap prodi pilot (menu **Prodi** → prodi → **dasbor prodi**).
   - Kotak **Versi bahasa Inggris** harus menunjukkan *Data resmi berbahasa Inggris lengkap*.
   - Bila ada yang kosong, lengkapi di www lalu unggah data www terbaru (menu **Data www**), atau isi di menu
     **Data prodi** prodi itu.
   - Nama Inggris fakultas hanya bisa diisi di www.
4. **Akun.** Buat akun admin prodi (koordinator) dan satu atau dua operator untuk prodi pilot yang belum punya, lewat
   menu **Akun**. Kata sandi sementara hanya tampil sekali; sampaikan langsung atau lewat telepon kepada pemiliknya.
   S1 Teknik Informatika mungkin sudah punya akun dari pilot Fase 2.
5. **Uji masuk.** Pastikan setiap peserta bisa membuka admin dari tempat kerjanya. Admin hanya terbuka dari jaringan
   kampus atau VPN UNSRAT.
6. **Aktifkan versi Inggris** setiap prodi pilot setelah sesi pengenalan: menu **Prodi** → prodi → **Aktifkan versi
   Inggris**. Situs prodi itu langsung dibangun ulang.
   - Rencana §6 meminta versi Inggris diaktifkan "setelah isinya cukup". Bagian dari data resmi sudah cukup: keenam
     prodi punya data resmi Inggris lengkap. Begitu diaktifkan, beranda, Profil Lulusan dan CPL, Spesifikasi,
     Akreditasi, Dosen Tetap, Kalender, dan Kontak langsung tayang dalam bahasa Inggris.
   - Halaman yang diisi prodi baru muncul setelah versi Inggrisnya terbit, jadi tidak ada halaman setengah jadi.
   - Peserta melihat hasil terjemahannya di situs sungguhan, termasuk tombol bahasa.
   - Bila sebuah prodi ingin menunggu, saklarnya bisa dinyalakan kapan saja, dan terjemahan tetap bisa disiapkan dan
     diterbitkan sebelumnya.

## Sesi pengenalan (±60 menit)

Lebih baik dilakukan langsung di depan komputer peserta. Peserta sudah mengenal admin dari pemakaian sebelumnya; prodi
yang belum pernah memakainya mengikuti dulu sesi pengenalan Fase 2 ([docs/pilot-fase-02.md](pilot-fase-02.md)).

| Waktu | Materi |
|---|---|
| 10 menit | Versi Inggris di `/<slug>/en/` dan tombol bahasa. Halaman yang otomatis dari data resmi, dan yang diisi prodi. Kotak **Versi bahasa Inggris** di Ringkasan prodi |
| 20 menit | Praktik halaman **Sejarah**: tab **English**, **Terjemahkan dari versi Indonesia**, periksa setiap isian bertanda terjemahan mesin, centang **Saya sudah memeriksa terjemahan mesin di halaman ini**, **Simpan dan pratinjau**, lalu ajukan atau terbitkan; lihat hasilnya di situs |
| 10 menit | Admin prodi: bagian *Versi bahasa Inggris* di **Bagian depan beranda**, label menu Inggris, nama Inggris halaman tambahan, nama kriteria Inggris |
| 10 menit | Pengumuman: bagian **Versi bahasa Inggris (opsional)**, **Simpan dan terjemahkan dari versi Indonesia**, pemeriksaan, menu **News** |
| 10 menit | Yang tidak diterjemahkan (nama orang dan mitra, kode, judul karya, tabel Excel), tanda **perlu diperbarui**, batas harian, teks dikirim ke DeepL (jangan memuat data pribadi), masukan, target pilot |

## Masa pengisian

Usul tiga minggu; pengguna yang menentukan.

- **Target per prodi:** paling sedikit 15 dari 22 halaman wajib terbit dalam bahasa Inggris, tanpa bantuan pengembang
  (rencana §6). Beranda Inggris tayang begitu versi Inggris diaktifkan.
- **Setiap minggu (superadmin):**
  - unduh CSV di menu **Kelengkapan** dan simpan sebagai catatan kemajuan. Kolom `inggris_aktif`, `wajib_terbit_en`,
    dan `perlu_diperbarui_en` memuat versi Inggris;
  - lihat pemakaian terjemahan mesin di dasbor superadmin;
  - baca **Masukan pengguna** dan tanggapi setiap masukan;
  - periksa acak halaman Inggris yang baru terbit: nama prodi, fakultas, dan universitas, gelar, serta lembaga
    akreditasi harus sama dengan data resmi, tidak ada data pribadi, dan tidak ada teks Indonesia selain nama dan judul
    yang memang tidak diterjemahkan.
- **Perbaikan dari masukan** dikerjakan pengembang per langkah kecil (`fase/05-5a-…`, `fase/05-5b-…`). Setiap langkah
  ditinjau sebelum dipasang di VM.

## Ukuran keberhasilan dan cara melihatnya

| Ukuran (rencana §6) | Cara melihat |
|---|---|
| Setiap prodi pilot menerbitkan versi Inggris beranda dan ≥15 dari 22 halaman wajib | Menu **Kelengkapan**, kolom "Versi Inggris"; CSV mingguan (`wajib_terbit_en`); kotak **Versi bahasa Inggris** di Ringkasan prodi |
| Tanpa bantuan pengembang | Masukan berjenis Kendala yang memerlukan pengembang, dan catatan sesi |
| Terjemahan mesin dipakai dan diperiksa | Log audit (`isi-en-terjemahan-mesin`, `pengumuman-en-terjemahan-mesin`) dan pemakaian di dasbor superadmin. Halaman dengan terjemahan mesin yang belum diperiksa tidak bisa diajukan atau diterbitkan, dan pengumuman seperti itu tidak tampil di versi Inggris |
| Tidak ada istilah resmi yang salah tayang | Pemeriksaan acak mingguan. Istilah resmi dikunci dari data resmi saat diterjemahkan mesin |

## Sesudah pilot

- Pengembang menulis ringkasan hasil di `docs/log/fase-05-pilot.md`:
  - angka per prodi dari CSV kelengkapan;
  - pemakaian DeepL;
  - masukan per jenis beserta statusnya;
  - istilah yang perlu ditambahkan ke kamus atau glosarium.
- Langkah 6 Fase 5: uji menyeluruh dan `docs/log/fase-05.md`.
- Membuka versi Inggris untuk prodi lain tidak memerlukan perubahan kode: superadmin menyalakan saklarnya per prodi.
