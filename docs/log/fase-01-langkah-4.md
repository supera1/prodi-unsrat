# Fase 1 · Langkah 4 — Akun dan peran (26 Oktober 2026)

Branch: `fase/01-4-akun` (bercabang dari `fase/01-3c-beranda`).

## Yang dikerjakan
- **Akun per orang** `platform/admin/akun.py` → `rahasia/akun.sqlite` (SQLite bawaan Python, berkas hanya bisa
  dibaca pemiliknya).
  - Peran: `super` (semua prodi), `admin` (koordinator, prodi yang ditautkan), `operator` (prodi yang ditautkan).
    Satu akun boleh memegang lebih dari satu prodi.
  - Sandi argon2. **Sandi kuat** (K-P10): minimal 12 karakter (superadmin 16), huruf dan angka, bukan kata/pola umum
    ("unsrat", "admin", "qwerty", "123456", …), tidak memuat nama pengguna, nama orang, atau nama prodinya, tidak
    terlalu berulang, berbeda dari sandi lama.
  - Akun baru dan akun yang direset mendapat **sandi sementara acak** (mis. `xxxxx-xxxxx-xxxxx-xxxxx`, tanpa huruf yang
    mirip) yang wajib diganti saat pertama masuk. Tanpa surel (K-P12).
  - Siapa mengelola siapa: superadmin semua akun; admin prodi hanya operator yang **seluruh** prodinya termasuk prodi
    si admin. Tidak ada yang bisa menonaktifkan dirinya sendiri; superadmin aktif terakhir tidak bisa dinonaktifkan.
- **Log audit** `platform/admin/audit.py` → `log/audit.jsonl`: masuk, gagal masuk, terkunci, keluar, ganti sandi, reset,
  akun dibuat/diaktifkan/dinonaktifkan, beserta prodi terkait. Sandi (juga yang sementara) tidak pernah ditulis.
- **Aplikasi admin** `platform/admin/app.py` (Flask), pola keamanan dari admin www:
  - hanya alamat di `ADMIN_IP_BOLEH` (jaringan/VPN UNSRAT) yang mendapat apa pun, termasuk halaman masuk;
  - penguncian: 5 gagal per alamat dan 10 gagal per nama pengguna dalam 15 menit; nama yang tidak ada butuh waktu sama;
  - sesi baru setiap masuk, terikat sidik sandi dan status akun (sandi baru, reset, atau nonaktif langsung mengakhiri
    sesi di perangkat lain), berhenti setelah 2 jam diam atau 12 jam;
  - CSRF diperiksa terpusat untuk **semua** POST; header CSP ketat, `X-Frame-Options: DENY`, `no-store`;
  - **setiap rute wajib mendeklarasikan aksesnya** (`@akses`); rute tanpa deklarasi ditolak (gagal tertutup) dan aplikasi
    menolak dijalankan bila ada rute seperti itu; akses prodi diperiksa di satu tempat sebelum halaman mana pun.
- **Halaman**: masuk, keluar, ganti sandi (wajib untuk sandi sementara), dasbor (daftar prodi per jenjang), dasbor prodi
  (ringkasan pengumuman, akun prodi), Akun prodi (admin: buat operator, reset sandi, aktif/nonaktif), Akun semua dan
  Log audit (superadmin), Log audit prodi (admin). Sandi sementara ditampilkan **sekali** di halaman hasil, tidak lewat
  pesan *flash*, kuki, atau log.
- `platform/admin/siapkan.py`: kunci sesi di `rahasia/.env`, superadmin pertama (sandi sementara ke
  `rahasia/.kredensial-<nama>.txt`), daftar akun.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 7 rangkaian, 0 gagal. `uji/uji_admin.py`:
- aturan sandi dan akun; sandi tidak tersimpan sebagai teks biasa; injeksi SQL di nama pengguna tidak berpengaruh;
- alamat di luar jaringan (juga IPv6 dan `::ffff:`) ditolak; CSRF; header; penguncian per alamat dan per nama;
- sandi sementara → wajib ganti; sesi berakhir saat sandi diganti di perangkat lain, saat direset, saat dinonaktifkan,
  setelah 12 jam, dan bila `akun_id` di sesi dipalsukan;
- **matriks akses: 19 rute × 6 akun** (superadmin, 2 admin prodi berbeda, 3 operator termasuk satu yang memegang dua
  prodi). Uji gagal bila ada rute admin yang belum masuk matriks. Uji mutasi: melonggarkan satu aturan akses (operator
  boleh membuka daftar akun prodi) langsung membuat matriks gagal.

Diperiksa di browser (admin lokal, akun uji `pengembang`): masuk dengan sandi sementara → dipaksa membuat sandi baru →
dasbor 97 prodi → membuat akun admin prodi contoh untuk S1 Teknik Informatika → sandi sementara tampil sekali →
dasbor prodi dan log audit. Kredensial uji lokal ada di `rahasia/` (tidak masuk Git).

## Catatan
- Halaman Akun superadmin sementara memakai isian kode PDDIKTI dipisah koma untuk prodi; langkah 5 menggantinya dengan
  pilihan prodi dari registri.
- Penguncian login disimpan di memori proses admin (seperti www); waitress di langkah 7 menjalankan satu proses.

## Langkah berikutnya
Langkah 5 — superadmin: daftar prodi, tetapkan/ubah slug, aktif/nonaktif, tautan dosen (termasuk impor massal), tarik
data www dengan pratinjau, riwayat dan pemulihan versi.
