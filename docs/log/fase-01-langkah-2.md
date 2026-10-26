# Fase 1 · Langkah 2 — Model data + tarik data www (26 Oktober 2026)

Branch: `fase/01-2-data` (bercabang dari `fase/01-1-kerangka`).

## Yang dikerjakan
- `platform/lokasi.py`: lokasi data (`PRODI_DATA`, `PRODI_RIWAYAT`, `WWW_DATA`), daftar nama berkas data yang sah
  (tidak bisa menunjuk ke luar folder data), baca/tulis JSON atomik, tulis dengan riwayat versi.
- `platform/riwayat.py`: dipindah dari `platform/admin/` dan diadaptasi dari www; jalur dari `lokasi.py`.
- `platform/tarik_www.py`: tarik data resmi dari www (pratinjau → terapkan).
  - Hanya kolom yang dibutuhkan yang disalin. Data pimpinan fakultas, `nama_asli`, dan `terjemahan_diperiksa`
    tidak ikut.
  - Seluruh tarikan ditolak (tidak ada yang ditulis) bila: berkas tidak terbaca, kolom wajib kosong, kode PDDIKTI
    ganda atau tidak sah, jenjang tak dikenal, SKS/tanggal tidak sah, CPL rusak, unit tidak dikenal, atau ada
    **teks judi** di mana pun (termasuk huruf samaran) — jaga-jaga bila www tersusupi.
  - Prodi yang hilang dari www tetap disimpan dan ditandai `hilang_dari_www`. Bila lebih dari 10% prodi hilang
    sekaligus, tarikan ditolak kecuali `--paksa`.
  - Laporan: prodi baru, hilang, kembali, kolom yang berubah, CPL ditambah/diubah/dihapus, unit/kalender berubah,
    prodi yang belum terdaftar, dan data resmi yang masih kosong.
- `platform/registri.py`: registri prodi.
  - `--siapkan`: registri awal dari `slug.csv`, dicocokkan dengan data resmi (kode dan jenjang), plus
    `prodi/<kode>/situs.json` bawaan untuk tiap prodi. Tidak menimpa registri yang sudah ada.
  - Fungsi untuk superadmin (langkah 5): `daftarkan`, `ganti_slug` (slug lama disimpan untuk redirect dan tidak bisa
    dipakai prodi lain), `atur` (aktif/nonaktif, tautan dosen yang hanya boleh ke `https://dosen.unsrat.ac.id/`).
- `uji/uji_data.py` (±60 pemeriksaan) dan pemisahan tabel `docs/asal-modul.md` menjadi "Salinan utuh" dan "Diadaptasi".

## Verifikasi
```bash
python3 uji/jalankan-semua.py
```
Hasil: 3 rangkaian, 0 gagal. `uji_data` juga menarik data www asli: 97 prodi ditarik, 97 didaftarkan dari
`slug.csv`, 97 `situs.json` dibuat. Uji mutasi: mengubah satu byte salinan `svg_aman.py` membuat `uji_asal_modul` gagal.

Verifikasi manual (dengan repo www di folder sebelah):
```bash
python3 platform/tarik_www.py             # pratinjau
python3 platform/tarik_www.py --terapkan
python3 platform/registri.py --siapkan
python3 platform/tarik_www.py             # sekarang: "Tidak ada perubahan."
```

## Temuan data (untuk dilengkapi di superadmin www, bukan di sini)
10 prodi masih punya data resmi yang kosong:
- Tanpa CPL: Sp-1 Anestesiologi dan Terapi Intensif (11706), S2 Teknik Sipil (22101),
  Profesi Pendidikan Profesi Arsitek (23906), S3 Ilmu Kelautan (54041).
- Tanpa lembaga akreditasi: Sp-2 Subspesialis Ilmu Kesehatan Anak (11733), Sp-1 Kedokteran Keluarga Layanan Primer
  (11759), Profesi Arsitek (23906), S1 Teknik Pertambangan (31201), S3 Ilmu Pertanian (54001), S2 Agronomi (54104),
  S3 Ilmu Akuntansi (62001).

## Catatan untuk langkah berikutnya
- Teks kalender www memuat tautan relatif (mis. `pengumuman.html`); generator (langkah 3) harus mengubahnya menjadi
  alamat lengkap `https://www.unsrat.ac.id/...`.
- Penulisan lembaga akreditasi di www belum seragam (`LAM-Tek` dan `LAM-Teknik`, `BAN-PT / LAM-PTIP`). Platform
  menampilkannya apa adanya; sebaiknya diseragamkan di www.

## Langkah berikutnya
Langkah 3 — template induk + generator (menu.json, halaman, palet warna, daftar prodi di root, folder publik).
