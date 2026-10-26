# Fase 1 · Langkah 5b — Data prodi bisa diubah (26 Oktober 2026)

Branch: `fase/01-5b-data-prodi` (bercabang dari `fase/01-5-superadmin`). Keputusan: K-P16 (mengubah K-P6 dan K-P15).

## Yang dikerjakan
- `platform/data_prodi.py`: **timpaan per kolom** di `prodi/<kode>/data.json` (nilai baru, nilai www saat diubah,
  siapa dan kapan). Salinan www (`warisan/prodi.json`) tidak pernah diubah.
  - Data efektif = data www + timpaan; dipakai generator (beranda, kartu fakta, Spesifikasi, Akreditasi, CPL), admin
    (nama prodi di semua halaman), dan dasbor superadmin.
  - Nilai yang sama dengan www tidak menjadi timpaan; mengembalikan nilai ke www menghapus timpaan.
  - Setiap nilai diperiksa (tanpa HTML, tanpa teks judi, panjang, jenjang, SKS 1–399, fakultas/pascasarjana yang ada,
    surel, tanggal yang ada, CPL ≤ 40 butir dengan isi), lalu seluruh rekaman diperiksa ulang dengan aturan tarik data.
  - **Bentrok**: kolom yang diubah prodi lalu diubah juga di www. Data prodi tetap dipakai; pilihan "Pakai data www"
    atau "Tetap data prodi". Timpaan yang sudah sama dengan www dihapus otomatis setelah tarik data.
- Halaman **Data prodi** (`/prodi/<kode>/data`, `platform/admin/prodi_admin.py`) untuk admin prodi dan superadmin:
  identitas, akreditasi (dengan saran nilai yang sudah ada), profil lulusan, dan **penyunting CPL** (ubah, hapus dengan
  mengosongkan isi, tambah lewat 3 baris kosong; tanpa JavaScript). Kolom yang diubah ditandai, nilai www ditampilkan di
  sampingnya, dan ada tabel "Kolom yang diubah di sini" dengan tindakan per kolom. Simpan → situs prodi dibangun ulang.
- Tarik data www menampilkan bentrok di pratinjau; dasbor superadmin menghitung prodi yang mengubah datanya sendiri
  dan yang bentrok; halaman prodi superadmin menautkan ke Data prodi.
- Matriks akses: 4 rute baru → **44 rute × 6 akun** (admin prodi lain dan operator ditolak).

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 9 rangkaian, 0 gagal. `uji/uji_data_prodi.py`: aturan timpaan dan 17 nilai tidak sah, data efektif, pindah
fakultas, formulir (CPL diubah/dihapus/ditambah, SKS dari isian angka, nilai tidak sah ditolak), situs dibangun ulang
(beranda, Akreditasi, CPL), bentrok saat tarik data (data prodi tetap; kolom lain mengikuti www), "tetap" dan "pakai
data www", timpaan dihapus setelah www menyamai, nama baru di admin, hitungan di dasbor superadmin.

Diperiksa di browser dengan data asli: S1 Agronomi → ubah CPL ke-1 → hanya kolom CPL yang tercatat sebagai timpaan
(kolom lain yang ikut terkirim tapi sama dengan www tidak), halaman CPL situs dibangun ulang 0,7 detik → "Pakai data
www" → kembali seperti semula. Pilihan fakultas kini hanya 12 fakultas/pascasarjana (bukan biro dan UPA); judul tiap
CPL "CPL ke-n (kode …)"; ringkasan CPL menyebut berapa butir yang berbeda dari www.

## Perlu diketahui
- Data di situs prodi bisa berbeda dengan www.unsrat.ac.id bila prodi mengubahnya. Halaman Data prodi mengingatkan
  agar perubahan yang benar juga disampaikan ke pengelola www.
- CPL dibandingkan sebagai satu daftar: bila www mengubah satu butir CPL setelah prodi mengubah CPL-nya, seluruh daftar
  CPL ditandai bentrok.
