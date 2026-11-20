# Fase 5 langkah 5a — Terjemahkan semua (K-P37)

Tanggal: 20 November 2026. Branch: `fase/05-5a-terjemahkan-semua`.

## Latar
Saat mencoba di komputer sendiri, pengguna menilai terjemahan per halaman merepotkan bila 22 halaman wajib harus
dibuka satu per satu. Pengguna meminta satu tombol **Terjemahkan semua**. Pengembang mengusulkan enam hal (letak
tombol, halaman yang diterjemahkan, layar konfirmasi, hasil berupa draf bertanda mesin, pemeriksaan tetap per halaman
tetapi dipercepat, dan pekerjaan di latar). Pengguna menyetujui keenamnya, dengan tiga keputusan sendiri:

- operator juga boleh menekan tombol ini;
- draf Indonesia ikut diterjemahkan;
- pengumuman ikut diterjemahkan sekaligus.

## Yang dikerjakan
- **`platform/admin/terjemah_semua.py`** (baru):
  - `rencana`:
    - halaman prodi menurut urutan menu yang isi Indonesianya punya teks tanpa terjemahan Inggris. Isi Indonesianya
      adalah draf bila ada, selain itu yang terbit, sama dengan tombol per halaman;
    - pengumuman yang boleh diubah akun itu (`pengumuman_admin.boleh_ubah`), selain yang ditarik, terbaru dulu;
    - yang dilewati: halaman yang disembunyikan di menu, judul tabel Excel, dan versi Inggris yang menunggu
      persetujuan. Versi Inggris yang menunggu ditampilkan sebagai "dilewati" beserta alasannya. Terjemahan yang ada
      tidak pernah ditimpa;
  - `jalankan`, per butir:
    - baca ulang butirnya, cek batas harian dan bulanan (yang tidak muat ditandai "belum" dan butir lain jalan), lalu
      terjemahkan dan catat pemakaiannya;
    - simpan sebagai draf Inggris bertanda mesin. Halaman memakai `ih.simpan_draf` dengan versi yang dibaca, jadi
      butir yang diubah orang lain di tengah jalan dilewati tanpa ditimpa. Pengumuman memakai `pengumuman.ubah`, dan
      hanya isian yang masih kosong yang diisi;
    - setiap butir masuk log audit (`semua=1`);
    - penyedia yang gagal (kunci, kuota, jaringan) menghentikan pekerjaan; yang sudah selesai tetap tersimpan;
  - `Pekerja`: satu pekerjaan per prodi. Berjalan di utas latar (`PRODI_BANGUN=latar`, bawaan), supaya load balancer
    tidak memutus permintaan yang lama, atau di dalam permintaan (`sinkron`/`mati`, untuk uji). Keadaan pekerjaan
    terakhir disimpan di memori;
  - rute `/prodi/<kode>/terjemahkan-semua`, untuk admin dan operator:
    - layar konfirmasi berisi daftar butir, jumlah teks, perkiraan karakter, dan sisa batas hari ini, dengan peringatan
      bila batasnya tidak cukup;
    - halaman kemajuan yang memuat ulang sendiri lewat `meta refresh`, tanpa JavaScript;
    - hasil terakhir dengan tautan ke setiap butir;
    - audit `terjemahkan-semua-dimulai` dan `terjemahkan-semua-selesai`.
- **Pengumuman:** `pengumuman.teks_mesin` dan `pengumuman.pasang_mesin` dipindahkan dari rute per pengumuman, sehingga
  tombol per pengumuman dan Terjemahkan semua memakai kode yang sama.
- **Pemeriksaan:**
  - daftar Isi halaman mendapat saringan **Terjemahan mesin belum diperiksa** (`?status=mesin`), dan daftar pengumuman
    juga (`?en=mesin`);
  - tab English mendapat **Terbitkan dan buka berikutnya** (admin) dan **Ajukan dan buka berikutnya** (operator),
    dengan aksi `terbitkan-lanjut`/`ajukan-lanjut` yang memakai aturan yang sama dengan tombol biasa;
  - halaman berikutnya adalah halaman berikut menurut urutan menu (lalu memutar ke awal) yang draf Inggrisnya masih
    memuat terjemahan mesin. Untuk admin, draf Inggris yang diajukan juga termasuk; untuk operator, draf yang menunggu
    persetujuan tidak. Bila tidak ada lagi, admin kembali ke daftar dengan pesan.
- **Tautan Terjemahkan semua** di daftar Isi halaman (dengan pesan selama pekerjaan berjalan), di daftar pengumuman,
  dan di kotak Versi bahasa Inggris Ringkasan prodi. Angka-angka kotak itu menautkan saringan baru.
- **Kotak terjemahan mesin per halaman** tidak lagi menulis "0 teks, ±0 karakter" bila semua teks sudah
  diterjemahkan.
- `dasar.html` (admin) mendapat `{% block kepala %}` untuk `meta refresh`.
- **Panduan, rencana, dokumen pilot:**
  - panduan: bagian "Terjemahkan semua" dan cara memeriksa hasilnya;
  - rencana §3.5 dan §8: keputusan pengguna;
  - sesi pengenalan pilot memakai alur baru.

## Uji
- `.venv/bin/python uji/jalankan-semua.py`: 28 rangkaian lulus.
- **`uji/uji_terjemahkan_semua.py`** (baru):
  - tanpa penyedia: tanpa tombol, pekerjaan ditolak;
  - rencana operator: urutan menu, draf Indonesia ikut, hanya pengumumannya sendiri; yang tersembunyi, yang sudah
    lengkap, dan yang ditarik tidak ikut; yang menunggu persetujuan dilewati beserta alasannya;
  - hasil pekerjaan operator:
    - draf bertanda mesin dan ketikan sendiri tetap;
    - judul tabel Excel tidak ikut, dan versi Inggris yang menunggu tetap utuh;
    - pemakaian tercatat tepat, log audit lengkap, halaman hasil muncul, dan bila dijalankan lagi tidak ada yang
      diterjemahkan;
  - saringan halaman dan pengumuman, nilai saringan yang tidak sah (404), dan tautan di Ringkasan;
  - rencana admin: semua pengumuman kecuali yang ditarik;
  - penyedia gagal: berhenti, tidak ada yang berubah, pemakaian tetap;
  - batas: yang tidak muat menunggu, yang lebih kecil tetap jalan;
  - diubah orang lain saat diterjemahkan: dilewati, dan simpanan orang lain tetap;
  - mode latar: kemajuan dengan `meta refresh`, pesan di daftar, pekerjaan kedua ditolak, lalu selesai;
  - tombol "… dan buka berikutnya":
    - urutan halaman berikutnya, dan pengajuan tanpa centang tetap di halaman yang sama;
    - draf yang menunggu persetujuan hanya menjadi halaman berikutnya bagi admin;
    - admin menerbitkan dari halaman ke halaman sampai tidak ada lagi, lalu muncul pesan di daftar.
- `uji_admin.py`: dua rute baru di matriks peran × rute (112 rute).
- `uji_pilot.py`: label "Terjemahkan semua", "Ya, terjemahkan semua", dan saringan yang disebut panduan tampil di
  admin.
- **Uji mutasi:** sebelas aturan dimatikan satu per satu, dan setiap kali ada uji yang gagal:
  - draf yang menunggu tidak dilewati, cek versi, pengumuman akun lain, pengumuman yang ditarik;
  - halaman tersembunyi, batas per butir, penyedia gagal tidak menghentikan;
  - "lanjut", halaman berikutnya bagi operator dan bagi admin, pengumuman ditimpa.

  Aturan "admin juga diarahkan ke pengajuan tanpa terjemahan mesin" awalnya lolos, lalu mendapat ujinya sendiri.
- **Dilihat di browser** (cuplikan dari data awal www dengan penyedia tiruan): layar konfirmasi (3 halaman,
  1 pengumuman, termasuk draf Indonesia Visi-Misi), hasil terakhir, serta tab English dengan "Terbitkan dan buka
  berikutnya" dan keterangan halaman berikutnya.

## Catatan
- Tidak ada paket Python baru, variabel stack baru, atau migrasi data.
- Belum dicoba dengan DeepL sungguhan dari langkah ini. Satu "Terjemahkan semua" untuk 22 halaman bisa memakai
  sebagian besar batas harian bawaan (50.000 karakter); layar konfirmasi menampilkan perkiraannya.
- Keadaan pekerjaan disimpan di memori. Bila admin dinyalakan ulang di tengah pekerjaan, butir yang sudah selesai tetap
  tersimpan, dan tombol yang sama melanjutkan sisanya.
