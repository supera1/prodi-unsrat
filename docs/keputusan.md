# Log Keputusan — Platform Website Program Studi UNSRAT

Setiap keputusan arsitektur atau kebijakan dicatat di sini: konteks, keputusan, konsekuensi.
Rincian Fase 1 ada di `rencana-fase-01.md`.

### K-P1 — Slug singkat, ditetapkan manual oleh superadmin
- **Konteks:** alamat yang diinginkan berbentuk `prodi.unsrat.ac.id/s1informatika`. Slug otomatis dari jenjang + nama
  menghasilkan `s1teknikinformatika`, dan yang terpanjang 38 huruf.
- **Keputusan:** slug ditetapkan superadmin; sistem hanya mengusulkan. Kunci tetap prodi adalah `kode_pddikti`.
- **Konsekuensi:** slug bisa diganti tanpa memindahkan data; slug lama disimpan dan dialihkan (301).
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P2 — Tiga peran, tanpa admin fakultas
- **Keputusan:** superadmin, admin prodi (koordinator), operator. Satu akun boleh memegang lebih dari satu prodi.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P3 — Seluruh 97 prodi mendapat situs
- **Konteks:** termasuk 7 prodi Profesi dan 12 Spesialis (Sp-1/Sp-2), yang juga diakreditasi.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P4 — Redirect situs prodi lama di luar repo ini
- **Keputusan:** pengalihan dari situs lama (mis. informatika.unsrat.ac.id) dikerjakan admin VM/jaringan UNSRAT.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P5 — Stack Docker terpisah di VM yang sama dengan www
- **Konsekuensi:** stack www tidak diubah; data www dibaca lewat volume yang dipasang hanya-baca.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P6 — Data resmi prodi hanya dari www (satu arah)
- **Konteks:** angka di situs universitas dan situs prodi tidak boleh berbeda, terutama saat visitasi asesor.
- **Keputusan:** nama, jenjang, gelar, SKS, CPL, bidang kerja, akreditasi, dan kode PDDIKTI diambil dari data www dan
  terkunci di platform prodi. Prodi hanya bisa mengusulkan perubahan (Fase 2). Prodi baru ditambahkan dulu di www.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P7 — Generator statis + admin Flask, admin hanya dari jaringan/VPN UNSRAT
- **Konteks:** pola ini sudah teruji di www dan tahan terhadap penyusupan judi online yang menimpa CMS dinamis.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P8 — Daftar slug disetujui
- **Keputusan:** `platform/data-awal/slug.csv`. Kata "Teknik" dan "Ilmu" dihilangkan; sebagian memakai singkatan
  (`s1pwk`, `s1msp`, `s1thp`, `s1psp`, `s2psdp`, `s2ppw`, `sp1obgin`, `sp1kklp`, …).
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P9 — Nama repo `prodi-unsrat`
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P10 — Tanpa 2FA; sandi kuat wajib
- **Keputusan:** minimal 12 karakter, memuat huruf dan angka, bukan sandi umum, tidak memuat nama pengguna atau nama
  prodi. Sandi sementara wajib diganti saat pertama masuk. Penguncian login dan batas sesi dari www tetap dipakai.
- **Konsekuensi:** pembatasan IP admin (jaringan/VPN UNSRAT) menjadi lapisan pelindung utama selain sandi.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P11 — Logo dan unggahan di Google Cloud Storage
- **Keputusan:** bucket yang sama dengan www, folder `prodi/<kode_pddikti>/`.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P12 — Tanpa SMTP
- **Keputusan:** pemilik akun mengganti sandinya sendiri; superadmin bisa mereset sandi siapa pun dan admin prodi bisa
  mereset sandi operator prodinya. Setiap reset dicatat di log audit.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P14 — Pengumuman dan berita per prodi masuk Fase 1 (langkah 3b)
- **Konteks:** prodi perlu memuat pengumuman (jadwal kuliah, ujian) dan berita (kegiatan, prestasi). Kabar yang bertanggal
  juga menjadi bukti kegiatan untuk akreditasi.
- **Keputusan:**
  - Satu jenis konten dengan 7 kategori tetap (`platform/template/kategori.json`). Kategori prestasi mahasiswa, prestasi
    dosen, penelitian, PkM, dan kerja sama otomatis tampil sebagai "Kabar terkait" di halaman akreditasi yang sesuai.
  - Foto JPEG/PNG (dikodekan ulang, EXIF/GPS dibuang) dan PDF (tanpa skrip, formulir aktif, sisipan, atau teks judi).
  - PDF dibaca dengan pembaca bawaan browser (bukan PDF.js); di ponsel hanya tombol Buka/Unduh.
  - Pratinjau tautan (Open Graph), umpan RSS per prodi, tanggal kedaluwarsa, sematkan, dan tanpa hapus permanen
    (hanya "ditarik").
  - Formulir admin dan alur operator → admin prodi dikerjakan di langkah 6; sampai itu lewat `platform/pengumuman.py`.
- **Konsekuensi:** pengumuman yang kedaluwarsa baru turun dari beranda saat situs dibangun ulang, jadi langkah 7 perlu
  bangun ulang terjadwal harian.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P15 — Bagian depan beranda bisa disesuaikan prodi; nilai resmi tetap dikunci (langkah 3c)
- **Konteks:** setiap prodi ingin bagian depan berandanya lebih khas. K-P6 mengunci data resmi dari www.
- **Keputusan** (pengguna, 26 Oktober 2026, dari dua pilihan):
  - Admin prodi boleh mengganti latar (warna pucat, warna utama penuh, warna pilihan, atau foto), label kecil, judul,
    subjudul, kalimat pengantar, label/urutan/tampil kartu fakta, dan menambah 2 kartu sendiri.
  - **Nilai** kartu resmi (akreditasi dan lembaganya, gelar, SKS, akreditasi internasional) tetap dari www dan tidak
    bisa ditimpa; judul halaman (`<title>`), kepala situs, dan halaman Spesifikasi tetap memakai nama resmi.
  - Foto latar: JPEG/PNG minimal 2400 × 800 piksel, dipotong otomatis 3:1 (2400 dan 1600 px) dan 4:3 untuk ponsel
    (1200 × 900) di sekitar titik fokus (tengah, kiri, kanan, atas, bawah).
  - Keterbacaan dijamin: warna pilihan mendapat teks putih atau gelap yang mencapai 4,5:1 (warna yang tidak bisa
    ditolak); foto diberi lapisan warna gelap prodi dengan opasitas yang dihitung agar teks putih tetap 4,5:1 di atas
    bagian foto yang putih sekalipun.
- **Konsekuensi:** formulir di langkah 6 menampilkan petunjuk ukuran foto (`media.PETUNJUK_HERO`) dan pratinjau.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P13 — Port di VM menyusul
- **Status:** terbuka. Diisi saat langkah 7 (Docker & deploy staging).
