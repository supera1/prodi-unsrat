# Fase 5 langkah 2a — Isi Inggris di penyunting (K-P37)

Tanggal: 19 November 2026. Branch: `fase/05-2-isi-en`.

## Latar
Langkah 2 [rencana Fase 5](../rencana-fase-05.md) memuat dua bagian. Bagian ini (2a) adalah intinya: versi Inggris
halaman yang diisi prodi, dengan alur persetujuan, riwayat, dan tanda "perlu diperbarui". Teks Inggris lain (bagian
depan beranda, label menu, nama halaman tambahan, label kriteria) menyusul di 2b.

## Yang dikerjakan
- **Model** (`isi_halaman.py`, `platform/isi_inggris.py`):
  - versi Inggris sebuah halaman disimpan sebagai halaman `"<id>:en"` (`halaman-<id>-en.json`), dengan draf, ajukan,
    terbitkan, kembalikan, tarik, buang, dan riwayat yang sama dengan halaman lain;
  - isinya **memori terjemahan per teks**: `{"teks": {teks Indonesia: teks Inggris}, "asal": {...}}`. Saat dibangun,
    teks itu diletakkan di atas isi Indonesia yang terbit; struktur, baris, angka, tahun, tautan, berkas, dan sematan
    tetap milik versi Indonesia. Terjemahan dicari menurut bunyi teksnya, jadi baris yang disisipkan atau diurutkan
    ulang tidak pernah tertukar terjemahannya;
  - teks yang belum diterjemahkan: di luar daftar, uraian yang berubah tetap memakai terjemahan lamanya (`asal`); di
    dalam daftar, baris yang teks wajibnya belum diterjemahkan ditunda, sedangkan isian opsionalnya dikosongkan;
  - templat isi menandai kolom yang tidak diterjemahkan (`terjemah=False`: nama orang, mitra, kode mata kuliah, nama
    sistem, nama jurnal, tahun akademik) dan yang boleh diterjemahkan (`"boleh"`: judul penelitian, publikasi,
    pengabdian, luaran, tugas akhir, nama organisasi, lomba). Teks alternatif foto juga boleh;
  - pemeriksaan terjemahan: teks dan markah terbatas, tautan hanya `https://`, tanpa istilah judi, paling banyak
    20.000 teks; pratinjau membuang terjemahan yang tidak sah satu per satu;
  - "perlu diperbarui" dihitung dari cakupan: jumlah teks versi Indonesia terbit yang belum punya terjemahan.
- **Situs** (`bangun.py`): halaman isi dan dokumen halaman Akreditasi masuk versi Inggris bila kedua versi terbit dan
  sah. Judul bagian, nama kolom, label kartu, dan pilihan tetap diambil dari kamus. Kotak cari tabel berbahasa Inggris
  di halaman Inggris. Tombol bahasa dan `hreflang` ikut untuk halaman itu.
- **Admin** (`isi_admin.py`):
  - tab **Bahasa Indonesia | English** di penyunting, dan penyunting Inggris `/prodi/<kode>/halaman/<id>/en`
    (`halaman_sunting_en.html`): setiap teks Indonesia tampil sekali dengan isian Inggrisnya; teks yang berubah sejak
    diterjemahkan ditandai kuning; tabel Excel tidak masuk formulir;
  - perubahan versi Indonesia saat menerjemahkan diberitahukan;
  - pratinjau, riwayat, dan "Jadikan draf" versi Inggris (rute `/en/pratinjau`, `/en/riwayat`, `/en/riwayat/<versi>`);
  - daftar Isi halaman: kolom **English** (belum ada, draf, menunggu, terbit, perlu diperbarui) dan jumlah halaman wajib
    berversi Inggris. Saringan status ikut menghitung draf versi Inggris;
  - kelengkapan superadmin dan CSV: kolom versi Inggris aktif, halaman wajib berversi Inggris, dan halaman yang perlu
    diperbarui;
  - riwayat superadmin menyebut "(versi Inggris)".
- **Panduan:** bagian baru "Versi bahasa Inggris"; rencana Fase 5 §3.4 dan §4 mencatat cara pelaksanaannya.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 24 rangkaian lulus.
- **`uji/uji_isi_inggris.py`** (baru):
  - memori terjemahan: teks yang diterjemahkan; baris sisipan tidak menggeser terjemahan; uraian lama tetap; baris
    wajib ditunda; judul boleh tidak diterjemahkan; tabel Excel di luar formulir; teks alternatif foto; formulir
    (terjemahan baru, dibuang, dikosongkan, isian tak dikenal); pemeriksaan dan pratinjau;
  - admin: tab English, formulir dengan teks aslinya, pengajuan berteks judi ditolak, operator mengajukan tetapi
    tidak menerbitkan, pratinjau Inggris, dikembalikan, diterbitkan, kolom English, perlu diperbarui setelah versi
    Indonesia berubah, perubahan saat menerjemahkan, riwayat dan versi lama, kelengkapan dan CSV, riwayat superadmin;
  - situs: halaman Sejarah dan dokumen Akreditasi berbahasa Inggris; halaman tanpa versi Inggris tidak ada; ditarik;
    versi Indonesia ditarik atau tidak lolos pemeriksaan membuat versi Inggris tidak tampil; pemeriksaan halaman bersih.
- **Uji mutasi:** sembilan aturan dimatikan satu per satu, dan setiap kali ada uji yang gagal. Tiga yang awalnya lolos
  (jalur lama hanya di luar daftar, tayang memerlukan dua versi, versi Indonesia yang tidak sah) kini punya pemeriksaan.
- Uji lama yang disesuaikan: `uji_alur_isi.py` (kolom CSV), `uji_penyunting.py` dan `uji_alur_isi.py` (setiap baris
  daftar juga menautkan versi Inggrisnya), `uji_admin.py` (enam rute baru), `uji_pilot.py` (label penyunting Inggris).
- **Dilihat di browser** (situs dan admin sementara dari data awal www): penyunting Inggris halaman Kerja Sama dengan
  tanda perlu diperbarui; halaman Partnerships dengan nama kolom dan pilihan berbahasa Inggris, nama mitra apa adanya.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data. Berkas versi Inggris baru dibuat saat pertama
  kali disimpan.
- Halaman tambahan baru masuk versi Inggris setelah punya nama menu Inggris (2b).
