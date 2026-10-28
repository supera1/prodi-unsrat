# Label kriteria akreditasi — usulan bersama dan pemeriksaan LPMPP UNSRAT

**Status (27 Oktober 2026):** label kriteria **diisi admin prodi sendiri** di menu prodi **Kriteria akreditasi**
(K-P33), tanpa menunggu LPMPP. Kriteria setiap prodi disimpan di `data/prodi/<kode>/kriteria.json` dan jumlahnya
terlihat di menu **Kelengkapan** superadmin (layar dan CSV).

Berkas bersama `platform/template/kriteria.json` (kode: `platform/kriteria.py`) sekarang berfungsi sebagai **usulan**:
lembaga yang punya daftar kriteria (saat ini draf BAN-PT IAPS 4.0) bisa mengisi formulir admin prodi. Lembaga yang
dikonfirmasi di berkas itu (K-P29) hanya dipakai untuk prodi yang belum mengisi kriterianya sendiri; saat ini belum ada.
Bagian di bawah tetap berlaku untuk LPMPP yang ingin memeriksa atau melengkapi usulan.

## Untuk apa
Situs prodi dipakai untuk akreditasi. Bila pemetaan ini sudah dikonfirmasi, setiap halaman wajib menyebut kriteria
instrumen akreditasi yang dilayaninya, misalnya:

> Kriteria akreditasi BAN-PT: Kriteria 2, Tata Pamong, Tata Kelola, dan Kerja Sama

Halaman **Akreditasi** setiap prodi juga mendapat daftar "Halaman menurut kriteria akreditasi", sehingga asesor bisa
membuka halaman yang relevan per kriteria. Label dipilih menurut `lembaga_akreditasi` prodi di data resmi (www).

## Yang diminta dari LPMPP
1. **BAN-PT (IAPS 4.0):** periksa nama ke-9 kriteria dan pemetaan halaman di bawah. Halaman boleh punya lebih dari satu
   kriteria, dan boleh juga tanpa kriteria.
2. **Setiap LAM** (LAM-PTKes, LAM-SPAK, LAMEMBA, LAM Teknik, LAMSAMA, LAM-Infokom, LAM-PTIP): bila ada, kirim daftar
   kriteria instrumennya dan pemetaan halamannya sebagai usulan bersama. Pengembang tidak mengisi kriteria LAM sendiri
   supaya tidak ada yang dikarang; sampai itu, admin prodi mengetiknya dari instrumen lembaganya.
3. **Nilai lembaga di data resmi** yang perlu diputuskan:
   - 3 prodi bertanda `BAN-PT / LAM-PTIP` dan 7 prodi tanpa lembaga belum mendapat label apa pun;
   - `LAM-Teknik` dan `LAM-Tek` dianggap lembaga yang sama (LAM Teknik).
   Perbaikan nilai ini dilakukan di superadmin www, lalu data www diunggah lagi.
4. Untuk setiap lembaga yang sudah benar: nama pejabat atau unit yang mengonfirmasi, dan tanggalnya.

## Menyalakan label (pengembang)
Untuk lembaga yang dikonfirmasi, isi `kriteria.json` sebagai berikut:
- `"status": "dikonfirmasi"`;
- `"dikonfirmasi": {"oleh": "LPMPP UNSRAT", "tanggal": "YYYY-MM-DD"}`;
- kriteria dan pemetaannya.

Lalu jalankan langkah berikut, kemudian bangun ulang semua situs:

```bash
python3 platform/kriteria.py periksa
python3 platform/kriteria.py tabel
```

`periksa` memastikan berkasnya sah. `tabel` mencetak tabel untuk bagian "Pemetaan sekarang" di bawah: salin
keluarannya ke sini, karena `uji/uji_akreditasi.py` memastikan dokumen ini sama dengan berkasnya. Berkas yang rusak tidak
memunculkan label apa pun, dan generator mencatat peringatan.

## Pemetaan sekarang

### BAN-PT — Instrumen Akreditasi Program Studi (IAPS) 4.0 (draf)

Nilai `lembaga_akreditasi` di data resmi: `BAN-PT`.

| Kriteria | Halaman |
|---|---|
| 1. Visi, Misi, Tujuan, dan Strategi | Visi, Misi, Tujuan, dan Strategi |
| 2. Tata Pamong, Tata Kelola, dan Kerja Sama | Struktur Organisasi dan Tata Pamong, Penjaminan Mutu, Kerja Sama |
| 3. Mahasiswa | Penerimaan Mahasiswa Baru, Layanan Kemahasiswaan, Organisasi dan Prestasi |
| 4. Sumber Daya Manusia | Kelompok Keahlian, Tenaga Kependidikan, Prestasi dan Pengembangan Dosen |
| 5. Keuangan, Sarana, dan Prasarana | Laboratorium, Ruang Kuliah dan Ruang Pendukung, Perpustakaan dan Referensi, Sistem Informasi |
| 6. Pendidikan | Kurikulum, Peraturan dan Panduan, Jadwal Kuliah dan Ujian |
| 7. Penelitian | Penelitian |
| 8. Pengabdian kepada Masyarakat | Pengabdian kepada Masyarakat |
| 9. Luaran dan Capaian Tridharma | Publikasi Ilmiah, Luaran dan HKI, Organisasi dan Prestasi, Alumni dan Tracer Study, Survei Kepuasan |

Halaman tanpa kriteria: Sejarah, Akreditasi, Tugas Akhir.

### LAM-PTKes — Instrumen akreditasi LAM-PTKes (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAM-PTKes`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.

### LAM-SPAK — Instrumen akreditasi LAM-SPAK (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAM-SPAK`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.

### LAMEMBA — Instrumen akreditasi LAMEMBA (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAMEMBA`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.

### LAM Teknik — Instrumen akreditasi LAM Teknik (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAM-Teknik`, `LAM-Tek`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.

### LAMSAMA — Instrumen akreditasi LAMSAMA (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAMSAMA`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.

### LAM-Infokom — Instrumen akreditasi LAM-Infokom (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAM-Infokom`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.

### LAM-PTIP — Instrumen akreditasi LAM-PTIP (draf)

Nilai `lembaga_akreditasi` di data resmi: `LAM-PTIP`.

Daftar kriteria belum ada: menunggu daftar dari LPMPP.
