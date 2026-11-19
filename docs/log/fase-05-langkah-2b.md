# Fase 5 langkah 2b — Teks Inggris prodi lainnya (K-P37)

Tanggal: 19 November 2026. Branch: `fase/05-2b-teks-en`.

## Latar
Bagian kedua langkah 2 [rencana Fase 5](../rencana-fase-05.md) (§3.2, §3.3): teks berbahasa Inggris milik prodi di luar
isi halaman, yaitu bagian depan beranda, label menu yang diganti prodi, nama halaman tambahan, dan label kriteria
akreditasi. Sebelumnya versi Inggris memakai teks bawaan Inggris dan tidak pernah memakai teks Indonesia prodi.

## Yang dikerjakan
- **Bagian depan beranda** (`tampilan_prodi.py`, menu Bagian depan beranda):
  - `situs.json` mendapat `"en"`: label kecil, judul, subjudul, kalimat pengantar, label kartu fakta, dan kartu
    tambahan, diperiksa `periksa_en` (panjang, karakter, istilah terlarang);
  - `situs_inggris` menyusun beranda Inggris: teks Inggris prodi, ditambah latar, urutan, dan kartu tersembunyi dari
    pengaturan Indonesia. Kartu tambahan tampil bila label Inggrisnya diisi; nilainya memakai nilai Indonesia bila
    dikosongkan. Isian kosong memakai teks bawaan Inggris;
  - formulir mendapat bagian **Versi bahasa Inggris**, dengan teks bawaan Inggris sebagai petunjuk.
- **Menu** (`menu.py`, menu Menu): `label_en` per butir di pengaturan menu, diperiksa seperti label. Situs Inggris,
  daftar Isi halaman, dan penyunting Inggris memakainya.
- **Halaman tambahan** (`halaman_tambahan.py`, menu Halaman tambahan): `label_en` opsional, saat membuat dan di tabel
  halaman. Halaman tambahan masuk situs Inggris bila nama Inggrisnya diisi dan versi Inggris isinya terbit.
- **Kriteria akreditasi** (`kriteria.py`, menu Kriteria akreditasi): `nama_en` per kriteria dan `instrumen_en`, juga
  boleh ada di berkas bersama. `kriteria.inggris` hanya memuat kriteria bernama Inggris, sehingga label dan peta kriteria
  di situs Inggris tidak pernah memuat teks Indonesia.
- **Generator:** halaman Inggris memakai label kriteria dan peta kriteria Inggris (hanya halaman yang ada di versi
  Inggris), serta beranda dari `situs_inggris`. Pengaturan Inggris yang tidak lolos pemeriksaan diabaikan dengan
  peringatan.
- **Panduan:** bagian "Versi bahasa Inggris" menyebut keempat isian itu.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 25 rangkaian lulus.
- **`uji/uji_teks_inggris.py`** (baru):
  - pemeriksaan teks Inggris beranda, label menu, dan susunan beranda Inggris;
  - formulir beranda: teks berjudi ditolak tanpa tersimpan, ketikan tetap; beranda Inggris dari teks prodi (kartu
    tambahan dengan nilai Indonesia, kartu tanpa label Inggris tidak tampil, kartu tersembunyi tetap tersembunyi);
    beranda Indonesia tetap;
  - menu: label Inggris di situs dan penyunting; label berjudi ditolak; label Indonesia tetap;
  - halaman tambahan: tampil di situs Inggris dengan nama Inggris, hilang dari situs Inggris tanpa nama itu, nama
    tidak sah ditolak;
  - kriteria: label Inggris di halaman Inggris, hanya kriteria bernama Inggris, peta kriteria dan nama instrumen
    Inggris, label Indonesia tetap, nama berjudi ditolak; pemeriksaan halaman bersih.
- **Uji mutasi:** empat aturan dimatikan satu per satu (halaman tambahan perlu nama Inggris, kriteria tanpa nama
  Inggris, kartu tambahan perlu label Inggris, label menu Inggris prodi), dan setiap kali ada uji yang gagal.
- `uji_pilot.py`: label "Nama menu (bahasa Inggris)" yang disebut panduan tampil di admin.
- **Dilihat di browser** (situs sementara dari data awal www): beranda Inggris dengan judul, kalimat, dan kartu
  tambahan berbahasa Inggris, menu "About"; halaman History dengan label kriteria Inggris; bagian bahasa Inggris di
  formulir beranda.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Pengaturan lama tanpa teks Inggris tetap sah.
- Nama kriteria di berkas bersama (`platform/template/kriteria.json`) tidak diberi terjemahan oleh pengembang; prodi
  mengisinya sendiri atau LPMPP menambahkannya bersama konfirmasi.
