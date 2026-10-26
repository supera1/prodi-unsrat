# Fase 1 · Langkah 6 — Admin prodi (26 Oktober 2026)

Branch: `fase/01-6-admin-prodi` (bercabang dari `fase/01-5b-data-prodi`).

## Yang dikerjakan
Semua halaman prodi kini punya navigasi bersama (Ringkasan, Pengumuman, Data prodi, Identitas, Bagian depan beranda,
Menu, Akun, Riwayat, Log audit, Lihat situs); operator hanya melihat Ringkasan dan Pengumuman.

- **Dasbor prodi**: jumlah pengumuman per status (operator: miliknya), yang menunggu persetujuan (admin), 5 terakhir,
  dan **daftar periksa kesiapan situs** (data prodi lengkap, tautan dosen, logo, bagian depan, akun operator, 22 halaman
  wajib akreditasi yang menunggu penyunting halaman di Fase 2).
- **Identitas** (`/prodi/<kode>/identitas`): pilihan palet dengan contoh gambar (warna bendera fakultas sebagai bawaan,
  9 palet), media sosial (Instagram, Facebook, YouTube, TikTok, X, LinkedIn; hanya alamat https di situs itu sendiri),
  **logo prodi** (SVG dibersihkan dengan `svg_aman.py` dari www; PNG/JPG dikodekan ulang ke tinggi 56/112/168 px),
  lepas logo. Di situs: logo di kepala samping lambang UNSRAT, media sosial di kaki halaman.
- **Bagian depan beranda** (`/prodi/<kode>/beranda`): latar (warna prodi muda/penuh, warna pilihan dengan pemilih
  warna, foto), label, judul, subjudul, kalimat pengantar (teks bawaan tampil sebagai contoh), kartu fakta (label,
  urutan, sembunyi; nilainya dari Data prodi), 2 kartu tambahan; unggah foto latar dengan titik fokus dan pratinjau
  potongan 3:1 dan 4:3.
- **Menu** (`/prodi/<kode>/menu`): label kelompok dan halaman, urutan dalam kelompok, sembunyikan halaman opsional;
  jenis tiap halaman (wajib/opsional/otomatis) ditampilkan.
- **Pengumuman** (`/prodi/<kode>/pengumuman`, `platform/admin/pengumuman_admin.py`):
  - daftar dengan saringan status (yang menunggu di atas); formulir dengan foto (teks alternatif wajib), PDF,
    sematkan, berlaku sampai, peringatan privasi, dan pratinjau isi;
  - **alur**: operator menulis draf → ajukan → admin prodi **terbitkan** atau **kembalikan dengan catatan** → operator
    memperbaiki dan mengajukan lagi; admin juga bisa menulis dan menerbitkan langsung, mengubah yang sudah terbit,
    **menarik** dari situs, dan mengarsipkan draf. Tidak ada hapus permanen;
  - operator hanya melihat dan mengubah pengumuman miliknya selama masih draf/menunggu; apa pun yang dikirim formulir
    buatan, operator tidak bisa menerbitkan;
  - foto/PDF diperiksa **sebelum** disimpan; formulir yang ditolak tidak meninggalkan berkas.
- **Riwayat prodi** (`/prodi/<kode>/riwayat`): versi data prodi, identitas/beranda/menu, dan pengumuman milik prodi itu
  saja; bandingkan dan pulihkan. Perbandingan versi dipakai bersama dengan superadmin (`platform/admin/beda.py`).
- **Berkas unggahan di admin** (`/prodi/<kode>/berkas/...`): pratinjau foto/PDF/logo yang tersimpan lokal, hanya berkas
  prodi itu; SVG disajikan dengan CSP ketat.
- Setiap simpanan diperiksa modul pemilik datanya (`tampilan_prodi`, `menu`, `pengumuman`, `media`), dicatat di log audit,
  dan diikuti bangun ulang situs prodi itu. `tampilan_prodi.atur()` kini mengatur palet, logo, media sosial, dan menu juga.

## Verifikasi
```bash
.venv/bin/python uji/jalankan-semua.py
```
Hasil: 10 rangkaian, 0 gagal.
- `uji_admin`: matriks akses **64 rute × 6 akun**.
- `uji/uji_admin_prodi.py` (bangun ulang sungguhan): palet dan media sosial (4 alamat salah ditolak), logo PNG, logo SVG
  berisi `<script>`/`onload`/`javascript:` dibersihkan, 4 logo salah ditolak (termasuk SVG dengan entitas/XXE), bagian
  depan (warna tak terbaca ditolak, foto dengan titik fokus, pratinjau lewat admin), menu (permintaan buatan tidak bisa
  menyembunyikan halaman wajib), alur pengumuman lengkap dengan foto dan PDF, PDF berskrip ditolak, operator tidak bisa
  menerbitkan atau menyentuh milik orang lain, riwayat prodi (pulihkan; berkas prodi lain dan registri ditolak), akses
  berkas, dasbor admin dan operator, pemeriksaan semua halaman situs dan cek integritas.
- Uji mutasi: mengizinkan operator menerbitkan lewat tombol buatan langsung membuat 13 pemeriksaan gagal.

Diperiksa di browser (admin lokal): dasbor prodi dengan daftar periksa, Identitas (pilihan palet bergambar), Bagian
depan beranda, formulir pengumuman dengan pratinjau foto. Dua perbaikan dari pemeriksaan ini: tombol radio dan kotak
centang sempat ikut melebar penuh karena aturan CSS isian (kini dikecualikan), dan nama palet dipindah ke bawah
gambarnya. Jumlah halaman wajib yang benar adalah 22 (log langkah 3 sempat menulis 23; sudah dikoreksi).

## Perlu diketahui
- Admin prodi belum bisa mengunggah dokumen di halaman wajib (sejarah, VMTS, kurikulum, dll.): penyunting halaman
  tetap di Fase 2 sesuai rencana; dasbor prodi menghitung halaman yang menunggu.
- Tanpa surel (K-P12): operator mengetahui pengumumannya dikembalikan lewat dasbor dan daftar pengumuman.

## Langkah berikutnya
Langkah 7 — Docker & deploy staging: stack `prodi-unsrat` (web, admin, pemantau), volume, Nginx (termasuk memuat ulang
pengalihan slug), bangun ulang terjadwal harian, panduan Portainer, catatan DNS/load balancer untuk admin VM.

## Tambahan (26 Oktober 2026, sebelum langkah 7)
- **Keputusan baru** (pengguna): aplikasi di **VM sendiri**, di-deploy admin UNSRAT dari GitHub (K-P17); data www
  **diunggah manual oleh superadmin** (K-P18; Excel ekspor program studi dari superadmin www atau berkas JSON www);
  unggahan di **volume lokal** VM prodi (K-P19, mengganti K-P11); HTTPS disiapkan dua cara (load balancer atau di VM).
  Rencana langkah 7 diperbarui.
- **Perbaikan bug (dari langkah 3):** 7 prodi di data www berakreditasi `belum` (www: "Belum dilengkapi"). Situs prodi
  sempat menampilkannya sebagai nilai ("Akreditasi: belum"). Sekarang `belum` diperlakukan sebagai kosong (tanpa kartu
  akreditasi, halaman Akreditasi "sedang dilengkapi", dihitung sebagai data kosong di dasbor), dan nilai lain memakai
  label yang sama dengan www (mis. `TERAKREDITASI` → "Terakreditasi"). Uji ditambah dan dibuktikan dengan uji mutasi.
- **Perbaikan uji:** dua pemeriksaan bagian depan (`uji_bangun`, `uji_beranda`) memotong HTML pada kemunculan kedua
  `class="pahlawan` sehingga tidak benar-benar memeriksa kartu fakta; kini memotong satu bagian `<section>` utuh.
