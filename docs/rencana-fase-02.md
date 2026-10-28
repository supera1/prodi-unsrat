# Rencana Fase 2 — Penyunting halaman wajib dan pilot 3 prodi

Status: **disetujui** (27 Oktober 2026) dengan semua usulan §11. Prodi pilot: S1 Teknik Informatika, S1 Pendidikan
Dokter Gigi, dan S1 Teknik Elektro. Dikerjakan per langkah (§8). Keputusan: K-P23–K-P26.
Dasar: [rencana Fase 1](rencana-fase-01.md) §2 dan [log Fase 1](log/fase-01.md).

---

## 0. Titik awal

- Fase 1 sudah digabung ke `main`. Ke-97 situs prodi punya 38 halaman per prodi. Dari jumlah itu, **22 halaman wajib
  akreditasi** dan 2 halaman opsional masih tertulis "sedang dilengkapi", karena penyuntingnya memang dijadwalkan di
  Fase 2.
- Keputusan Fase 1 yang tetap berlaku untuk Fase 2:

  | No | Keputusan |
  |---|---|
  | K-P2 | Tiga peran: superadmin, admin prodi, operator |
  | K-P7 | Pola sama dengan www: generator statis + admin Flask, admin hanya dari jaringan/VPN UNSRAT |
  | K-P12 | Tanpa surel; pemberitahuan lewat dasbor |
  | K-P14 | Alur operator menulis → admin prodi menerbitkan (sudah dipakai pengumuman) |
  | K-P16 | Data resmi dari www bisa diubah prodi sebagai timpaan per kolom |
  | K-P17, K-P19 | VM sendiri dengan `docker compose`; unggahan di volume lokal |

- **Prasyarat pilot:** staging sudah di-deploy admin VM, dan data www terbaru sudah diunggah. Staging cukup dibuka lewat
  alamat IP VM; nama DNS dan HTTPS diperlukan untuk produksi (`docs/pilot-fase-02.md`). Kedua kriteria Fase 1
  yang masih terbuka ("tayang di staging" dan "berjalan di VM") menjadi syarat mulai pilot, bukan syarat mulai
  membangun penyunting.

## 1. Tujuan Fase 2

1. Admin prodi dan operator **mengisi 22 halaman wajib dan 2 halaman opsional** dari admin, tanpa bantuan
   pengembang. Isinya teks, daftar, tabel, foto, dan dokumen PDF.
2. Isi melewati **alur persetujuan** operator → admin prodi, dengan pratinjau, riwayat versi, dan pemulihan.
3. Situs menampilkan isi itu dengan rapi dan aksesibel. Halaman yang belum diisi tetap tertulis "sedang dilengkapi".
4. Prodi dan superadmin melihat **kelengkapan halaman wajib** per prodi.
5. Ada halaman **Dokumen Akreditasi** per prodi, dan **label kriteria akreditasi** ditampilkan setelah daftarnya
   dikonfirmasi (§3.7).
6. **Tiga prodi pilot** mengisi halaman wajibnya di staging. Masukan mereka dipakai memperbaiki penyunting sebelum
   peluncuran ke 97 prodi di Fase 4.

## 2. Di luar lingkup Fase 2

| Pekerjaan | Fase |
|---|---|
| Halaman akar dengan pencarian dan saringan | 3 |
| Peluncuran ke 97 prodi, pelatihan semua admin prodi, beralih ke produksi | 4 |
| Keputusan tampil/sembunyi halaman wajib yang belum diisi di produksi | 4 |
| Versi bahasa Inggris `/<slug>/en/` | 5 |
| Ekspor isi ke format instrumen akreditasi (LKPS/LED) | Belum direncanakan; templat isi Fase 2 dibuat supaya kelak bisa |

## 3. Penyunting halaman

### 3.1 Isi terstruktur per halaman (usulan)

Setiap halaman wajib punya **templat isi**: bagian-bagian tetap dengan isian dan tabel yang sesuai deskripsi halaman di
menu induk dan kebutuhan akreditasi, ditambah "bagian tambahan" bebas untuk hal yang tidak tertampung. Formulirnya
dibentuk otomatis dari templat itu, dengan pola penyunting superadmin www (`site/admin/editor.py`, diadaptasi dan
dicatat di `docs/asal-modul.md`).

Alasan memilih isi terstruktur (bukan satu kotak teks bebas per halaman):
- **Seragam di 97 situs:** asesor menemukan informasi yang sama di tempat yang sama, dan prodi tahu apa yang harus diisi.
- **Lebih aman:** tidak ada HTML. Hanya teks dengan markah terbatas, daftar, dan tabel, sehingga tampilan dan
  aksesibilitas dijaga generator.
- **Bisa dipakai ulang:** ringkasan lintas prodi untuk LPMPP (Lembaga Penjaminan Mutu dan Pengembangan Pembelajaran
  UNSRAT), pencarian di Fase 3, dan kelak bahan instrumen akreditasi.

### 3.2 Jenis isian

| Isian | Keterangan |
|---|---|
| Paragraf | Teks dengan markah terbatas seperti www: `[teks tautan](https://…)` dan `**tebal**`; tanpa HTML |
| Daftar | Butir teks (mis. misi, tujuan); bisa ditambah, dihapus, diurutkan |
| Tabel | Kolom ditentukan templat, baris ditambah/dihapus/diurutkan **tanpa JavaScript**; di situs tampil sebagai tabel aksesibel yang bisa digulir di ponsel |
| Dokumen | PDF (judul, tahun, keterangan), diperiksa seperti lampiran pengumuman: tanpa konten aktif, tanpa teks judi, maksimal 20 MB |
| Foto | JPEG/PNG, teks alternatif wajib, dikodekan ulang ke 1600/800/400 px |
| Tautan | Judul + alamat `https://` (mis. jurnal, repositori, sistem informasi) |
| Angka, tanggal, pilihan | Untuk kolom tabel (tahun, jumlah, tingkat: lokal/nasional/internasional) |

### 3.3 Templat isi 22 halaman wajib (draf, disempurnakan saat pilot)

| Halaman | Isi yang disiapkan |
|---|---|
| Sejarah | Paragraf; linimasa (tahun, peristiwa); foto opsional |
| Visi dan misi | Visi keilmuan; daftar misi, tujuan, sasaran, strategi; keterkaitan dengan visi fakultas dan universitas; dokumen SK/VMTS |
| Struktur organisasi | Bagan (foto/PDF); tabel pejabat (jabatan, nama); paragraf tata pamong |
| Penjaminan mutu | Paragraf SPMI; dokumen (standar mutu, SOP, laporan AMI, tindak lanjut) |
| Kerja sama | Tabel (mitra, jenis: pendidikan/penelitian/PkM, tingkat, bentuk kegiatan, tahun, bukti PDF, manfaat) |
| Kurikulum | Paragraf struktur kurikulum; tabel mata kuliah (semester, kode, nama, SKS, wajib/pilihan, tautan RPS); dokumen kurikulum |
| Peraturan dan panduan | Dokumen (peraturan akademik, panduan PA, panduan tugas akhir) |
| Tenaga kependidikan | Tabel (nama, tugas/jabatan, unit kerja) |
| Prestasi dan pengembangan SDM | Tabel studi lanjut, pelatihan/sertifikasi, prestasi dosen (nama, kegiatan, tingkat, tahun) |
| Penelitian | Paragraf agenda; tabel (judul, ketua, tahun, sumber dana, keterlibatan mahasiswa) |
| Publikasi | Tabel (judul, penulis, wadah publikasi, tahun, tautan DOI/URL) |
| Pengabdian kepada masyarakat | Tabel seperti penelitian, ditambah mitra/lokasi |
| Luaran dan HKI | Tabel (jenis: HKI/paten/buku/TTG/produk, judul, tahun, nomor/tautan) |
| Penerimaan | Paragraf + tautan PMB; tabel per tahun (daya tampung, pendaftar, lulus seleksi, mahasiswa baru) |
| Layanan mahasiswa | Bagian per layanan (bimbingan, beasiswa, kesehatan, minat bakat, disabilitas): paragraf + tautan |
| Organisasi dan prestasi | Daftar organisasi; tabel prestasi (kegiatan, tingkat, tahun, capaian) |
| Alumni | Paragraf; tabel tracer study per tahun lulus (lulusan, terlacak, masa tunggu, kesesuaian bidang); dokumen laporan |
| Survei kepuasan | Tabel per aspek (persentase sangat baik/baik/cukup/kurang); paragraf tindak lanjut; dokumen laporan |
| Laboratorium | Tabel/kartu (nama, fungsi, kapasitas, peralatan utama, foto, SOP PDF) |
| Ruang | Tabel (jenis ruang, jumlah, kapasitas, keterangan) |
| Perpustakaan | Paragraf; tautan (katalog, repositori, jurnal daring) |
| Sistem informasi | Tabel (nama sistem, fungsi, tautan) |

Halaman opsional: **Jadwal** (dokumen PDF atau tabel), **Kelompok keahlian** (tabel kelompok, ketua, anggota, topik).
Setiap halaman juga punya paragraf pengantar dan bagian tambahan bebas.

### 3.4 Alur dan peran

Alurnya sama dengan pengumuman:
- operator menulis draf → **ajukan**;
- admin prodi **terbitkan**, atau **kembalikan** dengan catatan;
- admin prodi juga bisa menyunting dan menerbitkan langsung;
- isi yang sudah terbit bisa **ditarik** sehingga halaman kembali "sedang dilengkapi".

Pengaturan per halaman:
- Satu halaman punya satu isi terbit dan satu draf. Situs selalu menampilkan isi terbit selama draf dikerjakan.
- Bila dua orang menyunting halaman yang sama, penyimpanan kedua ditolak dengan pesan "halaman ini baru saja diubah
  oleh …; muat ulang", sehingga isi tidak saling menimpa diam-diam.
- Setiap simpanan masuk riwayat versi (bandingkan, pulihkan) dan log audit. Superadmin bisa melakukan semuanya untuk
  semua prodi.

### 3.5 Pratinjau dan tampilan di situs

Pratinjau di admin memakai gaya situs. Di situs:
- tabel punya judul kolom dan keterangan (*caption*);
- dokumen menyebut jenis dan ukurannya (mis. "PDF, 1,2 MB");
- foto berukuran responsif.

Semua tetap tanpa JavaScript, lolos pemeriksaan halaman bersama (`uji/pemeriksa_halaman.py`), dan tanpa gulir ke
samping pada lebar 320 px kecuali di dalam wadah tabel.

### 3.6 Kelengkapan

- Setiap halaman berstatus kosong, draf, menunggu, atau terbit, beserta tanggalnya.
- Dasbor prodi menampilkan "*n* dari 22 halaman wajib terbit", menggantikan baris "menunggu Fase 2".
- Superadmin mendapat tabel kelengkapan ke-97 prodi yang bisa diunduh sebagai CSV, berguna untuk LPMPP memantau
  kesiapan akreditasi.

### 3.7 Halaman Dokumen Akreditasi dan label kriteria

- **Dokumen Akreditasi** adalah satu halaman per prodi, misalnya `profil/dokumen-akreditasi`, yang memuat sertifikat
  dan SK akreditasi serta dokumen publik lain yang dipilih prodi. Dokumen yang memuat data pribadi tidak diunggah ke
  situs publik (§5).
- **Label kriteria:** setiap halaman wajib bisa diberi label kriteria instrumen akreditasi, misalnya "Kriteria 2: Tata
  Pamong, Tata Kelola, dan Kerja Sama".
  - Instrumen BAN-PT (IAPS 4.0) memakai 9 kriteria, sedangkan LAM bisa berbeda.
  - Supaya tidak ada yang dikarang, daftar label per lembaga dan pemetaan halaman → kriteria **disiapkan atau
    dikonfirmasi LPMPP UNSRAT** dulu.
  - Sebelum ada konfirmasi itu, label tidak ditampilkan. Pengembang hanya menyiapkan draf pemetaan untuk diperiksa.
  - **Diubah K-P33 (27 Oktober 2026):** admin prodi mengisi daftar kriteria dan pemetaannya sendiri di menu Kriteria
    akreditasi, tanpa menunggu LPMPP; draf pemetaan menjadi usulan untuk formulir itu.

### 3.8 Pilihan tambahan (dikerjakan bila pilot memerlukannya)

- **Impor Excel untuk tabel besar** (mata kuliah, publikasi, penelitian) dengan templat unduhan, seperti impor tautan
  dosen di Fase 1.
- **Laporan perubahan data prodi untuk pengelola www.** Superadmin mengunduh daftar timpaan data resmi semua prodi
  (kolom, nilai www, nilai prodi) untuk diteruskan ke superadmin www, sehingga www ikut diperbaiki. Fitur ini
  menggantikan butir "usulan perubahan data resmi" di rencana Fase 1 §2, yang sudah diselesaikan dengan cara lain oleh
  K-P16.

## 4. Model data

| Berkas | Isi |
|---|---|
| `data/prodi/<kode>/halaman-<id>.json` | `terbit` (isi yang tayang + oleh, waktu) dan `draf` (isi + status draf/menunggu/dikembalikan, catatan, oleh, waktu), `versi` (untuk menolak simpanan yang saling menimpa) |
| `unggahan/<kode>/…` | PDF dan foto halaman, nama acak per unggahan (pola Fase 1) |
| `platform/isi_halaman.py` | Templat isi setiap halaman (skema) dan pemeriksaannya |

- Nama berkas `prodi/<kode>/halaman-<id>` sudah sah menurut `lokasi.NAMA_SAH`, jadi riwayat versi langsung berlaku.
- Kunci yang tidak dikenal templat disimpan apa adanya, sehingga perubahan templat sesudah pilot tidak menghapus isi.

## 5. Keamanan dan privasi

- Semua teks di-escape; markah terbatas hanya membuat tautan `https://` dan huruf tebal. Semua teks diperiksa
  `saringan_spam.py`.
- PDF diperiksa `media.periksa_pdf`; foto dibuka hanya oleh `gambar_aman` lalu dikodekan ulang. SVG tidak diterima
  untuk dokumen dan foto halaman.
- Setiap rute baru memakai `@akses` dan masuk uji matriks peran × rute (operator vs admin prodi, prodi lain, superadmin).
  CSRF di setiap formulir; penyimpanan yang saling menimpa ditolak.
- Formulir memuat peringatan privasi seperti pengumuman: jangan unggah NIK, nomor HP, nilai atau IPK perorangan, data
  kesehatan, atau dokumen internal akreditasi yang memuat data pribadi.
- Tabel tenaga kependidikan dan prestasi hanya memuat nama dan peran.
- Pemantau integritas tidak berubah: halaman tetap dibangun dari data, jadi perubahan di luar admin tetap terdeteksi.

## 6. Pilot 3 prodi

- **Persiapan:**
  - staging sudah tayang dan data www terbaru sudah diunggah;
  - superadmin membuat akun admin prodi (koordinator) dan operator untuk tiap prodi pilot;
  - `docs/panduan-admin-prodi.md` sudah tersedia: panduan singkat berbahasa sederhana untuk mengisi halaman, mengajukan,
    menerbitkan, dan memulihkan versi.
- **Pemilihan:** tiga prodi dengan jenjang, fakultas, dan lembaga akreditasi berbeda, yang koordinatornya siap. Usulan
  satu calon: **S1 Teknik Informatika**, karena informatika.unsrat.ac.id disebut sebagai rujukan sejak awal. Dua lainnya
  dipilih pengguna (§11).
- **Pelaksanaan:**
  - satu sesi pengenalan;
  - masa pengisian beberapa minggu, dengan masukan dikumpulkan berkala (kendala, isian yang kurang, waktu pengisian);
  - perbaikan kecil dikerjakan per langkah dan masing-masing ditinjau.
- **Ukuran keberhasilan** (usulan, §11): setiap prodi pilot menerbitkan minimal 15 dari 22 halaman wajib tanpa bantuan
  pengembang; tidak ada masalah keamanan atau data pribadi yang tayang; setiap masukan pilot tercatat dan
  ditindaklanjuti atau diputuskan ditunda.

## 7. Uji

- **Templat isi:** setiap halaman bisa diisi penuh dan kosong. Isian salah ditolak dengan pesan yang jelas, termasuk
  upaya HTML/skrip di teks, tautan `javascript:`, dan teks judi.
- **Situs:** halaman dengan semua jenis isian lolos pemeriksaan halaman, tanpa skrip, dan tanpa gulir ke samping di
  320 px (diperiksa di browser). Tabel besar (mis. 80 mata kuliah) tetap terbaca.
- **Alur:** draf → ajukan → terbit → tarik; dikembalikan dengan catatan; simpanan yang saling menimpa ditolak; pulihkan
  versi; operator tidak bisa menerbitkan.
- **Matriks akses:** semua rute baru × semua peran, dengan uji mutasi pada aturan penting.
- **Uji penerimaan Fase 2** (`uji/uji_fase2.py`): kriteria §9 diperiksa satu per satu, seperti `uji_fase1.py`. Seluruh
  uji tetap berjalan di dalam image saat build.

## 8. Urutan kerja (satu branch per langkah, setiap langkah ditinjau)

0. **Rencana ini** (`fase/02-0-rencana`), juga membetulkan status Fase 1 di README dan rencana Fase 1.
1. **Model data dan templat isi**: 22 + 2 templat, pemeriksaan, dan tampilan di generator, diuji dengan isi contoh.
   Belum ada formulir.
2. **Penyunting di admin**: formulir dari templat (adaptasi `editor.py` www), daftar dan tabel tanpa JavaScript, unggah
   PDF dan foto, pratinjau, simpan draf.
3. **Alur dan kelengkapan**: ajukan/terbitkan/kembalikan/tarik, penolakan simpanan yang saling menimpa, riwayat isi
   halaman, kelengkapan di dasbor prodi dan superadmin (dengan unduhan CSV).
4. **Dokumen Akreditasi dan label kriteria**: halaman dokumen sudah bisa dikerjakan; label menunggu daftar dari LPMPP.
   **4b.** Label kriteria diisi admin prodi (K-P33, `fase/02-4b-kriteria-admin`).
5. **Panduan dan persiapan pilot**: `docs/panduan-admin-prodi.md`, akun prodi pilot (dibuat superadmin di staging).
6. **Pilot**: masukan dan perbaikan dalam beberapa langkah kecil (`fase/02-6a-…`, `fase/02-6b-…`).
7. **Pilihan tambahan**: impor Excel tabel besar (dikerjakan, pembaruan §11); laporan perubahan data untuk pengelola
   www bila diperlukan pilot.
8. **Uji menyeluruh** dan `docs/log/fase-02.md`.

Langkah 1–4 tidak bergantung pada staging. Langkah 5–6 menunggu staging tayang (§0).

## 9. Kriteria selesai Fase 2

- [ ] Ke-22 halaman wajib dan 2 halaman opsional bisa diisi lewat admin dengan alur persetujuan; uji matriks akses
  lulus tanpa kebocoran antar-prodi.
- [ ] Setiap jenis isian tampil aksesibel di situs: lolos pemeriksaan halaman, tanpa skrip, tanpa gulir ke samping di
  320 px.
- [ ] Kelengkapan halaman wajib ke-97 prodi tampil di dasbor superadmin.
- [ ] Tiga prodi pilot mencapai ukuran keberhasilan §6 di staging; masukan mereka tercatat dan ditindaklanjuti.
- [ ] Seluruh uji lulus di dalam image; log fase ditulis.

## 10. Risiko

| Risiko | Penanganan |
|---|---|
| Isi bergantung pada dokumen yang dimiliki prodi, bukan pada penyunting | Kelengkapan terlihat di dasbor; pilot menunjukkan halaman mana yang paling sulit diisi |
| Data pribadi ikut terunggah | Peringatan di formulir, persetujuan admin prodi, tombol tarik, riwayat |
| Templat isi tidak cocok untuk semua lembaga akreditasi | Bagian tambahan bebas di setiap halaman; templat direvisi setelah pilot tanpa menghapus isi |
| Staging belum tayang saat penyunting siap | Langkah 1–4 dikerjakan lebih dulu; pilot menunggu deploy |
| Dua orang menyunting halaman yang sama | Simpanan yang saling menimpa ditolak dengan pesan |

## 11. Pertanyaan untuk diputuskan

| No | Pertanyaan | Usulan |
|---|---|---|
| 1 | Tiga prodi pilot | S1 Teknik Informatika + dua prodi lain dengan jenjang/fakultas/lembaga berbeda, dipilih pengguna |
| 2 | Isi halaman terstruktur per halaman (templat) atau satu kotak teks bebas | Terstruktur, dengan bagian tambahan bebas (§3.1) |
| 3 | Label kriteria akreditasi: siapa yang menyiapkan daftarnya, dan tampil di mana | Disiapkan/dikonfirmasi LPMPP; tampil di setiap halaman wajib dan di halaman Dokumen Akreditasi |
| 4 | Dokumen akreditasi di situs | Hanya dokumen yang boleh publik (sertifikat, SK, ringkasan); dokumen berisi data pribadi tidak diunggah |
| 5 | Siapa yang mengisi | Operator dan admin prodi, dengan persetujuan admin prodi (seperti pengumuman) |
| 6 | Butir "usulan perubahan data resmi" di rencana Fase 1 §2 | Diganti laporan perubahan data untuk pengelola www (§3.8) |
| 7 | Impor Excel untuk tabel besar | Dikerjakan di Fase 2 hanya bila pilot memerlukannya |
| 8 | Ukuran keberhasilan pilot | Minimal 15 dari 22 halaman wajib terbit per prodi pilot, tanpa bantuan pengembang |
| 9 | Jadwal deploy staging oleh admin VM | Diperlukan sebelum langkah 5 |

### Jawaban (pengguna, 27 Oktober 2026)

Semua usulan di atas disetujui: pertanyaan 2–8 sesuai kolom "Usulan". Untuk pertanyaan 1, prodi pilot pertama adalah
S1 Teknik Informatika, dan dua lainnya akan disebutkan pengguna. Pertanyaan 9 (jadwal deploy staging) tetap mengikuti
admin VM; pilot dimulai setelah staging tayang.

Pembaruan (pengguna, 27 Oktober 2026):
- Prodi pilot kedua dan ketiga: **S1 Pendidikan Dokter Gigi** (12201, LAM-PTKes) dan **S1 Teknik Elektro** (20201,
  LAM-Teknik).
- Impor Excel untuk tabel besar dikerjakan di langkah 7 tanpa menunggu pilot (mengubah jawaban pertanyaan 7).
