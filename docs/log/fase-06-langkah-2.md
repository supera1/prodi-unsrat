# Fase 6 langkah 2 — Judul halaman akar dan kotak versi Inggris di dasbor superadmin

Tanggal: 27 November 2026. Branch: `fase/06-2-dasbor-dan-judul`.

## Latar
- Pengguna meminta judul halaman akar "Mau ke program studi mana?" diganti menjadi **"Pencarian Program Studi"**.
- Tangkapan dasbor superadmin di VM menunjukkan cacat tata letak dari langkah 5b Fase 5. Baris "Versi bahasa Inggris
  dan terjemahan mesin aktif untuk … prodi" ada di dalam kisi kartu ringkasan (`.ringkasan`). Karena kisi itu
  menganggap setiap butir sebagai satu tautan berbentuk kartu, teksnya terpecah dan nama prodi tampil sebagai kartu
  panjang yang menabrak bagian "Data resmi dari www".

## Yang dikerjakan
- `akar.html`: judul h1 menjadi "Pencarian Program Studi". `DESIGN.md` dan kontrak desain di `.impeccable/surfaces/`
  ikut diperbarui.
- `super_dasbor.html`: baris versi Inggris dan pemakaian terjemahan mesin keluar dari kisi ringkasan dan pindah ke
  kotak tersendiri **Versi bahasa Inggris** (`#inggris`). Isinya:
  - jumlah prodi yang aktif dan daftar prodinya;
  - pemakaian terjemahan mesin bulan ini, atau keterangan "Terjemahan mesin belum aktif: kunci DeepL belum dipasang"
    beserta cara memasangnya bila penyedia terjemahan belum diatur;
  - tautan ke menu Prodi.
- `docs/versi-inggris-prodi.md` menunjuk ke kotak yang baru.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: semua rangkaian lulus.
- `uji_inggris_terbatas`: kotak versi Inggris tersendiri, di luar kisi ringkasan, berisi daftar prodi dan pemakaian.
- `uji_superadmin`: tanpa prodi berversi Inggris dan tanpa penyedia, kotak menulis 0 prodi dan keterangan kunci
  DeepL. Uji ini kini juga mengosongkan `TERJEMAH_PENYEDIA` dan `TERJEMAH_KUNCI` dari lingkungan.
