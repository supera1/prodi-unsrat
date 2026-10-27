# Fase 2 · Langkah 5b — Tautan dosen di data awal (27 Oktober 2026)

Branch: `fase/02-5b-tautan-dosen` (bercabang dari `main` sesudah PR #2). Keputusan **K-P31 (baru)**, atas permintaan
pengguna.

## Yang dikerjakan
- **`platform/data-awal/dosen.csv`**: tautan daftar dosen tetap di dosen.unsrat.ac.id untuk 94 dari 97 prodi, dalam
  format templat impor menu Tautan dosen.
  - Sumbernya `program-studi-tautan.csv` dari pengguna: 86 baris cocok lewat slug www, 8 lewat nama dengan fakultas
    dan jenjang yang sama.
  - Daftar pasangan dan tiga prodi tanpa tautan ada di K-P31.
- **Registri baru langsung bertautan** (`registri.siapkan_dari_csv(..., dosen=DOSEN_AWAL)`), di ketiga jalur pembuatan
  registri:
  - start VM baru (`impor_www.py --isi-awal`; pesannya kini "97 prodi, 94 dengan tautan dosen");
  - `registri.py --siapkan`;
  - unggahan data www pertama di admin (pesan dan log audit menyebut jumlah tautannya).

  Uji yang membuat registri sendiri tidak memakai berkas ini.
- **Data lokal** pengembang sudah diisi lebih dulu lewat `registri.atur_banyak` (satu versi riwayat). Untuk VM yang
  registrinya sudah ada, superadmin mengunggah `platform/data-awal/dosen.csv` di menu Tautan dosen (`docs/deploy.md`
  §5).
- Butir 0 daftar periksa pilot (`docs/pilot-fase-02.md`) diperbarui: Fase 2 sudah di `main`.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
- 18 rangkaian, 0 gagal.
- `uji_impor_www.py` memeriksa:
  - `dosen.csv` memuat tepat satu baris untuk setiap prodi `slug.csv`, dengan tautan sah dan unik, dan bisa diunggah
    di Tautan dosen tanpa galat;
  - VM baru mendapat semua tautannya (termasuk Informatika);
  - unggahan data www pertama juga, beserta log auditnya.
- Mutasi: bila tautan diabaikan saat registri dibuat, 4 pemeriksaan gagal.
- Di situs lokal: 94 halaman Dosen Tetap menautkan daftar dosen prodinya. Tiga halaman tetap "sedang disiapkan":
  Pendidikan Profesi Arsitek, Sp-1 Kedokteran Keluarga Layanan Primer, Sp-2 Subspesialis Ilmu Kesehatan Anak.
