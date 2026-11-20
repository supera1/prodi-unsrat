# Fase 5 langkah 4 — Pengumuman berbahasa Inggris (K-P37)

Tanggal: 20 November 2026. Branch: `fase/05-4-pengumuman-en`.

## Latar
Langkah 4 [rencana Fase 5](../rencana-fase-05.md) (§3.7, opsional): pengumuman dan berita prodi dalam bahasa Inggris,
dengan tombol terjemahan mesin dari langkah 3. Sebelumnya menu berita tidak ada di `/<slug>/en/` dan pengumuman hanya
tampil di situs Indonesia. Pengguna meminta langkah ini setelah PR langkah 3 digabung.

## Yang dikerjakan
- **Model (`platform/pengumuman.py`):**
  - butir pengumuman boleh punya `"en"`: judul, ringkasan, isi (aturan teks biasa yang sama), `mesin` (hasil mesin yang
    belum diperiksa per isian) dan `asal` (teks Indonesia yang diterjemahkan). Diperiksa seperti teks Indonesia (tanpa
    HTML, saringan spam, batas panjang); isi Inggris perlu judul dan ringkasan Inggris;
  - `keadaan_en`: kosong, belum lengkap, terjemahan mesin belum diperiksa, atau lengkap. `inggris(b)` hanya mengembalikan
    butir lengkap tanpa tanda mesin, dengan tanggal, kategori, foto, dan PDF yang sama;
  - `perlu_diperbarui`: isian yang teks Indonesianya berubah sejak diterjemahkan;
  - versi Inggris ikut status dan alur persetujuan butirnya, tanpa berkas atau riwayat tersendiri.
- **Admin (`pengumuman_admin.py`, formulir pengumuman):**
  - bagian **Versi bahasa Inggris (opsional)** dengan Judul, Ringkasan, dan Isi (Inggris), keadaan versi Inggris, dan
    catatan bila situs Inggris prodi belum diaktifkan; pratinjau isi Inggris;
  - **Simpan dan terjemahkan dari versi Indonesia** (hanya bila penyedia terpasang, untuk pengumuman yang sudah
    disimpan): menyimpan formulir, lalu mengisi isian Inggris yang kosong (atau semua, dengan pilihan terjemahkan
    ulang). Hasilnya bertanda mesin. Batas harian dan bulanan, pencatatan pemakaian, glosarium istilah resmi, dan
    pesan galat sama dengan halaman. Log audit `pengumuman-en-terjemahan-mesin`;
  - isian yang diubah orang kehilangan tanda mesinnya; kotak **Saya sudah memeriksa versi Inggris pengumuman ini**
    menghapus semua tanda dan menandai terjemahan sesuai dengan teks Indonesia sekarang;
  - teks Indonesia yang berubah sejak diterjemahkan diberi tanda kuning; terjemahan lama tetap tampil;
  - daftar pengumuman mendapat kolom **Versi Inggris**.
- **Situs (`bangun.py`, templat berita):**
  - `bangun_pengumuman` membangun daftar, kategori, arsip tahun, dan halaman butir untuk kedua bahasa, di bawah `akar`
    bahasanya. Versi Inggris hanya memuat butir dari `pengumuman.inggris`, tanpa RSS;
  - menu **News** ada di versi Inggris selama ada pengumuman Inggris yang terbit. Beranda Inggris memuat berita terbaru,
    dan halaman isi Inggris memuat kabar terkait;
  - tombol bahasa dan `hreflang` menghubungkan halaman yang ada di kedua bahasa (daftar, kategori dan arsip yang
    sama-sama ada, butir yang punya versi Inggris). Sitemap memasangkannya otomatis;
  - kategori mendapat `label_en`. Teks tetap templat berita masuk kamus `teks-en.json` (19 teks baru). Ukuran PDF
    memakai titik desimal di versi Inggris;
  - teks alternatif foto dan judul PDF (dipakai bersama) ditandai `lang="id"` di halaman Inggris.
- **Panduan admin prodi:** bagian "Pengumuman dan berita" menjelaskan versi Inggris dan terjemahan mesinnya, dan bagian
  "Versi bahasa Inggris" menyebut menu News.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 27 rangkaian lulus.
- **`uji/uji_pengumuman_inggris.py`** (baru):
  - model: versi Inggris sah dan tidak sah (bukan objek, kunci asing, isi tanpa judul, HTML, judi, terlalu panjang,
    tanda mesin/asal tidak sah), keadaan versi Inggris, butir Inggris, teks yang berubah, nama Inggris kategori;
  - admin tanpa penyedia: versi Inggris diketik sendiri tersimpan bersama `asal`, tanpa kotak terjemahan mesin, kolom
    daftar; teks berjudi ditolak tanpa tersimpan;
  - admin dengan penyedia tiruan: perkiraan, isian kosong terisi dan bertanda, ketikan sendiri tetap, pemakaian, log
    audit; terbit dengan tanda mesin tetapi tidak di situs Inggris (tanpa menu News); isian yang diubah kehilangan
    tandanya; dicentang lalu tampil; teks Indonesia berubah ditandai; tanpa timpa tidak menimpa (juga bila teks
    Indonesia yang sama ada di dua isian); penyedia gagal menyimpan formulir tanpa mengubah terjemahan; terjemahkan
    ulang; operator tidak mengubah butir yang terbit;
  - situs: daftar Inggris hanya pengumuman berversi Inggris, halaman butir (kategori dan tanggal Inggris, `lang="id"`
    untuk teks foto dan judul PDF), beranda Inggris, kategori dan arsip, tanpa RSS Inggris, `hreflang` dua arah, daftar
    dan kategori Indonesia hanya berpasangan bila ada versi Inggrisnya, sitemap; pemeriksaan halaman bersih.
- **Uji mutasi:** delapan aturan dimatikan satu per satu (tanda mesin menghalangi tampil, pemeriksaan teks Inggris,
  isi Inggris wajib bila ada isi Indonesia, diubah berarti diperiksa, tanpa timpa tidak menimpa, pasangan bahasa hanya
  bila ada versi Inggris, menu News hanya bila ada berita Inggris, `asal` tidak bergeser tanpa perubahan). Setiap kali
  ada uji yang gagal. Aturan "tanpa timpa" awalnya lolos, lalu mendapat uji teks yang sama di dua isian.
- `uji_pilot.py`: label bagian Inggris pengumuman dan kolom daftar yang disebut panduan tampil di admin.
- **Keluaran Indonesia tidak berubah:** situs dari data lokal dibangun dengan `main` dan dengan branch ini; hasilnya
  identik (0 berkas berbeda, termasuk versi Inggris s1informatika yang aktif di komputer pengembang).
- **Dilihat di browser** (cuplikan sementara dari data awal www dengan penyedia tiruan): halaman butir Inggris dengan
  menu News, kategori Inggris, dan tautan "Bahasa Indonesia"; formulir admin dengan bagian Inggris, kotak terjemahan
  mesin, dan isian bertanda mesin.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Pengumuman lama tanpa `"en"` tetap sah.
- Belum dicoba dengan akun DeepL sungguhan; cuplikan dan uji memakai penyedia tiruan, supaya kuota pengguna tidak
  terpakai.
