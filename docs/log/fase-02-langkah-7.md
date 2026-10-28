# Fase 2 langkah 7 — Impor Excel untuk tabel besar (K-P34)

Tanggal: 27 Oktober 2026. Branch: `fase/02-7-impor-excel`.

## Latar
Pengguna meminta impor Excel dikerjakan di langkah 7 tanpa menunggu pilot (pembaruan K-P26). Beberapa halaman wajib
memuat tabel ratusan baris (mata kuliah 250, publikasi 500, penelitian dan PkM 300), padahal datanya biasanya sudah
ada di Excel prodi.

## Yang dikerjakan
- **`platform/admin/impor_tabel.py`**:
  - **tabel yang bisa diimpor** dihitung dari templat isi: tampil sebagai tabel, minimal 50 baris, tanpa kolom berkas
    wajib. Sekarang 16 tabel di 14 halaman, termasuk semua yang dijanjikan rencana: mata kuliah, kerja sama, penelitian,
    publikasi, PkM, luaran, prestasi mahasiswa, pelatihan dan prestasi dosen, survei kepuasan, jadwal, tenaga
    kependidikan; lalu linimasa sejarah, studi lanjut, ruang, sistem informasi;
  - **templat .xlsx per tabel:** lembar Data (nama kolom, baris yang ada di halaman, daftar pilihan untuk kolom pilihan
    dan ya/tidak), lembar Petunjuk (isi setiap kolom, wajib atau tidak), dan lembar pilihan tersembunyi. Teks yang
    diawali `=` ditulis sebagai teks (bukan rumus), karakter kendali dibuang. Kolom berkas (RPS, bukti kerja sama)
    tidak ada di Excel;
  - **pembacaan:** lembar pertama Excel atau CSV (2 MB, 2.000 baris, 40 kolom). Nama kolom tanpa membedakan huruf
    besar, spasi, dan tanda; boleh label atau kunci; kolom lain diabaikan dan disebut. Sel dibaca seperti isian
    formulir: angka Excel, tahun "2.025", persen "87,5%" dan sel berformat persen Excel (0,875 → 87,5), pilihan tanpa
    membedakan huruf besar, ya/tidak (ya, x, ✓, 1 …), tanggal dan jam di kolom teks (dd/mm/yyyy, hh:mm), baris baru di
    teks satu baris menjadi spasi;
  - **pemeriksaan per baris** dengan aturan halaman yang sama (`isi_halaman.masalah_nilai`, baru): wajib, batas,
    https, saringan spam. Pesan menyebut nomor baris di Excel; baris bermasalah tidak ikut. Berkas tanpa nama kolom
    yang dikenal, tanpa kolom wajib, atau melebihi batas baris ditolak seluruhnya dengan alasannya;
  - **tambah atau ganti:** "tambah" melewati baris yang sama persis dengan baris yang ada (spasi dan isian kosong tidak
    dibedakan); "ganti" mempertahankan berkas baris yang tidak berubah. Batas baris tabel tetap berlaku.
- **Admin** (operator dan admin prodi, seperti menyimpan draf):
  - tautan "Impor dari Excel" di penyunting halaman yang punya tabel besar;
  - halaman impor per halaman: unduh templat, kolom dan isinya, unggah;
  - pratinjau tanpa menyimpan: jumlah baris dibaca, siap, dan bermasalah beserta pesannya, pilihan tambah/ganti dengan
    ukuran hasilnya (tambah dimatikan bila melebihi batas), berkas yang akan terlepas, dan 20 baris pertama;
  - "Masukkan ke draf": `simpan_draf` dengan pemeriksaan versi; isi terbit tidak berubah, versi sebelumnya masuk
    riwayat, impor tercatat di log audit (`isi-impor-pratinjau`, `isi-tabel-diimpor`);
  - pratinjau disimpan di folder sementara superadmin (`simpan_sementara`, kini juga lewat `alat`): 30 menit, sekali
    pakai, hanya untuk akun pengunggah, prodi, halaman, dan tabelnya.
- **Dokumen:** K-P34, panduan admin prodi (bagian "Mengisi tabel dari Excel" dan pesan "Pratinjau impor sudah tidak
  berlaku"), rencana Fase 2 §8, CLAUDE.md.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 20 rangkaian lulus.
- **`uji/uji_impor_tabel.py` (baru):**
  - tabel yang memenuhi syarat (juga dengan templat buatan berkolom foto wajib) dan nama kolom yang tidak ganda;
  - templat: lembar, baris yang ada, daftar pilihan, teks `=` tetap teks, karakter kendali dibuang;
  - templat bolak-balik untuk setiap jenis kolom;
  - sel dari berkas buatan luar, termasuk persen Excel, tanggal, dan jam;
  - pesan per baris dengan nomor baris, CSV, dan 9 jenis berkas yang ditolak;
  - tambah/ganti/batas;
  - alur admin: tautan, halaman impor, templat berisi draf, pratinjau tanpa simpan, impor ke draf (terbit tetap, riwayat,
    log audit), pratinjau sekali pakai, milik akun lain, dari prodi atau halaman lain, ganti dengan RPS tetap, batas
    tabel, dan unggahan yang ditolak.
- `uji_admin.py`: 4 rute baru di matriks peran × rute.
- `uji_pilot.py`: tombol yang disebut panduan tampil di admin; pesan baru sama dengan di kode.
- **Uji mutasi:** 19 aturan dimatikan satu per satu; setiap kali ada uji yang gagal.

  | Mutasi | Uji yang gagal |
  |---|---|
  | tabel kecil ikut | 4 |
  | tabel dengan kolom berkas wajib ikut | 1 |
  | teks `=` menjadi rumus | 1 |
  | karakter kendali tidak dibuang | 1 |
  | persen Excel tidak dikali 100 | 2 |
  | pilihan peka huruf besar | 8 |
  | centang selalu ya | 1 |
  | tanggal berjam sebagai teks mentah | 1 |
  | jam sebagai teks mentah | 1 |
  | baris tidak diperiksa | 8 |
  | kolom wajib yang hilang diterima | 2 |
  | batas baris berkas | 1 |
  | tambah menggandakan baris | 5 |
  | ganti membuang berkas baris yang sama | 2 |
  | batas tabel saat digabung | 2 |
  | pratinjau tidak dicek prodinya | 1 |
  | pratinjau langsung menyimpan | 3 |
  | impor langsung terbit | 5 |
  | templat tanpa baris yang ada | 3 |

- **Dilihat di browser** (cuplikan dari platform sementara, desktop dan 375 px): halaman impor, pratinjau dengan
  baris bermasalah, dan penyunting sesudah impor; tanpa scroll horizontal halaman.

## Catatan
- Tidak ada paket Python baru (`openpyxl` sudah dipakai impor tautan dosen dan data www), variabel stack baru, atau
  migrasi data.
- Tabel baru di `isi_halaman.TEMPLAT` otomatis bisa diimpor bila memenuhi syarat.
