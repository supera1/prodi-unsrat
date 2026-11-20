# Fase 5 langkah 5 — Panduan dan pilot versi bahasa Inggris (K-P37)

Tanggal: 20 November 2026. Branch: `fase/05-5-pilot-en`.

## Latar
Langkah 5 [rencana Fase 5](../rencana-fase-05.md) (§6, §8) menyiapkan pilot di produksi, dengan versi Inggris aktif
hanya untuk prodi pilot. Pengguna menyebutkan enam prodi pilot dan meminta langkah ini dimulai:

| Prodi | Kode | Alamat |
|---|---|---|
| S1 Teknik Informatika | 55201 | `/s1informatika/` |
| S2 Informatika | 55100 | `/s2informatika/` |
| S1 Biologi | 46201 | `/s1biologi/` |
| S1 Agribisnis | 54201 | `/s1agribisnis/` |
| S1 Kehutanan ("S1 Ilmu Kehutanan") | 54251 | `/s1kehutanan/` |
| S1 Agroteknologi | 54211 | `/s1agroteknologi/` |

Pengembang tidak menjalankan apa pun ke server produksi. Menyalakan saklar versi Inggris dan memasang kunci DeepL
dikerjakan superadmin dan admin VM menurut `docs/pilot-fase-05.md`.

## Yang dikerjakan
- **Persiapan pilot** (`docs/pilot-fase-05.md`), dengan susunan yang sama seperti pilot Fase 2:
  - prodi pilot beserta keadaan data resmi Inggrisnya di data awal. Keenamnya lengkap: nama prodi dan fakultas, bidang
    kerja, dan semua CPL;
  - langkah sebelum pilot: deploy, kunci DeepL dan batasnya, coba kunci sekali, periksa data resmi Inggris, akun, uji
    masuk, kapan saklar dinyalakan;
  - sesi pengenalan ±60 menit, masa pengisian dengan pemantauan mingguan, ukuran keberhasilan beserta cara melihatnya,
    dan langkah sesudah pilot.
- **Kotak Versi bahasa Inggris di Ringkasan prodi.** Ini kriteria selesai Fase 5 §9: isi Inggris yang tertinggal
  terlihat di dasbor prodi. Kotak ini muncul untuk admin dan operator, dan memuat:
  - status saklar, dengan tautan ke `/<slug>/en/` bila aktif;
  - halaman wajib yang terbit dalam bahasa Inggris;
  - halaman yang perlu diperbarui, dan halaman yang draf Inggrisnya masih memuat terjemahan mesin yang belum diperiksa
    (`ringkasan_isi` mendapat `en_mesin`);
  - pengumuman berbahasa Inggris yang terbit, dan pengumuman yang terjemahan mesinnya belum diperiksa;
  - untuk admin prodi: kekurangan data resmi berbahasa Inggris (`tarik_www.kekurangan_en`: nama prodi, bidang kerja,
    CPL tanpa terjemahan, nama fakultas) dan bagian depan beranda Inggris;
  - tautan ke bagian panduan.
- **Keterangan saklar superadmin** diperbarui. Sebelumnya masih menyebut halaman prodi "menyusul setelah penyunting
  tersedia"; kini menyebut halaman prodi, News, dan tautan ke Ringkasan prodi serta Kelengkapan.
- **Panduan admin prodi:** isi kotak Versi bahasa Inggris dan urutan kerja yang disarankan.
- **Rencana dan keputusan:** prodi pilot dicatat di rencana §6 dan §11 (jawaban pengguna) serta K-P37, dan pelaksanaan
  langkah 5 di §6.
- **Perbaikan Data prodi (ditemukan saat memeriksa kesiapan pilot):**
  - formulir Data prodi menolak setiap simpanan bagi 21 dari 97 prodi data awal, termasuk prodi pilot S2 Informatika
    dan S1 Agribisnis. Penyebabnya data www mereka sendiri melampaui batas formulir: lebih dari 40 CPL (S2 Informatika
    42, S2 Akuntansi dan S1 Sastra Jerman 45), atau nama kurikulum CPL lebih dari 20 karakter (sampai 78);
  - batasnya kini 60 CPL dan 100 karakter, dengan konstanta yang juga dipakai `maxlength` formulir;
  - CPL yang disimpan selalu memuat keempat kolomnya. Sebelumnya CPL tanpa kolom lengkap yang disimpan lewat
    `data_prodi.simpan` bisa membuat generator gagal; formulir admin sendiri selalu mengirim keempatnya.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 27 rangkaian lulus.
- `uji_data_prodi.py`:
  - setiap prodi data awal (97) bisa menyimpan formulir Data prodinya tanpa perubahan;
  - CPL dan nama kurikulum di atas batas tetap ditolak;
  - CPL disimpan dengan semua kolomnya;
  - contoh "CPL terlalu banyak" kini memakai batas + 1.
- `uji_isi_inggris.py`:
  - kekurangan data resmi Inggris;
  - dasbor admin sebelum saklar (belum diaktifkan, 1 dari 22, bidang kerja dan 1 CPL kosong, beranda bawaan, 0
    pengumuman) dan sesudahnya (aktif dengan tautan);
  - dasbor operator tanpa baris data resmi.
- `uji_terjemah_mesin.py`: dasbor menghitung halaman dengan terjemahan mesin yang belum diperiksa.
- `uji_pengumuman_inggris.py`: dasbor menghitung pengumuman bertanda mesin dan pengumuman Inggris yang terbit.
- `uji_pilot.py`: label "Versi bahasa Inggris" dan "Data resmi berbahasa Inggris" yang disebut panduan tampil di
  dasbor.
- **Uji mutasi:** delapan aturan dimatikan satu per satu (batas CPL dan batas kurikulum lama, CPL tidak dilengkapi,
  bidang kerja Inggris tanpa bidang kerja Indonesia, nama fakultas, hitungan halaman mesin, pengumuman tanpa versi
  Inggris, status saklar), dan setiap kali ada uji yang gagal.
- **Dilihat di browser** (cuplikan sementara dari data awal www, S2 Informatika): kotak Versi bahasa Inggris sebelum
  dan sesudah saklar (data resmi Inggris lengkap, 42 CPL), serta keterangan saklar di halaman prodi superadmin.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data.
- Pilot sendiri belum berjalan. Pilot menunggu PR ini digabung, stack di VM diperbarui, kunci DeepL dipasang, dan sesi
  pengenalan; saklar dinyalakan superadmin. Hasilnya dicatat di `docs/log/fase-05-pilot.md`.
- Angka data resmi Inggris di dokumen pilot berasal dari data awal (26 Oktober 2026). Data di produksi diperiksa
  superadmin lewat Ringkasan prodi.
