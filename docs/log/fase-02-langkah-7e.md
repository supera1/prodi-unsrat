# Fase 2 langkah 7e — Sematan di halaman bawaan (K-P36)

Tanggal: 29 Oktober 2026. Branch: `fase/02-7e-sematan-halaman` (di atas `fase/02-7d-tampilan`).

## Latar
Masukan nomor 3 dari staging: halaman Jadwal Kuliah dan Ujian hanya bisa menautkan PDF di Google Drive lewat teks
Uraian. Pengguna ingin isi Google Sheets, Drive, atau Forms tampil langsung di halaman, dengan keterangan cara
menyematkan seperti keterangan cara membuat tautan. Disetujui sebagai K-P36: bagian Sematan terpisah, bukan kode di
dalam teks Uraian.

## Yang dikerjakan
- **Templat isi** (`isi_halaman.py`):
  - `sematan_daftar()` adalah bagian Sematan yang sama untuk halaman bawaan dan halaman tambahan: judul, alamat atau
    kode sematan, tinggi bingkai, keterangan; paling banyak 5;
  - `halaman()` menyisipkannya ke setiap templat: tepat di bawah `uraian`; tanpa uraian, di atas `dokumen`; selain itu
    di akhir, sebelum Bagian tambahan. Contoh halaman Jadwal: Uraian → Sematan → Jadwal → Jadwal dalam PDF;
  - `CARA_SEMATAN` adalah keterangan cara menyematkan (Google Drive, Sheets atau Docs, Forms), satu layanan per baris.
    Keterangan ini tampil di bawah judul bagian, juga saat bagian masih kosong. Penyunting kini mempertahankan baris
    baru di keterangan;
  - isi contoh memakai alamat sematan contoh yang sah.
- **Penyunting:** kotak "Cara mengisi" menyebut sematan. Alamat yang ditempel (tautan berbagi Drive
  `…/view?usp=sharing`, kode `<iframe>`) diubah ke bentuk sematan, sama seperti di halaman tambahan.
- **Situs:** templat tidak berubah; bagian sematan dari K-P35 dipakai apa adanya: bingkai bersandbox tanpa navigasi
  atas, `title`, `loading="lazy"`, dan tautan "Buka … di tab baru". CSP `frame-src` dan pemantau tidak berubah.
- **Superadmin:** `/super/tambahan` mendapat tabel "Sematan di halaman bawaan" (prodi, halaman, layanan, tautan ke
  penyunting dan situs).
- **Dokumen:** K-P36; panduan admin prodi (bagian baru "Sematan" dengan langkah per layanan, dan bagian Halaman tambahan
  merujuk ke sana); CLAUDE.md; rencana §8.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 22 rangkaian lulus.
- `uji_isi_halaman.py`:
  - setiap templat punya tepat satu Sematan di letak yang benar, sama dengan bagian Sematan halaman tambahan;
  - halaman Jadwal contoh: 3 bingkai bersandbox di antara uraian dan tabel jadwal.
- `uji_tambahan.py`:
  - penyunting Jadwal: urutan Uraian → Sematan → Jadwal, cara menyematkan per baris, tombol Tambah sematan;
  - alamat dari layanan lain ditolak, dan ketikan tetap di draf;
  - tautan berbagi Google Drive menjadi alamat sematan;
  - admin menerbitkan, dan situs menampilkan bingkai di bawah uraian;
  - daftar superadmin memuat halaman bawaan yang bersematan.
- `uji_pilot.py`: label yang disebut panduan (Tambah sematan, Judul, Alamat atau kode sematan, Tinggi bingkai) tampil
  di penyunting.
- **Dilihat di browser** (situs sementara, dengan PDF jadwal di Google Drive yang sudah ditautkan prodi pilot):
  - layar 1280 px: PDF tampil di bingkai 766 × 894 px tepat di bawah uraian, tanpa galat di konsol;
  - layar 375 px: bingkai selebar layar, tanpa gulir datar. Penampil Drive versi ponsel perlu beberapa detik sebelum
    halaman PDF muncul. Bingkai uji tanpa sandbox sama lambatnya, jadi sandbox tidak mengganggu;
  - penyunting menampilkan Sematan di bawah Uraian dengan cara menyematkan per baris; daftar superadmin memuat halaman
    Jadwal dengan layanan Google Drive.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Isi lama tetap sah; bagian Sematan kosong
  sampai diisi.
- Tautan Drive yang sekarang ada di teks Uraian halaman Jadwal prodi pilot tidak dipindahkan otomatis. Prodi
  menempelkannya sendiri di bagian Sematan.
