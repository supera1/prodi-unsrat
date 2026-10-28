# Fase 2 langkah 7b — Halaman tambahan prodi dengan sematan (K-P35)

Tanggal: 28 Oktober 2026. Branch: `fase/02-7b-halaman-tambahan`.

## Latar
Pengguna ingin setiap prodi bisa menambah menu sendiri di luar halaman akreditasi, dengan PDF, foto, dan sematan dari
situs lain. Contoh yang dirujuk (`informatika.unsrat.ac.id/database-skripsi-ta/`) ternyata bukan sematan: tabel
1.522 baris (No, NIM, judul, dua pembimbing; HTML 368 KB) dan skrip pencarian 631 karakter yang ditempel langsung ke
WordPress. Cara itu sengaja ditutup di platform ini. Usulan enam keputusan disetujui pengguna; nomor 3 diubah: daftar
domain sematan tetap, tanpa jalur menambah domain baru (K-P35).

## Yang dikerjakan
- **`platform/halaman_tambahan.py`** (baru): daftar halaman tambahan per prodi (`data/prodi/<kode>/tambahan.json`):
  - id `x` + 6 heksa, nama menu (1–60 karakter, tanpa markah, saringan spam, tidak ganda), kelompok menu yang ada,
    alamat (huruf kecil, angka, tanda hubung, diawali huruf, maks. 40; dibuat dari nama, tetap setelah dibuat);
  - paling banyak 10 halaman; tambah, ubah nama/kelompok/urutan, hapus; setiap perubahan masuk riwayat.
- **`platform/sematan.py`** (baru): daftar layanan tetap (Google Docs, Sheets, Slides, Forms, Drive, Calendar, Maps,
  YouTube tanpa kuki):
  - `normalkan()`: kode `<iframe>` yang ditempel diambil alamatnya, tautan berbagi diubah ke alamat sematan
    (Docs/Sheets → `/preview`, Slides → `/embed`, Forms → `viewform?embedded=true`, Drive → `/preview`, YouTube →
    `youtube-nocookie.com/embed/<id>`); alamat lain ditolak dengan alasannya (host lain, http, tautan pendek, tautan
    sunting formulir, folder Drive, peta tanpa kode sematan, tanda kutip atau markah);
  - `periksa()`: yang disimpan dan diterbitkan harus persis bentuk sematan itu;
  - `CSP_FRAME` untuk `frame-src` (www.google.com hanya `/maps/embed`), `SANDBOX` tanpa navigasi atas.
- **`isi_halaman.py`**: `TEMPLAT_TAMBAHAN` (uraian, sematan maks. 5, dokumen PDF maks. 30, foto maks. 20, tautan maks.
  20, bagian tambahan); `templat_halaman()` dipakai di semua tempat yang dulu membaca `TEMPLAT[id]`; isian `url` dengan
  `sematan=True`; tampilan "sematan" (setiap sematan punya judul h2 sendiri).
- **Situs** (`menu.py`, `bangun.py`, `_isi.html`, `kelompok.html`, `prodi.css`):
  - halaman tambahan masuk menu hanya setelah terbit, sesudah halaman bawaan kelompoknya, di `/<slug>/halaman/<alamat>/`;
  - daftar yang rusak diabaikan dengan peringatan; isi halaman dihitung sekali per bangun (`isi_siap`);
  - bingkai: `sandbox`, `title`, `loading="lazy"`, `referrerpolicy`, `allow="fullscreen"`; tinggi pendek/sedang/tinggi,
    video 16:9; tautan "Buka … di tab baru" di bawahnya;
  - pratinjau admin menampilkan penanda, tidak memuat situs lain.
- **CSP:** `frame-src` di `bangun.CSP` dan `docker/nginx/header-keamanan.conf` ditambah host layanan sematan (uji Docker
  memastikan keduanya sama).
- **Pemantau** (`cek_integritas.py`, kini di bagian "Diadaptasi" `docs/asal-modul.md`): host yang boleh dari
  `sematan.HOST` ditambah bucket unggahan (`peta.unsrat.ac.id` asal www dibuang); sematan tanpa `sandbox` atau dengan
  `allow-top-navigation` dilaporkan `SKRIP`. PDF di bingkai dari situs sendiri (pengumuman) tidak terkena, karena PDF
  tidak tampil di bingkai bersandbox.
- **Admin:**
  - menu prodi **Halaman tambahan** (`tambahan_admin.py`, admin prodi dan superadmin): buat lalu langsung ke penyunting;
    ubah nama, kelompok, dan urutan; hapus (isi tetap di riwayat);
  - halaman tambahan ikut di **Isi halaman** (jenis "Tambahan") dan disunting dengan penyunting biasa, operator juga;
  - penyunting mengubah kode sematan atau tautan berbagi yang ditempel menjadi alamat sematan;
  - tautan "Lihat halaman ini di situs" hanya bila halaman tambahan sudah tampil;
  - superadmin: **Halaman tambahan** (`/super/tambahan`), daftar semua halaman tambahan dengan layanan sematannya;
  - riwayat menamai halaman tambahan, juga yang sudah dihapus;
  - kelengkapan halaman wajib tidak berubah.
- **Dokumen:** K-P35, panduan admin prodi (bagian "Halaman tambahan"), rencana §8, CLAUDE.md, `lokasi.py`,
  `docs/deploy.md`, `docs/asal-modul.md`.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 21 rangkaian lulus.
- **`uji/uji_tambahan.py`** (baru):
  - 14 bentuk alamat diterima dan 15 ditolak, termasuk bentuk tetap dan CSP;
  - daftar halaman tambahan: 13 kasus ditolak; tambah, ubah, urutan, hapus, dan riwayat;
  - templat dan pemeriksaan isi;
  - situs: belum terbit tidak tampil; terbit dengan bingkai bersandbox; judul di-escape; urutan di kelompok; ganti nama
    dan kelompok dengan alamat tetap; ditarik; daftar rusak;
  - pemantau bersih, dan melaporkan sematan tanpa sandbox, navigasi atas, dan host lain;
  - admin: buat, empat penolakan, operator mengajukan dengan kode sematan, pratinjau tanpa bingkai, terbitkan membangun,
    simpan nama/kelompok/urutan, prodi lain, daftar superadmin, riwayat, hapus, batas 10, log audit.
- `uji_admin.py`: 5 rute baru di matriks peran × rute. `uji_pilot.py`: menu dan tombol halaman tambahan yang disebut
  panduan tampil di admin.
- **Uji mutasi:** 24 aturan dimatikan satu per satu; setiap kali ada uji yang gagal (host lain, alamat mentah, http,
  tanda kutip, pemeriksaan isi, sandbox, navigasi atas, judul bingkai, tautan tab baru, pratinjau, CSP, belum terbit,
  daftar rusak, nama judi, batas 10, alamat ganda, kelompok, penyunting, dua aturan pemantau, akses operator,
  kelengkapan, bangun ulang saat hapus, tautan situs sebelum terbit).
- **Dilihat di browser** (cuplikan dari platform sementara, desktop dan 375 px):
  - halaman tambahan dengan Google Forms (bingkai termuat dari Google), video 16:9, PDF, dan tautan, tanpa scroll
    horizontal;
  - menu samping dan remah roti;
  - halaman admin Halaman tambahan;
  - pratinjau admin tanpa bingkai.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data.
- Langkah berikutnya (7c): halaman tugas akhir dengan tabel, impor Excel, dan kotak cari, tanpa NIM (K-P35 nomor 4–5).
