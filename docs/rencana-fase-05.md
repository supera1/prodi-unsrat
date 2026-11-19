# Rencana Fase 5 — Versi bahasa Inggris situs prodi

Status: **disetujui** (19 November 2026) dengan semua usulan §11. Dikerjakan per langkah (§8), lebih dulu dari Fase 3
dan 4. Keputusan: K-P37.
Dasar: [rencana Fase 2](rencana-fase-02.md), keputusan K-P23–K-P36, dan panduan admin prodi.

---

## 0. Titik awal

- **Situs sudah tayang di produksi** sebagai `https://prodi.unsrat.ac.id` (admin `https://bo-prodi.unsrat.ac.id`,
  hanya dari jaringan kampus/VPN), di belakang load balancer.
- **Kebutuhan:** akreditasi internasional mewajibkan situs prodi tersedia dalam bahasa Inggris. Versi Inggris
  `/<slug>/en/` sejak Fase 1 dijadwalkan di Fase 5, dan `en` sudah dicadangkan sehingga tidak bisa dipakai sebagai slug
  (`platform/slug.py`). Fase 3 (halaman akar dengan pencarian) dan Fase 4 (peluncuran ke 97 prodi) tetap direncanakan;
  Fase 5 dikerjakan lebih dulu dan tidak bergantung pada keduanya.
- **Pilihan yang ditimbang** (19 November 2026):
  - widget terjemahan gratis (GTranslate gratis, Google Translate): ditolak, karena memerlukan skrip pihak ketiga di
    setiap halaman (bertentangan dengan CSP dan aturan keamanan), tidak menghasilkan halaman Inggris yang diindeks, dan
    tidak tampil tanpa JavaScript;
  - proxy terjemahan berbayar (Weglot, GTranslate berbayar): ditolak, karena biayanya per kata untuk 97 prodi, dan
    isinya disajikan server vendor di luar alur persetujuan, saringan spam, dan pemantau;
  - plugin WordPress (TrueLang, TranslatePress, WPML): tidak cocok, karena platform ini bukan WordPress;
  - **versi Inggris bawaan platform dengan draf terjemahan mesin yang ditinjau prodi: dipilih.**
- **Data resmi berbahasa Inggris sudah ada** di salinan data www untuk ke-97 prodi: nama prodi (`nama_en`), bidang kerja
  lulusan (`bidang_kerja_en`), dan 1.259 CPL (`isi_en`); juga nama unit (`nama_en`) dan identitas universitas di
  `situs.json`. Kalender akademik www belum punya versi Inggris.

## 1. Tujuan Fase 5

1. Setiap prodi bisa memiliki **situs berbahasa Inggris** di `https://prodi.unsrat.ac.id/<slug>/en/`, dengan menu,
   halaman, dan tampilan yang sama dengan versi Indonesia, berupa halaman statis yang diindeks mesin pencari.
2. **Isi Inggris ditulis dan diterbitkan lewat admin** dengan alur persetujuan yang sama (operator menulis, admin prodi
   menerbitkan; K-P24), riwayat, dan saringan spam.
3. **Draf terjemahan mesin** dari versi Indonesia, dengan daftar istilah tetap, supaya prodi tidak menerjemahkan dari
   nol; setiap terjemahan mesin diperiksa manusia sebelum terbit.
4. **Isi Inggris yang tertinggal** dari versi Indonesia terlihat oleh prodi dan superadmin.
5. Tidak ada skrip pihak ketiga dan tidak ada pelonggaran CSP; situs tetap berfungsi tanpa JavaScript.

## 2. Di luar lingkup Fase 5

| Pekerjaan | Keterangan |
|---|---|
| Bahasa selain Inggris | Rancangan alamat dan model data memungkinkan bahasa lain kelak, tetapi tidak dikerjakan |
| Antarmuka admin berbahasa Inggris | Admin tetap berbahasa Indonesia; hanya isian isi yang berbahasa Inggris |
| Kalender akademik berbahasa Inggris | Menunggu versi Inggris dari www; sampai itu, versi Inggris menautkan kalender berbahasa Indonesia |
| Halaman akar `/en/` dengan pencarian | Bersama Fase 3 |
| Mengubah data resmi berbahasa Inggris dari www | Tetap lewat www atau timpaan di halaman Data prodi (K-P16) |

## 3. Rancangan

### 3.1 Alamat dan struktur

- Versi Inggris sebuah halaman ada di alamat yang sama dengan sisipan `en/` setelah slug:
  `/s1informatika/profil/sejarah/` ↔ `/s1informatika/en/profil/sejarah/`. Bagian alamat tidak diterjemahkan, sehingga
  pasangan halaman selalu jelas, tautan stabil, dan halaman tambahan memakai alamat yang sama
  (`/<slug>/en/halaman/<alamat>/`).
- Setiap halaman memakai `lang="en"`, `<link rel="alternate" hreflang="id|en">` ke pasangannya, dan tombol
  **English / Indonesia** di kepala halaman. Tombol ini tautan biasa ke pasangan halaman (tanpa JavaScript), dan hanya
  tampil bila pasangannya ada.
- Halaman yang belum punya isi Inggris terbit **tidak dibuat** di versi Inggris dan tidak muncul di menunya. Tidak ada
  halaman campuran atau setengah jadi.
- `sitemap.xml` memuat kedua bahasa dengan pasangan `hreflang`.
- Versi Inggris sebuah prodi baru tayang setelah **diaktifkan** (§3.6).

### 3.2 Halaman per jenis

| Jenis | Versi Inggris |
|---|---|
| Halaman wajib dan opsional (isi dari penyunting) | Dari isi Inggris yang terbit (§3.4) |
| Halaman tambahan | Dari isi Inggris yang terbit; nama menu Inggris diisi di menu Halaman tambahan |
| Beranda | Bagian depan beranda berbahasa Inggris (judul, subjudul, pengantar, kartu fakta); nilai resmi tetap (K-P15) |
| Profil Lulusan dan CPL, Spesifikasi | Dari data resmi berbahasa Inggris (`nama_en`, `bidang_kerja_en`, CPL `isi_en`) |
| Akreditasi | Status dari data resmi dengan label Inggris; dokumen dari isi Inggris halaman Akreditasi, atau dokumen yang sama |
| Dosen Tetap | Daftar dan tautan yang sama; hanya label yang berbahasa Inggris |
| Kalender Akademik | Tautan ke kalender berbahasa Indonesia, dengan keterangan (§2) |
| Kontak | Identitas dan kontak dari `situs.json` (sudah punya versi Inggris) |
| Pengumuman | Langkah 4 (opsional): hanya pengumuman yang punya versi Inggris |

### 3.3 Teks antarmuka dan label

- **Teks tetap situs** (menu, kepala dan kaki halaman, "sedang dilengkapi", jejak halaman, tanggal, tombol) diambil
  dari satu kamus `platform/template/teks-en.json`. Uji memastikan setiap kunci yang dipakai templat ada di kamus.
- **Menu induk** (`menu.json`) mendapat `label_en` dan `deskripsi_en`. Label menu yang diganti prodi (menu Menu) dan
  nama halaman tambahan mendapat isian Inggris; bila kosong, dipakai label Inggris bawaan.
- **Templat isi** (`isi_halaman.py`) mendapat label Inggris setiap bagian dan kolom tabel, untuk judul dan kepala tabel
  di situs. Pilihan tetap (Wajib/Pilihan, Lokal/Nasional/Internasional, jenis luaran, responden survei, dan
  sejenisnya) diterjemahkan dari kamus, bukan oleh mesin.
- **Label kriteria akreditasi** (K-P33) mendapat isian Inggris di menu Kriteria akreditasi.

### 3.4 Isi Inggris di penyunting

- Penyunting setiap halaman mendapat tab **Bahasa Indonesia | English**. Versi Inggris punya draf, ajukan, terbitkan,
  kembalikan, tarik, dan riwayat sendiri, dengan aturan peran yang sama.
- Versi Inggris memakai **struktur dan berkas versi Indonesia**: baris tabel, angka, tahun, tautan, PDF, foto, dan
  sematan mengikuti versi Indonesia; yang diisi hanya teksnya. Formulir Inggris menampilkan teks Indonesia di samping
  setiap isian sebagai acuan.
- **Tanda "perlu diperbarui":** saat isi Inggris diterbitkan, sidik isi Indonesia yang menjadi dasarnya ikut disimpan.
  Bila versi Indonesia yang terbit berubah sesudahnya, halaman itu ditandai **perlu diperbarui** di daftar Isi halaman,
  dasbor prodi, dan kelengkapan superadmin. Versi Inggris yang lama tetap tayang sampai diperbarui; baris yang ditambah
  di versi Indonesia tampil di versi Inggris setelah teksnya diisi.
- **Tabel panjang:** nama mata kuliah diterjemahkan. Judul tugas akhir dibiarkan dalam bahasa aslinya secara bawaan;
  prodi boleh memilih menerjemahkannya.
- Daftar Isi halaman mendapat kolom **English**: belum ada, draf, menunggu, terbit, perlu diperbarui.
- **Pelaksanaan (langkah 2, 19 November 2026):**
  - isi Inggris disimpan sebagai memori terjemahan per teks (`{"teks": {teks Indonesia: teks Inggris}, "asal": {...}}`),
    bukan salinan halaman. Terjemahan dicari menurut bunyi teksnya, jadi baris yang ditambah, dihapus, atau diurutkan
    ulang di versi Indonesia tidak pernah tertukar dengan terjemahan baris lain (`platform/isi_inggris.py`);
  - "perlu diperbarui" dihitung dari cakupan: teks versi Indonesia yang terbit yang belum punya terjemahan. Cara ini
    menggantikan sidik isi, dengan hasil yang sama dan tanpa catatan yang bisa usang;
  - nama orang, nama mitra, kode, nama sistem, dan nama jurnal tidak diterjemahkan (`terjemah=False` di templat);
    judul karya dan nama organisasi boleh diterjemahkan (`"boleh"`); teks alternatif foto juga boleh;
  - tabel yang diisi lewat Excel (judul tugas akhir) tampil dalam bahasa aslinya; pilihan menerjemahkannya dibuat
    bersama terjemahan mesin di langkah 3, karena ribuan judul tidak muat di formulir.

### 3.5 Terjemahan mesin

- Tombol **Terjemahkan dari versi Indonesia** di tab English mengisi draf Inggris dari isi Indonesia yang terbit (atau
  drafnya). Hanya isian teks yang dikirim; isian yang sudah diisi manusia tidak ditimpa kecuali diminta.
- **Penyedia: DeepL API** (bahasa sumber Indonesia, sasaran Inggris), dipanggil dari server admin dengan pustaka standar
  Python (tanpa paket baru). Sambungannya dibuat di balik satu antarmuka kecil, sehingga Google Cloud Translation bisa
  menggantikannya bila diputuskan kelak.
- **Daftar istilah tetap** dari data resmi: nama prodi (`nama_en`), nama fakultas (`unit.nama_en`), nama universitas,
  gelar (tidak diterjemahkan), dan istilah akreditasi yang baku. Daftar ini dikirim sebagai glosarium DeepL dan diperiksa
  lagi sesudahnya.
- **Markah dilindungi:** alamat tautan, `**tebal**`, dan butir daftar diganti penanda sebelum dikirim dan dikembalikan
  sesudahnya, sehingga mesin tidak mengubah alamat atau merusak markah.
- Hasil terjemahan lewat **saringan spam** dan pemeriksaan isi yang sama, lalu masuk draf dengan tanda
  "Terjemahan mesin — periksa sebelum terbit". Draf ini tidak bisa diterbitkan tanpa dibuka dan disimpan dulu oleh
  admin prodi.
- **Batas pemakaian:** jumlah karakter per prodi per hari dan per bulan untuk seluruh platform; pemakaian tercatat di
  log audit dan tampil di dasbor superadmin.
- **Variabel stack baru:** `TERJEMAH_PENYEDIA` (`deepl` atau kosong), `TERJEMAH_KUNCI` (kunci API, rahasia),
  `TERJEMAH_BATAS_HARIAN`, `TERJEMAH_BATAS_BULANAN`. Tanpa kunci, tombol tidak tampil dan isi Inggris diketik sendiri.
  Kunci API disiapkan UPA TIK; harga dan kuota penyedia diperiksa saat langkah 3.

### 3.6 Mengaktifkan versi Inggris dan kelengkapan

- Superadmin mengaktifkan versi Inggris per prodi di menu Prodi. Syarat yang ditampilkan (bukan pemaksaan): bagian
  depan beranda Inggris sudah terbit, dan setidaknya halaman Profil (sejarah, visi-misi, struktur organisasi) sudah
  punya isi Inggris.
- Selama belum aktif, admin prodi tetap bisa mengisi dan menerbitkan isi Inggris dan melihatnya di pratinjau; situs
  belum membuat `/<slug>/en/`.
- Kelengkapan superadmin dan CSV mendapat kolom: versi Inggris aktif, halaman wajib dengan isi Inggris terbit, dan
  halaman yang perlu diperbarui.

### 3.7 Pengumuman (langkah 4, opsional)

- Pengumuman boleh diberi judul, ringkasan, dan isi berbahasa Inggris, dengan tombol terjemahan mesin yang sama.
- Daftar berita Inggris hanya memuat pengumuman yang punya versi Inggris. Foto dan PDF dipakai bersama.

## 4. Model data

| Berkas | Isi |
|---|---|
| `data/prodi/<kode>/halaman-<id>-en.json` | Isi Inggris sebuah halaman, halaman `"<id>:en"` di `isi_halaman.py`: `terbit` dan `draf` berisi memori terjemahan (§3.4), dengan status, catatan, dan `versi` yang sama dengan halaman lain. Nama ini sah menurut `lokasi.NAMA_SAH`, jadi riwayat langsung berlaku |
| `data/prodi/<kode>/situs.json` | `en`: aktif atau tidak, label menu Inggris, bagian depan beranda Inggris |
| `data/prodi/<kode>/tambahan.json` | `label_en` setiap halaman tambahan |
| `data/prodi/<kode>/kriteria.json` | label kriteria Inggris |
| `platform/template/teks-en.json` | Kamus teks tetap situs |
| `platform/template/menu.json`, `platform/isi_halaman.py` | `label_en`, `deskripsi_en`; label Inggris bagian, kolom, dan pilihan |
| `data/prodi/<kode>/terjemah-pemakaian.json` | Jumlah karakter terjemahan mesin prodi itu per hari dan per bulan; batas bulanan platform dihitung dari jumlah semua prodi |

- Isi Inggris hanya menyimpan teks. Saat dibangun, teks itu digabung dengan struktur, angka, dan berkas versi Indonesia
  yang terbit; teks yang belum diterjemahkan tidak tampil di versi Inggris.
- Kunci yang tidak dikenal tetap disimpan, seperti di Fase 2, sehingga perubahan templat tidak menghapus isi.

## 5. Keamanan dan privasi

- Tidak ada skrip pihak ketiga; CSP, sandbox sematan, dan pemantau tidak berubah. Pemantau juga memeriksa `/en/`.
- Semua teks Inggris, termasuk hasil mesin, di-escape dan lewat `saringan_spam.py`.
- **Yang dikirim ke penyedia terjemahan hanya teks isi halaman** yang memang untuk situs publik, tidak pernah akun,
  catatan pengembalian, log, atau data lain. Draf yang belum terbit bisa memuat teks yang belum diperiksa; peringatan
  privasi di formulir (Fase 2 §5) tetap berlaku, dan panduan menyebut bahwa teks dikirim ke penyedia terjemahan.
- Kunci API hanya di `.env`/volume rahasia, tidak pernah di repo, log, atau halaman admin.
- Setiap rute baru memakai `@akses` dan masuk uji matriks peran × rute; tombol terjemahan hanya untuk peran yang boleh
  menyunting halaman itu, dan batas pemakaian diperiksa di server.

## 6. Pilot

- **Prodi pilot:** prodi yang sedang menuju akreditasi internasional. Selama belum disebutkan, dipakai tiga prodi pilot
  Fase 2: S1 Teknik Informatika, S1 Pendidikan Dokter Gigi, dan S1 Teknik Elektro.
- **Pelaksanaan:** versi Inggris diaktifkan untuk prodi pilot setelah isinya cukup; masukan dikumpulkan lewat menu
  Masukan; perbaikan dikerjakan per langkah kecil.
- **Ukuran keberhasilan** (usulan): setiap prodi pilot menerbitkan versi Inggris beranda dan minimal 15 dari 22 halaman
  wajib tanpa bantuan pengembang; terjemahan mesin dipakai dan diperiksa; tidak ada istilah resmi yang salah tayang.

## 7. Uji

- **Situs:** halaman Inggris lolos pemeriksaan halaman (satu `h1`, heading berurutan, `lang="en"`, tanpa gulir datar di
  320 px); pasangan `hreflang` dan tombol bahasa benar dua arah; halaman tanpa isi Inggris tidak dibuat dan tidak
  ditautkan; prodi yang belum aktif tidak punya `/en/`; sitemap memuat kedua bahasa.
- **Kamus:** setiap teks tetap templat dan setiap label menu, bagian, kolom, dan pilihan punya padanan Inggris.
- **Penyunting dan alur:** isi Inggris dengan alur dan riwayat sendiri; struktur dan berkas mengikuti versi Indonesia;
  tanda perlu diperbarui muncul dan hilang dengan benar; uji matriks peran × rute mencakup rute baru.
- **Terjemahan mesin** dengan penyedia tiruan (tanpa jaringan): markah dan alamat utuh, glosarium dipakai, hasil berisi
  teks judi ditolak, batas harian dan bulanan, kegagalan penyedia memberi pesan yang jelas tanpa merusak draf.
- Uji yang ada tetap lulus; semua uji berjalan saat image dibangun (K-P20).

## 8. Urutan kerja (satu branch per langkah, setiap langkah ditinjau)

0. **Rencana ini** (`fase/05-0-rencana`): K-P37, urutan fase di README.
1. **Kerangka bahasa di situs** (`fase/05-1-kerangka-en`): kamus teks tetap, label Inggris menu dan templat isi,
   `/<slug>/en/` untuk halaman dari data resmi (beranda bawaan, Profil Lulusan dan CPL, Spesifikasi, Akreditasi,
   Dosen, Kalender, Kontak), tombol bahasa, `hreflang`, sitemap, saklar aktif per prodi untuk superadmin.
2. **Isi Inggris di penyunting** (`fase/05-2-isi-en`): tab English, model data dan alur, tanda perlu diperbarui, kolom
   English di daftar dan kelengkapan; beranda, label menu, halaman tambahan, dan label kriteria berbahasa Inggris.
3. **Terjemahan mesin** (`fase/05-3-terjemah-mesin`): sambungan DeepL, glosarium, perlindungan markah, batas pemakaian,
   log audit, variabel stack di `.env.example` dan `docs/deploy.md`.
4. **Pengumuman berbahasa Inggris** (`fase/05-4-pengumuman-en`, opsional).
5. **Panduan dan pilot**: bagian "Versi bahasa Inggris" di panduan admin prodi; pilot di produksi dengan versi Inggris
   aktif hanya untuk prodi pilot.
6. **Uji menyeluruh** dan `docs/log/fase-05.md`.

Langkah 1 dan 2 tidak memerlukan kunci API; langkah 3 memerlukan akun DeepL dari UPA TIK untuk mencoba penyedia yang
sebenarnya (ujinya memakai penyedia tiruan).

## 9. Kriteria selesai Fase 5

- [ ] Versi Inggris setiap halaman bisa diisi lewat admin dengan alur persetujuan; uji matriks akses lulus.
- [ ] `/<slug>/en/` tayang untuk prodi yang diaktifkan: halaman lolos pemeriksaan, `hreflang` dan tombol bahasa benar,
  sitemap memuat kedua bahasa, tanpa skrip pihak ketiga.
- [ ] Terjemahan mesin menghasilkan draf dengan istilah resmi yang benar dan markah utuh, dalam batas pemakaian.
- [ ] Isi Inggris yang tertinggal terlihat di dasbor prodi dan kelengkapan superadmin.
- [ ] Prodi pilot mencapai ukuran keberhasilan §6.
- [ ] Seluruh uji lulus di dalam image; panduan dan log fase ditulis.

## 10. Risiko

| Risiko | Penanganan |
|---|---|
| Terjemahan mesin salah pada istilah resmi atau akademik | Glosarium dari data resmi; kamus untuk pilihan tetap; draf mesin wajib diperiksa sebelum terbit |
| Versi Inggris tertinggal dari versi Indonesia | Sidik isi dasar dan tanda perlu diperbarui di daftar, dasbor, dan kelengkapan |
| Situs Inggris setengah jadi terlihat asesor | Halaman tanpa isi Inggris tidak dibuat; versi Inggris diaktifkan per prodi |
| Biaya atau kuota penyedia terlampaui | Batas harian dan bulanan di server; tanpa kunci, isi Inggris tetap bisa diketik |
| Penyedia tidak tersedia atau berganti | Satu antarmuka penyedia; kegagalan tidak merusak draf |
| Teks yang belum diperiksa dikirim ke pihak ketiga | Hanya teks isi halaman; peringatan di panduan dan formulir |

## 11. Pertanyaan yang diputuskan

| No | Pertanyaan | Keputusan |
|---|---|---|
| 1 | Penyedia terjemahan mesin | DeepL API, di balik antarmuka yang bisa diganti; kunci dari UPA TIK |
| 2 | Bentuk alamat | `/<slug>/en/<alamat yang sama>/` |
| 3 | Pengumuman | Diterjemahkan belakangan (langkah 4, opsional) |
| 4 | Tabel panjang | Nama mata kuliah diterjemahkan; judul tugas akhir tetap bahasa asli, prodi boleh menerjemahkan |
| 5 | Prodi pilot | Prodi yang menuju akreditasi internasional; sampai disebutkan, tiga prodi pilot Fase 2 |

### Jawaban (pengguna, 19 November 2026)

Rencana opsi D disetujui dengan semua usulan di atas ("Setuju, mulai langkah 0"). Prodi pilot belum disebutkan, jadi
dipakai tiga prodi pilot Fase 2 sampai ada prodi lain yang disebutkan.
