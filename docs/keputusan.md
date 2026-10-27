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

### K-P5 — Stack Docker terpisah di VM yang sama dengan www *(digantikan K-P17, 26 Oktober 2026)*
- **Konsekuensi:** stack www tidak diubah; data www dibaca lewat volume yang dipasang hanya-baca.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P6 — Data resmi prodi hanya dari www (satu arah)
- **Konteks:** angka di situs universitas dan situs prodi tidak boleh berbeda, terutama saat visitasi asesor.
- **Keputusan:** nama, jenjang, gelar, SKS, CPL, bidang kerja, akreditasi, dan kode PDDIKTI diambil dari data www dan
  terkunci di platform prodi. Prodi hanya bisa mengusulkan perubahan (Fase 2). Prodi baru ditambahkan dulu di www.
- **Diubah oleh K-P16 (26 Oktober 2026):** data tetap ditarik dari www, tetapi superadmin dan admin prodi boleh
  mengubahnya di platform; kode PDDIKTI tetap kunci dan prodi baru tetap ditambahkan lewat www.
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
- **Pelaksanaan (langkah 4):** superadmin minimal 16 karakter (admin prodi dan operator 12), karena akunnya
  menjangkau semua prodi; kata umum seperti "unsrat", "admin", "qwerty", "123456" ditolak di bagian mana pun.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P11 — Logo dan unggahan di Google Cloud Storage *(digantikan K-P19, 26 Oktober 2026)*
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
  - *Diubah oleh K-P16:* nilai itu kini diambil dari data prodi (www + perubahan di halaman Data prodi); pengaturan
    bagian depan tetap tidak bisa menimpanya, jadi setiap angka di situs berasal dari satu tempat.
  - Foto latar: JPEG/PNG minimal 2400 × 800 piksel, dipotong otomatis 3:1 (2400 dan 1600 px) dan 4:3 untuk ponsel
    (1200 × 900) di sekitar titik fokus (tengah, kiri, kanan, atas, bawah).
  - Keterbacaan dijamin: warna pilihan mendapat teks putih atau gelap yang mencapai 4,5:1 (warna yang tidak bisa
    ditolak); foto diberi lapisan warna gelap prodi dengan opasitas yang dihitung agar teks putih tetap 4,5:1 di atas
    bagian foto yang putih sekalipun.
- **Konsekuensi:** formulir di langkah 6 menampilkan petunjuk ukuran foto (`media.PETUNJUK_HERO`) dan pratinjau.
- **Disetujui:** pengguna, 26 Oktober 2026.

### K-P16 — Data resmi dari www bisa diubah di platform; perubahan lokal tetap dipakai (langkah 5b)
- **Konteks:** prodi perlu memperbarui datanya sendiri (mis. CPL kurikulum baru) tanpa menunggu www.
- **Keputusan** (pengguna, 26 Oktober 2026, dari pilihan yang diajukan):
  - **Superadmin dan admin prodi** boleh mengubah semua kolom data prodinya: nama, nama Inggris, jenjang, gelar, SKS,
    fakultas, surel, bidang kerja, akreditasi (peringkat, lembaga, berlaku hingga, internasional), dan CPL. Operator
    tidak. Kode PDDIKTI tidak bisa diubah.
  - Salinan dari www tidak pernah diubah; perubahan disimpan per kolom sebagai **timpaan** di `prodi/<kode>/data.json`
    bersama nilai www saat diubah. Situs memakai data www dengan timpaan di atasnya.
  - **Data prodi tetap dipakai** walau www berubah. Bila www mengubah kolom yang sudah diubah prodi, kolom itu ditandai
    **bentrok** (pratinjau tarik data, dasbor superadmin, halaman Data prodi) dengan pilihan "pakai data www" atau
    "tetap data prodi". Kolom yang tidak diubah prodi tetap mengikuti www. Timpaan yang sudah sama dengan www dihapus
    otomatis setelah tarik data.
- **Konsekuensi:** data di situs prodi bisa berbeda dengan www.unsrat.ac.id; halaman Data prodi mengingatkan agar
  perubahan yang benar juga disampaikan ke pengelola www. Semua perubahan tercatat di riwayat dan log audit.

### K-P17 — VM sendiri; di-deploy admin UNSRAT dari GitHub (mengganti K-P5)
- **Konteks:** aplikasi tidak lagi berbagi VM dengan www.unsrat.ac.id.
- **Keputusan** (pengguna, 26 Oktober 2026):
  - Stack `prodi-unsrat` berjalan di **VM sendiri**. Deploy dilakukan **admin UNSRAT** dengan mengambil kode dari
    GitHub `supera1/prodi-unsrat`; repo menyediakan berkas Docker dan panduannya, Claude tidak menjalankan apa pun ke
    server.
  - **Dengan `docker compose` di VM UNSRAT lain, tanpa Portainer** (pengguna, 26 Oktober 2026, sesudah langkah 8).
    `docs/deploy.md` hanya memuat cara itu; nama stack `prodi-unsrat` ditetapkan di `docker-compose.yml`.
  - **HTTPS: disiapkan dua cara.** Bawaan: stack melayani HTTP di belakang load balancer/reverse proxy yang memegang
    sertifikat (seperti www). Panduan deploy juga menjelaskan cara memasang sertifikat di VM itu sendiri bila tidak ada
    load balancer.
- **Konsekuensi:** volume data www tidak bisa dipasang ke VM prodi → K-P18. Kunci GCS www tidak ada di VM prodi → K-P19.
  Pembatasan admin ke jaringan/VPN UNSRAT (`ADMIN_IP_BOLEH`) tetap berlaku.

### K-P18 — Data resmi dari www diunggah manual oleh superadmin
- **Konteks:** www hanya menerbitkan `data/prodi.json` yang diringkas (kode dan alamat), jadi data lengkap (CPL,
  akreditasi, dll.) tidak bisa ditarik dari luar VM www.
- **Keputusan** (pengguna, 26 Oktober 2026, dari tiga pilihan: ekspor JSON publik di www, salin antar-VM, unggah
  manual): **superadmin prodi mengunggah berkas data www** di halaman Data www, lalu pratinjau → terapkan seperti
  sebelumnya (semua pemeriksaan tetap berlaku, termasuk saringan judi).
  - Data prodi dan CPL: **berkas Excel ekspor program studi dari superadmin www** (lembar "Program studi" dan "CPL";
    tombolnya sudah ada di www, www tidak perlu diubah), atau `prodi.json`.
  - Fakultas, kalender, dan kontak universitas (jarang berubah): `unit.json`, `kalender.json`, `situs.json` dari www;
    yang tidak diunggah tetap memakai salinan terakhir.
  - Folder `WWW_DATA` tetap didukung (komputer pengembang, atau bila kelak berkas disalin antar-VM).
- **Konsekuensi:** data prodi mengikuti www hanya sejauh superadmin rutin mengunggah; dasbor superadmin menampilkan
  kapan data terakhir diunggah.

### K-P19 — Unggahan disimpan di volume lokal VM prodi (mengganti K-P11)
- **Keputusan** (pengguna, 26 Oktober 2026): logo, foto, dan PDF disimpan di volume VM prodi (`PRODI_PENYIMPANAN=lokal`)
  dan disajikan Nginx situs prodi. Tidak perlu kunci GCS; berkas yang diterbitkan ikut diawasi pemantau integritas.
  Kode penyimpanan GCS tetap ada sebagai pilihan.
- **Konsekuensi:** volume data (termasuk unggahan) wajib dicadangkan setiap hari.

### K-P13 — Port di VM menyusul
- **Status:** terbuka untuk nilai akhirnya. Langkah 7 menyiapkan bawaan yang bisa diganti lewat variabel stack
  (`docs/deploy.md` §4): situs `PORT_SITUS=8080`, admin `PORT_ADMIN=8081`; dengan HTTPS di VM situs 80/443 dan admin
  `PORT_ADMIN_HTTPS` (mis. 8444). Nilai akhir disepakati dengan admin VM.

### K-P20 — Seluruh uji dijalankan saat image dibangun (langkah 7)
- **Konteks:** deploy dikerjakan admin UNSRAT dari GitHub; pengembang tidak menyentuh server (K-P17). Rencana §11
  meminta "seluruh uji lulus di dalam image".
- **Keputusan** (usulan langkah 7, perlu dikonfirmasi): `Dockerfile` menjalankan `uji/jalankan-semua.py` di dalam image
  itu sendiri, sebagai pengguna yang menjalankan admin. Bila satu uji gagal, build gagal dan stack lama tetap berjalan.
  `UJI_SAAT_BUILD=0` hanya untuk perbaikan darurat. Pelari uji memberi setiap rangkaian folder sementara dan membuang
  variabel `PRODI_*` stack, sehingga uji tidak pernah menyentuh volume.
- **Konsekuensi:** setiap deploy bertambah ±1–3 menit; yang berjalan di server selalu versi yang lulus semua uji di
  image yang sama. Uji data asli memakai salinan data www di repo (K-P22).

### K-P21 — Pengalihan slug lama disaring kontainer web (langkah 7)
- **Konteks:** generator (kontainer admin) menulis `slug-lama.conf` untuk Nginx. Bila Nginx memuat berkas itu langsung,
  siapa pun yang menguasai kontainer admin bisa menyisipkan direktif Nginx lain (mis. menyajikan kunci TLS).
- **Keputusan:** kontainer web hanya menyalin baris `rewrite` berbentuk tetap dengan slug yang sah, memeriksa
  `nginx -t`, lalu memuat ulang Nginx sendiri (diperiksa setiap 30 detik). Tanpa soket Docker, tanpa restart. Cara
  yang sama memuat ulang sertifikat TLS yang diperpanjang (HTTPS di VM).
- **Konsekuensi:** slug baru aktif paling lama ±30 detik setelah bangun ulang.

### K-P22 — VM baru mulai dari salinan data www di repo (langkah 7)
- **Keputusan:** `platform/data-awal/www/` (salinan data www dalam format www, dari commit www `37b5e6d`) diterapkan
  otomatis sekali pada VM yang belum punya data, bersama registri 97 prodi dari `slug.csv`, sehingga situs langsung
  terbangun; superadmin lalu mengunggah data www terbaru (K-P18). Data ini memang tayang publik di www.
- **Konsekuensi:** salinan diperbarui pengembang sesekali (`impor_www.py --tulis-data-awal`); `uji_impor_www.py` memberi
  tahu bila salinan sudah berbeda dari data www di komputer pengembang.

### K-P23 — Isi halaman wajib terstruktur per halaman (Fase 2)
- **Konteks:** 22 halaman wajib akreditasi per prodi diisi prodi sendiri; asesor perlu menemukan informasi yang sama di
  tempat yang sama di 97 situs.
- **Keputusan** (pengguna, 27 Oktober 2026, rencana Fase 2 §3): setiap halaman wajib dan opsional punya **templat isi**
  (bagian, isian, tabel) ditambah bagian tambahan bebas. Formulirnya dibentuk dari templat dengan pola penyunting
  superadmin www (`editor.py`), tanpa HTML; teks hanya dengan markah tautan `https://` dan huruf tebal.
- **Konsekuensi:** templat bisa direvisi setelah pilot tanpa menghapus isi (kunci yang tidak dikenal disimpan).

### K-P24 — Alur isi halaman operator → admin prodi, dan kelengkapan per prodi (Fase 2)
- **Keputusan** (pengguna, 27 Oktober 2026): operator dan admin prodi mengisi; admin prodi menerbitkan atau
  mengembalikan dengan catatan, seperti pengumuman (K-P14). Satu isi terbit dan satu draf per halaman; simpanan yang
  saling menimpa ditolak. Kelengkapan halaman wajib tampil di dasbor prodi dan superadmin.

### K-P25 — Dokumen akreditasi hanya yang boleh publik; label kriteria dari LPMPP (Fase 2)
- **Keputusan** (pengguna, 27 Oktober 2026): halaman Dokumen Akreditasi memuat dokumen yang boleh publik saja
  (sertifikat, SK, ringkasan); dokumen berisi data pribadi tidak diunggah ke situs. Label kriteria akreditasi per
  lembaga disiapkan atau dikonfirmasi LPMPP UNSRAT; sebelum itu tidak ditampilkan.

### K-P26 — Pilot 3 prodi dan pilihan tambahan (Fase 2)
- **Keputusan** (pengguna, 27 Oktober 2026):
  - pilot di staging: S1 Teknik Informatika dan dua prodi lain yang disebutkan pengguna; ukuran keberhasilan minimal 15
    dari 22 halaman wajib terbit per prodi pilot tanpa bantuan pengembang;
  - butir "usulan perubahan data resmi" (rencana Fase 1 §2) diganti laporan perubahan data prodi untuk diteruskan ke
    pengelola www;
  - impor Excel untuk tabel besar hanya bila pilot memerlukannya.

### K-P27 — Penyunting isi halaman: draf bersama, isian apa adanya, riwayat untuk simpanan sengaja (Fase 2 langkah 2)
- **Konteks:** formulir isi halaman bisa panjang (tabel sampai 300–500 baris) dan diisi bergantian oleh operator dan
  admin prodi. Tombol daftar (Tambah, Naik, Turun, Hapus) mengirim formulir tanpa JavaScript, jadi setiap klik adalah
  satu simpanan.
- **Keputusan** (usulan pengembang, disetujui pengguna 27 Oktober 2026):
  - satu draf bersama per halaman (bukan per orang); setiap simpanan memeriksa versi asal formulir, dan simpanan dari
    versi lama ditolak dengan nama pengubah dan waktunya, tanpa menulis apa pun (juga berkas);
  - isian yang belum sah (mis. tahun "20o5") disimpan apa adanya di draf lalu ditandai, supaya ketikan tidak hilang;
    halaman baru bisa diterbitkan (langkah 3) bila semua isian lolos pemeriksaan;
  - baris yang ditambah lalu dibiarkan kosong dibuang saat "Simpan draf"; butir yang baru dihapus bisa dikembalikan
    sampai simpanan berikutnya;
  - riwayat versi mencatat "Simpan draf", "Buang draf", penerbitan, dan penarikan; tombol daftar dan pratinjau
    menyimpan draf tanpa riwayat. Ini lebih sempit dari bunyi rencana §3.4 ("setiap simpanan masuk riwayat"), supaya
    riwayat berisi simpanan yang berarti, bukan setiap klik;
  - batas bagian formulir admin dinaikkan dari 1.000 (bawaan Flask) ke 4.000; formulir terbesar (300 baris kerja sama)
    2.725 bagian, diperiksa uji untuk setiap templat.
- **Konsekuensi:** perubahan lewat tombol daftar yang belum disusul "Simpan draf" tidak bisa dipulihkan dari riwayat
  (hanya dibuang bersama drafnya); pemulihan versi meneruskan hitungan versi (`riwayat.pulihkan`).

### K-P28 — Alur isi halaman: aturan rinci di dalam K-P24 (Fase 2 langkah 3)
- **Konteks:** K-P24 menetapkan alur operator → admin prodi seperti pengumuman. Beberapa hal rinci perlu ditentukan
  agar alurnya sulit dirusak oleh pengelola yang bukan developer.
- **Keputusan** (usulan pengembang, disetujui pengguna 27 Oktober 2026):
  - setiap tombol penyunting (termasuk Ajukan, Terbitkan, Kembalikan, Tarik) menyimpan dulu apa yang ada di formulir,
    jadi ketikan tidak pernah hilang karena tombol yang dipilih;
  - draf baru bisa diajukan atau diterbitkan bila lolos semua pemeriksaan dan tidak kosong. Admin tidak pernah menerima
    draf yang tidak bisa diterbitkan;
  - draf yang menunggu tetap bisa disunting operator (tetap menunggu; admin yang menerbitkan selalu melihat versi
    terbaru karena simpanan dari versi lama ditolak), tetapi tidak bisa dibuang operator sebelum pengajuannya dibatalkan;
  - Kembalikan wajib dengan catatan (paling banyak 500 karakter). Catatan tampil sampai draf diajukan lagi dan tetap ada
    di riwayat;
  - Tarik menurunkan isi dari situs dan menjadikannya draf (bila belum ada draf), supaya bisa diperbaiki dan diterbitkan
    lagi;
  - versi lama di riwayat halaman hanya bisa **dijadikan draf**, tidak langsung ke situs, sehingga melewati pemeriksaan
    dan persetujuan yang sama. Operator juga boleh, karena hanya mengubah draf. Pemulihan langsung tetap ada di menu
    Riwayat untuk admin prodi;
  - kelengkapan menghitung halaman wajib yang **terbit dan tampil** (lolos pemeriksaan), bukan sekadar pernah terbit.
- **Konsekuensi:** tanpa SMTP (K-P12), pemberitahuan hanya lewat dasbor: admin melihat jumlah halaman yang menunggu,
  operator melihat halaman yang dikembalikan.

### K-P29 — Dokumen akreditasi di halaman Akreditasi; label kriteria dari berkas yang dikonfirmasi LPMPP (Fase 2 langkah 4)
- **Konteks:** rencana §3.7 meminta satu halaman Dokumen Akreditasi per prodi ("misalnya `profil/dokumen-akreditasi`")
  dan label kriteria yang baru tampil setelah dikonfirmasi LPMPP (K-P25). Halaman **Akreditasi** (`profil/akreditasi`)
  sudah ada sejak Fase 1, menampilkan status dari data resmi, dan sudah menjanjikan "Sertifikat akreditasi sedang
  dilengkapi oleh Program Studi".
- **Keputusan** (usulan pengembang, disetujui pengguna 27 Oktober 2026):
  - **Dokumen Akreditasi** menjadi bagian dokumen di halaman Akreditasi itu, bukan halaman baru. Isinya daftar dokumen
    (sertifikat, SK, ringkasan hasil; judul, tahun, keterangan, PDF), keterangan, dan bagian tambahan, diisi lewat
    penyunting dengan alur K-P24.
    - Status akreditasi tetap otomatis dari data resmi dan tidak bisa diubah di sini (K-P15, K-P16).
    - Halaman ini tidak menambah hitungan halaman wajib (tetap 22) dan tercatat di kelengkapan sebagai "pelengkap".
  - **Label kriteria** ada di `platform/template/kriteria.json`, per lembaga akreditasi:
    - isinya nama instrumen, daftar kriteria, pemetaan halaman → kriteria, dan nilai `lembaga_akreditasi` data resmi yang
      berarti lembaga itu (mis. `LAM-Teknik` dan `LAM-Tek`);
    - lembaga baru tampil bila berstatus `dikonfirmasi` dengan nama pengonfirmasi dan tanggalnya;
    - draf tidak pernah tampil di situs maupun di penyunting.
    - Berkas disunting pengembang atas dasar daftar dari LPMPP (perubahannya jarang); berkas yang rusak tidak
      memunculkan label apa pun.
  - **Draf awal:** BAN-PT (IAPS 4.0, 9 kriteria) dengan usulan pemetaan. LAM hanya terdaftar namanya, tanpa kriteria;
    daftarnya menunggu LPMPP supaya tidak ada yang dikarang.
  - **Tampilan setelah dikonfirmasi:**
    - halaman yang dipetakan menyebut kriterianya di bawah judul;
    - halaman Akreditasi memuat "Halaman menurut kriteria akreditasi", hanya halaman yang ada di situs prodi itu.
- **Konsekuensi:** prodi dengan nilai lembaga yang tidak diklaim lembaga mana pun (kosong, `BAN-PT / LAM-PTIP`) tidak
  mendapat label sampai LPMPP memutuskan dan data www diperbaiki. Panduan untuk LPMPP: `docs/kriteria-akreditasi.md`.

### K-P30 — Panduan di dalam admin dan menu Masukan untuk pilot (Fase 2 langkah 5)
- **Konteks:** panduan admin prodi (`docs/panduan-admin-prodi.md`, rencana §6) ada di repo GitHub yang privat, padahal
  pembacanya admin prodi dan operator. Rencana §6 dan §9 juga meminta setiap masukan pilot tercatat dan ditindaklanjuti
  atau ditunda; tanpa surel (K-P12), masukan mudah tercecer di percakapan.
- **Keputusan** (usulan pengembang, disetujui pengguna 27 Oktober 2026):
  - **Panduan di admin.** Panduan tampil di admin sebagai menu **Panduan** (`/panduan`), dari berkas yang sama.
    - Berkasnya ikut di image admin. Penguraiannya Markdown sederhana dengan semua karakter di-escape; tanpa paket baru.
    - Penyunting menautkan bagian "Mengisi halaman".
    - Uji memastikan setiap tombol dan menu yang disebut panduan tampil di admin, dan batas serta pesan galat di
      panduan sama dengan di kode.
  - **Menu Masukan untuk setiap pengguna admin.** Isinya jenis (kendala, pertanyaan, usulan) dan teks; halaman asalnya
    ikut tercatat.
    - Pengirim melihat masukannya sendiri beserta tanggapannya.
    - Superadmin melihat semua masukan di **Masukan pengguna**, menandainya ditindaklanjuti atau ditunda dengan
      tanggapan, dan mengunduh CSV-nya untuk laporan pilot.
    - Dasbor superadmin menyebut jumlah masukan baru.
    - Disimpan di `masukan.json`; setiap kiriman dan tanggapan masuk log audit.
- **Konsekuensi:** masukan juga bisa datang dari luar admin (sesi pengenalan, telepon). Superadmin mencatatnya lewat
  menu yang sama supaya laporan pilot lengkap.

### K-P31 — Tautan dosen tetap setiap prodi ikut data awal VM baru (Fase 2)
- **Konteks:** halaman Dosen Tetap setiap situs menautkan daftar dosen prodi itu di dosen.unsrat.ac.id (`dosen_url` di
  registri). Registri dibuat sekali di VM baru dari `slug.csv`, tanpa tautan dosen, sehingga semua situs menampilkan
  "Tautan ke daftar dosen tetap program studi ini sedang disiapkan" sampai superadmin mengimpornya.
- **Keputusan** (pengguna, 27 Oktober 2026: "Masukkan tautan dosen ke data-awal supaya VM baru (staging) langsung terisi
  saat registri dibuat"):
  - `platform/data-awal/dosen.csv` memakai format templat impor menu Tautan dosen, satu baris untuk setiap prodi
    `slug.csv`. Tautan diterapkan di versi pertama registri, di setiap jalur pembuatannya: start VM baru
    (`impor_www.py --isi-awal`), `registri.py --siapkan`, dan unggahan data www pertama di admin.
  - **Asal data:** `program-studi-tautan.csv` dari pengguna (27 Oktober 2026), berisi 94 tautan dari dosen.unsrat.ac.id.
    - 86 tautan dicocokkan lewat slug www (`slug_di_www` di `slug.csv`).
    - 8 tautan dicocokkan menurut nama, dengan fakultas dan jenjang yang sama: Ilmu Administrasi Niaga → Ilmu
      Administrasi Bisnis; Sp-1 Ilmu Penyakit Jantung → Sp-1 Ilmu Penyakit Jantung dan Pembuluh Darah; Sp-1 Ilmu
      Penyakit Saraf → Sp-1 Neurologi; Pendidikan Profesi Apoteker → Profesi Apoteker; S1 Manajemen Sumber Daya
      Perairan → S1 Manajemen Sumberdaya Perairan; S1 Pemanfaatan Sumber Daya Perikanan → S1 Pemanfaatan Sumberdaya
      Perikanan; S2 Ilmu Linguistik → S2 Linguistik; S2 Kesehatan Masyarakat → S2 Ilmu Kesehatan Masyarakat.
    - Tiga prodi tanpa tautan di sumber: Pendidikan Profesi Arsitek, Sp-1 Kedokteran Keluarga Layanan Primer, Sp-2
      Subspesialis Ilmu Kesehatan Anak.
  - Hanya alamat di `https://dosen.unsrat.ac.id/` yang dipakai; baris lain dilewati.
- **Konsekuensi:** VM yang registrinya sudah ada tidak berubah sendiri. Superadmin mengunggah berkas yang sama di menu
  Tautan dosen. Tautan yang berubah di dosen.unsrat.ac.id diperbarui lewat menu itu, dan data awal diperbarui pengembang
  sesekali.
