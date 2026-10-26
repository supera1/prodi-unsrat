# Fase 1 · Langkah 5 — Superadmin (26 Oktober 2026)

Branch: `fase/01-5-superadmin` (bercabang dari `fase/01-4-akun`).

## Yang dikerjakan
- **Dasbor superadmin** (`/`): situs aktif dan terdaftar, prodi baru di www yang belum terdaftar, situs aktif tanpa
  admin prodi, tanpa tautan dosen, data resmi yang masih kosong, prodi hilang dari www, waktu tarik data terakhir,
  status bangun ulang.
- **Prodi** (`/super/prodi`, `/super/prodi/<kode>`):
  - daftar semua prodi dengan alamat, slug lama, status, jumlah admin/operator, tautan dosen, kelengkapan data resmi;
  - ubah slug (aturan slug, tidak boleh slug atau slug lama prodi lain); slug lama disimpan dan dialihkan 301;
  - aktifkan/nonaktifkan situs, simpan tautan dosen, bangun ulang satu situs;
  - **daftarkan prodi baru dari www** dengan usulan slug sesuai pola yang disetujui (jenjang + nama tanpa
    "Teknik"/"Ilmu").
- **Tautan dosen massal** (`/super/dosen`): unduh templat CSV (semua prodi + tautan sekarang, BOM untuk Excel, sel yang
  bisa menjadi rumus dinetralkan) → isi → unggah CSV (koma atau titik koma) atau Excel .xlsx → **pratinjau** (berubah,
  sama, kosong, baris bermasalah) → terapkan. Pratinjau sekali pakai, milik akun pembuatnya, berlaku 30 menit.
- **Data resmi dari www** (`/super/tarik`): pratinjau perubahan (prodi baru/hilang/kembali, kolom berubah, CPL,
  fakultas, kalender, identitas universitas, data yang masih kosong) → terapkan → semua situs dibangun ulang.
  - Pratinjau yang usang (data www berubah setelah pratinjau dibuat) tidak bisa diterapkan.
  - Sumber yang rusak atau berisi teks judi ditampilkan sebagai masalah dan tidak pernah diterapkan.
  - Bila >10% prodi hilang sekaligus, perlu centang konfirmasi.
- **Riwayat** (`/super/riwayat`): semua versi berkas data, saringan per berkas/prodi, **bandingkan dengan isi sekarang**
  (beda baris), **pulihkan** (isi sekarang disimpan dulu sebagai versi baru), lalu bangun ulang yang terdampak.
- **Akun**: halaman ubah nama lengkap, peran, dan prodi dengan **kotak centang per fakultas** (menggantikan isian kode
  dipisah koma). Berlaku langsung juga untuk sesi yang sedang berjalan. Peran akun sendiri tidak bisa diubah.
- **Log audit**: saringan per prodi, akun, dan jenis aksi.
- **Bangun ulang otomatis** (`platform/admin/pembangun.py`): setiap perubahan memicu bangun ulang di proses terpisah, satu
  per satu; permintaan yang datang selama bangun digabung (lebih dari 5 prodi → satu bangun penuh). Status, peringatan,
  dan keluarannya di `/super/bangun`; hasilnya tercatat di log audit.
- Pendukung: `akses.py` (deklarasi akses dipisah), `impor_dosen.py`, `registri.belum_terdaftar / periksa_dosen_url /
  atur_banyak / nama_tampil / kunci_urut`, `slug.usulan`, `akun.ubah`, `audit.baca(oleh, aksi)`.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 8 rangkaian, 0 gagal.
- `uji_admin`: matriks akses kini **39 rute × 6 akun**; ke-20 rute superadmin baru hanya terbuka untuk superadmin.
  Uji itu sendiri yang menolak berjalan sebelum rute baru dimasukkan ke matriks.
- `uji_superadmin` (bangun ulang sungguhan): ganti slug (ditolak bila tidak sah/terpakai, situs pindah folder,
  pengalihan ditulis), aktif/nonaktif, tautan dosen satuan dan massal (CSV, CSV titik koma + BOM, Excel; token sekali
  pakai, kedaluwarsa, dan token aneh ditolak; berkas palsu/besar/lama ditolak), tarik data (pratinjau usang, sumber
  berjudi, banyak prodi hilang), daftarkan prodi baru, riwayat (bandingkan, pulihkan, jalur `../` ditolak), ubah akun
  (akses baru dan pencabutan langsung berlaku di sesi berjalan), saringan log, antrean bangun (penggabungan, bangun gagal
  dilaporkan). Akhirnya semua halaman situs hasil bangun diperiksa lagi.

Diperiksa di browser dengan data asli (97 prodi) dan bangun ulang di latar belakang: dasbor superadmin, halaman prodi,
simpan tautan dosen uji → situs prodi itu dibangun ulang dalam 0,8 detik, Data www ("tidak ada perubahan"), Riwayat →
bandingkan → pulihkan (tautan uji hilang lagi, semua situs dibangun ulang 5,1 detik), halaman ubah akun dengan 97 kotak
centang dalam 12 kelompok fakultas.

## Perlu diketahui
- **Pemulihan versi mengembalikan seluruh berkas.** Memulihkan registri ke versi lama juga membatalkan pendaftaran
  prodi atau tautan dosen yang dibuat sesudah versi itu. Halaman perbandingan menunjukkan semua perbedaannya sebelum
  tombol "Pulihkan" ditekan.
- **Pengalihan slug lama** ditulis ke `nginx-buatan/slug-lama.conf` setiap bangun; Nginx baru memakainya setelah memuat
  ulang konfigurasi. Cara memuat ulang otomatis dirancang di langkah 7 (stack Docker).
- **Format daftar tautan dosen** yang akan diberikan diasumsikan satu tautan per prodi (kolom kode PDDIKTI atau slug +
  `dosen_url`). Bila daftarnya berupa satu baris per dosen (nama + tautan profil), perlu model data tambahan.

## Langkah berikutnya
Langkah 6 — admin prodi: identitas dan bagian depan beranda (latar, foto, teks, kartu), palet warna, logo, menu,
operator, formulir pengumuman dengan alur operator → admin prodi.
