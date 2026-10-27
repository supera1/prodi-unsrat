# Fase 2 · Langkah 5 — Panduan admin prodi dan persiapan pilot (27 Oktober 2026)

Branch: `fase/02-5-panduan` (bercabang dari `fase/02-4-akreditasi`). Rencana: [rencana Fase 2](../rencana-fase-02.md) §6
dan §8, keputusan K-P29 (disetujui), dan **K-P30 (baru, menunggu tinjauan)**.

## Yang dikerjakan
- **[Panduan admin prodi dan operator](../panduan-admin-prodi.md)** (`docs/panduan-admin-prodi.md`), berbahasa
  sederhana, dengan langkah bernomor dan nama tombol persis seperti di admin. Isinya:
  - sebelum mulai: jaringan/VPN, akun dan kata sandi, kedua peran;
  - Ringkasan; mengisi halaman: teks bermarkah, daftar dan tabel, PDF dan foto;
  - mengajukan dan menerbitkan; riwayat dan memulihkan versi; halaman Akreditasi; pengumuman; pengaturan situs;
  - data pribadi dan keamanan; tabel pesan yang sering muncul beserta artinya; bantuan.
- **Panduan di dalam admin** (K-P30), karena admin prodi tidak bisa membuka repo GitHub yang privat:
  - menu **Panduan** (`/panduan`, `platform/admin/panduan.py`), dari berkas yang sama, dengan daftar isi;
  - penguraiannya Markdown sederhana dengan semua karakter di-escape lebih dulu: tautan hanya ke `#bagian` atau
    `https://`, kode tidak ikut diurai, dan tidak ada paket baru;
  - berkasnya ikut di image admin (`Dockerfile`, dicatat di `docs/asal-modul.md`);
  - penyunting menautkan bagian "Mengisi halaman".
- **Menu Masukan** (K-P30, `platform/admin/masukan_admin.py`):
  - **pengirim:** setiap pengguna admin mengirim kendala, pertanyaan, atau usulan dari halaman mana pun (tautan di
    kepala admin membawa alamat halaman itu), lalu melihat masukannya sendiri beserta tanggapannya;
  - **superadmin:** menu **Masukan pengguna**, dengan saringan Baru / Ditindaklanjuti / Ditunda, tanggapan, dan
    unduhan CSV. Dasbor superadmin menyebut jumlah masukan baru;
  - **pemeriksaan:** isi wajib, paling banyak 2.000 karakter, tanpa karakter kendali, tanpa teks judi. Alamat asal hanya
    alamat admin ini; alamat situs lain tidak pernah disimpan;
  - **penyimpanan** di `masukan.json` di bawah satu kunci tulis, paling banyak 5.000 butir; setiap kiriman dan
    tanggapan masuk log audit.
- **[Persiapan pilot](../pilot-fase-02.md)** (`docs/pilot-fase-02.md`), untuk superadmin UPA TIK dan pemimpin pilot:
  - tabel prodi pilot (S1 Teknik Informatika; dua lainnya menunggu Anda);
  - daftar periksa sebelum pilot: staging, data www, prodi, akun dan cara menyerahkan kata sandi sementara, uji masuk;
  - susunan sesi pengenalan ±90 menit; kegiatan mingguan selama masa pengisian;
  - ukuran keberhasilan rencana §6 dan cara melihat masing-masing; apa yang ditulis sesudah pilot.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 18 rangkaian, 0 gagal. `uji_admin.py`: matriks 87 rute × 6 akun (6 baris baru).

Rangkaian baru `uji/uji_pilot.py` memeriksa:
- **pengurai panduan**:
  - judul ber-id, daftar isi, daftar bertingkat dengan baris lanjutan, tabel, kutipan, kode, huruf tebal;
  - `<script>`, markah di tabel, dan tautan `javascript:`, `//`, maupun `http://` tidak pernah menjadi HTML;
- **panduan sesuai admin**:
  - 33 tombol dan menu yang disebut panduan benar-benar tampil di halaman admin pada keadaan yang tepat (operator
    dengan draf, operator dengan draf menunggu, admin dengan draf menunggu, admin dengan isi terbit, riwayat halaman,
    daftar dan tabel, dasbor);
  - batas di panduan sama dengan kode: PDF 20 MB, foto 10 MB, lebar 600 piksel, 40 MB per simpan, kata sandi 12
    karakter, sesi 2 jam, 22 halaman wajib;
  - kesembilan pesan di tabel panduan memang pesan admin; tautan penyunting ke panduan punya tujuan;
- **/panduan** terbuka untuk superadmin, admin prodi, dan operator (4 akun uji; matriks akses: 6 akun), tanpa
  skrip/gaya sebaris; kepala admin menautkan Panduan dan Masukan;
- **masukan**:
  - tersimpan dengan pengirim, peran, prodi, dan halaman asal;
  - 5 bentuk isian salah ditolak, tanpa menyimpan apa pun; alamat asal yang bukan alamat admin dibuang;
  - pengirim hanya melihat masukannya sendiri, bahkan admin prodi tidak melihat masukan operatornya;
  - superadmin: jumlah di dasbor, daftar, tanggapan yang dibaca pengirim, status yang tidak dikenal dan tanggapan
    berteks judi ditolak, ganti status tanpa menghapus tanggapan, masukan yang tidak ada (404), saringan;
  - CSV dengan rumus dinetralkan; batas jumlah; 10 utas sekaligus tanpa ada yang hilang; log audit.

Uji mutasi (setiap aturan dimatikan sementara):

| Aturan yang dimatikan | Uji yang gagal |
|---|---|
| Escaping di pengurai panduan | 3 |
| Tautan panduan hanya `#…` dan `https://` | 4 |
| Kode tidak diurai sebagai huruf tebal | 2 |
| Alamat asal masukan hanya alamat admin | 3 |
| Pengirim hanya melihat masukannya | 2 |
| Masukan berteks judi ditolak | 6 |
| Kunci tulis masukan (dengan jeda 20 ms) | 1 |
| Panduan sesuai tombol admin ("Batalkan pengajuan" diganti) | 1 |
| Panduan sesuai batas unggahan (PDF 25 MB) | 1 |

Mutasi "tombol admin" awalnya lolos, karena label yang sama juga ada di formulir pengumuman. Pemeriksaannya kini memakai
halaman yang dirender pada setiap keadaan, bukan seluruh kode.

Diperiksa di browser (cuplikan statis dari klien uji):
- halaman Panduan (daftar isi dua kolom, tabel peran, tabel pesan);
- formulir Masukan dengan tiga masukan, satu sudah ditanggapi;
- Masukan pengguna dan dasbor superadmin;
- keempat halaman pada 320 px tanpa gulir ke samping.

## Perlu diketahui
- **K-P30** menambah dua hal yang tidak tertulis rinci di rencana: panduan di dalam admin dan menu Masukan. Mohon
  ditinjau.
- **Akun pilot belum dibuat**, karena staging belum tayang dan saya tidak menjalankan apa pun di server. Superadmin
  membuatnya di menu Akun mengikuti [docs/pilot-fase-02.md](../pilot-fase-02.md).
- **Dua prodi pilot** masih menunggu Anda (tabel di dokumen persiapan pilot).
- **Panduan tanpa gambar layar.** Gambar mudah usang saat admin berubah; bila pilot memintanya, bisa ditambahkan
  sesudah sesi pengenalan.

## Langkah berikutnya
Langkah 6 — pilot di staging: dimulai setelah staging tayang, akun dibuat, dan dua prodi pilot ditentukan. Perbaikan
dari masukan dikerjakan per langkah kecil (`fase/02-6a-…`).
