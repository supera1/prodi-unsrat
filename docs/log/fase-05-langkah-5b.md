# Fase 5 langkah 5b — Versi bahasa Inggris hanya untuk prodi akreditasi internasional (K-P38)

Tanggal: 22 November 2026. Branch: `fase/05-5b-inggris-terbatas`, dibuat di atas `fase/05-5a-terjemahkan-semua`
(PR #20 belum digabung).

## Latar
Pengguna mengoreksi: S1 Teknik Informatika, S2 Informatika, S1 Biologi, S1 Agribisnis, S1 Kehutanan ("S1 Ilmu
Kehutanan"), dan S1 Agroteknologi bukan prodi pilot, tetapi prodi yang akan mengikuti akreditasi internasional.
Karena keterbatasan API DeepL, hanya prodi-prodi ini yang boleh punya tombol terjemahan ke bahasa Inggris dan yang
bisa diterjemahkan ke bahasa Inggris, bukan semua prodi. Sebelumnya, penyunting bahasa Inggris dan terjemahan mesin
tersedia untuk semua prodi, dan saklar superadmin hanya mengatur situs `/<slug>/en/`.

## Keputusan (K-P38)
- Pembatasnya **saklar versi Inggris per prodi yang sudah ada**, bukan daftar kode di program.
  - Superadmin menyalakannya untuk keenam prodi.
  - Prodi lain yang kelak mengikuti akreditasi internasional cukup dinyalakan saklarnya.
  - Pengelolanya bukan pengembang, jadi daftar ini harus bisa diubah tanpa deploy.
- Saklar itu kini mengatur seluruh versi Inggris: situs, admin, dan terjemahan mesin.
- Mematikan saklar tidak menghapus data.

## Yang dikerjakan
- **Status saklar di setiap halaman admin:** `info_prodi` memuat `inggris`, jadi `g.prodi["inggris"]` dan `pr.inggris`
  tersedia di rute dan templat.
- **Rute versi Inggris tanpa saklar menjawab 404:**
  - tab English halaman (sunting, simpan, pratinjau, riwayat, versi lama), lewat `isi_admin.perlu_inggris`;
  - Terjemahkan semua;
  - saringan `?status=mesin` dan `?en=mesin`.
- **Yang tidak tampil tanpa saklar:**
  - tab English di penyunting, serta kolom English, angka versi Inggris, tombol Terjemahkan semua, dan saringan
    terjemahan mesin di daftar Isi halaman;
  - kotak Versi bahasa Inggris di Ringkasan prodi;
  - di pengumuman: bagian Versi bahasa Inggris dengan tombol terjemahannya, pratinjau Inggris, kolom Versi Inggris,
    saringan, dan tombol Terjemahkan semua. Aksi `terjemahkan` yang dikirim paksa tidak dijalankan;
  - isian Inggris di Bagian depan beranda, Menu, Halaman tambahan, dan Kriteria akreditasi.
- **Nilai Inggris tersimpan dipertahankan** saat formulir disimpan tanpa isian Inggris:
  - beranda: `"en"` tidak dikirim ke `tampilan_prodi.atur`;
  - menu: `label_en` lama dipakai lagi;
  - kriteria: `dengan_nama_inggris` mengambil nama Inggris lama menurut nomor, juga nama instrumen Inggris;
  - pengumuman: `"en"` lama dipakai lagi;
  - halaman tambahan sudah aman sebelumnya.
- **Hitungan draf:** `ringkasan_isi(..., inggris=False)` tidak menghitung draf Inggris yang tersembunyi, baik di
  daftar halaman, Ringkasan, maupun Kelengkapan.
- **Superadmin:**
  - dasbor mendaftar prodi yang versi Inggris dan terjemahan mesinnya aktif;
  - keterangan saklar di detail prodi menjelaskan K-P38 dan bahwa mematikan saklar tidak menghapus terjemahan.
- **Dokumen:**
  - `docs/pilot-fase-05.md` menjadi `docs/versi-inggris-prodi.md`, ditulis ulang tanpa istilah pilot, dengan tabel
    "yang diatur saklar" dan saklar dinyalakan sejak awal;
  - K-P38 di `docs/keputusan.md`;
  - rencana §3.6, §6, §9, dan §11 (jawaban 22 November 2026);
  - panduan bagian "Versi bahasa Inggris", README, dan CLAUDE.md.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 29 rangkaian lulus.
- **`uji/uji_inggris_terbatas.py`** (baru). Prodi B pernah punya versi Inggris, lalu saklarnya mati:
  - Ringkasan, daftar halaman, penyunting, daftar pengumuman, formulir pengumuman (admin dan operator), Bagian depan
    beranda, Menu, Halaman tambahan, dan Kriteria tidak memuat apa pun yang berbahasa Inggris;
  - rute versi Inggris 404, dan draf Inggris yang tersembunyi tidak dihitung;
  - formulir yang disimpan seperti browser mempertahankan setiap nilai Inggris, dan aksi terjemahkan tidak memakai
    DeepL;
  - situs B tanpa `/en/`.

  Prodi A dengan saklar menyala menampilkan semuanya. Dasbor superadmin mendaftar A saja. Setelah saklar B dinyalakan,
  bagian Inggrisnya kembali dengan nilai tersimpan, dan situs Inggrisnya dibangun.
- **Matriks akses** (`uji_admin.py`):
  - prodi A di uji kini bersaklar;
  - tujuh baris baru untuk prodi B tanpa saklar (tab English GET/POST, riwayat Inggris, Terjemahkan semua GET/POST,
    kedua saringan) menjawab 404 bagi akun prodi itu dan 403 bagi yang lain.
- **Uji yang menyesuaikan aturan baru** dengan menyalakan saklar lebih dulu: `uji_isi_inggris`, `uji_terjemah_mesin`,
  `uji_terjemahkan_semua`, `uji_pilot`, `uji_penyunting`.
  - `uji_isi_inggris` kini memeriksa bahwa tanpa saklar tidak ada tab, rute 404, dan tidak ada kotak di Ringkasan.
  - `uji_isi_inggris` juga memeriksa bahwa mematikan saklar setelah terbit menghapus versi Inggris dari situs dan
    admin, sedangkan terjemahannya tetap.
  - `uji_penyunting` memeriksa daftar tanpa dan dengan saklar.
- **Uji mutasi:** sebelas aturan dimatikan satu per satu, dan setiap kali ada uji yang gagal:
  - menimpa nilai Inggris beranda, menu, kriteria, dan pengumuman;
  - terjemahan pengumuman tanpa saklar, rute tanpa saklar, draf tersembunyi dihitung;
  - tab, isian beranda, bagian pengumuman, dan kotak Ringkasan tanpa saklar.

  Aturan "terjemahan pengumuman tanpa saklar" awalnya lolos, karena contoh pengumumannya sudah lengkap. Aturan itu
  lalu mendapat contoh pengumuman tanpa versi Inggris.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Data Inggris prodi yang saklarnya mati tetap
  utuh.
- Di produksi, superadmin perlu menyalakan saklar keenam prodi (menu Prodi). Pengembang tidak menjalankan apa pun ke
  produksi. Di komputer pengembang, saklar keenam prodi dinyalakan di data lokal untuk dicoba pengguna.
